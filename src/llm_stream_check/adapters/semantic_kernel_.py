from __future__ import annotations

import asyncio
from typing import Any

from ..compare import Observed
from ..corpus import Case
from ._common import KEY, PROMPT, call, usage


async def _stream(case: Case, base: str) -> Observed:
    from openai import AsyncOpenAI
    from semantic_kernel import Kernel
    from semantic_kernel.connectors.ai.function_choice_behavior import FunctionChoiceBehavior
    from semantic_kernel.connectors.ai.open_ai import OpenAIChatCompletion, OpenAIChatPromptExecutionSettings
    from semantic_kernel.contents import ChatHistory, FunctionCallContent
    from semantic_kernel.functions import kernel_function

    kernel = Kernel()
    fns = []
    for n in case.tool_names:

        @kernel_function(name=n, description=n)
        def f() -> str:
            return "ok"

        fns.append(f)
    kernel.add_functions(plugin_name="t", functions=fns)
    svc = OpenAIChatCompletion(
        ai_model_id="gpt-4o", async_client=AsyncOpenAI(base_url=base + "/v1", api_key=KEY, max_retries=0)
    )
    settings = OpenAIChatPromptExecutionSettings(
        function_choice_behavior=FunctionChoiceBehavior.Auto(auto_invoke=False)
    )
    hist = ChatHistory()
    hist.add_user_message(PROMPT)
    full: Any = None
    async for chunks in svc.get_streaming_chat_message_contents(hist, settings, kernel=kernel):
        for c in chunks:
            full = c if full is None else full + c
    if full is None:
        return Observed([], None)
    calls = [
        call(i.function_name if not i.plugin_name else i.name, i.arguments, i.id)
        for i in full.items
        if isinstance(i, FunctionCallContent)
    ]
    u = (full.metadata or {}).get("usage")
    return Observed(
        calls, usage(getattr(u, "prompt_tokens", None), getattr(u, "completion_tokens", None)) if u else None
    )


def openai(case: Case, base: str) -> Observed:
    return asyncio.run(_stream(case, base))
