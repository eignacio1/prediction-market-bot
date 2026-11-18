<!-- session-meta
task_id: T-517
tier: STANDARD
timestamp: 2026-09-03T23:52Z
commit: adf68b3
one_line_summary: APR-0033 accepted (Option 3), Phase 2 re-scoped to moneyline-first LR, HYP-011/EXP-026 pre-registered
gg_touched: none
adr_touched: none
plan_deliverable_moved: no
-->

**Trigger:** Operator sign-off on APR-0033, formally recorded per GG-126 before any downstream edit.

**Last commit:** `adf68b3` (SESSION_CLAIMS.md CLOSED row, manual close-out prior to this /session-end pass)

## Status
Phase 6/7 ACTIVE, MLB pool. No test/gate/portfolio change — doc/governance session only.

## ⚠️ STRATEGIC DECISIONS THIS SESSION

| Decision | Rationale | Owner |
|---|---|---|
| Chat "yes" insufficient; formally moved APR-0033 PENDING→ACCEPTED (Option 3) first | GG-126 discipline | T-517 |
| HYP-011 effect band tighter than HYP-010's (+0.003/+0.015 vs +0.005/+0.025) | Moneyline more efficient than totals (CLAUDE.md) | T-517 |
| HYP-011 scored NET of fill cost or not at all | T-507: ~65% gross-edge haircut on T4M-PROJ | T-517 |

## Tasks Completed This Session
| Item | Result |
|---|---|
| APR-0033 register update | PENDING→ACCEPTED, `a9e70a7` |
| Deliverable 1: re-scope boxes 2.4-2.8 | `MARKET_EXPANSION_ACTION_PLAN.md`, `01643be`; box 2.3 unchanged |
| Deliverable 2: pre-register HYP-011/EXP-026 | `HYP011_*.md` + `HYPOTHESES.md`, `3d19b44` |
| Manual close-out | `7576906`, `adf68b3` |
| TODO_NEXT.md: registered T-518 | uncommitted, this pass |

## ONE THING PENDING
T-518 — execute EXP-026 (HYP-011). Not started; no model fit/scored (LL-009). Re-sync `exp_output/PRICE_ARCHIVE/` from VPS and re-count `KXMLBGAME` archive first; score NET of fill cost only.

## Key Constraints
- HYP-010 (box 2.3) stays INCONCLUSIVE — do not relabel.
- HYP-011/EXP-026: pre-registration only (LL-009).
- `kelly_fraction`/price-archive cron untouched.

## ⚙️ DECISION AUDIT
Captured via existing T-517 DECISION_LOG.md entry (`7576906`), not duplicated into the older table (append-only discipline).

## Resume Command
```bash
cd "/Users/earlignacio/Documents/Claude/Projects/Prediction Markets"
# Next: staff T-518 (execute EXP-026) in a fresh isolated worktree.
```
