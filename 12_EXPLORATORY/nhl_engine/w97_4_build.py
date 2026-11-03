"""W97.4 Part A on real data: build the point-in-time per-game feature frame from the compiled NHL event store.

Exploratory; reads the store, writes one parquet under the path given. Seasons 2021-2026 (2021 is the xG burn-in).
Usage: python3 w97_4_build.py <store_root> <out_parquet>
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from prediction_market_bot.nhl_engine import inputs as I  # noqa: E402

SEASONS = [2021, 2022, 2023, 2024, 2025, 2026]
XG_FIRST = 2022


def main(root: str, out: str) -> None:
    rd = lambda n: pd.concat([pd.read_parquet(Path(root) / f"{n}_{s}.parquet") for s in SEASONS], ignore_index=True)
    g, ev, bx = rd("games"), rd("events"), rd("box_players")
    g = g[g["game_type"].isin([2, 3]) & g["game_state"].isin(["OFF", "FINAL"])].copy()
    g["game_id"] = g["game_id"].astype("int64")
    ev = ev[ev["game_id"].isin(g["game_id"])]
    sx = I.xg_by_season(I.shots(ev), XG_FIRST)
    g = g[g["season"] >= XG_FIRST]
    sx = sx[sx["game_id"].isin(g["game_id"])]
    tg = I.team_game_table(g, sx, ev[ev["game_id"].isin(g["game_id"])])
    gs = I.previous_starter_gsax(g, bx, sx)
    fr = I.game_features(tg, gs)
    meta = g[["game_id", "game_type", "start_time_utc", "game_date_et", "home", "away", "home_score", "away_score", "last_period_type"]]
    fr = fr.merge(meta, on="game_id", how="left")
    reg = tg[["game_id", "is_home", "reg_goals"]].pivot(index="game_id", columns="is_home", values="reg_goals")
    fr = fr.merge(reg.rename(columns={True: "reg_h", False: "reg_a"}).reset_index(), on="game_id", how="left")
    fr.to_parquet(out)
    print(fr.shape, fr["season"].value_counts().sort_index().to_dict())


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
