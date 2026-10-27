"""W88.3 Part A (NBA): frozen nba_pregame_v1 home-win probabilities for the 2025-26 regular season, as of start - 1h.
Same NBAFeatureBuilder + NBAPregameModel + artifact the live runner uses (models/nba_pregame_v1.json, unchanged).
History: the live 2025-26 store (data/raw/nba/games_2026.json, ESPN rows) plus 2024-25 regular-season rows from the box's
schedule parquet, whose only time-of-day is missing -- those rows get a 23:30Z start (evening ET); this moves only
rest/back-to-back counts for games early in 2025-26. `inseason_prior_min` (fewer of the two teams' completed 2025-26 games
before this one) lets the scorer drop rows whose windows touch that approximated history.
usage: nba_model_side.py <repo_root> <games_2026.json> <schedule_2025.parquet> > out.json  (JSON to stdout)"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

repo = Path(sys.argv[1])
sys.path.insert(0, str(repo / "src"))
import pandas as pd  # noqa: E402
from prediction_market_bot.c1_signal_ingestion.nba_ingest import ESPN_TO_KALSHI  # noqa: E402
from prediction_market_bot.c1_signal_ingestion.nba_pregame_features import NBAFeatureBuilder, _dt  # noqa: E402
from prediction_market_bot.pregame_shadow.nba_model import NBAPregameModel  # noqa: E402

live = [g for g in json.loads(Path(sys.argv[2]).read_text())["games"].values()]
hist = []
for r in pd.read_parquet(sys.argv[3]).itertuples():
    if r.season_type != "regular-season":
        continue
    h, a = ESPN_TO_KALSHI.get(r.home_team_abbreviation), ESPN_TO_KALSHI.get(r.away_team_abbreviation)
    if h is None or a is None:
        raise SystemExit(f"unmapped abbreviation {r.home_team_abbreviation}/{r.away_team_abbreviation}")
    hist.append({"game_id": "h" + r.game_id, "start_time_utc": f"{r.game_date}T23:30:00Z", "season": 2025, "season_type": 2,
                 "completed": True, "home": h, "away": a, "home_score": int(r.home_pts), "away_score": int(r.away_pts)})
model = NBAPregameModel.load(repo / "models/nba_pregame_v1.json")
builder = NBAFeatureBuilder(hist + live)
cur = sorted([g for g in live if g["season_type"] == 2 and g["completed"] and g["home_score"] is not None],
             key=lambda g: (g["start_time_utc"], g["game_id"]))
seen: dict[str, int] = {}
rows = []
for g in cur:
    st = _dt(g["start_time_utc"])
    n_prior = min(seen.get(g["home"], 0), seen.get(g["away"], 0))
    seen[g["home"]] = seen.get(g["home"], 0) + 1
    seen[g["away"]] = seen.get(g["away"], 0) + 1
    r = builder.row(g["home"], g["away"], st, st - timedelta(hours=1))
    if r is None:
        continue
    p = NBAPregameModel.p_home_win(model.distribution(r["features"]))
    rows.append({"game_id": g["game_id"], "start_time_utc": g["start_time_utc"], "home": g["home"], "away": g["away"],
                 "p_model": p, "y": int(g["home_score"] > g["away_score"]), "inseason_prior_min": n_prior})
sys.stdout.write(json.dumps({"model_sha256": model.sha256, "season": 2026, "n_live_completed_regular": len(cur),
                                         "rows": rows}))
print(len(cur), "completed regular-season games;", len(rows), "predicted;", model.sha256[:12], file=sys.stderr)
