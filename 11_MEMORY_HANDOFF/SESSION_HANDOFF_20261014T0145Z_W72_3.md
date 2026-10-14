<!-- session-meta
task_id: T-920
tier: STANDARD
timestamp: 2026-10-14T01:55:00Z
commit: 8b1fb3b
one_line_summary: W72.3 closed: deploy truth machine-checked (GG-661/668/669); ledger and point-in-time audit finds no leak; GG-690/691 opened.
gg_touched: GG-661, GG-668, GG-669, GG-690, GG-691
adr_touched: none
plan_deliverable_moved: no
vision_pillar: PLUMBING
gap_measure: PLUMBING
gap_delta: none
-->

# SESSION HANDOFF W72.3 (2026-10-14)

vision_pillar: PLUMBING
gap_measure: none (PLUMBING)
gap_delta: none. Deploy truth is now machine-checked (alarm in scan and /project, status file, healthcheck); proof checks run on the judged ledgers.

Status: DONE. Part A #247 (GG-661, 668, 669). Part B #249 (point-in-time tests, ledger audit, H2 remainder).
Box read back over ssh: HEAD 10e34368, decision `deployed` / t4-mlb `not_needed`, t4-mlb active, healthcheck HEALTHY 0 faults after Part A.

Results: invariants 16 violations, all one stale enum (GG-691); 3,495 rows lack market_type so 24 assertion pairs were not evaluated (GG-690). Data validation found 0 duplicates, bad prices, tz-naive or settle-before-entry rows. Point-in-time: 7 tests pass with positive controls.
Caveats: shadow-file checks matched by field name; MLB same-date doubleheader ordering is untested.
Next undone: GG-690 (read-only market_type derivation in the invariants script), GG-691 (add CANCELLED), then W72 punch-list M-A..M-F.
Operator decisions: none from this block.
