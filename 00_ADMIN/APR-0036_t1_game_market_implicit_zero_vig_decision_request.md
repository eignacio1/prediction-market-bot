# APR-0036 — T1 game markets gate on an implicit `vig=0.00` assumption; T2/T4 do not (T-566/GG candidate)

**Status:** DECISION REQUEST — not adjudicated at drafting time; presented options, did not select one.
**Touches (if accepted):** `run_t1_mlb_game_market.py`, `run_t1_nfl_game_market.py` (their gate arithmetic — `edge_yes = p_estimate - market_implied_prob`, `EDGE_THRESHOLD = 0.02`). No file is touched by this document itself; it is analysis and a decision request only. Does not touch `risk.py`, `execution_bands.py`, `kelly_fraction`, any gate threshold, `VIG_CEILING`, or T2/T4's already-live-measured vig logic.
**Drafted:** 2026-09-23, T-566.
**Prior context:** T-566's brief was to replace assumption with measurement for the C4 edge condition's `vig` term, grounded in the price archive, without changing the gate itself. Full supporting analysis: `05_RESEARCH_EXPERIMENTS/RESULTS_SUMMARIES/T566_RESULTS_vig_grounding_from_archive.md` (this session).

---

## The gap

T-566's code inventory (Deliverable 1) found three distinct conventions for
the same `vig` concept across the bands that trade the same underlying
resource (Kalshi bid/ask spread):

- **T4 MLB** (`KXMLBHIT`, live): charges the full live-fetched spread as a
  cost every cycle — `gross_edge = p_t4 - mip - vig`.
- **T2 MLB** (`KXMLBHIT`, same-day): charges half the live-fetched spread —
  `half_spread`, the economically standard one-sided entry cost.
- **T1 MLB/NFL game markets** (11 series across two run scripts): charges
  **nothing**. `edge_yes = p_estimate - market_implied_prob` has no cost
  term at all — an implicit, unstated assumption that entering a position
  costs zero.

T2 and T4 both fetch and apply a real, quote-derived spread every cycle —
there is no assumption to ground for those two; the number they use *is*
the measurement. T1 is the one genuine case where a code path assumes a
fixed value (zero) for something the archive shows is real and nonzero.

**Measured size of the gap (Deliverable 2/3, archive-derived, 54 days /
1,824,195 rows, `half_spread` — the economically correct one-sided cost,
matching T2's own convention):**

| series | median half_spread (typical gap) | p90 half_spread (tail gap) | vs. `EDGE_THRESHOLD=0.02` |
|---|---:|---:|---|
| KXMLBGAME | 0.0050 | 0.0250 | tail 1.25x |
| KXMLBSPREAD | 0.0050 | 0.0150 | tail < threshold |
| KXMLBTOTAL | 0.0050 | 0.0150 | tail < threshold |
| KXMLBTEAMTOTAL | 0.0150 | 0.1050 | median 0.75x, tail 5.25x |
| KXMLBF3 | 0.0200 | 0.1950 | median = threshold, tail 9.75x |
| KXMLBF5 | 0.0100 | 0.1250 | median 0.5x, tail 6.25x |
| KXMLBF7 | 0.0200 | 0.2950 | median = threshold, tail 14.75x |
| KXNFLGAME | 0.0050 | 0.0150 | tail < threshold |
| KXNFLSPREAD | 0.0100 | 0.0250 | median 0.5x, tail 1.25x |
| KXNFLTOTAL | 0.0100 | 0.0200 | median 0.5x, tail = threshold |
| KXNFLTEAMTOTAL | 0.0200 | 0.0850 | median = threshold, tail 4.25x |

For the partial-game series (`KXMLBF3/F5/F7`) and the team-total series
(`KXMLBTEAMTOTAL`, `KXNFLTEAMTOTAL`), the *typical* unmeasured cost already
equals or approaches the entire edge threshold, and the *tail* cost runs
4-15x the threshold. A bet approved at a marginal edge in those series
could, under real median-to-tail spread conditions, have zero or negative
true edge once a spread-aware cost is applied — the gate as written cannot
distinguish that case from a genuinely wide, real edge.

**This document does not conclude T1 should adopt T2's exact half-spread
formula, or any specific number.** Per the governing task's constraints, no
cross-family recommendation is drawn from this single finding — T1, T2, and
T4 differ in more than their cost-term convention (time horizon, decision
tree complexity, band-activation status per `EXECUTION_BANDS.md`), and this
document does not have evidence about those other differences. What it
establishes is narrower and load-bearing on its own: **T1's zero-cost
assumption is unmeasured, and the archive shows the true cost is not
uniformly small relative to T1's own threshold.**

---

## What this document does not do

This is analysis and a decision request. It does not: change
`EDGE_THRESHOLD`, add a cost term to any gate, touch `kelly_fraction`,
promote a cell, submit an order, or restart a service. It does not touch
`VIG_CEILING`, T2's or T4's already-live vig measurement, or the
price-capture window/cadence. It does not cite ADR-0046's Brier/ECE
baselines as a validity reference for this finding. `T566_RESULTS_...md`
carries the full measured detail this document summarizes.

---

## Options (presented, not selected)

**Option 1 — Keep T1's gate as-is; treat the zero-cost assumption as an
accepted, documented simplification.** No superseding document required.
Cost: made explicit, in writing, for the first time — T1's approvals in the
sparser/wider series (`F3`, `F5`, `F7`, both `TEAMTOTAL` series) carry an
unmeasured cost that can rival or exceed the entire edge threshold at the
tail. This option is honest about the cost but does not change anything
about whether the operator is comfortable carrying it.

**Option 2 — Add a measured half-spread cost term to T1's gate, mirroring
T2's convention (`edge_yes = p_estimate - market_implied_prob - half_spread`),
sourced from the same live Kalshi fetch T1 already performs for its
position-sizing stratum (confirmed in Deliverable 1: `vig`/`half_spread`
are already fetched live in T1's code path today, just unused for gating).
This would make T1's cost treatment consistent with T2's for the same
underlying mechanism. **Requires a superseding ADR** (Hard Rule 3 — this
changes live gate arithmetic) and DS sign-off before any implementation;
this document does not select or size the specific formula.

**Option 3 — Add a per-series, archive-derived static offset instead of a
live fetch**, using the measured medians in the table above (or a
different derivation, e.g. a fixed multiple of median to buy tail margin)
as a per-`MarketType` constant rather than a per-cycle live measurement.
Cheaper to implement than Option 2 (no live-fetch dependency added to T1's
hot path) but reintroduces the same "assumption vs. reality" gap this
document exists to close, one level down — the constant would need its own
re-derivation cadence as market conditions shift, the way `VIG_CEILING`
did. Not developed further here; named as a lower-fidelity alternative to
Option 2.

**Option 4 — Something else the operator surfaces, not enumerated above** —
e.g., applying the fix only to the series where the tail gap is largest
relative to threshold (`F3`, `F5`, `F7`, both `TEAMTOTAL` series) while
leaving the tighter series (`SPREAD`, `TOTAL`, `GAME`) as-is, given their
tail gap already sits below `EDGE_THRESHOLD`. Not developed here; flagged
as a live possibility.

---

## Register row (for session 32.3 / whoever owns `GOVERNANCE_GAP_LOG.md` this wave)

Candidate entry, not registered by this session (T-566 does not own
`GOVERNANCE_GAP_LOG.md` this wave): *T1 MLB/NFL game-market gates
(`run_t1_mlb_game_market.py`, `run_t1_nfl_game_market.py`) apply no
vig/spread cost term — implicit assumption of zero — while T2 and T4 both
measure live spread every cycle for the same underlying Kalshi bid/ask
mechanism. Archive-measured gap (54 days, `T566_RESULTS_...md`): median
0.005-0.02pp, p90 tail 0.015-0.295pp depending on series, largest relative
to `EDGE_THRESHOLD=0.02` in `KXMLBF3/F5/F7` and both `TEAMTOTAL` series.
See APR-0036 for options; DECISION REQUEST, not yet adjudicated.*
