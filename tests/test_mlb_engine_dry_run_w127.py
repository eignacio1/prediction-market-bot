"""W127.2 Part A: opening-day dry run with the ENGINE's prices (no network, no orders, nothing live).

Same replay as test_mlb_opening_day_dry_run_w122 (LAD v ATL, four Kalshi series, T1/T2/T3 horizons, the real shadow
runner) but p_yes comes from the joint board (sim -> price_draws) instead of the v1 ridge. All 12 game cells must log
a priced row; the engine price must sit on the same side of 1 as the simulated draws; orders stay off."""
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np
import pytest

from prediction_market_bot.mlb_engine.forecaster import MLBEngineForecaster
from prediction_market_bot.mlb_engine.joint_board import price_draws
from prediction_market_bot.mlb_engine.sim import simulate
from prediction_market_bot.pregame_shadow.mlb_forecaster import MLBScheduleIndex
from prediction_market_bot.pregame_shadow.runner import run_once
from tests.test_mlb_opening_day_dry_run_w122 import CELLS, START, _games, _markets, _rows

LG = np.array([.22, .085, .14, .043, .004, .03, .478])
KEY = ("LAD", "ATL", "2026-07-15")


@pytest.fixture(scope="module")
def prices():
    d = simulate(np.tile(LG, (2, 2, 9, 1)), np.array([22., 22.]), 4000, 7)
    return price_draws(d)


@pytest.fixture()
def replay(tmp_path, monkeypatch, prices):
    monkeypatch.setenv("PM_SHADOW_DIR", str(tmp_path))
    idx = MLBScheduleIndex(_games())
    fc = MLBEngineForecaster({KEY: prices})
    skipped = {}
    for i, hours in enumerate((24.0, 6.0, 0.5)):
        res = run_once(forecaster=fc, cells=CELLS, list_markets=_markets, kickoff_for=idx.kickoff_for_event,
                       kickoff_miss_reason=idx.miss_reason_for_event, ledger_dir=tmp_path, run_id=f"eng{i}",
                       now_utc=START - timedelta(hours=hours), code_sha="dryrun")
        for k, v in res["skipped"].items():
            skipped[k] = skipped.get(k, 0) + v
    return tmp_path, skipped


def test_all_12_game_cells_log_an_engine_priced_row(replay):
    d, skipped = replay
    n = 0
    for mt, _ in CELLS:
        for band in ("T1", "T2", "T3"):
            rows = _rows(d, mt, band)
            assert rows, f"{mt}/{band} wrote no row; skipped={skipped}"
            r = rows[0]
            assert 0.0 < r["p_yes"] < 1.0 and r["model_id"].startswith("mlb_engine_joint_board")
            assert 0 < r["yes_bid"] < r["yes_ask"] < 1 and r["half_spread"] > 0 and r["band"] == band
            assert r["router"]["branch"] != "ERROR" and r["router"]["orders"] == "off"
            n += 1
    assert n == 12


def test_rung_mapping_matches_the_simulated_draws(replay, prices):
    d, _ = replay
    want = {("MLB_MONEYLINE", "KXMLBGAME-26JUL151910ATLLAD-LAD"): prices["p_home_ml"],
            ("MLB_MONEYLINE", "KXMLBGAME-26JUL151910ATLLAD-ATL"): 1 - prices["p_home_ml"],
            ("MLB_GAME_TOTAL", "KXMLBTOTAL-26JUL151910ATLLAD-7"): prices["ge_total_7"],
            ("MLB_RUN_LINE", "KXMLBSPREAD-26JUL151910ATLLAD-LAD2"): prices["home_by_ge_2"],
            ("MLB_RUN_LINE", "KXMLBSPREAD-26JUL151910ATLLAD-ATL2"): prices["away_by_ge_2"],
            ("MLB_TEAM_TOTAL", "KXMLBTEAMTOTAL-26JUL151910ATLLAD-LAD4"): prices["home_runs_ge_4"],
            ("MLB_TEAM_TOTAL", "KXMLBTEAMTOTAL-26JUL151910ATLLAD-ATL4"): prices["away_runs_ge_4"]}
    for (mt, tk), v in want.items():
        got = [r["p_yes"] for r in _rows(d, mt, "T3") if r["market_ticker"] == tk]
        assert got and abs(got[0] - min(max(v, 1e-4), 1 - 1e-4)) < 1e-9, (tk, got, v)


def test_unpriced_game_or_rung_returns_none(prices):
    fc = MLBEngineForecaster({KEY: prices})
    t = datetime(2026, 7, 15, tzinfo=timezone.utc)
    assert fc.forecast("KXMLBGAME-26JUL151910ATLLAD-LAD", t) is not None
    assert MLBEngineForecaster({}).forecast("KXMLBGAME-26JUL151910ATLLAD-LAD", t) is None
    assert fc.forecast("KXMLBTOTAL-26JUL151910ATLLAD-40", t) is None       # rung off the ladder
    assert fc.forecast("not-a-ticker", t) is None
