"""EXP-047 / W109.3: engine props forecaster + shadow runner, offline on synthetic games. No order path."""
from datetime import datetime, timezone

from prediction_market_bot.c5_execution import market_type_registry as R
from prediction_market_bot.pregame_shadow import nba_engine_props_forecaster as F
from prediction_market_bot.pregame_shadow.runner import run_once

KEYS = ["minutes", "points", "rebounds", "assists", "threePointFieldGoalsMade-threePointFieldGoalsAttempted"]


def _team(abbr, names, k):
    ath = [{"athlete": {"displayName": n}, "stats": ["30", str(18 - i), str(8 - i), str(4 - i % 3), f"{3 - i % 3}-7"]}
           for i, n in enumerate(names)]
    return {"team": {"abbreviation": abbr}, "statistics": [{"keys": KEYS, "athletes": ath}]}


def _store():
    names = {"GS": [f"Guy{c} Curry{c}" for c in "ABCDEFGH"], "NO": [f"Dud{c} Queen{c}" for c in "ABCDEFGH"]}
    raw = {}
    for g in range(6):
        raw[str(g)] = {"date": f"2026-10-{21 + g}", "box": {"players": [_team("GS", names["GS"], g), _team("NO", names["NO"], g)]},
                       "hdr": [f"GS:home:{110 + g}", f"NO:away:{105 + g}"]}
    return raw


def _fc():
    games, pl = F.parse_box(_store())
    tip = datetime(2026, 11, 9, 23, 0, tzinfo=timezone.utc)
    return F.NBAEngineProps(games, pl, {("2026-11-09", frozenset(("NOP", "GSW"))): tip}), tip


def test_parse_ticker_and_rejects():
    p = F.parse_market_ticker("KXNBAAST-26NOV09NOPGSW-NOPDQUEEN22-6")
    assert p["market_type"] == "NBA_PLAYER_ASSISTS" and p["n"] == 6 and p["team"] == "NOP" and p["home"] == "GSW"
    assert F.parse_market_ticker("KXNBAPTS-26NOV09NOPGSW-NOPDQUEEN22-6") is None
    assert F.parse_market_ticker("KXNBAREB-26NOV09NOPGSW-LALDQUEEN22-6") is None     # player team not in game


def test_kickoff_lookup():
    fc, tip = _fc()
    assert fc.kickoff_for_event("KXNBAREB-26NOV09NOPGSW")[0] == tip
    assert fc.kickoff_for_event("KXNBAREB-26NOV10NOPGSW") is None


def test_forecast_monotone_and_unknown_player_none():
    fc, _ = _fc()
    now = datetime(2026, 11, 9, 12, tzinfo=timezone.utc)
    ps = []
    for n in (2, 4, 6, 8):
        f = fc.forecast(f"KXNBAREB-26NOV09NOPGSW-NOPDQUEENA22-{n}".replace("DQUEENA22", "DQUEENA22"), now)
        ps.append(f.p_yes if f else None)
    assert all(p is not None and 0 < p < 1 for p in ps) and ps == sorted(ps, reverse=True)
    assert fc.forecast("KXNBAREB-26NOV09NOPGSW-NOPZNOBODY1-4", now) is None


def test_run_once_logs_rows_no_orders(tmp_path):
    fc, _ = _fc()
    now = datetime(2026, 11, 8, 20, tzinfo=timezone.utc)      # 27h before tip -> T1 window
    mk = {"ticker": "KXNBAREB-26NOV09NOPGSW-NOPDQUEENA22-6", "event_ticker": "KXNBAREB-26NOV09NOPGSW",
          "yes_bid_dollars": "0.40", "yes_ask_dollars": "0.44"}
    res = run_once(forecaster=fc, cells=[("NBA_PLAYER_REBOUNDS", "KXNBAREB")],
                   list_markets=lambda s: (True, [mk]), kickoff_for=fc.kickoff_for_event, ledger_dir=tmp_path,
                   run_id="t", now_utc=now, code_sha="x", on_row=None)
    assert sum(res["written"].values()) == 1
    files = list(tmp_path.glob("NBAENG_NBA_PLAYER_REBOUNDS_*.jsonl"))
    assert len(files) == 1 and F.MODEL_SHA256 in files[0].read_text()


def test_registry_cells_shadow_kelly_zero():
    from prediction_market_bot.execution_bands import ExecutionBand
    for mt in ("NBA_PLAYER_REBOUNDS", "NBA_PLAYER_ASSISTS", "NBA_PLAYER_THREES"):
        for b in (ExecutionBand.T1_MULTI_DAY, ExecutionBand.T2_SAME_DAY, ExecutionBand.T3_PRE_TIP):
            cell = R.MARKET_TYPE_REGISTRY[(R.MarketType[mt], b)]
            assert cell.status is R.CellStatus.SHADOW
