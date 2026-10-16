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
        # v2 (47.1 D6): demo data only behind an explicit ?demo flag; default is NOT LIVE.
        assert "DEMO_FLAG" in raw and "DEMO" in raw
        assert "NOT LIVE" in raw
        assert "NOT CONNECTED" not in raw, "the old silent demo fallback must not return"


# ─────────────────────────────────────────────────────────────────────────────
# /api/data additive keys (D2) — one test group per key
# ─────────────────────────────────────────────────────────────────────────────
_EXISTING_KEYS = {
    "portfolio", "t4_portfolio", "audit", "t4_audit", "pipe_log", "pipe_mtimes",
    "server_time", "current_logic_epoch", "nfl_portfolio", "nfl_audit",
    "nfl_model_provenance",
}


def _portfolio_text(n_rejected: int, tricky: bool = False) -> str:
    rej = []
    for i in range(n_rejected):
        rej.append({"ticker": f"K{i}", "reason": 'has ] and [ and "quote" \\ inside' if tricky else "x",
                    "nested": {"a": [1, 2, {"b": "]"}]}})
    return json.dumps({"bankroll_usd": 1.0, "open_positions": [], "rejected_positions": rej,
                       "last_updated": "t"}, indent=2)


def _api(srv):
    status, _h, body = _get(srv, "/api/data")
    assert status == 200
    return json.loads(body)


class TestRejectedCounts:
    @pytest.mark.unit
    def test_counts_per_pool_and_never_ships_the_arrays(self, server, tmp_path):
        (tmp_path / "paper_portfolio_mlb.json").write_text(_portfolio_text(3, tricky=True))
        (tmp_path / "paper_portfolio_mlb_t4.json").write_text(_portfolio_text(2000))
        (tmp_path / "paper_portfolio_t1_nfl_game_market.json").write_text(_portfolio_text(0))
        d = _api(server)
        assert d["rejected_counts"] == {"mlb": 3, "mlb_t4": 2000, "nfl": 0}
        assert d["t4_portfolio"].get("rejected_positions") == []  # still dropped pre-parse

    @pytest.mark.unit
    def test_missing_file_is_none_not_zero(self, server):
        assert _api(server)["rejected_counts"] == {"mlb": None, "mlb_t4": None, "nfl": None}

    @pytest.mark.unit
    def test_array_not_last_key_and_compact_small_file(self, tmp_path):
        p = tmp_path / "p.json"
        p.write_text(json.dumps({"rejected_positions": [{"a": 1}, {"b": [1, 2]}], "z": [1, 2, 3]}, indent=2))
        assert web_dashboard._count_json_array_key(p, "rejected_positions") == 2

    @pytest.mark.unit
    def test_overlong_line_aborts_to_none(self, tmp_path, monkeypatch):
        monkeypatch.setattr(web_dashboard, "_COUNT_LINE_LIMIT", 64)
        p = tmp_path / "p.json"
        p.write_text(json.dumps({"rejected_positions": [{"a": "x" * 500}]}))  # single line
        assert web_dashboard._count_json_array_key(p, "rejected_positions") is None

    @pytest.mark.unit
    def test_cache_invalidates_on_change(self, tmp_path):
        p = tmp_path / "p.json"
        p.write_text(_portfolio_text(2))
        assert web_dashboard._count_json_array_key(p, "rejected_positions") == 2
        p.write_text(_portfolio_text(5))
        assert web_dashboard._count_json_array_key(p, "rejected_positions") == 5

    @pytest.mark.unit
    def test_failure_isolated(self, server, monkeypatch):
        def boom(*a, **k):
            raise RuntimeError("x")
        monkeypatch.setattr(web_dashboard, "_rejected_counts", boom)
        d = _api(server)
        assert d["rejected_counts"] == {}
        assert _EXISTING_KEYS <= set(d)


class TestCycleTail:
    @pytest.mark.unit
    def test_tail_is_bounded_and_ordered(self, server, tmp_path):
        rows = [{"ts": f"2026-09-30T00:{i // 60:02d}:{i % 60:02d}Z", "cycle_id": f"C{i}"} for i in range(500)]
        (tmp_path / ".vps_t4_mlb_cycle_log_cache.jsonl").write_text("\n".join(json.dumps(r) for r in rows) + "\n")
        t = _api(server)["t4_cycle_tail"]
        assert len(t) == web_dashboard.CYCLE_TAIL_ROWS
        assert t[-1]["cycle_id"] == "C499" and t[0]["cycle_id"] == "C300"

    @pytest.mark.unit
    def test_falls_back_to_native_log_name_and_empty_when_absent(self, server, tmp_path):
        assert _api(server)["t4_cycle_tail"] == []
        (tmp_path / "t4_mlb_cycle_log.jsonl").write_text('{"ts":"t","cycle_id":"C1"}\n')
        assert _api(server)["t4_cycle_tail"] == [{"ts": "t", "cycle_id": "C1"}]

    @pytest.mark.unit
    def test_does_not_read_whole_file(self, tmp_path):
        p = tmp_path / ".vps_t4_mlb_cycle_log_cache.jsonl"
        with open(p, "w") as f:
            for i in range(60000):  # ~ several MB
                f.write(json.dumps({"ts": "t", "cycle_id": f"C{i}", "pad": "x" * 80}) + "\n")
        reads = []
        real_open = open

        def spy(file, mode="r", *a, **k):
            fh = real_open(file, mode, *a, **k)
            if str(file).endswith(".jsonl") and "b" in mode:
                orig = fh.read
                fh.read = lambda n=-1: (reads.append(n), orig(n))[1]
            return fh
        import builtins
        builtins_open = builtins.open
        builtins.open = spy
        try:
            out = web_dashboard._load_cycle_tail(tmp_path)
        finally:
            builtins.open = builtins_open
        assert len(out) == web_dashboard.CYCLE_TAIL_ROWS
        assert reads and all(n != -1 and n <= (1 << 16) for n in reads)

    @pytest.mark.unit
    def test_failure_isolated(self, server, monkeypatch):
        monkeypatch.setattr(web_dashboard, "_load_cycle_tail", lambda *a, **k: 1 / 0)
        d = _api(server)
        assert d["t4_cycle_tail"] == []
        assert _EXISTING_KEYS <= set(d)


class TestProcessInfo:
    @pytest.mark.unit
    def test_started_at_and_sha_shape(self, server):
        pr = _api(server)["process"]
        import re
        assert re.fullmatch(r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ", pr["started_at"])
        assert pr["sha"] == "unknown" or re.fullmatch(r"[0-9a-f]{40}", pr["sha"])

    @pytest.mark.unit
    def test_sha_is_fixed_at_import_not_per_request(self, server, monkeypatch):
        monkeypatch.setattr(web_dashboard, "_RUNNING_SHA", "a" * 40)
        assert _api(server)["process"]["sha"] == "a" * 40

    @pytest.mark.unit
    def test_resolver_degrades_to_unknown(self, monkeypatch):
        def boom(*a, **k):
            raise OSError("no git")
        monkeypatch.setattr(web_dashboard.subprocess, "run", boom)
        assert web_dashboard._resolve_running_sha() == "unknown"

    @pytest.mark.unit
    def test_existing_keys_unchanged_additive_only(self, server):
        d = _api(server)
        assert _EXISTING_KEYS <= set(d)
        assert {"rejected_counts", "t4_cycle_tail", "process"} <= set(d)
        assert set(d) - _EXISTING_KEYS == {
            "rejected_counts", "t4_cycle_tail", "process",
            "season", "freshness", "origin", "coverage", "shadow", "verdicts", "mlb_postseason", "pipeline", "decisions", "t4_execution", "t1_execution", "silent_arms", "runtime"}


class TestTerminalWiring:
    @pytest.mark.unit
    def test_status_bar_fields_and_contract_present(self):
        raw = _SOURCE.read_text(encoding="utf-8")
        for needle in ('id="sha"', 'id="cyc"', "statusExtras", "cycleRate",
                       "rejected_counts", "t4_cycle_tail", "process{"):
            assert needle in raw, needle
