"""EXP-044 live entry (W94.1): strike mapping, quote picking, and as-of rating equivalence with the pinned ratings."""
from datetime import datetime, timedelta, timezone

import numpy as np
import pandas as pd

from prediction_market_bot.nba_engine import live as L, ratings as R

PARSED = dict(event_ticker="KXNBAGAME-26OCT28OKCDAL", game_date="2026-10-28", away="OKC", home="DAL", subject="DAL", strike=None)


def _sample():
    return L.sim_game(dict(mu_poss=99.0, ppp_h=114.0, ppp_a=113.0), dict(hca=1.7, tbias=0.0, s_p=5.3, s_e=10.4), seed=3)


def test_moneyline_sides_sum_to_one():
    s = _sample()
    ph = L.engine_p(s, dict(PARSED, market_type="NBA_MONEYLINE", subject="DAL"))
    pa = L.engine_p(s, dict(PARSED, market_type="NBA_MONEYLINE", subject="OKC"))
    assert abs(ph + pa - 1.0) < 1e-12


def test_strike_suffix_is_p_ge_n():
    s = _sample()
    # suffix 220 -> strike 219.5 -> P(total >= 220), known answer from the sample itself
    p = L.engine_p(s, dict(PARSED, market_type="NBA_GAME_TOTAL", subject="", strike=219.5))
    assert abs(p - float((s.total >= 220).mean())) < 1e-12
    p2 = L.engine_p(s, dict(PARSED, market_type="NBA_SPREAD", subject="DAL", strike=5.5))
    assert abs(p2 - float((s.margin >= 6).mean())) < 1e-12


def test_spread_monotone_and_unknown_subject_none():
    s = _sample()
    a = L.engine_p(s, dict(PARSED, market_type="NBA_SPREAD", subject="DAL", strike=2.5))
    b = L.engine_p(s, dict(PARSED, market_type="NBA_SPREAD", subject="DAL", strike=8.5))
    assert a > b
    assert L.engine_p(s, dict(PARSED, market_type="NBA_SPREAD", subject="XXX", strike=2.5)) is None


def test_quote_at_latest_before_cutoff_and_not_stale():
    cut = datetime(2026, 10, 29, 0, 0, tzinfo=timezone.utc)
    rows = [dict(ticker="T", run_ts=(cut - timedelta(minutes=m)).isoformat(), yes_mid=v)
            for m, v in ((90, 0.1), (30, 0.2), (10, 0.3), (-5, 0.9))]
    assert L.quote_at(rows, cut)["T"]["yes_mid"] == 0.3     # the +5 min row is after the cutoff
    assert "T" not in L.quote_at(rows[:1], cut)             # 90 min old = stale


def test_team_rating_equals_add_ratings():
    rng = np.random.default_rng(0)
    rows, gid = [], 0
    for season in (2025, 2026):
        t0 = pd.Timestamp(f"{season - 1}-11-01", tz="UTC")
        for d in range(20):
            for h, a in ((1, 2), (3, 4)):
                gid += 1
                tip = t0 + pd.Timedelta(days=d)
                for tid, side in ((h, "home"), (a, "away")):
                    rows.append(dict(game_id=gid, team_id=tid, side=side, season=season, season_type="regular-season",
                                     pts=100.0, pace=95 + rng.normal(), ortg=110 + rng.normal(), drtg=110 + rng.normal(),
                                     tip_earliest=tip, tip_latest=tip))
    tg = pd.DataFrame(rows)
    ar = R.add_ratings(tg, k=10.0)
    for _, r in ar[(ar.season == 2026) & (ar.team_id == 1)].iloc[[0, 5, 19]].iterrows():
        t = L.team_rating(tg, 1, 2026, r.tip_earliest)
        assert abs(t["pace"] - r.pace_hat) < 1e-9 and abs(t["ortg"] - r.ortg_hat) < 1e-9
        assert t["n_prior"] == r.n_prior


def test_params_hash_stable():
    cal = dict(hca=1.7, tbias=1.6, s_p=5.3, s_e=10.4, n_cal_games=1230, K=10.0)
    assert L.frozen_params_hash(cal) == L.frozen_params_hash(dict(cal))
