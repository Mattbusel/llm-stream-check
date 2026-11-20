from __future__ import annotations

import asyncio
from typing import Any

from ..compare import Observed
from ..corpus import Case
from ._common import KEY, PROMPT, call, model, schema, usage


async def _stream(m: Any, case: Case) -> Observed:
    from pydantic_ai.messages import ModelRequest, ToolCallPart, UserPromptPart
    from pydantic_ai.models import ModelRequestParameters
    from pydantic_ai.tools import ToolDefinition

    params = ModelRequestParameters(
        function_tools=[ToolDefinition(name=n, description=n, parameters_json_schema=schema()) for n in case.tool_names]
    )
    msgs = [ModelRequest(parts=[UserPromptPart(PROMPT)])]
    async with m.request_stream(msgs, None, params) as s:
        async for _ in s:
            pass
        resp = s.get()
        u = s.usage() if callable(s.usage) else s.usage
    calls = [call(p.tool_name, p.args, p.tool_call_id) for p in resp.parts if isinstance(p, ToolCallPart)]
    return Observed(calls, usage(u.input_tokens, u.output_tokens))


def openai_chat(case: Case, base: str) -> Observed:
    from pydantic_ai.models.openai import OpenAIChatModel
    from pydantic_ai.providers.openai import OpenAIProvider

    m = OpenAIChatModel(model(case, "gpt-4o"), provider=OpenAIProvider(base_url=base + "/v1", api_key=KEY))
    return asyncio.run(_stream(m, case))


def openai_responses(case: Case, base: str) -> Observed:
    from pydantic_ai.models.openai import OpenAIResponsesModel
    from pydantic_ai.providers.openai import OpenAIProvider

    m = OpenAIResponsesModel(model(case, "gpt-4o"), provider=OpenAIProvider(base_url=base + "/v1", api_key=KEY))
    return asyncio.run(_stream(m, case))


def anthropic(case: Case, base: str) -> Observed:
    from pydantic_ai.models.anthropic import AnthropicModel
    from pydantic_ai.providers.anthropic import AnthropicProvider

    m = AnthropicModel(model(case, "claude-sonnet-4-5"), provider=AnthropicProvider(base_url=base, api_key=KEY))
    return asyncio.run(_stream(m, case))


def google(case: Case, base: str) -> Observed:
    from pydantic_ai.models.google import GoogleModel
    from pydantic_ai.providers.google import GoogleProvider

    m = GoogleModel(model(case, "gemini-2.5-flash"), provider=GoogleProvider(api_key=KEY, base_url=base + "/"))
    return asyncio.run(_stream(m, case))
