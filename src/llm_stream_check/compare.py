"""Compare what a framework surfaced from a stream with what the stream said."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

from .reference import parse_args

# Every kind below is a loss. The checker fails closed on any of them.
KINDS = (
    "dropped_tool_call",  # a call in the stream never reached the caller
    "merged_tool_calls",  # two or more calls came out as one
    "corrupted_tool_call",  # right number of calls, wrong name or arguments
    "phantom_tool_call",  # the caller got a call the stream never made
    "wrong_tool_call_id",  # the id the next turn must echo back is not the one the provider sent
    "lost_usage",  # the provider reported token usage and the caller got none
    "wrong_usage",  # the caller got usage that differs from what the provider reported
    "error",  # the framework raised on a recorded, well-formed stream
)


@dataclass
class Observed:
    """What a framework handed back. ``usage`` is None when the framework surfaced no usage;
    set ``usage_supported`` False only when the framework has no streaming usage API at all."""

    tool_calls: list[dict[str, Any]] = field(default_factory=list)
    usage: dict[str, int | None] | None = None
    usage_supported: bool = True
    error: str | None = None


@dataclass
class Loss:
    kind: str
    detail: str

    def to_dict(self) -> dict[str, str]:
        return {"kind": self.kind, "detail": self.detail}


def _norm(args: Any) -> Any:
    if isinstance(args, str):
        return parse_args(args)
    return args if args is not None else {}


def _key(c: dict[str, Any]) -> str:
    return json.dumps([c.get("name"), _norm(c.get("arguments"))], sort_keys=True, default=str)


def compare(expected: dict[str, Any], obs: Observed) -> list[Loss]:
    if obs.error:
        return [Loss("error", obs.error[:500])]
    losses: list[Loss] = []
    exp_calls = expected["tool_calls"]
    got = obs.tool_calls
    exp_keys = [_key(c) for c in exp_calls]
    got_keys = [_key(c) for c in got]
    remaining = list(got_keys)
    missing = []
    for i, k in enumerate(exp_keys):
        if k in remaining:
            remaining.remove(k)
        else:
            missing.append(i)
    extra = [g for g in remaining]
    if missing:
        names = [exp_calls[i]["name"] for i in missing]
        if len(got) < len(exp_calls) and _looks_merged(exp_calls, got):
            losses.append(
                Loss("merged_tool_calls", f"{len(exp_calls)} calls in the stream came out as {len(got)}: {_brief(got)}")
            )
        elif len(got) < len(exp_calls):
            losses.append(
                Loss("dropped_tool_call", f"{len(exp_calls)} calls in the stream, {len(got)} surfaced; missing {names}")
            )
        else:
            losses.append(
                Loss(
                    "corrupted_tool_call",
                    f"expected {_brief([exp_calls[i] for i in missing])}, got {_brief_keys(extra)}",
                )
            )
    elif extra:
        losses.append(Loss("phantom_tool_call", f"{len(extra)} call(s) the stream never made: {_brief_keys(extra)}"))
    if not missing and not extra:
        # Same calls; check the ids in order of appearance where the framework exposes them.
        for e, g in zip(_order(exp_calls, got), got, strict=True):
            gid = str(g.get("id")) if g.get("id") is not None else None
            # LiteLLM carries Gemini thought signatures inside the id and strips them on the way back.
            if gid and "__thought__" in gid:
                gid = gid.split("__thought__")[0]
            if e.get("id") and gid is not None and gid != e.get("id"):
                losses.append(
                    Loss("wrong_tool_call_id", f"{g.get('name')}: provider id {e['id']!r}, got {g.get('id')!r}")
                )
    if obs.usage_supported:
        eu = expected.get("usage") or {}
        if eu.get("input_tokens") is not None or eu.get("output_tokens") is not None:
            u = obs.usage
            if not u or (not u.get("input_tokens") and not u.get("output_tokens")):
                losses.append(
                    Loss(
                        "lost_usage",
                        f"provider reported {eu.get('input_tokens')} in / "
                        f"{eu.get('output_tokens')} out; framework surfaced none",
                    )
                )
            else:
                bad = []
                ins = {eu.get("input_tokens"), eu.get("input_tokens_alt")} - {None}
                if ins and u.get("input_tokens") not in ins:
                    bad.append(f"input {u.get('input_tokens')} != {eu['input_tokens']}")
                outs = {eu.get("output_tokens"), eu.get("output_tokens_alt")} - {None}
                if outs and u.get("output_tokens") not in outs:
                    bad.append(f"output {u.get('output_tokens')} != {eu.get('output_tokens')}")
                if bad:
                    losses.append(Loss("wrong_usage", "; ".join(bad)))
    return losses


def _order(exp_calls: list[dict[str, Any]], got: list[dict[str, Any]]) -> list[dict[str, Any]]:
    pool = list(exp_calls)
    out = []
    for g in got:
        k = _key(g)
        for e in pool:
            if _key(e) == k:
                out.append(e)
                pool.remove(e)
                break
    return out


def _looks_merged(exp_calls: list[dict[str, Any]], got: list[dict[str, Any]]) -> bool:
    exp_names = [c["name"] for c in exp_calls]
    exp_keys = {_key(c) for c in exp_calls}
    # Fewer calls than the stream made, and a surfaced call that matches none of them: the
    # missing calls went into it (often as arguments that no longer parse, or as {}).
    if any(_key(g) not in exp_keys for g in got):
        return True
    for g in got:
        name = str(g.get("name") or "")
        args = g.get("arguments")
        raw = args if isinstance(args, str) else json.dumps(args, default=str)
        if sum(1 for n in exp_names if n and n in name) > 1 and name not in exp_names:
            return True
        if isinstance(_norm(args), dict) and "__unparseable__" in _norm(args):
            return True
        if raw.count("}{") or raw.count("} {"):
            return True
    return False


def _brief(calls: list[dict[str, Any]]) -> str:
    return ", ".join(f"{c.get('name')}({json.dumps(_norm(c.get('arguments')), default=str)[:80]})" for c in calls)


def _brief_keys(keys: list[str]) -> str:
    return ", ".join(k[:120] for k in keys)
