# Session Handoff — 2026-09-29T05:45Z

<!-- session-meta
task_id: T-587
tier: STANDARD
timestamp: 2026-09-29T05:45:00Z
commit: b2faddb
one_line_summary: T-587 wave 38.1: NFL T1 runs now self-identify (runtime sha/trigger/run id/host); live hand-run wrote 802 STUB rows (GG-317).
gg_touched: GG-316, GG-317
adr_touched: none
plan_deliverable_moved: no
-->

**Trigger:** operator-initiated. **Last commit:** `b2faddb` (origin/main). VPS fast-forwarded to 1d65b9b, no restart.

## Status
- NFL T1 pool: 824 open rows, of which 802 are STUB-model (run PT-T1-NFLGM-71208CC5); 42 GG-302 rows still quarantined.
- Tests: 70 passing (new + NFL runner + paper_trader). No live capital.

## Strategic Decisions This Session
| Decision | Rationale | Reference | Owner |
|---|---|---|---|
| Distinct runtime provenance fields beside `approval_commit` | epoch marker read by other tooling | DECISION_LOG 2026-09-29 T-587 | DS |
| D3 NFL cron skipped | no authorization line in ACTIVE_QUEUE | same | Operator |

## What changed
- `run_provenance.py` new; `run_t1_nfl_game_market.py`, `paper_trader.py` (fence extension) edited; `tests/test_gg302_run_provenance.py`.
- GG-316 (attribution) and GG-317 (stub-row inflation) registered, both OPEN.
- D4: ~10.5k rows vs n* ~2,610 by rows; ~237 games (~9% of n*) by independent units. Correlation decision (ADR-0053 s2.5) governs.

## One thing pending
Operator: quarantine STUB rows from n-counts (GG-317) and decide on NFL cron authorization; verify re-run de-duplication first.

## Resume
`scripts/session_delta.sh "$(cat 04_EXECUTION/.last_session_checkpoint)"`
