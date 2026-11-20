"""The bundled replay corpus: recorded provider streams with their reference results."""

from __future__ import annotations

import json
from dataclasses import dataclass
from importlib import resources
from typing import Any

PROTOCOLS = ("openai-chat", "openai-responses", "anthropic", "gemini")


@dataclass(frozen=True)
class Case:
    id: str
    protocol: str
    provider: str
    model: str | None
    core: bool
    source: dict[str, Any]
    features: tuple[str, ...]
    expected: dict[str, Any]
    body: str

    @property
    def tool_names(self) -> list[str]:
        names: list[str] = []
        for c in self.expected["tool_calls"]:
            if c["name"] not in names:
                names.append(c["name"])
        return names


def _root() -> Any:
    return resources.files("llm_stream_check") / "corpus"


def load(protocols: tuple[str, ...] | list[str] = PROTOCOLS, core_only: bool = True) -> list[Case]:
    out = []
    for proto in protocols:
        d = _root() / proto
        if not d.is_dir():
            continue
        for f in sorted(d.iterdir(), key=lambda p: p.name):
            if not f.name.endswith(".json"):
                continue
            raw = json.loads(f.read_text(encoding="utf-8"))
            if core_only and not raw.get("core", True):
                continue
            out.append(
                Case(
                    id=raw["id"],
                    protocol=raw["protocol"],
                    provider=raw["provider"],
                    model=raw.get("model"),
                    core=raw.get("core", True),
                    source=raw["source"],
                    features=tuple(raw["features"]),
                    expected=raw["expected"],
                    body=raw["body"],
                )
            )
    return out


def followup(protocol: str) -> str:
    raw = json.loads((_root() / "followups" / f"{protocol}.json").read_text(encoding="utf-8"))
    return str(raw["body"])


def by_id(cases: list[Case]) -> dict[str, Case]:
    return {c.id: c for c in cases}
