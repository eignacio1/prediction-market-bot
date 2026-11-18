# SESSION HANDOFF — 2026-08-20T00:43Z

<!-- session-meta
task_id: T-470
tier: MICRO
timestamp: 2026-08-20T00:43:19Z
commit: e2b5f9e
one_line_summary: T-470: outcome-store extended to 08-07..08-15, all 532/532 corrupted epoch-12 positions now re-derivable (repair path, not discard)
gg_touched: GG-193
adr_touched: none
plan_deliverable_moved: no
-->

**Task:** T-470 / GG-193 (reserved, closed as answered-not-a-gap) — extend `t4_mlb_outcome_store.jsonl` coverage to 2026-08-07..08-15 and report re-derivability of the 532 corrupted epoch-12 ledger positions (GG-170/GG-185).

**Tier:** MICRO (per session_end_prep.sh suggestion — 2 commits, no `src/` touched; claimed STANDARD but scope stayed single-deliverable).

## Result

**All 532/532 corrupted epoch-12 positions are now re-derivable.** Ran `scripts/build_t4_outcome_store.py --workers 1` (sequential, respects `run_resolve_mlb.py` pacing constants) against a fresh VPS cycle-log pull (coverage through 2026-08-19). Store grew 2021 → 3199 rows. Join via new `scripts/t470_rederivable_check.py`: 532 found in store with `resolved=true`, 0 not-in-store, 0 unresolved.

Wrote **only** to the outcome store — `t4_mlb_resolved_ledger.jsonl` untouched, no `game_date` corrected, nothing re-resolved, per hard scope constraint.

**Note, not a new GG:** `build_t4_outcome_store.py` soft-falls-back to raw `game_date` on unparseable ticker rather than hard-refusing (task spec asked for hard-refuse). Empirically moot — 0/3199 tickers failed to parse this run. Flagged for whoever next touches `group_by_ticker()`.

## Implication (decision NOT made this session)

Epoch-12 reset can proceed on a **repair** path (n=719 recoverable) instead of discard (n=187). No corrected P&L/clean_n/comparison was computed — explicitly out of scope.

## Artifacts

- `scripts/t470_rederivable_check.py` (new, committed)
- DECISION_LOG.md entry appended (heredoc, 2026-08-20)
- Main-tree `logs/t4_mlb_outcome_store.jsonl` updated with extended copy

## Next steps

- Operator decision: repair (n=719) vs discard (n=187) for epoch-12 reset.
- Separate task if wanted: fix soft-fallback → hard-refuse in `build_t4_outcome_store.py`.
- Any clean-vs-corrupted P&L comparison needs pre-registration first (temporal confound, low power at n=187).
