#!/usr/bin/env python3
"""Lightweight mock of Ollama's HTTP endpoints for CI smoke tests.

Provides /api/version, /api/chat, /api/generate, /api/tags and /api/ps.
Designed for quick integration tests; not a full Ollama implementation.
"""
from __future__ import annotations

import argparse
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Tuple


class MockHandler(BaseHTTPRequestHandler):
    server_version = "BatLLM-Ollama-Mock/0.1"

    def _send_json(self, obj, code=200):
        data = json.dumps(obj).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if self.path == "/api/version":
            self._send_json({"version": "mock-0.0.0"})
            return
        if self.path == "/api/tags":
            # minimal local model listing
            self._send_json({"models": [{"name": "smollm2"}, {"name": "mistral-small:latest"}]})
            return
        if self.path == "/api/ps":
            self._send_json({"models": [{"name": "smollm2"}]})
            return

        self.send_response(404)
        self.end_headers()

    def do_POST(self):
        length = int(self.headers.get("Content-Length") or 0)
        body = self.rfile.read(length) if length else b""
        try:
            payload = json.loads(body.decode("utf-8")) if body else {}
        except Exception:
            payload = {}

        if self.path == "/api/chat":
            # Echo/interpret simple instructions for predictable smoke responses
            content = ""
            messages = payload.get("messages") or []
            if isinstance(messages, list) and messages:
                last = messages[-1]
                content = (last.get("content") or "").strip()

            if "Reply with exactly OK" in content:
                reply = "OK"
            elif "Reply with exactly M" in content:
                reply = "M"
            else:
                reply = "mock reply"

            self._send_json({"message": {"content": reply}})
            return

        if self.path == "/api/generate":
            model = payload.get("model")
            keep_alive = payload.get("keep_alive")
            # respond with a small payload acknowledging the request
            self._send_json({"model": model, "keep_alive": keep_alive})
            return

        # Unknown path
        self.send_response(404)
        self.end_headers()


def run_server(host: str, port: int) -> None:
    server = ThreadingHTTPServer((host, port), MockHandler)
    print(f"Mock Ollama server listening on http://{host}:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


def parse_args() -> Tuple[str, int]:
    p = argparse.ArgumentParser(description="Mock Ollama HTTP server for CI smoke tests")
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--port", type=int, default=11434)
    args = p.parse_args()
    return args.host, args.port


if __name__ == "__main__":
    host, port = parse_args()
    run_server(host, port)
