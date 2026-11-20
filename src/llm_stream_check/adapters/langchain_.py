from __future__ import annotations

from typing import Any

from ..compare import Observed
from ..corpus import Case
from ._common import KEY, PROMPT, call, model, openai_tools, usage


def _gather(llm: Any, case: Case) -> Observed:
    gathered = None
    for chunk in llm.bind_tools(openai_tools(case)).stream(PROMPT):
        gathered = chunk if gathered is None else gathered + chunk
    if gathered is None:
        return Observed([], None)
    calls = [call(t["name"], t["args"], t.get("id")) for t in gathered.tool_calls]
    # Calls LangChain could not parse are kept apart, not dropped; count them as surfaced.
    calls += [call(t.get("name"), t.get("args"), t.get("id")) for t in getattr(gathered, "invalid_tool_calls", [])]
    um = gathered.usage_metadata
    return Observed(calls, usage(um.get("input_tokens"), um.get("output_tokens")) if um else None)


def openai_chat(case: Case, base: str) -> Observed:
    from langchain_openai import ChatOpenAI

    return _gather(
        ChatOpenAI(
            model=model(case, "gpt-4o"),
            base_url=base + "/v1",
            api_key=KEY,  # type: ignore[arg-type]
            stream_usage=True,
            max_retries=0,
        ),
        case,
    )


def openai_responses(case: Case, base: str) -> Observed:
    from langchain_openai import ChatOpenAI

    return _gather(
        ChatOpenAI(
            model=model(case, "gpt-4o"),
            base_url=base + "/v1",
            api_key=KEY,  # type: ignore[arg-type]
            use_responses_api=True,
            max_retries=0,
        ),
        case,
    )


def anthropic(case: Case, base: str) -> Observed:
    from langchain_anthropic import ChatAnthropic

    return _gather(
        ChatAnthropic(
            model=model(case, "claude-sonnet-4-5"),
            base_url=base,
            api_key=KEY,  # type: ignore[call-arg, arg-type]
            stream_usage=True,
            max_retries=0,
        ),
        case,
    )


def google(case: Case, base: str) -> Observed:
    from langchain_google_genai import ChatGoogleGenerativeAI

    llm = ChatGoogleGenerativeAI(
        model=model(case, "gemini-2.5-flash"),
        google_api_key=KEY,  # type: ignore[call-arg]
        base_url=base + "/",
        max_retries=0,
    )
    return _gather(llm, case)
