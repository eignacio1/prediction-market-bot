"""Selection-vs-placement decomposition of a treatment-minus-control fill gain.

Descriptive only. Rows are *fills*: (arm, game, stratum, value) where value is
settle-minus-price and stratum is the matching key (e.g. ticker + held side).

    total      = mean_T - mean_C
    placement  = mean_T[S] - C_reweighted[S]   within-stratum difference on the
                                               common support S (both arms filled),
                                               weighted by treatment's mix
    selection  = C_reweighted[S] - mean_C      moving control's fill mix to
                                               treatment's (on S)
    unmatched  = mean_T - mean_T[S]            treatment fills in strata control
                                               never filled (no counterfactual)
    total = placement + selection + unmatched   (exact)

Also reports skipped_control: control's mean value on fills in strata where
treatment did NOT fill (what waiting skipped).

Intervals: game-cluster bootstrap (resample games with replacement).
Applicability: strata must be defined so every order in a stratum shares one
settlement outcome (ticker + side); otherwise "placement" absorbs outcome noise.
"""
from __future__ import annotations

import random
from collections import defaultdict
from typing import Iterable, Sequence

Row = tuple  # (arm, game, stratum, value)

_KEYS = ("total", "placement", "selection", "unmatched", "skipped_control")


def decompose(rows: Iterable[Row]) -> dict:
    t_by = defaultdict(list)
    c_by = defaultdict(list)
    for arm, _g, s, v in rows:
        (t_by if arm == "treatment" else c_by)[s].append(v)
    nT = sum(len(v) for v in t_by.values())
    nC = sum(len(v) for v in c_by.values())
    if nT == 0 or nC == 0:
        raise ValueError("need fills in both arms")
    mT = sum(sum(v) for v in t_by.values()) / nT
    mC = sum(sum(v) for v in c_by.values()) / nC
    common = [s for s in t_by if s in c_by]
    nTS = sum(len(t_by[s]) for s in common)
    out = {"n_treatment": nT, "n_control": nC, "total": mT - mC,
           "n_common_strata": len(common)}
    if nTS == 0:
        out.update(placement=float("nan"), selection=float("nan"),
                   unmatched=mT - mT, skipped_control=float("nan"))
        return out
    mTS = sum(sum(t_by[s]) for s in common) / nTS
    crw = sum(len(t_by[s]) * (sum(c_by[s]) / len(c_by[s])) for s in common) / nTS
    skipped = [x for s, v in c_by.items() if s not in t_by for x in v]
    out.update(
        placement=mTS - crw,
        selection=crw - mC,
        unmatched=mT - mTS,
        skipped_control=(sum(skipped) / len(skipped)) if skipped else float("nan"),
        n_skipped_control=len(skipped),
        n_treatment_common=nTS,
    )
    return out


def cluster_bootstrap(rows: Sequence[Row], reps: int = 2000, seed: int = 7,
                      level: float = 0.90) -> dict:
    """Game-clustered percentile intervals for every component of decompose()."""
    by_game = defaultdict(list)
    for r in rows:
        by_game[r[1]].append(r)
    games = list(by_game)
    rng = random.Random(seed)
    draws = {k: [] for k in _KEYS}
    for _ in range(reps):
        sample = []
        for _i in range(len(games)):
            sample.extend(by_game[games[rng.randrange(len(games))]])
        try:
            d = decompose(sample)
        except ValueError:
            continue
        for k in _KEYS:
            x = d.get(k)
            if x == x:  # drop NaN
                draws[k].append(x)
    lo_q, hi_q = (1 - level) / 2, 1 - (1 - level) / 2
    res = {"games": len(games), "reps": reps, "level": level, "point": decompose(rows)}
    for k, xs in draws.items():
        xs.sort()
        if xs:
            res[k] = (xs[int(lo_q * (len(xs) - 1))], xs[int(hi_q * (len(xs) - 1))])
        else:
            res[k] = (float("nan"), float("nan"))
    return res
