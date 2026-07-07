#!/usr/bin/env python3
"""
ab_harness — A/B Edge-Delta Framework for Strategy/Config Variants
Companion infrastructure to EXP-017 / 017B / 017C.  "The methodology is the asset."

WHY THIS EXISTS
---------------
Before any strategy change (YES-quarantine, min-edge filter, recalibrated
model_p, and eventually PAM / psych-gradient enhancers) is adopted, it must
clear one bar: does it produce a DEFENSIBLE edge delta vs the current baseline,
or is the apparent improvement in-sample noise-fitting?

EXP-017C established that realized P&L at n~151 is variance-dominated. That makes
it trivially easy to "improve" the book in-sample by dropping whatever lost.
This harness exists to stop that: it measures Δ(metric) with a bootstrap CI and,
crucially, supports a HOLDOUT split so a rule selected on one period is scored on
another — the only statistically valid way to validate a filter.

CONTRACT
--------
A Strategy has:
    name, description, hypothesis   (hypothesis pre-registered BEFORE results)
    fit(train_recs)                 optional; learns params (e.g. Platt IRLS)
    apply(recs) -> list[dict]       returns the taken subset (optionally rescored)

Records are the EXP-017B loader dicts (direction-aware _fne per GG-077), plus a
reconstructed binary _event. pnl/size are the realized, immutable ground truth;
re-scoring model_p only changes SELECTION and calibration metrics, never a bet's
realized pnl.

METRICS (per taken set)
    n, win_rate, ev_per_bet_usd (Σpnl/n), pnl_per_dollar (Σpnl/Σsize),
    total_pnl, brier, calib_slope

COMPARISON (B vs A)
    Primary metric: pnl_per_dollar (sizing-neutral).
    Independent bootstrap of A and B taken sets; Δ_j = boot_B_j − boot_A_j.
    Report Δ point, 95% CI, P(Δ>0). When B ⊆ A (a filter), also report the
    EV of REMOVED bets (A∖B) and P(kept > removed) — a filter is only defensible
    if the bets it drops are distinguishably worse than the ones it keeps.

VERDICT
    DEFENSIBLE_IMPROVEMENT : Δ CI excludes 0 (and Δ>0) and n_B >= MIN_N
    HARMFUL                : Δ CI excludes 0 and Δ<0
    INCONCLUSIVE           : Δ CI includes 0  (most in-sample "wins" land here)
    UNDERPOWERED           : n_B < MIN_N
"""
from __future__ import annotations

import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

sys.path.insert(0, str(Path(__file__).resolve().parent))
import run_exp017b_decomp_mlb as d17b   # noqa: E402  loader
import run_exp017c_calibration_mlb as c17c  # noqa: E402  logit/irls/sigmoid

MIN_N = 30           # ADR-0005 paper-gate floor; below this Δ is UNDERPOWERED
P_THRESHOLD = 0.05


# ── records ──────────────────────────────────────────────────────────────────────

def load(portfolio: Path) -> list[dict]:
    recs = d17b.load_records(portfolio)
    for r in recs:
        r["_event"] = 1 if ((r["_dir"] == "YES") == (r["_win"] == 1)) else 0
    return recs


def holdout_split(recs: list[dict], cutoff: str) -> tuple[list[dict], list[dict]]:
    """train = game_date < cutoff ; test = game_date >= cutoff."""
    train = [r for r in recs if str(r.get("game_date", "")) < cutoff]
    test = [r for r in recs if str(r.get("game_date", "")) >= cutoff]
    return train, test


# ── strategy ─────────────────────────────────────────────────────────────────────

@dataclass
class Strategy:
    name: str
    description: str
    hypothesis: str
    select: Callable[[dict], bool] = lambda r: True
    rescore: Callable[[dict, dict], float] | None = None  # (rec, params)->model_p
    params: dict = field(default_factory=dict)
    _fitter: Callable[[list[dict]], dict] | None = None

    def fit(self, train: list[dict]) -> None:
        if self._fitter is not None:
            self.params = self._fitter(train)

    def apply(self, recs: list[dict]) -> list[dict]:
        out = []
        for r in recs:
            rr = dict(r)
            if self.rescore is not None:
                rr["_model_p"] = self.rescore(r, self.params)
                # recompute direction-aware edge with rescored p (GG-077)
                import run_exp017_mlb as e17
                rr["_fne"] = e17.compute_fee_net_edge(rr["_dir"], rr["_model_p"], rr["_mip"])
            if self.select(rr):
                out.append(rr)
        return out


# ── metrics ──────────────────────────────────────────────────────────────────────

def metrics(taken: list[dict]) -> dict:
    n = len(taken)
    if n == 0:
        return {"n": 0, "win_rate": 0.0, "ev_per_bet_usd": 0.0,
                "pnl_per_dollar": 0.0, "total_pnl": 0.0, "brier": None,
                "calib_slope": None}
    wins = sum(r["_win"] for r in taken)
    tot_pnl = sum(r["_pnl"] for r in taken)
    tot_size = sum(r["_size"] for r in taken)
    brier = sum((r["_model_p"] - r["_event"]) ** 2 for r in taken) / n
    if n >= 8:
        xs = [c17c.logit(r["_model_p"]) for r in taken]
        ys = [r["_event"] for r in taken]
        _, b = c17c.irls_logistic(xs, ys)
    else:
        b = None
    return {"n": n, "win_rate": wins / n, "ev_per_bet_usd": tot_pnl / n,
            "pnl_per_dollar": (tot_pnl / tot_size) if tot_size else 0.0,
            "total_pnl": tot_pnl, "brier": brier, "calib_slope": b}


def _boot_ppd(taken: list[dict], boot: int, rng: random.Random) -> list[float]:
    """Bootstrap distribution of pnl_per_dollar."""
    n = len(taken)
    pnl = [r["_pnl"] for r in taken]
    size = [r["_size"] for r in taken]
    out = []
    for _ in range(boot):
        sp = ss = 0.0
        for _ in range(n):
            i = rng.randrange(n)
            sp += pnl[i]; ss += size[i]
        out.append((sp / ss) if ss else 0.0)
    return out


def _boot_delta_paired(A: list[dict], B_ids: set, boot: int,
                       rng: random.Random) -> list[float]:
    """Paired bootstrap Δ(ppd) for nested B ⊆ A: one common resample of A,
    with B's metric computed on the resampled rows that pass B's selection.
    Preserves shared-bet covariance -> correct (tighter) CI than independent."""
    n = len(A)
    pnl = [r["_pnl"] for r in A]
    size = [r["_size"] for r in A]
    inB = [r.get("position_id") in B_ids for r in A]
    deltas = []
    for _ in range(boot):
        spA = ssA = spB = ssB = 0.0
        for _ in range(n):
            i = rng.randrange(n)
            spA += pnl[i]; ssA += size[i]
            if inB[i]:
                spB += pnl[i]; ssB += size[i]
        ppdA = (spA / ssA) if ssA else 0.0
        ppdB = (spB / ssB) if ssB else 0.0
        deltas.append(ppdB - ppdA)
    return deltas


def compare(A: list[dict], B: list[dict], boot: int, rng: random.Random) -> dict:
    """B vs A on pnl_per_dollar. Paired bootstrap when B ⊆ A (nested), else
    independent. Δ = B − A."""
    mA, mB = metrics(A), metrics(B)
    if not A or not B:
        return {"metrics_A": mA, "metrics_B": mB, "delta_ppd": None,
                "verdict": "UNDERPOWERED"}
    A_ids = {r.get("position_id") for r in A}
    B_ids = {r.get("position_id") for r in B}
    nested = B_ids.issubset(A_ids)
    if nested:
        deltas = sorted(_boot_delta_paired(A, B_ids, boot, rng))
        boot_method = "paired"
    else:
        bA = _boot_ppd(A, boot, rng)
        bB = _boot_ppd(B, boot, rng)
        deltas = sorted(bB[i] - bA[i] for i in range(boot))
        boot_method = "independent"
    lo = deltas[int(0.025 * boot)]
    hi = deltas[min(int(0.975 * boot), boot - 1)]
    p_improve = sum(1 for d in deltas if d > 0) / boot
    d_point = mB["pnl_per_dollar"] - mA["pnl_per_dollar"]

    # subset (filter) diagnostics: removed = A \ B by position_id
    idB = {r.get("position_id") for r in B}
    removed = [r for r in A if r.get("position_id") not in idB]
    subset = len(B) < len(A) and all(r.get("position_id") in
             {x.get("position_id") for x in A} for r in B)
    removed_block = None
    if subset and removed:
        mR = metrics(removed)
        bR = _boot_ppd(removed, boot, rng)
        bKept = _boot_ppd(B, boot, rng)
        p_kept_gt_removed = sum(1 for i in range(boot) if bKept[i] > bR[i]) / boot
        removed_block = {"n_removed": len(removed),
                         "removed_ppd": mR["pnl_per_dollar"],
                         "removed_total_pnl": mR["total_pnl"],
                         "kept_ppd": mB["pnl_per_dollar"],
                         "p_kept_gt_removed": p_kept_gt_removed}

    ci_excludes_0 = (lo > 0) or (hi < 0)
    if mB["n"] < MIN_N:
        verdict = "UNDERPOWERED"
    elif ci_excludes_0 and d_point > 0:
        verdict = "DEFENSIBLE_IMPROVEMENT"
    elif ci_excludes_0 and d_point < 0:
        verdict = "HARMFUL"
    else:
        verdict = "INCONCLUSIVE"

    return {"metrics_A": mA, "metrics_B": mB,
            "delta_ppd_point": d_point, "delta_ppd_ci": [lo, hi],
            "p_improve": p_improve, "boot_method": boot_method,
            "verdict": verdict, "filter_diag": removed_block}


# ── run a comparison matrix ──────────────────────────────────────────────────────

def run_matrix(recs: list[dict], baseline: Strategy, variants: list[Strategy],
               boot: int, seed: int, mode: str = "in_sample",
               cutoff: str | None = None) -> dict:
    rng = random.Random(seed)
    if mode == "holdout":
        assert cutoff, "holdout mode requires cutoff date"
        train, test = holdout_split(recs, cutoff)
        baseline.fit(train)
        A = baseline.apply(test)
        results = {}
        for v in variants:
            v.fit(train)                       # learn params on TRAIN only
            B = v.apply(test)                  # score on TEST only
            results[v.name] = {"hypothesis": v.hypothesis,
                               **compare(A, B, boot, rng)}
        universe = {"mode": mode, "cutoff": cutoff,
                    "n_train": len(train), "n_test": len(test)}
    else:
        baseline.fit(recs)
        A = baseline.apply(recs)
        results = {}
        for v in variants:
            v.fit(recs)
            B = v.apply(recs)
            results[v.name] = {"hypothesis": v.hypothesis,
                               **compare(A, B, boot, rng)}
        universe = {"mode": mode, "n": len(recs)}
    return {"universe": universe, "baseline": baseline.name,
            "baseline_metrics": metrics(A), "comparisons": results}
