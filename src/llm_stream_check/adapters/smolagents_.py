from __future__ import annotations

from typing import Any

from ..compare import Observed
from ..corpus import Case
from ._common import KEY, PROMPT, call, model, usage


def _tools(case: Case) -> list[Any]:
    from smolagents import Tool

    out = []
    for n in case.tool_names:
        cls = type(
            f"T_{abs(hash(n))}",
            (Tool,),
            {
                "name": n,
                "description": n,
                "inputs": {},
                "output_type": "string",
                "forward": lambda self: "ok",
                "skip_forward_signature_validation": True,
            },
        )
        out.append(cls())
    return out


def _run(m: Any, case: Case) -> Observed:
    from smolagents.models import agglomerate_stream_deltas

    deltas = list(
        m.generate_stream(
            [{"role": "user", "content": [{"type": "text", "text": PROMPT}]}], tools_to_call_from=_tools(case)
        )
    )
    msg = agglomerate_stream_deltas(deltas)
    calls = [call(t.function.name, t.function.arguments, t.id) for t in (msg.tool_calls or [])]
    tu = msg.token_usage
    return Observed(calls, usage(tu.input_tokens, tu.output_tokens) if tu else None)


def openai(case: Case, base: str) -> Observed:
    from smolagents import OpenAIServerModel

    return _run(OpenAIServerModel(model_id="gpt-4o", api_base=base + "/v1", api_key=KEY), case)


def litellm(case: Case, base: str) -> Observed:
    import litellm as _litellm
    from smolagents import LiteLLMModel

    # smolagents forces tool_choice="required"; let LiteLLM downgrade it where a model map says no.
    _litellm.drop_params = True
    from .litellm_ import route

    m, api_base = route(case, base)
    return _run(LiteLLMModel(model_id=m, api_base=api_base, api_key=KEY), case)


__all__ = ["openai", "litellm", "model"]
