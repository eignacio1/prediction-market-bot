# Session Handoff — 2026-09-30T01:15Z

<!-- session-meta
task_id: T-592
tier: MICRO
timestamp: 2026-09-30T01:15:00Z
commit: b9b21ab
one_line_summary: T-592 provenance allowlist: 1,694/1,694 T4M-PROJ clean rows attributable via inert 13-window allowlist; nothing flipped.
gg_touched: none
adr_touched: none
plan_deliverable_moved: no
-->

**Trigger:** task complete. **Last commit:** `b9b21ab` on `session/20260930T005212Z-provenance-allowlist`.

## Strategic Decisions This Session
| Decision | Note |
|---|---|
| None — implementation-only session. | Gaps G-A..G-E recorded in results summary only (GGL/DECISION_LOG owned by 40.1). |

## What changed
- New: `05_RESEARCH_EXPERIMENTS/provenance/t4m_proj_provenance_allowlist.json` (inert, 13 cited windows), `scripts/provenance_allowlist_recompute.py`, `tests/test_provenance_allowlist.py` (6 tests), `RESULTS_SUMMARIES/T592_provenance_allowlist_2026-09-30.md`.
- Result: countable 0 -> 1,694 (all clean rows; 43.2% of 3,923 raw) under overlay; predicate, ledgers, logic_epoch untouched.
- Collision: T-592 was ALSO claimed at 00:53:30Z by the 40.1 doctrine session (GG-162 race). Reconcile IDs.

## One thing pending
Operator decision: accept allowlist caveats L1-L4 and register identity, AND fix the run path/ledger builder so new rows carry model_identity. Reflog evidence ages out ~2026-10-29 — snapshot it before then.

## Resume
`cd PM-worktrees/20260930T005212Z-provenance-allowlist && python3 scripts/provenance_allowlist_recompute.py --help`
