"""NHL granularity index (W109.2): the filtering mechanism -- split, rank vs history, matchup cross, market map.

The factor built here is a REST-STATE split of regulation scoring: how much a team's goals for / against move when it is
on the second night of a back-to-back (rest < 1.5 days) versus rested, relative to its own season mean. Everything is
point-in-time: a game's number uses only that team's EARLIER games of the same season (the game itself and anything
later never enter), and the rank uses only EARLIER seasons.

Five parts (GRANULARITY_INDEX.md): split (``asof_split``), rank vs history at the same games-played point
(``rank_vs_history``), matchup cross (``game_cross``), market map (``MARKET_MAP``), application
(``fit_shift_weight`` + ``apply_shift``). ``stability`` is the gate: a split whose odd/even reliability interval does
not clear zero is not passed to the price (``filter_entries``).

When it applies: regular-season games with the team's rest known and >= ``min_n`` prior games in the bucket. When it
does not: a team's first games of a season (shrunk to zero by construction), playoffs (rest is not back-to-back
scheduling), and any bucket with a handful of games -- the shrinkage ``n/(n+k)`` is the guard, not a proof.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

B2B_REST_DAYS = 1.5
BOOT_SEED = 20261111

# Which Kalshi families each split informs (the market map).
MARKET_MAP = {
    "gf": ("TEAMTOTAL_OWN", "TOTAL", "SPREAD_OWN", "ML_OWN"),
    "ga": ("TEAMTOTAL_OPP", "TOTAL", "SPREAD_OPP", "ML_OPP"),
    "total": ("TOTAL",),
}


def team_games(fr: pd.DataFrame) -> pd.DataFrame:
    """One row per (team, game) from the per-game frame: regulation goals for/against, rest, home, and ``game_no``
    (1-based order of the team's games inside its season by puck drop). Needs reg_h/reg_a, rest_h/rest_a, team_id_h/a."""
    rows = []
    for s, o in (("h", "a"), ("a", "h")):
        rows.append(pd.DataFrame({
            "game_id": fr["game_id"].to_numpy(), "season": fr["season"].to_numpy(), "start": pd.to_datetime(fr["start"]).to_numpy(),
            "team": fr[f"team_id_{s}"].to_numpy(), "opp": fr[f"team_id_{o}"].to_numpy(),
            "is_home": 1 if s == "h" else 0,
            "gf": fr[f"reg_{s}"].to_numpy(float), "ga": fr[f"reg_{o}"].to_numpy(float),
            "rest": fr[f"rest_{s}"].to_numpy(float)}))
    tg = pd.concat(rows, ignore_index=True)
    tg["total"] = tg["gf"] + tg["ga"]
    tg["b2b"] = (tg["rest"] < B2B_REST_DAYS).astype(int)
    tg = tg.sort_values(["team", "season", "start", "game_id"]).reset_index(drop=True)
    tg["game_no"] = tg.groupby(["team", "season"]).cumcount() + 1
    return tg


def asof_split(tg: pd.DataFrame, metric: str, k: float = 8.0, bucket: str = "b2b") -> pd.DataFrame:
    """Point-in-time split. For each team-game: ``n_b`` earlier games of the same team-season in the SAME bucket as this
    game, ``delta_raw`` = mean of ``metric`` in those games minus the mean over ALL earlier games (so a rest-state effect e
    of size e on a share p of games reads as e*(1-p) for the b2b bucket), and
    ``delta`` = delta_raw * n_b/(n_b+k). NaN-free: with no earlier games in the bucket (or none at all) delta = 0."""
    d = tg.sort_values(["team", "season", "game_no"]).copy()
    g = d.groupby(["team", "season"])
    prior_n = g.cumcount()
    prior_sum = g[metric].cumsum() - d[metric]
    out_n_b = np.zeros(len(d)); out_sum_b = np.zeros(len(d))
    for flag in (0, 1):
        m = (d[bucket] == flag).astype(float)
        cs_n = m.groupby([d["team"], d["season"]]).cumsum() - m
        cs_s = (d[metric] * m).groupby([d["team"], d["season"]]).cumsum() - d[metric] * m
        sel = (d[bucket] == flag).to_numpy()
        out_n_b[sel] = cs_n.to_numpy()[sel]; out_sum_b[sel] = cs_s.to_numpy()[sel]
    n_all = prior_n.to_numpy(float)
    with np.errstate(invalid="ignore", divide="ignore"):
        mean_b = np.where(out_n_b > 0, out_sum_b / np.maximum(out_n_b, 1), 0.0)
        mean_all = np.where(n_all > 0, prior_sum.to_numpy() / np.maximum(n_all, 1), 0.0)
    raw = np.where((out_n_b > 0) & (n_all > 0), mean_b - mean_all, 0.0)
    d[f"n_b_{metric}"] = out_n_b
    d[f"delta_raw_{metric}"] = raw
    d[f"delta_{metric}"] = np.where(out_n_b + k > 0, raw * out_n_b / np.maximum(out_n_b + k, 1e-12), 0.0)
    return d


def rank_vs_history(d: pd.DataFrame, col: str, window: int = 3) -> pd.Series:
    """Percentile (0..1) of this row's ``col`` among rows from EARLIER seasons with the same bucket and a games-played
    count within +-``window``. NaN when there is no earlier season (the first season in the table)."""
    out = np.full(len(d), np.nan)
    d = d.reset_index(drop=True)
    for s in sorted(d["season"].unique()):
        hist = d[d["season"] < s]
        if hist.empty:
            continue
        idx = d.index[d["season"] == s]
        for b in (0, 1):
            h = hist[hist["b2b"] == b]
            hg = h["game_no"].to_numpy(); hv = h[col].to_numpy()
            for i in idx[(d.loc[idx, "b2b"] == b).to_numpy()]:
                m = np.abs(hg - d.at[i, "game_no"]) <= window
                if m.sum() >= 20:
                    out[i] = float(np.mean(hv[m] <= d.at[i, col]))
    return pd.Series(out, index=d.index, name=f"rank_{col}")


def _spearman_brown(r: float) -> float:
    return 2 * r / (1 + r) if r > -1 else float("nan")


def stability(tg: pd.DataFrame, metric: str = "gf", min_each: int = 4, n_boot: int = 1000, seed: int = BOOT_SEED) -> dict:
    """Odd/even split-half reliability of the b2b-minus-rested contrast across team-seasons (Spearman-Brown), with a
    bootstrap interval over team-seasons. A contrast is built from odd-numbered games and from even-numbered games
    separately; the correlation between the two contrasts is the reliability. Team-seasons need ``min_each`` b2b games
    in each half."""
    rows = []
    for (t, s), g in tg.groupby(["team", "season"]):
        c = []
        for par in (0, 1):
            h = g[g["game_no"] % 2 == par]
            hb, hr = h[h["b2b"] == 1][metric], h[h["b2b"] == 0][metric]
            c.append(hb.mean() - hr.mean() if len(hb) >= min_each and len(hr) >= min_each else np.nan)
        if not np.isnan(c).any():
            rows.append(c)
    a = np.array(rows)
    if len(a) < 10:
        return {"r": float("nan"), "sb": float("nan"), "lo": float("nan"), "hi": float("nan"), "n": int(len(a))}
    r = float(np.corrcoef(a[:, 0], a[:, 1])[0, 1])
    rng = np.random.default_rng(seed)
    bs = []
    for _ in range(n_boot):
        ix = rng.integers(0, len(a), len(a))
        bs.append(_spearman_brown(float(np.corrcoef(a[ix, 0], a[ix, 1])[0, 1])))
    return {"r": r, "sb": _spearman_brown(r), "lo": float(np.nanquantile(bs, 0.025)), "hi": float(np.nanquantile(bs, 0.975)), "n": int(len(a))}


def game_cross(fr: pd.DataFrame, tg_gf: pd.DataFrame, tg_ga: pd.DataFrame) -> pd.DataFrame:
    """Matchup cross on the game table. ``tg_gf``/``tg_ga`` are ``asof_split`` outputs for metric gf / ga. The home side's
    expected-goal shift is its own offence split plus the road team's defence split (each measured in the bucket that
    team is in tonight); the road side's is the mirror. Additive: both are deviations from a team's own mean."""
    a = tg_gf.set_index(["game_id", "is_home"]); b = tg_ga.set_index(["game_id", "is_home"])
    gid = fr["game_id"].to_numpy()
    sh_h = a.loc[list(zip(gid, [1] * len(gid))), "delta_gf"].to_numpy() + b.loc[list(zip(gid, [0] * len(gid))), "delta_ga"].to_numpy()
    sh_a = a.loc[list(zip(gid, [0] * len(gid))), "delta_gf"].to_numpy() + b.loc[list(zip(gid, [1] * len(gid))), "delta_ga"].to_numpy()
    nb = np.minimum(a.loc[list(zip(gid, [1] * len(gid))), "n_b_gf"].to_numpy(), a.loc[list(zip(gid, [0] * len(gid))), "n_b_gf"].to_numpy())
    return pd.DataFrame({"game_id": gid, "shift_h": sh_h, "shift_a": sh_a, "shift_total": sh_h + sh_a, "min_n_b": nb})


def filter_entries(x: pd.DataFrame, stable: bool, min_n: float = 5.0, tail: float = 0.0, col: str = "shift_total") -> pd.DataFrame:
    """Keep rows the filter lets through: the split is stable (gate), the smaller bucket count >= ``min_n``, and |``col``|
    >= ``tail``. A failed stability gate returns nothing: an unreliable split does not move a price."""
    if not stable:
        return x.iloc[0:0]
    return x[(x["min_n_b"] >= min_n) & (x[col].abs() >= tail)]


def fit_shift_weight(shift: np.ndarray, resid: np.ndarray) -> float:
    """OLS weight through the origin of realized residual (actual - predicted goals) on the cross shift, fit on TRAINING
    games only; clipped to [0, 1.5] (a negative weight is not applied: the sign is the thesis)."""
    s = np.asarray(shift, float); r = np.asarray(resid, float)
    den = float((s ** 2).sum())
    return float(np.clip((s * r).sum() / den, 0.0, 1.5)) if den > 0 else 0.0


def apply_shift(lam_h: np.ndarray, lam_a: np.ndarray, shift_h: np.ndarray, shift_a: np.ndarray, w: float, floor: float = 0.3):
    """lam' = max(lam + w*shift, floor), per side."""
    return np.maximum(np.asarray(lam_h, float) + w * np.asarray(shift_h, float), floor), \
        np.maximum(np.asarray(lam_a, float) + w * np.asarray(shift_a, float), floor)
