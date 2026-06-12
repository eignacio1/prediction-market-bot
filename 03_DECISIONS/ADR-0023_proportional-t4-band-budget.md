# ADR-0023: Proportional T4 Band Budget — Remove PAPER_T4_FLAT_SIZING

**Status:** ACCEPTED  
**Date:** 2026-06-11  
**Author:** Earl Ignacio (DS) + Claude Code (implementation)  
**Amends:** ADR-0013 (T4 throughput capital budget)  
**Supersedes:** ADR-0017 (removes PAPER_T4_FLAT_SIZING bypass)  
**Resolves:** GG-026 / T-163  
**Decisions logged:** true

---

## Context

`PAPER_T4_FLAT_SIZING=true` was introduced in ADR-0017 (SESSION 24, 2026-06-05) to work around
a specific architectural problem: at `T4_BAND_WEIGHT=0.10`, the fractional-allocation formula
exhausted the band budget in ~16 bets on a $500 pool, leaving 99% of the ~1,000 evaluations/game
unfunded. The bypass hardcoded `t4_band_budget = PAPER_T4_POOL_USD = $500` and set
`approved_size = mip` (1 contract per bet).

This was correct at G1 launch when the T4 pool was $500. By G5 the T4 pool has grown to $1,869.68
through paper wins. The flat cap is now 26.7% of pool — an arbitrary fraction with no principled
relationship to capital position. It doesn't scale: a growing pool will have an ever-smaller
effective weight; a shrinking pool retains the same absolute floor even when the account can no
longer support it.

DS directive (SESSION 46 CLOSE): "I don't want arbitrary capital restraint — no bandaid fixes."

## Root cause of ADR-0017's failure

ADR-0017 diagnosed the wrong layer. The fractional-allocation formula was correct; the weight
was wrong. `T4_BAND_WEIGHT=0.10` was a Phase 8 placeholder — explicitly marked "inactive in
flat-sizing mode, never calibrated." The calibration that should have set the weight was deferred
behind the flat bypass. ADR-0017 solved the symptom (budget exhaustion) by bypassing the
mechanism rather than calibrating it.

## Decision

**Remove `PAPER_T4_FLAT_SIZING` and `PAPER_T4_POOL_USD`. Calibrate `T4_BAND_WEIGHT=0.27`
from G4 empirical data. Activate `_compute_t4_band_budget` as the single budget path.**

### T4_BAND_WEIGHT derivation

G4 Finals (2026-06-10) provides the first clean empirical budget observation with flat sizing:

- Total flat-sizing deployment: $499.95 (1,199 YES bets × mean_mip $0.417)
- T4 pool at game start: $1,869.68 (`paper_portfolio_t4.json bankroll_usd`)
- Required weight: $499.95 / $1,869.68 = **0.267 → 0.27**

This derivation uses ~1,200 evaluations/game with the ADR-0021 incremental-delta gate active
(fire rate reduced from 100% → 9.7%). The weight reflects how much of the pool the T4 band
actually consumed per game at current throughput and average market price.

### Budget formula

```
t4_band_budget = pool_bankroll × T4_BAND_WEIGHT
```

No `RESERVE_MANDATE_PCT` deduction. Rationale: `RESERVE_MANDATE_PCT` governs the T1 bankroll —
it keeps a floor so Kelly doesn't over-commit T1 capital. The T4 pool is **already isolated
capital** at the portfolio level. Applying a 40% reserve to an already-isolated pool would
double-count the reserve and underallocate: at $1,869.68 pool with RESERVE_MANDATE=0.40,
the prior formula yielded $1,121.81 × 0.10 = $112.18 — 22% of what G4 actually consumed.

### Scaling behavior

| Pool | ADR-0023 budget | Flat cap (ADR-0017) |
|------|----------------|---------------------|
| $500 (G1 launch) | $135 | $500 |
| $1,869.68 (G5) | $504.81 | $500 |
| $3,000 | $810 | $500 |
| $1,000 (after losses) | $270 | $500 |

At G5 the two approaches produce nearly identical budgets — the derivation is self-consistent.
Past G5, budget scales with capital, which is correct behavior under Kelly theory and the
CLAUDE.md ~1,000 evaluations/game design mandate. The budget is a ceiling; at lower pools
the reduced budget simply means fewer bets fire (proportional risk reduction).

### Flat sizing retained as T4 paper policy (hardcoded)

`approved_size = mip` (1 contract at market price) is retained unconditionally in `_run_cycle`.
This is the correct evidence-accumulation design for this stage: flat sizing decouples bet COUNT
from Kelly-sized amount, letting us validate throughput and signal quality without compounding
per-bet sizing noise. It is not a paper-only workaround — it is a deliberate choice that
remains until per-bet Kelly sizing is calibrated and ADR-0018's Phase 8 formula is validated.

### pool_isolated=True hardcoded

`pool_isolated=True` replaces `pool_isolated=PAPER_T4_FLAT_SIZING`. T4 positions must always
be pool-isolated for `_reconstruct_t4_ledger` restart safety (ADR-0022) and for the clean
T1/T4 capital separation invariant.

## Coherence with existing controls

- **ADR-0013 (band budget):** framework unchanged; only the weight constant and formula path change.
- **ADR-0017 (flat sizing paper mode):** superseded. Flat sizing retained as hardcoded T4 paper
  policy, but `PAPER_T4_FLAT_SIZING` environment variable and `PAPER_T4_POOL_USD` are removed.
- **ADR-0021 (incremental delta materiality):** reduced fire rate (~10% of G4 throughput)
  means budget consumption is expected to be well below the $504 budget at G5. GG-026's
  early-exhaustion risk is doubly mitigated: calibrated weight + reduced fire rate.
- **ADR-0022 (realized-value exit credit):** unchanged. `_reconstruct_t4_ledger` and
  `_exit_budget_credit` are unaffected; `pool_isolated` wiring is now unconditional (True).

## Review trigger

Post-G5: compare budget trajectory and `BAND_BUDGET_EXHAUSTED` count against G4 baseline.
If exhaustion still occurs before the final horn with ADR-0021 active, escalate
T4_BAND_WEIGHT recalibration to DS with updated deployment data.
