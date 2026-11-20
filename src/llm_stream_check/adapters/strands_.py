from __future__ import annotations

import asyncio
from typing import Any

from ..compare import Observed
from ..corpus import Case
from ._common import KEY, PROMPT, call, schema, usage


async def _stream(model: Any, case: Case) -> Observed:
    from strands.event_loop.streaming import process_stream

    specs = [{"name": n, "description": n, "inputSchema": {"json": schema()}} for n in case.tool_names]
    msgs = [{"role": "user", "content": [{"text": PROMPT}]}]
    final = None
    async for ev in process_stream(model.stream(msgs, specs)):
        if isinstance(ev, dict) and "stop" in ev:
            final = ev["stop"]
    if final is None:
        return Observed([], None, error="no stop event surfaced")
    _, message, u, _ = final
    calls = [
        call(b["toolUse"]["name"], b["toolUse"].get("input"), b["toolUse"].get("toolUseId"))
        for b in message.get("content", [])
        if "toolUse" in b
    ]
    return Observed(calls, usage(u.get("inputTokens"), u.get("outputTokens")) if u else None)


def openai(case: Case, base: str) -> Observed:
    from strands.models.openai import OpenAIModel

    m = OpenAIModel(client_args={"base_url": base + "/v1", "api_key": KEY, "max_retries": 0}, model_id="gpt-4o")
    return asyncio.run(_stream(m, case))


def anthropic(case: Case, base: str) -> Observed:
    from strands.models.anthropic import AnthropicModel

    m = AnthropicModel(
        client_args={"base_url": base, "api_key": KEY, "max_retries": 0}, model_id="claude-sonnet-4-5", max_tokens=1024
    )
    return asyncio.run(_stream(m, case))


def gemini(case: Case, base: str) -> Observed:
    from strands.models.gemini import GeminiModel

    m = GeminiModel(client_args={"api_key": KEY, "http_options": {"base_url": base + "/"}}, model_id="gemini-2.5-flash")
    return asyncio.run(_stream(m, case))


def litellm(case: Case, base: str) -> Observed:
    from strands.models.litellm import LiteLLMModel

    m = LiteLLMModel(client_args={"api_base": base + "/v1", "api_key": KEY}, model_id="openai/gpt-4o")
    return asyncio.run(_stream(m, case))
