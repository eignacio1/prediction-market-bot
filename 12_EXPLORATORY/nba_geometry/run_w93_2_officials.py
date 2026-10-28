#!/usr/bin/env python3
"""W93.2 Part B: NBA officials (crew tendencies, point-in-time) - does it move the game total beyond B1 + B9 + B2 + prior carry?

Same protocol and seed family as run_w93_2.py (train 2017-2024, test 2025 and 2026, regular season, paired MSE gain, 1000-rep
bootstrap over test games, moves = 95% CI excludes 0). Crew features are the shrunk (K=30) prior-games-only deviations of fouls,
FTA and pace from nba_officials.official_rates. Also reports whether the crew's fouls deviation predicts the game's own fouls and FTA.
Usage: run_w93_2_officials.py [NBA_EVENTS root] [out json]
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import run_w93_2 as A  # noqa: E402
from prediction_market_bot.c1_signal_ingestion.nba_officials import SHRINK_K, game_quantities, official_rates  # noqa: E402
from _fence import safe_out  # noqa: E402


def main(root: Path, out: Path):
    np.random.seed(0)
    g, tg = A.build_frame(root)
    box, off = A.rd(root, "team_box"), A.rd(root, "officials")
    q = game_quantities(box)
    gm = tg.groupby("game_id").agg(date=("date", "first"), pace=("pace", "mean"))
    games = gm.join(q[["fouls", "fta"]], how="inner")
    rates = official_rates(off[["game_id", "official_id"]], games)
    g = g.merge(rates, left_on="game_id", right_index=True, how="left").merge(q[["fouls", "fta"]], left_on="game_id", right_index=True, how="left")
    g["crew_known"] = g["crew_n"].fillna(0) >= 20  # every official in the crew has >= 20 earlier games
    res = {"frame_games": int(len(g)), "k": SHRINK_K, "crew_known_games": int(g.crew_known.sum())}
    gk = g[g.crew_known].dropna(subset=["base_margin", "base_total", "crew_dev_fouls"])
    bt = ["base_total", "pace_mean", "eff_mean", "pace_dev_mean", "b2b_sum", "prior_total_mean", "prior_pace_mean"]
    specs = {
        "total | crew fouls+fta+pace deviation over baseline + prior": (bt, ["crew_dev_fouls", "crew_dev_fta", "crew_dev_pace"], "total"),
        "total | crew FTA deviation only": (bt, ["crew_dev_fta"], "total"),
        "total | crew fouls deviation only": (bt, ["crew_dev_fouls"], "total"),
        "total | crew pace deviation only": (bt, ["crew_dev_pace"], "total"),
        "fta | crew FTA deviation over baseline + prior": (bt, ["crew_dev_fta"], "fta"),
        "fouls | crew fouls deviation over baseline + prior": (bt, ["crew_dev_fouls"], "fouls"),
        "margin | crew deviations over baseline (control)": (["base_margin", "net_dev_diff", "rest_diff", "b2b_diff", "prior_margin"],
                                                           ["crew_dev_fouls", "crew_dev_fta", "crew_dev_pace"], "margin"),
    }
    res["gain"] = {}
    for name, (b, e, t) in specs.items():
        r = {str(ts): A.gain(gk, b, e, t, [ts]) for ts in A.TESTS}
        r["pooled_2025_26"] = A.gain(gk, b, e, t, list(A.TESTS))
        res["gain"][name] = r
        print(name, {k: (round(v["gain"], 3), [round(x, 3) for x in v["gain_ci"]], v["n_test"]) for k, v in r.items()}, flush=True)
    # split: games whose crew sits in the top / bottom decile of FTA deviation (training-window cut-offs not needed: descriptive)
    d = gk.dropna(subset=["crew_dev_fta"])
    lo, hi = d.crew_dev_fta.quantile(0.1), d.crew_dev_fta.quantile(0.9)
    res["descriptive"] = {
        "league_total": A.boot_mean(d.total), "fta_top_decile_total": A.boot_mean(d[d.crew_dev_fta >= hi].total),
        "fta_bottom_decile_total": A.boot_mean(d[d.crew_dev_fta <= lo].total),
        "fta_top_decile_fta": A.boot_mean(d[d.crew_dev_fta >= hi].fta), "fta_bottom_decile_fta": A.boot_mean(d[d.crew_dev_fta <= lo].fta),
        "crew_dev_fta_sd": float(d.crew_dev_fta.std()), "crew_dev_fouls_sd": float(d.crew_dev_fouls.std()),
    }
    print(json.dumps(res["descriptive"], indent=1, default=float))
    safe_out(out).write_text(json.dumps(res, indent=2, default=float))


if __name__ == "__main__":
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else A.REPO / "exp_output" / "NBA_EVENTS"
    out = Path(sys.argv[2]) if len(sys.argv) > 2 else HERE / "results_W93_2_officials.json"
    main(root, out)
