"""Replay server: answers any streaming request with a recorded provider stream.

Point a client's base URL at ``http://127.0.0.1:<port>/c/<session>/``. ``<session>`` is
``<case-id>~<nonce>``. The first POST in a session gets the case's recorded stream, byte for
byte, one SSE event per write; every later POST gets the protocol's recorded text-only
answer, so an agent loop that runs the tool and asks again ends cleanly. GET requests (model
lists, health checks) get an empty JSON object.
"""

from __future__ import annotations

import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

from . import corpus, sse

_CASES: dict[str, corpus.Case] = {}
_FOLLOWUPS: dict[str, str] = {}
_COUNTS: dict[str, int] = {}
_REQUESTS: dict[str, list[dict[str, Any]]] = {}
_LOCK = threading.Lock()


def requests_for(session: str) -> list[dict[str, Any]]:
    with _LOCK:
        return list(_REQUESTS.get(session, []))


def _chunks(body: str) -> list[bytes]:
    """Split a body at event boundaries, keeping every byte."""
    sep = "\r\n\r\n" if "\r\n\r\n" in body else "\n\n"
    parts = body.split(sep)
    out = [(p + sep).encode("utf-8") for p in parts[:-1]]
    if parts[-1].strip():
        # A recorded file may lose the blank line after its last event; on the wire it was there,
        # and without it an SSE parser must discard that event.
        out.append((parts[-1].rstrip("\r\n") + sep).encode("utf-8"))
    return out


class _Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, format: str, *args: Any) -> None:  # noqa: A002 - stdlib signature
        return

    def _session(self) -> str:
        parts = self.path.split("/")
        return parts[2] if len(parts) > 2 and parts[1] == "c" else ""

    def do_GET(self) -> None:  # noqa: N802 - stdlib name
        payload = b"{}"
        if self.path == "/cases":
            payload = json.dumps(
                [{"id": c.id, "protocol": c.protocol, "tool_names": c.tool_names} for c in _CASES.values()]
            ).encode()
        elif self.path.startswith("/requests/"):
            payload = json.dumps(_REQUESTS.get(self.path.split("/")[2], [])).encode()
        self.send_response(200)
        self.send_header("content-type", "application/json")
        self.send_header("content-length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def do_POST(self) -> None:  # noqa: N802 - stdlib name
        n = int(self.headers.get("content-length") or 0)
        raw = self.rfile.read(n) if n else b""
        session = self._session()
        cid = session.split("~")[0]
        case = _CASES.get(cid)
        if case is None:
            self.send_error(404, f"unknown case {cid!r}")
            return
        with _LOCK:
            k = _COUNTS.get(session, 0)
            _COUNTS[session] = k + 1
            try:
                req = json.loads(raw or b"{}")
            except json.JSONDecodeError:
                req = {}
            if not isinstance(req, dict):
                req = {}
            _REQUESTS.setdefault(session, []).append(
                {
                    "path": self.path,
                    "stream": req.get("stream"),
                    "stream_options": req.get("stream_options"),
                    "parallel_disabled": req.get("parallel_tool_calls") is False
                    or bool(
                        (req.get("tool_choice") or {}).get("disable_parallel_tool_use")
                        if isinstance(req.get("tool_choice"), dict)
                        else False
                    ),
                }
            )
        body = case.body if k == 0 else _FOLLOWUPS[case.protocol]
        self.send_response(200)
        self.send_header("content-type", "text/event-stream; charset=utf-8")
        self.send_header("cache-control", "no-cache")
        self.send_header("transfer-encoding", "chunked")
        self.end_headers()
        try:
            for chunk in _chunks(body):
                self.wfile.write(f"{len(chunk):x}\r\n".encode() + chunk + b"\r\n")
                self.wfile.flush()
            self.wfile.write(b"0\r\n\r\n")
            self.wfile.flush()
        except (BrokenPipeError, ConnectionResetError):
            pass


def start(cases: list[corpus.Case], host: str = "127.0.0.1", port: int = 0) -> ThreadingHTTPServer:
    for c in cases:
        _CASES[c.id] = c
        if c.protocol not in _FOLLOWUPS:
            _FOLLOWUPS[c.protocol] = corpus.followup(c.protocol)
    srv = ThreadingHTTPServer((host, port), _Handler)
    srv.daemon_threads = True
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv


def url(srv: ThreadingHTTPServer) -> str:
    host, port = srv.server_address[:2]
    return f"http://{host!s}:{port}"


__all__ = ["start", "url", "sse"]
