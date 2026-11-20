"""Helpers shared by adapters."""

from __future__ import annotations

import json
from typing import Any

from ..corpus import Case

PROMPT = "Use the tools."
KEY = "sk-llm-stream-check"


def schema() -> dict[str, Any]:
    # No additionalProperties: Gemini's API rejects it, and no provider needs it to send arguments.
    return {"type": "object", "properties": {}}


def openai_tools(case: Case) -> list[dict[str, Any]]:
    return [
        {"type": "function", "function": {"name": n, "description": n, "parameters": schema()}} for n in case.tool_names
    ]


def responses_tools(case: Case) -> list[dict[str, Any]]:
    return [
        {"type": "function", "name": n, "description": n, "parameters": schema(), "strict": False}
        for n in case.tool_names
    ]


def anthropic_tools(case: Case) -> list[dict[str, Any]]:
    return [{"name": n, "description": n, "input_schema": schema()} for n in case.tool_names]


def model(case: Case, default: str) -> str:
    """One fixed model name per protocol: frameworks switch code paths on model names, and the
    recorded model names (some unreleased, some on other providers) would send them down paths
    that have nothing to do with the stream."""
    return default


def call(name: Any, arguments: Any, call_id: Any = None) -> dict[str, Any]:
    if isinstance(arguments, (bytes, bytearray)):
        arguments = arguments.decode()
    if hasattr(arguments, "model_dump"):
        arguments = arguments.model_dump()
    return {"name": name, "arguments": arguments, "id": call_id}


def usage(inp: Any, out: Any) -> dict[str, int | None] | None:
    if inp is None and out is None:
        return None
    return {
        "input_tokens": int(inp) if inp is not None else None,
        "output_tokens": int(out) if out is not None else None,
    }


def dumps(x: Any) -> str:
    return json.dumps(x, default=str)
