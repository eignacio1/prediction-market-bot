"""W80R.3: scripts/nba_totals_applied.py pure helpers -- ticker parse, OLS, bootstrap, quote rule, market pick, verdict."""
from __future__ import annotations

import importlib.util
import random
from datetime import date
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("nba_totals_applied", REPO / "scripts" / "nba_totals_applied.py")
na = importlib.util.module_from_spec(spec)
spec.loader.exec_module(na)


def test_parse_event():
    assert na.parse_event("KXNBATOTAL-25OCT21HOUOKC") == (date(2025, 10, 21), "HOU", "OKC")
    assert na.parse_event("KXNBATOTAL-26JAN05NYKSAS") == (date(2026, 1, 5), "NYK", "SAS")
    assert na.parse_event("KXNBATOTAL-BAD") is None


def test_ols_recovers_coefficients():
    rng = random.Random(1)
    X, y = [], []
    for _ in range(200):
        a, b = rng.random(), rng.random()
        X.append([1.0, a, b]); y.append(2 + 3 * a - 1.5 * b)
    beta = na.ols(X, y)
    assert all(abs(u - v) < 1e-9 for u, v in zip(beta, [2, 3, -1.5]))


def test_boot_coef_ci_contains_truth():
    rng = random.Random(2)
    rows = [{"x": rng.gauss(0, 1)} for _ in range(300)]
    for r in rows:
        r["y"] = 0.7 * r["x"] + rng.gauss(0, 0.5)
    c = na.boot_coef(rows, ["x"], "y", 1, b=300)
    assert c["lo"] < 0.7 < c["hi"] and c["n"] == 300


def test_quote_mid_prevailing_and_validity():
    cs = [{"end_period_ts": 100, "yes_bid": {"close": "0.40"}, "yes_ask": {"close": "0.46"}},
          {"end_period_ts": 200, "yes_bid": {"close": "0.00"}, "yes_ask": {"close": "1.00"}}]
    assert abs(na.quote_mid(cs, 150) - 0.43) < 1e-12
    assert na.quote_mid(cs, 50) is None and na.quote_mid(cs, 250) is None


def test_pick_one_market_per_game_nearest_base_prediction():
    games = {(date(2025, 10, 21), "HOU", "OKC"): {"pred_base": 221.0, "term": 1.0, "game_id": "1", "total": 230, "tip": "x"}}
    ms = [{"ticker": f"KXNBATOTAL-25OCT21HOUOKC-{k}", "event_ticker": "KXNBATOTAL-25OCT21HOUOKC", "strike_type": "greater",
           "floor_strike": k - 0.5, "result": "yes"} for k in (212, 218, 221, 222, 230)]
    ms.append({"ticker": "KXNBATOTAL-25OCT22AAABBB-200", "event_ticker": "KXNBATOTAL-25OCT22AAABBB", "strike_type": "greater",
               "floor_strike": 199.5, "result": "no"})
    picks = na.pick_markets(ms, games)
    assert len(picks) == 1 and picks[0]["strike"] == 220.5 and picks[0]["y"] == 1.0   # |220.5-221| = |221.5-221|: lower wins


def test_verdict_rules():
    ci = lambda lo, hi: {"lo": lo, "hi": hi, "est": (lo + hi) / 2}  # noqa: E731
    assert na.verdict(ci(-0.1, 0.5), ci(0.5, 1), ci(-0.1, 0.1)) == "NOT REAL"
    assert na.verdict(ci(0.2, 1.0), ci(0.5, 1), ci(0.01, 0.1)) == "REAL-NOT-PRICED"
    assert na.verdict(ci(0.2, 1.0), ci(0.5, 1), ci(-0.1, 0.1)) == "REAL-AND-PRICED"
    assert na.verdict(ci(0.2, 1.0), ci(-0.3, 1), ci(-0.1, 0.1)) == "INVISIBLE"


def test_analyse_on_a_market_that_prices_the_term_fully():
    rng = random.Random(3)
    games, picks, sigma = {}, [], 12.0
    for i in range(400):
        pb, term = 220 + rng.gauss(0, 6), rng.gauss(0, 3)
        total = pb + term + rng.gauss(0, sigma)
        games[i] = {"pred_base": pb, "term": term, "total": total}
        strike = round(pb) + 0.5
        p = 1 - na.statistics.NormalDist(pb + term, sigma).cdf(strike)       # the market knows the term
        picks.append({"pred_base": pb, "term": term, "strike": strike, "p": p, "y": 1.0 if total > strike else 0.0})
    r = na.analyse(games, picks, sigma)
    assert r["priced"]["lo"] > 0.8 and r["verdict"] in ("REAL-AND-PRICED",)


def test_hash_sample_is_order_free_and_deterministic():
    picks = [{"ticker": f"T{i}"} for i in range(50)]
    a = na.hash_sample(picks, 10)
    b = na.hash_sample(list(reversed(picks)), 10)
    assert a == b and len(a) == 10
