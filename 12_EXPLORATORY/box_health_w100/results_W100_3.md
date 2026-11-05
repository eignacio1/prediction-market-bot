# W100.3 results — picks sheet read-back, box memory after the fix, installer leftovers

Sources: box tasks `box_memory_read` (00:57Z 11-05), `picks_sheet_read` (`20261105T0137Z_w1003c`, 01:43Z), `deploy_truth_read`, `budget_read`. Dates UTC.

## Part C — DONE (PR #415, 73eda44, CI green)
- B-040: v1's marker `…nba_engine.live` was a prefix of v3's `…nba_engine.live_v3`. All four installers now use one boundary-safe `marker_in`. A test over the real `deploy/` files proves no cron line is claimed by two installers.
- `tests/test_tensions.py` and `tests/test_seat_interface.py` (and the two renderers) collect on Py3.9 (`tomli` fallback). Full suite on 3.9.6: 5096 passed, 44 skipped.

## Part B — PARTIAL: kills down, not zero; fix prepared, not installed
| Measure | 11-03 | 11-04 | read 00:57Z 11-05 |
|---|---|---|---|
| OOM kills per 24h | 142 | 24 | **39** (python 38, systemd 1) |
Peak RSS per runner (MB): nba_pregame_shadow T2 312.5, nhl_staked T3 310.1, nba_pregame T3 263.5, nba_pregame T2 251.4, pregame_shadow 249.8, nba_player_points T3 246.1, demo_cancel_sweeper 227.1, dashboard 137.8. Largest anon-rss at a kill: 205.9 MB.
Lock skips (T3 lock working): 18 — nba_pregame_shadow_t3 10, nba_player_points_t3 6, nhl_staked_t3 2.
Memory: 985 MB total, 51 MB available, load about 9, swap 710 MB free of 2 GB. Surface budget GREEN. No silent arms.

**Next cause (numbers):** four concurrent `run_nba_pregame_shadow --bands T2` copies, three T3 copies and two `run_pregame_shadow` copies were alive at once. At 250–310 MB each, three copies exceed the box. The T3 lock covered only T3; T1/T2 lines had none. The kill count did not reach 0 because the reading was taken on the first full night with that gap open. I do not know whether kills cluster at tip-off; `box_memory_read` gives counts only.
**Fix (PR #416, c3a2fcc, CI green):** the same non-blocking flock for the 10 T1/T2 shadow runners (nba, pregame, mlb, nba player points, nhl), one lock per runner and band, no schedule change, deploy mirrors regenerated, tests. **Not installed.** Install = box task `t3_lock_stagger_install` (existing entry; idempotent; backs up crontab first; undo `t3_lock_stagger_uninstall`; check `t3_lock_stagger_readback`). Needs the operator's approval by name.

## Part A — PARTIAL: first night read; second night not yet possible
`picks_sheet_read` (sheet 11-04 built 22:47Z): 2614 picks, 134 games, median 8 per game (max 74, a team-total ladder). Reasons stored on 2353/2614 (90%); 261 have none (259 "no reasons available", 2 on a model without per-factor contributions). Demo orders placed on 2609; 4 skipped with a stated reason (2 not listed on demo, 1 one-sided book, 1 mid gap above threshold); 1 has no order row. Arms disagree in 2 games. Results: all 2614 still open — expected for a sheet built while the games were in progress; the 05:37Z sheet is the first that can show yesterday's results. nba_engine v1/v2: no pick in window; v3: no rows file yet.
Defect registered, not fixed: GG-1690 (both mirror sides and both arms of one bet are listed as separate picks, so 2614 overstates distinct opinions).
**Still to read:** the 05:37Z 11-05 sheet (results filled?) — request `picks_sheet_read` again after it.
