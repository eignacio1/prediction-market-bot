<!-- session-meta
task_id: T-1250
tier: STANDARD
timestamp: 2026-10-27T04:50:00Z
commit: 3791166
one_line_summary: W89.2 DONE: 1,258 Kalshi price cells BH-tested, 11 survive net of fee, Part B 0; 3 pre-registration candidates
gg_touched: GG-1250, GG-1251, GG-1252, GG-1253, GG-1254
adr_touched: none
plan_deliverable_moved: no
vision_pillar: PROOF, DEPTH
gap_measure: families calibration-tested with BH; surviving market-level adjustments
gap_delta: families 0 -> 14 (1,258 testable cells); survivors 0 -> 11 cell rows, 3 recommended (12_EXPLORATORY/longshot_bias/out/summary.json, 2026-10-27)
pattern_sweep: n/a (no defect fixed); exploratory write fence hit by this block's own new code, fixed in PR #345 via _fence.safe_out
surface_delta: 0
-->

# SESSION HANDOFF — W89.2 (longshot bias, calibration of Kalshi sports prices)

Strategic decisions: NFL D0 excluded from survivors (date-only tickers); 3 candidates recommended (DECISION_LOG 2026-10-27).

PR #345 merged (f50f49c), CI green; main Test Suite green. No Deploy job ran, nothing live, t4-mlb untouched.
- Part A: 1,258 testable cells, 66 BH-flagged, 11 survive net of fee. Part B: 0 survivors.
- Candidates (in-sample): KXMLBHIT T0-2h 20-25c YES; KXMLBF5TOTAL T6-24h 90-95c YES; KXNFLTOTAL D1 5-10c NO.
- Caveats: no hold-out (GG-1254), ET assumption (GG-1253), NFL D0 (GG-1252), no NHL/NBA/parlays (GG-1250), partial candles (GG-1251).
- Raw data in untracked exp_output/W89_2/ keeps the worktree from retiring.

One thing pending: operator decides whether to pre-register the 3 candidates.
Resume: read 12_EXPLORATORY/longshot_bias/results_W89.md.
