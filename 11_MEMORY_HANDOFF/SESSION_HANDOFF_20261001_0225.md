# Session Handoff — 2026-10-01T02:25Z

<!-- session-meta
task_id: EXP-033
tier: STANDARD
timestamp: 2026-10-01T02:25:00Z
commit: 7bdbb9a
one_line_summary: EXP-033 multi-leg coherence: 0 of 24 pre-registered cells survive the toll; ADR-0069 correlation group drafted PROPOSED.
gg_touched: none
adr_touched: ADR-0069
plan_deliverable_moved: no
-->

**Trigger:** wave deliverable complete. **Last commit:** `7bdbb9a` on `session/20261001T015004Z-multileg-coherence` (not merged to main).

## Status
Paper-trading only, no live capital. Tests: 11/11 new. No `src/` change. Bet count not re-checked this close-out.

## Strategic decisions this session
| Decision | Rationale | Reference | Owner |
|---|---|---|---|
| None made; ADR-0069 is PROPOSED only (changes no sizing, activates nothing). DECISION_LOG/GG log not written (44.1 owns them). | Wave ownership rule | ADR-0069, EXP033 results | DS |

## What changed
- `scripts/multileg_coherence.py` + `tests/test_multileg_coherence.py`; pre-registration c9143b1 (frozen before computing).
- Result: 0/24 SURVIVES, 5 NO NET VIOLATION, 19 NOT DISTINGUISHABLE; NFL TEAMTOTAL persistent cluster is a watch item.
- `03_DECISIONS/ADR-0069_game-key-correlation-group.md` PROPOSED; no register row.
- Gaps for 44.1/Wave 45 are listed in the results summary: cost surface GG-325 not landed, bootstrap CIs not implemented, stale EXP-032 text in claim row 695 (GG-322), sparse depth, 20-min cadence. Q1-Q7 not written up this session.

## One thing pending
44.1/Wave 45 registers the gaps; re-run `measure` once GG-325 lands. Branch needs merge by operator/44.1 routing.

## Resume
`git -C PM-worktrees/20261001T015004Z-multileg-coherence log -3` then read `05_RESEARCH_EXPERIMENTS/RESULTS_SUMMARIES/EXP033_RESULTS_multileg_coherence_2026-10-01.md`.
