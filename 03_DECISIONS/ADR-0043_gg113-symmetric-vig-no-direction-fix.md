# ADR-0043 — GG-113: NO-Direction Vig Must Be a Symmetric Cost, Not a Sign-Flipped Credit (ACCEPTED)

**Status:** ACCEPTED — DS sign-off received (operator, Earl Ignacio, 2026-07-14; see DECISION_LOG.md 2026-07-14 entry).
**Date:** 2026-07-14
**Session:** GG-113 fix (Window 1), worktree `session/20260714T050514Z-gg113-vig-sign-fix`.
**Operator:** Earl Ignacio
**Scope:** MLB T4M-PROJ live gating math (`run_t4_mlb_live.py`) and its paper-trade write path (`paper_trader.py::open_position`). No change to `risk.py` `_HARD_LIMITS`, no change to model class (ADR-0004), no NBA impact, no change to vig *magnitude* convention (see Open items).
**Supersedes / relates:** Corrects a defect introduced by GG-087's fix (dark, no ADR of its own). Relates to GG-077 (the original sign-convention bug GG-087 was designed to avoid reintroducing), GG-113 (this ADR's governing gap, OPEN → RESOLVED on merge), T-333/H5 (the parity check that validated internal consistency but not economic correctness — see Context), ADR-0024/APR-0024 (commercial validation gate — this fix causes a `clean_n`/logic-epoch reset, addressed below), `run_exp017.py` (the pre-existing, correct vig convention this fix aligns to).

---

## Context

`run_t4_mlb_live.py` computes the YES-frame gross edge as `gross_edge = p_t4 - mip - vig` — vig is baked in once, as a cost, with a fixed sign. GG-087's fix made NO-direction bets actionable by setting `directional_gross_edge = -gross_edge` when `gross_edge < 0`. Algebraically:

```
-gross_edge = -(p_t4 - mip - vig) = (mip - p_t4) + vig
```

This flips vig from a subtracted cost into an added credit for every NO bet. The codebase already has an established, correct convention for this — `run_exp017.py`'s `compute_pnl_unit()` treats vig as a symmetric cost via `half_vig`, added to `price_paid` identically on both YES and NO sides. Vig is a bid-ask spread cost; it must never flip sign with direction.

`paper_trader.py::open_position()` independently reproduced the identical bug in its own direction-effective edge computation (`_directional_gross = gross_edge if direction == "YES" else -gross_edge`), for the same algebraic reason.

**Why this survived GG-087's own review:** GG-087's fix solved the direction-flip problem for the *signal* term (`p_t4 - mip`) but did not separately account for the fact that vig was already folded into the same expression with its own fixed sign — fixing one term accidentally broke the other. T-333's H5 check (2026-07-11) explicitly verified "vig is used consistently... never sign-flipped... across the YES/NO direction split," but that check validated internal self-consistency with the live (buggy) code, not economic correctness against the project's own pre-existing `run_exp017.py` convention. Two different bars; only the weaker one was checked.

**Impact (measured, T-344 diagnostic, `scripts/run_t344_vig_sign_diag.py` against the live VPS clean_n=412 ledger, 2026-07-12):** 337/412 (81.8%) of T4M-PROJ's clean_n resolved book is NO-direction. Every one of those bets was gated on an edge inflated by `+2×vig` relative to the correct symmetric-cost treatment. Recomputing with the corrected formula shows 137/412 (33.3%) of clean_n positions have true (corrected) edge ≤ 0 — roughly a third of the currently-approved book would not have cleared `MIN_EDGE_TO_APPROVE=0.04` gating under correct vig treatment. Note this does **not** explain GG-105 (a separate anti-predictive edge/win-rate pattern found the same session) — correcting this bug strengthens that pattern rather than resolving it (`05_RESEARCH_EXPERIMENTS/RESULTS_SUMMARIES/T344_GG105_DECOMPOSITION_MEMO.md`). This is an independent correctness bug, not the cause of GG-105.

**DS sign-off (2026-07-14, operator, quoted verbatim from DECISION_LOG.md):** "stop accumulating based on biased formulas... it's so that our process and formulaic design is stress-tested and held to a relentless standard of precision without letting it cut corners." The operator reviewed the tradeoff — fix now (accepting T4M-PROJ's `clean_n`/logic-epoch reset) vs. defer (keep accumulating on a formula known to inflate edge on 81.8% of the book) — and chose to fix now. This decision formally supersedes "accumulate toward Tier 2 as the dominant lever" (T-333/DECISION_LOG 2026-07-07) with calibration-correctness-first priority: sample count is not to be optimized at the expense of formula correctness, and a `clean_n` reset is an accepted cost, not a failure.

## Decision

**D1 — Fix vig to a symmetric, direction-independent cost in both write paths.**

`run_t4_mlb_live.py` (the live gating decision): recompute the NO-direction edge from the signal term directly, rather than algebraically re-deriving it from the already vig-inclusive `gross_edge`:

```python
elif gross_edge < 0.0:
    direction = "NO"
    directional_gross_edge = (mip - p_t4) - vig
```

`paper_trader.py::open_position()` (the paper-trade write path): correct the sign-flip to also re-subtract vig, since a plain `-gross_edge` flip both flips the signal term (correct) and flips vig's sign (incorrect, since `gross_edge` already has vig subtracted once with a fixed sign):

```python
_directional_gross = gross_edge if direction == "YES" else (-gross_edge - 2.0 * vig)
```

Both forms are algebraically equivalent — `-gross_edge - 2*vig = -(p-mip-vig) - 2*vig = (mip-p) - vig` — and match `run_exp017.py`'s established convention of vig as a cost applied identically regardless of direction.

**D2 — Advance `CURRENT_LOGIC_EPOCH` and accept the resulting `clean_n` reset.** This fix changes which bets clear `MIN_EDGE_TO_APPROVE` gating for NO-direction bets, so pre-fix and post-fix bets are not comparable under the same epoch. Per the DS sign-off above, this is an accepted, deliberate cost — `logic_epoch.py` must report the reset cleanly (new epoch, `clean_n` starts over) rather than silently carrying stale pre-fix `clean_n` forward as if it were computed under the corrected formula.

**D3 — T1 MLB's parallel instance of this bug (`run_mlb_paper_trade.py::_directional_edge()`) is explicitly OUT OF SCOPE for this ADR.** T1 is the active/primary G6 book and requires its own fresh, explicit DS sign-off before any live-formula change (Hard Rule 3 / ADR-0039 Tier B precedent) — this ADR's sign-off was scoped to T4M-PROJ only. Registered separately as GG-119 (OPEN, deferred, not fixed).

## Consequences

- **Positive:** T4M-PROJ's live gating and paper-trade write path now match the project's own established, correct vig convention. Removes a structural edge-inflation bias affecting 81.8% of the resolved book. Closes the gap between T-333/H5's "internally consistent" bar and actual economic correctness — the distinction this ADR exists to draw.
- **Negative / cost (accepted per DS sign-off):** `CURRENT_LOGIC_EPOCH` advances, resetting T4M-PROJ's `clean_n` to zero under the new epoch. APR-0024's per-band `n*` ETA for T4M-PROJ (previously ~0.9 weeks at clean_n=338/n*=787) restarts from zero clean_n post-fix. This is explicitly not a failure — it is the cost of correcting a formula that was inflating edge on the majority of the book, and continuing to accumulate on the biased formula was the rejected alternative.
- **Explicitly deferred, not resolved by this ADR:** GG-113's Resolution field also flagged a **separate, secondary magnitude question** — `run_t4_mlb_live.py` and `paper_trader.py` use *full* vig as the cost, while `run_exp017.py`'s convention uses *half*-vig (reflecting that a single-sided execution only crosses half the spread from mid). This ADR fixes the **sign** only; it does not touch vig magnitude in either direction. The magnitude question remains open and is not authorized for change under this sign-off — a future task should scope and seek separate sign-off for it if warranted.

## Evidence / reproducibility

- Fix commits: `run_t4_mlb_live.py` (session branch `gg113-rebase-clean`, cherry-picked from `3abab4e`, landed as `fb13166`); `paper_trader.py` (this session, committed alongside this ADR).
- Regression tests: `tests/test_run_t4_mlb_live.py::TestRunCycle::test_no_direction_vig_is_symmetric_cost_not_credit` (pins the economically correct `fee_net_edge` value against a live `_run_cycle()` invocation, deriving expected `p_t4` via the same `_compute_ab_remaining`/`p_hits_gte_threshold` functions the code uses rather than hardcoding it); `tests/test_paper_trader.py::TestOpenPosition::test_fee_net_edge_is_direction_effective_for_no_bet` (updated — previously pinned the pre-fix/buggy value as "expected"; now pins `-gross_edge - 2*vig - fee`). Full suites: `tests/test_run_t4_mlb_live.py` (177 passed), `tests/test_paper_trader.py` (45 passed).
- Diagnostic: `scripts/run_t344_vig_sign_diag.py` (T-344, 2026-07-12) — the 81.8%/33.3% impact figures cited above.
- Prior finding memo: `05_RESEARCH_EXPERIMENTS/RESULTS_SUMMARIES/T344_GG105_DECOMPOSITION_MEMO.md`.

## Open items

- GG-119 (T1 MLB parallel bug in `run_mlb_paper_trade.py::_directional_edge()`) remains OPEN, registered, deferred — requires its own DS sign-off, out of scope here.
- The full-vig-vs-half-vig magnitude question (GG-113 Resolution item 2) remains unresolved and unauthorized for change under this ADR.
- Post-fix live verification (VPS deploy, re-pull ledger, confirm `clean_n` actually reset) is tracked as a Window 1 deliverable, not part of this ADR's text.
