"""W90.3 quant-bar tests: a simulated trend must be recovered as FOLLOW, a simulated mean-reversion as FADE."""
import importlib.util
import os
import random

_p = os.path.join(os.path.dirname(__file__), "..", "12_EXPLORATORY", "momentum_j", "core.py")
_s = importlib.util.spec_from_file_location("w90_core", _p)
K = importlib.util.module_from_spec(_s)
_s.loader.exec_module(K)

STEP = 1200.0  # 20-min snapshots
START = 10_000_000.0


def _sim(n_games, drift, seed, spread=0.01):
    """Each game: a jump of +/-6c lands at snapshot 20, then the mid keeps drifting by `drift` per snapshot in the
    jump direction (drift>0 trend, drift<0 reversion). Returns rows via find_signals + realize."""
    rng = random.Random(seed)
    rows = []
    for g in range(n_games):
        sgn = 1 if rng.random() < 0.5 else -1
        mid, pts = 0.50, []
        for i in range(60):
            ts = START - 80 * STEP + i * STEP
            if i == 20:
                mid += sgn * 0.06
            elif i > 20:
                mid += sgn * drift + rng.gauss(0, 0.002)
            else:
                mid += rng.gauss(0, 0.002)
            pts.append((ts, mid - spread / 2, mid + spread / 2))
        for s in K.find_signals(pts, START):
            r = K.realize(s, None)
            if "3h" in r:
                rows.append({"game": f"G{g}", **r["3h"]})
    return rows


def test_simulated_trend_recovered_as_follow():
    rows = _sim(120, drift=0.008, seed=1)
    f, d = K.cell_stats(rows, "follow"), K.cell_stats(rows, "fade")
    assert f["testable"] and f["lo"] > 0 and d["hi"] < 0 and f["p"] < 1e-3


def test_simulated_reversion_recovered_as_fade():
    rows = _sim(120, drift=-0.008, seed=2)
    f, d = K.cell_stats(rows, "follow"), K.cell_stats(rows, "fade")
    assert d["lo"] > 0 and f["hi"] < 0


def test_random_walk_not_flagged_after_costs():
    rows = _sim(120, drift=0.0, seed=3)
    f, d = K.cell_stats(rows, "follow"), K.cell_stats(rows, "fade")
    assert f["net"] < 0 and d["net"] < 0  # no drift: costs make both sides lose


def test_costs_are_charged_both_legs():
    # Flat book, 1c half-spread each leg, entry 0.50 -> sell 0.50: follow loses 2 half-spreads + two fees.
    s = {"dir": 1, "entry": (0.49, 0.51), "entry_mid": 0.50, "ex": {"1h": (0.49, 0.51, 0.0)}}
    r = K.realize(s, None)["1h"]
    expect = 0.49 - 0.51 - K.fee_k007(0.51) - K.fee_k007(0.49)
    assert abs(r["follow"] - expect) < 1e-12 and r["gross"] == 0.0


def test_settlement_hold_pays_outcome():
    s = {"dir": -1, "entry": (0.60, 0.62), "entry_mid": 0.61, "ex": {}}
    r = K.realize(s, 0.0)["settle"]  # down-move -> follow buys NO at 1-bid=0.40; NO wins
    assert abs(r["follow"] - (1.0 - 0.40 - K.fee_k007(0.40))) < 1e-12


def test_news_proxy_windows():
    # An MLB game at START: a move ending 2h before first pitch overlaps the lineup window; 10h before does not.
    assert K.news_flag("mlb", START, START - 2.5 * 3600, START - 2 * 3600) == "news"
    assert K.news_flag("mlb", START, START - 11 * 3600, START - 10 * 3600) == "quiet"
