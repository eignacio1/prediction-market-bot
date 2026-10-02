"""Operator terminal v2 additive /api/data keys (Wave 47 / 47.1 D6).

Every key: populated case, empty dir, missing-file case, and failure isolation.
A missing source must say "awaiting ..." — never a placeholder number.
"""
from __future__ import annotations

import json
import sys
import threading
import urllib.request
from datetime import datetime, timedelta, timezone
from http.server import HTTPServer
from pathlib import Path

import pytest

_REPO = Path(__file__).parent.parent
sys.path.insert(0, str(_REPO / "scripts"))
import web_dashboard as wd  # noqa: E402

NOW = datetime(2026, 10, 2, 20, 0, tzinfo=timezone.utc)


@pytest.fixture
def server(tmp_path, monkeypatch):
    monkeypatch.setattr(wd, "_log_dir", tmp_path)
    srv = HTTPServer(("127.0.0.1", 0), wd.DashboardHandler)
    t = threading.Thread(target=srv.serve_forever, daemon=True)
    t.start()
    yield srv
    srv.shutdown()
    t.join(timeout=5)


def _api(srv):
    with urllib.request.urlopen(f"http://127.0.0.1:{srv.server_address[1]}/api/data", timeout=5) as r:
        return json.loads(r.read())


class TestSeason:
    @pytest.mark.unit
    def test_wednesday_in_season_vs_offseason(self):
        s = wd._season_state(NOW)
        assert s["NFL"]["state"] == "in_season" and s["MLB_POSTSEASON"]["state"] == "in_season"
        jul = wd._season_state(datetime(2026, 7, 8, tzinfo=timezone.utc))
        assert jul["NFL"]["state"] == "off" and jul["NFL"]["red_s"] is None
        assert jul["MLB_POSTSEASON"]["state"] == "off"


class TestFreshness:
    @pytest.mark.unit
    def test_empty_dir_is_awaiting_not_a_number(self, tmp_path):
        f = wd._freshness(tmp_path, NOW)
        for v in f.values():
            assert v["age_s"] is None and v["awaiting"] and v["level"] == "none"

    @pytest.mark.unit
    def test_levels_amber_red_and_offseason_is_not_red(self, tmp_path):
        import os
        p = tmp_path / "paper_portfolio_mlb.json"
        p.write_text("{}")
        old = (NOW - timedelta(hours=10)).timestamp()
        os.utime(p, (old, old))
        assert wd._freshness(tmp_path, NOW)["t1_mlb"]["level"] == "amber"
        older = (NOW - timedelta(hours=30)).timestamp()
        os.utime(p, (older, older))
        assert wd._freshness(tmp_path, NOW)["t1_mlb"]["level"] == "red"
        nfl = tmp_path / "audit_t1_nfl_game_market.jsonl"
        nfl.write_text("{}\n")
        os.utime(nfl, (older, older))
        july = datetime(2026, 7, 8, tzinfo=timezone.utc)
        os.utime(nfl, (july.timestamp() - 40 * 86400,) * 2)
        assert wd._freshness(tmp_path, july)["nfl"]["level"] == "off"

    @pytest.mark.unit
    def test_t4_age_from_last_row_ts(self, tmp_path):
        ts = (NOW - timedelta(minutes=5)).strftime("%Y-%m-%dT%H:%M:%SZ")
        (tmp_path / "t4_mlb_cycle_log.jsonl").write_text(json.dumps({"ts": ts}) + "\n")
        assert 299 <= wd._freshness(tmp_path, NOW)["t4_mlb"]["age_s"] <= 301


class TestOrigin:
    @pytest.mark.unit
    def test_shape_and_running_sha(self):
        wd._ORIGIN_CACHE.update(at=0.0, val=None)
        o = wd._origin_status()
        assert o["running_sha"] == wd._RUNNING_SHA
        assert "origin_sha" in o or o.get("awaiting")

    @pytest.mark.unit
    def test_no_git_ref_says_awaiting(self, monkeypatch):
        wd._ORIGIN_CACHE.update(at=0.0, val=None)
        monkeypatch.setattr(wd, "_git", lambda a: None)
        assert wd._origin_status()["awaiting"] == "origin/main ref"


class TestCoverage:
    @pytest.mark.unit
    def test_grid_counts_match_registry(self):
        c = wd._coverage(NOW)
        assert c["total"] == sum(c["counts"].values()) == len(c["cells"])
        assert c["counts"].get("active") == 1 and "shadow" in c["counts"]
        assert all(x["status"] in {"active", "shadow", "blocked", "dark", "ruled_out", "not_implemented"}
                   for x in c["cells"])
        assert all(x["recent"] for x in c["cells"] if x["status"] == "shadow")


class TestShadow:
    @pytest.mark.unit
    def test_no_ledgers_awaiting_and_no_numbers(self, tmp_path, monkeypatch):
        monkeypatch.setattr(wd, "_REPO_ROOT", tmp_path)
        s = wd._shadow(NOW)
        assert s["cells"] == [] and s["tape"] == [] and s["awaiting"]

    @pytest.mark.unit
    def test_rows_group_by_cell_and_scored_summary(self, tmp_path, monkeypatch):
        monkeypatch.setattr(wd, "_REPO_ROOT", tmp_path)
        d = tmp_path / "logs" / "shadow"
        d.mkdir(parents=True)
        rows = [{"ts_utc": "2026-10-02T18:00:00Z", "sport": "NHL", "market_type": "MONEYLINE", "band": "T1",
                 "market_ticker": "K1", "p_yes": 0.5, "mid": 0.5, "e_net_yes_k007": 0.01, "e_net_no_k007": -0.02},
                {"ts_utc": "2026-10-01T18:00:00Z", "sport": "NHL", "market_type": "MONEYLINE", "band": "T1",
                 "market_ticker": "K0", "p_yes": 0.4, "mid": 0.4, "e_net_yes_k007": 0.5}]
        (d / "nhl.jsonl").write_text("\n".join(json.dumps(r) for r in rows) + "\n")
        s = wd._shadow(NOW)
        c = s["cells"][0]
        assert c["rows_today"] == 1 and c["last_ts"] == "2026-10-02T18:00:00Z"
        assert c["latest_e_net"] == 0.01 and c["settled_n"] is None   # unscored stays None
        assert s["tape"][0]["market_ticker"] == "K1"
        (d / "nhl.scored.json").write_text(json.dumps({"settled_n": 12, "judged_n": 9, "delta_brier_market": -0.002}))
        c = wd._shadow(NOW)["cells"][0]
        assert (c["settled_n"], c["judged_n"], c["delta_brier_market"]) == (12, 9, -0.002)


class TestVerdicts:
    @pytest.mark.unit
    def test_missing_files_awaiting(self, tmp_path, monkeypatch):
        monkeypatch.setattr(wd, "_REPO_ROOT", tmp_path)
        v = wd._verdicts()
        assert set(v) == {"GATE2", "EXP-034", "EXP-035"}
        assert all("awaiting" in x for x in v.values())

    @pytest.mark.unit
    def test_shapes_all_passed_and_nested_gate(self, tmp_path, monkeypatch):
        monkeypatch.setattr(wd, "_REPO_ROOT", tmp_path)
        for rel, body in (("exp_output/BOARD_SURVEY_SPORTS_G2/gate2_result.json", {"ALL_PASSED": True}),
                          ("exp_output/EXP-034-NONSPORTS-CONTROL/d1b_gate_result.json", {"gate": {"gate": "FAIL"}}),
                          ("exp_output/EXP-035-BOARD-SURVEY-SPORTS/gate_result.json", {"ALL_PASSED": False})):
            p = tmp_path / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(json.dumps(body))
        v = wd._verdicts()
        assert v["GATE2"]["passed"] is True and v["GATE2"]["verdict"] == "PASS"
        assert v["EXP-034"]["passed"] is False and v["EXP-034"]["verdict"] == "FAIL"
        assert v["EXP-035"]["passed"] is False


class TestPostseason:
    @pytest.mark.unit
    def test_empty_is_awaiting(self, tmp_path):
        m = wd._mlb_postseason(tmp_path, NOW, {}, {})
        assert m["t1_players_matched_last_run"] is None and m["t4_cycle_age_s"] is None and m["awaiting"]

    @pytest.mark.unit
    def test_matched_stuck_and_open(self, tmp_path):
        (tmp_path / "paper_mlb_cron.log").write_text("noise\n21 players in live MLB markets\n")
        old = (NOW - timedelta(hours=40)).strftime("%Y-%m-%dT%H:%M:%SZ")
        new = (NOW - timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%SZ")
        m = wd._mlb_postseason(tmp_path, NOW, {"open_positions": [{"entry_time": old}]},
                               {"open_positions": [{"entry_time": new}]})
        assert (m["t1_players_matched_last_run"], m["open_positions"], m["stuck_positions"]) == (21, 2, 1)
        assert m["awaiting"] is None


class TestApiIntegration:
    @pytest.mark.unit
    def test_new_keys_present_on_empty_dir_and_fast(self, server):
        import time
        t = time.time()
        d = _api(server)
        assert time.time() - t < 2
        for k in ("season", "freshness", "origin", "coverage", "shadow", "verdicts", "mlb_postseason"):
            assert k in d
        assert d["coverage"]["total"] > 0

    @pytest.mark.unit
    @pytest.mark.parametrize("fn", ["_season_state", "_freshness", "_origin_status", "_coverage",
                                    "_shadow", "_verdicts", "_mlb_postseason"])
    def test_failure_isolated(self, server, monkeypatch, fn):
        monkeypatch.setattr(wd, fn, lambda *a, **k: 1 / 0)
        d = _api(server)
        assert "portfolio" in d and "process" in d


class TestFrontendContract:
    @pytest.mark.unit
    def test_page_wiring(self):
        raw = (_REPO / "Live Terminal.html").read_text(encoding="utf-8")
        for needle in ("DEMO_FLAG", "NOT LIVE", "viewCoverage", "viewShadow", "viewPost", "viewVerdicts",
                       "paintFresh", 'id="osha"', "data-fr", "fillV2", "body.demo .panel::after"):
            assert needle in raw, needle


# ── pipeline (D6 g) ────────────────────────────────────────────────────────

class TestPipeline:
    def test_empty_dir_every_component_tile_present_and_gaps_listed(self, server):
        p = _api(server)["pipeline"]
        comps = {(t["c"], t["sport"]) for t in p["tiles"]}
        for c in ("C1", "C2", "C3", "C4", "C5", "C6", "C7"):
            assert (c, "MLB") in comps and (c, "NFL") in comps
        assert ("C8", "SERVER") in comps
        ni = [t for t in p["tiles"] if t["status"] == "ni"]
        assert ni and len(p["gaps"]) == len(ni)

    def test_ni_tiles_say_not_instrumented(self, server):
        for t in _api(server)["pipeline"]["tiles"]:
            if t["status"] == "ni":
                assert "not instrumented" in t["headline"]

    def test_c8_present_with_sha(self, server):
        c8 = [t for t in _api(server)["pipeline"]["tiles"] if t["c"] == "C8"][0]
        assert "sha" in (c8["headline"] + c8["detail"]).lower()

    def test_stale_feature_store_is_not_silently_ok(self, tmp_path, monkeypatch):
        store = tmp_path / "f.csv"
        store.write_text("game_date,x\n2026-09-27,1\n")
        monkeypatch.setattr(wd, "FEATURE_STORES", {"MLB": str(store)})
        t = wd._pipeline(tmp_path, NOW, {})["tiles"]
        c2 = [x for x in t if x["c"] == "C2" and x["sport"] == "MLB"][0]
        assert "2026-09-27" in c2["headline"] + c2["detail"]

    def test_corrupt_audit_file_does_not_break_pipeline(self, tmp_path):
        (tmp_path / "audit_t1_nfl_game_market.jsonl").write_text("{not json\n\n")
        assert wd._pipeline(tmp_path, NOW, {})["tiles"]

    def test_failure_isolated_to_pipeline_key(self, server, monkeypatch):
        def boom(*a, **k):
            raise RuntimeError("x")
        monkeypatch.setattr(wd, "_pipeline", boom)
        d = _api(server)
        assert d["pipeline"]["tiles"] == [] and "awaiting" in d["pipeline"]
        assert "portfolio" in d
