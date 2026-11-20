from __future__ import annotations

from ..compare import Observed
from ..corpus import Case
from ._common import KEY, PROMPT, call, model, schema, usage


def client(base: str):  # type: ignore[no-untyped-def]
    from google import genai
    from google.genai import types

    return genai.Client(api_key=KEY, http_options=types.HttpOptions(base_url=base + "/"))


def tools(case: Case):  # type: ignore[no-untyped-def]
    from google.genai import types

    return [
        types.Tool(
            function_declarations=[
                types.FunctionDeclaration(name=n, description=n, parameters_json_schema=schema())
                for n in case.tool_names
            ]
        )
    ]


def stream(case: Case, base: str) -> Observed:
    from google.genai import types

    c = client(base)
    calls, last = [], None
    cfg = types.GenerateContentConfig(
        tools=tools(case), automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True)
    )
    for chunk in c.models.generate_content_stream(model=model(case, "gemini-2.5-flash"), contents=PROMPT, config=cfg):
        for fc in chunk.function_calls or []:
            calls.append(call(fc.name, fc.args or {}, fc.id))
        if chunk.usage_metadata:
            last = chunk.usage_metadata
    return Observed(calls, usage(last.prompt_token_count, last.candidates_token_count) if last else None)
