"""The checker's own parser, over HTTP. No framework needed: proves the replay path is lossless."""

from __future__ import annotations

import json
import urllib.request

from .. import reference, sse
from ..compare import Observed
from ..corpus import Case

PATHS = {
    "openai-chat": "/v1/chat/completions",
    "openai-responses": "/v1/responses",
    "anthropic": "/v1/messages",
    "gemini": "/v1beta/models/gemini-2.5-flash:streamGenerateContent?alt=sse",
}


def run(case: Case, base: str) -> Observed:
    body = json.dumps({"stream": True, "stream_options": {"include_usage": True}}).encode()
    req = urllib.request.Request(
        base + PATHS[case.protocol], data=body, method="POST", headers={"content-type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=30) as r:  # noqa: S310 - local replay server only
        text = r.read().decode("utf-8")
    res = reference.expected(case.protocol, sse.json_events(text))
    return Observed(
        [t.to_dict() for t in res.tool_calls], {"input_tokens": res.input_tokens, "output_tokens": res.output_tokens}
    )
