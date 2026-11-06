"""W105.1 Part A: games needed to detect w=0.25/0.5 (80% power, one-sided 5%) per NBA engine x family.

READ-ONLY inputs (copied from the box to a scratch dir): NBA_ENGINE_LIVE{,_V2,_V3}.jsonl rows + ESPN finals.
usage: run_power_nba.py <rows_dir> <finals.json> <out.json under 12_EXPLORATORY/>
Per-row variance comes from the observed 104.2 rows (cluster = whole game); effect and sd are from the comonotone
simulation at weight w; n_max is the FINAL-look game count of a 4-look O'Brien-Fleming plan."""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent), str(HERE.parent / 'quant_w104_blend')]

from _fence import safe_out  # noqa: E402
from run_blend_nba import ENGINES, FAMS, final_for, load_finals
from prediction_market_bot.nba_engine.live_scoring import outcome
from prediction_market_bot.quant import blend_power as bp

FRACS = [0.25, 0.5, 0.75, 1.0]


def main(rows_dir, finals_path, out_path):
    finals = load_finals(finals_path)
    n_finals = sum(len(v) for v in finals.values())
    cells = []
    for eng, d in ENGINES.items():
        rows = [json.loads(l) for l in open(Path(rows_dir) / f"{d}.jsonl")]
        for fam in FAMS:
            data = []
            for r in rows:
                if r["family"] != fam or r.get("p_market") is None or r.get("p_engine") is None:
                    continue
                f = final_for(r, finals)
                if f is None:
                    continue
                y = outcome(r, f)
                if y is None:
                    continue
                data.append(((r["game_date"], r["home"], r["away"]), r["p_market"], r["p_engine"], float(y)))
            gs = bp.game_scores(data)
            cell = {"engine": eng, "family": fam, "n_games": len(gs), "n_rows": sum(v[2] for v in gs.values()),
                    "coverage_of_finals": round(len(gs) / n_finals, 3),
                    "w_score_hat": bp.w_score_estimate(gs)}
            for w in (0.25, 0.5):
                e = bp.effect_and_sd(data, w, reps=300)
                g = bp.gs_games_needed(e["mu"], e["sigma"], FRACS)
                cell[f"w{w}"] = {"mu": e["mu"], "sigma": e["sigma"], "n_fixed": g["n_fixed"], "n_max": g["n_max"],
                                 "inflation": g["inflation"]}
            cells.append(cell)
    json.dump({"fracs": FRACS, "alpha": 0.05, "power": 0.8, "n_finals": n_finals, "cells": cells},
              open(safe_out(out_path), "w"), indent=1)
    for c in cells:
        print(c["engine"], c["family"], c["n_games"], c["coverage_of_finals"],
              round(c["w0.25"]["n_max"]), round(c["w0.5"]["n_max"]), c["w_score_hat"])


if __name__ == "__main__":
    main(*sys.argv[1:4])
