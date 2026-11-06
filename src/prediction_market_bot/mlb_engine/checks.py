"""Store integrity checks: duplicates, pitch counts vs box scores, id resolution, point-in-time."""
from __future__ import annotations

import json
import urllib.request
from pathlib import Path
from typing import Callable, Dict, Iterable, Optional

import pandas as pd

from .store import KEY

BOX_URL = "https://statsapi.mlb.com/api/v1/game/{pk}/boxscore"
REGISTER_URL = "https://raw.githubusercontent.com/chadwickbureau/register/master/data/people-{h}.csv"


def duplicate_pitches(p: pd.DataFrame) -> int:
    return int(p.duplicated(subset=KEY).sum())


def fetch_boxscore(pk: int, timeout: int = 30) -> dict:
    req = urllib.request.Request(BOX_URL.format(pk=pk), headers={"User-Agent": "pm-bot mlb_engine"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())


def box_totals(box: dict) -> Dict[str, int]:
    """Pitches thrown (both teams) and final runs from a Stats API boxscore payload."""
    t = box["teams"]
    return {
        "pitches": int(t["home"]["teamStats"]["pitching"].get("pitchesThrown", 0))
        + int(t["away"]["teamStats"]["pitching"].get("pitchesThrown", 0)),
        "home_runs": int(t["home"]["teamStats"]["batting"].get("runs", 0)),
        "away_runs": int(t["away"]["teamStats"]["batting"].get("runs", 0)),
    }


def pitch_counts_vs_box(
    games: pd.DataFrame, sample: Iterable[int], fetcher: Callable[[int], dict] = fetch_boxscore
) -> pd.DataFrame:
    """Per sampled game: store pitch count vs box-score pitchesThrown, and the final score both ways."""
    g = games.set_index("game_pk")
    rows = []
    for pk in sample:
        b = box_totals(fetcher(int(pk)))
        r = g.loc[pk]
        rows.append({
            "game_pk": int(pk), "store_pitches": int(r["n_pitches"]), "box_pitches": b["pitches"],
            "pitch_diff": int(r["n_pitches"]) - b["pitches"],
            "score_match": bool(int(r["home_runs"]) == b["home_runs"] and int(r["away_runs"]) == b["away_runs"]),
        })
    return pd.DataFrame(rows)


def load_register(cache: Path) -> pd.DataFrame:
    """Chadwick register (id crosswalk), cached; only the columns we need."""
    cache = Path(cache)
    if cache.exists():
        return pd.read_parquet(cache)
    frames = []
    for h in "0123456789abcdef":
        req = urllib.request.Request(REGISTER_URL.format(h=h), headers={"User-Agent": "pm-bot mlb_engine"})
        with urllib.request.urlopen(req, timeout=90) as r:
            frames.append(pd.read_csv(r, usecols=["key_mlbam", "key_retro", "key_bbref", "name_first", "name_last"],
                                      low_memory=False))
    reg = pd.concat(frames, ignore_index=True).dropna(subset=["key_mlbam"])
    reg["key_mlbam"] = reg["key_mlbam"].astype("int64")
    reg.to_parquet(cache, index=False)
    return reg


def unresolved_ids(p: pd.DataFrame, register: pd.DataFrame) -> Dict[str, int]:
    known = set(register["key_mlbam"].astype("int64"))
    out = {}
    for col in ("pitcher", "batter"):
        ids = set(p[col].dropna().astype("int64"))
        out[col] = len(ids - known)
        out[col + "_total"] = len(ids)
    return out


def assert_no_future_rows(pit: pd.DataFrame, player: str, source: pd.DataFrame, count_col: str,
                          source_count_fn: Callable[[pd.DataFrame], pd.Series]) -> bool:
    """For each pit row, recompute the count from `source` rows with game_date < as_of; must equal."""
    cnt = source_count_fn(source).groupby([source[player], source["game_date"]]).sum()
    for _, r in pit.iterrows():
        mask = (cnt.index.get_level_values(0) == r[player]) & (cnt.index.get_level_values(1) < r["game_date"])
        if abs(float(cnt[mask].sum()) - float(r[count_col])) > 1e-9:
            return False
    return True
