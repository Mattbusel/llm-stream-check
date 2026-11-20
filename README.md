# llm-stream-check

**Your agent didn't forget the tool call. Your stream parser threw it away.**

We replayed one recorded Gemini response through 21 OpenAI-compatible stream parsers. The response holds two parallel tool calls (`get_weather` for Taipei and for Kaohsiung), recorded from Google's OpenAI-compatible endpoint, the one Google [documents](https://ai.google.dev/gemini-api/docs/openai) for use with OpenAI client libraries. 16 of the 21 parsers lost something:

- **8 merged the two calls into one.** LiteLLM, OpenAI Agents SDK, AutoGen, CrewAI, LlamaIndex, Strands (both its OpenAI and LiteLLM models) and smolagents on LiteLLM handed back a single `get_weather` call whose arguments were `{"city":"Taipei"}{"city":"Kaohsiung"}`. That is not JSON. LlamaIndex also renamed the call `get_weatherget_weather`. Strands parsed the broken string to `{}` and handed on one call with no arguments.
- **1 dropped both.** agno ran neither tool.
- **5 crashed.** openai-python's `chat.completions.stream()`, openai-node, the Vercel AI SDK's `@ai-sdk/openai` chat model, Haystack and smolagents threw on the missing `index`.
- **2 kept the calls but tripled the bill.** LangChain and Pydantic AI reported 222 input tokens for a request that used 74, because Gemini repeats the running usage on every chunk and both frameworks add them up.

The cause is one field. OpenAI's stream tags every tool call fragment with an `index`. Gemini's OpenAI endpoint and Mistral leave it out. Most parsers key their accumulator on that index, so every call lands in slot `None` (or slot 0) and gets glued to the one before it. Nobody tested with a real response from the provider they claim to support. The agent logs show one tool call, the model gets blamed for "forgetting" the other, and the fix is a few lines in the parser.

It is not only missing indexes. LlamaIndex's OpenAI integration reads only the first tool call in each chunk ([`utils.py`: `tc_delta = tool_calls_delta[0]`](https://github.com/run-llama/llama_index/blob/99d7433/llama-index-integrations/llms/llama-index-llms-openai/llama_index/llms/openai/utils.py#L1107)), so a recorded Mistral response with three parallel calls in one chunk comes out as one. AutoGen's Anthropic client reports 699 input tokens for a request Anthropic billed at 1,630, because it never reads the input count Anthropic restates in `message_delta` when server-side tool search runs.

The same bug was in our own merged work before this: [rust-genai#347](https://github.com/jeremychone/rust-genai/pull/347) dropped every tool call after the first in a chunk.

## What it does

`llm-stream-check` replays **243 recorded provider streams** through your framework's own streaming code and fails on anything lost on the way:

| loss | meaning |
|---|---|
| `dropped_tool_call` | a call in the stream never reached your code |
| `merged_tool_calls` | two or more calls came out as one |
| `corrupted_tool_call` | right number of calls, wrong name or arguments |
| `phantom_tool_call` | your code got a call the model never made |
| `wrong_tool_call_id` | the id your next turn must send back is not the one the provider sent |
| `lost_usage` / `wrong_usage` | the provider reported token usage and your code got none, or a different number |
| `error` | the framework raised on a recorded, well-formed provider stream |

It fails closed: any loss, any crash, any adapter you asked for that is not installed, exits nonzero. There is no "warn" mode.

Every stream is a real recording, never a hand-written fixture. They come from cassettes and fixtures in public repos (Pydantic AI's VCR cassettes, the Vercel AI SDK's recorded chunk fixtures, openai-python's and anthropic-sdk-python's streaming snapshots, Simon Willison's llm-gemini and llm-anthropic cassettes), each kept byte for byte with a permalink to the file at a pinned commit. Fixtures whose names or ids show they were typed by hand (`msg_1`, `toolu_1`, "spliced", "malformed") are excluded. Files that hold several responses of one multi-step run are split back into one stream per response.

| protocol | streams | shapes covered |
|---|---:|---|
| OpenAI Chat Completions | 38 | parallel calls, arguments split mid-JSON, empty deltas, usage-only final chunk, calls with no `index`, several calls in one chunk, name and arguments in one chunk; OpenAI, Mistral, Groq, DeepSeek, xAI, Alibaba, Moonshot, OpenRouter, Gemini's OpenAI endpoint |
| OpenAI Responses | 26 | split arguments, reasoning items before the call (output index gaps); OpenAI, Azure, Bedrock, LM Studio, DeepSeek, the ChatGPT Codex backend |
| Anthropic Messages | 169 | parallel `tool_use`, split `input_json_delta`, empty deltas, `ping`, thinking blocks, tool blocks after text (index gaps), calls with no input, server tool search mixed with client tools |
| Gemini `streamGenerateContent` | 10 | calls across chunks, usage-only final chunk, thought signatures, calls with no arguments |

## Use it

```
pip install llm-stream-check
llm-stream-check adapters          # which frameworks it found in this environment
llm-stream-check run               # replay the corpus through every installed one; exit 1 on any loss
llm-stream-check run --adapter langchain-openai --json report.json
```

`run` starts a local replay server, points each framework's base URL at it and reads back only the framework's public result fields. No API key, no network, no model calls.

For a stack in another language, serve the corpus and check what your code produced:

```
llm-stream-check serve --port 8765 &
node harness/js/run.mjs http://127.0.0.1:8765 observed.jsonl   # Vercel AI SDK, openai-node, anthropic-sdk-typescript, LangChain.js
llm-stream-check check observed.jsonl --json report.json
```

In CI, run it in the environment your agent ships with. A framework upgrade that starts merging calls fails the build instead of showing up as an agent that "sometimes forgets".

## Results

48 adapters across 22 projects (Python and JavaScript), 3,804 stream replays. Full table and every loss with its recording: [docs/results.md](docs/results.md). How to rebuild the environments: [docs/matrix.md](docs/matrix.md).

Clean on every recorded stream they speak: the official Anthropic SDKs (Python and TypeScript), google-genai, Pydantic AI on Anthropic, Gemini and Responses, Google ADK, Microsoft Agent Framework, LlamaIndex on Anthropic and Gemini, Haystack on Anthropic and Gemini, Strands on Anthropic and Gemini, `llm` with llm-anthropic, the Vercel AI SDK on Anthropic, Gemini and Responses.

Fixes for the losses above are going upstream as pull requests, each with the recorded stream as its test.

## Adapters

Run `llm-stream-check adapters` for the list. Each adapter drives the framework's documented streaming entry point (for example `ChatOpenAI.stream()` summed chunk by chunk, `litellm.stream_chunk_builder()`, `OpenAIChatCompletionsModel.stream_response()`) and records what the framework returned. Frameworks that only expose tool calls by running them (agno) are driven as real agents, and the run records which tools the agent actually executed. To add one, write `run(case, base_url) -> Observed` in `src/llm_stream_check/adapters/` and register it.

## Rebuilding the corpus

`tools/build_corpus.py` rebuilds the corpus from sparse clones of the source repositories and pins each case to the commit it came from. The reference parser (`llm_stream_check.reference`) follows each provider's documented wire format; the test suite checks that it reproduces every stored expectation, and the `reference` adapter replays the whole corpus over HTTP with zero losses.

## License

MIT. The recorded streams keep the licenses of the repositories they come from (MIT and Apache-2.0); each case links its source.
