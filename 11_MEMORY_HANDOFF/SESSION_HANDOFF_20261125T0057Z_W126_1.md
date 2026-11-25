<!-- session-meta
task_id: W126.1
tier: MICRO
timestamp: 2026-11-25T02:20:00Z
commit: 8668534
one_line_summary: W126.1 partial: #562 and #565 merged (router per-day skip totals, archive_dense gate read); box reads pending.
gg_touched: none
adr_touched: none
plan_deliverable_moved: no
vision_pillar: PLUMBING
gap_measure: D6 per sport, E1 router ERROR rows per day
gap_delta: none (box d6_read / router_error_read results not yet landed)
pattern_sweep: grep market_ticker KeyError form across src/ scripts/ tests/ -> no other leaf-row builder without ticker
surface_delta: +1 read-only box task (archive_dense_gate_read), no cron/service/workflow
-->

# Session handoff W126.1 — D6 / router: finish 125.2 (PARTIAL: box reads pending)
Common rules quoted: "# Wave 126 common rules". Worktree PM-worktrees/w126-1. PURPOSE: DEPTH D6 + EXECUTION E1.

## Done
- Part 0: PR #562 merged (rebased; conflict markers in DECISION_LOG removed before merge).
- Part A diagnosis: all 6,340 post-epoch router ERROR rows are one bug, KeyError('market_ticker') on MODEL_FADE leaf rows
  (two forms). Fixed by #503 (W116.3, merged 11-17 16:48 PT), regression test tests/test_leaf_map_router.py. UNROUTED NHL
  (5,573 rows) ended when the NHL router was wired (W118). Before: 478–1,611 ERROR rows/day on 11-12..11-17; 0 after 11-18.
  Added per-day-per-sport post-epoch skip totals to scripts/router_error_read.py (+test) so "0 after" is shown with real totals.
- Part C: `gate` subcommand (JSON) in scripts/archive_dense_install.py; read-only box task `archive_dense_gate_read`
  in scripts/box_tasks.py; tests/test_w126_1_archive_dense_gate.py. PR #565 merged, CI green. NOT installed.
- Requests pushed 2026-11-25 00:39Z (137fb05): router_error_read, d6_read, d6_trace_read, archive_dense_gate_read.
  No results had landed at 00:57Z (box last wrote a result 11-24 05:54Z).

## Not done (resume here, in order)
1. Read the four 20261125T0039Z_* results in 04_EXECUTION/BOX_TASKS/results/ once the box deploys #565 and runs them.
   If none appear, ask for a deploy_truth_read first (box timer may be stalled).
2. Report router ERROR rows per sport per day before/after and D6 per sport after vs before (17/117: NBA 7, NFL 4, NHL 6, MLB 0).
3. Part B code fixes: none made. Registered-not-fixed: NBA_PLAYER_POINTS layer 2 (no leaves in frozen v1 leaf map, so a
   leaf-map coverage item), NBA/NFL moneyline `leaf_not_in_map`, and the prop ticker parse (`nba_event_ticker_unparsed` for
   prop series in filter_supply; fixing the parse alone does not wire the layer). Open GG numbers for these; update GG-2007
   (cause fixed by #503, none since 11-18).
4. Add the ACTIVE_QUEUE NOW row (docs-only) and a RUNTIME_REGISTRY note: read-only box tasks have no per-task entry; they are
   covered by the workflow|box_tasks.yml component, so none was added for archive_dense_gate_read.

## operator decisions:
- NFL per-leaf rule (W117.1 A3, operator-approved) routes NFL cells to NO_BET, so they stop at layer 7. Visible in the
  truncated trace: 593 NO_BET skips (81 + 216 + 81 + 215). Rule left unchanged. Question: keep NFL NO_BET in these leaves
  (D6 for NFL stays at 4), or allow a flat-demo-stake arm order so fills can be measured?
- archive_dense_install: the last gate read projects 86.2% disk at 30 days vs the 80% ceiling, so it REFUSES. Recommendation:
  do not install as built. Options: shrink capture to about 108 MB/day (vs 159), or supersede the 80% ceiling by decision.
  Approval line only if the fresh `archive_dense_gate_read` says PASS: "approve archive_dense_install".

## session meta
measure moved: none yet measured (D6 and ERROR/day pending the box reads); diagnosis plus tooling only.
surface_delta: +1 read-only box task (archive_dense_gate_read), +1 reader field; no cron, service or workflow.
pattern_sweep: grep of src/ scripts/ tests/ for the market_ticker KeyError form found no other leaf-row builder without ticker.
directive_conflicts: none found in OPERATOR_DIRECTIVES.md. No frozen PREREG, hash, leaf map, cron or kelly change.

## Strategic Decisions This Session
None — implementation-only session. Two operator questions are listed above under operator decisions.

One-thing-pending: read the four 20261125T0039Z box results.
Resume: git fetch origin && ls 04_EXECUTION/BOX_TASKS/results | grep 20261125T0039Z

## Box results (landed after the first write; results/20261125T0039Z_*)
- router_error_read: ERROR rows per day 11-12..11-18 = 478, 1047, 1134, 1611, 961, 949, 160; zero on 11-19..11-25 (day totals of all
  skip rows now shown per sport per day). Cause fixed by #503. E1 gap_delta: ERROR/day 478-1611 -> 0 (router_error_read, 20261125T0039Z).
- d6_read (00:52Z): wired 18 of 129 (was 17 of 117): NBA 7, NFL 4, NHL 7 (was 6), MLB 0. Delta is the NHL +1 and 12 new registered cells, not from a fix in this block.
- archive_dense_gate_read at 00:40Z ran pre-deploy code (printed usage, exit 2). Rerun queued (…T0219Z request). Last known gate: 86.2% REFUSE.
