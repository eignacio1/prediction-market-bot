<!-- session-meta
task_id: T-1290
tier: MICRO
timestamp: 2026-10-27T05:58:00Z
commit: 07af8ee
one_line_summary: W89.7 Part A partial: NBA/NHL/NFL Kalshi backfill + true-start join; PR 349 CI failed on EXPLORATORY fence, unmerged
gg_touched: GG-1260
adr_touched: none
plan_deliverable_moved: no
vision_pillar: PROOF, DEPTH
gap_measure: families with settled Kalshi history for a calibration test; hold-out cells tested
gap_delta: MLB+NFL -> +NBA,NHL game-family candles (MANIFEST.json 2026-10-27); hold-out cells 0 -> 0
pattern_sweep: ESPN scoreboard multi-day dates= returns 400; grep of src/scripts/12_EXPLORATORY found 2 other callers, both single-date, no defect
surface_delta: 0
-->
# SESSION HANDOFF — W89.7 (PARTIAL), operator asleep
vision_pillar: PROOF+DEPTH
gap_measure: families with settled Kalshi history for a calibration test
gap_delta: MLB+NFL -> game-family candles added for NBA, NHL (+partial NFL game); source MANIFEST.json 2026-10-27. Hold-out cells tested 0 -> 0.
pattern_sweep: ESPN scoreboard now returns HTTP 400 for multi-day `dates=` ranges (fixed in w89_7_backfill.py, one date per request). Other ESPN range callers not swept: `grep -rn "scoreboard?dates=" src scripts 12_EXPLORATORY` — register as GG if any.
surface_delta: none (no cron, service or archiver change).
Status: PARTIAL | branch session/20261027T051711Z-w89-7-ride-data | PR open, CI not read, NOT merged.
Next undone: (1) fix LA alias (Kalshi LA=Rams/ESPN LAR, LAC=Chargers) for 135 NFL events; (2) run `w89_7_backfill.py candles` for spread/total/team-total (+props) per sport, newest first; (3) Part B hold-out scan; (4) register GGs in GG-1260..1269, DECISION_LOG, ACTIVE_QUEUE row, check MLB HHMM (GG-1253); (5) end_session_worktree.
Note: run a sport's phases one at a time — the original chained prep run overwrote a good NFL schedule with an empty one.
CI (PR #349): FAILED, NOT merged. tests/test_exploratory_isolation.py::[w89_7_backfill.py] — fail-closed fence (CHARTER rule 3) flags w89_7_backfill.py:86 `.replace()` and :277 `.write_text()` as writes not routed through safe_out(). Cause: the block mandates data under exp_output/KALSHI_HISTORY/, which is outside 12_EXPLORATORY/, which the fence forbids. Not worked around (no noqa/fence edit). Options: (a) move manifests into 12_EXPLORATORY via safe_out and keep raw data writes in a src/ module via PR; (b) operator amends the charter for exp_output/KALSHI_HISTORY. Recommend (a). The other 98 isolation tests pass.
Pattern sweep done: other ESPN scoreboard `dates=` callers (scripts/demo_fill_timing_audit.py:15, 12_EXPLORATORY/nba_pam_mass_tier/w89_join.py:61) use single dates — no defect.
SESSION-END: TRUNCATED AT BUDGET — generator, DECISION_LOG, GG registration, ACTIVE_QUEUE row and claim closure NOT run. Worktree + claim left open. See commit range.
