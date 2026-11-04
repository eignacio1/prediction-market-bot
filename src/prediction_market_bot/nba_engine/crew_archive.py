"""W99.1 Part B: NBA referee priors from the Muse archive (read only), joined to each game's crew.

Applies to a game whose crew is known (the box officials table is post-game with no assignment timestamp, GG-1390, so
every result built on it is a game-day-known upper bound). A referee's feature is the PRIOR-season record (archive
``referees-<start-year>``, Basketball-Reference register: games worked, PF/g, FTA/g, total points/g) shrunk to the league
mean with K games; a game's feature is the mean over its crew. ``box_season = archive_start_year + 1`` (2024-25 -> 2025).
"""
from __future__ import annotations

import glob
import json
import os
import re
import unicodedata
from typing import Dict, Iterable, Tuple

import numpy as np
import pandas as pd

SHRINK_K = 30.0
_M = {
    "games worked": "g",
    "personal fouls per game": "pf",
    "free-throw attempts per game": "fta",
    "total points per game": "pts",
}


def norm_name(s: str) -> str:
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode().lower()
    s = re.sub(r"\b(jr|sr|ii|iii)\b\.?", "", s)
    return re.sub(r"[^a-z ]", "", s).strip()


def load_ref_table(archive_dir: str) -> pd.DataFrame:
    """One row per (referee, box_season): g, pf, fta, pts."""
    rec: Dict[Tuple[str, int], dict] = {}
    for f in sorted(glob.glob(os.path.join(archive_dir, "L3-split", "nba", "referees-*.claims.jsonl"))):
        with open(f) as fh:
            for line in fh:
                r = json.loads(line)
                key = next((v for k, v in _M.items() if r["metric"].startswith(k)), None)
                if key is None or r.get("value") is None:
                    continue
                b = int(r["season"]) + 1
                d = rec.setdefault((norm_name(r["subject"]), b), {"ref": norm_name(r["subject"]), "box_season": b})
                d[key] = float(r["value"])
    t = pd.DataFrame(list(rec.values())).dropna().reset_index(drop=True)
    return t


def ref_prior(tab: pd.DataFrame, ref: str, box_season: int, col: str, k: float = SHRINK_K) -> float:
    """Shrunk per-game rate minus league rate, from archive seasons with box label STRICTLY BEFORE ``box_season``.
    Weighted by games worked. 0.0 with no record."""
    prev = tab[tab.box_season < box_season]
    if prev.empty:
        return 0.0
    league = float((prev[col] * prev.g).sum() / prev.g.sum())
    mine = prev[prev.ref == ref]
    if mine.empty:
        return 0.0
    n = float(mine.g.sum())
    return float(((mine[col] * mine.g).sum() + k * league) / (n + k) - league)


def crew_features(tab: pd.DataFrame, crews: pd.DataFrame, game_season: Dict[str, int], cols: Iterable[str] = ("pf", "fta", "pts")) -> pd.DataFrame:
    """``crews``: game_id, ref (normalised name). Returns index game_id, columns crew_<col>, crew_matched (share of the
    crew with an archive record before the game's season)."""
    cols = list(cols)
    cache: Dict[Tuple[str, int, str], float] = {}
    seen = set(tab.ref)
    out = []
    for gid, grp in crews.groupby("game_id"):
        s = game_season[gid]
        row = {"game_id": gid}
        for c in cols:
            vals = []
            for r in grp.ref:
                key = (r, s, c)
                if key not in cache:
                    cache[key] = ref_prior(tab, r, s, c)
                vals.append(cache[key])
            row["crew_" + c] = float(np.mean(vals)) if vals else 0.0
        prior = tab[tab.box_season < s]
        row["crew_matched"] = float(np.mean([r in set(prior.ref) for r in grp.ref])) if len(grp) else 0.0
        out.append(row)
    return pd.DataFrame(out).set_index("game_id")
