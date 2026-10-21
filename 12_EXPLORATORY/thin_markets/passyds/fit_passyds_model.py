"""W81.3 fit + sanity gate for the KXNFLPASSYDS strike model (passyds_strike_v1).

Train: QB-games 2019-2023 (2018 is history only). Held out: 2024-2025. Nothing after 2025 is read.
Writes models/passyds_strike_v1.json (+ .sha256) and a sanity report. The sanity gate is reported, not a verdict:
Brier of P(over) on a synthetic strike ladder vs a naive QB same-season-average baseline."""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1]))
sys.path.insert(0, str(HERE.parents[2] / "src"))
from _fence import safe_out  # noqa: E402
from prediction_market_bot.pregame_shadow import passyds_model as pm  # noqa: E402

LADDER = (-50, -25, 0, 25, 50)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True, help="dir with w2018..w2025.parquet and sched.parquet")
    ap.add_argument("--models-dir", default="models")
    ap.add_argument("--report", default="12_EXPLORATORY/thin_markets/passyds/sanity_report.json")
    ap.add_argument("--write", action="store_true", help="write the frozen artifact (otherwise report only)")
    a = ap.parse_args()
    d = Path(a.data)
    ws = pd.concat([pd.read_parquet(d / f"w{y}.parquet") for y in range(2018, 2026)], ignore_index=True)
    ws = ws[ws["season_type"] == "REG"]
    sched = pd.read_parquet(d / "sched.parquet")
    sched = sched[sched["season"] <= 2025]
    qg, dg = pm.qb_games(ws, sched), pm.defense_games(ws, sched)

    art = pm.fit(qg, dg, pd.Timestamp("2024-01-01"), pd.Timestamp("2019-01-01"))
    model = pm.StrikeModel(art)

    briers_m, briers_b, rows = [], [], 0
    pooled_sd = float(qg.loc[qg["gameday"] < "2024-01-01", "passing_yards"].std())
    for r in qg[(qg["gameday"] >= "2024-01-01")].itertuples():
        pq, pd_ = pm.league_priors(qg, dg, r.gameday)
        f = pm.features_for(qg, dg, r.name_key, r.opponent_team, r.home, r.gameday, pq, pd_)
        if f is None:
            continue
        h = qg[(qg["name_key"] == r.name_key) & (qg["gameday"] < r.gameday)]
        cur = h[h["season"] == r.season]
        base = cur if len(cur) else h[h["season"] == r.season - 1]
        if len(base) == 0:
            continue
        mu0 = float(base["passing_yards"].mean())
        center = round(mu0 / 25.0) * 25
        for off in LADDER:
            k = center + off
            y = 1.0 if r.passing_yards >= k else 0.0
            pb = pm.baseline_p_ge(qg, r.name_key, r.gameday, r.season, k, pooled_sd, pq)
            briers_m.append((model.p_ge(f, k) - y) ** 2)
            briers_b.append((pb - y) ** 2)
        rows += 1
    out = {"model_id": "passyds_strike_v1", "train": "2019-2023 REG", "heldout": "2024-2025 REG", "coef": art["coef"],
           "sigma_c": art["sigma_c"], "n_train": art["n_train"], "heldout_qb_games": rows,
           "heldout_strike_rows": len(briers_m), "brier_model": float(np.mean(briers_m)),
           "brier_baseline": float(np.mean(briers_b)), "brier_delta_model_minus_baseline":
           float(np.mean(briers_m) - np.mean(briers_b)), "gate": "reported, not a verdict"}
    print(json.dumps(out, indent=2))
    safe_out(a.report).write_text(json.dumps(out, indent=2) + "\n")
    if a.write:
        print("frozen", pm.write_frozen(art, Path(a.models_dir)))


if __name__ == "__main__":
    main()
