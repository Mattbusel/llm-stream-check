"""Runs one adapter over a list of cases against a running replay server (subprocess side).

Usage: python -m llm_stream_check.worker <adapter> <server-url> <out.jsonl> (case ids on stdin).
Appends one JSON line per case to <out.jsonl>: {"case", "session", "observed"}. Results go to a
file, not stdout, because some frameworks print their own output to stdout.
"""

from __future__ import annotations

import asyncio
import json
import sys
import threading
import traceback
import uuid
from dataclasses import asdict
from typing import Any

from .adapters import REGISTRY
from .compare import Observed
from .corpus import by_id, load

TIMEOUT = 60.0


def _run(fn: Any, case: Any, base: str) -> Observed:
    box: dict[str, Any] = {}

    def target() -> None:
        try:
            asyncio.set_event_loop(asyncio.new_event_loop())
            box["obs"] = fn(case, base)
        except BaseException as e:  # noqa: BLE001 - every failure is reported, none hidden
            tb = traceback.extract_tb(e.__traceback__)
            where = next(
                (f"{fr.filename}:{fr.lineno}" for fr in reversed(tb) if "llm_stream_check" not in fr.filename), ""
            )
            box["obs"] = Observed(error=f"{type(e).__name__}: {e} @ {where}")

    t = threading.Thread(target=target, daemon=True)
    t.start()
    t.join(TIMEOUT)
    if t.is_alive():
        return Observed(error=f"timeout after {TIMEOUT:.0f}s")
    obs: Observed = box["obs"]
    return obs


def main(argv: list[str]) -> int:
    name, url, out = argv
    adapter = REGISTRY[name]
    with open(out, "a", encoding="utf-8") as fh:
        try:
            fn = adapter.load()
        except Exception as e:  # noqa: BLE001
            fh.write(json.dumps({"fatal": f"cannot load adapter {name}: {type(e).__name__}: {e}"}) + "\n")
            return 3
        ids = [ln.strip() for ln in sys.stdin if ln.strip()]
        cases = by_id(load(core_only=False))
        for cid in ids:
            case = cases[cid]
            session = f"{cid}~{uuid.uuid4().hex[:8]}"
            obs = _run(fn, case, f"{url}/c/{session}")
            fh.write(json.dumps({"case": cid, "session": session, "observed": asdict(obs)}, default=str) + "\n")
            fh.flush()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
