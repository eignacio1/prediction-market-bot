"""EXP-030 (T-598) T4M-PROJ structure enhancer: a residual logistic model over the incumbent.

New module. The incumbent `run_t4_mlb_live.p_hits_gte_threshold` is NOT imported for
modification and is never edited (40.3's provenance hash chain depends on it).
Pre-registration: 05_RESEARCH_EXPERIMENTS/EXP030_T4_STRUCTURE_PREREGISTRATION_2026-09-30.md.
Every input is available at decision time (D1 inventory); game-state fields are excluded.
"""
from __future__ import annotations

import math
from typing import Callable, Sequence

import numpy as np
from scipy.optimize import minimize

P_MIN, P_MAX = 0.001, 0.999
C_GRID = (0.01, 0.1, 1.0)
FEATURE_NAMES = ("threshold", "h_needed", "ab_remaining", "slot_4_6", "slot_7_9",
                 "inn_4_6", "inn_7p", "ba_l10_shrunk", "batter_home")


def batter_is_home(ticker: str) -> float:
    """KXMLBHIT-<date><AWAY><HOME>-<TEAM><PLAYER><num>-<thr>: home if player segment starts with HOME."""
    parts = ticker.split("-")
    event, player = parts[1], parts[2]
    return 1.0 if player.startswith(event[-3:]) else 0.0


def _logit(p: float) -> float:
    p = min(max(p, P_MIN), P_MAX)
    return math.log(p / (1.0 - p))


def features(row: dict) -> np.ndarray:
    slot, inn = row["batting_slot"], row["inning"]
    return np.array([
        row["threshold"],
        max(0, row["threshold"] - row["h_so_far"]),
        row["ab_remaining"],
        1.0 if 4 <= slot <= 6 else 0.0,
        1.0 if slot >= 7 else 0.0,
        1.0 if 4 <= inn <= 6 else 0.0,
        1.0 if inn >= 7 else 0.0,
        row["ba_l10_shrunk"],
        batter_is_home(row["ticker"]),
    ])


class ResidualLogit:
    """p = sigmoid(logit(p_incumbent) + b0 + w . standardised_features); L2 on w (not b0)."""

    def __init__(self, C: float):
        self.C = C

    def fit(self, rows: Sequence[dict]) -> "ResidualLogit":
        X = np.array([features(r) for r in rows])
        y = np.array([r["outcome"] for r in rows], dtype=float)
        off = np.array([_logit(r["p_incumbent"]) for r in rows])
        self.mu, self.sd = X.mean(0), X.std(0)
        self.sd[self.sd == 0] = 1.0
        Z = (X - self.mu) / self.sd
        n, k = Z.shape

        def nll(theta):
            b0, w = theta[0], theta[1:]
            eta = off + b0 + Z @ w
            loss = np.sum(np.logaddexp(0, eta) - y * eta) + 0.5 / self.C * float(w @ w)
            pr = 1.0 / (1.0 + np.exp(-eta))
            g = np.concatenate([[np.sum(pr - y)], Z.T @ (pr - y) + w / self.C])
            return loss, g

        res = minimize(nll, np.zeros(k + 1), jac=True, method="L-BFGS-B")
        self.b0, self.w = res.x[0], res.x[1:]
        return self

    def predict(self, row: dict) -> float:
        z = (features(row) - self.mu) / self.sd
        eta = _logit(row["p_incumbent"]) + self.b0 + float(z @ self.w)
        return min(max(1.0 / (1.0 + math.exp(-eta)), P_MIN), P_MAX)


def brier_gain(rows: Sequence[dict], predict: Callable[[dict], float]) -> float:
    """Mean paired Brier gain (incumbent minus candidate); positive = candidate better."""
    return float(np.mean([(r["p_incumbent"] - r["outcome"]) ** 2 - (predict(r) - r["outcome"]) ** 2
                          for r in rows]))


def select_c(train: Sequence[dict], val: Sequence[dict]) -> tuple[float, dict]:
    """Choose C on validation by Brier gain; ties go to the smaller C (C_GRID is ascending)."""
    gains = {C: brier_gain(val, ResidualLogit(C).fit(train).predict) for C in C_GRID}
    best = max(C_GRID, key=lambda c: (round(gains[c], 12), -c))
    return best, gains


def permutation_control(train: Sequence[dict], val: Sequence[dict], C: float,
                        n_perm: int = 200, seed: int = 30) -> np.ndarray:
    """Shuffle train outcomes across tickers within threshold; refit; validation Brier gain each time."""
    rng = np.random.default_rng(seed)
    tickers: dict = {}
    for r in train:
        tickers.setdefault(r["ticker"], r["outcome"])
    thr_of = {}
    for r in train:
        thr_of.setdefault(r["ticker"], r["threshold"])
    by_thr: dict = {}
    for t, thr in thr_of.items():
        by_thr.setdefault(thr, []).append(t)
    out = np.empty(n_perm)
    for i in range(n_perm):
        perm = {}
        for ts in by_thr.values():
            labs = [tickers[t] for t in ts]
            rng.shuffle(labs)
            perm.update(zip(ts, labs))
        shuffled = [{**r, "outcome": perm[r["ticker"]]} for r in train]
        out[i] = brier_gain(val, ResidualLogit(C).fit(shuffled).predict)
    return out


def make_candidate(split_date: str, c_fixed: float) -> Callable[[list], Callable[[dict], float]]:
    """Harness candidate factory. `c_fixed` was chosen on validation BEFORE the holdout call;
    the fit sees pre-cutoff rows only (train + validation)."""
    def candidate(train_rows: list) -> Callable[[dict], float]:
        return ResidualLogit(c_fixed).fit(train_rows).predict
    return candidate
