"""W125.1 Part A + C: fill model known answers, the compact read task, skip-reason counts."""
from __future__ import annotations

import importlib.util
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))

from prediction_market_bot.c5_execution.placement import fill_model as fm  # noqa: E402


def rec(i, filled, won, price=0.50, fee=0.0, hours=3.0, game=None, series="KXNBAGAME", arm="FADE", markout=None, placement="rest_touch"):
    g = game if game is not None else f"G{i}"
    return {"arm": arm, "sport": "nba", "series": series, "ticker": f"{series}-26NOV17{g}-X", "order_id": f"o{i}", "filled": filled,
            "won": won, "price": price, "fee_per_contract": fee, "hours": hours, "placement": placement, "spread": 0.02,
            "markout": markout or {}}


def test_family_of():
    assert fm.family_of("KXNBAGAME") == "moneyline"
    assert fm.family_of("KXNBASPREAD") == "spread"
    assert fm.family_of("KXNBATOTAL") == "total"
    assert fm.family_of("KXNBATEAMTOTAL") == "team_total"
    assert fm.family_of("KXNBAPTS") == "prop"
    assert fm.family_of("KXFOO") == "other"


def test_net_per_filled_uses_the_fee_charged():
    assert abs(fm.net_per_filled(rec(0, True, True, 0.40, 0.01)) - 0.59) < 1e-9
    assert abs(fm.net_per_filled(rec(0, True, False, 0.40, 0.01)) - (-0.41)) < 1e-9
    assert fm.net_per_filled(rec(0, False, True)) is None
    assert fm.net_per_filled(rec(0, True, None)) is None


def test_known_answer_cell():
    # 10 orders, 6 filled (4 win at 0.50, fee 0.01; 2 lose), 4 unfilled (3 win, 1 lose); 10 distinct games
    rs = ([rec(i, True, i < 4, fee=0.01, markout={"h5": 0.02, "h30": -0.01}) for i in range(6)]
          + [rec(6 + i, False, i < 3) for i in range(4)])
    t = fm.fill_model(rs, min_orders=5)
    c = t["cells"]["FADE|moneyline|1-6h"]
    assert c["n"] == 10 and c["fills"] == 6 and c["p_fill"] == 0.6
    assert c["win_filled"] == round(4 / 6, 4) and c["win_unfilled"] == 0.75
    # edge filled = mean(+.5 x4, -.5 x2) = 1/6 ; edge unfilled = mean(.5 x3, -.5) = 0.25 -> adverse_sel = -1/12
    assert c["adverse_sel"] == round(1 / 6 - 0.25, 4)
    assert c["net_filled"] == round((4 * 0.49 + 2 * -0.51) / 6, 4)
    assert c["n_settled_filled"] == 6 and c["n_games_settled_filled"] == 6
    assert c["supported"] is False            # 6 games < MIN_GAMES
    assert c["markout"]["h5"] == {"mean": 0.02, "n": 6} and c["markout"]["h30"]["mean"] == -0.01


def test_games_not_orders_are_the_n():
    # 40 filled winning orders, all on 3 games: orders are plentiful, games are not
    rs = [rec(i, True, True, game=f"G{i % 3}") for i in range(40)]
    c = fm.fill_model(rs)["cells"]["FADE|moneyline|1-6h"]
    assert c["n_settled_filled"] == 40 and c["n_games_settled_filled"] == 3 and c["supported"] is False


def test_supported_at_min_games():
    rs = [rec(i, True, i % 2 == 0) for i in range(fm.MIN_GAMES)]
    assert fm.fill_model(rs)["cells"]["FADE|moneyline|1-6h"]["supported"] is True


def test_small_cells_dropped_and_counted():
    rs = [rec(i, True, True) for i in range(3)] + [rec(10 + i, True, True, hours=30) for i in range(6)]
    t = fm.fill_model(rs, min_orders=5)
    assert list(t["cells"]) == ["FADE|moneyline|24h+"] and t["cells_below_min_orders_dropped"] == 1


def test_unknown_fill_status_is_excluded():
    rs = [rec(i, None, None) for i in range(8)]
    assert fm.fill_model(rs)["n_orders"] == 0


def test_partial_pool_within_an_arm_only():
    rs = []
    for fam, ser, win in (("a", "KXNBAGAME", True), ("b", "KXNBATOTAL", False), ("c", "KXNBASPREAD", True)):
        rs += [rec(len(rs) + i, True, win if i % 4 else (not win), series=ser, game=f"{fam}{i}") for i in range(24)]
    rs += [rec(500 + i, True, i % 2 == 0, arm="RIDE", game=f"r{i}") for i in range(12)]  # a lone RIDE cell: not pooled
    t = fm.fill_model(rs)
    assert "_arm|FADE" in t["arm_pool"] and "_arm|RIDE" not in t["arm_pool"]
    for c in ("FADE|moneyline|1-6h", "FADE|total|1-6h", "FADE|spread|1-6h"):
        p = t["cells"][c]["pooled"]
        lo, hi = t["cells"][c]["net_filled_ci90"]
        assert p["lo"] <= p["shrunk"] <= p["hi"] and 0.0 <= p["B"] <= 1.0
        assert hi - lo >= p["hi"] - p["lo"] - 1e-6        # shrinkage never widens the interval
    assert "pooled" not in t["cells"]["RIDE|moneyline|1-6h"]


def test_skip_counts_per_reason():
    import placement_fill_read as pfr
    rows = [{"event": "arm_skip", "ts": "2026-11-13T01:00:00Z", "arm": "FADE", "reason": "size_zero:day"},
            {"event": "arm_skip", "ts": "2026-11-13T02:00:00Z", "arm": "FADE", "reason": "size_zero:day"},
            {"event": "arm_skip", "ts": "2026-11-14T02:00:00Z", "arm": "RIDE", "reason": "no_bet"},
            {"event": "arm_skip", "ts": "2026-11-10T02:00:00Z", "arm": "RIDE", "reason": "no_bet"},   # before --since
            {"event": "arm_order", "ok": True, "ts": "2026-11-13T03:00:00Z", "arm": "FADE", "stake_usd": 5.0}]
    s = pfr.skip_counts(rows)
    assert s["by_reason"] == {"size_zero:day": 2, "no_bet": 1} and s["skips"] == 3 and s["decisions"] == 4
    assert s["placed_per_day"] == {"2026-11-13": 1} and s["stake_usd_per_day"] == {"2026-11-13": 5.0}
    json.dumps(s)


def test_task_is_allowlisted_read_only_and_writes_nothing():
    spec = importlib.util.spec_from_file_location("box_tasks", REPO / "scripts" / "box_tasks.py")
    bt = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(bt)
    cmd = bt.TASKS["placement_fill_read"]
    assert cmd.endswith("scripts/placement_fill_read.py") and bt.NAME_RE.match("placement_fill_read") and ">" not in cmd
    src = (REPO / "scripts" / "placement_fill_read.py").read_text()
    assert not re.search(r"open\([^)]*['\"][wa]b?['\"]|write_text|atomic_write|\.mkdir\(", src)
