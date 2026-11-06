"""Pitch store: raw Savant day files -> typed parquet tables (pitches, plate appearances, games).

Point-in-time safety is decided HERE, at ingest: LEAKY_COLUMNS are dropped because they describe the
future relative to the pitch (days until the player's next game) or are deprecated. Outcome columns
that describe the pitch itself (description, events, launch_speed) stay: they are facts AT that pitch
and become point-in-time features only after aggregation with a strict earlier-date cut (pit.py).
"""
from __future__ import annotations

import gzip
import io
from datetime import date
from pathlib import Path
from typing import Iterable, List

import numpy as np
import pandas as pd

# Columns that look into the future of the pitch (never usable as a feature) -- dropped at ingest.
LEAKY_COLUMNS = ("pitcher_days_until_next_game", "batter_days_until_next_game")

KEEP = [
    "game_pk", "game_date", "at_bat_number", "pitch_number", "pitcher", "batter", "p_throws", "stand",
    "home_team", "away_team", "inning", "inning_topbot", "outs_when_up", "balls", "strikes",
    "on_1b", "on_2b", "on_3b", "pitch_type", "release_speed", "release_spin_rate", "release_extension",
    "pfx_x", "pfx_z", "plate_x", "plate_z", "zone", "type", "description", "events", "bb_type",
    "launch_speed", "launch_angle", "bat_speed", "swing_length", "woba_value", "woba_denom",
    "estimated_woba_using_speedangle", "delta_run_exp",
    "home_score", "away_score", "post_home_score", "post_away_score",
]
KEY = ["game_pk", "at_bat_number", "pitch_number"]

SWING_DESC = {
    "swinging_strike", "swinging_strike_blocked", "foul_tip", "foul", "hit_into_play", "foul_bunt",
    "missed_bunt", "bunt_foul_tip", "hit_into_play_no_out", "hit_into_play_score",
}
WHIFF_DESC = {"swinging_strike", "swinging_strike_blocked", "foul_tip", "missed_bunt", "bunt_foul_tip"}
FASTBALL = {"FF", "SI", "FC", "FA"}


def read_raw_day(path: Path) -> pd.DataFrame:
    with gzip.open(path, "rb") as fh:
        body = fh.read()
    if not body.strip():
        return pd.DataFrame(columns=KEEP)
    df = pd.read_csv(io.BytesIO(body), encoding="utf-8-sig", low_memory=False)
    df = df.drop(columns=[c for c in LEAKY_COLUMNS if c in df.columns])
    for c in KEEP:
        if c not in df.columns:
            df[c] = np.nan
    return df[KEEP]


def load_raw(store: Path, years: Iterable[int]) -> pd.DataFrame:
    frames: List[pd.DataFrame] = []
    for y in years:
        for p in sorted((Path(store) / "raw" / str(y)).glob("*.csv.gz")):
            f = read_raw_day(p)
            if len(f):
                frames.append(f)
    if not frames:
        return pd.DataFrame(columns=KEEP)
    return pd.concat(frames, ignore_index=True)


def clean_pitches(df: pd.DataFrame) -> pd.DataFrame:
    """Typed, de-duplicated, ordered. Duplicates on (game_pk, at_bat_number, pitch_number) keep the first."""
    d = df.copy()
    d["game_date"] = pd.to_datetime(d["game_date"]).dt.date.astype("datetime64[ns]")
    for c in ["game_pk", "at_bat_number", "pitch_number", "pitcher", "batter", "inning", "outs_when_up",
              "balls", "strikes"]:
        d[c] = pd.to_numeric(d[c], errors="coerce").astype("Int64")
    for c in ["on_1b", "on_2b", "on_3b"]:
        d[c] = d[c].notna()
    d = d.drop_duplicates(subset=KEY, keep="first")
    d = d.sort_values(["game_date", "game_pk", "at_bat_number", "pitch_number"]).reset_index(drop=True)
    d["is_swing"] = d["description"].isin(SWING_DESC)
    d["is_whiff"] = d["description"].isin(WHIFF_DESC)
    d["is_fastball"] = d["pitch_type"].isin(FASTBALL)
    # out-of-zone = Statcast zones 11-14; chase = swing at an out-of-zone pitch
    z = pd.to_numeric(d["zone"], errors="coerce")
    d["out_of_zone"] = z >= 11
    d["in_zone"] = (z >= 1) & (z <= 9)
    return d


def plate_appearances(p: pd.DataFrame) -> pd.DataFrame:
    """One row per PA = the last pitch of the at-bat (the row carrying `events`)."""
    last = p[p["events"].notna()].drop_duplicates(["game_pk", "at_bat_number"], keep="last")
    cols = ["game_pk", "game_date", "at_bat_number", "pitcher", "batter", "p_throws", "stand", "home_team",
            "away_team", "inning", "inning_topbot", "events", "bb_type", "launch_speed", "launch_angle",
            "woba_value", "woba_denom", "estimated_woba_using_speedangle"]
    return last[cols].reset_index(drop=True)


def games(p: pd.DataFrame) -> pd.DataFrame:
    """One row per game: final score from the last pitch's post_* scores; starters; lineups (first 9 batters)."""
    g = p.sort_values(["game_pk", "at_bat_number", "pitch_number"])
    last = g.groupby("game_pk").tail(1).set_index("game_pk")
    first = g.groupby("game_pk").head(1).set_index("game_pk")
    out = pd.DataFrame({
        "game_date": first["game_date"],
        "home_team": first["home_team"],
        "away_team": first["away_team"],
        "home_runs": pd.to_numeric(last["post_home_score"], errors="coerce"),
        "away_runs": pd.to_numeric(last["post_away_score"], errors="coerce"),
        "n_pitches": g.groupby("game_pk").size(),
    })
    # starters: pitcher on the first pitch of each team's defensive half in inning 1
    inn1 = g[g["inning"] == 1]
    top = inn1[inn1["inning_topbot"] == "Top"].groupby("game_pk")["pitcher"].first()  # home pitches in the Top
    bot = inn1[inn1["inning_topbot"] == "Bot"].groupby("game_pk")["pitcher"].first()
    out["home_starter"] = top
    out["away_starter"] = bot
    return out.reset_index()


def lineups(p: pd.DataFrame) -> pd.DataFrame:
    """First nine distinct batters per team per game, in order of first appearance."""
    b = p.drop_duplicates(["game_pk", "at_bat_number"])[["game_pk", "at_bat_number", "batter", "inning_topbot"]]
    b = b.sort_values(["game_pk", "at_bat_number"])
    b["team_side"] = np.where(b["inning_topbot"] == "Top", "away", "home")
    b = b.drop_duplicates(["game_pk", "team_side", "batter"], keep="first")
    b["slot"] = b.groupby(["game_pk", "team_side"]).cumcount() + 1
    return b[b["slot"] <= 9][["game_pk", "team_side", "slot", "batter"]].reset_index(drop=True)


def build_store(store: Path, years: Iterable[int]) -> dict:
    """Raw -> tables/{pitches,pa,games,lineups}.parquet. Returns row counts."""
    p = clean_pitches(load_raw(store, years))
    out = Path(store) / "tables"
    out.mkdir(parents=True, exist_ok=True)
    pa, g, lu = plate_appearances(p), games(p), lineups(p)
    p.to_parquet(out / "pitches.parquet", index=False)
    pa.to_parquet(out / "pa.parquet", index=False)
    g.to_parquet(out / "games.parquet", index=False)
    lu.to_parquet(out / "lineups.parquet", index=False)
    return {"pitches": len(p), "pa": len(pa), "games": len(g), "lineups": len(lu)}
