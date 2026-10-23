"""W86.1 Part B(2): nfl_pregame_v1 2025 held-out Brier against the de-vigged nflverse close.

Usage: PYTHONPATH=src python3 heldout_nfl_vs_market.py <schedule.parquet> <team_stats.parquet> <games.parquet> <out.json>
Read-only on the frozen model. Ties excluded (as in training). Paired diff: positive = model better.
"""
import json
import sys
from datetime import datetime, timezone

import pandas as pd
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _fence import safe_out  # noqa: E402

sys.path.insert(0, "scripts")
from train_nfl_pregame import build_frame  # noqa: E402

from prediction_market_bot.pregame_shadow.nfl_model import NFLPregameModel  # noqa: E402
from prediction_market_bot.c1_signal_ingestion.nfl_pregame_features import FEATURE_NAMES  # noqa: E402
from prediction_market_bot.quant import scoring, inference  # noqa: E402


def ml_prob(ml):
    return 100.0 / (ml + 100.0) if ml > 0 else -ml / (-ml + 100.0)


def main(sched_p, stats_p, games_p, out_p):
    sched, stats = pd.read_parquet(sched_p), pd.read_parquet(stats_p)
    m = NFLPregameModel.load("models/nfl_pregame_v1.json")
    df = build_frame(sched, stats)
    df = df[(df.season == 2025) & (df.margin != 0)]
    g = pd.read_parquet(games_p).set_index("game_id")
    pm, pk, ys, gid = [], [], [], []
    for r in df.to_dict("records"):
        gm = g.loc[r["game_id"]]
        if pd.isna(gm.home_moneyline) or pd.isna(gm.away_moneyline):
            continue
        h, a = ml_prob(gm.home_moneyline), ml_prob(gm.away_moneyline)
        pk.append(h / (h + a))
        pm.append(NFLPregameModel.p_moneyline_home(m.distribution({n: r[n] for n in FEATURE_NAMES})))
        ys.append(1.0 if r["margin"] > 0 else 0.0)
        gid.append(r["game_id"])
    n = len(ys)
    d = [scoring.brier(pk[i], ys[i]) - scoring.brier(pm[i], ys[i]) for i in range(n)]
    ci = inference.cluster_bootstrap({gid[i]: [d[i]] for i in range(n)}, b=10000)
    out = {
        "model_id": "nfl_pregame_v1", "model_sha256": m.sha256, "market_source": "nflverse home/away_moneyline close, de-vigged by normalisation",
        "season": 2025, "market": "NFL moneyline (home win), REG, ties excluded", "n_games": n,
        "brier_model": scoring.brier_mean(pm, ys), "brier_market": scoring.brier_mean(pk, ys),
        "paired_brier_diff_market_minus_model": ci,
        "reading": "positive = model better than market",
        "timing_caveat": "GG-1090: nflverse close is at/near kickoff, later than the model's decision time (ko-36h/-24h/-6h anchor-vs-close SD 0.026/0.021/0.015 vs 0.010 at ko-30min). The comparison flatters the market.",
        "kalshi_note": "Kalshi KXNFLGAME candles cover only part of 2025 (415 of 862 markets, PARTIAL) and were not used.",
        "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    safe_out(Path(__file__).parent / Path(out_p).name).write_text(json.dumps(out, indent=1, default=str))  # lands inside 12_EXPLORATORY; copy to models/ by hand
    print(json.dumps(out, indent=1, default=str))


main(*sys.argv[1:5])
