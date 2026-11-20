from __future__ import annotations

from ..compare import Observed
from ..corpus import Case
from ._common import KEY, PROMPT, call, model, openai_tools, responses_tools, usage


def chat(case: Case, base: str) -> Observed:
    import openai

    client = openai.OpenAI(base_url=base + "/v1", api_key=KEY, max_retries=0)
    with client.chat.completions.stream(
        model=model(case, "gpt-4o"),
        messages=[{"role": "user", "content": PROMPT}],
        tools=openai_tools(case),
        stream_options={"include_usage": True},  # type: ignore[arg-type]
    ) as s:
        final = s.get_final_completion()
    msg = final.choices[0].message if final.choices else None
    calls = [call(t.function.name, t.function.arguments, t.id) for t in (msg.tool_calls or [])] if msg else []
    u = final.usage
    return Observed(calls, usage(u.prompt_tokens, u.completion_tokens) if u else None)


def responses(case: Case, base: str) -> Observed:
    import openai

    client = openai.OpenAI(base_url=base + "/v1", api_key=KEY, max_retries=0)
    with client.responses.stream(model=model(case, "gpt-4o"), input=PROMPT, tools=responses_tools(case)) as s:  # type: ignore[arg-type]
        final = s.get_final_response()
    calls = [call(o.name, o.arguments, o.call_id) for o in final.output if o.type == "function_call"]
    u = final.usage
    return Observed(calls, usage(u.input_tokens, u.output_tokens) if u else None)
