"""
Live Terminal front-end embedding + /api/data additive keys (Wave 43.2 / T-600).

`Live Terminal.html` (repo root) is the source of truth for the page the dashboard
serves; `scripts/web_dashboard.py::_HTML` is a verbatim embed of it. The page
contains backslashes, backticks and ${...} template literals, so the embed is easy
to corrupt silently (an escaped backslash, a reflowed line, a stripped trailing
newline) and the page would still "mostly work". These tests make drift fail loudly:
the bytes served over HTTP at GET / must equal the bytes of the source file.

Rule when this fails: fix the EMBEDDING, never the page.
"""
from __future__ import annotations

import json
import sys
import threading
import urllib.request
from http.server import HTTPServer
from pathlib import Path

import pytest

_REPO = Path(__file__).parent.parent
_SCRIPTS = _REPO / "scripts"
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

import web_dashboard  # noqa: E402

_SOURCE = _REPO / "Live Terminal.html"


@pytest.fixture
def server(tmp_path, monkeypatch):
    monkeypatch.setattr(web_dashboard, "_log_dir", tmp_path)
    srv = HTTPServer(("127.0.0.1", 0), web_dashboard.DashboardHandler)
    t = threading.Thread(target=srv.serve_forever, daemon=True)
    t.start()
    try:
        yield srv
    finally:
        srv.shutdown()
        t.join(timeout=5)


def _get(srv: HTTPServer, path: str):
    port = srv.server_address[1]
    with urllib.request.urlopen(f"http://127.0.0.1:{port}{path}", timeout=5) as resp:
        return resp.status, resp.headers, resp.read()


class TestTerminalByteFidelity:
    @pytest.mark.unit
    def test_source_file_exists_and_is_tracked_shape(self):
        assert _SOURCE.is_file(), "Live Terminal.html must live at the repo root"
        raw = _SOURCE.read_bytes()
        assert raw.startswith(b"<!DOCTYPE html>")
        assert b"\r" not in raw, "CRLF would be normalised away in transit"
        assert b'"""' not in raw, "a triple double-quote would terminate the r-string early"

    @pytest.mark.unit
    @pytest.mark.parametrize("path", ["/", "/index.html"])
    def test_served_bytes_equal_source_file_bytes(self, server, path):
        status, headers, body = _get(server, path)
        assert status == 200
        assert headers["Content-Type"].startswith("text/html")
        assert body == _SOURCE.read_bytes(), (
            "served page differs from Live Terminal.html — fix the embedding in "
            "web_dashboard.py::_HTML, not the page"
        )
        assert int(headers["Content-Length"]) == len(body)

    @pytest.mark.unit
    def test_embedded_string_equals_source_text(self):
        assert web_dashboard._HTML.encode("utf-8") == _SOURCE.read_bytes()

    @pytest.mark.unit
    def test_demo_fallback_and_not_connected_banner_survive(self):
        # Offline judgement of the page depends on both; they must never be dropped.
        raw = _SOURCE.read_text(encoding="utf-8")
        assert "DEMO" in raw
        assert "NOT CONNECTED" in raw
