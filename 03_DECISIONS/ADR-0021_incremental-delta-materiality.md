# ADR-0021: Incremental Delta Materiality — Calibration-Free T4 Signal Gate

**Status:** ACCEPTED  
**Date:** 2026-06-10  
**Author:** Earl Ignacio (DS) + Claude Code (implementation)  
**Supersedes:** ADR-0020 Decision D2 (T4_MIN_DELTA_P = 0.50). ADR-0020 D1 (MIN_EDGE_TO_APPROVE = 0.04) remains in force.  
**Resolves:** GG-025  
**Decisions logged:** true

---

## Context

ADR-0020 D2 raised T4_MIN_DELTA_P from 0.08 to 0.50 after G4 trajectory analysis showed
`delta_p = p_t4 − p_t1` is dominated by the **calibration gap** between the raw-Poisson
in-play model (p_t4, no Platt scaling) and the Platt-scaled pregame model (p_t1). At
tip-off — zero points scored, zero live information — the gap distribution across G4
tickers was mean 0.376, σ 0.165. The old 0.08 gate sat at the 0th percentile of that
distribution: 89% of tickers were "material" before the game contained any signal, and
the T4 budget exhausted by Q2 (GG-023 symptom).

ADR-0020 D2 was a derived threshold, but it was still a **fixed constant fitted to one
game night's calibration-gap distribution**. The DS ruled this insufficient
("we don't want a band-aid — the architecture needs the correct fix"): the quantity
being gated was wrong, not just the gate level. GG-025 was registered for the
architectural fix; this ADR delivers it.

### The defect, precisely

`delta_p = p_t4 − p_t1` mixes two components:

1. **Calibration gap** — the systematic difference between two model families
   evaluated on the same pregame information. Carries zero live signal. Varies by
   ticker, threshold distance, and pace. Cannot be removed by any single constant.
2. **Live game-state signal** — the movement of p_t4 caused by what has actually
   happened in the game.

Any fixed threshold on the mixture either fires on component (1) — the G4 failure —
or, set high enough to suppress (1), goes blind to component (2). T4_MIN_DELTA_P = 0.50
suppressed the Q1 false-fire flood but at the cost of requiring live signal to overcome
a 0.50 hurdle that has nothing to do with live signal. Both regimes are wrong.

---

## Decision

### D1 — Materiality is judged on the incremental delta, not the cross-model delta

```
p_t4_baseline = p_exceeds_threshold(0, threshold, pace × 48)
delta_p_incr  = p_t4 − p_t4_baseline
```

`p_t4_baseline` is the in-play model's own probability at the null state (zero points,
full game remaining). Subtracting it removes the calibration gap **exactly** — both
terms come from the same raw-Poisson model, so the systematic component cancels and
`delta_p_incr` contains live game-state signal only.

**Statelessness / restart safety:** `pace = pts_l10_mean / 36.0` is fixed pregame per
player per game (run_t4_live.py PACE_MINUTES_PER_GAME). The baseline is therefore a
deterministic function of (pace, threshold) — recomputable from any game state with no
stored snapshot. The T4 process died mid-game in G4; this design is immune to that
failure mode.

### D2 — The gate is the exact null noise envelope, not a constant

```
is_material(signal)  ⟺  |delta_p_incr| ≥ max(T4_DELTA_SIGMA_Z × σ_null(t), T4_MIN_DELTA_FLOOR)
```

where `σ_null(t)` is the **exact standard deviation of delta_p_incr at elapsed time t
under the null hypothesis** (player scores at pregame pace). It is computed in closed
form by Poisson pmf enumeration (`null_delta_sigma()` in game_state_model.py):

- By Poisson additivity, Poisson(pace·elapsed) + Poisson(pace·remaining) =
  Poisson(pace·48), so **E[delta_p_incr] = 0 exactly** under the null — no bias
  correction needed, verified by test to 1e-9.
- `σ_null(0) = 0` (tip-off: no information yet, any nonzero delta is impossible).
- `σ_null(48) = √(b(1−b))` where b = baseline (final horn: outcome resolved,
  delta is a shifted Bernoulli).
- σ_null is non-decreasing in elapsed time (martingale variance accumulation).

All three invariants are enforced by tests (`TestNullDeltaSigma`).

### D3 — Constants and their derivations (none fitted to G4 data)

| Constant | Value | Derivation |
|----------|-------|------------|
| `GAME_MINUTES_TOTAL` | 48.0 | NBA regulation length |
| `T4_DELTA_SIGMA_Z` | 2.0 | House σ-convention (EXP-019A methodology, as used for NOISE_BUFFER_BAND): signal must clear 2 standard deviations of its own null noise |
| `T4_MIN_DELTA_FLOOR` | 0.04 | Mirrors `MIN_EDGE_TO_APPROVE` (ADR-0020 D1): a probability movement smaller than the minimum economically actionable edge cannot justify a trade regardless of statistical significance. Governs early-game when σ_null is small. |

The gate is **per ticker, per game time** — situationally agnostic by construction.
Edge cases handled explicitly: pace = 0 (scratch player) → σ = 0, floor governs;
t_remaining > 48 or < 0 (malformed feed) → clamped; tail mass of the pmf enumeration
bounded conservatively at the Bernoulli maximum.

The economic fire condition is unchanged: `is_material AND p_t4 > mip + vig`
(plus the T-149 fee gate at C4).

---

## Empirical validation — G4 trajectory replay (n = 2,193)

Materiality pass rate by quarter, old gate (|delta_p| ≥ 0.08) vs this ADR:

| Bucket | n | Old 0.08 gate | ADR-0021 gate | Actual G4 fires |
|--------|------|---------------|----------------|------------------|
| Q1 | 1,548 | 89.3% | **10.8%** | 70.0% |
| Q2 | 453 | 55.2% | **6.8%** | 32.2% |
| Q3 | 118 | 1.7% | 3.4% | 0.8% |
| Q4 | 74 | 1.4% | **13.5%** | 1.4% |
| **Total** | 2,193 | 74.6% | **9.7%** | — |

Two properties confirm the architecture is correct, not merely stricter:

1. **The Q1 flood is gone** (89.3% → 10.8%) without any constant tuned to G4's
   calibration-gap distribution — the gap cancels algebraically.
2. **The gate gains sensitivity late** (Q4: 1.4% → 13.5%) exactly where genuine live
   signal accumulates. A fixed 0.50 threshold (ADR-0020 D2) would have suppressed both
   regions indiscriminately; the old G4 behavior had the profile inverted (firing early
   on bias, blind late). Surviving Q1 passes are genuine early deviations exceeding
   2σ of the exact null — the intended behavior, throttled by the economic
   `p_t4 > mip + vig` condition before any order is staged.

---

## Consequences

- `T4_MIN_DELTA_P` is removed from the codebase. `T4Signal` carries
  `p_t4_baseline`, `delta_p_incr`, `sigma_null`; all three are logged per cycle in
  `t4_position_trajectories.jsonl` so G5 produces direct empirical validation data.
- `delta_p = p_t4 − p_t1` remains on the signal for observability but no longer
  gates anything.
- Exit mechanics (ADR-0019) are untouched — the exit path evaluates `p_current`
  independently of the materiality gate.
- GG-023 (monotonic T4 budget counter) is the remaining T4 capital defect and is
  governed separately (T-161 / ADR-0013 amendment).
- Test coverage: 830/830 passing, including 10 structural-invariant tests for
  `null_delta_sigma` and 5 behavioral tests for the new gate.

## Review trigger

After G5 (or 3 T4-active game nights, whichever first): replay logged
`delta_p_incr` / `sigma_null` against realized outcomes. If fired signals do not show
positive realized edge versus non-fired, escalate to DS before T4 continues —
the gate isolates live signal, but whether live signal carries edge over Kalshi's
live prices is an open commercial question under GG-004's standard.
