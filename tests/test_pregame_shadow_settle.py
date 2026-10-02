"""EXP-037: settlement join writes outcomes only, idempotently, first row per (market, band)."""
import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from run_pregame_shadow_settle import settle  # noqa: E402

CLIM = {"home_win_rate_ex_ties": 0.57, "mean_margin": 2.0, "mean_total": 45.0,
        "sd_margin": 13.5, "sd_total": 13.4}


def _row(ts, tkr, mt, band="T1"):
    return {"run_id": ts, "ts_utc": ts, "sport": "NFL", "market_type": mt, "band": band, "market_ticker": tkr,
            "p_yes": 0.6, "yes_bid": 0.5, "yes_ask": 0.52}


def test_settle_joins_outcome_once_and_computes_no_scores(tmp_path):
    t = "KXNFLGAME-26OCT04LACSEA-LAC"   # LAC away at SEA
    rows = [_row("2026-10-03T00:00:00", t, "NFL_MONEYLINE"), _row("2026-10-03T06:00:00", t, "NFL_MONEYLINE")]
    (tmp_path / "NFL_NFL_MONEYLINE_T1.jsonl").write_text("\n".join(json.dumps(r) for r in rows) + "\n")
    sched = pd.DataFrame([{"gameday": "2026-10-04", "home_team": "SEA", "away_team": "LAC",
                           "home_score": 20.0, "away_score": 27.0}])
    assert settle(tmp_path, sched, CLIM) == {"NFL_NFL_MONEYLINE_T1": 1}      # first row only
    assert settle(tmp_path, sched, CLIM) == {"NFL_NFL_MONEYLINE_T1": 0}      # idempotent
    out = [json.loads(x) for x in (tmp_path / "settled" / "NFL_NFL_MONEYLINE_T1.jsonl").read_text().splitlines()]
    assert len(out) == 1 and out[0]["y"] == 1.0 and out[0]["ts_utc"] == "2026-10-03T00:00:00"
    assert not any(k.startswith(("brier", "logloss", "delta")) for k in out[0])


def test_unfinished_game_not_settled(tmp_path):
    t = "KXNFLGAME-26OCT04LACSEA-SEA"
    (tmp_path / "NFL_NFL_MONEYLINE_T1.jsonl").write_text(json.dumps(_row("2026-10-03T00:00:00", t, "NFL_MONEYLINE")) + "\n")
    sched = pd.DataFrame([{"gameday": "2026-10-04", "home_team": "SEA", "away_team": "LAC",
                           "home_score": float("nan"), "away_score": float("nan")}])
    assert settle(tmp_path, sched, CLIM) == {"NFL_NFL_MONEYLINE_T1": 0}
