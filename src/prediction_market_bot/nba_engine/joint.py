"""NBA engine joint with a shared latent (W113.3, B-086): same-player and teammate legs priced from one draw.

W110.4 measured the props layer (``props.py``) wrong where legs share a player: points x threes realised covariance +0.091
vs engine +0.005, teammates' points negative where realised is positive. Cause: each player's other stats were drawn
independently of the player's points, and teammates split a fixed team total with no common cause.

Here one game draw (team points T, margin from the engine's own ``simulate``) gets, per team, these shared latents:
  * pace   = T / mean team points   (every rate stat scales with it)
  * blowout = how far |margin| exceeds a threshold: starters lose minutes, the bench and the "rest" bucket gain them
  * minutes  M_i = mpg_i * exp(s_min * e_i) * blowout factor   (e_i a player-night draw)
  * form     u_i, a player-night draw shared by the player's usage weight, his three-point rate and his assist rate
Points are a multinomial split of T with weights rate_i * M_i * exp(s_use * u_i) (+ a rest bucket), so a usage shift lowers a
teammate's points while a common minutes cut lifts nobody's. Threes are Binomial(points // 3, q_i * exp(s3 * u_i)), so threes are
part of points. Rebounds and assists are negative-binomial around rate * M_i * pace^beta (assists also load on form).

When it applies: pre-game, with per-player trailing means and minutes (point-in-time) and the engine's team points draws.
When it does not: it does not decide who plays (the caller passes expected minutes, 0 for out) and rebounds/assists carry no
team-total cap (a leg never needs one). The team's points, hence moneyline / spread / total / team total, are the engine's
own draws and are returned unchanged: this module only adds the player layer.
"""
from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Mapping, Sequence

import numpy as np

STATS = ("points", "rebounds", "assists", "threes")


@dataclass(frozen=True)
class JointParams:
    """Latent scales. Defaults are the values fitted on the 2024-25 season (random search, 200 games after the first 60, 70 draws of params; see 12_EXPLORATORY/sgp_correlation/fit_joint.py and fit_joint_2024-25.json)."""
    blow_thresh: float = 4       # |margin| above which starters start to sit
    blow_k: float = 0.19502           # fraction of starter minutes lost at a 23+ point margin
    s_min: float = 0.10618            # sd of log minutes (foul trouble, rotation)
    s_use: float = 0.2832            # sd of log usage weight (player-night form)
    s_three: float = 0.23287          # loading of form on the three-point share of the player's points
    s_reb: float = 0.06697             # loading of form on rebounds (fitted; 0 = rebounds follow minutes and pace only)
    s_ast: float = 0.02839            # loading of form on assists
    rest_floor: float = 0.03       # least share of team points left to players outside the modelled roster
    beta_reb: float = -0.16905        # elasticity of rebounds to the game's pace (T / mean T)
    beta_ast: float = 0.0
    r_reb: float = 14.0            # negative-binomial dispersion (var = m + m^2 / r)
    r_ast: float = 12.0
    max_min: float = 42.0
    # W114.4 team pool (default 0 = off: the 2024-25 fit, fit_joint_2024-25_w114.json, did not improve held-out teammate legs; see RESULT_W114_4.md): one usage pool per team per game (the shares sum to the team's possessions used).
    s_pool: float = 0.0             # sd of the team-level log weight of the non-modelled bucket: when the bench/rest takes less, every named teammate scores more
    s_tmin: float = 0.0             # sd of a team-level log-minutes shock shared by all named players (game script, rotation)
    gamma_ast: float = 0.0          # elasticity of a player's assists to his teammates' made shots (team points less his own, vs expectation)
    gamma_reb: float = 0.0          # elasticity of rebounds to the game's misses (opponent points below expectation -> more misses)


@dataclass(frozen=True)
class JointRoster:
    """Expected per-game stats and minutes of each modelled player (same order everywhere)."""
    players: tuple[str, ...]
    mpg: Sequence[float]
    mu: Mapping[str, Sequence[float]]      # per-game means for points / rebounds / assists / threes
    team_mean_pts: float
    usage: Sequence[float] | None = None   # multiplicative tilt on a player's scoring weight (a lineup / usage-shift factor); 1 = none


@dataclass(frozen=True)
class JointDraws:
    """(n, k) integer draws per stat for the k players, the (n,) rest-bucket points, and the shared latents."""
    players: tuple[str, ...]
    stat: dict
    rest_points: np.ndarray
    minutes: np.ndarray
    pace: np.ndarray


def _rates(roster: JointRoster):
    mpg = np.maximum(np.asarray(roster.mpg, float), 1.0)
    return mpg, {s: np.maximum(np.asarray(roster.mu[s], float), 1e-6) / mpg for s in STATS}


def _split(total: np.ndarray, w: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    """Exact multinomial(total_t, w_t / sum w_t) per row by sequential binomials; (n, k) with column order of ``w``."""
    n, k = w.shape
    out = np.zeros((n, k), dtype=np.int64)
    remaining = np.asarray(total, np.int64).copy()
    rem_w = w.sum(axis=1)
    for j in range(k - 1):
        p = np.clip(w[:, j] / np.maximum(rem_w, 1e-12), 0.0, 1.0)
        x = rng.binomial(remaining, p)
        out[:, j] = x
        remaining = remaining - x
        rem_w = rem_w - w[:, j]
    out[:, k - 1] = remaining
    return out


def _nb(mean: np.ndarray, r: float, rng: np.random.Generator) -> np.ndarray:
    lam = rng.gamma(r, np.maximum(mean, 1e-9) / r)
    return rng.poisson(lam).astype(np.int64)


def simulate_team(team_pts: np.ndarray, margin_abs: np.ndarray, roster: JointRoster, rng: np.random.Generator,
                  p: JointParams = JointParams(), opp_pts: np.ndarray | None = None, opp_mean_pts: float | None = None) -> JointDraws:
    """Player stats for one team from the engine's draws of the team's points and the game's |margin|.

    W114.4: the team is ONE usage pool. Points are a multinomial split of T over the named players plus a rest bucket, so the shares
    sum to T; a team-level latent moves the rest bucket's weight (``s_pool``) and the named players' minutes together (``s_tmin``),
    which gives teammates positive covariance the fixed split alone cannot. Assists load on the teammates' made shots (T less the
    player's own points, ``gamma_ast``); rebounds load on the game's misses, proxied by the opponent scoring below its mean
    (``gamma_reb``, needs ``opp_pts``)."""
    T = np.asarray(team_pts, np.int64)
    n, k = len(T), len(roster.players)
    mpg, rate = _rates(roster)
    pace = np.maximum(T, 1) / roster.team_mean_pts
    blow = np.clip((np.asarray(margin_abs, float) - p.blow_thresh) / 15.0, 0.0, 1.0)            # (n,)
    starter = np.clip((mpg - 20.0) / 12.0, -1.0, 1.0)                                          # +1 starter, -1 deep bench
    fac = 1.0 - p.blow_k * blow[:, None] * starter[None, :]                                    # (n, k)
    e = rng.standard_normal((n, k))
    u = rng.standard_normal((n, k))
    z_min = rng.standard_normal((n, 1))
    z_pool = rng.standard_normal(n)
    minutes = np.clip(mpg[None, :] * np.exp(p.s_min * e - 0.5 * p.s_min ** 2 + p.s_tmin * z_min - 0.5 * p.s_tmin ** 2) * fac,
                      0.0, p.max_min)
    tilt = np.ones(k) if roster.usage is None else np.asarray(roster.usage, float)
    w_pts = (rate["points"] * tilt)[None, :] * minutes * np.exp(p.s_use * u - 0.5 * p.s_use ** 2)
    uncovered = max(roster.team_mean_pts - float((rate["points"] * mpg).sum()), p.rest_floor * roster.team_mean_pts)
    w_rest = uncovered * (1.0 + 2.0 * p.blow_k * blow) * np.exp(p.s_pool * z_pool - 0.5 * p.s_pool ** 2)   # bench soaks up blowouts; team-level pool shock
    parts = _split(T, np.hstack([w_pts, w_rest[:, None]]), rng)
    pts, rest = parts[:, :k], parts[:, k]
    q = np.clip(3.0 * rate["threes"] / np.maximum(rate["points"], 1e-6), 0.0, 0.9)             # share of a player's points from threes
    q_n = np.clip(q[None, :] * np.exp(p.s_three * u - 0.5 * p.s_three ** 2), 0.0, 0.95)
    threes = rng.binomial(pts // 3, q_n)
    miss = np.ones((n, 1))
    if opp_pts is not None and p.gamma_reb:
        miss = (np.maximum(np.asarray(opp_pts, float), 1.0) / float(opp_mean_pts or np.mean(opp_pts)))[:, None] ** (-p.gamma_reb)
    own = np.maximum(T[:, None] - pts, 1.0) / np.maximum(roster.team_mean_pts - (rate["points"] * mpg)[None, :], 1.0)   # teammates' makes vs expectation
    makes = own ** p.gamma_ast
    reb = _nb(rate["rebounds"][None, :] * minutes * pace[:, None] ** p.beta_reb * miss * np.exp(p.s_reb * u - 0.5 * p.s_reb ** 2), p.r_reb, rng)
    ast = _nb(rate["assists"][None, :] * minutes * pace[:, None] ** p.beta_ast * makes * np.exp(p.s_ast * u - 0.5 * p.s_ast ** 2),
              p.r_ast, rng)
    return JointDraws(roster.players, {"points": pts, "rebounds": reb, "assists": ast, "threes": threes}, rest, minutes, pace)


def price_game(home_pts: np.ndarray, away_pts: np.ndarray, home: JointRoster, away: JointRoster,
               strikes: Mapping[str, Sequence[int]], seed: int = 0, p: JointParams = JointParams()):
    """{stat: {player: {strike: P(stat >= strike)}}} for both rosters, drawn jointly with the engine's team scores."""
    rng = np.random.default_rng(seed)
    margin_abs = np.abs(np.asarray(home_pts, float) - np.asarray(away_pts, float))
    out: dict = {s: {} for s in STATS}
    for roster, pts in ((home, home_pts), (away, away_pts)):
        opp, opp_roster = (away_pts, away) if roster is home else (home_pts, home)
        d = simulate_team(pts, margin_abs, roster, rng, p, opp_pts=opp, opp_mean_pts=opp_roster.team_mean_pts)
        for stat in STATS:
            for i, name in enumerate(roster.players):
                out[stat][name] = {int(kk): float((np.sum(d.stat[stat][:, i] >= kk) + 0.5) / (len(pts) + 1.0))
                                   for kk in strikes[stat]}
    return out


def with_params(**kw) -> JointParams:
    return replace(JointParams(), **kw)
