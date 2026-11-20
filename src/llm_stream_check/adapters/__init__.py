"""Framework adapters.

An adapter drives one framework's own streaming code path against the replay server and
reports what that framework handed its caller: the tool calls (name, arguments, id) and the
token usage. Adapters never post-process the framework's result beyond reading its public
fields, so a loss in the report is a loss the framework's users get.

Each adapter is ``run(case, base_url) -> Observed`` and is registered in ``REGISTRY`` with
the protocols it speaks and the distributions whose versions go in the report.
"""

from __future__ import annotations

import importlib
from collections.abc import Callable
from dataclasses import dataclass

from ..compare import Observed
from ..corpus import Case


@dataclass(frozen=True)
class Adapter:
    name: str
    module: str
    func: str
    protocols: tuple[str, ...]
    dists: tuple[str, ...]
    what: str

    def load(self) -> Callable[[Case, str], Observed]:
        mod = importlib.import_module(f"{__name__}.{self.module}")
        fn: Callable[[Case, str], Observed] = getattr(mod, self.func)
        return fn


_A = Adapter
REGISTRY: dict[str, Adapter] = {
    a.name: a
    for a in [
        _A(
            "reference",
            "reference",
            "run",
            ("openai-chat", "openai-responses", "anthropic", "gemini"),
            (),
            "llm-stream-check's own parser over HTTP (proves the replay path; needs no framework)",
        ),
        _A(
            "openai-python.chat",
            "openai_sdk",
            "chat",
            ("openai-chat",),
            ("openai",),
            "client.chat.completions.stream(...).get_final_completion()",
        ),
        _A(
            "openai-python.responses",
            "openai_sdk",
            "responses",
            ("openai-responses",),
            ("openai",),
            "client.responses.stream(...).get_final_response()",
        ),
        _A(
            "anthropic-python",
            "anthropic_sdk",
            "messages",
            ("anthropic",),
            ("anthropic",),
            "client.messages.stream(...).get_final_message()",
        ),
        _A(
            "google-genai",
            "google_genai",
            "stream",
            ("gemini",),
            ("google-genai",),
            "client.models.generate_content_stream(...), chunk.function_calls from every chunk",
        ),
        _A(
            "litellm",
            "litellm_",
            "completion",
            ("openai-chat", "anthropic", "gemini"),
            ("litellm",),
            "litellm.completion(stream=True) + litellm.stream_chunk_builder(chunks)",
        ),
        _A(
            "litellm.responses",
            "litellm_",
            "responses",
            ("openai-responses",),
            ("litellm",),
            "litellm.responses(stream=True), response.completed event",
        ),
        _A(
            "langchain-openai",
            "langchain_",
            "openai_chat",
            ("openai-chat",),
            ("langchain-openai", "langchain-core"),
            "ChatOpenAI(stream_usage=True).bind_tools(...).stream(), chunks summed",
        ),
        _A(
            "langchain-openai.responses",
            "langchain_",
            "openai_responses",
            ("openai-responses",),
            ("langchain-openai", "langchain-core"),
            "ChatOpenAI(use_responses_api=True).stream(), chunks summed",
        ),
        _A(
            "langchain-anthropic",
            "langchain_",
            "anthropic",
            ("anthropic",),
            ("langchain-anthropic", "langchain-core"),
            "ChatAnthropic(stream_usage=True).bind_tools(...).stream(), chunks summed",
        ),
        _A(
            "langchain-google-genai",
            "langchain_",
            "google",
            ("gemini",),
            ("langchain-google-genai", "langchain-core"),
            "ChatGoogleGenerativeAI.bind_tools(...).stream(), chunks summed",
        ),
        _A(
            "llama-index-openai",
            "llama_index_",
            "openai",
            ("openai-chat",),
            ("llama-index-llms-openai", "llama-index-core"),
            "OpenAI.stream_chat_with_tools(), last response, get_tool_calls_from_response()",
        ),
        _A(
            "llama-index-anthropic",
            "llama_index_",
            "anthropic",
            ("anthropic",),
            ("llama-index-llms-anthropic", "llama-index-core"),
            "Anthropic.stream_chat_with_tools(), last response, get_tool_calls_from_response()",
        ),
        _A(
            "llama-index-google-genai",
            "llama_index_",
            "google",
            ("gemini",),
            ("llama-index-llms-google-genai", "llama-index-core"),
            "GoogleGenAI.stream_chat_with_tools(), last response, get_tool_calls_from_response()",
        ),
        _A(
            "pydantic-ai.openai-chat",
            "pydantic_ai_",
            "openai_chat",
            ("openai-chat",),
            ("pydantic-ai-slim",),
            "OpenAIChatModel.request_stream(), stream.get() / stream.usage()",
        ),
        _A(
            "pydantic-ai.openai-responses",
            "pydantic_ai_",
            "openai_responses",
            ("openai-responses",),
            ("pydantic-ai-slim",),
            "OpenAIResponsesModel.request_stream(), stream.get() / stream.usage()",
        ),
        _A(
            "pydantic-ai.anthropic",
            "pydantic_ai_",
            "anthropic",
            ("anthropic",),
            ("pydantic-ai-slim",),
            "AnthropicModel.request_stream(), stream.get() / stream.usage()",
        ),
        _A(
            "pydantic-ai.google",
            "pydantic_ai_",
            "google",
            ("gemini",),
            ("pydantic-ai-slim",),
            "GoogleModel.request_stream(), stream.get() / stream.usage()",
        ),
        _A(
            "openai-agents.chat",
            "openai_agents_",
            "chat",
            ("openai-chat",),
            ("openai-agents",),
            "OpenAIChatCompletionsModel.stream_response(), response.completed event",
        ),
        _A(
            "openai-agents.responses",
            "openai_agents_",
            "responses",
            ("openai-responses",),
            ("openai-agents",),
            "OpenAIResponsesModel.stream_response(), response.completed event",
        ),
        _A(
            "haystack.openai",
            "haystack_",
            "openai",
            ("openai-chat",),
            ("haystack-ai",),
            "OpenAIChatGenerator(streaming_callback=...).run(), replies[0].tool_calls",
        ),
        _A(
            "haystack.anthropic",
            "haystack_",
            "anthropic",
            ("anthropic",),
            ("anthropic-haystack", "haystack-ai"),
            "AnthropicChatGenerator(streaming_callback=...).run(), replies[0].tool_calls",
        ),
        _A(
            "haystack.google-genai",
            "haystack_",
            "google",
            ("gemini",),
            ("google-genai-haystack", "haystack-ai"),
            "GoogleGenAIChatGenerator(streaming_callback=...).run(), replies[0].tool_calls",
        ),
        _A(
            "autogen.openai",
            "autogen_",
            "openai",
            ("openai-chat",),
            ("autogen-ext", "autogen-core"),
            "OpenAIChatCompletionClient.create_stream(), final CreateResult",
        ),
        _A(
            "autogen.anthropic",
            "autogen_",
            "anthropic",
            ("anthropic",),
            ("autogen-ext", "autogen-core"),
            "AnthropicChatCompletionClient.create_stream(), final CreateResult",
        ),
        _A(
            "smolagents.openai",
            "smolagents_",
            "openai",
            ("openai-chat",),
            ("smolagents",),
            "OpenAIServerModel.generate_stream() + agglomerate_stream_deltas()",
        ),
        _A(
            "smolagents.litellm",
            "smolagents_",
            "litellm",
            ("openai-chat", "anthropic", "gemini"),
            ("smolagents", "litellm"),
            "LiteLLMModel.generate_stream() + agglomerate_stream_deltas()",
        ),
        _A(
            "crewai",
            "crewai_",
            "llm",
            ("openai-chat", "anthropic", "gemini"),
            ("crewai",),
            "crewai.LLM(stream=True).call(messages, tools=...) without available_functions",
        ),
        _A(
            "semantic-kernel.openai",
            "semantic_kernel_",
            "openai",
            ("openai-chat",),
            ("semantic-kernel",),
            "OpenAIChatCompletion.get_streaming_chat_message_contents(), chunks summed",
        ),
        _A(
            "agent-framework.openai",
            "agent_framework_",
            "openai",
            ("openai-chat",),
            ("agent-framework-openai", "agent-framework-core"),
            "RawOpenAIChatCompletionClient.get_response(stream=True).get_final_response()",
        ),
        _A(
            "agent-framework.anthropic",
            "agent_framework_",
            "anthropic",
            ("anthropic",),
            ("agent-framework-anthropic", "agent-framework-core"),
            "RawAnthropicClient.get_response(stream=True).get_final_response()",
        ),
        _A(
            "google-adk.litellm",
            "google_adk_",
            "litellm",
            ("openai-chat", "anthropic", "gemini"),
            ("google-adk", "litellm"),
            "LiteLlm.generate_content_async(stream=True), final aggregated LlmResponse",
        ),
        _A(
            "google-adk.gemini",
            "google_adk_",
            "gemini",
            ("gemini",),
            ("google-adk",),
            "Gemini.generate_content_async(stream=True), non-partial LlmResponses",
        ),
        _A(
            "strands.openai",
            "strands_",
            "openai",
            ("openai-chat",),
            ("strands-agents",),
            "OpenAIModel.stream() through strands.event_loop.streaming.process_stream()",
        ),
        _A(
            "strands.anthropic",
            "strands_",
            "anthropic",
            ("anthropic",),
            ("strands-agents",),
            "AnthropicModel.stream() through strands.event_loop.streaming.process_stream()",
        ),
        _A(
            "strands.gemini",
            "strands_",
            "gemini",
            ("gemini",),
            ("strands-agents",),
            "GeminiModel.stream() through strands.event_loop.streaming.process_stream()",
        ),
        _A(
            "strands.litellm",
            "strands_",
            "litellm",
            ("openai-chat",),
            ("strands-agents", "litellm"),
            "LiteLLMModel.stream() through strands.event_loop.streaming.process_stream()",
        ),
        _A(
            "agno.openai",
            "agno_",
            "openai",
            ("openai-chat",),
            ("agno",),
            "Agent(model=OpenAIChat, tools=[...], stream=True).run(), tools the agent executed",
        ),
        _A(
            "agno.anthropic",
            "agno_",
            "anthropic",
            ("anthropic",),
            ("agno",),
            "Agent(model=Claude, tools=[...], stream=True).run(), tools the agent executed",
        ),
        _A(
            "llm.openai",
            "llm_",
            "openai",
            ("openai-chat",),
            ("llm",),
            "llm model.prompt(tools=..., stream=True), response.tool_calls()",
        ),
        _A(
            "llm.anthropic",
            "llm_",
            "anthropic",
            ("anthropic",),
            ("llm", "llm-anthropic"),
            "llm model.prompt(tools=..., stream=True), response.tool_calls()",
        ),
    ]
}
