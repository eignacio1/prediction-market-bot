"""W88.3 Part A (MLB): frozen mlb_game_pregame_v1 home-win probabilities for the held-out 2025 regular season.
Same feature builder and model file the live runner uses (MLBGameFeatureBuilder, models/mlb_game_pregame_v1.json,
unchanged), as of game start - 1h. Inputs: the Stats API schedule snapshot (box: exp_output/MLB_GAME/cache_w47/games.parquet).
Caveat: the snapshot's home_sp/away_sp are the starters recorded after the fact, so the starter feature is the
confirmed starter, as in the live runner once starters post; a late scratch is not modelled.
usage: mlb_model_side.py <repo_root> <games.parquet> [season=2025] > out.json  (JSON to stdout)"""
from __future__ import annotations

import json
import sys
from datetime import timedelta
from pathlib import Path

import pandas as pd

repo, games_path = Path(sys.argv[1]), Path(sys.argv[2])
season = int(sys.argv[3]) if len(sys.argv) > 3 else 2025
sys.path.insert(0, str(repo / "src"))
from prediction_market_bot.c1_signal_ingestion.mlb_game_pregame_features import MLBGameFeatureBuilder, canon  # noqa: E402
from prediction_market_bot.pregame_shadow.mlb_model import MLBPregameModel, p_yes_for  # noqa: E402

games = pd.read_parquet(games_path)
model = MLBPregameModel.load(repo / "models/mlb_game_pregame_v1.json")
builder = MLBGameFeatureBuilder(games)
sel = games[(games.season == season) & (games.game_type == "R") & (games.status == "Final")
            & games.home_score.notna() & games.away_score.notna() & games.start_utc.notna()]
rows, skipped = [], 0
for r in sel.itertuples():
    st = pd.Timestamp(r.start_utc).to_pydatetime()
    f = builder.row(r.home, r.away, st - timedelta(hours=1),
                    None if pd.isna(r.home_sp) else int(r.home_sp), None if pd.isna(r.away_sp) else int(r.away_sp))
    if f is None or float(r.home_score) == float(r.away_score):
        skipped += 1
        continue
    p = min(max(p_yes_for(model, f["features"], "MLB_MONEYLINE", subject_is_home=True), 1e-4), 1 - 1e-4)
    rows.append({"game_id": int(r.game_pk), "game_date": r.game_date, "start_time_utc": r.start_utc,
                 "home": canon(r.home), "away": canon(r.away), "p_model": p, "y": int(r.home_score > r.away_score),
                 "sp_known": f["sp_known"]})
sys.stdout.write(json.dumps({"model_sha256": model.sha256, "season": season, "n_games_in_season": len(sel), "skipped": skipped, "rows": rows}))
print(len(sel), "season games;", len(rows), "predicted;", skipped, "skipped;", model.sha256[:12], file=sys.stderr)
