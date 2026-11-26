"""Point-in-time NBA archetype mixture on the PRF-1..15 taxonomy (W130.4 Part B).

Mass-tier classifier: no human label enters the fit. The fit step stores the mean and sd of each profile feature from
TRAINING seasons only (end-of-season profiles, ``min_poss`` on the floor); ``assign`` z-scores a point-in-time profile
with those stored numbers and turns per-archetype scores into a softmax mixture. The score of each archetype is a
fixed, signed combination of the signals that taxonomy.json names for it (written below, not tuned). Two named choices,
neither fitted to the 100 deep-tier records: TEMP (softmax temperature) and RELIAB_K (possessions of pseudo-evidence).

Not derivable from the event store, so given NO score (weight 0, listed in ``UNBUILT``): PRF-10 POA Stopper
(needs matchup/screen-navigation tracking) and PRF-13 Transition Weapon (needs per-player transition frequency).
PRF-6 Post/Elbow Hub is scored from a big's assist rate because post-up counts do not exist in the store.
"""
from __future__ import annotations

import math
from typing import Mapping

import numpy as np
import pandas as pd

VERSION = "pit-archetype-w130.4-v1"
TEMP = 0.75        # softmax temperature (named choice)
RELIAB_K = 1500.0  # pseudo-possessions for the confidence shrink (named choice)
MIN_W = 0.10       # weights below this are dropped, rest renormalised
MAX_ARCH = 3
UNBUILT = ("PRF-10", "PRF-13")
FEATURES = ["usage_per100", "ast_per100", "tov_per100", "fta_rate", "rim_share", "three_share", "rim_fg", "three_fg",
            "oreb_share", "dreb_share", "stl_per100", "blk_per100", "opp_rim_rate_on", "dreb_per100", "mpg"]


def with_derived(f: pd.DataFrame) -> pd.DataFrame:
    f = f.copy()
    f["mpg"] = f["minutes"] / f["gp"].clip(lower=1)
    return f


def fit(train_profiles: pd.DataFrame) -> dict:
    """train_profiles: end-of-season profiles from training seasons only (already filtered to min_poss)."""
    t = with_derived(train_profiles)
    mu, sd = t[FEATURES].mean(), t[FEATURES].std(ddof=0).replace(0, 1.0)
    return {"version": VERSION, "mu": mu.to_dict(), "sd": sd.to_dict(), "n_train": int(len(t))}


def _z(f: pd.DataFrame, params: Mapping) -> pd.DataFrame:
    f = with_derived(f)
    mu, sd = pd.Series(params["mu"]), pd.Series(params["sd"])
    return (f[FEATURES] - mu) / sd


def scores(f: pd.DataFrame, params: Mapping) -> pd.DataFrame:
    z = _z(f, params)
    big = (z["dreb_per100"] + z["blk_per100"] + z["rim_share"] - z["three_share"]) / 4.0
    mid_u = -z["usage_per100"].sub(0.3).abs()   # prefers mid-high usage rather than extreme
    s = pd.DataFrame(index=f.index)
    s["PRF-1"] = 1.3 * z["usage_per100"] + 0.6 * z["ast_per100"] + 0.4 * z["fta_rate"]
    s["PRF-2"] = 0.9 * z["usage_per100"] + 0.7 * z["ast_per100"] + 0.4 * z["fta_rate"] + 0.5 * mid_u - 0.5 * big
    s["PRF-3"] = 0.9 * z["ast_per100"] - 0.4 * z["tov_per100"] + 0.4 * mid_u - 0.4 * big
    s["PRF-4"] = 1.1 * z["three_share"] + 0.5 * z["three_fg"] - 0.5 * z["usage_per100"] - 0.4 * big
    s["PRF-5"] = 1.0 * z["rim_share"] + 0.8 * z["fta_rate"] + 0.3 * z["usage_per100"] - 0.8 * big
    s["PRF-6"] = 0.9 * big + 0.8 * z["ast_per100"] - 0.4 * z["three_share"]
    s["PRF-7"] = 0.9 * big + 0.7 * z["rim_share"] + 0.5 * z["rim_fg"] - 0.6 * z["three_share"] - 0.4 * z["usage_per100"]
    s["PRF-8"] = 0.8 * big + 1.0 * z["three_share"] + 0.4 * z["three_fg"]
    s["PRF-9"] = 1.1 * z["blk_per100"] - 0.8 * z["opp_rim_rate_on"] + 0.5 * big
    s["PRF-11"] = 0.7 * z["stl_per100"] + 0.4 * z["blk_per100"] - 0.7 * big - 0.2 * z["usage_per100"]
    s["PRF-12"] = 0.8 * z["dreb_share"] + 0.8 * z["oreb_share"] + 0.3 * big
    s["PRF-14"] = 0.8 * z["usage_per100"] - 1.0 * z["mpg"] + 0.3 * z["fta_rate"]
    s["PRF-15"] = -1.0 * z["usage_per100"] - 0.5 * z["tov_per100"] + 0.3 * z["three_fg"]
    return s


def assign(f: pd.DataFrame, params: Mapping) -> pd.DataFrame:
    """Returns one row per player: weights (dict), confidence, top. Weights sum to 1 over <= MAX_ARCH archetypes."""
    s = scores(f, params)
    e = np.exp((s.sub(s.max(axis=1), axis=0)) / TEMP)
    w = e.div(e.sum(axis=1), axis=0)
    rows = []
    k = w.shape[1]
    for pid, r in w.iterrows():
        top = r.sort_values(ascending=False).head(MAX_ARCH)
        top = top[top >= MIN_W] if (top >= MIN_W).any() else top.head(1)
        top = top / top.sum()
        h = -(r * np.log(r.clip(lower=1e-12))).sum() / math.log(k)
        poss = float(f.loc[pid, "poss"])
        conf = float((1 - h) * poss / (poss + RELIAB_K))
        wd = {a: round(float(v), 4) for a, v in top.items()}
        last = list(wd)[-1]
        wd[last] = round(1.0 - sum(v for k2, v in wd.items() if k2 != last), 4)  # exact sum 1 after rounding
        rows.append({"pid": pid, "weights": wd, "confidence": round(conf, 4),
                     "top": top.index[0], "poss": poss})
    return pd.DataFrame(rows).set_index("pid")
