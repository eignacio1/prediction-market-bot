# APR-0028 — GG-122: T2 MLB Full-Vig-vs-Half-Spread Magnitude Fix — Decision Request (PROPOSED)

**Status:** PROPOSED — awaiting DS sign-off (operator, Earl Ignacio). Not yet authorized. No code has been changed under this request.
**Date:** 2026-07-15
**Session:** T-368, isolated worktree `session/20260715T200705Z-gg-t2-half-spread-audit`, drafted per explicit instruction: GG-122 must be escalated via a formal decision request, not resolved unilaterally (Hard Rule 3 — this touches live gating math on an active MLB band).
**Operator:** Earl Ignacio
**Scope of this request:** MLB T2 same-day gating math (`run_t2_mlb_sameday.py`'s local `gross_edge`/`net_edge` computation) only. Does not propose any change to T1, T3, or T4M-PROJ. Does not propose any change to `risk.py` `_HARD_LIMITS`, model class (ADR-0004), or NBA. Does not overlap with ADR-0045 (T1's separate NO-direction sign-flip fix, still PROPOSED, unrelated bug class).
**Supersedes / relates:** GG-122 (OPEN, this request's governing gap — diagnosed and quantified 2026-07-15, T-368, but explicitly not fixed pending this sign-off), GG-119 (which first flagged this as an out-of-scope adjacent observation), ADR-0045 (Proposed D3, which named this exact question as deliberately deferred future work), `run_exp017.py` (the pre-existing, correct symmetric-cost convention this aligns to), `kalshi_client.py::PlayerMarket` (the dataclass whose own docstring documents `half_spread` as "the cost to enter").

---

## Context

GG-119's diagnosis (2026-07-15, T-362) confirmed T1's NO-direction sign-flip bug and, in the course of that work, re-confirmed an earlier observation from GG-113/ADR-0043: T2's local gating formula in `run_t2_mlb_sameday.py` subtracts the FULL `vig` (bid-ask spread) as its cost term, where the established convention — `run_exp017.py`, and T1's own formula — subtracts only `half_spread` (`vig / 2.0`), the actual one-sided transaction cost. ADR-0045 named this "Proposed D3" and explicitly deferred it as its own separately-scoped question.

**This session (T-368) completed that diagnosis, not yet a fix:**

- **Confirmed via direct code read.** `run_t2_mlb_sameday.py` (~lines 416-423): `vig = current_mkt.vig; gross_edge = p_calibrated - mid - vig; net_edge = gross_edge - kalshi_fee`. Compare `run_mlb_paper_trade.py` (T1, ~lines 891-892): `half = mkt.half_spread; gross_edge = p_calibrated - mid - half`. `kalshi_client.py::PlayerMarket`'s own docstring: "vig is the full spread (yes_ask - yes_bid); half-spread is the cost to enter." T2's use of `.vig` directly is an unambiguous deviation from the codebase's own documented convention.
- **Independently re-confirmed T2 has no NO-direction branch** — `PAPER_YES_ONLY` defaults `"true"`, no `"NO"`/`EDGE_NO` string anywhere in the file. This is NOT the GG-113/GG-119 sign-flip pattern; it is a magnitude-only bug, and it is **conservative-direction** — it under-computes edge and can cause T2 to pass on bets that actually clear the gate under the correct formula, costing profit rather than admitting bad bets.
- **Quantified** (`scripts/run_t368_gg122_t2_vig_magnitude_diag.py`, full output `exp_output/T368-GG122-T2-VIG-MAGNITUDE-DIAG/t2_vig_magnitude_diag_results.json`):
  - T2's resolved ledger is **n=2** (both YES, both WIN) — far too small for a dollar-denominated realized-P&L estimate analogous to GG-119's T1 finding (n=259); none is asserted here.
  - Structural gating impact assessed instead across **39 evaluated candidates** from T2's 15 most-recent daily report files (2026-07-01 through 2026-07-15), reconstructing `vig` algebraically from each row's stored fields. **1 row** (Ketel Marte, 2026-07-12) flips PASS→YES at T2's own local `EDGE_YES=0.02` gate under correction (buggy 0.016 → corrected 0.021). **0 of 39 rows** would additionally clear the binding `MIN_EDGE_TO_APPROVE` (0.04, `risk.py` CHECK 3) — the actual determinant of whether a bet is placed. **Zero realized bet-outcome changes in the observed sample.**
  - **One near-miss**: Junior Caminero (2026-07-04), corrected edge 0.0345, only 0.0055 below the 0.04 floor.
  - Reconstructed `half_spread` across all 39 rows: mean $0.0085, median $0.01, max $0.015 — small but real and nonzero on every evaluated row.
- **Bottom line:** the bug is real and structurally confirmed, but currently produces zero observed changes to actual bet placement — the risk is present but not yet realized, and would grow on any day with a wider vig.

## Decision requested

This request proposes — but does **not** enact — the following, mirroring ADR-0045's D1/D2 shape:

**Proposed D1 — Switch T2's cost term from full `vig` to `half_spread`:**

```python
# run_t2_mlb_sameday.py, current (buggy):
#   vig = current_mkt.vig
#   gross_edge = p_calibrated - mid - vig
#
# Proposed fix, matching run_exp017.py / T1's convention:
half_spread = current_mkt.half_spread
gross_edge = p_calibrated - mid - half_spread
```

(`net_edge = gross_edge - kalshi_fee` and the `direction = "YES" if net_edge > EDGE_YES else "PASS"` gate are unchanged — only the cost-term magnitude changes.)

**Proposed D2 — Advance `CURRENT_LOGIC_EPOCH` and accept the resulting T2 `clean_n` reset.** Same rationale as ADR-0045 §D2: pre-fix and post-fix T2 evaluations are not directly comparable, since the fix changes which candidates clear gating. T2's `clean_n` is currently near-zero (n=2 resolved), so this reset is low-cost relative to T1's much larger `n*` — a materially smaller cost/benefit tradeoff than ADR-0045 faced for T1.

## Decision — awaiting Earl

**This section is intentionally blank pending DS review.** Earl needs to decide:

1. Authorize the T2-scoped fix (Proposed D1) — yes/no, and if yes, on what timeline?
2. Accept the `clean_n` reset cost (Proposed D2), given T2's currently tiny resolved sample makes this a low-cost reset relative to T1's.
3. Whether the currently-zero realized impact (0 of 39 observed rows changes bet placement) means this can wait for a batched fix alongside ADR-0045, or should be treated with its own urgency given the real, nonzero, structural exposure on every evaluated row.

Once a decision is made, this document should be updated in place — status flipped to ACCEPTED or REJECTED, the "Decision" section filled with the verbatim ruling, and GG-122's `GOVERNANCE_GAP_LOG.md` entry updated to reflect the outcome. If accepted, implementation (code change, regression tests, epoch bump, VPS deploy/verification) is future work, not part of this document.

## Evidence / reproducibility

- Diagnosis: `scripts/run_t368_gg122_t2_vig_magnitude_diag.py` (T-368, 2026-07-15), full output `exp_output/T368-GG122-T2-VIG-MAGNITUDE-DIAG/t2_vig_magnitude_diag_results.json`.
- Structural template: ADR-0045 (`03_DECISIONS/ADR-0045_gg119-t1-vig-sign-fix-decision-request.md`), the T1 decision request this mirrors.
- Governing gap: GG-122, `03_DECISIONS/GOVERNANCE_GAP_LOG.md`.
- `run_exp017.py` / `kalshi_client.py::PlayerMarket.half_spread` — the established, correct symmetric-cost convention this aligns to.

## Open items

- No code has been changed under this request. `run_t2_mlb_sameday.py` remains in its pre-fix (buggy) state pending sign-off.
- If accepted, confirm whether `paper_trader.py::open_position()`'s shared write path needs any T2-specific consideration analogous to GG-113's band-gating note (initial read suggests no — T2's stored `fee_net_edge` is independently recomputed there and was not part of this diagnosis's scope; verify at implementation time).
- This request does not touch T1 (ADR-0045, separate sign-off track) or T4M-PROJ (ADR-0043, already resolved).
