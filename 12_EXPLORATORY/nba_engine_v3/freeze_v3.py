"""W97.1 Part A: fit the v3 all-factor parameters once (seasons 2024-2026, K=10, lead-60 factors) and write the hashed frozen artifact.

Inputs: w97/v3_factors_lead60.parquet + w97/snapshot_2027.json (build_frozen_v3.py). Output: frozen/v3_frozen_2027.json, read by
src/prediction_market_bot/nba_engine/live_v3.py. Params fit exactly as study_v3.train_variant does for the v3_all variant.
Run: PYTHONPATH=src python3 12_EXPLORATORY/nba_engine_v3/freeze_v3.py <NBA_EVENTS raw dir>
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "nba_board"))
import study_v3 as S  # noqa: E402
import study_a as SA  # noqa: E402
from _fence import safe_out  # noqa: E402
from prediction_market_bot.nba_engine import engine_v2 as V, ratings as R  # noqa: E402

TRAIN = (2024, 2025, 2026)
K = 10.0


def main(raw: str):
    F = pd.read_parquet(HERE / "w97" / "v3_factors_lead60.parquet")
    F = F[F.season >= 2023].dropna(subset=S.COLS)
    tg = SA.load(raw)
    tg = tg[tg["season_type"] == "regular-season"]
    g = R.game_inputs(R.add_ratings(tg[tg.season <= max(TRAIN)], k=K))
    g = g[g.index.astype(str).isin(F.index) & g.season.isin(TRAIN)]
    p, c = S.train_variant(g, F, S.VARIANTS["v3_all"])
    snap = json.loads((HERE / "w97" / "snapshot_2027.json").read_text())
    art = dict(
        version="v3", K=K, train_seasons=list(TRAIN), lead_min=60, n_train_games=int(len(g)),
        params=dict(hca=p.hca, tbias=p.tbias, sd_margin=p.sd_margin, sd_total=p.sd_total,
                    shift_margin=p.shift_margin, shift_total=p.shift_total, platt={f: list(v) for f, v in p.platt.items()}),
        centers=c.mean, factors=list(S.VARIANTS["v3_all"]),
        rates=snap["rates"], rotation=snap["rotation"], abbr=snap["abbr"],
        snapshot_note="rotation = each team's last 10 completed 2025-26 games; ratings as of 2027 start; NOT updated in season",
    )
    body = json.dumps(art, sort_keys=True, indent=1)
    art["sha256"] = hashlib.sha256(body.encode()).hexdigest()
    out = safe_out(HERE / "frozen" / "v3_frozen_2027.json")
    out.write_text(json.dumps(art, sort_keys=True, indent=1))
    print("frozen", out, art["sha256"][:16], art["n_train_games"], p.shift_margin, p.shift_total, c.mean)


if __name__ == "__main__":
    main(sys.argv[1])
