from __future__ import annotations

import os
from typing import Any

from ..compare import Observed
from ..corpus import Case
from ._common import PROMPT, call, model, schema, usage


def _tools(case: Case) -> list[Any]:
    from haystack.tools import Tool

    return [Tool(name=n, description=n, parameters=schema(), function=lambda **kw: "ok") for n in case.tool_names]


def _run(gen: Any) -> Observed:
    from haystack.dataclasses import ChatMessage

    reply = gen.run(messages=[ChatMessage.from_user(PROMPT)])["replies"][0]
    calls = [call(t.tool_name, t.arguments, t.id) for t in reply.tool_calls]
    u = (reply.meta or {}).get("usage") or {}
    inp = u.get("prompt_tokens", u.get("input_tokens"))
    out = u.get("completion_tokens", u.get("output_tokens"))
    return Observed(calls, usage(inp, out))


def openai(case: Case, base: str) -> Observed:
    from haystack.components.generators.chat import OpenAIChatGenerator

    gen = OpenAIChatGenerator(
        model="gpt-4o",
        api_base_url=base + "/v1",
        streaming_callback=lambda c: None,
        tools=_tools(case),
        max_retries=0,
        generation_kwargs={"stream_options": {"include_usage": True}},
    )
    return _run(gen)


def anthropic(case: Case, base: str) -> Observed:
    os.environ["ANTHROPIC_BASE_URL"] = base
    from haystack_integrations.components.generators.anthropic import AnthropicChatGenerator

    gen = AnthropicChatGenerator(model="claude-sonnet-4-5", streaming_callback=lambda c: None, tools=_tools(case))
    return _run(gen)


def google(case: Case, base: str) -> Observed:
    os.environ["GOOGLE_GEMINI_BASE_URL"] = base + "/"
    from haystack_integrations.components.generators.google_genai import GoogleGenAIChatGenerator

    gen = GoogleGenAIChatGenerator(
        model=model(case, "gemini-2.5-flash"), streaming_callback=lambda c: None, tools=_tools(case)
    )
    return _run(gen)
