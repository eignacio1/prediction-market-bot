import numpy as np
import pandas as pd

from prediction_market_bot.nhl_engine import model, model_pit


def test_pit_rate_is_strictly_trailing_and_uses_fallback_first():
    start = pd.to_datetime(["2024-01-01 19:00", "2024-01-02 19:00", "2024-01-02 19:00", "2024-01-03 19:00"])
    own = np.array([2.0, 4.0, 6.0, 8.0]); opp = own.copy(); fb = np.full(4, 99.0)
    r = model_pit.pit_league_rate(start, own, opp, fb, window=10)
    assert r[0] == 99.0                       # no earlier game -> fallback
    assert r[1] == 2.0 and r[2] == 2.0        # same puck drop: neither sees the other
    assert abs(r[3] - np.mean([2.0, 4.0, 6.0])) < 1e-12
    r2 = model_pit.pit_league_rate(start[::-1], own[::-1], opp[::-1], fb, window=10)   # row order must not matter
    assert np.allclose(r2[::-1], r)


def test_pit_rate_window_caps_lookback():
    start = pd.date_range("2024-01-01", periods=6, freq="D")
    v = np.arange(6, dtype=float)
    r = model_pit.pit_league_rate(start, v, v, np.zeros(6), window=2)
    assert r[5] == 3.5                        # mean of rows 3, 4


def _frame(n, rng, lg):
    d = {"game_id": np.arange(n), "start": pd.date_range("2024-01-01", periods=n, freq="h"),
         "sec5_h": 3000.0, "lg_f5_h": lg, "lg_pp_h": 7.0}
    for s in ("h", "a"):
        d[f"f5_{s}"] = rng.normal(2.4, 0.3, n); d[f"a5_{s}"] = 2.4; d[f"pp_{s}"] = 7.0; d[f"pk_{s}"] = 7.0
        d[f"ppt_{s}"] = 300.0; d[f"sht_{s}"] = 300.0; d[f"rest_{s}"] = 2.0; d[f"gs_{s}"] = 0.0
    return pd.DataFrame(d)


def test_stale_denominator_deflates_the_merged_cross_and_pit_removes_it():
    rng = np.random.default_rng(3)
    fr = _frame(3000, rng, lg=2.8)            # stale league rate 2.8 vs same-vintage team mean ~2.4
    p = model_pit.with_pit_denominators(fr, window=500)
    merged = model.side_rows(fr)["lx"].to_numpy().mean()
    pit = model_pit.side_rows_pit(p.iloc[200:])["lx"].to_numpy().mean()
    assert pit - merged > 0.1                 # about log(2.8 / 2.4) = 0.154


def test_fit_pit_runs_and_restores_module_state():
    rng = np.random.default_rng(4)
    fr = model_pit.with_pit_denominators(_frame(4000, rng, lg=2.4), window=500)
    n = len(fr); rh, ra = rng.poisson(3.0, n), rng.poisson(3.0, n)
    base = model.side_rows
    m = model_pit.fit_pit(fr, rh, ra, rng.random(n) < 0.5)
    assert model.side_rows is base            # monkeypatch undone
    lh, la = m.rates(fr.iloc[:20])
    assert lh.shape == (20,) and (lh > 0).all() and (la > 0).all()
