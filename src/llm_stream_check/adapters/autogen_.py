from __future__ import annotations

import asyncio
from typing import Any

from ..compare import Observed
from ..corpus import Case
from ._common import KEY, PROMPT, call, schema, usage

INFO = {
    "vision": False,
    "function_calling": True,
    "json_output": True,
    "family": "unknown",
    "structured_output": True,
    "multiple_system_messages": True,
}


async def _stream(client: Any, case: Case, **kw: Any) -> Observed:
    from autogen_core.models import CreateResult, UserMessage

    tools = [{"name": n, "description": n, "parameters": schema()} for n in case.tool_names]
    final = None
    async for item in client.create_stream([UserMessage(content=PROMPT, source="user")], tools=tools, **kw):
        if isinstance(item, CreateResult):
            final = item
    if final is None:
        return Observed([], None, error="no CreateResult surfaced")
    calls = [call(f.name, f.arguments, f.id) for f in final.content] if isinstance(final.content, list) else []
    u = final.usage
    return Observed(calls, usage(u.prompt_tokens, u.completion_tokens) if u else None)


def openai(case: Case, base: str) -> Observed:
    from autogen_ext.models.openai import OpenAIChatCompletionClient

    client = OpenAIChatCompletionClient(
        model="gpt-4o", base_url=base + "/v1", api_key=KEY, max_retries=0, model_info=INFO
    )
    return asyncio.run(_stream(client, case, include_usage=True))


def anthropic(case: Case, base: str) -> Observed:
    from autogen_ext.models.anthropic import AnthropicChatCompletionClient

    client = AnthropicChatCompletionClient(
        model="claude-sonnet-4-5", base_url=base, api_key=KEY, max_retries=0, model_info=INFO
    )
    return asyncio.run(_stream(client, case))
