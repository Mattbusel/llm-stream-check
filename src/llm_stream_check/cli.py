"""llm-stream-check: replay recorded provider streams through your stack and fail on any loss."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
import time
from collections import Counter
from importlib import metadata
from typing import Any

from . import __version__, corpus, server
from .adapters import REGISTRY, Adapter
from .compare import Observed, compare

QUIET_ENV = {
    "OPENAI_API_KEY": "sk-llm-stream-check",
    "ANTHROPIC_API_KEY": "sk-llm-stream-check",
    "GEMINI_API_KEY": "llm-stream-check",
    "GOOGLE_API_KEY": "llm-stream-check",
    "NO_PROXY": "127.0.0.1,localhost",
    "no_proxy": "127.0.0.1,localhost",
    "CREWAI_TELEMETRY_OPT_OUT": "true",
    "OTEL_SDK_DISABLED": "true",
    "HAYSTACK_TELEMETRY_ENABLED": "False",
    "ANONYMIZED_TELEMETRY": "False",
    "AGNO_TELEMETRY": "false",
    "LITELLM_LOCAL_MODEL_COST_MAP": "True",
    "DO_NOT_TRACK": "1",
    "SCARF_NO_ANALYTICS": "true",
    "TOKENIZERS_PARALLELISM": "false",
    "PYTHONIOENCODING": "utf-8",
    "GOOGLE_GENAI_USE_VERTEXAI": "false",
}


def versions(a: Adapter) -> dict[str, str] | None:
    out = {}
    for d in a.dists:
        try:
            out[d] = metadata.version(d)
        except metadata.PackageNotFoundError:
            return None
    return out


def usage_requested(case: corpus.Case, reqs: list[dict[str, Any]]) -> bool:
    """OpenAI Chat only sends usage when the client asks; other protocols always send it."""
    if case.protocol != "openai-chat":
        return True
    first = reqs[0] if reqs else {}
    return bool((first.get("stream_options") or {}).get("include_usage"))


def _row(a: Adapter, c: corpus.Case, losses: list[dict[str, str]], **extra: Any) -> dict[str, Any]:
    return {
        "adapter": a.name,
        "case": c.id,
        "protocol": c.protocol,
        "provider": c.provider,
        "features": list(c.features),
        "source": c.source["url"],
        "losses": losses,
        **extra,
    }


def run_adapter(a: Adapter, cases: list[corpus.Case], url: str) -> list[dict[str, Any]]:
    mine = [c for c in cases if c.protocol in a.protocols]
    if not mine:
        return []
    env = dict(os.environ)
    for k, v in QUIET_ENV.items():
        env.setdefault(k, v)
    src = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    env["PYTHONPATH"] = src + os.pathsep + env.get("PYTHONPATH", "")
    byid = corpus.by_id(mine)
    rows: list[dict[str, Any]] = []
    todo = [c.id for c in mine]
    while todo:
        # A framework that kills its own process on a bad stream loses that case, not the rest.
        fd, out = tempfile.mkstemp(prefix="llm-stream-check-", suffix=".jsonl")
        os.close(fd)
        try:
            p = subprocess.run(
                [sys.executable, "-m", "llm_stream_check.worker", a.name, url, out],
                input=os.linesep.join(todo),
                capture_output=True,
                text=True,
                env=env,
                encoding="utf-8",
                errors="replace",
                timeout=60 * 30,
            )
            with open(out, encoding="utf-8") as fh:
                lines = fh.read().splitlines()
        finally:
            os.unlink(out)
        done = set()
        for line in lines:
            try:
                r = json.loads(line)
            except json.JSONDecodeError:
                continue
            if "fatal" in r:
                return [{"adapter": a.name, "case": None, "losses": [{"kind": "error", "detail": r["fatal"]}]}]
            case = byid[r["case"]]
            done.add(case.id)
            o = r["observed"]
            obs = Observed(o["tool_calls"], o["usage"], o["usage_supported"], o["error"])
            reqs = server.requests_for(r["session"])
            if not usage_requested(case, reqs):
                obs.usage_supported = False
            losses = compare(case.expected, obs)
            if reqs and reqs[0].get("parallel_disabled") and len(case.expected["tool_calls"]) > 1:
                # The client asked for one call at most; a provider honoring that never sends more.
                losses = [x for x in losses if x.kind in ("lost_usage", "wrong_usage")]
            rows.append(_row(a, case, [x.to_dict() for x in losses], observed=o, usage_checked=obs.usage_supported))
        rest = [cid for cid in todo if cid not in done]
        if rest:
            rows.append(
                _row(
                    a,
                    byid[rest[0]],
                    [
                        {
                            "kind": "error",
                            "detail": "the framework ended the process on this "
                            "stream: " + (p.stderr or "").strip()[-400:],
                        }
                    ],
                )
            )
            rest = rest[1:]
        todo = rest
    return rows


def summarize(rows: list[dict[str, Any]], meta: dict[str, Any]) -> dict[str, Any]:
    adapters: dict[str, Any] = {}
    for r in rows:
        s = adapters.setdefault(
            r["adapter"],
            {"cases": 0, "cases_with_loss": 0, "losses": Counter(), "versions": meta.get(r["adapter"], {})},
        )
        s["cases"] += 1
        if r["losses"]:
            s["cases_with_loss"] += 1
        for x in r["losses"]:
            s["losses"][x["kind"]] += 1
    for s in adapters.values():
        s["losses"] = dict(s["losses"])
    return {
        "tool": f"llm-stream-check {__version__}",
        "generated": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "adapters": adapters,
        "rows": rows,
    }


def print_table(rep: dict[str, Any]) -> None:
    print(f"{'adapter':34} {'version':28} {'cases':>5} {'lossy':>5}  losses")
    for name, s in sorted(rep["adapters"].items()):
        v = ",".join(f"{k}={x}" for k, x in s["versions"].items())[:28]
        ls = ", ".join(f"{k}={n}" for k, n in sorted(s["losses"].items())) or "none"
        print(f"{name:34} {v:28} {s['cases']:>5} {s['cases_with_loss']:>5}  {ls}")


def cmd_run(ns: argparse.Namespace) -> int:
    cases = corpus.load(core_only=not ns.include_opt_in)
    if ns.protocol:
        cases = [c for c in cases if c.protocol in ns.protocol]
    if ns.case:
        cases = [c for c in cases if c.id in ns.case]
    if ns.adapter:
        unknown = [a for a in ns.adapter if a not in REGISTRY]
        if unknown:
            print("unknown adapter(s):", ", ".join(unknown), file=sys.stderr)
            return 2
        chosen = [REGISTRY[a] for a in ns.adapter]
    else:
        chosen = [a for a in REGISTRY.values() if versions(a) is not None]
    meta = {}
    for a in chosen:
        v = versions(a)
        if v is None:
            print(f"{a.name}: not installed ({', '.join(a.dists)}); asked for it, so this fails", file=sys.stderr)
            return 2
        meta[a.name] = v
    if not chosen or not cases:
        print("nothing to run: no installed adapter or no matching case", file=sys.stderr)
        return 2
    srv = server.start(cases)
    rows: list[dict[str, Any]] = []
    try:
        for a in chosen:
            rows += run_adapter(a, cases, server.url(srv))
    finally:
        srv.shutdown()
    rep = summarize(rows, meta)
    if ns.json:
        with open(ns.json, "w", encoding="utf-8") as fh:
            json.dump(rep, fh, indent=1, default=str)
    print_table(rep)
    lossy = sum(s["cases_with_loss"] for s in rep["adapters"].values())
    if lossy:
        print(
            f"\nFAIL: {lossy} case run(s) lost a tool call, its arguments, its id or the usage. "
            f"See {ns.json or 'the --json report'} for each one."
        )
        return 1
    print("\nOK: every recorded tool call and usage count came through.")
    return 0


def cmd_list(ns: argparse.Namespace) -> int:
    cases = corpus.load(core_only=not ns.include_opt_in)
    feats: Counter[tuple[str, str]] = Counter()
    for c in cases:
        for f in c.features:
            feats[(c.protocol, f)] += 1
    by = Counter(c.protocol for c in cases)
    for p, n in sorted(by.items()):
        print(f"{p}: {n} recorded streams")
        for (pp, f), k in sorted(feats.items()):
            if pp == p:
                print(f"  {f}: {k}")
    if ns.verbose:
        for c in cases:
            print(c.id, c.provider, c.model, c.source["url"])
    return 0


def cmd_adapters(ns: argparse.Namespace) -> int:
    for a in REGISTRY.values():
        v = versions(a)
        state = (
            ("built in" if not v else ", ".join(f"{k} {x}" for k, x in v.items())) if v is not None else "not installed"
        )
        print(f"{a.name:32} {'/'.join(a.protocols):40} {state}")
    return 0


def cmd_serve(ns: argparse.Namespace) -> int:
    cases = corpus.load(core_only=not ns.include_opt_in)
    srv = server.start(cases, port=ns.port)
    print(f"replaying {len(cases)} recorded streams at {server.url(srv)}/c/<case-id>~<any-nonce>/", flush=True)
    print("case ids: llm-stream-check list -v", flush=True)
    try:
        while True:
            time.sleep(3600)
    except KeyboardInterrupt:
        srv.shutdown()
    return 0


def cmd_check(ns: argparse.Namespace) -> int:
    """Check observations from a harness in another language (see harness/js) against the corpus.

    Each JSONL line: {"adapter", "case", "observed": {tool_calls, usage, usage_supported, error},
    "parallel_disabled"?, "versions"?}.
    """
    cases = corpus.by_id(corpus.load(core_only=False))
    rows: list[dict[str, Any]] = []
    meta: dict[str, Any] = {}
    with open(ns.file, encoding="utf-8") as fh:
        for line in fh:
            if not line.strip():
                continue
            r = json.loads(line)
            case = cases[r["case"]]
            o = r["observed"]
            obs = Observed(o.get("tool_calls") or [], o.get("usage"), o.get("usage_supported", True), o.get("error"))
            losses = compare(case.expected, obs)
            if r.get("parallel_disabled") and len(case.expected["tool_calls"]) > 1:
                losses = [x for x in losses if x.kind in ("lost_usage", "wrong_usage")]
            name = r.get("adapter", "external")
            meta.setdefault(name, r.get("versions") or {})
            rows.append(
                {
                    "adapter": name,
                    "case": case.id,
                    "protocol": case.protocol,
                    "provider": case.provider,
                    "features": list(case.features),
                    "source": case.source["url"],
                    "losses": [x.to_dict() for x in losses],
                    "observed": o,
                    "usage_checked": obs.usage_supported,
                }
            )
    if not rows:
        print("no observations", file=sys.stderr)
        return 2
    rep = summarize(rows, meta)
    if ns.json:
        with open(ns.json, "w", encoding="utf-8") as fh:
            json.dump(rep, fh, indent=1, default=str)
    print_table(rep)
    return 1 if any(s["cases_with_loss"] for s in rep["adapters"].values()) else 0


def cmd_report(ns: argparse.Namespace) -> int:
    """Merge reports from several environments (one per dependency set) into one."""
    rows: list[dict[str, Any]] = []
    meta: dict[str, Any] = {}
    for f in ns.reports:
        with open(f, encoding="utf-8") as fh:
            rep = json.load(fh)
        rows += rep["rows"]
        for name, s in rep["adapters"].items():
            meta[name] = s["versions"]
    rep = summarize(rows, meta)
    if ns.json:
        with open(ns.json, "w", encoding="utf-8") as fh:
            json.dump(rep, fh, indent=1, default=str)
    print_table(rep)
    lossy = sum(s["cases_with_loss"] for s in rep["adapters"].values())
    return 1 if lossy else 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="llm-stream-check", description=__doc__)
    ap.add_argument("--version", action="version", version=__version__)
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run", help="replay the corpus through installed frameworks; exit 1 on any loss")
    r.add_argument("--adapter", action="append", help="adapter name (repeatable); default: every installed one")
    r.add_argument("--protocol", action="append", choices=corpus.PROTOCOLS)
    r.add_argument("--case", action="append")
    r.add_argument("--json", help="write the full report here")
    r.add_argument("--include-opt-in", action="store_true", help="also replay beta / opt-in stream shapes")
    r.set_defaults(fn=cmd_run)
    s = sub.add_parser("list", help="what the corpus covers")
    s.add_argument("-v", "--verbose", action="store_true")
    s.add_argument("--include-opt-in", action="store_true")
    s.set_defaults(fn=cmd_list)
    sub.add_parser("adapters", help="adapters and whether their framework is installed").set_defaults(fn=cmd_adapters)
    v = sub.add_parser("serve", help="serve the corpus over HTTP for a harness in another language")
    v.add_argument("--port", type=int, default=8765)
    v.add_argument("--include-opt-in", action="store_true")
    v.set_defaults(fn=cmd_serve)
    c = sub.add_parser("check", help="check a JSONL of {case, observed} from another harness")
    c.add_argument("file")
    c.add_argument("--json", help="write the full report here")
    c.set_defaults(fn=cmd_check)
    m = sub.add_parser("report", help="merge --json reports from several environments; exit 1 on any loss")
    m.add_argument("reports", nargs="+")
    m.add_argument("--json")
    m.set_defaults(fn=cmd_report)
    ns = ap.parse_args(argv)
    rc: int = ns.fn(ns)
    return rc


if __name__ == "__main__":
    sys.exit(main())
