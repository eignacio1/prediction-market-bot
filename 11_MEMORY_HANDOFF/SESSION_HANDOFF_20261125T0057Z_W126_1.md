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
