#!/usr/bin/env python3
"""
ab_harness_t4 — ADR-0042 D2 holdout gate for T4 probability-model enhancers.
Parent: T-583 (design: RESULTS_SUMMARIES/T583_t4_ab_harness_DESIGN.md)

Parallel to (NOT a modification of) ab_harness.py, which is the T1 bet-subset
P&L harness. A T4 enhancer replaces a probability on every evaluation row, so
the statistic is a PAIRED PROPER-SCORING gain, and the independent unit is the
GAME, not the row.

INPUT CONTRACT (enforced in code; every violation RAISES — the harness never
imputes, never drops silently, never returns a number on an inadequate cohort)

Each row is a dict with REQUIRED fields:
    ticker, game_id, game_date (YYYY-MM-DD), p_incumbent (0..1),
    outcome (0/1), resolution_source, cohort_band, logic_epoch
plus every field named in `required_state_fields` (the candidate's declared
game-state inputs; ADR-0065's set is WALKOFF_STATE_FIELDS), present and non-None.

RESOLUTION SEMANTICS: `outcome` must come from a source decoupled from the
paper ledger (RESOLUTION_SOURCES_OK). Ledger-derived outcomes are refused
(GG-166 corrupted ~44% of epoch-12 ledger outcomes). `game_date` must equal the
date embedded in `ticker` (GG-164/GG-170: stored dates are wrong on ~70% of
cycle-log rows). Train days must strictly precede test days by that true date.

MINIMUMS: MIN_TRAIN_GAMES, MIN_TEST_GAMES, and MIN_DIFFERING_TEST_GAMES (games
where candidate != incumbent on >=1 row). Rows where the two are identical carry
no information, so they cannot buy power.

FORBIDDEN COHORT: the T4M-PROJ epoch-12 ledger (T-577 UNRECOVERABLE). Refused by
(a) band+epoch labels, (b) any ticker in scripts/t4_forbidden_cohort_manifest.json.

VERDICTS (only after every refusal has passed):
    DEFENSIBLE_IMPROVEMENT : ΔBrier gain CI (game-clustered) lower bound > 0
                             AND Δlog-loss gain point estimate > 0
    HARMFUL                : ΔBrier gain CI upper bound < 0
    INCONCLUSIVE           : otherwise
`gate_eligible` is False for synthetic cohorts: a synthetic run exercises the
machinery; it is never evidence about a real enhancer.
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path
from typing import Callable, Sequence

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from clv_harness import _block_bootstrap_mean_ci  # noqa: E402  generic cluster-bootstrap primitive
from prediction_market_bot.c5_execution.market_type_registry import derive_game_date  # noqa: E402

MIN_TRAIN_GAMES = 30
MIN_TEST_GAMES = 30
MIN_DIFFERING_TEST_GAMES = 30
N_BOOT = 5000
EPS = 1e-6  # log-loss clip; documented, symmetric

REQUIRED_FIELDS = ("ticker", "game_id", "game_date", "p_incumbent", "outcome",
                   "resolution_source", "cohort_band", "logic_epoch")
RESOLUTION_SOURCES_OK = frozenset({"kalshi_settlement", "boxscore_rederived",
                                   "synthetic_ground_truth"})
WALKOFF_STATE_FIELDS = ("inning_half", "home_score", "away_score", "outs",
                        "base_state", "pitcher_id", "pitch_count")  # ADR-0065 §activation
FORBIDDEN_BAND, FORBIDDEN_EPOCH = "T4M-PROJ", 12
MANIFEST_PATH = Path(__file__).resolve().parent / "t4_forbidden_cohort_manifest.json"


class T4HarnessRefusal(Exception):
    """Base: the harness refuses to score. Never caught internally."""


class MissingFieldError(T4HarnessRefusal): ...
class ForbiddenCohortError(T4HarnessRefusal): ...
class UnresolvedOutcomeError(T4HarnessRefusal): ...
class DateIntegrityError(T4HarnessRefusal): ...
class SplitError(T4HarnessRefusal): ...
class InadequateCohortError(T4HarnessRefusal): ...
class PreRegistrationError(T4HarnessRefusal): ...


def _forbidden_tickers() -> frozenset:
    return frozenset(json.loads(MANIFEST_PATH.read_text())["tickers"])


def validate_rows(rows: Sequence[dict], required_state_fields: Sequence[str] = ()) -> None:
    """Raise on the first contract violation. Pure check; no mutation."""
    if not rows:
        raise InadequateCohortError("empty cohort")
    forbidden = _forbidden_tickers()
    need = tuple(REQUIRED_FIELDS) + tuple(required_state_fields)
    for i, r in enumerate(rows):
        if r.get("cohort_band") == FORBIDDEN_BAND and r.get("logic_epoch") == FORBIDDEN_EPOCH:
            raise ForbiddenCohortError(
                f"row {i}: {FORBIDDEN_BAND} epoch-{FORBIDDEN_EPOCH} cohort is refused by name "
                f"(T-577 UNRECOVERABLE: 35 confirmed-real rows, non-random, GG-166 outcomes)")
        if r.get("ticker") in forbidden:
            raise ForbiddenCohortError(
                f"row {i}: ticker {r['ticker']} is in the T-577 forbidden-cohort manifest")
        for f in need:
            if f not in r or r[f] is None:
                raise MissingFieldError(f"row {i} ({r.get('ticker')}): required field '{f}' absent/None")
        if r["resolution_source"] not in RESOLUTION_SOURCES_OK:
            raise UnresolvedOutcomeError(
                f"row {i}: resolution_source={r['resolution_source']!r} not in "
                f"{sorted(RESOLUTION_SOURCES_OK)} (ledger outcomes are refused)")
        if r["outcome"] not in (0, 1):
            raise UnresolvedOutcomeError(f"row {i}: outcome={r['outcome']!r} is not a resolved 0/1")
        if not (0.0 <= r["p_incumbent"] <= 1.0):
            raise MissingFieldError(f"row {i}: p_incumbent={r['p_incumbent']!r} outside [0,1]")
        try:
            true_date = derive_game_date(r["ticker"])
        except Exception as e:  # registry refuses unparseable tickers; propagate as refusal
            raise DateIntegrityError(f"row {i}: cannot derive date from ticker {r['ticker']!r}: {e}")
        if str(r["game_date"]) != true_date:
            raise DateIntegrityError(
                f"row {i}: stored game_date {r['game_date']} != ticker-derived {true_date} (GG-164)")


def _brier(p: float, y: int) -> float:
    return (p - y) ** 2


def _logloss(p: float, y: int) -> float:
    p = min(max(p, EPS), 1 - EPS)
    return -(y * math.log(p) + (1 - y) * math.log(1 - p))


def run_gate(rows: Sequence[dict], candidate: Callable[[list], Callable[[dict], float]], *,
             cutoff: str, hypothesis: str, required_state_fields: Sequence[str] = (),
             synthetic: bool = False, n_boot: int = N_BOOT, seed: int = 17) -> dict:
    """Holdout gate. `candidate(train_rows)` is fit on TRAIN ONLY and returns
    predict(row)->p. Raises T4HarnessRefusal subclasses on any inadequacy."""
    if not (hypothesis or "").strip():
        raise PreRegistrationError("hypothesis must be pre-registered (non-empty) before scoring")
    validate_rows(rows, required_state_fields)
    train = [r for r in rows if r["game_date"] < cutoff]
    test = [r for r in rows if r["game_date"] >= cutoff]
    if {r["game_id"] for r in train} & {r["game_id"] for r in test}:
        raise SplitError("a game_id appears on both sides of the cutoff")
    n_tr, n_te = len({r["game_id"] for r in train}), len({r["game_id"] for r in test})
    if n_tr < MIN_TRAIN_GAMES:
        raise InadequateCohortError(f"train games {n_tr} < {MIN_TRAIN_GAMES}")
    if n_te < MIN_TEST_GAMES:
        raise InadequateCohortError(f"test games {n_te} < {MIN_TEST_GAMES}")

    predict = candidate(train)  # fit sees train only
    g, d_brier, d_ll, differing = [], [], [], set()
    for r in test:
        pc = predict(r)
        if not (0.0 <= pc <= 1.0):
            raise MissingFieldError(f"candidate returned p={pc!r} outside [0,1] for {r['ticker']}")
        pi, y = r["p_incumbent"], r["outcome"]
        d_brier.append(_brier(pi, y) - _brier(pc, y))
        d_ll.append(_logloss(pi, y) - _logloss(pc, y))
        g.append(r["game_id"])
        if pc != pi:
            differing.add(r["game_id"])
    if len(differing) < MIN_DIFFERING_TEST_GAMES:
        raise InadequateCohortError(
            f"games where candidate differs from incumbent = {len(differing)} < "
            f"{MIN_DIFFERING_TEST_GAMES}; identical rows carry no information")

    b = _block_bootstrap_mean_ci(d_brier, g, n_boot=n_boot, seed=seed)
    ll = _block_bootstrap_mean_ci(d_ll, g, n_boot=n_boot, seed=seed + 1)
    if b["ci_low"] > 0 and ll["mean"] > 0:
        verdict = "DEFENSIBLE_IMPROVEMENT"
    elif b["ci_high"] < 0:
        verdict = "HARMFUL"
    else:
        verdict = "INCONCLUSIVE"
    return {"verdict": verdict, "gate_eligible": not synthetic, "synthetic": synthetic,
            "hypothesis": hypothesis, "cutoff": cutoff,
            "n_train_games": n_tr, "n_test_games": n_te, "n_test_rows": len(test),
            "n_differing_test_games": len(differing),
            "brier_gain": b, "logloss_gain": ll,
            "unit": "game-clustered paired bootstrap; positive = candidate better"}
