# Session handoff - W117.3 (2026-11-18 05:10Z, Sonnet)

session-meta: block 117.3 + SW-9 addendum; PRs #511 (coverage/d6_read/ml_team_total), #516 (healthcheck + health_rerun); box at ea9d08ee.

MEASURE MOVED: D6 on the box 3 -> 4 wired, all NBA (source: d6_read 2026-11-18T05:01Z).
- Wired by name: NBA_GAME_TOTAL|T3, NBA_SPREAD|T2, NBA_SPREAD|T3, NBA_TEAM_TOTAL|T3.
- NBA layer-1 cells: 12 -> 15 (moneyline + team totals now count logged p_yes). NBA layer 3: 12 stump cells, 9 with a kept split (stricter l3_kept).
- Per sport wired: NBA 4/25, NFL 0/29, NHL 0/21, MLB 0/42. NHL layer 3 not re-read (nhl_event_store_install has not run; store dir absent on box).

One cause per unwired NBA cell (first missing layer):
- MONEYLINE T1/T2/T3: layer 4 (every leaf thin, 456 rows/154 games, no arm leaf). SPREAD T1: layer 4 (no non-thin arm leaf).
- TEAM_TOTAL T1: layer 4. GAME_TOTAL T1: layer 6 (size_for always NO_BET). GAME_TOTAL T2 and TEAM_TOTAL T2: layer 7 (no post-epoch fills yet).
- Player props (assists/rebounds/threes, points T4): layer 1; PLAYER_POINTS T1-3: layer 2.
- TEAM_TOTAL T1-3 layer 3 now passes under the approved stump rule (GG-1951: counts box rows, not the split file).

Part A: nba_engine/ml_team_total.py; tolerance to spread-implied P(win) 0.02 (measured worst 0.017); team means vs total, planted-case recovery tested.

Addendum: healthcheck "cron arm MISSING" was false: `echo "$LIVE" | grep -q` under pipefail takes SIGPIPE on a large crontab. Registry was right. Fixed with here-strings (+ regression test). health_rerun box task added; box result: HEALTHY, 0 faults, 1 warn (disk 87%). Cron line is present; nothing reinstalled.
Disk: NHL store is 325M locally (exp_output/NHL_EVENTS); box disk is 87% used (was 85%), i.e. ~13% free; absolute GB not measured. The install is not blocked by it but 90% is the FAIL line.

pattern_sweep: grep for `echo "$X" | grep -q` in deploy/ scripts: fixed in healthcheck.sh (3 sites).
surface_delta: +1 allowlisted read/append box task (health_rerun); 0 new cron/services.
directive_conflicts: none. Local test note: 3 test_healthcheck tests fail on the laptop only (local disk 90%); same without the change; CI green.
clock lever: more cells wired - next is layer 4 on NBA moneyline/spread/team-total T1 (needs rows to make a non-thin leaf) and fills on T2 game/team totals.
Open for window: regenerate CLAUDE.md Right-now (gap count 273 vs 274); register a GG for the healthcheck false-FAIL.
