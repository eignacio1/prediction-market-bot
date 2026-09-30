# Session Handoff — 2026-09-30T00:25Z

<!-- session-meta
task_id: T-588
tier: STANDARD
timestamp: 2026-09-30T00:25:00Z
commit: d837096
one_line_summary: T-588 (39.2): unwired fail-closed is_countable_evidence(); census; T4M-PROJ clean_n 1694->0 computed; GG-317 updated, GG-318/319 registered
gg_touched: GG-317, GG-318, GG-319
adr_touched: none
plan_deliverable_moved: no
-->

**Trigger:** task complete, operator-initiated `/session-end`.
**Last commit:** `d837096` on `session/20260930T001333Z-evidence-boundary` (pushed, NOT merged).

## Strategic Decisions This Session

| Decision | Rationale | Canonical Reference | Owner |
|---|---|---|---|
| T4M-PROJ route forward is a provenance-established allowlist, not a weaker predicate or backfill | Backfill manufactures provenance (GG-228); count is 0 until evidenced | DECISION_LOG 2026-09-30 T-588 | Operator (build allowlist? flip counters?) |

## What changed
- `logic_epoch.py`: `evidence_class()`, `is_countable_evidence()` (unwired); `tests/test_evidence_boundary.py` (21 pass).
- `scripts/evidence_boundary_census.py`; results `T588_evidence_boundary_2026-09-30.md`.
- GG-317 updated (OPEN); GG-318, GG-319 registered.

## Open / not done
- D0: shared-main ff blocked by foreign 0-byte `.git/index.lock` + dirty `OPERATOR_CONSOLE.md`; local main 28 behind. Not deleted. Operator to clear.
- Branch merge: STANDARD (src change) needs PR review; not merged.
- Q2/Q3/Q5 not answered separately; Q7 verified nothing (logs/ gitignored in worktree). Bet count not re-checked.

## One thing pending
Operator decides: allowlist for T4M-PROJ, and which counters adopt `is_countable_evidence()` (about 15 call sites still epoch-only).

## Resume
`git -C "<repo>" fetch && git log origin/session/20260930T001333Z-evidence-boundary` then read the T-588 results summary.
