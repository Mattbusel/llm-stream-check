// Replays the llm-stream-check corpus through JavaScript frameworks.
//
//   llm-stream-check serve --port 8765 &
//   node harness/js/run.mjs http://127.0.0.1:8765 observed.jsonl [adapter ...]
//   llm-stream-check check observed.jsonl --json report.json
//
// Each line written is {"adapter", "case", "observed"}: the tool calls and usage the framework
// handed back, read from its public result fields only.

import { appendFileSync, readFileSync, writeFileSync } from "node:fs";
import { randomUUID } from "node:crypto";

const [server, out, ...only] = process.argv.slice(2);
const KEY = "sk-llm-stream-check";
const PROMPT = "Use the tools.";
const schema = { type: "object", properties: {} };

const adapters = {
  "vercel-ai.openai-chat": { protocols: ["openai-chat"], run: vercel("openai-chat"), pkgs: ["ai", "@ai-sdk/openai"] },
  "vercel-ai.openai-responses": { protocols: ["openai-responses"], run: vercel("openai-responses"), pkgs: ["ai", "@ai-sdk/openai"] },
  "vercel-ai.anthropic": { protocols: ["anthropic"], run: vercel("anthropic"), pkgs: ["ai", "@ai-sdk/anthropic"] },
  "vercel-ai.google": { protocols: ["gemini"], run: vercel("gemini"), pkgs: ["ai", "@ai-sdk/google"] },
  "openai-node.chat": { protocols: ["openai-chat"], run: openaiChat, pkgs: ["openai"] },
  "openai-node.responses": { protocols: ["openai-responses"], run: openaiResponses, pkgs: ["openai"] },
  "anthropic-node": { protocols: ["anthropic"], run: anthropicNode, pkgs: ["@anthropic-ai/sdk"] },
  "langchainjs.openai": { protocols: ["openai-chat"], run: langchainOpenAI, pkgs: ["@langchain/openai", "@langchain/core"] },
};

function vercel(protocol) {
  return async (base, c) => {
    const { streamText, tool, jsonSchema } = await import("ai");
    let model;
    if (protocol === "openai-chat" || protocol === "openai-responses") {
      const { createOpenAI } = await import("@ai-sdk/openai");
      const p = createOpenAI({ baseURL: base + "/v1", apiKey: KEY });
      model = protocol === "openai-chat" ? p.chat("gpt-4o") : p.responses("gpt-4o");
    } else if (protocol === "anthropic") {
      const { createAnthropic } = await import("@ai-sdk/anthropic");
      model = createAnthropic({ baseURL: base + "/v1", apiKey: KEY })("claude-sonnet-4-5");
    } else {
      const { createGoogleGenerativeAI } = await import("@ai-sdk/google");
      model = createGoogleGenerativeAI({ baseURL: base + "/v1beta", apiKey: KEY })("gemini-2.5-flash");
    }
    const tools = Object.fromEntries(c.tool_names.map((n) => [n, tool({ description: n, inputSchema: jsonSchema(schema) })]));
    let streamError = null;
    const r = streamText({ model, prompt: PROMPT, tools, maxRetries: 0, onError: ({ error }) => { streamError = error; } });
    await r.consumeStream();
    if (streamError) throw streamError;
    // Tools the provider ran itself (tool search, web search) come back with providerExecuted set.
    const calls = (await r.toolCalls).filter((t) => !t.providerExecuted)
      .map((t) => ({ name: t.toolName, arguments: t.input, id: t.toolCallId }));
    const u = await r.usage;
    return { tool_calls: calls, usage: u && (u.inputTokens != null || u.outputTokens != null)
      ? { input_tokens: u.inputTokens ?? null, output_tokens: u.outputTokens ?? null } : null };
  };
}

async function openaiChat(base, c) {
  const { default: OpenAI } = await import("openai");
  const client = new OpenAI({ baseURL: base + "/v1", apiKey: KEY, maxRetries: 0 });
  const s = client.chat.completions.stream({
    model: "gpt-4o", messages: [{ role: "user", content: PROMPT }], stream_options: { include_usage: true },
    tools: c.tool_names.map((n) => ({ type: "function", function: { name: n, description: n, parameters: schema } })),
  });
  const f = await s.finalChatCompletion();
  const m = f.choices[0]?.message;
  return { tool_calls: (m?.tool_calls ?? []).map((t) => ({ name: t.function.name, arguments: t.function.arguments, id: t.id })),
    usage: f.usage ? { input_tokens: f.usage.prompt_tokens, output_tokens: f.usage.completion_tokens } : null };
}

async function openaiResponses(base, c) {
  const { default: OpenAI } = await import("openai");
  const client = new OpenAI({ baseURL: base + "/v1", apiKey: KEY, maxRetries: 0 });
  const s = client.responses.stream({ model: "gpt-4o", input: PROMPT,
    tools: c.tool_names.map((n) => ({ type: "function", name: n, description: n, parameters: schema, strict: false })) });
  const f = await s.finalResponse();
  return { tool_calls: f.output.filter((o) => o.type === "function_call").map((o) => ({ name: o.name, arguments: o.arguments, id: o.call_id })),
    usage: f.usage ? { input_tokens: f.usage.input_tokens, output_tokens: f.usage.output_tokens } : null };
}

async function anthropicNode(base, c) {
  const { default: Anthropic } = await import("@anthropic-ai/sdk");
  const client = new Anthropic({ baseURL: base, apiKey: KEY, maxRetries: 0 });
  const s = client.messages.stream({ model: "claude-sonnet-4-5", max_tokens: 1024, messages: [{ role: "user", content: PROMPT }],
    tools: c.tool_names.map((n) => ({ name: n, description: n, input_schema: schema })) });
  const f = await s.finalMessage();
  return { tool_calls: f.content.filter((b) => b.type === "tool_use").map((b) => ({ name: b.name, arguments: b.input, id: b.id })),
    usage: { input_tokens: f.usage.input_tokens, output_tokens: f.usage.output_tokens } };
}

async function langchainOpenAI(base, c) {
  const { ChatOpenAI } = await import("@langchain/openai");
  const llm = new ChatOpenAI({ model: "gpt-4o", apiKey: KEY, configuration: { baseURL: base + "/v1" }, streamUsage: true, maxRetries: 0 });
  const bound = llm.bindTools(c.tool_names.map((n) => ({ type: "function", function: { name: n, description: n, parameters: schema } })));
  let acc = null;
  for await (const ch of await bound.stream(PROMPT)) acc = acc ? acc.concat(ch) : ch;
  const calls = [...(acc?.tool_calls ?? []), ...(acc?.invalid_tool_calls ?? [])].map((t) => ({ name: t.name, arguments: t.args, id: t.id }));
  const u = acc?.usage_metadata;
  return { tool_calls: calls, usage: u ? { input_tokens: u.input_tokens, output_tokens: u.output_tokens } : null };
}

const versions = {};
for (const p of ["ai", "@ai-sdk/openai", "@ai-sdk/anthropic", "@ai-sdk/google", "openai", "@anthropic-ai/sdk", "@langchain/openai", "@langchain/core"]) {
  try { versions[p] = JSON.parse(readFileSync(`node_modules/${p}/package.json`, "utf8")).version; } catch { /* not installed */ }
}
const cases = await (await fetch(server + "/cases")).json();
writeFileSync(out, "");
for (const [name, a] of Object.entries(adapters)) {
  if (only.length && !only.includes(name)) continue;
  for (const c of cases.filter((x) => a.protocols.includes(x.protocol))) {
    const session = `${c.id}~${randomUUID().slice(0, 8)}`;
    let observed;
    try {
      observed = { usage_supported: true, error: null, ...(await a.run(`${server}/c/${session}`, c)) };
    } catch (e) {
      observed = { tool_calls: [], usage: null, usage_supported: true, error: `${e?.name}: ${String(e?.message ?? e).slice(0, 400)}` };
    }
    const reqs = await (await fetch(`${server}/requests/${session}`)).json();
    const first = reqs[0] ?? {};
    if (c.protocol === "openai-chat" && !(first.stream_options ?? {}).include_usage) observed.usage_supported = false;
    appendFileSync(out, JSON.stringify({ adapter: name, case: c.id, observed, parallel_disabled: !!first.parallel_disabled,
      versions: Object.fromEntries((a.pkgs ?? []).map((p) => [p, versions[p]])) }) + "\n");
  }
}
