<!-- session-meta
task_id: T-1430
tier: STANDARD
timestamp: 2026-10-29T01:40:00Z
commit: 3582308
one_line_summary: W94.Q: exact-fee recompute of every reported net, ride.py LADDER side fixed, Bayesian skill weights applied; PROOF_CALENDAR.md generated (64 rows) from the box read
gg_touched: GG-1430, GG-1431 opened
adr_touched: none
plan_deliverable_moved: no
vision_pillar: PROOF
gap_measure: nets re-checked with the exact fee; LADDER side hazard; skill weight with an interval; P3 frozen hypotheses with a projected look date
gap_delta: nets re-checked 0 -> all (89.2's 11 cells, 90.3 headline, 91.2 whole sample + 2 HELD_OUT cells); LADDER side open -> fixed; skill weight posterior with interval 0 -> 4 of 6 models (2 have no held-out score, prior only); frozen hypotheses with a projected look date 1 -> all 64 rows (PROOF_CALENDAR.md, box read 2026-10-29T05:17Z)
pattern_sweep: side != "yes" swept in decision_trees and c5_execution, no other instance; exploratory-isolation fence defect (write-shaped calls outside safe_out) fixed in the one file I wrote
surface_delta: +1 allowlisted read-only box task (proof_calendar_read); no running component
-->

# SESSION_HANDOFF W94.Q (quant in tandem)

## Status: DONE. Parts A, B, C. Part B closed 2026-10-29T05:2xZ: `04_EXECUTION/PROOF_CALENDAR.md` generated (64 rows) after two emit fixes: #375 (537KB blob cut by the 30KB bridge cap -> per-day counts) and #376 (counted market tickers, 532 vs 58 games -> game_key). Open item 1 below is superseded. NFL look date 10-30 vs the engine's 11-02 (settle lag): treat the engine date as binding. Still unregistered (Rule 11): GG for the 2 non-reproducing KXMLBHIT cells and the reported-n mismatches.

## Merged (CI green read before each merge)
- #372: `exact_fee_recompute.py`, ride.py LADDER side fix + tests, `quant/bayes_skill.py` (+7 known-answer tests), `scripts/proof_calendar.py` (+7 tests incl. known-answer on a synthetic accrual series), `proof_calendar_read` box task, results.
- #373: `12_EXPLORATORY/quant_w94/bayes_skill_apply.py` (stdout only) and the Part C section of `results_W94_Q.md`.

## Results (full tables in `12_EXPLORATORY/quant_w94/results_W94_Q.md`)
- Exact fee equals k007 for NFL/NBA/NHL; only MLB moves, and it moves up (prelive taker multiplier 0.5).
- 89.2: 9 of 11 cells reproduced; 8 keep lo>0 under both fees. The 2 KXMLBHIT T0-2h 20-25c cells re-ran at n=0 (NOT REPRODUCED from the local archive subset).
- 90.3 MLB follow, exact: 3h -0.1128 [-0.1165, -0.1091], settle -0.0816 [-0.0906, -0.0725]; the 23-cell grid has 0 cells with net_lo>0.
- 91.2 whole sample exact +0.0083 [-0.0009, +0.0170]; HELD_OUT net5c+ stays positive (n 53, +0.3029 [+0.1420, +0.4637]); net2-5c did not reproduce the report's n 117 (re-run n 202/324).
- Part C: no frozen model earns a weight above 0.02 or can on its current point estimate. MLB posterior weight 0.0016, the other three 0. nfl_qb_challenger_v1 and nba_player_points_v1 have no held-out score, so they sit at the prior (weight 0). If a true advantage were +0.01 Brier, 124 (NHL) to 332 (NFL) games would earn 0.02. Gate replay is descriptive from the W88 JSONs only; the full replay needs a box snapshot.

## Open items
1. **Part B not finished.** `proof_calendar_read` has run 3 times on the box and each time failed with `scripts/proof_calendar.py: No such file`. The box has not pulled #372 (box HEAD was ec92612, the #371 merge; Deploy to VPS has not run since 2026-10-16, so the box syncs some other way, with a lag). Next session: re-dispatch (`gh workflow run box_tasks.yml -f task=proof_calendar_read`), save the emitted JSON, run `PYTHONPATH=src python3.11 scripts/proof_calendar.py --input FILE`, and push `04_EXECUTION/PROOF_CALENDAR.md` docs-only. I did not dispatch Deploy to VPS myself: it is a production deploy onto a RED box and not mine to trigger.
2. To register (not registered here, Rule 11): GG for the 2 KXMLBHIT cells not reproducing from the local archive subset; GG for the 89.2/91.2 reported-n vs re-run-n mismatches (KXMLBSPREAD 186 vs 179; net2-5c 117 vs 202).
3. NFL GG-1090 timing caveat applies to nfl_pregame_v1's score; EXP-042/043 game counts in the calendar are upper bounds.
