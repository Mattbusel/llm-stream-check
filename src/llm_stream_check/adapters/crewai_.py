from __future__ import annotations

import os
from typing import Any

from ..compare import Observed
from ..corpus import Case
from ._common import KEY, PROMPT, call, openai_tools, usage


def _calls(result: Any) -> list[dict[str, Any]]:
    out = []
    for t in result if isinstance(result, list) else []:
        if isinstance(t, dict):
            fn = t.get("function") or t
            out.append(call(fn.get("name"), fn.get("arguments", fn.get("args", fn.get("input"))), t.get("id")))
        else:
            fn = getattr(t, "function", None) or getattr(t, "function_call", None) or t
            args = next(
                (getattr(fn, k) for k in ("arguments", "args", "input") if getattr(fn, k, None) is not None), None
            )
            out.append(call(getattr(fn, "name", None), args, getattr(t, "id", None)))
    return out


def llm(case: Case, base: str) -> Observed:
    from crewai import LLM

    if case.protocol == "anthropic":
        m = LLM(model="anthropic/claude-sonnet-4-5", base_url=base, api_key=KEY, stream=True, max_tokens=1024)
    elif case.protocol == "gemini":
        os.environ["GOOGLE_GEMINI_BASE_URL"] = base + "/"
        m = LLM(model="gemini/gemini-2.5-flash", base_url=base, api_key=KEY, stream=True)
    else:
        m = LLM(model="openai/gpt-4o", base_url=base + "/v1", api_key=KEY, stream=True)
    result = m.call([{"role": "user", "content": PROMPT}], tools=openai_tools(case))  # type: ignore[arg-type]
    calls = _calls(result)
    u: Any = None
    try:
        s = m.get_token_usage_summary()
        u = usage(s.prompt_tokens, s.completion_tokens) if (s.prompt_tokens or s.completion_tokens) else None
    except Exception:  # noqa: BLE001 - no usage API on this version
        u = None
    return Observed(calls, u)
