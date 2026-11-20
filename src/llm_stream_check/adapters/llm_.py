from __future__ import annotations

import os
from typing import Any

from ..compare import Observed
from ..corpus import Case
from ._common import KEY, PROMPT, call, schema, usage


def _run(model: Any, case: Case) -> Observed:
    import llm

    tools = [
        llm.Tool(name=n, description=n, input_schema=schema(), implementation=lambda **kw: "ok")
        for n in case.tool_names
    ]
    resp = model.prompt(PROMPT, tools=tools, stream=True, key=KEY)
    for _ in resp:
        pass
    calls = [call(t.name, t.arguments, t.tool_call_id) for t in resp.tool_calls()]
    u = resp.usage()
    return Observed(calls, usage(u.input, u.output) if u and (u.input or u.output) else None)


def openai(case: Case, base: str) -> Observed:
    import llm

    os.environ["OPENAI_BASE_URL"] = base + "/v1"
    return _run(llm.get_model("gpt-4o"), case)


def anthropic(case: Case, base: str) -> Observed:
    import llm

    os.environ["ANTHROPIC_BASE_URL"] = base
    return _run(llm.get_model("claude-sonnet-4.5"), case)
