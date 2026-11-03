# W97.3 results (flex lane: B-026 picks sheet, B-006 MLB winter posture, B-007 box memory)

Measured 2026-11-03 00:08-00:31Z on the box (961 MB RAM, 2 GB swap, swappiness 10, load average 9.5). Sources: `/proc/<pid>/status`
(VmHWM = peak RSS), `ps`, `dmesg -T`, `crontab -l`.

## Part A: picks sheet
- Builder `scripts/build_picks_sheet.py` + `pregame_shadow/picks_sheet.py` + dashboard panel "Tonight's picks" merged (#389, #392).
- Peak RSS of the builder: 141 MB (first version, window read whole) -> **19.8 MB** after `tail_rows` streamed line by line (#392). Run time 39 s, 4538 picks in 161 games (2026-11-02 sheet).
- Reasons: not available. Ledger rows carry `feature_row_sha256`, not features, so each pick says "no reasons available" (GG-1580).
- **Cron `37 5,22 * * *` is registered but NOT installed.** `runtime_registry.py live` read SURFACE BUDGET RED (silent arm NBA engine v3 EXP-044c, plus another block's uninstalled NBA events cron). Hard Rule 14 holds the install. The panel shows its missing-file message until then.

## Part B: MLB winter posture
- MLB arms already read IDLE on the box (`silent_arms`): game-market shadow, T1 paper pipeline, T4 live. Change (#393): the idle line now says why (next game date / last game date and none scheduled / no schedule). Alarm logic untouched; tests pin winter IDLE and the regular-season silent alarm (GG-163 detection kept).
- T1 MLB `SemanticFloorViolation`, 2 hits in `paper_mlb_cron.log`: 2026-10-16 (1 game fetched, 0 players matched, then "No KXMLBHIT markets available") = a postseason day with no player-hit markets listed at run time, not a defect. 2026-07-10 (16 games, 0 matched) = unexplained and predates this window; registered as GG-1582.

## Part C: box memory (the finding)
Peak RSS (VmHWM) of live processes, largest first (several instances of the same script are separate runs):

| Runner | Peak RSS | Cron cadence | Instances running now (oldest) |
|---|---|---|---|
| run_nhl_shadow_staked T3 | 381 MB | every 10 min, 17-02Z | 2 (904 s) |
| run_nba_player_points_shadow T3 | 337 MB | 14,24,44,54 | 2 (2238 s) |
| run_nba_pregame_shadow T3 | 249 MB | every 10 min | **3 (3738 s)** |
| run_pregame_shadow T3 | 243 MB | every 10 min | 2 (798 s) |
| demo_cancel_sweeper | 219 MB | every minute | 1 |
| run_t4_mlb_live (service) | 151 MB | service | 1 |
| run_t4_live (service) | 126 MB | service | 1 |
| web_dashboard (service) | 112 MB | service | 1 |
| frozen_evidence_check resume | 77 MB | other block | 1 |
| picks builder (not installed) | 19.8 MB | 2x/day, :37 (no other job at :37) | 0 |

- RAM 961 MB; available 57-134 MB during the window; swap 1.3-1.5 GB used.
- **20 OOM kills in the last ~90 min (6 at 23:xx on Nov 2, 14 at 00:xx on Nov 3)**, all `python`; two were 171-180 MB anon (shadow runners). Each kill is a lost cycle for an arm: rows not written.
- Cause: the T3 runners are launched every 10 min with no lock and each run takes 13-62 min (NBA pregame T3 oldest is 62 min), so copies of the same runner stack 2-3 deep, and the four T3 runners fire within minutes of each other (:03, :04, :06, :08, :09, :14). Peak RSS sums to well over 1 GB if the stack lands together.
- Not changed here. The fix is an edit of existing cron lines (a `flock -n` per runner, as the NBA engine lines already do) or a staggered schedule. Both are outside this block's PERMISSIONS (no edit of an existing cron line; no change to a live runner). Registered as GG-1581 (HIGH) with the exact proposal for the strategic window. No arm was stopped.
- A `flock -n` skips an overlapping launch, so a still-running cycle is not doubled. It does drop a launch while the previous run is alive; the owner should confirm that is acceptable for each arm's pre-registration before applying.
