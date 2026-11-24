"""W125.3: H-EDGE-5 close rule / net arithmetic and the per-leaf pot-of-gold scorer (known-answer tests)."""
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "12_EXPLORATORY", "edge_location", "h5_flb"))
sys.path.insert(0, os.path.join(REPO, "12_EXPLORATORY", "pot_of_gold"))
sys.path.insert(0, os.path.join(REPO, "12_EXPLORATORY", "longshot_bias"))
sys.path.insert(0, os.path.join(REPO, "12_EXPLORATORY"))
sys.path.insert(0, os.path.join(REPO, "src"))

import run_h5 as H  # noqa: E402
import score_w125 as S  # noqa: E402

START = 1_000_000


def _row(cs):
    return {"cs": cs, "start": START}


def test_close_takes_last_candle_before_start():
    b, a, fl = H.close_row(_row([(START - 7200, .40, .44), (START - 1800, .50, .54)]))
    assert (b, a, fl) == (.50, .54, False)


def test_close_drops_candle_older_than_3h():
    assert H.close_row(_row([(START - 4 * 3600, .50, .54)]))[2] == "no_candle_in_3h"


def test_close_drops_wide_spread_and_flags_backfill():
    assert H.close_row(_row([(START - 600, .40, .55)]))[2] == "spread_gt_10c"
    b, a, fl = H.close_row(_row([(START - 5400, .50, .54), (START - 600, 0, .54)]))
    assert (b, a, fl) == (.50, .54, True)


def test_contract_net_equals_gross_minus_cost_both_arms():
    fav = H.contract("KXNBAGAME", .60, .64, 1, False)   # mid .62 -> buy YES at mid
    assert fav["side"] == "yes" and abs(fav["gross"] - .38) < 1e-9 and abs(fav["net"] - (fav["gross"] - fav["cost"])) < 1e-12
    lng = H.contract("KXNBAGAME", .20, .24, 0, False)   # mid .22 -> NO, wins
    assert lng["side"] == "no" and abs(lng["gross"] - .22) < 1e-9 and lng["cost"] > 0.02  # half spread alone is 2c


def test_cell_underpowered_below_thresholds():
    rows = [{"g": i, "net": .01, "gross": .02, "cost": .01, "mid": .6, "y_side": 1} for i in range(20)]
    assert H.cell(rows, "x")["testable"] is False


def test_flb_buckets_cover_and_edges():
    assert S.flb_bucket(.02) == "[0.02,0.10)" and S.flb_bucket(.10) == "[0.10,0.25)"
    assert S.flb_bucket(.98) == "[0.90,0.98)" and S.flb_bucket(.01) is None


def _syn(n_games, p, y_rate_fn, series="KXNBATOTAL", tier="D1"):
    rows = []
    for g in range(n_games):
        rows.append({"sport": "nba", "series": series, "tier": tier, "game": "G%d" % g, "p": p, "bid": p - .01,
                     "ask": p + .01, "y": y_rate_fn(g), "flb": S.flb_bucket(p)})
    return rows


def test_calibrated_market_loses_the_cost_and_is_routed_away():
    rows = _syn(200, .20, lambda g: 1.0 if g % 5 == 0 else 0.0)  # settles exactly at its price
    rows += _syn(200, .80, lambda g: 1.0 if g % 5 else 0.0)
    lv = S.leaves(rows)
    S.pool(lv)
    S.verdicts(lv)
    assert lv and all(r["verdict"] != "EARNED" for r in lv)
    yes_fav = [r for r in lv if r["flb"] == "[0.75,0.90)" and r["side"] == "yes"][0]
    assert yes_fav["mean"] < 0  # fee + half spread on a fair price


def test_planted_underpriced_favourite_is_earned():
    # 0.80 favourite that really wins 95% of the time (minority >= 5 keeps it judgeable), plus calibrated peers so pooling has >= 2 leaves
    rows = _syn(200, .80, lambda g: 0.0 if g % 20 == 0 else 1.0)
    rows += _syn(200, .60, lambda g: 1.0 if g % 5 < 3 else 0.0)
    lv = S.leaves(rows)
    S.pool(lv)
    S.verdicts(lv)
    top = [r for r in lv if r["flb"] == "[0.75,0.90)" and r["side"] == "yes"][0]
    assert top["judged"] and top["verdict"] == "EARNED"


def test_unjudged_leaf_is_never_scored():
    rows = _syn(10, .20, lambda g: 0.0)
    lv = S.leaves(rows)
    S.pool(lv)
    S.verdicts(lv)
    assert all(r["verdict"] == "IN_SAMPLE" and not r["judged"] for r in lv)
