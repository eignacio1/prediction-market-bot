"""W88.3 Part A (NHL): frozen nhl_pregame_v1 home-win probabilities for the held-out 2025-26 regular season.
Same feature store and model file the live runner uses (NhlFeatureStore, models/nhl_pregame_v1.json, unchanged), as of
game start - 1h, the band's decision time. Reads the box's raw boxscores read-only; writes one JSON of per-game rows.
usage: nhl_model_side.py <repo_root> <boxscore_dir> [season=2025] > out.json  (JSON to stdout)"""
from __future__ import annotations

import json
import sys
from datetime import timedelta
from pathlib import Path

repo, box_dir = Path(sys.argv[1]), Path(sys.argv[2])
season = int(sys.argv[3]) if len(sys.argv) > 3 else 2025
sys.path.insert(0, str(repo / "src"))
from prediction_market_bot.c1_signal_ingestion import nhl_ingest as ni  # noqa: E402
from prediction_market_bot.c2_feature_store.nhl_features import NhlFeatureStore, parse_ts  # noqa: E402
from prediction_market_bot.c3_forecasting import nhl_pregame as m  # noqa: E402

games = []
for p in sorted(box_dir.glob("*.json")):
    raw = json.loads(p.read_text())
    row = ni.parse_game_row(raw["payload"], raw["fetched_at_utc"])
    if row:
        games.append(row)
model, sha = m.load_model(repo / "models/nhl_pregame_v1.json")
store = NhlFeatureStore(games)
rows = []
for g in games:
    if int(str(g["season"])[:4]) != season:
        continue
    st = parse_ts(g["start_time_utc"])
    p = model.ladder(store.game_features(g["home"], g["away"], st, st - timedelta(hours=1))).p_home_win()
    rows.append({"game_id": g["game_id"], "game_date": g["game_date"], "start_time_utc": g["start_time_utc"],
                 "home": g["home"], "away": g["away"], "p_model": p, "y": int(g["home_score"] > g["away_score"])})
sys.stdout.write(json.dumps({"model_sha256": sha, "season": season, "n_games_loaded": len(games), "rows": rows}))
print(len(games), "games loaded;", len(rows), "predicted;", sha[:12], file=sys.stderr)
