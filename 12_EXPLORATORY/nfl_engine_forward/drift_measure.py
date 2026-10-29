"""EXPLORATORY -- W94.2 Part B: which NFL team-game factors drift inside a season (temporal_evolution scaffold).

Reads nflverse play_by_play_<year>.parquet (free, public) from --pbp-dir; writes drift_W94_2.json beside this file.
Regular season, 2016-2025 (2026 is a partial season and excluded). Nothing here is wired to an order or model.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _fence import safe_out

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from prediction_market_bot.nfl_engine import temporal_evolution as te  # noqa: E402

COLS = ["game_id", "season", "week", "season_type", "posteam", "defteam", "play_type", "epa", "success",
        "down", "wp", "qtr", "half_seconds_remaining"]


def team_games(pbp_dir: Path, seasons: range) -> dict[str, pd.DataFrame]:
    p = pd.concat([pd.read_parquet(pbp_dir / f"play_by_play_{s}.parquet", columns=COLS) for s in seasons])
    p = p[(p.season_type == "REG") & p.play_type.isin(["pass", "run"]) & p.epa.notna() & p.posteam.notna()]
    neutral = p[p.down.isin([1, 2]) & p.wp.between(0.2, 0.8) & ~((p.qtr == 2) & (p.half_seconds_remaining < 120))]
    key = ["season", "week", "game_id"]

    def tab(g, team_col, col, fn) -> pd.DataFrame:
        r = g.groupby(key + [team_col]).apply(fn, include_groups=False).reset_index(name="v")
        return r.assign(team=r[team_col]).drop(columns=[team_col])

    return {
        "off_epa_per_play": tab(p, "posteam", "epa", lambda x: x.epa.mean()),
        "off_success_rate": tab(p, "posteam", "success", lambda x: x.success.mean()),
        "neutral_pass_rate": tab(neutral, "posteam", "play_type", lambda x: (x.play_type == "pass").mean()),
        "plays_per_game": tab(p, "posteam", "epa", lambda x: float(len(x))),
        "def_epa_per_play_allowed": tab(p, "defteam", "epa", lambda x: x.epa.mean()),
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pbp-dir", required=True)
    ap.add_argument("--out", default=str(Path(__file__).with_name("drift_W94_2.json")))
    a = ap.parse_args()
    res = {}
    for name, d in team_games(Path(a.pbp_dir), range(2016, 2026)).items():
        sl, rg = te.within_season_slope(d), te.reliability_gap(d)
        res[name] = {"n_team_games": int(len(d)), "league_mean": float(d.v.mean()), "sd": float(d.v.std()),
                     "slope": {k: v for k, v in sl.items() if k != "per_season"},
                     "slope_per_season": sl["per_season"], "reliability": rg,
                     "blend": te.blend_weight_by_week(d)}
        print(name, json.dumps({"slope": res[name]["slope"], "rel": rg}, default=float))
    safe_out(a.out).write_text(json.dumps(res, indent=1, default=float))


if __name__ == "__main__":
    main()
