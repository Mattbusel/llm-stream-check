from __future__ import annotations

from ..compare import Observed
from ..corpus import Case
from ._common import KEY, PROMPT, call, model, openai_tools, responses_tools, usage


def route(case: Case, base: str) -> tuple[str, str]:
    if case.protocol == "anthropic":
        return "anthropic/" + model(case, "claude-sonnet-4-5"), base + "/v1/messages"
    if case.protocol == "gemini":
        return "gemini/" + model(case, "gemini-2.5-flash"), base
    return "openai/" + model(case, "gpt-4o"), base + "/v1"


def completion(case: Case, base: str) -> Observed:
    import litellm

    m, api_base = route(case, base)
    msgs = [{"role": "user", "content": PROMPT}]
    chunks = list(
        litellm.completion(
            model=m,
            api_base=api_base,
            api_key=KEY,
            messages=msgs,
            tools=openai_tools(case),
            stream=True,
            stream_options={"include_usage": True},
            max_tokens=1024,
            num_retries=0,
        )
    )
    final = litellm.stream_chunk_builder(chunks, messages=msgs)
    if final is None:
        return Observed([], None)
    msg = final.choices[0].message
    calls = [call(t.function.name, t.function.arguments, t.id) for t in (msg.tool_calls or [])]
    u = getattr(final, "usage", None)
    return Observed(calls, usage(u.prompt_tokens, u.completion_tokens) if u else None)


def responses(case: Case, base: str) -> Observed:
    import litellm

    final = None
    for ev in litellm.responses(
        model="openai/" + model(case, "gpt-4o"),
        api_base=base + "/v1",
        api_key=KEY,
        input=PROMPT,
        tools=responses_tools(case),
        stream=True,
    ):
        if getattr(ev, "type", "") in ("response.completed", "response.incomplete"):
            final = ev.response
    if final is None:
        return Observed([], None, error="no response.completed event surfaced")
    out = final.output if hasattr(final, "output") else final["output"]
    calls = []
    for o in out:
        t = o.get("type") if isinstance(o, dict) else getattr(o, "type", None)
        if t == "function_call":
            g = (lambda k: o.get(k)) if isinstance(o, dict) else (lambda k: getattr(o, k, None))
            calls.append(call(g("name"), g("arguments"), g("call_id")))
    u = getattr(final, "usage", None)
    return Observed(calls, usage(getattr(u, "input_tokens", None), getattr(u, "output_tokens", None)) if u else None)
