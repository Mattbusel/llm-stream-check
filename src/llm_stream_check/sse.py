"""Server-sent events: parse recorded bodies and frame events for replay."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class Event:
    """One SSE event: the optional ``event:`` name and the raw ``data:`` payload."""

    name: str | None
    data: str

    def json(self) -> Any:
        return json.loads(self.data)


def parse(body: str) -> list[Event]:
    """Split an SSE body into events (WHATWG rules: blank line ends an event)."""
    events: list[Event] = []
    name: str | None = None
    data: list[str] = []
    for raw in body.replace("\r\n", "\n").replace("\r", "\n").split("\n"):
        if raw == "":
            if data:
                events.append(Event(name, "\n".join(data)))
            name, data = None, []
            continue
        if raw.startswith(":"):
            continue
        field, _, value = raw.partition(":")
        if value.startswith(" "):
            value = value[1:]
        if field == "event":
            name = value
        elif field == "data":
            data.append(value)
    if data:
        events.append(Event(name, "\n".join(data)))
    return events


def json_events(body: str) -> list[Any]:
    """The JSON payloads of a body, skipping ``[DONE]`` and non-JSON keepalives."""
    out = []
    for ev in parse(body):
        if ev.data.strip() == "[DONE]":
            continue
        try:
            out.append(ev.json())
        except json.JSONDecodeError:
            continue
    return out


def frame(payloads: list[Any], protocol: str) -> str:
    """Build an SSE body from JSON payloads the way each provider frames it on the wire."""
    parts = []
    for p in payloads:
        data = p if isinstance(p, str) else json.dumps(p, separators=(",", ":"))
        if protocol in ("anthropic", "openai-responses"):
            parts.append(f"event: {json.loads(data).get('type')}\ndata: {data}\n\n")
        else:
            parts.append(f"data: {data}\n\n")
    if protocol == "openai-chat":
        parts.append("data: [DONE]\n\n")
    return "".join(parts)
