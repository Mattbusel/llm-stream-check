from __future__ import annotations

from ..compare import Observed
from ..corpus import Case
from ._common import KEY, PROMPT, anthropic_tools, call, model, usage


def messages(case: Case, base: str) -> Observed:
    import anthropic

    client = anthropic.Anthropic(base_url=base, api_key=KEY, max_retries=0)
    with client.messages.stream(
        model=model(case, "claude-sonnet-4-5"),
        max_tokens=1024,
        messages=[{"role": "user", "content": PROMPT}],
        tools=anthropic_tools(case),  # type: ignore[arg-type]
    ) as s:
        final = s.get_final_message()
    calls = [call(b.name, b.input, b.id) for b in final.content if b.type == "tool_use"]
    return Observed(calls, usage(final.usage.input_tokens, final.usage.output_tokens))
