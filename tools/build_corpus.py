"""Build the replay corpus from recorded provider streams in public repositories.

Usage: python -I tools/build_corpus.py <src_dir> <out_dir>

<src_dir> holds sparse clones named owner_repo (see SOURCES). Every case keeps the exact
bytes the source recorded (or, for JSONL chunk fixtures and Gemini JSON-array streams, the
recorded payloads framed as SSE the way the provider frames them), a permalink to the file at
the pinned commit, the reference result and the stream shapes it exercises. Nothing is
synthesized: a case is a recorded response or it is not in the corpus.
"""

from __future__ import annotations

import glob
import gzip
import hashlib
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "src"))

import yaml  # noqa: E402

from llm_stream_check import reference, sse  # noqa: E402

SOURCES = {
    "pydantic_pydantic-ai": ("pydantic/pydantic-ai", "yaml", "tests/**/cassettes/**/*.yaml"),
    "vercel_ai": ("vercel/ai", "chunks", "packages/*/src/**/__fixtures__/*.chunks.txt"),
    "openai_openai-python": ("openai/openai-python", "sse", ".inline-snapshot/external/*.bin"),
    "anthropics_anthropic-sdk-python": ("anthropics/anthropic-sdk-python", "sse", "tests/lib/streaming/fixtures/*.txt"),
    "simonw_llm-gemini": ("simonw/llm-gemini", "yaml", "tests/cassettes/**/*.yaml"),
    "simonw_llm-anthropic": ("simonw/llm-anthropic", "yaml", "tests/cassettes/**/*.yaml"),
}

# Fixture names that describe a hand-built edge case rather than a recording. Excluded.
SYNTHETIC = re.compile(
    r"malformed|spliced|duplicate-message|missing-terminal|invalid_json|incomplete_partial|"
    r"input_transformations|unknown_events|omitted_usage|message_delta_fields|fallback",
    re.I,
)
# Shapes a client only gets after opting in to a beta or a request flag; not in the core suite.
OPT_IN = re.compile(r'"partialArgs"|"willContinue"|"caller":\{"type":"code_execution|programmatic', re.I)
# Recorded text-only answers, served for any request after the first one in a session, so
# agent loops that call the model again after running a tool get a real final answer.
FOLLOWUPS = {
    "openai-chat": ("vercel_ai", "chunks", "packages/openai/src/chat/__fixtures__/openai-text.chunks.txt", None),
    "anthropic": ("vercel_ai", "chunks", "packages/anthropic/src/__fixtures__/anthropic-text.chunks.txt", None),
    "gemini": ("vercel_ai", "chunks", "packages/google/src/__fixtures__/google-text.chunks.txt", None),
    "openai-responses": (
        "pydantic_pydantic-ai",
        "yaml",
        "tests/models/cassettes/test_openai_responses/test_openai_responses_stream.yaml",
        1,
    ),
}
MAX_BODY = 400_000
GZIP_MAGIC = bytes([0x1F, 0x8B])


def commit(path: str) -> str:
    return subprocess.check_output(["git", "-C", path, "rev-parse", "HEAD"], text=True).strip()


def provider_of(protocol: str, payloads: list, hint: str) -> str:
    h = hint.lower()
    for name in (
        "codex",
        "mistral",
        "groq",
        "deepseek",
        "xai",
        "openrouter",
        "moonshot",
        "cohere",
        "alibaba",
        "azure",
        "copilot",
        "snowflake",
        "together",
        "fireworks",
        "cerebras",
        "huggingface",
        "bedrock",
        "vertex",
        "ollama",
        "lmstudio",
        "nebius",
        "grok",
    ):
        if name in h:
            return name
    return {"openai-chat": "openai", "openai-responses": "openai", "anthropic": "anthropic", "gemini": "google"}[
        protocol
    ]


def model_of(payloads: list) -> str | None:
    for p in payloads:
        if not isinstance(p, dict):
            continue
        for k in ("model", "modelVersion"):
            if isinstance(p.get(k), str):
                return p[k]
        for k in ("message", "response"):
            if isinstance(p.get(k), dict) and isinstance(p[k].get("model"), str):
                return p[k]["model"]
    return None


def features(protocol: str, payloads: list, exp: reference.Result, body: str) -> list[str]:
    f: set[str] = set()
    if len(exp.tool_calls) > 1:
        f.add("parallel_tool_calls")
    if exp.input_tokens is not None or exp.output_tokens is not None:
        f.add("usage")
    if protocol == "openai-chat":
        frags: dict[int, int] = {}
        indices: list[int] = []
        for p in payloads:
            if p.get("usage") and not p.get("choices"):
                f.add("usage_only_final_chunk")
            for ch in p.get("choices") or []:
                d = ch.get("delta") or {}
                if not d or all(v in (None, "", []) for k, v in d.items() if k != "role"):
                    f.add("empty_delta")
                tcs = d.get("tool_calls") or []
                if len(tcs) > 1:
                    f.add("multiple_tool_calls_in_one_chunk")
                for tc in tcs:
                    if tc.get("index") is None:
                        f.add("indexless_tool_call")
                    else:
                        indices.append(tc["index"])
                    if (tc.get("function") or {}).get("arguments"):
                        k = tc.get("index", -1)
                        frags[k] = frags.get(k, 0) + 1
                    fn = tc.get("function") or {}
                    if tc.get("id") and fn.get("name") and fn.get("arguments"):
                        f.add("name_and_arguments_in_one_chunk")
                if d.get("tool_calls") and (d.get("content") or d.get("reasoning_content") or d.get("reasoning")):
                    f.add("text_and_tool_call_in_one_chunk")
        if any(n > 1 for n in frags.values()):
            f.add("arguments_split_mid_json")
        uniq = sorted(set(indices))
        if uniq and (uniq[0] != 0 or uniq != list(range(uniq[0], uniq[0] + len(uniq)))):
            f.add("tool_call_index_gap")
    elif protocol == "anthropic":
        per: dict[int, int] = {}
        tool_idx = []
        for p in payloads:
            t = p.get("type")
            cb = p.get("content_block") or {}
            if t == "ping":
                f.add("ping_event")
            if t == "content_block_start" and cb.get("type") == "tool_use":
                tool_idx.append(p["index"])
            if t == "content_block_start" and cb.get("type") in ("thinking", "redacted_thinking"):
                f.add("thinking_block")
            if t == "content_block_delta" and (p.get("delta") or {}).get("type") == "input_json_delta":
                if p["delta"].get("partial_json", "") == "":
                    f.add("empty_delta")
                else:
                    per[p["index"]] = per.get(p["index"], 0) + 1
            if t == "message_delta" and (p.get("usage") or {}).get("input_tokens") is not None:
                f.add("usage_restated_in_message_delta")
        if any(n > 1 for n in per.values()):
            f.add("arguments_split_mid_json")
        if tool_idx and tool_idx[0] != 0:
            f.add("tool_call_index_gap")
        if any(not c.arguments for c in exp.tool_calls):
            f.add("tool_call_without_arguments")
    elif protocol == "openai-responses":
        per_item: dict[str, int] = {}
        out_idx = []
        for p in payloads:
            t = p.get("type", "")
            item = p.get("item") or {}
            if t == "response.function_call_arguments.delta":
                per_item[p.get("item_id", "")] = per_item.get(p.get("item_id", ""), 0) + 1
                if p.get("delta") == "":
                    f.add("empty_delta")
            if t == "response.output_item.added" and item.get("type") == "function_call":
                out_idx.append(p.get("output_index"))
            if t == "response.output_item.added" and item.get("type") == "reasoning":
                f.add("reasoning_item")
        if any(n > 1 for n in per_item.values()):
            f.add("arguments_split_mid_json")
        if out_idx and out_idx[0] not in (0, None):
            f.add("tool_call_index_gap")
    elif protocol == "gemini":
        chunks_with_calls = 0
        for p in payloads:
            parts = [pt for c in (p.get("candidates") or [])[:1] for pt in (c.get("content") or {}).get("parts") or []]
            if any("functionCall" in pt for pt in parts):
                chunks_with_calls += 1
                if sum(1 for pt in parts if "functionCall" in pt) > 1:
                    f.add("multiple_tool_calls_in_one_chunk")
            if p.get("usageMetadata") and not any(pt.get("text") or "functionCall" in pt for pt in parts):
                f.add("usage_only_final_chunk")
            if any(pt.get("thoughtSignature") for pt in parts):
                f.add("thought_signature")
        if chunks_with_calls > 1:
            f.add("tool_calls_across_chunks")
        if any(not c.arguments for c in exp.tool_calls):
            f.add("tool_call_without_arguments")
    return sorted(f)


def hand_written_ids(protocol: str, payloads: list) -> bool:
    """Ids like msg_1 or toolu_1 mark a fixture someone typed, not one an API returned."""
    ids = []
    for p in payloads:
        if not isinstance(p, dict):
            continue
        if protocol == "anthropic" and p.get("type") == "message_start":
            ids.append((p.get("message") or {}).get("id", ""))
        if protocol == "anthropic" and p.get("type") == "content_block_start":
            ids.append((p.get("content_block") or {}).get("id") or "toolu_" + "x" * 12)
        if protocol == "openai-chat" and p.get("id"):
            ids.append(p["id"])
        if protocol == "openai-responses" and isinstance(p.get("response"), dict):
            ids.append(p["response"].get("id", ""))
    return any(len(i) < 9 for i in ids if isinstance(i, str))


def split_responses(protocol: str, body: str) -> list[str]:
    """Some fixtures hold several consecutive responses of one multi-step run in one file.
    Split them back into one stream per response (each segment keeps its recorded payloads)."""
    events = sse.parse(body)
    segs: list[list[sse.Event]] = [[]]
    last_id = None
    for ev in events:
        try:
            p = json.loads(ev.data)
        except json.JSONDecodeError:
            segs[-1].append(ev)
            continue
        if not isinstance(p, dict):
            segs[-1].append(ev)
            continue
        start = False
        if protocol == "anthropic":
            start = p.get("type") == "message_start"
        elif protocol == "openai-responses":
            start = p.get("type") == "response.created"
        elif protocol == "openai-chat":
            cur = p.get("id")
            start = bool(cur) and last_id is not None and cur != last_id
            last_id = cur or last_id
        elif protocol == "gemini":
            cur = p.get("responseId")
            start = bool(cur) and last_id is not None and cur != last_id
            last_id = cur or last_id
        if start and any(e.data.strip() != "[DONE]" for e in segs[-1]):
            segs.append([])
        segs[-1].append(ev)
    if len(segs) == 1:
        return [body]
    out = []
    for seg in segs:
        datas = [e.data for e in seg if e.data.strip() != "[DONE]"]
        out.append(sse.frame(datas, protocol))
    return out


def iter_yaml(path: str):
    loader = getattr(yaml, "CSafeLoader", yaml.SafeLoader)
    try:
        with open(path, encoding="utf-8") as fh:
            doc = yaml.load(fh, Loader=loader)  # noqa: S506 - safe loader
    except Exception:
        return
    for i, inter in enumerate((doc or {}).get("interactions") or []):
        resp = inter.get("response") or {}
        body = resp.get("body") or {}
        text = body.get("string") if isinstance(body, dict) else None
        if text is None and isinstance(body, dict):
            text = body.get("content") if isinstance(body.get("content"), str) else None
        if isinstance(text, bytes):
            try:
                text = (gzip.decompress(text) if text[:2] == GZIP_MAGIC else text).decode("utf-8")
            except (OSError, UnicodeDecodeError):
                continue
        uri = (inter.get("request") or {}).get("uri", "")
        if isinstance(text, str) and "streamGenerateContent" in uri and text.lstrip().startswith("["):
            # Gemini without alt=sse streams one JSON array: the same payloads, framed as SSE.
            try:
                text = sse.frame(json.loads(text), "gemini")
            except json.JSONDecodeError:
                continue
        if not isinstance(text, str) or "data:" not in text[:2000]:
            continue
        yield i, text, uri


def main(src: str, out: str) -> None:
    os.makedirs(out, exist_ok=True)
    seen: set[str] = set()
    ids: set[str] = set()
    cases = []
    for folder, (repo, kind, pattern) in SOURCES.items():
        base = os.path.join(src, folder)
        if not os.path.isdir(base):
            print("missing source", folder, file=sys.stderr)
            continue
        sha = commit(base)
        for path in sorted(glob.glob(os.path.join(base, pattern), recursive=True)):
            rel = os.path.relpath(path, base).replace("\\", "/")
            if SYNTHETIC.search(rel):
                continue
            items = []
            if kind == "yaml":
                items = list(iter_yaml(path))
            elif kind == "chunks":
                with open(path, encoding="utf-8") as fh:
                    lines = [ln for ln in fh.read().splitlines() if ln.strip()]
                try:
                    payloads = [json.loads(ln) for ln in lines]
                except json.JSONDecodeError:
                    continue
                proto = reference.detect(payloads)
                if proto:
                    items = [(None, sse.frame(lines, proto), rel)]
            else:
                with open(path, encoding="utf-8", errors="replace") as fh:
                    items = [(None, fh.read(), rel)]
            expanded = []
            for inter, body, hint in items:
                if len(body) > MAX_BODY:
                    continue
                proto = reference.detect(sse.json_events(body))
                if not proto:
                    continue
                segs = split_responses(proto, body)
                for k, seg in enumerate(segs):
                    tag = inter if len(segs) == 1 else f"{'' if inter is None else str(inter) + '.'}r{k + 1}"
                    expanded.append((tag, seg, hint, len(segs) > 1))
            for inter, body, hint, was_split in expanded:
                payloads = sse.json_events(body)
                proto = reference.detect(payloads)
                if not proto:
                    continue
                if proto == "anthropic" and not (payloads and payloads[0].get("type") == "message_start"):
                    continue  # a fragment, not a whole response
                if hand_written_ids(proto, payloads):
                    continue
                if proto == "openai-chat" and any(
                    ch.get("index", 0) != 0 for p in payloads if isinstance(p, dict) for ch in (p.get("choices") or [])
                ):
                    continue  # n > 1 sampling; out of scope
                exp = reference.expected(proto, payloads)
                if not exp.tool_calls:
                    continue
                if any(isinstance(c.arguments, dict) and "__unparseable__" in c.arguments for c in exp.tool_calls):
                    continue
                digest = hashlib.sha256(body.encode()).hexdigest()
                if digest in seen:
                    continue
                seen.add(digest)
                opt_in = bool(OPT_IN.search(body))
                stem = re.sub(r"[^A-Za-z0-9]+", "-", os.path.splitext(os.path.basename(rel))[0]).strip("-").lower()
                cid = f"{proto}--{repo.split('/')[1]}--{stem}"[:110] + (f"--{inter}" if inter is not None else "")
                base_id, n = cid, 2
                while cid in ids:
                    cid, n = f"{base_id}--{n}", n + 1
                ids.add(cid)
                cases.append(
                    {
                        "id": cid,
                        "protocol": proto,
                        "provider": provider_of(proto, payloads, hint + " " + rel),
                        "model": model_of(payloads),
                        "core": not opt_in,
                        "source": {
                            "repo": repo,
                            "commit": sha,
                            "path": rel,
                            "interaction": inter,
                            "split_from_multi_response_recording": was_split,
                            "url": f"https://github.com/{repo}/blob/{sha}/{rel}",
                        },
                        "features": features(proto, payloads, exp, body),
                        "expected": exp.to_dict(),
                        "sha256": digest,
                        "body": body,
                    }
                )
    by: dict[tuple[str, bool], int] = {}
    for c in cases:
        d = os.path.join(out, c["protocol"])
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, c["id"] + ".json"), "w", encoding="utf-8", newline="\n") as fh:
            json.dump(c, fh, indent=1, ensure_ascii=False)
            fh.write("\n")
        by[(c["protocol"], c["core"])] = by.get((c["protocol"], c["core"]), 0) + 1
    print(len(cases), "cases", by)
    fdir = os.path.join(out, "followups")
    os.makedirs(fdir, exist_ok=True)
    for proto, (folder, kind, rel, inter) in FOLLOWUPS.items():
        base = os.path.join(src, folder)
        repo = SOURCES[folder][0]
        path = os.path.join(base, rel)
        if kind == "chunks":
            with open(path, encoding="utf-8") as fh:
                lines = [ln for ln in fh.read().splitlines() if ln.strip()]
            body = sse.frame(lines, proto)
        else:
            body = next(t for i, t, _ in iter_yaml(path) if i == inter)
        assert not reference.expected(proto, sse.json_events(body)).tool_calls
        sha = commit(base)
        with open(os.path.join(fdir, proto + ".json"), "w", encoding="utf-8", newline="\n") as fh:
            json.dump(
                {
                    "protocol": proto,
                    "source": {
                        "repo": repo,
                        "commit": sha,
                        "path": rel,
                        "interaction": inter,
                        "url": f"https://github.com/{repo}/blob/{sha}/{rel}",
                    },
                    "body": body,
                },
                fh,
                indent=1,
            )
            fh.write("\n")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
