"""Known-answer tests for quant/ladder_loo.py (W91.2)."""
import numpy as np
from scipy.stats import norm

from prediction_market_bot.quant.ladder_loo import loo_ladder_prices


def _total_rows(mu, sigma, ks, tweak=None):
    rows = []
    for k in ks:
        s = 1 - norm.cdf((k - 0.5 - mu) / sigma)
        if tweak and k in tweak:
            s += tweak[k]
        rows.append({"ticker": f"KXNFLTOTAL-26OCT04DENSF-{k}", "bid": s - 0.005, "ask": s + 0.005})
    return rows


def test_recovers_clean_strike_price():
    rows = _total_rows(44.0, 7.0, range(36, 53))
    got = loo_ladder_prices(rows, "total")
    for r in rows:
        assert abs(got[r["ticker"]] - 0.5 * (r["bid"] + r["ask"])) < 0.01


def test_mispriced_strike_shows_gap_with_right_sign():
    rows = _total_rows(44.0, 7.0, range(36, 53), tweak={44: -0.06})
    got = loo_ladder_prices(rows, "total")
    t = "KXNFLTOTAL-26OCT04DENSF-44"
    mid = [0.5 * (r["bid"] + r["ask"]) for r in rows if r["ticker"] == t][0]
    assert got[t] - mid > 0.05  # the ladder says the cheap strike is worth ~6c more


def test_short_ladder_returns_nothing():
    assert loo_ladder_prices(_total_rows(44.0, 7.0, [40, 44, 48]), "total") == {}


def test_margin_both_teams_consistent():
    rows = []
    for k in range(1, 12):  # home favoured by 4: P(home wins by > k-0.5)
        s = 1 - norm.cdf((k - 0.5 - 4.0) / 11.0)
        rows.append({"ticker": f"KXNFLSPREAD-26OCT04DENSF-SF{k}", "bid": s - 0.005, "ask": s + 0.005})
        s2 = norm.cdf((-(k - 0.5) - 4.0) / 11.0)  # DEN wins by > k-0.5
        rows.append({"ticker": f"KXNFLSPREAD-26OCT04DENSF-DEN{k}", "bid": s2 - 0.005, "ask": s2 + 0.005})
    got = loo_ladder_prices(rows, "margin")
    assert len(got) >= 18
    for r in rows:
        assert abs(got[r["ticker"]] - 0.5 * (r["bid"] + r["ask"])) < 0.02
