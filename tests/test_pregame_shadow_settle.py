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


def _mlb_games(status="Final", hs=5.0, as_=3.0):
    return pd.DataFrame([{"game_pk": 1, "season": 2026, "status": status, "home": "LAD", "away": "ATL",
                          "start_utc": "2026-10-03T20:00:00Z", "home_score": hs, "away_score": as_}])


def _mlb_row(tkr, mt, ts="2026-10-02T00:00:00"):
    return {"run_id": ts, "ts_utc": ts, "sport": "MLB", "market_type": mt, "band": "T1", "market_ticker": tkr,
            "p_yes": 0.5}


def test_mlb_settle_all_four_market_types(tmp_path):
    from run_pregame_shadow_settle import settle_mlb
    ev = "26OCT031600ATLLAD"          # ATL @ LAD, final LAD 5 - ATL 3
    cases = {"MLB_MONEYLINE": [("KXMLBGAME-%s-LAD" % ev, 1.0), ("KXMLBGAME-%s-ATL" % ev, 0.0)],
             "MLB_RUN_LINE": [("KXMLBSPREAD-%s-LAD2" % ev, 1.0), ("KXMLBSPREAD-%s-LAD3" % ev, 0.0),
                              ("KXMLBSPREAD-%s-ATL2" % ev, 0.0)],
             "MLB_GAME_TOTAL": [("KXMLBTOTAL-%s-8" % ev, 1.0), ("KXMLBTOTAL-%s-9" % ev, 0.0)],
             "MLB_TEAM_TOTAL": [("KXMLBTEAMTOTAL-%s-LAD5" % ev, 1.0), ("KXMLBTEAMTOTAL-%s-ATL4" % ev, 0.0)]}
    for mt, items in cases.items():
        (tmp_path / f"MLB_{mt}_T1.jsonl").write_text("\n".join(json.dumps(_mlb_row(t, mt)) for t, _ in items) + "\n")
    counts = settle_mlb(tmp_path, _mlb_games())
    assert all(v == len(cases[k]) for k, v in ((n[4:-3], c) for n, c in counts.items()))
    for mt, items in cases.items():
        out = {j["market_ticker"]: j for j in (json.loads(x) for x in
               (tmp_path / "settled" / f"MLB_{mt}_T1.jsonl").read_text().splitlines())}
        for t, y in items:
            assert out[t]["y"] == y, t
    assert sum(settle_mlb(tmp_path, _mlb_games()).values()) == 0       # idempotent
    raw = (tmp_path / "MLB_MLB_MONEYLINE_T1.jsonl").read_text()
    assert "\"y\"" not in raw                                           # raw ledger never rewritten


def test_mlb_unfinal_or_missing_game_stays_unsettled(tmp_path):
    from run_pregame_shadow_settle import settle_mlb
    t = "KXMLBGAME-26OCT031600ATLLAD-LAD"
    (tmp_path / "MLB_MLB_MONEYLINE_T1.jsonl").write_text(json.dumps(_mlb_row(t, "MLB_MONEYLINE")) + "\n")
    assert settle_mlb(tmp_path, _mlb_games(status="In Progress")) == {"MLB_MLB_MONEYLINE_T1": 0}
    assert settle_mlb(tmp_path, _mlb_games(status="Final", hs=float("nan"))) == {"MLB_MLB_MONEYLINE_T1": 0}
    assert not (tmp_path / "settled").exists()
