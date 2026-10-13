"""Freeze models/nba_player_points_minutes_v1.json (EXP-040). Offline only (Hard Rule 4); run ONCE.
Recipe is the W69.3 plan's: ridge lambda 100 on 2023-24, NB dispersion MLE + pooled-strike Platt on 2025. No 2026 data."""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
STUDY = ROOT / "12_EXPLORATORY" / "20261012_nba_points_minutes"
sys.path.insert(0, str(ROOT / "src")); sys.path.insert(0, str(ROOT / "scripts")); sys.path.insert(0, str(STUDY))
import features as F  # noqa: E402
from train_nba_player_points import LAMBDA, STRIKES, arr, nb_loglik, platt, ridge  # noqa: E402
from prediction_market_bot.pregame_shadow.nba_player_points_model import logit, nb_sf  # noqa: E402
from prediction_market_bot.pregame_shadow.nfl_model import canonical_sha  # noqa: E402


def main(raw: str, inj: str, out: str) -> None:
    keys = F.ARMS["minutes_inj"]
    rows = [r for r in F.build_frame(Path(raw), inj, seasons=(2023, 2024, 2025)) if r["season"] <= 2025]
    tr = [r for r in rows if r["season"] in (2023, 2024)]
    ca = [r for r in rows if r["season"] == 2025]
    b0, w, mu, sd = ridge(arr(tr, keys), np.array([r["points"] for r in tr], float))
    mean = lambda rs: np.maximum(b0 + ((arr(rs, keys) - mu) / sd) @ w, 0.5)  # noqa: E731
    mc, yc = mean(ca), np.array([r["points"] for r in ca], float)
    grid = np.exp(np.linspace(math.log(0.5), math.log(200), 60))
    r_hat = float(grid[int(np.argmax([nb_loglik(yc, mc, r) for r in grid]))])
    xs, ys = [], []
    for k in STRIKES:
        xs += [logit(nb_sf(k, m, r_hat)) for m in mc]
        ys += [1.0 if p >= k else 0.0 for p in yc]
    a, b = platt(np.array(xs), np.array(ys))
    art = {"model_id": "nba_player_points_minutes_v1", "experiment": "EXP-040", "feature_names": keys,
           "lambda": LAMBDA, "train_seasons": [2023, 2024], "cal_season": 2025, "registered_strikes": [15],
           "mean_model": {"intercept": b0, "coef": w.tolist(), "mean": mu.tolist(), "std": sd.tolist()},
           "dispersion_r": r_hat, "platt": {"a": a, "b": b}, "n_train": len(tr), "n_cal": len(ca)}
    art["sha256"] = canonical_sha(art)
    Path(out).write_text(json.dumps(art, indent=1, sort_keys=True))
    print(art["sha256"], r_hat, a, b, len(tr), len(ca))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else str(ROOT / "models" / "nba_player_points_minutes_v1.json"))
