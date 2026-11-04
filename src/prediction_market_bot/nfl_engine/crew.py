"""W99.1 Part A: NFL referee-crew priors from the Muse archive (read only), joined point-in-time to nflverse games.

Applies when a game's referee is known before the price (weekly assignment) and the question is whether the crew's
PRIOR-season penalty rate moves the total relative to the market's own line. Nothing from the season being priced
enters a game's feature (leakage rule); records are shrunk toward the league mean with K pseudo-games.
"""
from __future__ import annotations

import glob
import json
import os
from typing import Dict, Optional, Tuple

import numpy as np
import pandas as pd

SHRINK_K = 16.0  # pseudo-games toward the league mean (one crew-season is ~16 games)
ALIASES = {"Pete Morelli": "Peter Morelli", "Ron Torbert": "Ronald Torbert"}
_METRICS = {"penalties logged (count)": "pen", "penalty yardage (yards)": "yds"}


def load_crew_table(archive_dir: str) -> pd.DataFrame:
    """One row per (referee, season): games, penalties, yards (season totals, REPORTED, archive L3-split/nfl)."""
    rec: Dict[Tuple[str, int], dict] = {}
    for f in sorted(glob.glob(os.path.join(archive_dir, "L3-split", "nfl", "crew-penalties-*.claims.jsonl"))):
        with open(f) as fh:
            for line in fh:
                r = json.loads(line)
                if r.get("split") != "season total" or r.get("metric") not in _METRICS:
                    continue
                name = ALIASES.get(r["subject"], r["subject"])
                d = rec.setdefault((name, int(r["season"])), {"ref": name, "season": int(r["season"]), "games": int(r["population_n"])})
                d[_METRICS[r["metric"]]] = float(r["value"])
    return pd.DataFrame(list(rec.values())).dropna().reset_index(drop=True)


def league_rate(tab: pd.DataFrame, col: str = "pen") -> pd.Series:
    """Per-season league penalties (or yards) per crew-game."""
    g = tab.groupby("season")
    return g[col].sum() / g["games"].sum()


def prior_feature(tab: pd.DataFrame, ref: Optional[str], season: int, col: str = "pen", k: float = SHRINK_K) -> float:
    """Shrunk crew rate minus league rate, from seasons STRICTLY BEFORE ``season``. 0.0 when the crew has no record."""
    prev = tab[tab.season < season]
    if prev.empty or ref is None or (isinstance(ref, float) and np.isnan(ref)):
        return 0.0
    league = prev[col].sum() / prev["games"].sum()
    mine = prev[prev.ref == ALIASES.get(ref, ref)]
    if mine.empty:
        return 0.0
    return float((mine[col].sum() + k * league) / (mine["games"].sum() + k) - league)


def attach_feature(sched: pd.DataFrame, tab: pd.DataFrame, col: str = "pen", k: float = SHRINK_K) -> pd.DataFrame:
    out = sched.copy()
    out["crew_" + col] = [prior_feature(tab, r, int(s), col, k) for r, s in zip(out["referee"], out["season"])]
    return out


def fit_beta(x: np.ndarray, resid: np.ndarray) -> float:
    """OLS slope through the origin of (actual total - total line) on the crew feature (feature is centred)."""
    d = float((x * x).sum())
    return float((x * resid).sum() / d) if d > 0 else 0.0
