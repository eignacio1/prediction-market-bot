"""W86.3: discrete-time absorbing Markov chain for an order's life, estimated from observed lives.

WHEN IT APPLIES: orders whose exit (filled / cancelled) and exit time are both logged, the time axis can be cut into
a few bins, and exits within a bin are not informative about which bin comes next beyond the bin itself (first-order
Markov in the bin index). It does NOT see the book: "behind others" and "book moved away" are not states here
because the logs carry no queue position or book path. The chain is over elapsed-time bins only.

State k (0..K-1) = the order is still resting in time bin k = [edges[k-1], edges[k]). Absorbing: F (filled), C (cancelled
unfilled). A life still resting at the end of observation (censored) contributes the bins it fully crossed plus half
exposure in the bin it was censored in (actuarial adjustment; assumes censoring independent of exit).
"""
from __future__ import annotations

import random
from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np

# A life: (t_exit_seconds, exit) with exit in {"F", "C", "O"}; "O" = still resting, censored at t_exit.
Life = Tuple[float, str]


def bin_of(t: float, edges: Sequence[float]) -> int:
    for k, e in enumerate(edges):
        if t < e:
            return k
    return len(edges)


def estimate(lives: Sequence[Life], edges: Sequence[float]) -> Dict[str, np.ndarray]:
    """Counts -> row-stochastic transient blocks. Returns advance[k], to_F[k], to_C[k] (length K) and at_risk[k]."""
    K = len(edges) + 1
    adv = np.zeros(K)
    fF = np.zeros(K)
    fC = np.zeros(K)
    cen = np.zeros(K)
    for t, ex in lives:
        j = bin_of(t, edges)
        for k in range(j):
            adv[k] += 1
        if ex == "F":
            fF[j] += 1
        elif ex == "C":
            fC[j] += 1
        else:
            cen[j] += 1  # censored inside bin j: actuarial half-exposure for that bin
    risk = adv + fF + fC + 0.5 * cen
    with np.errstate(invalid="ignore", divide="ignore"):
        pa, pf, pc = adv / risk, fF / risk, fC / risk
    pa[risk == 0] = pf[risk == 0] = pc[risk == 0] = 0.0
    pa[-1] = 0.0  # last bin is open-ended: nothing to advance to
    # the last bin renormalises over exits only
    tot = pf[-1] + pc[-1]
    if tot > 0:
        pf[-1], pc[-1] = pf[-1] / tot, pc[-1] / tot
    return {"advance": pa, "to_F": pf, "to_C": pc, "at_risk": risk}


def summarise(est: Dict[str, np.ndarray], edges: Sequence[float]) -> Dict[str, object]:
    """P(fill), P(cancel), conditional fill-time distribution by bin, expected time to absorption (seconds)."""
    pa, pf, pc = est["advance"], est["to_F"], est["to_C"]
    K = len(pa)
    Q = np.zeros((K, K))
    for k in range(K - 1):
        Q[k, k + 1] = pa[k]
    N = np.linalg.inv(np.eye(K) - Q)          # fundamental matrix: expected visits to each bin from bin 0
    visits = N[0]
    mass_F = visits * pf                        # P(exit F from bin k)
    mass_C = visits * pc
    lo = np.array([0.0] + list(edges))
    hi = np.array(list(edges) + [edges[-1] * 2.0])  # open last bin: width = the last edge (documented assumption)
    mid = (lo + hi) / 2.0
    wid = hi - lo
    pF, pC = float(mass_F.sum()), float(mass_C.sum())
    out: Dict[str, object] = {
        "p_fill": pF, "p_cancel": pC,
        "exit_mass_F_by_bin": mass_F.tolist(), "exit_mass_C_by_bin": mass_C.tolist(),
        "expected_time_to_absorb_s": float((visits * wid).sum() - 0.0),
    }
    out["expected_time_to_fill_given_fill_s"] = float((mass_F * mid).sum() / pF) if pF > 0 else None
    cum = np.cumsum(mass_F) / pF if pF > 0 else np.zeros(K)
    out["fill_cdf_by_bin_edge"] = {str(e): float(c) for e, c in zip(list(edges) + ["inf"], cum)}
    return out


def cluster_bootstrap(groups: Dict[str, List[Life]], edges: Sequence[float], stat, reps: int = 400,
                      seed: int = 86) -> Optional[Tuple[float, float, float]]:
    """Resample whole games with replacement; stat(summary dict) -> float. Returns (point, lo95, hi95)."""
    keys = list(groups)
    if len(keys) < 3:
        return None
    pooled = [l for g in keys for l in groups[g]]
    pt = stat(summarise(estimate(pooled, edges), edges))
    rng = random.Random(seed)
    vals = []
    for _ in range(reps):
        lives: List[Life] = []
        for _k in keys:
            lives.extend(groups[keys[rng.randrange(len(keys))]])
        v = stat(summarise(estimate(lives, edges), edges))
        if v is not None:
            vals.append(v)
    if not vals:
        return None
    vals.sort()
    return pt, vals[int(0.025 * len(vals))], vals[min(len(vals) - 1, int(0.975 * len(vals)))]


def simulate(P_adv: Sequence[float], P_F: Sequence[float], P_C: Sequence[float], edges: Sequence[float], n: int,
             seed: int = 1, censor_rate: float = 0.0) -> List[Life]:
    """Draw n order lives from a known chain (uniform time inside the exit bin) to test the estimator."""
    rng = random.Random(seed)
    K = len(edges) + 1
    lo = [0.0] + list(edges)
    hi = list(edges) + [edges[-1] * 2.0]
    lives: List[Life] = []
    for _ in range(n):
        k = 0
        while True:
            u = rng.random()
            if u < P_F[k]:
                ex = "F"
            elif u < P_F[k] + P_C[k]:
                ex = "C"
            else:
                ex = None
            if ex is not None or k == K - 1:
                t = lo[k] + rng.random() * (hi[k] - lo[k])
                break
            k += 1
        if rng.random() < censor_rate:
            c = rng.random() * hi[-1]  # independent censoring time
            lives.append((c, "O") if c < t else (t, ex or "C"))
        else:
            lives.append((t, ex or "C"))
    return lives
