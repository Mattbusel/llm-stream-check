from __future__ import annotations

import asyncio
from typing import Any

from ..compare import Observed
from ..corpus import Case
from ._common import KEY, PROMPT, call, schema, usage


def _request(case: Case, model_name: str) -> Any:
    from google.adk.models.llm_request import LlmRequest
    from google.genai import types

    decls = [types.FunctionDeclaration(name=n, description=n, parameters_json_schema=schema()) for n in case.tool_names]
    return LlmRequest(
        model=model_name,
        contents=[types.Content(role="user", parts=[types.Part(text=PROMPT)])],
        config=types.GenerateContentConfig(tools=[types.Tool(function_declarations=decls)]),
    )


async def _stream(llm: Any, case: Case, model_name: str) -> Observed:
    calls, last_usage = [], None
    async for r in llm.generate_content_async(_request(case, model_name), stream=True):
        if r.usage_metadata:
            last_usage = r.usage_metadata
        if getattr(r, "partial", False):
            continue  # ADK documents partial chunks as previews; the final response carries the calls
        for p in r.content.parts if r.content and r.content.parts else []:
            if p.function_call:
                calls.append(call(p.function_call.name, p.function_call.args or {}, p.function_call.id))
    u = usage(last_usage.prompt_token_count, last_usage.candidates_token_count) if last_usage else None
    return Observed(calls, u)


def litellm(case: Case, base: str) -> Observed:
    from google.adk.models.lite_llm import LiteLlm

    from .litellm_ import route

    m, api_base = route(case, base)
    return asyncio.run(_stream(LiteLlm(model=m, api_base=api_base, api_key=KEY), case, m))


def gemini(case: Case, base: str) -> Observed:
    import os

    from google.adk.models.google_llm import Gemini

    os.environ["GOOGLE_API_KEY"] = KEY
    return asyncio.run(_stream(Gemini(model="gemini-2.5-flash", base_url=base + "/"), case, "gemini-2.5-flash"))
