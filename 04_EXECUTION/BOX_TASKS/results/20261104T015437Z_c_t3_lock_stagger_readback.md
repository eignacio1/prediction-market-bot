# Box task `t3_lock_stagger_readback` — 20261104T015437Z_c_t3_lock_stagger_readback

- request: `04_EXECUTION/BOX_TASKS/requests/20261104T015437Z_c_t3_lock_stagger_readback.toml`
- note: readback after the T3 lock install
- ran: 2026-11-04T01:54:58Z on root@157.230.91.33:/opt/prediction-market-bot
- exit code: 0
- command (allowlisted, scripts/box_tasks.py): `PYTHONPATH=src:. venv/bin/python scripts/t3_lock_stagger.py readback`

```
T3 LINES WRAPPED: 6
  nhl_staked_t3            6,16,26,36,46,56 17-23 * * *
  nhl_staked_t3            6,16,26,36,46,56 0-2 * * *
  pregame_shadow_t3        8,18,28,38,48,58 * * * *
  mlb_pregame_shadow_t3    3,13,23,33,43,53 * * * *
  nba_pregame_shadow_t3    1,11,21,31,41,51 * * * *
  nba_player_points_t3     14,24,44,54 * * * *
T3 LINES NOT WRAPPED: 0
SKIP ROWS (logs/t3_skips.jsonl): 0  by runner: {}  last: none

```
