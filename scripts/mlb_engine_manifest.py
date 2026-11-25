#!/usr/bin/env python3
"""W127.2: per-season integrity manifest of the local MLB pitch store (D4 data layer for MLB).

usage: python3 scripts/mlb_engine_manifest.py [store_root=~/mlb_store] [out=02_ARCHITECTURE_DESIGN/MLB_ENGINE/event_store_manifest.json]
Offline: every check is store-internal (no box-score fetch): duplicate pitches, per-game pitch count vs games.n_pitches,
nine-man lineups both sides, starters present, PA rows per game. Reads only; writes the one JSON."""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd


def build(store: Path) -> dict:
    t = {n: pd.read_parquet(store / "tables" / f"{n}.parquet") for n in ("games", "pitches", "pa", "lineups")}
    g, p, pa, lu = t["games"], t["pitches"], t["pa"], t["lineups"]
    g = g.assign(season=pd.to_datetime(g.game_date).dt.year)
    p = p.assign(season=pd.to_datetime(p.game_date).dt.year)
    pa = pa.assign(season=pd.to_datetime(pa.game_date).dt.year)
    per_game = p.groupby("game_pk").size()
    full = lu[lu.slot.between(1, 9)].groupby(["game_pk", "team_side"]).size().unstack().reindex(columns=["away", "home"]).eq(9).all(axis=1)
    out = {}
    for s, gs in g.groupby("season"):
        ps, pas = p[p.season == s], pa[pa.season == s]
        pk = set(gs.game_pk)
        got = per_game.reindex(list(pk)).fillna(0)
        exp = gs.set_index("game_pk").n_pitches
        match = float((got.reindex(exp.index) == exp).mean()) if len(exp) else None
        out[str(int(s))] = {
            "games": int(len(gs)), "pitches": int(len(ps)), "plate_appearances": int(len(pas)),
            "first_date": str(gs.game_date.min())[:10], "last_date": str(gs.game_date.max())[:10],
            "dup_pitches": int(ps.duplicated(["game_pk", "at_bat_number", "pitch_number"]).sum()),
            "dup_pa": int(pas.duplicated(["game_pk", "at_bat_number"]).sum()),
            "pitch_count_vs_games_n_pitches": match,
            "games_with_both_starters": float((gs.home_starter.notna() & gs.away_starter.notna()).mean()),
            "games_with_full_lineups": float(pd.Series(list(pk)).isin(full[full].index).mean()),
            "games_with_pitches": float(len(set(ps.game_pk) & pk) / max(len(pk), 1)),
        }
    return {"built_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "source": "baseballsavant.mlb.com statcast csv (public, unauthenticated GETs) via mlb_engine/fetch.py",
            "contract": "src/prediction_market_bot/mlb_engine/pit.py", "failures": [], "seasons": out}


if __name__ == "__main__":
    store = Path(sys.argv[1] if len(sys.argv) > 1 else "~/mlb_store").expanduser()
    dest = Path(sys.argv[2] if len(sys.argv) > 2 else "02_ARCHITECTURE_DESIGN/MLB_ENGINE/event_store_manifest.json")
    m = build(store)
    dest.write_text(json.dumps(m, indent=1) + "\n")
    for s, v in m["seasons"].items():
        print(s, v["games"], v["pitches"], v["plate_appearances"], "dup", v["dup_pitches"], "pitch_match", v["pitch_count_vs_games_n_pitches"], "lineups", round(v["games_with_full_lineups"], 3))
