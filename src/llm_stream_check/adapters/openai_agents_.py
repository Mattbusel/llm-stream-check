from __future__ import annotations

import asyncio
from typing import Any

from ..compare import Observed
from ..corpus import Case
from ._common import KEY, PROMPT, call, model, schema, usage


async def _stream(m: Any, case: Case) -> Observed:
    from agents import FunctionTool, ModelSettings
    from agents.models.interface import ModelTracing

    async def invoke(ctx: Any, args: str) -> str:
        return "ok"

    tools = [
        FunctionTool(
            name=n, description=n, params_json_schema=schema(), on_invoke_tool=invoke, strict_json_schema=False
        )
        for n in case.tool_names
    ]
    final = None
    async for ev in m.stream_response(
        None, PROMPT, ModelSettings(include_usage=True), tools, None, [], ModelTracing.DISABLED
    ):
        if getattr(ev, "type", "") in ("response.completed", "response.incomplete"):
            final = ev.response
    if final is None:
        return Observed([], None, error="no response.completed event surfaced")
    calls = [call(o.name, o.arguments, o.call_id) for o in final.output if getattr(o, "type", "") == "function_call"]
    u = final.usage
    return Observed(calls, usage(u.input_tokens, u.output_tokens) if u else None)


def chat(case: Case, base: str) -> Observed:
    from agents import OpenAIChatCompletionsModel
    from openai import AsyncOpenAI

    client = AsyncOpenAI(base_url=base + "/v1", api_key=KEY, max_retries=0)
    return asyncio.run(_stream(OpenAIChatCompletionsModel(model(case, "gpt-4o"), client), case))


def responses(case: Case, base: str) -> Observed:
    from agents import OpenAIResponsesModel
    from openai import AsyncOpenAI

    client = AsyncOpenAI(base_url=base + "/v1", api_key=KEY, max_retries=0)
    return asyncio.run(_stream(OpenAIResponsesModel(model(case, "gpt-4o"), client), case))
