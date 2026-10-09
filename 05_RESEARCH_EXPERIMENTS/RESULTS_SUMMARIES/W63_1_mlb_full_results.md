# W63.1 — MLB wired to full (results)

## Part A — game-market arm (DONE)
- GG-532: scheduled T1 run 2026-10-09T12:07Z wrote 33 rows (newest 12:07:02Z) after #195 -> RESOLVED.
- Pre-registration c3ba006 (2026-10-03T01:11Z) precedes first row (2026-10-05T13:12Z) -> flip authorised.
- 12 cells (ML, RL, game total, team total x T1-T3) flipped to SHADOW; PR #201, deploy b25b63b, t4-mlb restarted (no game live).
- VPS proof: registry Counter = SHADOW 36, ACTIVE 1, NOT_IMPLEMENTED 64, BLOCKED 2, DARK 1; calibration engine (engine_20261009T134917Z.json) lists all 12 cells SEALED.
- MEASURE MOVED: B1 25/104 -> 37/104, B2 8/18 -> 12/18 (VPS registry).

## Part B — player hits (pending)

### Part B — player hits: premise falsified, nothing to wire (DONE, no code change)
**Step 4 trace (VPS `logs/paper_mlb_cron.log`, `exp_output/MLB/mlb_feature_matrix.meta.json`, Stats API schedule):**
- "0 players matched since ~2026-09-27" is false. T1 matched 73/70 players on 09-26/27 and 32, 32, 9, 27, 15, 12, 27, 6 on 09-29..10-08 (postseason started 10-03/04). Zeros occurred only on days with no MLB games: 09-28, 10-02, and 10-09 (Stats API schedule for 2026-10-09 = 0 games; PIPE-08 "0 active games"). On 10-09 T1 saw 39 quoted KXMLBHIT markets and matched 0 because none is for a game on that date.
- The feature CSV already carries postseason: 52,116 rows, max_game_date 2026-10-08, generated 03:16Z by `mlb_features_sync.yml` (runs `generate_mlb_features.py --seasons 2026 --include-postseason`, W57.1/GG-489; the VPS PIPE-05FX line is disabled).
- Orders are 0 because kelly_fraction = 0 (ADR-0048), not matching.
**Step 5 scope:** DECISION_LOG 2026-10-06 operator ruling ("MLB can't go dark while games are going on; shadow arms keep logging through every..."), and EXP-037 MLB (postseason rows counted, never scored). Postseason is in scope; no separate labelling needed because the feature CSV carries `season_type` and no stake rows are written.
**Step 6:** already wired (above); no PR. Next real proof: T1 11:00Z 2026-10-10 (slate: CWS@CLE, Stats API date 2026-10-10; 10-11 LAD@MIL) should show >0 players and latest game_date 2026-10-09 or 10-08.
**Step 7 (winter):** stops by itself: T4M-PROJ stake gate (kelly 0 + no live games => no evaluations), shadow crons (no open markets => skips), PIPE-05/T2/T3 (0 players). Needs a block: T4M-PROJ registry flip to DARK; nothing was added for the postseason in this block, so nothing to remove (`--include-postseason` in the sync workflow is harmless offseason).
MEASURE MOVED (Part B): none.
