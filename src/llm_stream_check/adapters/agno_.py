"""agno runs tools inside its model loop, so this adapter drives a real Agent and records the
tool calls the agent actually executed. The replay server answers the agent's second request
with a recorded text-only answer, which ends the run."""

from __future__ import annotations

from typing import Any

from ..compare import Observed
from ..corpus import Case
from ._common import KEY, PROMPT, call, schema


def _run(model: Any, case: Case) -> Observed:
    from agno.agent import Agent
    from agno.tools import Function

    executed: list[dict[str, Any]] = []

    def make(name: str) -> Any:
        def fn(**kwargs: Any) -> str:
            executed.append(call(name, kwargs))
            return "ok"

        return fn

    tools = [
        Function(name=n, description=n, parameters=schema(), entrypoint=make(n), skip_entrypoint_processing=True)
        for n in case.tool_names
    ]
    agent = Agent(model=model, tools=tools, telemetry=False, tool_call_limit=len(case.expected["tool_calls"]) + 4)
    for _ in agent.run(PROMPT, stream=True):
        pass
    # Usage here would sum both model calls of the loop, so it is not compared.
    return Observed(executed, None, usage_supported=False)


def openai(case: Case, base: str) -> Observed:
    from agno.models.openai import OpenAIChat

    return _run(OpenAIChat(id="gpt-4o", base_url=base + "/v1", api_key=KEY, max_retries=0), case)


def anthropic(case: Case, base: str) -> Observed:
    from agno.models.anthropic import Claude

    return _run(Claude(id="claude-sonnet-4-5", api_key=KEY, client_params={"base_url": base, "max_retries": 0}), case)
