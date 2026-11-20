"""W122.4 / GG-1957: opening-day dry run for the 12 MLB game cells (no network, no orders, nothing live).

Replays one 2026 date (2026-07-15, LAD vs ATL, 19:10 ET) through the real shadow runner at three horizons so each of
T1 / T2 / T3 is hit, with the four Kalshi series (KXMLBGAME / KXMLBSPREAD / KXMLBTOTAL / KXMLBTEAMTOTAL) listed.
Every registered game cell (4 market types x 3 bands) must write a row with a model p, the market state and the arm the
pinned 2027 leaf map chooses. Layer 1 of D6 is credited by a logged p_yes, so this is the 3 -> 12 measure for the game cells.
"""
import hashlib
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pandas as pd
import pytest

from prediction_market_bot.c1_signal_ingestion.mlb_game_pregame_features import MLBGameFeatureBuilder
from prediction_market_bot.decision_trees import leaf_map as lm
from prediction_market_bot.pregame_shadow.mlb_forecaster import MLBForecaster, MLBScheduleIndex, parse_market_ticker
from prediction_market_bot.pregame_shadow.mlb_model import MLBPregameModel
from prediction_market_bot.pregame_shadow.runner import run_once

ROOT = Path(__file__).resolve().parent.parent
MODEL = ROOT / "models" / "mlb_game_pregame_v1.json"
MAP_2027 = ROOT / "src" / "prediction_market_bot" / "decision_trees" / "leaf_maps" / "mlb_2026_lookback.json"
pytestmark = pytest.mark.skipif(not MODEL.exists(), reason="frozen artifact not present")

CELLS = [("MLB_MONEYLINE", "KXMLBGAME"), ("MLB_RUN_LINE", "KXMLBSPREAD"),
         ("MLB_GAME_TOTAL", "KXMLBTOTAL"), ("MLB_TEAM_TOTAL", "KXMLBTEAMTOTAL")]
EVENT_SUFFIX = "26JUL151910ATLLAD"            # ET first pitch 19:10 -> 23:10Z
START = datetime(2026, 7, 15, 23, 10, tzinfo=timezone.utc)
LADDER = {"KXMLBGAME": ["LAD", "ATL"], "KXMLBSPREAD": ["LAD2", "ATL2"], "KXMLBTOTAL": ["7", "9"],
          "KXMLBTEAMTOTAL": ["LAD4", "ATL4"]}


def _games() -> pd.DataFrame:
    rows, pk = [], 1
    for day in range(60):
        d = (datetime(2026, 5, 1) + timedelta(days=day)).date().isoformat()
        for h, a, hs, as_ in (("LAD", "ATL", 5, 3), ("ATL", "LAD", 2, 4)):
            rows.append({"game_pk": pk, "game_type": "R", "season": 2026, "game_date": d, "start_utc": f"{d}T23:00:00Z",
                         "status": "Final", "home": h, "away": a, "home_score": hs, "away_score": as_,
                         "home_sp": 1.0, "away_sp": 2.0})
            pk += 1
    rows.append({"game_pk": 9999, "game_type": "R", "season": 2026, "game_date": "2026-07-15",
                 "start_utc": "2026-07-15T23:10:00Z", "status": "Preview", "home": "LAD", "away": "ATL",
                 "home_score": None, "away_score": None, "home_sp": 1.0, "away_sp": None})
    return pd.DataFrame(rows)


def _markets(series: str) -> tuple:
    out = []
    for suf in LADDER[series]:
        strike = parse_market_ticker(f"{series}-{EVENT_SUFFIX}-{suf}")["strike"]
        m = {"ticker": f"{series}-{EVENT_SUFFIX}-{suf}", "event_ticker": f"{series}-{EVENT_SUFFIX}",
             "yes_bid_dollars": "0.48", "yes_ask_dollars": "0.51"}
        if strike is not None:
            m["floor_strike"] = strike
        out.append(m)
    return True, out


@pytest.fixture()
def replay(tmp_path, monkeypatch):
    monkeypatch.setenv("PM_SHADOW_DIR", str(tmp_path))
    games = _games()
    idx = MLBScheduleIndex(games)
    fc = MLBForecaster(MLBPregameModel.load(MODEL), MLBGameFeatureBuilder(games), idx)
    written, skipped = {}, {}
    for i, hours in enumerate((24.0, 6.0, 0.5)):          # T1, T2, T3
        res = run_once(forecaster=fc, cells=CELLS, list_markets=_markets, kickoff_for=idx.kickoff_for_event,
                       kickoff_miss_reason=idx.miss_reason_for_event, ledger_dir=tmp_path, run_id=f"replay{i}",
                       now_utc=START - timedelta(hours=hours), code_sha="dryrun")
        for k, v in res["written"].items():
            written[k] = written.get(k, 0) + v
        for k, v in res["skipped"].items():
            skipped[k] = skipped.get(k, 0) + v
    return tmp_path, written, skipped


def _rows(d: Path, mt: str, band: str) -> list:
    p = d / f"MLB_{mt}_{band}.jsonl"
    return [json.loads(x) for x in p.read_text().splitlines() if x.strip()] if p.exists() else []


def test_every_registered_game_cell_writes_a_priced_row(replay):
    d, written, skipped = replay
    cells_with_p = 0
    for mt, _ in CELLS:
        for band in ("T1", "T2", "T3"):
            rows = _rows(d, mt, band)
            assert rows, f"{mt}/{band} wrote no row; skipped={skipped}"
            r = rows[0]
            assert 0.0 < r["p_yes"] < 1.0 and r["model_id"] == "mlb_game_pregame_v1"
            assert 0 < r["yes_bid"] < r["yes_ask"] < 1 and r["mid"] and r["half_spread"] > 0   # market state
            assert r["horizon_hours_to_start"] > 0 and r["start_time_utc"] and r["band"] == band
            cells_with_p += 1
    assert cells_with_p == 12                                   # MEASURE MOVED: MLB layer-1 game cells in the dry run


def test_rows_carry_v1_arm_and_the_pinned_2027_map_arm(replay):
    d, _, _ = replay
    sha = hashlib.sha256(MAP_2027.read_bytes()).hexdigest()
    doc = json.loads(MAP_2027.read_text())
    arms_allowed = {l["arm"] for l in doc["leaves"].values()} | {"NO_BET"}
    for mt, _ in CELLS:
        for band in ("T1", "T2", "T3"):
            for r in _rows(d, mt, band):
                assert r["router"]["branch"] != "ERROR" and r["router"]["orders"] == "off", r["router"]
                c = r["router_candidates"]["mlb_2027"]
                assert c["arm"] in arms_allowed and c["map_sha256"] == sha and c["branch"] != "ERROR", c
                assert c["arm"] == "NO_BET"                       # pre-registered: every cell starts NO BET


def test_no_order_path_and_default_map_unchanged(replay):
    assert lm.MAP_VERSIONS["v1"] != str(MAP_2027)               # the 2027 map is a candidate, never the router default
    d, _, _ = replay
    for mt, _ in CELLS:
        for band in ("T1", "T2", "T3"):
            assert all(r["router"]["orders"] == "off" for r in _rows(d, mt, band))
