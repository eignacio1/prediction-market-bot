"""W69.3 evaluation. Run ONCE after the README plan commit. Writes results.json via _fence.safe_out()."""
from __future__ import annotations

import json
import math
import os
import sys
from pathlib import Path

import numpy as np

HERE = os.path.dirname(__file__)
ROOT = Path(HERE).resolve().parents[1]
sys.path.insert(0, HERE)
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "12_EXPLORATORY"))
import features as F  # noqa: E402
from train_nba_player_points import STRIKES, nb_loglik, platt, ridge  # noqa: E402
from prediction_market_bot.pregame_shadow.nba_player_points_model import NBAPlayerPointsModel, logit, nb_sf  # noqa: E402

B, SEED, M = 20000, 20261012, 8
ALPHA = 0.05 / M
FOLDS = {"A": ((2023,), 2024, 2025), "B": ((2023, 2024), 2025, 2026)}


def fit_predict(rows, keys, tr, ca, te):
    R = lambda ss: [r for r in rows if r["season"] in ss]  # noqa: E731
    trr, car, ter = R(tr), R((ca,)), R((te,))
    X = lambda rs: np.array([[r[k] for k in keys] for r in rs], float)  # noqa: E731
    y = lambda rs: np.array([r["points"] for r in rs], float)  # noqa: E731
    b0, w, mu, sd = ridge(X(trr), y(trr))
    mean = lambda rs: np.maximum(b0 + ((X(rs) - mu) / sd) @ w, 0.5)  # noqa: E731
    mc, yc = mean(car), y(car)
    grid = np.exp(np.linspace(math.log(0.5), math.log(200), 60))
    r_hat = float(grid[int(np.argmax([nb_loglik(yc, mc, r) for r in grid]))])
    xs, ys = [], []
    for k in STRIKES:
        xs += [logit(nb_sf(k, m, r_hat)) for m in mc]
        ys += [1.0 if p >= k else 0.0 for p in yc]
    a, bb = platt(np.array(xs), np.array(ys))
    mt = mean(ter)
    P = {k: 1 / (1 + np.exp(-(a * np.array([logit(nb_sf(k, m, r_hat)) for m in mt]) + bb))) for k in STRIKES}
    return ter, P, {"r": r_hat, "platt": [a, bb], "n_tr": len(trr), "n_ca": len(car), "n_te": len(ter),
                    "rmse": float(np.sqrt(np.mean((mt - y(ter)) ** 2)))}


def boot_ci(d, gid, rng):
    ug, inv = np.unique(gid, return_inverse=True)
    S = np.bincount(inv, weights=d); N = np.bincount(inv).astype(float)
    G = len(ug); bs = np.empty(B)
    for i in range(0, B, 500):
        idx = rng.integers(0, G, size=(min(500, B - i), G))
        bs[i:i + len(idx)] = S[idx].sum(1) / N[idx].sum(1)
    q = lambda a: float(np.quantile(bs, a))  # noqa: E731
    return {"delta": float(d.mean()), "ci95": [q(.025), q(.975)], "ci_corrected": [q(ALPHA / 2), q(1 - ALPHA / 2)],
            "n": int(len(d)), "n_games": int(G)}


def main():
    raw = Path(sys.argv[1]); inj = sys.argv[2]
    rows = F.build_frame(raw, inj)
    cov = {s: {"with_report": a, "without": b} for s, (a, b) in F.build_frame.coverage.items()}
    out = {"m": M, "alpha": ALPHA, "B": B, "seed": SEED, "coverage_games": cov, "folds": {}, "frozen_check": {}}
    preds = {}
    for fold, (tr, ca, te) in FOLDS.items():
        for arm, keys in F.ARMS.items():
            ter, P, info = fit_predict(rows, keys, tr, ca, te)
            preds[(fold, arm)] = (ter, P)
            out["folds"][f"{fold}:{arm}"] = info
    rng = np.random.default_rng(SEED)
    res = {}
    for arm in ("minutes_box", "minutes_inj"):
        for sub in ("all", "star"):
            for k in STRIKES:
                d, g, s = [], [], []
                for fold in FOLDS:
                    ter, Pc = preds[(fold, "ctrl_refit")]
                    _, Pa = preds[(fold, arm)]
                    ysel = np.array([1.0 if r["points"] >= k else 0.0 for r in ter])
                    m = np.array([sub == "all" or r["pts10"] >= 15 for r in ter])
                    dd = (Pa[k] - ysel) ** 2 - (Pc[k] - ysel) ** 2
                    d.append(dd[m]); g += [r["game_id"] for r, mm in zip(ter, m) if mm]
                    s.append(float(dd[m].mean()))
                dall = np.concatenate(d)
                e = boot_ci(dall, np.array(g), rng)
                e["delta_by_test_season"] = {"2025": s[0], "2026": s[1]}
                res[f"{arm}|{sub}|{k}"] = e
    out["delta_brier_vs_ctrl_refit"] = res
    # actual frozen artifact vs ctrl_refit on the 2026 fold
    mod = NBAPlayerPointsModel.load(str(ROOT / "models" / "nba_player_points_v1.json"))
    ter, Pc = preds[("B", "ctrl_refit")]
    for k in STRIKES:
        y = np.array([1.0 if r["points"] >= k else 0.0 for r in ter])
        pf = np.array([mod.p_at_least(r, k) for r in ter])
        out["frozen_check"][str(k)] = {"brier_frozen": float(np.mean((pf - y) ** 2)),
                                       "brier_ctrl_refit": float(np.mean((Pc[k] - y) ** 2))}
    try:
        from _fence import safe_out
        dest = safe_out(Path(HERE) / "results.json")
    except Exception:
        dest = Path(HERE) / "results.json"
    Path(dest).write_text(json.dumps(out, indent=1))
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
