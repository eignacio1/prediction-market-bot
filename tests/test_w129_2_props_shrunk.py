"""W129.2 EXP-047-S: known-answer tests for the shrinkage (planted reliability recovered; zero-noise does not beat the raw mean),
constants pinned to the PAM-3 draft, and C2 / v1 unchanged by the shrunk subclass."""
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from prediction_market_bot.nba_engine import shrunk_means as S
from prediction_market_bot.pregame_shadow import nba_engine_props_c2_forecaster as C2
from prediction_market_bot.pregame_shadow import nba_engine_props_forecaster as F
from prediction_market_bot.pregame_shadow import nba_engine_props_shrunk_forecaster as SF
from tests.test_nba_engine_props_shadow import _store

ROOT = Path(__file__).resolve().parents[1]
NOW = datetime(2026, 11, 9, 12, tzinfo=timezone.utc)
TIPS = {("2026-11-09", frozenset(("NOP", "GSW"))): datetime(2026, 11, 9, 23, 0, tzinfo=timezone.utc)}


def _sim(k_true, noise, n=4000, minutes=300.0, seed=3):
    """True per-minute rates ~ gamma around 0.2 with reliability k_true (pseudo-minutes); observed over `minutes` with Poisson noise."""
    rng = np.random.default_rng(seed)
    a = k_true * 0.2
    true = rng.gamma(a, 0.2 / a, n)
    lam = true * minutes
    obs = rng.poisson(lam) / minutes if noise else true.copy()
    return true, obs


def test_constants_pinned_to_pam3_draft():
    d = json.loads((ROOT / "12_EXPLORATORY/pam_stability/trait_reliability_draft.json").read_text())
    rows = {r["stat"]: r["k"] for r in d["rows"]}
    for s in S.STATS:
        assert S.K[s] == rows[s]
    assert S.K_MIN == rows["mpg"]


def test_planted_reliability_recovered():
    """Poisson noise, true-rate sd from gamma(shape=k*0.2): the Bayes shrink constant for `m` minutes is k_true. Split-half recovers it."""
    k_true, minutes = 150.0, 400.0
    ka, kb = [], []
    for seed in (1, 2, 3, 4):
        rng = np.random.default_rng(seed)
        n = 6000
        a = k_true * 0.2
        true = rng.gamma(a, 0.2 / a, n)
        ka.append(rng.poisson(true * minutes / 2) / (minutes / 2))
        kb.append(rng.poisson(true * minutes / 2) / (minutes / 2))
    est = S.estimate_k(np.concatenate(ka), np.concatenate(kb), minutes)
    assert 0.85 * k_true < est < 1.15 * k_true


def test_shrinkage_beats_raw_mean_when_noisy_and_not_when_noise_free():
    k, lg = 150.0, 0.2
    true, obs = _sim(k, noise=True)
    mse_raw = float(np.mean((obs - true) ** 2))
    shr = np.array([S.shrunk_rate(300.0, o, k, lg) for o in obs])
    assert np.mean((shr - true) ** 2) < 0.8 * mse_raw          # planted reliability: shrinkage wins clearly
    true0, obs0 = _sim(k, noise=False)                         # zero sampling noise: the raw rate IS the truth
    shr0 = np.array([S.shrunk_rate(300.0, o, k, lg) for o in obs0])
    assert float(np.mean((obs0 - true0) ** 2)) == 0.0
    assert np.mean((shr0 - true0) ** 2) > 0.0                   # shrinking a noise-free rate can only hurt


def test_k_zero_is_the_raw_rate_times_raw_minutes():
    rows = [dict(min=30.0, points=20.0, rebounds=5.0, assists=4.0, threes=2.0), dict(min=20.0, points=10.0, rebounds=3.0, assists=2.0, threes=1.0)]
    prev = dict(min=2000.0, games=80.0, points=1200.0, rebounds=400.0, assists=300.0, threes=150.0)
    lg = {b: {s: 0.3 for s in S.STATS} for b in range(4)}
    mu = S.shrunk_mu(rows, prev, lg, k={s: 0.0 for s in S.STATS}, k_min=0.0)
    assert mu["points"] == 15.0 and mu["threes"] == 1.5      # mean of prior games, exactly the control
    far = S.shrunk_mu(rows, prev, lg, k={s: 1e9 for s in S.STATS}, k_min=1e9)
    # huge k -> the prior: (2000*0.6 + 500*0.3)/2500 = 0.54 per min (previous rate blended to league) x previous mpg 25 = 13.5
    assert abs(far["points"] - 13.5) < 1e-3


def test_no_prev_season_uses_league_prior_and_raw_minutes():
    rows = [dict(min=25.0, points=10.0, rebounds=2.0, assists=2.0, threes=1.0)] * 5
    lg = {b: {s: 0.5 for s in S.STATS} for b in range(4)}
    mu = S.shrunk_mu(rows, None, lg)
    assert mu["points"] > 10.0 and S.shrunk_minutes(5, 25.0, None) == 25.0
    assert S.shrunk_mu(rows, None, {}) is None


def _fc(cls, out, **kw):
    games, pl = F.parse_box(_store())
    return cls(games, pl, TIPS, lambda p, t: out, C2.parse_attempts(_store()), **kw)


def test_c2_and_v1_identity_untouched():
    assert C2.MODEL_ID == "nba_engine_v2_props_c2_w126_2" and C2.LAMBDA == {"rebounds": 0.26, "assists": 0.31, "threes": 0.27}
    assert len({SF.MODEL_SHA256, C2.MODEL_SHA256, F.MODEL_SHA256}) == 3 and SF.MODEL_ID != C2.MODEL_ID


def test_empty_prior_tables_reduce_to_c2_when_k_irrelevant():
    """With no prev table and no league table every player falls back to C2's raw mean: the shrunk class prices byte-identically to C2."""
    games, pl = F.parse_box(_store())
    ros = F.NBAEngineProps(games, pl, {}).roster("GSW", "2026-11-09")
    p = {"team": "GSW", "game_date": "2026-11-09"}
    c2, sh = _fc(C2.NBAEnginePropsC2, frozenset()), _fc(SF.NBAEnginePropsShrunk, frozenset())
    assert c2._mu(ros, p) == sh._mu(ros, p)


def test_shrunk_moves_the_mean_and_keeps_the_shift():
    games, pl = F.parse_box(_store())
    ros = F.NBAEngineProps(games, pl, {}).roster("GSW", "2026-11-09")
    p = {"team": "GSW", "game_date": "2026-11-09"}
    prev = {}
    for _, name, _ in ros:
        from prediction_market_bot.c1_signal_ingestion.nba_injury_reports import norm_name
        prev[norm_name(name)] = dict(min=2400.0, games=80.0, points=2400.0, rebounds=900.0, assists=700.0, threes=250.0)
    lg = {b: {s: 0.2 for s in S.STATS} for b in range(4)}
    sh = _fc(SF.NBAEnginePropsShrunk, frozenset(), prev=prev, league=lg)
    c2 = _fc(C2.NBAEnginePropsC2, frozenset())
    assert sh._mu(ros, p) != c2._mu(ros, p)
    out_name = ros[0][1]
    sh._out = frozenset({__import__("prediction_market_bot.c1_signal_ingestion.nba_injury_reports", fromlist=["norm_name"]).norm_name(out_name)})
    shifted = sh._mu(ros, p)
    assert shifted["points"][0] == 0.0 and sum(shifted["points"]) > 0
