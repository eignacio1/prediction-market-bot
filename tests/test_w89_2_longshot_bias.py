"""W89.2 quant-bar tests: a simulated market with a known bias is recovered; a calibrated one is not flagged."""
import importlib.util
import os
import random

_p = os.path.join(os.path.dirname(__file__), "..", "12_EXPLORATORY", "longshot_bias", "calib.py")
_s = importlib.util.spec_from_file_location("w89_calib", _p)
C = importlib.util.module_from_spec(_s)
_s.loader.exec_module(C)


def _market(n_games, bias, seed, price=0.10):
    """Each game: one contract priced `price`, true prob = price + bias, 2c spread."""
    rng = random.Random(seed)
    return [{"game": f"G{i}", "p": price, "y": 1.0 if rng.random() < price + bias else 0.0,
             "bid": price - 0.01, "ask": price + 0.01} for i in range(n_games)]


def test_known_longshot_bias_recovered():
    # longshots priced 10c that truly win 4% -> NO side is the edge; gap = -0.06
    cell = C.cell_test(_market(3000, -0.06, 1), boot=50)
    assert cell["testable"] and cell["p_value"] < 1e-3 and cell["gap"] < -0.03 and cell["side"] == "no"


def test_calibrated_market_not_flagged():
    # Under a global null BH may flag in at most ~q of runs; 40 replicates of 25 calibrated cells.
    runs_with_flag = 0
    for rep in range(40):
        cells = {(rep, i): C.cell_test(_market(300, 0.0, rep * 100 + i, price=(0.1, 0.3, 0.5, 0.7, 0.9)[i % 5]), boot=2)
                 for i in range(25)}
        out = C.bh_flags(cells)
        assert out["tested"] == 25
        runs_with_flag += out["flagged"] > 0
    assert runs_with_flag <= 10  # expected ~4 (q=0.10); 10 is ~p<0.01 under the null


def test_thin_cell_is_descriptive():
    cell = C.cell_test(_market(10, -0.5, 2), boot=20)
    assert cell["p_value"] is None and not cell["testable"]


def test_fee_wipes_small_gap():
    # 1-point bias is below spread+fee: significant but net CI must not be positive
    cell = C.cell_test(_market(4000, -0.01, 3, price=0.5), boot=100)
    assert cell["net_lo"] < 0


def _walk(n, rho, seed):
    rng = random.Random(seed)
    games = {}
    for g in range(n):
        mids, m = [], 0.5
        prev = 0.0
        for _ in range(12):
            step = rho * prev + rng.gauss(0, 0.03)
            prev = step
            m = min(max(m + step, 0.05), 0.95)
            mids.append(m)
        games[f"G{g}"] = mids
    return games


def _moves(games, cost):
    out = []
    for g, mids in games.items():
        for i in range(1, 9):
            d = mids[i] - mids[i - 1]
            if abs(d) >= 0.05:
                out.append({"game": g, "rev": -(1 if d > 0 else -1) * (mids[i + 3] - mids[i]), "cost": cost})
    return out


def test_mean_reversion_detected_and_random_walk_not():
    rev = C.reversion_cell(_moves(_walk(600, -0.6, 4), 0.0), boot=20)
    rw = C.reversion_cell(_moves(_walk(600, 0.0, 5), 0.0), boot=20)
    assert rev["p_value"] < 1e-3 and rev["gross"] > 0
    assert rw["p_value"] > 0.01


def test_tier_and_start_parse():
    ts = C.parse_ts("2026-10-19T22:00:00Z")  # 18:00 ET
    assert C.tier("KXMLBGAME-26OCT192008CLETB", ts) == "T2-6h"
    assert C.tier("KXMLBGAME-26OCT192008CLETB", C.parse_ts("2026-10-20T01:00:00Z")) is None
    assert C.parse_ts("2026-10-20T00:00:04.12345Z") > C.parse_ts("2026-10-20T00:00:04Z")
