"""
Regression tests for scripts/web_dashboard.py's /api/data endpoint.

GG-270/T-539: paper_portfolio_mlb_t4.json's `rejected_positions` field grows
unbounded (24k+ entries / ~33MB observed on the VPS 2026-09-10) and is never
read by the dashboard frontend. Parsing it on every request cost ~4.3s and
~96MB of peak Python-object memory, blowing past the service's 128M
MemoryMax cgroup and OOM-killing the process in a restart loop — which
looked to the browser like a dead SSH tunnel, not a crashed server.

Coverage:
  - _strip_json_array_key: byte-level array-value removal is correct,
    string/escape aware, and a no-op when the key is absent or not an array.
  - _load_json_dropping_key: drops the target key's contents without
    disturbing any other field.
  - /api/data end-to-end: 200 with a complete MLB payload when both NFL
    files are absent (T-534's NFL block is additive-only and must not be
    able to take MLB down); 200 even when T4's rejected_positions is huge;
    200 (with that one key degraded to {}) even when T4's portfolio file is
    outright corrupt — per-key isolation, not a single try/except around
    the whole payload.
"""
from __future__ import annotations

import json
import sys
import threading
import urllib.request
from http.server import HTTPServer
from pathlib import Path

import pytest

_SCRIPTS = Path(__file__).parent.parent / "scripts"
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

import web_dashboard  # noqa: E402


# ---------------------------------------------------------------------------
# _strip_json_array_key
# ---------------------------------------------------------------------------


class TestStripJsonArrayKey:
    @pytest.mark.unit
    def test_replaces_array_value_with_empty_array(self):
        text = '{"a": 1, "target": [1, 2, {"x": "]"}, 3], "b": 2}'
        out = web_dashboard._strip_json_array_key(text, "target")
        assert json.loads(out) == {"a": 1, "target": [], "b": 2}

    @pytest.mark.unit
    def test_missing_key_is_noop(self):
        text = '{"a": 1}'
        assert web_dashboard._strip_json_array_key(text, "target") == text

    @pytest.mark.unit
    def test_non_array_value_is_noop(self):
        text = '{"target": "not-an-array"}'
        assert web_dashboard._strip_json_array_key(text, "target") == text

    @pytest.mark.unit
    def test_handles_nested_brackets_and_escaped_quotes_in_strings(self):
        text = (
            '{"target": [{"note": "a \\"quoted [bracket]\\" here"}, '
            '[1, [2, 3]]], "after": true}'
        )
        out = web_dashboard._strip_json_array_key(text, "target")
        assert json.loads(out) == {"target": [], "after": True}

    @pytest.mark.unit
    def test_key_as_last_field_before_close_brace(self):
        text = '{"a": 1, "target": [1, 2, 3]}'
        out = web_dashboard._strip_json_array_key(text, "target")
        assert json.loads(out) == {"a": 1, "target": []}


class TestLoadJsonDroppingKey:
    @pytest.mark.unit
    def test_drops_key_and_keeps_other_fields(self, tmp_path):
        p = tmp_path / "portfolio.json"
        p.write_text(json.dumps({
            "bankroll_usd": 1000.0,
            "closed_positions": [{"id": 1}],
            "rejected_positions": [{"id": i} for i in range(5000)],
        }))
        result = web_dashboard._load_json_dropping_key(p, "rejected_positions")
        assert result["bankroll_usd"] == 1000.0
        assert result["closed_positions"] == [{"id": 1}]
        assert result["rejected_positions"] == []

    @pytest.mark.unit
    def test_missing_file_returns_empty(self, tmp_path):
        result = web_dashboard._load_json_dropping_key(
            tmp_path / "nope.json", "rejected_positions"
        )
        assert result == {}

    @pytest.mark.unit
    def test_malformed_json_returns_empty(self, tmp_path):
        p = tmp_path / "bad.json"
        p.write_text("{not json")
        assert web_dashboard._load_json_dropping_key(p, "rejected_positions") == {}


# ---------------------------------------------------------------------------
# /api/data — live server, end-to-end
# ---------------------------------------------------------------------------


@pytest.fixture
def dashboard_server(tmp_path, monkeypatch):
    monkeypatch.setattr(web_dashboard, "_log_dir", tmp_path)
    server = HTTPServer(("127.0.0.1", 0), web_dashboard.DashboardHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield server
    finally:
        server.shutdown()
        thread.join(timeout=5)


def _get(server: HTTPServer, path: str) -> tuple[int, bytes]:
    port = server.server_address[1]
    with urllib.request.urlopen(f"http://127.0.0.1:{port}{path}", timeout=5) as resp:
        return resp.status, resp.read()


class TestApiDataEndpoint:
    @pytest.mark.unit
    def test_returns_200_with_complete_mlb_payload_when_nfl_files_absent(
        self, dashboard_server, tmp_path
    ):
        (tmp_path / "paper_portfolio_mlb.json").write_text(json.dumps({
            "bankroll_usd": 958.99,
            "initial_bankroll_usd": 1000.0,
            "open_positions": [],
            "closed_positions": [{"outcome": "WIN", "pnl": 5.0}],
        }))
        (tmp_path / "paper_portfolio_mlb_t4.json").write_text(json.dumps({
            "bankroll_usd": 500.0,
            "initial_bankroll_usd": 1000.0,
            "open_positions": [],
            "closed_positions": [],
        }))
        # paper_portfolio_t1_nfl_game_market.json / audit_t1_nfl_game_market.jsonl
        # intentionally absent — this must not affect the MLB payload at all.

        status, body = _get(dashboard_server, "/api/data")
        assert status == 200
        data = json.loads(body)
        assert data["portfolio"]["bankroll_usd"] == 958.99
        assert data["portfolio"]["closed_positions"][0]["outcome"] == "WIN"
        assert data["t4_portfolio"]["bankroll_usd"] == 500.0
        assert data["nfl_portfolio"] == {}
        assert data["nfl_audit"] == []

    @pytest.mark.unit
    def test_large_rejected_positions_does_not_break_response(
        self, dashboard_server, tmp_path
    ):
        (tmp_path / "paper_portfolio_mlb.json").write_text(json.dumps({
            "bankroll_usd": 1000.0,
            "initial_bankroll_usd": 1000.0,
            "open_positions": [],
            "closed_positions": [],
        }))
        (tmp_path / "paper_portfolio_mlb_t4.json").write_text(json.dumps({
            "bankroll_usd": 500.0,
            "initial_bankroll_usd": 1000.0,
            "open_positions": [],
            "closed_positions": [{"outcome": "LOSS", "pnl": -1.0}],
            "rejected_positions": [
                {"id": i, "reason": "no_edge"} for i in range(20000)
            ],
        }))

        status, body = _get(dashboard_server, "/api/data")
        assert status == 200
        data = json.loads(body)
        assert data["t4_portfolio"]["bankroll_usd"] == 500.0
        assert data["t4_portfolio"]["closed_positions"] == [
            {"outcome": "LOSS", "pnl": -1.0}
        ]
        assert data["t4_portfolio"]["rejected_positions"] == []

    @pytest.mark.unit
    def test_corrupt_t4_portfolio_degrades_without_killing_response(
        self, dashboard_server, tmp_path
    ):
        (tmp_path / "paper_portfolio_mlb.json").write_text(json.dumps({
            "bankroll_usd": 1000.0,
            "initial_bankroll_usd": 1000.0,
            "open_positions": [],
            "closed_positions": [{"outcome": "WIN", "pnl": 1.0}],
        }))
        (tmp_path / "paper_portfolio_mlb_t4.json").write_text("{not valid json")

        status, body = _get(dashboard_server, "/api/data")
        assert status == 200
        data = json.loads(body)
        assert data["portfolio"]["closed_positions"][0]["outcome"] == "WIN"
        assert data["t4_portfolio"] == {}
