# ADR-0045 — GG-119: T1 MLB NO-Direction Vig Sign Fix — Decision Request (PROPOSED)

**Status:** ACCEPTED — DS sign-off Earl Ignacio 2026-07-15.
**Date:** 2026-07-15
**Session:** GG-odd-burndown (T-368), drafted per explicit standing instruction: GG-119 must be escalated via a formal ADR/APR decision request, not resolved unilaterally (Hard Rule 3 — this touches live gating math on the primary/active G6 book).
**Operator:** Earl Ignacio
**Scope of this request:** MLB T1 live gating math (`run_mlb_paper_trade.py::_directional_edge()`) only. Does not propose any change to T2, T3, or T4M-PROJ (T4M-PROJ's parallel bug is already fixed, ADR-0043/GG-113). Does not propose any change to `risk.py` `_HARD_LIMITS`, model class (ADR-0004), vig *magnitude* convention, or NBA.
**Supersedes / relates:** GG-119 (OPEN, this ADR's governing gap — diagnosed and quantified 2026-07-15, T-362, but explicitly not fixed pending this sign-off), ADR-0043/GG-113 (the T4M-PROJ precedent this request mirrors), ADR-0024/APR-0024 (commercial validation gate — this fix would cause a T1 `clean_n`/logic-epoch reset, addressed below), `run_exp017.py` (the pre-existing, correct symmetric-vig convention both this and ADR-0043 align to).

---

## Context

GG-113/ADR-0043 (2026-07-14) found and fixed a bug in T4M-PROJ's live gating math: `directional_gross_edge = -gross_edge` for NO-direction bets algebraically flips vig from a subtracted cost into an added credit, because `gross_edge` already has vig subtracted once with a fixed sign before the negation. ADR-0043 explicitly scoped T1's parallel instance of this pattern out — Hard Rule 3 requires T1, as the active/primary G6 gate-lever book, to clear its own fresh sign-off before any live-formula change, regardless of how mechanically similar the bug is.

**T-362 (2026-07-15, this burn-down session's predecessor, isolated worktree `session/20260715T054123Z-gg119-t2-vig-diagnosis`) completed that diagnosis, not yet a fix:**

- **T1 CONFIRMED.** Direct code read of `run_mlb_paper_trade.py::_directional_edge()` shows the identical algebraic pattern: `directional_gross = gross_edge if direction=="YES" else -gross_edge; return directional_gross - kalshi_fee`. This negates the whole vig-inclusive `gross_edge` term for NO bets, flipping the embedded `half_spread` (vig/2) cost into a credit. `kalshi_fee` is handled correctly (uniform subtraction, never flipped) — only the half-spread term is affected.
- **Empirically quantified against the live T1 resolved ledger** (`paper_portfolio_mlb.json`, band="T1", n=259 resolved, pulled 2026-07-15; `scripts/run_t362_gg119_t1_vig_diag.py`, full output `exp_output/T362-GG119-T1-VIG-DIAG/t1_vig_sign_diag_results.json`): all 248 NO-direction resolved bets show edge inflation of exactly `2 × half_spread` (verified per-row against real data, not a synthetic derivation).
- **The concrete, dollar-denominated finding:** 74 of those 248 NO bets (29.84% of NO bets, 28.57% of the entire resolved T1 book) only cleared `MIN_EDGE_TO_APPROVE` (0.04, `risk.py` CHECK 3) because of the inflation — under the corrected symmetric-vig formula their edge falls below 0.04 (six even go negative, -0.0007 to -0.0286), meaning they should never have been approved/placed at all. That 74-bet subgroup's aggregate realized P&L is **-$48.26** (36 wins / 38 losses, a net-losing subgroup), against a T1 book-wide total of +$34.56 across all 259 resolved positions. The bug is not inflating T1's apparent P&L — it is admitting a batch of marginal/negative-edge bets that on net lose money. A corrected book (removing the falsely-admitted subgroup's drag) would show materially higher realized P&L (~$82.82 back-of-envelope) — a direct G6/APR-0024 integrity concern, since T1 is the primary gate-lever book.
- **T2 was ruled out** for this specific sign-flip pattern (structurally cannot occur — `run_t2_mlb_sameday.py` has no NO-direction branch at all). Not part of this request.
- Monotonicity/tercile check under the corrected framing shows no strong directional pattern either way (pos-edge win rate 50.0% vs neg-edge 52.0%, Fisher p=1.0) — this is **not** GG-105's anti-predictive signature. The two findings are independent; fixing this does not touch GG-105, and GG-105's own remediation (APR-0025) is separately gated and untouched by this request.

**Why a fix has not already been applied:** T-362's own scope was diagnosis-only (Window 1 instruction). This burn-down session inherits that discipline: Hard Rule 3 requires this to go to Earl as a decision request, not be resolved inline in `GOVERNANCE_GAP_LOG.md`.

## Decision requested

This ADR proposes — but does **not** enact — the following, mirroring ADR-0043's D1/D2 shape exactly, applied to T1 instead of T4M-PROJ:

**Proposed D1 — Fix `_directional_edge()`'s NO branch to recompute the signal term directly, rather than negating an already vig-inclusive `gross_edge`:**

```python
# run_mlb_paper_trade.py::_directional_edge(), current NO branch (buggy):
#   directional_gross = -gross_edge
#   return directional_gross - kalshi_fee
#
# Proposed fix, mirroring ADR-0043's T4M-PROJ pattern:
elif direction == "NO":
    directional_gross = -gross_edge - 2.0 * half_spread
    return directional_gross - kalshi_fee
```

(`-gross_edge - 2*half_spread` is algebraically equivalent to recomputing `(mid - p) - half_spread` directly from the signal term, matching `run_exp017.py`'s established symmetric-cost convention — the identical derivation ADR-0043 §D1 used for T4M-PROJ, substituting T1's `half_spread` naming for T4M-PROJ's `vig`.)

Note `paper_trader.py::open_position()`'s shared write path is **already band-gated** to T4M-PROJ only (ADR-0043 D1/D3) — T1 currently falls through to the `else: _directional_gross = -gross_edge` branch, i.e. the pre-fix formula, by design. If this ADR is accepted, that band gate must be extended to include `T1` alongside `T4M-PROJ` so the ledger write path and the gating decision path move together; a stray write-path fix without the matching gating fix (or vice versa) is exactly the scope-leak failure mode ADR-0043 §"Self-correction" already caught once for T4M-PROJ, and `tests/test_approval_path_invariants.py::TestFeeSignInvariance` should continue to enforce agreement between the two paths for T1 specifically once extended.

**Proposed D2 — Advance `CURRENT_LOGIC_EPOCH` and accept the resulting T1 `clean_n` reset.** Same rationale as ADR-0043 §D2: pre-fix and post-fix T1 bets are not comparable under the same epoch, since the fix changes which NO-direction bets clear `MIN_EDGE_TO_APPROVE` gating. Per APR-0024, this resets T1's `clean_n` toward its own `n*` (T1's `n*` is far larger than T4M-PROJ's — per CLAUDE.md's 2026-07-11 snapshot, T1 `n*≈2,322` vs T4M-PROJ's `n*≈787` — so this reset is proportionally a much larger cost on the primary gate-lever book's own ETA to `clean_n ≥ n*`, a materially different cost/benefit shape than ADR-0043 faced and the main reason this needs Earl's own judgment rather than inheriting ADR-0043's precedent by analogy alone).

**Proposed D3 (open question, explicitly not decided here) — whether to also open a separately-scoped look at T2's full-vig-vs-half-vig magnitude question**, noted as an adjacent-but-distinct, out-of-scope observation in GG-119's Impact field (T2 uses full `vig` as its cost term where T1/`run_exp017.py` use `half_spread`/half-vig — a magnitude question, not a sign-flip, and conservative-direction, i.e. it costs the book too much edge rather than too little). This ADR does not request authorization for that; it is flagged so it is not lost, matching how ADR-0043 flagged its own analogous open item.

## Decision — Earl Ignacio, 2026-07-15

Earl reviewed and approved GG-119/ADR-0045 in full:

1. **Authorized the T1-scoped fix (Proposed D1), immediate.** Implement exactly as specified — fix `run_mlb_paper_trade.py::_directional_edge()`'s NO branch, and extend `paper_trader.py::open_position()`'s band gate from `{"T4M-PROJ"}` to include `T1` so the ledger write path and the gating decision path move together, mirroring ADR-0043/GG-113's T4M-PROJ precedent.
2. **Accepted the resulting T1 `clean_n` reset (Proposed D2)**, notwithstanding T1's much larger `n*` (~2,322 vs T4M-PROJ's ~787) making this a proportionally larger ETA cost than ADR-0043 accepted for T4M-PROJ. Correctness of the gating formula on the primary/active G6 gate-lever book takes priority over preserving accumulated `clean_n` on a formula now confirmed to admit a batch of marginal/negative-edge NO bets it should not have.
3. **Separately authorized the T2 full-vig-vs-half-vig magnitude investigation (Proposed D3)**, to be handled by a parallel, independently-scoped session — not this one. This ADR's implementation touches T1 files only; T2 files are explicitly out of scope here.

Status flipped to ACCEPTED. Implementation (code change, regression tests, epoch bump, VPS deploy/verification) proceeds under T-371.

## Evidence / reproducibility

- Diagnosis: `scripts/run_t362_gg119_t1_vig_diag.py` (T-362, 2026-07-15), full output `exp_output/T362-GG119-T1-VIG-DIAG/t1_vig_sign_diag_results.json`.
- Precedent / structural template: ADR-0043 (`03_DECISIONS/ADR-0043_gg113-symmetric-vig-no-direction-fix.md`), the accepted T4M-PROJ fix this request mirrors.
- Governing gap: GG-119, `03_DECISIONS/GOVERNANCE_GAP_LOG.md`.
- `run_exp017.py::compute_pnl_unit()` — the established, correct symmetric-vig-as-cost convention both this and ADR-0043 align to.

## Open items

- Implemented 2026-07-15 (T-371, commit `53a9208`): `run_mlb_paper_trade.py::_directional_edge()` fixed, `paper_trader.py::open_position()`'s band gate extended to `{"T4M-PROJ", "T1"}` (T1 uses `-gross_edge - 1.0*vig`, distinct coefficient from T4M-PROJ's `-2.0*vig`, since T1's `gross_edge` embeds only `half_spread` while T4M-PROJ's embeds the full `vig`).
- `CURRENT_LOGIC_EPOCH` advanced to 5 (`logic_epoch.py`), referencing commit `53a9208` directly — no self-correction needed since the write-path fix and the band-gate extension landed together in one commit.
- T2's full-vig-vs-half-vig magnitude question (Proposed D3) remains a separate, parallel-session investigation — not part of this ADR's implementation.
