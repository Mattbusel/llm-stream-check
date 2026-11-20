# Results

Generated 2026-11-20T18:59:26Z by llm-stream-check 0.1.0 from the bundled corpus (243 recorded streams). Every row below is a recorded provider response replayed byte for byte through the framework's own streaming code, compared with what the stream said.

| adapter | versions | streams | lossy | losses |
|---|---|---:|---:|---|
| `agent-framework.anthropic` | agent-framework-anthropic 1.0.0b261112, agent-framework-core 1.26.0 | 169 | 0 | none |
| `agent-framework.openai` | agent-framework-openai 1.18.2, agent-framework-core 1.26.0 | 38 | 0 | none |
| `agno.anthropic` | agno 3.2.1 | 169 | 0 | none |
| `agno.openai` | agno 3.2.1 | 38 | 3 | dropped_tool_call 3 |
| `anthropic-node` | @anthropic-ai/sdk 1.12.0 | 169 | 0 | none |
| `anthropic-python` | anthropic 2.12.0 | 169 | 0 | none |
| `autogen.anthropic` | autogen-ext 0.7.5, autogen-core 0.7.5 | 169 | 9 | wrong_usage 9 |
| `autogen.openai` | autogen-ext 0.7.5, autogen-core 0.7.5 | 38 | 2 | error 1, merged_tool_calls 1 |
| `crewai` | crewai 1.15.44 | 217 | 2 | error 1, merged_tool_calls 1 |
| `google-adk.gemini` | google-adk 2.15.0 | 10 | 0 | none |
| `google-adk.litellm` | google-adk 2.15.0, litellm 1.110.2 | 217 | 0 | none |
| `google-genai` | google-genai 2.34.0 | 10 | 0 | none |
| `haystack.anthropic` | anthropic-haystack 8.1.0, haystack-ai 3.5.0 | 169 | 0 | none |
| `haystack.google-genai` | google-genai-haystack 7.2.2, haystack-ai 3.5.0 | 10 | 0 | none |
| `haystack.openai` | haystack-ai 3.5.0 | 38 | 4 | error 3, wrong_tool_call_id 1 |
| `langchain-anthropic` | langchain-anthropic 1.7.12, langchain-core 1.8.4 | 169 | 2 | error 1, wrong_usage 1 |
| `langchain-google-genai` | langchain-google-genai 4.4.3, langchain-core 1.8.4 | 10 | 0 | none |
| `langchain-openai` | langchain-openai 1.8.4, langchain-core 1.8.4 | 38 | 1 | wrong_usage 1 |
| `langchain-openai.responses` | langchain-openai 1.8.4, langchain-core 1.8.4 | 26 | 0 | none |
| `langchainjs.openai` | @langchain/openai 1.8.4, @langchain/core 1.4.2 | 38 | 1 | dropped_tool_call 1, lost_usage 1 |
| `litellm` | litellm 1.110.2 | 217 | 1 | merged_tool_calls 1 |
| `litellm.responses` | litellm 1.110.2 | 26 | 4 | dropped_tool_call 4 |
| `llama-index-anthropic` | llama-index-llms-anthropic 0.13.0, llama-index-core 0.14.26 | 169 | 0 | none |
| `llama-index-google-genai` | llama-index-llms-google-genai 0.12.0, llama-index-core 0.14.26 | 10 | 0 | none |
| `llama-index-openai` | llama-index-llms-openai 0.9.0, llama-index-core 0.14.26 | 38 | 3 | dropped_tool_call 1, error 1, merged_tool_calls 1 |
| `llm.anthropic` | llm 0.38, llm-anthropic 0.31 | 169 | 0 | none |
| `llm.openai` | llm 0.38 | 38 | 1 | error 1 |
| `openai-agents.chat` | openai-agents 0.25.0 | 38 | 2 | error 1, merged_tool_calls 1 |
| `openai-agents.responses` | openai-agents 0.25.0 | 26 | 4 | dropped_tool_call 4 |
| `openai-node.chat` | openai 7.62.0 | 38 | 3 | error 3 |
| `openai-node.responses` | openai 7.62.0 | 26 | 4 | dropped_tool_call 4 |
| `openai-python.chat` | openai 3.57.0 | 38 | 2 | error 2 |
| `openai-python.responses` | openai 3.57.0 | 26 | 4 | dropped_tool_call 4 |
| `pydantic-ai.anthropic` | pydantic-ai-slim 2.71.0 | 169 | 0 | none |
| `pydantic-ai.google` | pydantic-ai-slim 2.71.0 | 10 | 0 | none |
| `pydantic-ai.openai-chat` | pydantic-ai-slim 2.71.0 | 38 | 1 | wrong_usage 1 |
| `pydantic-ai.openai-responses` | pydantic-ai-slim 2.71.0 | 26 | 0 | none |
| `semantic-kernel.openai` | semantic-kernel 1.47.0 | 38 | 1 | error 1 |
| `smolagents.litellm` | smolagents 1.26.0, litellm 1.110.2 | 217 | 1 | merged_tool_calls 1 |
| `smolagents.openai` | smolagents 1.26.0 | 38 | 3 | error 3 |
| `strands.anthropic` | strands-agents 1.65.0 | 169 | 0 | none |
| `strands.gemini` | strands-agents 1.65.0 | 10 | 0 | none |
| `strands.litellm` | strands-agents 1.65.0, litellm 1.106.12 | 38 | 1 | merged_tool_calls 1 |
| `strands.openai` | strands-agents 1.65.0 | 38 | 2 | error 1, merged_tool_calls 1 |
| `vercel-ai.anthropic` | ai 7.0.178, @ai-sdk/anthropic 4.0.107 | 169 | 0 | none |
| `vercel-ai.google` | ai 7.0.178, @ai-sdk/google 4.0.123 | 10 | 0 | none |
| `vercel-ai.openai-chat` | ai 7.0.178, @ai-sdk/openai 4.0.122 | 38 | 3 | error 3 |
| `vercel-ai.openai-responses` | ai 7.0.178, @ai-sdk/openai 4.0.122 | 26 | 0 | none |

## Every loss

Grouped by the recorded stream that caused it. The source link is the recording at a pinned commit.

### `openai-chat--pydantic-ai--test-compatible-api-gemini-3-tool-call-thought-signature-true--0`

Provider: openai. Shapes: arguments_split_mid_json, empty_delta, indexless_tool_call, name_and_arguments_in_one_chunk, parallel_tool_calls, usage. Recording: https://github.com/pydantic/pydantic-ai/blob/ebcaf6586c12885ea19f4e63cbe306e7527d00e1/tests/models/cassettes/test_openai/test_compatible_api_gemini_3_tool_call_thought_signature[True].yaml

- `agno.openai`: **dropped_tool_call**: 2 calls in the stream, 0 surfaced; missing ['get_weather', 'get_weather']
- `autogen.openai`: **merged_tool_calls**: 2 calls in the stream came out as 1: get_weatherget_weather({"__unparseable__": "{\"city\":\"Taipei\"}{\"city\":\"Kaohsiung\"}"})
- `crewai`: **merged_tool_calls**: 2 calls in the stream came out as 1: get_weather({"__unparseable__": "{\"city\":\"Taipei\"}{\"city\":\"Kaohsiung\"}"})
- `haystack.openai`: **error**: ValueError: If `tool_call`, `tool_call_result` or `reasoning` is set, `index` must also be set. @ C:\Users\Matthew\_lsc_fw\a\Lib\site-packages\haystack\dataclasses\streaming_chunk.py:153
- `langchain-openai`: **wrong_usage**: input 222 != 74; output 89 != 36
- `litellm`: **merged_tool_calls**: 2 calls in the stream came out as 1: get_weather({"__unparseable__": "{\"city\":\"Taipei\"}{\"city\":\"Kaohsiung\"}"})
- `llama-index-openai`: **merged_tool_calls**: 2 calls in the stream came out as 1: get_weatherget_weather({})
- `openai-agents.chat`: **merged_tool_calls**: 2 calls in the stream came out as 1: get_weather({"__unparseable__": "{\"city\":\"Taipei\"}{\"city\":\"Kaohsiung\"}"})
- `openai-node.chat`: **error**: Error: Chat completion stream contains an invalid tool call index: undefined
- `openai-python.chat`: **error**: TypeError: list indices must be integers or slices, not NoneType @ C:\Users\Matthew\_lsc_fw\a\Lib\site-packages\openai\lib\streaming\chat\_completions.py:537
- `pydantic-ai.openai-chat`: **wrong_usage**: input 222 != 74; output 89 != 36
- `smolagents.litellm`: **merged_tool_calls**: 2 calls in the stream came out as 1: get_weather({"__unparseable__": "{\"city\":\"Taipei\"}{\"city\":\"Kaohsiung\"}"})
- `smolagents.openai`: **error**: ValueError: Tool call index is not provided in tool delta: ChatMessageToolCallStreamDelta(index=None, id='call_108766', type='function', function=ChoiceDeltaToolCallFunction(arguments='{"city":"Taipei"}', name='get_weather')) @ C:\Users\Matthew\_lsc_fw\a\Lib\site-packages\smolagents\models.py:258
- `strands.litellm`: **merged_tool_calls**: 2 calls in the stream came out as 1: get_weather({})
- `strands.openai`: **merged_tool_calls**: 2 calls in the stream came out as 1: get_weather({})
- `vercel-ai.openai-chat`: **error**: AI_TypeValidationError: Type validation failed: Value: {"choices":[{"delta":{"role":"assistant","tool_calls":[{"function":{"arguments":"{\"city\":\"Kaohsiung\"}","name":"get_weather"},"id":"call_108772","type":"function"}]},"index":0}],"created":1791940063,"id":"3tXOasW2I-2KmtkPrtulEA","model":"gemi

### `openai-chat--pydantic-ai--test-mistral-stream-parallel-tool-calls-zai-glm-5-3--0`

Provider: mistral. Shapes: arguments_split_mid_json, empty_delta, multiple_tool_calls_in_one_chunk, name_and_arguments_in_one_chunk, parallel_tool_calls, usage. Recording: https://github.com/pydantic/pydantic-ai/blob/ebcaf6586c12885ea19f4e63cbe306e7527d00e1/tests/models/cassettes/test_mistral/test_mistral_stream_parallel_tool_calls[zai-glm-5-3].yaml

- `agno.openai`: **dropped_tool_call**: 3 calls in the stream, 0 surfaced; missing ['get_weather', 'get_weather', 'get_time']
- `autogen.openai`: **error**: TypeError: sequence item 0: expected str instance, list found @ C:\Users\Matthew\_lsc_fw\a\Lib\site-packages\autogen_ext\models\openai\_openai_client.py:1036
- `crewai`: **error**: TypeError: can only concatenate str (not "list") to str @ C:\Users\Matthew\_lsc_fw\b\Lib\site-packages\crewai\llms\providers\openai\completion.py:2737
- `haystack.openai`: **error**: TypeError: sequence item 2: expected str instance, list found @ C:\Users\Matthew\_lsc_fw\a\Lib\site-packages\haystack\components\generators\utils.py:125
- `llama-index-openai`: **error**: TypeError: can only concatenate str (not "list") to str @ C:\Users\Matthew\_lsc_fw\a\Lib\site-packages\llama_index\llms\openai\base.py:570
- `llm.openai`: **error**: TypeError: can only concatenate str (not "list") to str @ C:\Users\Matthew\_lsc_fw\d\Lib\site-packages\llm\default_plugins\openai_models.py:3347
- `openai-agents.chat`: **error**: ValidationError: 1 validation error for ResponseTextDeltaEvent delta   Input should be a valid string [type=string_type, input_value=[{'type': 'thinking', 'th...The'}], 'closed': True}], input_type=list]     For further information visit https://errors.pydantic.dev/2.14/v/string_type @ C:\Users\Matt
- `semantic-kernel.openai`: **error**: ValidationError: 1 validation error for StreamingTextContent text   Input should be a valid string [type=string_type, input_value=[{'type': 'thinking', 'th...The'}], 'closed': True}], input_type=list]     For further information visit https://errors.pydantic.dev/2.13/v/string_type @ C:\Users\Matthew
- `smolagents.openai`: **error**: TypeError: can only concatenate str (not "list") to str @ C:\Users\Matthew\_lsc_fw\a\Lib\site-packages\smolagents\models.py:235
- `strands.openai`: **error**: TypeError: can only concatenate str (not "list") to str @ C:\Users\Matthew\_lsc_fw\e\Lib\site-packages\strands\event_loop\streaming.py:246
- `vercel-ai.openai-chat`: **error**: AI_TypeValidationError: Type validation failed: Value: {"id":"032662f9522949949b473cfadd932705","object":"chat.completion.chunk","created":1793745184,"model":"zai-glm-5-3","choices":[{"index":0,"delta":{"index":0,"content":[{"type":"thinking","thinking":[{"type":"text","text":"_calls block."}],"clos

### `openai-chat--ai--mistral-tool-call-chunks`

Provider: mistral. Shapes: empty_delta, indexless_tool_call, name_and_arguments_in_one_chunk, usage. Recording: https://github.com/vercel/ai/blob/beccad37665bbc56afd85542a932e430bdbc4e2e/packages/mistral/src/__fixtures__/mistral-tool-call.chunks.txt

- `agno.openai`: **dropped_tool_call**: 1 calls in the stream, 0 surfaced; missing ['weather']
- `haystack.openai`: **error**: ValueError: If `tool_call`, `tool_call_result` or `reasoning` is set, `index` must also be set. @ C:\Users\Matthew\_lsc_fw\a\Lib\site-packages\haystack\dataclasses\streaming_chunk.py:153
- `openai-node.chat`: **error**: Error: Chat completion stream contains an invalid tool call index: undefined
- `openai-python.chat`: **error**: TypeError: list indices must be integers or slices, not NoneType @ C:\Users\Matthew\_lsc_fw\a\Lib\site-packages\openai\lib\streaming\chat\_completions.py:447
- `smolagents.openai`: **error**: ValueError: Tool call index is not provided in tool delta: ChatMessageToolCallStreamDelta(index=None, id='gSIMJiOkT', type=None, function=ChoiceDeltaToolCallFunction(arguments='{"location": "San Francisco"}', name='weather')) @ C:\Users\Matthew\_lsc_fw\a\Lib\site-packages\smolagents\models.py:258
- `vercel-ai.openai-chat`: **error**: AI_TypeValidationError: Type validation failed: Value: {"id":"b3999b8c93e04e11bcbff7bcab829667","object":"chat.completion.chunk","created":1769088854,"model":"mistral-small-latest","choices":[{"index":0,"delta":{"content":null,"tool_calls":[{"id":"gSIMJiOkT","function":{"name":"weather","arguments":

### `openai-responses--pydantic-ai--test-codex-calls-additional-tool--0`

Provider: codex. Shapes: arguments_split_mid_json, usage. Recording: https://github.com/pydantic/pydantic-ai/blob/ebcaf6586c12885ea19f4e63cbe306e7527d00e1/tests/models/cassettes/test_openai_codex/test_codex_calls_additional_tool.yaml

- `litellm.responses`: **dropped_tool_call**: 1 calls in the stream, 0 surfaced; missing ['lookup_refund_policy']
- `openai-agents.responses`: **dropped_tool_call**: 1 calls in the stream, 0 surfaced; missing ['lookup_refund_policy']
- `openai-node.responses`: **dropped_tool_call**: 1 calls in the stream, 0 surfaced; missing ['lookup_refund_policy']
- `openai-python.responses`: **dropped_tool_call**: 1 calls in the stream, 0 surfaced; missing ['lookup_refund_policy']

### `openai-responses--pydantic-ai--test-codex-deferred-tool-search--0`

Provider: codex. Shapes: tool_call_index_gap, usage. Recording: https://github.com/pydantic/pydantic-ai/blob/ebcaf6586c12885ea19f4e63cbe306e7527d00e1/tests/models/cassettes/test_openai_codex/test_codex_deferred_tool_search.yaml

- `litellm.responses`: **dropped_tool_call**: 1 calls in the stream, 0 surfaced; missing ['moo']
- `openai-agents.responses`: **dropped_tool_call**: 1 calls in the stream, 0 surfaced; missing ['moo']
- `openai-node.responses`: **dropped_tool_call**: 1 calls in the stream, 0 surfaced; missing ['moo']
- `openai-python.responses`: **dropped_tool_call**: 1 calls in the stream, 0 surfaced; missing ['moo']

### `openai-responses--pydantic-ai--test-codex-tool-roundtrip-false--0`

Provider: codex. Shapes: usage. Recording: https://github.com/pydantic/pydantic-ai/blob/ebcaf6586c12885ea19f4e63cbe306e7527d00e1/tests/models/cassettes/test_openai_codex/test_codex_tool_roundtrip[False].yaml

- `litellm.responses`: **dropped_tool_call**: 1 calls in the stream, 0 surfaced; missing ['moo']
- `openai-agents.responses`: **dropped_tool_call**: 1 calls in the stream, 0 surfaced; missing ['moo']
- `openai-node.responses`: **dropped_tool_call**: 1 calls in the stream, 0 surfaced; missing ['moo']
- `openai-python.responses`: **dropped_tool_call**: 1 calls in the stream, 0 surfaced; missing ['moo']

### `openai-responses--pydantic-ai--test-codex-tool-roundtrip-true--0`

Provider: codex. Shapes: usage. Recording: https://github.com/pydantic/pydantic-ai/blob/ebcaf6586c12885ea19f4e63cbe306e7527d00e1/tests/models/cassettes/test_openai_codex/test_codex_tool_roundtrip[True].yaml

- `litellm.responses`: **dropped_tool_call**: 1 calls in the stream, 0 surfaced; missing ['moo']
- `openai-agents.responses`: **dropped_tool_call**: 1 calls in the stream, 0 surfaced; missing ['moo']
- `openai-node.responses`: **dropped_tool_call**: 1 calls in the stream, 0 surfaced; missing ['moo']
- `openai-python.responses`: **dropped_tool_call**: 1 calls in the stream, 0 surfaced; missing ['moo']

### `openai-chat--ai--mistral-incremental-tool-call-chunks`

Provider: mistral. Shapes: usage. Recording: https://github.com/vercel/ai/blob/beccad37665bbc56afd85542a932e430bdbc4e2e/packages/mistral/src/__fixtures__/mistral-incremental-tool-call.chunks.txt

- `langchainjs.openai`: **dropped_tool_call**: 1 calls in the stream, 0 surfaced; missing ['webSearchTool']
- `langchainjs.openai`: **lost_usage**: provider reported 171 in / 14 out; framework surfaced none
- `openai-node.chat`: **error**: Error: missing role for choice 0

### `anthropic--anthropic-sdk-python--tool-use-response`

Provider: anthropic. Shapes: arguments_split_mid_json, empty_delta, ping_event, tool_call_index_gap, usage. Recording: https://github.com/anthropics/anthropic-sdk-python/blob/8baaef1c4d23b2e4861d05da0dca65252e879eb8/tests/lib/streaming/fixtures/tool_use_response.txt

- `langchain-anthropic`: **wrong_usage**: input 0 != 377

### `anthropic--pydantic-ai--test-anthropic-memory-tool--0`

Provider: anthropic. Shapes: arguments_split_mid_json, empty_delta, ping_event, usage, usage_restated_in_message_delta. Recording: https://github.com/pydantic/pydantic-ai/blob/ebcaf6586c12885ea19f4e63cbe306e7527d00e1/tests/models/cassettes/test_anthropic/test_anthropic_memory_tool.yaml

- `langchain-anthropic`: **error**: AttributeError: 'dict' object has no attribute 'model_dump' @ C:\Users\Matthew\_lsc_fw\a\Lib\site-packages\langchain_anthropic\chat_models.py:2574

### `openai-chat--pydantic-ai--test-mistral-stream-parallel-tool-calls-mistral-small-latest--0`

Provider: mistral. Shapes: empty_delta, multiple_tool_calls_in_one_chunk, name_and_arguments_in_one_chunk, parallel_tool_calls, usage. Recording: https://github.com/pydantic/pydantic-ai/blob/ebcaf6586c12885ea19f4e63cbe306e7527d00e1/tests/models/cassettes/test_mistral/test_mistral_stream_parallel_tool_calls[mistral-small-latest].yaml

- `llama-index-openai`: **dropped_tool_call**: 3 calls in the stream, 1 surfaced; missing ['get_weather', 'get_time']

### `openai-chat--ai--alibaba-tool-call-chunks`

Provider: alibaba. Shapes: arguments_split_mid_json, empty_delta, usage, usage_only_final_chunk. Recording: https://github.com/vercel/ai/blob/beccad37665bbc56afd85542a932e430bdbc4e2e/packages/alibaba/src/__fixtures__/alibaba-tool-call.chunks.txt

- `haystack.openai`: **wrong_tool_call_id**: weather: provider id 'call_eee11723464a4b9eb8cee71d', got ''

### `anthropic--ai--anthropic-tool-search-bm25-1-chunks--r1`

Provider: anthropic. Shapes: arguments_split_mid_json, empty_delta, ping_event, tool_call_index_gap, usage, usage_restated_in_message_delta. Recording: https://github.com/vercel/ai/blob/beccad37665bbc56afd85542a932e430bdbc4e2e/packages/anthropic/src/__fixtures__/anthropic-tool-search-bm25.1.chunks.txt

- `autogen.anthropic`: **wrong_usage**: input 699 != 1630

### `anthropic--ai--anthropic-tool-search-regex-1-chunks--r1`

Provider: anthropic. Shapes: arguments_split_mid_json, empty_delta, tool_call_index_gap, usage, usage_restated_in_message_delta. Recording: https://github.com/vercel/ai/blob/beccad37665bbc56afd85542a932e430bdbc4e2e/packages/anthropic/src/__fixtures__/anthropic-tool-search-regex.1.chunks.txt

- `autogen.anthropic`: **wrong_usage**: input 722 != 1681

### `anthropic--pydantic-ai--test-anthropic-count-tokens-before-request-with-every-tool-deferred--0`

Provider: anthropic. Shapes: arguments_split_mid_json, empty_delta, ping_event, tool_call_index_gap, usage, usage_restated_in_message_delta. Recording: https://github.com/pydantic/pydantic-ai/blob/ebcaf6586c12885ea19f4e63cbe306e7527d00e1/tests/models/cassettes/test_anthropic/test_anthropic_count_tokens_before_request_with_every_tool_deferred.yaml

- `autogen.anthropic`: **wrong_usage**: input 669 != 1529

### `anthropic--pydantic-ai--test-anthropic-native-tool-search-round-trip--0`

Provider: anthropic. Shapes: arguments_split_mid_json, empty_delta, ping_event, tool_call_index_gap, usage, usage_restated_in_message_delta. Recording: https://github.com/pydantic/pydantic-ai/blob/ebcaf6586c12885ea19f4e63cbe306e7527d00e1/tests/cassettes/test_tool_search/test_anthropic_native_tool_search_round_trip.yaml

- `autogen.anthropic`: **wrong_usage**: input 667 != 1536

### `anthropic--pydantic-ai--test-anthropic-native-tool-search-streaming--0`

Provider: anthropic. Shapes: arguments_split_mid_json, empty_delta, ping_event, tool_call_index_gap, usage, usage_restated_in_message_delta. Recording: https://github.com/pydantic/pydantic-ai/blob/ebcaf6586c12885ea19f4e63cbe306e7527d00e1/tests/cassettes/test_tool_search/test_anthropic_native_tool_search_streaming.yaml

- `autogen.anthropic`: **wrong_usage**: input 667 != 1535

### `anthropic--pydantic-ai--test-anthropic-tool-search-replays-every-input-field-false--0`

Provider: anthropic. Shapes: arguments_split_mid_json, empty_delta, ping_event, thinking_block, tool_call_index_gap, usage, usage_restated_in_message_delta. Recording: https://github.com/pydantic/pydantic-ai/blob/ebcaf6586c12885ea19f4e63cbe306e7527d00e1/tests/models/anthropic/cassettes/test_tool_search/test_anthropic_tool_search_replays_every_input_field[False].yaml

- `autogen.anthropic`: **wrong_usage**: input 737 != 1663

### `anthropic--pydantic-ai--test-anthropic-tool-search-replays-every-input-field-true--0`

Provider: anthropic. Shapes: arguments_split_mid_json, empty_delta, ping_event, thinking_block, tool_call_index_gap, usage, usage_restated_in_message_delta. Recording: https://github.com/pydantic/pydantic-ai/blob/ebcaf6586c12885ea19f4e63cbe306e7527d00e1/tests/models/anthropic/cassettes/test_tool_search/test_anthropic_tool_search_replays_every_input_field[True].yaml

- `autogen.anthropic`: **wrong_usage**: input 737 != 1663

### `anthropic--pydantic-ai--test-live-tool-search-handoff-anthropic-openai-anthropic--0`

Provider: anthropic. Shapes: arguments_split_mid_json, empty_delta, ping_event, tool_call_index_gap, usage, usage_restated_in_message_delta. Recording: https://github.com/pydantic/pydantic-ai/blob/ebcaf6586c12885ea19f4e63cbe306e7527d00e1/tests/cassettes/test_tool_search/test_live_tool_search_handoff_anthropic_openai_anthropic.yaml

- `autogen.anthropic`: **wrong_usage**: input 690 != 1552

### `anthropic--pydantic-ai--test-live-tool-search-handoff-anthropic-to-openai--0`

Provider: anthropic. Shapes: arguments_split_mid_json, empty_delta, ping_event, tool_call_index_gap, usage, usage_restated_in_message_delta. Recording: https://github.com/pydantic/pydantic-ai/blob/ebcaf6586c12885ea19f4e63cbe306e7527d00e1/tests/cassettes/test_tool_search/test_live_tool_search_handoff_anthropic_to_openai.yaml

- `autogen.anthropic`: **wrong_usage**: input 690 != 1552

