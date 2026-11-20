from __future__ import annotations

from typing import Any

from ..compare import Observed
from ..corpus import Case
from ._common import KEY, PROMPT, call, model, usage


def _tools(case: Case) -> list[Any]:
    from llama_index.core.tools import FunctionTool
    from pydantic import BaseModel

    class Args(BaseModel):
        pass

    def noop(**kwargs: Any) -> str:
        return "ok"

    return [FunctionTool.from_defaults(fn=noop, name=n, description=n, fn_schema=Args) for n in case.tool_names]


def _run(llm: Any, case: Case) -> Observed:
    last = None
    for r in llm.stream_chat_with_tools(_tools(case), user_msg=PROMPT, allow_parallel_tool_calls=True):
        last = r
    if last is None:
        return Observed([], None)
    sel = llm.get_tool_calls_from_response(last, error_on_no_tool_call=False)
    calls = [call(t.tool_name, t.tool_kwargs, t.tool_id) for t in sel]
    ak = dict(last.additional_kwargs or {})
    # The Anthropic integration puts usage on the message instead of the response.
    mu = (last.message.additional_kwargs or {}).get("usage") or {}
    if isinstance(mu, dict):
        ak.update({k: v for k, v in mu.items() if k not in ak})
    inp = ak.get("prompt_tokens", ak.get("input_tokens"))
    out = ak.get("completion_tokens", ak.get("output_tokens"))
    return Observed(calls, usage(inp, out))


def openai(case: Case, base: str) -> Observed:
    from llama_index.llms.openai import OpenAI

    llm = OpenAI(
        model="gpt-4o",
        api_base=base + "/v1",
        api_key=KEY,
        max_retries=0,
        additional_kwargs={"stream_options": {"include_usage": True}},
    )
    return _run(llm, case)


def anthropic(case: Case, base: str) -> Observed:
    from llama_index.llms.anthropic import Anthropic

    llm = Anthropic(model="claude-sonnet-4-5", base_url=base, api_key=KEY, max_retries=0)
    return _run(llm, case)


def google(case: Case, base: str) -> Observed:
    from google.genai import types
    from llama_index.llms.google_genai import GoogleGenAI

    llm = GoogleGenAI(
        model=model(case, "gemini-2.5-flash"),
        api_key=KEY,
        max_retries=0,
        http_options=types.HttpOptions(base_url=base + "/"),
    )
    return _run(llm, case)
