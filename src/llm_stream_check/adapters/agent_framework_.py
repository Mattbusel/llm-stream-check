from __future__ import annotations

import asyncio
from typing import Any

from ..compare import Observed
from ..corpus import Case
from ._common import KEY, PROMPT, call, schema, usage


async def _stream(client: Any, case: Case) -> Observed:
    from agent_framework import FunctionTool, Message

    tools = [FunctionTool(name=n, description=n, func=lambda **kw: "ok", input_model=schema()) for n in case.tool_names]
    stream = client.get_response([Message(role="user", contents=[PROMPT])], stream=True, options={"tools": tools})
    async for _ in stream:
        pass
    final = await stream.get_final_response()
    calls = []
    for m in final.messages:
        for c in m.contents:
            # Server-side tools the provider ran itself are marked hosted / informational_only.
            if getattr(c, "type", "") == "function_call" and not (
                getattr(c, "hosted", False) or getattr(c, "informational_only", False)
            ):
                calls.append(call(c.name, c.arguments, c.call_id))
    u = final.usage_details or {}
    return Observed(calls, usage(u.get("input_token_count"), u.get("output_token_count")))


def openai(case: Case, base: str) -> Observed:
    from agent_framework.openai import RawOpenAIChatCompletionClient

    client = RawOpenAIChatCompletionClient(model="gpt-4o", api_key=KEY, base_url=base + "/v1")
    return asyncio.run(_stream(client, case))


def anthropic(case: Case, base: str) -> Observed:
    from agent_framework_anthropic._chat_client import RawAnthropicClient

    client = RawAnthropicClient(model="claude-sonnet-4-5", api_key=KEY, base_url=base)
    return asyncio.run(_stream(client, case))
