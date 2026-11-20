from __future__ import annotations

import json
import urllib.request

import pytest

from llm_stream_check import cli, corpus, reference, server, sse
from llm_stream_check.compare import Observed, compare

CASES = corpus.load(core_only=False)


def test_corpus_is_large_and_cited() -> None:
    core = corpus.load()
    assert len(core) >= 200
    assert {c.protocol for c in core} == set(corpus.PROTOCOLS)
    for c in CASES:
        assert c.source["url"].startswith("https://github.com/") and "/blob/" in c.source["url"]
        assert len(c.source["commit"]) == 40
        assert c.expected["tool_calls"], c.id


@pytest.mark.parametrize("case", CASES, ids=[c.id for c in CASES])
def test_reference_reproduces_stored_expectation(case: corpus.Case) -> None:
    got = reference.expected(case.protocol, sse.json_events(case.body)).to_dict()
    assert got == case.expected


def test_corpus_covers_the_shapes_that_lose_calls() -> None:
    feats = {(c.protocol, f) for c in corpus.load() for f in c.features}
    for need in [
        ("openai-chat", "parallel_tool_calls"),
        ("openai-chat", "arguments_split_mid_json"),
        ("openai-chat", "empty_delta"),
        ("openai-chat", "usage_only_final_chunk"),
        ("openai-chat", "indexless_tool_call"),
        ("openai-chat", "multiple_tool_calls_in_one_chunk"),
        ("anthropic", "parallel_tool_calls"),
        ("anthropic", "arguments_split_mid_json"),
        ("anthropic", "tool_call_index_gap"),
        ("openai-responses", "tool_call_index_gap"),
        ("gemini", "usage_only_final_chunk"),
    ]:
        assert need in feats, need


def test_sse_parse_handles_crlf_comments_and_multiline() -> None:
    body = ': keepalive\r\nevent: a\r\ndata: {"x":\r\ndata: 1}\r\n\r\ndata: [DONE]\r\n\r\n'
    evs = sse.parse(body)
    assert evs[0].name == "a" and evs[0].json() == {"x": 1}
    assert sse.json_events(body) == [{"x": 1}]


EXP = {
    "tool_calls": [{"id": "a", "name": "f", "arguments": {"x": 1}}, {"id": "b", "name": "g", "arguments": {}}],
    "usage": {"input_tokens": 10, "output_tokens": 5},
}


def kinds(obs: Observed) -> list[str]:
    return [x.kind for x in compare(EXP, obs)]


def test_lossless_observation_passes() -> None:
    obs = Observed(
        [{"id": "a", "name": "f", "arguments": '{"x": 1}'}, {"id": "b", "name": "g", "arguments": ""}],
        {"input_tokens": 10, "output_tokens": 5},
    )
    assert kinds(obs) == []


def test_dropped_merged_phantom_and_corrupted() -> None:
    u = {"input_tokens": 10, "output_tokens": 5}
    assert kinds(Observed([{"id": "a", "name": "f", "arguments": {"x": 1}}], u)) == ["dropped_tool_call"]
    assert kinds(Observed([{"id": "a", "name": "fg", "arguments": '{"x": 1}{}'}], u)) == ["merged_tool_calls"]
    assert kinds(Observed([{"id": "a", "name": "f", "arguments": {}}], u)) == ["merged_tool_calls"]
    extra = [
        {"id": "a", "name": "f", "arguments": {"x": 1}},
        {"id": "b", "name": "g", "arguments": {}},
        {"id": "c", "name": "h", "arguments": {}},
    ]
    assert kinds(Observed(extra, u)) == ["phantom_tool_call"]
    wrong = [{"id": "a", "name": "f", "arguments": {"x": 2}}, {"id": "b", "name": "g", "arguments": {}}]
    assert kinds(Observed(wrong, u)) == ["corrupted_tool_call"]
    ids = [{"id": "zz", "name": "f", "arguments": {"x": 1}}, {"id": "b", "name": "g", "arguments": {}}]
    assert kinds(Observed(ids, u)) == ["wrong_tool_call_id"]


def test_usage_losses() -> None:
    calls = EXP["tool_calls"]
    assert kinds(Observed(calls, None)) == ["lost_usage"]
    assert kinds(Observed(calls, {"input_tokens": 30, "output_tokens": 5})) == ["wrong_usage"]
    assert kinds(Observed(calls, None, usage_supported=False)) == []
    assert kinds(Observed(error="boom")) == ["error"]


def test_server_replays_recorded_bytes_then_followup() -> None:
    case = next(c for c in CASES if c.protocol == "anthropic")
    srv = server.start([case])
    try:
        base = f"{server.url(srv)}/c/{case.id}~t1"
        bodies = []
        for _ in range(2):
            req = urllib.request.Request(
                base + "/v1/messages", data=json.dumps({"stream": True}).encode(), method="POST"
            )
            with urllib.request.urlopen(req, timeout=10) as r:
                bodies.append(r.read().decode())
        assert sse.json_events(bodies[0]) == sse.json_events(case.body)
        assert not reference.expected("anthropic", sse.json_events(bodies[1])).tool_calls
    finally:
        srv.shutdown()


def test_run_reference_adapter_is_lossless_and_exit_zero() -> None:
    assert cli.main(["run", "--adapter", "reference", "--protocol", "openai-chat"]) == 0


def test_unknown_or_missing_adapter_fails_closed() -> None:
    assert cli.main(["run", "--adapter", "no-such-framework"]) == 2
    from llm_stream_check.adapters import REGISTRY

    missing = next((a for a in REGISTRY.values() if cli.versions(a) is None), None)
    if missing is None:
        pytest.skip("every framework is installed here")
    assert cli.main(["run", "--adapter", missing.name]) == 2


def test_check_fails_on_loss(tmp_path: pytest.TempPathFactory) -> None:
    case = next(c for c in CASES if len(c.expected["tool_calls"]) > 1 and c.core)
    f = tmp_path / "obs.jsonl"  # type: ignore[operator]
    one = case.expected["tool_calls"][:1]
    f.write_text(
        json.dumps(
            {"adapter": "x", "case": case.id, "observed": {"tool_calls": one, "usage": None, "usage_supported": False}}
        )
        + "\n"
    )
    assert cli.main(["check", str(f)]) == 1
    f.write_text(
        json.dumps(
            {
                "adapter": "x",
                "case": case.id,
                "observed": {"tool_calls": case.expected["tool_calls"], "usage": None, "usage_supported": False},
            }
        )
        + "\n"
    )
    assert cli.main(["check", str(f)]) == 0
