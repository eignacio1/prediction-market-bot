# SESSION HANDOFF - W102.1 (engine lane) - PART A DONE, PARTS B/C NOT STARTED

vision_pillar: DEPTH (D4 NBA)
gap_measure: D4 - NBA arms with complete coverage on a slate (11-04: v1 56/56, v2 44/56, v3 38/56)
gap_delta: 0 measured so far. Fix merged but the cron line is NOT installed, so coverage is unchanged until the operator approves the install. Expected: 3 of 3 arms from the first slate after install.
pattern_sweep: checked the same chained-run / silent-lock-timeout / no-trace shape: v1, v2, v3 runners all got the attempt trace. The same `flock -w` silent exit exists in other lanes' cron lines (not audited - registered below). Operator-facing T3/T1/T2 locks were staggered on 11-05 02:11Z (separate fix).
surface_delta: +1 live cron component (catch-up), registered in RUNTIME_REGISTRY.toml + RUNTIME_MAP.md; INACTIVE on the box until the install task runs. Health signals were green at merge time (no silent arm, 0 OOM since 02:11Z).

## Status
Part A: DONE (merged). Part B (NHL goalie + rest): NOT STARTED - no pre-registration written, no rows. Part C (NBA store lag): NOT STARTED.

## Ticket states
- B-030 (v2/v3 miss): root cause named, fix merged (PR #425, squash 76b5e3d, CI green). Open: install on the box (operator approval), then verify the first slate.
- B-012 (NHL goalie + rest): open, untouched. Pre-registration must be committed before any row.
- B-017 (NBA store lag): open, untouched.

## Root cause (full text: 12_EXPLORATORY/nba_engine_coverage_w102/ROOT_CAUSE.md)
Kernel OOM burst on the 961 MB box (22 kills, 23:13-00:18Z on 11-04; 481 since 10-30) killed or starved v2/v3 fires inside the 23:00-00:30Z windows. v2 is chained behind v1; v3 waits 240s on the lock then exits silently; nothing retried inside the window; kills left no trace. Missed games tipped 00:00Z/00:30Z (12 v2, 18 v3). The 02:11Z lock stagger removed the trigger. No non-OOM miss found. "Without OOM" in the block title was not borne out.

## Operator decision needed
Approve by name: `nba_engine_catchup_install` (box_tasks allowlist; backup + readback; `nba_engine_catchup_readback` / `nba_engine_catchup_uninstall` alongside). Window runs it only on that approval. I did not run it.

## Defects found, to register (GG numbers reserved at claim, not yet written into the log)
1. Killed runs left no trace (fixed by attempts.py for the three engine runners).
2. `live.run()` loads history and calibrates before checking for pending events, so every fire pays full memory. Not changed (frozen runner logic).
3. v3 `flock -w 240` exits silently on timeout; other cron lines with the same pattern not audited.

## Deploy
Box pulls main every 5 min; the merged code is inert (the only new cron line is not installed). t4-mlb restart decision: no import of the changed files, no restart needed. I did not read the box deploy log.

## Next session
1. Operator approves the install -> window runs it -> read `attempts.jsonl` unfinished counts after the next slate.
2. Part B: commit `12_EXPLORATORY/nhl_engine/NHL_GOALIE_REST_PREREGISTRATION_<date>.md` first (starting goalie = who actually started; live capture branch stopped 10-14), then the new module + held-out test on 2023-2025.
3. Part C: compare NBA store last game date to yesterday's schedule (read-only).
