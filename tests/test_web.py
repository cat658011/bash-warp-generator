"""Tests for the web application (Node.js / Express).

The web interface has been rewritten from Flask to Node.js.
Web-specific tests now live in ``web/test/server.test.js`` and are
executed via ``cd web && npm test``.

This module validates that the Node.js server can start and respond
by spawning it as a subprocess.
"""

from __future__ import annotations

import json
import subprocess
import time
import urllib.request


def _start_server():
    """Start the Node.js web server on a test port and return the process."""
    proc = subprocess.Popen(
        ["node", "web/server.js"],
        env={**__import__("os").environ, "PORT": "5555"},
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    # Wait for server to start (up to ~3s)
    for _ in range(6):
        if proc.poll() is not None:
            break
        time.sleep(0.5)
    return proc


def test_node_server_health() -> None:
    """The Node.js web server responds to /health with {status: ok}."""
    proc = _start_server()
    try:
        with urllib.request.urlopen("http://127.0.0.1:5555/health") as resp:
            assert resp.status == 200
            data = json.loads(resp.read())
            assert data == {"status": "ok"}
    finally:
        proc.terminate()
        proc.wait()


def test_node_server_index() -> None:
    """The Node.js web server renders the index page with i18n names."""
    proc = _start_server()
    try:
        with urllib.request.urlopen("http://127.0.0.1:5555/") as resp:
            assert resp.status == 200
            html = resp.read().decode()
            assert "<form" in html
            assert "Генератор" in html
            # Config names should be resolved from i18n
            assert "Cloudflare DNS" in html
    finally:
        proc.terminate()
        proc.wait()
