<!-- session-meta
task_id: W114.1 (B-087)
tier: STANDARD
timestamp: 2026-11-13T00:40:00Z
commit: 499522d
one_line_summary: W114.1: Muse intake (#494) merged; NBA adapter now tags rows with 12 shot-distance filters (#500); 54 leaves scored, 5 kept.
gg_touched: GG-1932
adr_touched: none
plan_deliverable_moved: no
vision_pillar: DEPTH
gap_measure: D-06, D6 layer 3 (NBA)
gap_delta: NBA index entries 24 -> 36; NBA kept splits 27 -> 32 of 239 total; 0 BH survivors
pattern_sweep: nba_adapter is the only NBA filter entry point (grep filter_supply src/ scripts/ tests/); replay script and tests use it unchanged
surface_delta: 0
-->

# Session handoff - W114.1 (B-087), 20261113T0040Z

**Part A (done).** PR #494 (Muse archive intake) merged ae7562b. The conflicts were docs only (DECISION_LOG, PLAN, TODO_NEXT, MEMORY_BANK): kept main's version of the three nav files, kept both DECISION_LOG entries. Local precheck 241 passed; CI green on the head; squash-merged. Archive never written. Correction to the block text: 113.4 DID write a handoff (SESSION_HANDOFF_20261112T2344Z_W113_4.md, in the PR); it said CI was red on main for test_w109_3, which was fixed on main since.

**Part B (done).** PR #500 merged 499522d (CI green). decision_trees/filter_supply.py nba_adapter adds distance_filters() to the 111.4 leaves when the prior-season percentile table carries the 12 entries (the table was rebuilt from 12_EXPLORATORY/archive_intake/team_percentiles.json, same season label 2026, data_through 2026-06-30, so point-in-time is unchanged; a table without them skips them). scripts/build_filter_splits_w112.py now also reads archive_intake/leaf_scores.json with the same KEPT rule as every other split (not thin, arm != NO_BET, >= 10 held-out games, held-out net > 0). Tests added in tests/test_filter_supply_w112.py.

**Tables graded (GRADES.md @ pin cc7bf85):** VERIFIED 4 families (NBA opponent shooting by distance, NBA Traditional mostly, NHL counts, NHL shots/hits/faceoffs) · MISMATCH 3 items (NBA home/road neutral-site, NBA turnovers definition, NHL penaltiesFor) · UNCHECKABLE 7 rows (NBA zones/quarters/clutch/four-factors/advanced; NBA player tracking, hustle, Synergy, lineups; referees; NHL xG family; NHL 5on5 and other seasons; NHL scouting refs and coaches; NHL goalie snapshots).
**Index entries:** NBA 24 -> 36 (12 distance entries: opponent FG% and shot share, six bins).
**Layer-3 splits from Muse data:** 54 archive leaves scored on the 2026-27 shadow rows; 5 kept under the rule, 0 survive Benjamini-Hochberg. The 5 kept splits (n games held out 11-29, means +0.2 to +11.7 cents) are about what chance gives from 54 tries; they are logged and routed, not evidence of a real filter. Total NBA/NFL/NHL kept splits 27 -> 32 of 239.

**Replay, last 14 days of the local price archive (12,293 decisions; files prices_2026-10-31..2026-11-13, NBA 6,572 rows; no orders; paper replay):**
| NBA decisions | NO_BET | RIDE | FADE |
|---|---|---|---|
| no filters | 6,572 | 0 | 0 |
| filters before this block (origin/main) | 5,921 | 651 | 0 |
| with Muse distance filters | 6,190 | 382 | 0 |
Why RIDE fell 651 -> 382: kept splits that disagree on the arm cancel (split_conflict, router rule from 112.1) and the market-state arm (NO_BET) stands; 1,394 NBA rows hit a conflict. NFL (2,769) and NHL (2,952) unchanged (NHL has no store rows for these games).

**Still unread from Muse:** the 7 UNCHECKABLE rows above (nothing graded, so nothing fed to a model), plus all archive days after the pin. Needs: forward capture of NHL goalies + Kalshi candles (GG-1931), a recompute for NBA zone/quarter/clutch tables, and a refresh of the pin to read Muse's daily records.

- directive_conflicts: none
- Not done: box deploy read for the two merges (no allowlisted read from this window this turn); MLB idle so no t4-mlb decision applies. Window should confirm deploy_truth_read shows 499522d.
- Pushback: none. Surface: none. Dependencies: 114.2 reads coverage.py unchanged.
