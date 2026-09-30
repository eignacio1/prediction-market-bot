"""EXP-030 (T-598) unit tests. Synthetic data only."""
import numpy as np

from prediction_market_bot.c3_forecasting import t4_structure_model as m


def _row(i, y, p=0.4, ba=0.25, thr=1):
    return {"ticker": f"KXMLBHIT-26JUL181900NYYBOS-BOSPLAYER{i}-{thr}", "threshold": thr,
            "h_so_far": 0, "ab_remaining": 3, "batting_slot": 1 + i % 9, "inning": 1 + i % 9,
            "ba_l10_shrunk": ba, "p_incumbent": p, "outcome": y}


def test_batter_is_home():
    assert m.batter_is_home("KXMLBHIT-26JUL181900NYYBOS-BOSJUDGE1-1") == 1.0
    assert m.batter_is_home("KXMLBHIT-26JUL181900NYYBOS-NYYJUDGE1-1") == 0.0


def test_no_signal_stays_near_incumbent():
    rng = np.random.default_rng(0)
    rows = [_row(i, int(rng.random() < 0.4)) for i in range(600)]
    f = m.ResidualLogit(0.01).fit(rows)
    assert abs(f.predict(rows[0]) - 0.4) < 0.1


def test_learns_offset_bias():
    rng = np.random.default_rng(1)
    rows = [_row(i, int(rng.random() < 0.6)) for i in range(800)]  # incumbent says 0.4, truth 0.6
    f = m.ResidualLogit(1.0).fit(rows)
    assert f.predict(rows[0]) > 0.5
    assert m.brier_gain(rows, f.predict) > 0


def test_predictions_bounded_and_select_c_deterministic():
    rng = np.random.default_rng(2)
    rows = [_row(i, int(rng.random() < 0.5)) for i in range(300)]
    c1, _ = m.select_c(rows[:200], rows[200:])
    c2, _ = m.select_c(rows[:200], rows[200:])
    assert c1 == c2 and c1 in m.C_GRID
    assert all(m.P_MIN <= m.ResidualLogit(0.1).fit(rows).predict(r) <= m.P_MAX for r in rows[:20])


def test_permutation_control_shape():
    rng = np.random.default_rng(3)
    rows = [_row(i, int(rng.random() < 0.4)) for i in range(300)]
    g = m.permutation_control(rows[:200], rows[200:], 0.1, n_perm=5)
    assert g.shape == (5,)
