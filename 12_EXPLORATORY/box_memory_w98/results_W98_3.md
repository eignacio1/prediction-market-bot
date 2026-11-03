# W98.3 results — box memory, held installs, picks say why

**Pillar: PLUMBING + visibility.** Merged: PR #398 (Part A, de539ff), PR #401 (Parts B+C, 5e2eb1c). CI green on both.

## Install order (the strategic window runs these; terminals do not)
1. `t3_lock_stagger_install` -> readback `t3_lock_stagger_readback` (5 T3 lines wrapped, skip rows appear in logs/t3_skips.jsonl). **Must be first:** the v3 line's shared lock and the memory fix have to be on the box before v3 starts.
2. `nba_engine_cron_install` (NBA events refresh + v1/v2 lines) -> `nba_engine_cron_readback`; confirm the store refresh time moves after 12:33 UTC.
3. `nba_engine_v3_cron_install` -> `nba_engine_v3_cron_readback`; confirm v3 rows per game and family after a slate. v3 now uses `flock -w 240 /tmp/nba_engine_live.lock`, the same lock as v1/v2, so two ~500 MB runners are never co-resident.
4. `picks_sheet_cron_install` -> `picks_sheet_cron_readback`; confirm the picks panel after a real night (writes only exp_output/PICKS_SHEET/).
Uninstall tasks exist for 1, 3, 4. `box_memory_read` measures OOM kills before and after.

## Part C
Ridge arms (NBA, NFL, MLB game markets) now log `reasons`: top 3 factor contributions (exact coef x z, plain-word names, value, points toward YES). Arms that cannot give them log `reasons_note`. Picks render them ("supports / works against this pick"). Logging only: no probability, threshold, order or stake changed. NHL, NBA-points and nba_engine writers were NOT yet checked or marked; they fall back to "no reasons available".

## No pre-registration assumed concurrency
EXP036/037/038/040 contain no concurrency or cadence assumption; the lock changes WHEN a run happens, not what it computes.

## Not done
DECISION_LOG append, ACTIVE_QUEUE 98.3 row, SESSION_HANDOFF file, full pattern sweep, GG registration for the NHL/points/engine reasons gap. Local tests/test_seat_interface.py and test_tensions.py fail to collect on Python 3.9 (CI passes).
