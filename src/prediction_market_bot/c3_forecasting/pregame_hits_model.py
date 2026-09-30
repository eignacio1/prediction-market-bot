"""EXP-028 (T-594): pre-game MLB P(h >= 1) model on the frozen feature matrix.

Everything here implements ``05_RESEARCH_EXPERIMENTS/RESULTS_SUMMARIES/
EXP028_pregame_mlb_hits_PREREGISTRATION_2026-09-30.md`` (commit 90e96c2). Splits,
features, model class, C grid, metric, seeds and decision rule are frozen there.

Research module only: no order, pool or ledger access; nothing scheduled.
Scoring imports the T-583 harness primitives (scripts/ab_harness_t4.py) rather
than reimplementing them.
"""
from __future__ import annotations

import hashlib
import sys
from pathlib import Path
from typing import Sequence

import numpy as np
import pandas as pd

MATRIX_SHA256 = "b2a845a6fb35cfc8c0ec7589524313aeabd20e2140a353409e984f44979114a4"

TRAIN = ("2024-01-01", "2024-12-31")
VALIDATION = ("2025-01-01", "2025-12-31")
HOLDOUT = ("2026-01-01", "2026-07-17")
C_GRID = (0.01, 0.1, 1.0, 10.0)
SEED_BRIER, SEED_LOGLOSS, SEED_PERM = 17, 18, 2028
PLACEBO_LAG = 11

FEATURES = [
    "ba_l10_shrunk", "slg_l10", "obp_l10", "h_l10_mean", "k_rate_l10",
    "bb_rate_l10", "hr_rate_l10", "ab_l10_mean",
    "opp_runs_allowed_l10",
    "opp_sp_era_l5", "opp_sp_k9_l5", "opp_sp_bb9_l5", "opp_sp_missing",
    "is_home_game", "days_rest", "b2b_flag",
]
_CLIPS = {"opp_sp_era_l5": (0, 15), "opp_sp_k9_l5": (0, 20),
          "opp_sp_bb9_l5": (0, 15), "days_rest": (0, 10)}


def _harness():
    """Import T-583 harness primitives (imported, not reimplemented)."""
    scripts = str(Path(__file__).resolve().parents[3] / "scripts")
    if scripts not in sys.path:
        sys.path.insert(0, scripts)
    import ab_harness_t4 as h
    return h


def sha256_file(path: Path) -> str:
    d = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            d.update(chunk)
    return d.hexdigest()


def load_population(path: Path, *, verify_sha: bool = True) -> pd.DataFrame:
    """Load matrix and apply the pre-registered population filter (§3)."""
    if verify_sha and sha256_file(path) != MATRIX_SHA256:
        raise RuntimeError("matrix sha256 does not match pre-registration")
    df = pd.read_csv(path, low_memory=False)
    df = df.sort_values(["player_id", "game_date", "game_id"]).reset_index(drop=True)
    dup = df.duplicated(["player_id", "game_id"], keep=False)
    df = df[~dup].copy()
    # role proxy: mean ab over previous <=10 games (shift(1), min 3), all rows incl. ab==0
    g = df.groupby("player_id", sort=False)["ab"]
    df["ab_l10_mean"] = g.transform(lambda s: s.shift(1).rolling(10, min_periods=3).mean())
    df["y"] = (df["h"] >= 1).astype(int)
    # placebo: same player's outcome PLACEBO_LAG rows earlier (uses full sequence pre-filter on ab)
    df["y_backward"] = df.groupby("player_id", sort=False)["y"].shift(PLACEBO_LAG)
    df = df[(df["ab"] >= 1) & df["ba_l10"].notna()].copy()
    df["opp_sp_missing"] = df[["opp_sp_era_l5", "opp_sp_k9_l5", "opp_sp_bb9_l5"]].isna().all(axis=1).astype(int)
    df["is_home_game"] = df["is_home_game"].astype(int)
    df["b2b_flag"] = df["b2b_flag"].astype(float)
    for c, (lo, hi) in _CLIPS.items():
        df[c] = df[c].clip(lo, hi)
    df["game_date"] = df["game_date"].astype(str)
    return df.reset_index(drop=True)


def split(df: pd.DataFrame, bounds: tuple[str, str]) -> pd.DataFrame:
    return df[(df["game_date"] >= bounds[0]) & (df["game_date"] <= bounds[1])]


class PregameHitsModel:
    """Median-impute + standardise + L2 logistic regression."""

    def __init__(self, C: float):
        self.C = C

    def fit(self, d: pd.DataFrame) -> "PregameHitsModel":
        from sklearn.linear_model import LogisticRegression
        X = d[FEATURES].astype(float)
        self.med_ = X.median()
        X = X.fillna(self.med_)
        self.mu_, self.sd_ = X.mean(), X.std(ddof=0).replace(0, 1.0)
        self.lr_ = LogisticRegression(C=self.C, solver="lbfgs", max_iter=1000)
        self.lr_.fit(((X - self.mu_) / self.sd_).values, d["y"].values)
        return self

    def predict(self, d: pd.DataFrame) -> np.ndarray:
        X = d[FEATURES].astype(float).fillna(self.med_)
        return self.lr_.predict_proba(((X - self.mu_) / self.sd_).values)[:, 1]


def brier_vec(p: np.ndarray, y: np.ndarray) -> np.ndarray:
    return (p - y) ** 2


def logloss_vec(p: np.ndarray, y: np.ndarray, eps: float) -> np.ndarray:
    p = np.clip(p, eps, 1 - eps)
    return -(y * np.log(p) + (1 - y) * np.log(1 - p))


def baseline_b1(d: pd.DataFrame) -> np.ndarray:
    ba = d["ba_l10_shrunk"].fillna(d["ba_l10_shrunk"].median()).values
    ab = d["ab_l10_mean"].fillna(d["ab_l10_mean"].median()).values
    return np.clip(1 - (1 - ba) ** ab, 1e-6, 1 - 1e-6)


def paired_delta(p_base: np.ndarray, p_model: np.ndarray, y: np.ndarray,
                 games: Sequence[str], *, n_boot: int | None = None) -> dict:
    """Game-clustered paired delta (base minus model; positive = model better)."""
    h = _harness()
    n_boot = n_boot or h.N_BOOT
    keys = [str(g) for g in games]
    d_b = brier_vec(p_base, y) - brier_vec(p_model, y)
    d_l = logloss_vec(p_base, y, h.EPS) - logloss_vec(p_model, y, h.EPS)
    b = h._block_bootstrap_mean_ci(list(d_b), keys, n_boot=n_boot, seed=SEED_BRIER)
    l = h._block_bootstrap_mean_ci(list(d_l), keys, n_boot=n_boot, seed=SEED_LOGLOSS)
    return {"delta_brier": b, "delta_logloss": l, "verdict": verdict(b, l)}


def verdict(b: dict, l: dict) -> str:
    """Harness rule; INCONCLUSIVE is reported as NO DETECTABLE DIFFERENCE (ADR-0066)."""
    if b["ci_low"] > 0 and l["mean"] > 0:
        return "DEFENSIBLE_IMPROVEMENT"
    if b["ci_high"] < 0:
        return "HARMFUL"
    return "NO DETECTABLE DIFFERENCE"


def permute_within_date(d: pd.DataFrame, seed: int = SEED_PERM) -> np.ndarray:
    rng = np.random.default_rng(seed)
    y = d["y"].values.copy()
    for _, idx in d.groupby("game_date").indices.items():
        y[idx] = rng.permutation(y[idx])
    return y
