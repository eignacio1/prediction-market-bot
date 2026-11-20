"""W122.1: walk-forward held-out calibration of the NBA engine's player-points price, by line.

For every game dated >= --start, price each rotation player's P(points >= n) from data strictly before the game
(the same NBAEngineProps path the shadow runner uses), compare with what happened. Read-only; no orders.
  PYTHONPATH=src python3 scripts/nba_points_calibration.py --box data/raw/nba_props/box.json [--start 2026-11-05]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
from prediction_market_bot.nba_engine import props as P  # noqa: E402
from prediction_market_bot.pregame_shadow import nba_engine_props_forecaster as F  # noqa: E402

LINES = (10, 15, 20, 25, 30)


def run(box: dict, start: str, end: str = "9999", rest: float = F.POINTS_REST) -> dict:
    games, pl = F.parse_box(box)
    fc = F.NBAEngineProps(games, pl, {})
    rows = []     # (line, p, hit, game_id)
    team_err = []
    for gid, g in games.items():
        if g["date"] < start or g["date"] >= end:
            continue
        for team in (g["home"], g["away"]):
            ros = fc.roster(team, g["date"])
            if len(ros) < 5:
                continue
            p = {"game_date": g["date"], "home": g["home"], "away": g["away"]}
            h, a = fc._game_draws(p)
            pts = h if team == g["home"] else a
            R = P.TeamRoster(tuple(n for _, n, _ in ros), {s: [r[2][s] for r in ros] for s in P.STATS}, float(pts.mean()))
            d, _ = P.player_draws(pts, R, "points", np.random.default_rng(1),
                                  rest={**P.DEFAULT_REST, "points": rest})
            team_err.append(float(pts.mean()) - g["pts"][team])
            actual = {r["name"]: r["points"] for r in g["teams"][team]}
            for i, (_, name, _) in enumerate(ros):
                if name not in actual:
                    continue
                pr = P.strike_probs(d[:, i], LINES)
                for n in LINES:
                    rows.append((n, min(max(pr[n], 1e-4), 1 - 1e-4), float(actual[name] >= n), gid))
    out = {"games": len({r[3] for r in rows}), "rows": len(rows), "team_pts_bias": float(np.mean(team_err)) if team_err else None,
           "by_line": {}}
    for n in LINES:
        x = [(p, h) for ln, p, h, _ in rows if ln == n]
        if x:
            p, h = np.array(x).T
            out["by_line"][n] = {"n": len(x), "mean_p": round(float(p.mean()), 4), "hit_rate": round(float(h.mean()), 4),
                                 "brier": round(float(((p - h) ** 2).mean()), 4),
                                 "brier_base_rate": round(float(((h.mean() - h) ** 2).mean()), 4)}
    allp = np.array([r[1] for r in rows]); allh = np.array([r[2] for r in rows])
    if len(allp):
        bins = np.clip((allp * 5).astype(int), 0, 4)
        out["reliability_5bin"] = [{"p_lo": b / 5, "n": int((bins == b).sum()), "mean_p": round(float(allp[bins == b].mean()), 3),
                                    "hit": round(float(allh[bins == b].mean()), 3)} for b in range(5) if (bins == b).any()]
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--box", required=True)
    ap.add_argument("--start", default="2026-11-08")
    ap.add_argument("--end", default="9999")
    ap.add_argument("--rest", type=float, default=F.POINTS_REST)
    a = ap.parse_args()
    print(json.dumps(run(json.load(open(a.box)), a.start, a.end, a.rest), indent=1))
