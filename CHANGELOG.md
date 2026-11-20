# Changelog

## 0.1.0 (2026-11-20)

First release.

Why: agent frameworks key streamed tool calls on fields some providers never send, so parallel calls get merged, dropped or crash the run, and token counts get added up twice or not read at all. Nothing in their test suites replays a real provider stream, so these bugs ship. This release is the replay.

- 243 recorded provider streams (OpenAI Chat Completions, OpenAI Responses, Anthropic Messages, Gemini), each pinned to the public file and commit it came from, with the reference result for each.
- `llm-stream-check run`: replays the corpus through every installed framework's own streaming code and exits 1 on any dropped, merged, corrupted or phantom tool call, wrong call id, lost or wrong usage, or crash. Exits 2 when an adapter you asked for is not installed or nothing ran.
- 41 Python adapters (openai, anthropic, google-genai, LiteLLM, LangChain, LlamaIndex, Pydantic AI, OpenAI Agents SDK, Haystack, AutoGen, smolagents, CrewAI, Semantic Kernel, Microsoft Agent Framework, Google ADK, Strands, agno, llm) plus a built-in `reference` adapter that needs no framework.
- `serve` and `check` for harnesses in other languages; `harness/js/run.mjs` covers the Vercel AI SDK, openai-node, anthropic-sdk-typescript and LangChain.js.
- `report` merges reports from several environments. Results for 48 adapters: docs/results.md.
