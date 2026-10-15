"""W75.5 / GG-746, GG-751, GG-763a: typed settlement results, position sweep, open-past-end invariant."""
from __future__ import annotations

import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from prediction_market_bot.c1_signal_ingestion import nfl_espn_results as espn
from prediction_market_bot.c5_execution.paper_trader import PaperTrader
from prediction_market_bot.c6_audit_logger.audit_logger import AuditLogger
from prediction_market_bot.pregame_shadow import mlb_settlement as ms
from prediction_market_bot.pregame_shadow import nba_settlement as nbs
from prediction_market_bot.pregame_shadow import nfl_settlement as nfs
from prediction_market_bot.pregame_shadow import settle_result as sr
from prediction_market_bot.position_sweep import sweep_open_positions
import assert_ledger_invariants as ali
import run_pregame_shadow_settle as rps

EARLY = datetime(2026, 10, 4, 12, tzinfo=timezone.utc)    # inside the window for a 10-04 game
LATE = datetime(2026, 10, 8, 12, tzinfo=timezone.utc)     # well past end + grace
CLIM = {"home_win_rate_ex_ties": 0.55, "home_win_rate": 0.55, "mean_margin": 1.5, "mean_total": 45.0,
        "sd_margin": 13.5, "sd_total": 13.0}


# ── settle_result ───────────────────────────────────────────────────────────
def test_missing_final_window():
    assert sr.missing_final("2026-10-04", EARLY).status == sr.NOT_FINAL
    r = sr.missing_final("2026-10-04", LATE)
    assert r.status == sr.LOOKUP_FAILED and r.is_alarm and "2026-10-04" in r.reason


# ── NFL ─────────────────────────────────────────────────────────────────────
NFL_ROW = {"market_ticker": "KXNFLGAME-26OCT04ARINYG-NYG", "market_type": "NFL_MONEYLINE"}


def test_nfl_typed_join_three_states_and_tie():
    r = nfs.typed_join(NFL_ROW, "2026-10-04", ("NYG", "ARI", 20, 17), CLIM, EARLY)
    assert r.status == sr.FINAL and r.outcome["y"] == 1.0
    assert nfs.typed_join(NFL_ROW, "2026-10-04", None, CLIM, EARLY).status == sr.NOT_FINAL
    assert nfs.typed_join(NFL_ROW, "2026-10-04", None, CLIM, LATE).status == sr.LOOKUP_FAILED
    bad = nfs.typed_join({"market_ticker": "garbage"}, "2026-10-04", ("NYG", "ARI", 20, 17), CLIM, EARLY)
    assert bad.status == sr.LOOKUP_FAILED
    # GG-763a: pre-registration EXP-037 says a moneyline tie is y=0.5 -- FINAL, never a failure.
    tie = nfs.typed_join(NFL_ROW, "2026-10-04", ("NYG", "ARI", 20, 20), CLIM, EARLY)
    assert tie.status == sr.FINAL and tie.outcome["y"] == 0.5


def test_nfl_settle_alarms_on_overdue_missing_final(tmp_path):
    import json
    row = {"market_ticker": NFL_ROW["market_ticker"], "market_type": "NFL_MONEYLINE", "band": "T1",
           "run_id": "r", "ts_utc": "2026-10-03T00:00:00+00:00"}
    (tmp_path / "NFL_NFL_MONEYLINE_T1.jsonl").write_text(json.dumps(row) + "\n")
    sched = pd.DataFrame({"gameday": [], "home_team": [], "away_team": [], "home_score": [], "away_score": []})
    alarms: list = []
    assert rps.settle(tmp_path, sched, CLIM, "NFL", alarms, LATE) == {"NFL_NFL_MONEYLINE_T1": 0}
    assert len(alarms) == 1 and alarms[0]["market_ticker"] == row["market_ticker"]
    alarms2: list = []
    rps.settle(tmp_path, sched, CLIM, "NFL", alarms2, EARLY)
    assert alarms2 == []                                     # inside the window: wait, no alarm
    alarms3: list = []                                       # a final present: settles, no alarm
    sched = pd.DataFrame({"gameday": ["2026-10-04"], "home_team": ["NYG"], "away_team": ["ARI"],
                          "home_score": [20.0], "away_score": [20.0]})
    assert rps.settle(tmp_path, sched, CLIM, "NFL", alarms3, LATE) == {"NFL_NFL_MONEYLINE_T1": 1}
    assert alarms3 == []
    out = json.loads((tmp_path / "settled" / "NFL_NFL_MONEYLINE_T1.jsonl").read_text().splitlines()[0])
    assert out["y"] == 0.5


# ── NBA ─────────────────────────────────────────────────────────────────────
def test_nba_typed_join_three_states():
    t = "KXNBAGAME-26OCT20LALGSW-GSW"
    from prediction_market_bot.pregame_shadow.nba_forecaster import parse_market_ticker
    p = parse_market_ticker(t)
    assert p is not None, "NBA ticker fixture must parse"
    row = {"market_ticker": t}
    clim = {**CLIM}
    d = p["game_date"]
    early = datetime.fromisoformat(f"{d}T12:00:00+00:00")
    late = early + timedelta(days=5)
    assert nbs.typed_join(row, d, (p["home"], p["away"], 110.0, 100.0), clim, early).status == sr.FINAL
    assert nbs.typed_join(row, d, None, clim, early).status == sr.NOT_FINAL
    assert nbs.typed_join(row, d, None, clim, late).status == sr.LOOKUP_FAILED
    assert nbs.typed_join({"market_ticker": "x"}, d, (p["home"], p["away"], 1.0, 2.0), clim, early).status \
        == sr.LOOKUP_FAILED


# ── MLB ─────────────────────────────────────────────────────────────────────
def _mlb_finals(status="Final"):
    g = pd.DataFrame([{"game_pk": 1, "game_type": "D", "season": 2026, "game_date": "2026-10-03",
                       "start_utc": "2026-10-03T20:00:00Z", "status": status, "home": "LAD", "away": "ATL",
                       "home_score": 5.0, "away_score": 3.0}])
    return ms.final_games(g)


def test_mlb_typed_join_three_states():
    row = {"market_ticker": "KXMLBGAME-26OCT031600ATLLAD-LAD"}
    now_early = datetime(2026, 10, 3, 22, tzinfo=timezone.utc)
    now_late = datetime(2026, 10, 9, tzinfo=timezone.utc)
    r = ms.typed_join(row, _mlb_finals(), now_early)
    assert r.status == sr.FINAL and r.outcome["y"] == 1.0
    assert ms.typed_join(row, _mlb_finals("Live"), now_early).status == sr.NOT_FINAL
    assert ms.typed_join(row, _mlb_finals("Live"), now_late).status == sr.LOOKUP_FAILED
    assert ms.typed_join({"market_ticker": "KXMLBGAME-26OCT031600ATLLAD-XXX"}, _mlb_finals(), now_early).status \
        == sr.LOOKUP_FAILED


# ── ESPN fetcher ────────────────────────────────────────────────────────────
def _event(status, hs="24", as_="16", home="TB", away="DAL"):
    return {"competitions": [{"status": {"type": {"name": status}}, "competitors": [
        {"homeAway": "home", "team": {"abbreviation": home}, "score": hs},
        {"homeAway": "away", "team": {"abbreviation": away}, "score": as_}]}]}


def _fetch(events, err=None, d="2026-10-08"):
    with patch.object(espn, "_espn_scoreboard_events_checked", return_value=(events, err)):
        return espn.fetch_nfl_final_result(d, "TB", "DAL")


def test_espn_typed_result():
    assert _fetch([_event("STATUS_FINAL")]).outcome.home_score == 24.0
    assert _fetch([_event("STATUS_IN_PROGRESS")]).status == sr.NOT_FINAL
    assert _fetch([_event("STATUS_POSTPONED")]).status == sr.LOOKUP_FAILED
    assert _fetch([_event("STATUS_FINAL", hs="x")]).status == sr.LOOKUP_FAILED
    assert _fetch([], err="espn_request_failed: boom").status == sr.LOOKUP_FAILED      # not "not final yet"
    assert _fetch([_event("STATUS_FINAL", home="XX")], d="2020-01-01").status == sr.LOOKUP_FAILED  # overdue, absent
    assert espn.fetch_nfl_final_score  # legacy API intact


def test_espn_request_failure_is_reported(monkeypatch):
    def boom(*a, **k):
        raise RuntimeError("down")
    monkeypatch.setattr(espn.requests, "get", boom)
    events, err = espn._espn_scoreboard_events_checked("2026-10-08", delays=())
    assert events == [] and err and "down" in err


# ── position sweep (GG-746) ─────────────────────────────────────────────────
def _pf(tmp_path, positions):
    t = PaperTrader(tmp_path / "p.json", AuditLogger(log_path=tmp_path / "a.jsonl"))
    for pid, tick, gd in positions:
        t._state["open_positions"].append({
            "position_id": pid, "player_name": "X", "direction": "YES", "size_usd": 10.0,
            "mid_price_at_entry": 0.40, "vig_at_entry": 0.02, "model_p": 0.5, "logic_epoch": 12,
            "status": "OPEN", "kalshi_ticker": tick, "game_date": gd})
    t._save()


def test_sweep_books_settled_waits_and_alarms(tmp_path):
    _pf(tmp_path, [("A", "T-A", "2026-10-08"), ("B", "T-B", "2026-10-08"), ("C", "T-C", "2026-10-08"),
                   ("D", "T-D", "2026-10-08")])
    states = {"T-A": ("settled", {"result": "yes"}), "T-B": ("not_final", {}),
              "T-C": ("unknown", {}), "T-D": ("cancelled", {"result": "scalar", "settlement_value_dollars": "0.5"})}
    rep = sweep_open_positions(tmp_path / "p.json", tmp_path / "a.jsonl", apply=True,
                               state_fn=lambda t: states[t], now=datetime(2026, 10, 14, tzinfo=timezone.utc),
                               pause_s=0)
    assert rep["open_before"] == 4 and rep["booked"] == 2 and rep["open_after"] == 2
    assert {a["position_id"] for a in rep["alarms"]} >= {"B", "C"}      # B overdue -> alarm; C unknown -> alarm
    rep2 = sweep_open_positions(tmp_path / "p.json", tmp_path / "a.jsonl", apply=True,
                                state_fn=lambda t: states[t], now=EARLY, pause_s=0)
    assert [w["position_id"] for w in rep2["not_final"]] == ["B"]       # inside the window: wait, no alarm
    assert [a["position_id"] for a in rep2["alarms"]] == ["C"]          # unknown venue state still alarms
    assert rep2["open_after"] == 2 and rep2["booked"] == 0              # idempotent


def test_sweep_plan_does_not_write(tmp_path):
    _pf(tmp_path, [("A", "T-A", "2026-10-08")])
    before = (tmp_path / "p.json").read_text()
    rep = sweep_open_positions(tmp_path / "p.json", tmp_path / "a.jsonl", apply=False,
                               state_fn=lambda t: ("settled", {"result": "yes"}), now=LATE, pause_s=0)
    assert rep["bookable"] == 1 and rep["booked"] == 0
    assert (tmp_path / "p.json").read_text() == before


# ── invariant ───────────────────────────────────────────────────────────────
def test_open_past_game_end_invariant():
    books = {"nfl": {"open_positions": [
        {"position_id": "OLD", "kalshi_ticker": "T", "game_date": "2026-10-08", "status": "OPEN"},
        {"position_id": "NEW", "kalshi_ticker": "U", "game_date": "2026-10-13", "status": "OPEN"},
        {"position_id": "NOD", "kalshi_ticker": "V", "status": "OPEN"}]},
        "mlb": {"open_positions": []}}
    out = ali.assert_open_past_game_end(books, now=datetime(2026, 10, 14, tzinfo=timezone.utc))
    assert out["n_open"] == 3 and out["n_violations"] == 1
    assert out["violations"][0]["position_id"] == "OLD"
