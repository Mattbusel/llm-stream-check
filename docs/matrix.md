# Reproducing the results

Frameworks pin conflicting versions of the provider SDKs, so the published run uses one virtualenv per dependency set. Versions are the ones PyPI and npm served on 2026-11-20; each report row records the exact versions it ran against.

```
python -m venv a && a/bin/pip install openai anthropic google-genai litellm langchain-openai langchain-anthropic \
  langchain-google-genai llama-index-llms-openai llama-index-llms-google-genai "pydantic-ai-slim[openai,anthropic,google]" \
  openai-agents haystack-ai anthropic-haystack google-genai-haystack "autogen-ext[openai]" "smolagents[litellm]"
python -m venv b && b/bin/pip install "crewai[anthropic,google-genai]"
python -m venv c && c/bin/pip install --pre semantic-kernel agent-framework-openai agent-framework-anthropic
python -m venv d && d/bin/pip install google-adk litellm agno llm llm-anthropic
python -m venv e && e/bin/pip install "strands-agents[openai,anthropic,gemini,litellm]"
# llama-index-llms-anthropic 0.13.0 and autogen-ext's Anthropic client fail on every call with anthropic>=1
# (TypeError before any stream is read), so they run against the oldest anthropic they allow.
python -m venv f && f/bin/pip install llama-index-llms-anthropic "autogen-ext[anthropic]" "anthropic>=0.75,<0.76"

python tools/run_matrix.py <dir-with-venvs> out/

# JavaScript
npm install ai @ai-sdk/openai @ai-sdk/anthropic @ai-sdk/google openai @anthropic-ai/sdk @langchain/openai @langchain/core
llm-stream-check serve --port 8765 &
node harness/js/run.mjs http://127.0.0.1:8765 out/js.jsonl
llm-stream-check check out/js.jsonl --json out/report-js.json

llm-stream-check report out/report-*.json --json out/report-all.json
python tools/results_md.py out/report-all.json docs/results.md
```

## Fairness rules the adapters follow

- One fixed model name per protocol (`gpt-4o`, `claude-sonnet-4-5`, `gemini-2.5-flash`). Frameworks switch code paths on model names; the recorded names would send them down paths unrelated to the stream.
- Tool schemas are plain `{"type": "object", "properties": {}}`, registered under the names the stream calls.
- OpenAI Chat usage is only checked when the framework asked for it (`stream_options.include_usage`), because OpenAI only sends it then. The replay server records every request to know.
- When the framework asked for at most one tool call (`parallel_tool_calls: false`, `disable_parallel_tool_use`), streams with several calls are not counted against it.
- Tools the provider ran itself (Anthropic tool search, OpenAI tool search) are not counted as calls when the framework marks them as provider-executed.
- Frameworks that only expose tool calls by running them (agno) are driven as agents; the run records the tools the agent executed. Their usage is not compared, because it sums every model call of the loop.
