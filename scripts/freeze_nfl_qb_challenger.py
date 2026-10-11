"""Freeze models/nfl_qb_challenger_v1.json (W65.3). Offline, run ONCE; the artifact is then immutable (Hard Rule 4).

Recipe = the W64.1 study's rolling-origin recipe for the first live test season (2026): ridge lambda=100 on
seasons 2015..2024, sigma = std(ddof=1) of 2025 calibration residuals, probit-Platt on 2025 non-tie rows.
Features come from the SAME live code path the runner uses (NFLQBFeatureBuilder), as_of = 00:00 UTC on gameday.
Writes the artifact plus a metadata sidecar (artifact sha256, input data sha256, code sha, row counts).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from prediction_market_bot.c1_signal_ingestion.nfl_qb_features import CHALLENGER_FEATURE_NAMES, NFLQBFeatureBuilder  # noqa: E402
from prediction_market_bot.pregame_shadow.nfl_model import _phi, canonical_sha  # noqa: E402

LAMBDA = 100.0
TRAIN_LAST, CAL = 2024, 2025
FIRST = 2015


def build_frame(sched: pd.DataFrame, stats: pd.DataFrame) -> pd.DataFrame:
    fb = NFLQBFeatureBuilder(stats, sched)
    reg = sched[(sched.game_type == "REG") & sched.home_score.notna() & (sched.season >= FIRST) & (sched.season <= CAL)]
    rows = []
    for r in reg.itertuples():
        as_of = datetime.fromisoformat(str(r.gameday)).replace(tzinfo=timezone.utc)
        out = fb.row(r.home_team, r.away_team, as_of, r.home_rest, r.away_rest)
        if out is None:
            continue
        rows.append({"season": r.season, "margin": r.home_score - r.away_score, **out["features"]})
    return pd.DataFrame(rows)


def ridge(X, y, lam):
    mu, sd = X.mean(0), X.std(0)
    sd[sd == 0] = 1.0
    Z = (X - mu) / sd
    w = np.linalg.solve(Z.T @ Z + lam * np.eye(Z.shape[1]), Z.T @ (y - y.mean()))
    return float(y.mean()), w, mu, sd


def platt(z, y):
    a, b = 1.0, 0.0
    for _ in range(50):
        eta = a * z + b
        p = np.clip([_phi(e) for e in eta], 1e-6, 1 - 1e-6)
        pdf = np.exp(-0.5 * eta**2) / math.sqrt(2 * math.pi)
        w = pdf**2 / (p * (1 - p))
        g = (y - p) * pdf / (p * (1 - p))
        X = np.column_stack([z, np.ones_like(z)])
        s = np.linalg.solve(X.T @ (X * w[:, None]) + 1e-9 * np.eye(2), X.T @ g)
        a, b = a + s[0], b + s[1]
    return float(a), float(b)


def file_sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--schedule", required=True, help="schedule_extended.parquet (has qb ids)")
    ap.add_argument("--team-stats", required=True)
    ap.add_argument("--out", default=str(ROOT / "models" / "nfl_qb_challenger_v1.json"))
    a = ap.parse_args()
    out = Path(a.out)
    if out.exists():
        raise SystemExit(f"{out} exists -- the artifact is frozen; refusing to overwrite")
    sp, tp = Path(a.schedule), Path(a.team_stats)
    sched, stats = pd.read_parquet(sp), pd.read_parquet(tp)
    df = build_frame(sched, stats)
    tr, ca = df[df.season <= TRAIN_LAST], df[df.season == CAL]
    c = CHALLENGER_FEATURE_NAMES
    b0, w, mu, sd = ridge(tr[c].to_numpy(float), tr.margin.to_numpy(float), LAMBDA)
    raw = lambda f: b0 + ((f[c].to_numpy(float) - mu) / sd) @ w  # noqa: E731
    rc = raw(ca)
    sm = float(np.std(ca.margin.to_numpy(float) - rc, ddof=1))
    nt = (ca.margin != 0).to_numpy()
    pa, pb = platt(rc[nt] / sm, (ca.margin.to_numpy()[nt] > 0).astype(float))
    trn = tr[tr.margin != 0]
    art = {"model_id": "nfl_qb_challenger_v1", "feature_names": c, "lambda": LAMBDA,
           "train_seasons": [FIRST, TRAIN_LAST], "cal_season": CAL, "qb_source": "projected_prior_game_starter",
           "margin": {"intercept": b0, "coef": w.tolist(), "mean": mu.tolist(), "std": sd.tolist()},
           "platt": {"a": pa, "b": pb}, "sigma_margin": sm,
           "climatology": {"home_win_rate_ex_ties": float((trn.margin > 0).mean()), "mean_margin": float(tr.margin.mean()),
                           "mean_total": 0.0, "sd_margin": float(tr.margin.std()), "sd_total": 1.0,
                           "tie_rate": float((tr.margin == 0).mean())}}
    art["sha256"] = canonical_sha(art)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(art, indent=1, sort_keys=True))
    try:
        code = subprocess.check_output(["git", "-C", str(ROOT), "rev-parse", "HEAD"], text=True).strip()
    except Exception:
        code = "unknown"
    meta = {"model_id": art["model_id"], "artifact_sha256": art["sha256"], "artifact_file_sha256": file_sha(out),
            "frozen_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"), "code_sha": code,
            "input_schedule_sha256": file_sha(sp), "input_team_stats_sha256": file_sha(tp),
            "n_train": int(len(tr)), "n_cal": int(len(ca)), "sigma_margin": sm, "platt": art["platt"],
            "preregistration": "12_EXPLORATORY/NFL_QB_SHRUNK_CHALLENGER_PREREGISTRATION_2026-10-09.md (ACCEPTED 2026-10-10)"}
    out.with_name("nfl_qb_challenger_v1_meta.json").write_text(json.dumps(meta, indent=1))
    print(json.dumps(meta, indent=1))


if __name__ == "__main__":
    main()
