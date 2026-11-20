"""Reference accumulators: what a recorded stream actually says, per provider protocol.

Each function takes the JSON payloads of one streamed response and returns the tool calls
the model made and the usage the provider reported. These are the expected values every
framework is checked against, so they follow the provider's documented wire format only:

* OpenAI Chat Completions: ``choices[].delta.tool_calls[]`` fragments keyed by ``index``;
  the first fragment of a call carries ``id`` and ``function.name``, later ones append to
  ``function.arguments``. With ``stream_options.include_usage`` the last chunk has
  ``choices: []`` and a ``usage`` object.
* OpenAI Responses: ``response.output_item.done`` carries each finished ``function_call``
  item (``call_id``, ``name``, ``arguments``); ``response.completed`` carries ``usage``.
* Anthropic Messages: ``content_block_start`` with a ``tool_use`` block, then
  ``input_json_delta`` fragments for that block ``index`` until ``content_block_stop``.
  Input tokens arrive in ``message_start`` (and may be restated in ``message_delta``),
  output tokens are cumulative in ``message_delta``.
* Gemini ``streamGenerateContent``: every ``functionCall`` part is a complete call;
  ``usageMetadata`` on the last chunk is the final count.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ToolCall:
    name: str
    arguments: Any
    id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {"id": self.id, "name": self.name, "arguments": self.arguments}


@dataclass
class Result:
    tool_calls: list[ToolCall] = field(default_factory=list)
    input_tokens: int | None = None
    output_tokens: int | None = None
    # Gemini reports thinking tokens apart from candidates; frameworks may fold them in.
    output_tokens_alt: int | None = None
    # Anthropic reports cache reads and writes apart from input_tokens; frameworks may fold them in.
    input_tokens_alt: int | None = None

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {
            "tool_calls": [t.to_dict() for t in self.tool_calls],
            "usage": {"input_tokens": self.input_tokens, "output_tokens": self.output_tokens},
        }
        if self.output_tokens_alt is not None:
            d["usage"]["output_tokens_alt"] = self.output_tokens_alt
        if self.input_tokens_alt is not None:
            d["usage"]["input_tokens_alt"] = self.input_tokens_alt
        return d


def parse_args(raw: Any) -> Any:
    """Arguments as JSON. An empty string is ``{}`` (a call with no arguments)."""
    if isinstance(raw, (dict, list)):
        return raw
    if raw is None or (isinstance(raw, str) and raw.strip() == ""):
        return {}
    try:
        return json.loads(raw)
    except (TypeError, json.JSONDecodeError):
        return {"__unparseable__": raw}


def openai_chat(payloads: list[Any]) -> Result:
    res = Result()
    calls: dict[int, dict[str, Any]] = {}
    order: list[int] = []
    last_key: int | None = None
    for p in payloads:
        if not isinstance(p, dict):
            continue
        if p.get("usage"):
            u = p["usage"]
            res.input_tokens = u.get("prompt_tokens", res.input_tokens)
            res.output_tokens = u.get("completion_tokens", res.output_tokens)
        for ch in p.get("choices") or []:
            if ch.get("index", 0) != 0:
                continue
            for tc in (ch.get("delta") or {}).get("tool_calls") or []:
                fn = tc.get("function") or {}
                if "index" in tc and tc["index"] is not None:
                    key = int(tc["index"])
                elif tc.get("id") and (last_key is None or calls[last_key].get("id") not in (None, tc["id"])):
                    # Index-less providers: a new id starts a new call.
                    key = (max(calls) + 1) if calls else 0
                else:
                    key = last_key if last_key is not None else 0
                if key not in calls:
                    calls[key] = {"id": None, "name": "", "arguments": ""}
                    order.append(key)
                c = calls[key]
                if tc.get("id") and not c["id"]:
                    c["id"] = tc["id"]
                if fn.get("name"):
                    if not c["name"]:
                        c["name"] = fn["name"]
                if fn.get("arguments"):
                    c["arguments"] += fn["arguments"]
                last_key = key
    res.tool_calls = [ToolCall(calls[k]["name"], parse_args(calls[k]["arguments"]), calls[k]["id"]) for k in order]
    return res


def openai_responses(payloads: list[Any]) -> Result:
    res = Result()
    done: dict[str, dict[str, Any]] = {}
    order: list[str] = []
    completed_output: list[dict[str, Any]] | None = None
    for p in payloads:
        if not isinstance(p, dict):
            continue
        t = p.get("type", "")
        if t == "response.output_item.done":
            item = p.get("item") or {}
            if item.get("type") == "function_call":
                k = str(item.get("id") or item.get("call_id") or len(order))
                if k not in done:
                    order.append(k)
                done[k] = item
        elif t in ("response.completed", "response.incomplete"):
            r = p.get("response") or {}
            u = r.get("usage") or {}
            if u:
                res.input_tokens = u.get("input_tokens")
                res.output_tokens = u.get("output_tokens")
            completed_output = r.get("output")
    items = [done[k] for k in order]
    if not items and completed_output:
        items = [o for o in completed_output if o.get("type") == "function_call"]
    res.tool_calls = [ToolCall(i.get("name", ""), parse_args(i.get("arguments")), i.get("call_id")) for i in items]
    return res


def anthropic(payloads: list[Any]) -> Result:
    res = Result()
    blocks: dict[int, dict[str, Any]] = {}
    order: list[int] = []
    cache = 0
    for p in payloads:
        if not isinstance(p, dict):
            continue
        t = p.get("type")
        if t == "message_start":
            u = (p.get("message") or {}).get("usage") or {}
            cache = (u.get("cache_read_input_tokens") or 0) + (u.get("cache_creation_input_tokens") or 0)
            if u.get("input_tokens") is not None:
                res.input_tokens = u["input_tokens"]
            if u.get("output_tokens") is not None:
                res.output_tokens = u["output_tokens"]
        elif t == "content_block_start":
            cb = p.get("content_block") or {}
            if cb.get("type") == "tool_use":
                i = p["index"]
                blocks[i] = {"id": cb.get("id"), "name": cb.get("name", ""), "json": "", "input": cb.get("input")}
                order.append(i)
        elif t == "content_block_delta":
            d = p.get("delta") or {}
            if d.get("type") == "input_json_delta" and p.get("index") in blocks:
                blocks[p["index"]]["json"] += d.get("partial_json") or ""
        elif t == "message_delta":
            u = p.get("usage") or {}
            if u.get("input_tokens") is not None:
                res.input_tokens = u["input_tokens"]
            if u.get("cache_read_input_tokens") is not None or u.get("cache_creation_input_tokens") is not None:
                cache = (u.get("cache_read_input_tokens") or 0) + (u.get("cache_creation_input_tokens") or 0)
            if u.get("output_tokens") is not None:
                res.output_tokens = u["output_tokens"]
    if cache and res.input_tokens is not None:
        res.input_tokens_alt = res.input_tokens + cache
    for i in order:
        b = blocks[i]
        args = parse_args(b["json"]) if b["json"].strip() else (b["input"] or {})
        res.tool_calls.append(ToolCall(b["name"], args, b["id"]))
    return res


def gemini(payloads: list[Any]) -> Result:
    res = Result()
    for p in payloads:
        if not isinstance(p, dict):
            continue
        for cand in (p.get("candidates") or [])[:1]:
            for part in (cand.get("content") or {}).get("parts") or []:
                fc = part.get("functionCall")
                if fc and fc.get("name"):
                    res.tool_calls.append(ToolCall(fc["name"], fc.get("args") or {}, fc.get("id")))
        u = p.get("usageMetadata")
        if u:
            res.input_tokens = u.get("promptTokenCount", res.input_tokens)
            cand_tokens = u.get("candidatesTokenCount")
            thoughts = u.get("thoughtsTokenCount")
            if cand_tokens is not None:
                res.output_tokens = cand_tokens
                res.output_tokens_alt = cand_tokens + thoughts if thoughts else None
    return res


PROTOCOLS = {
    "openai-chat": openai_chat,
    "openai-responses": openai_responses,
    "anthropic": anthropic,
    "gemini": gemini,
}


def detect(payloads: list[Any]) -> str | None:
    for p in payloads:
        if not isinstance(p, dict):
            continue
        if p.get("object") == "chat.completion.chunk":
            return "openai-chat"
        t = str(p.get("type", ""))
        if t.startswith("response."):
            return "openai-responses"
        if t in ("message_start", "content_block_start", "content_block_delta", "message_delta"):
            return "anthropic"
        if "candidates" in p or "usageMetadata" in p:
            return "gemini"
    return None


def expected(protocol: str, payloads: list[Any]) -> Result:
    return PROTOCOLS[protocol](payloads)
