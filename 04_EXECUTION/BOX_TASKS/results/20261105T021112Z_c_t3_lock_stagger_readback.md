# Box task `t3_lock_stagger_readback` — 20261105T021112Z_c_t3_lock_stagger_readback

- request: `04_EXECUTION/BOX_TASKS/requests/20261105T021112Z_c_t3_lock_stagger_readback.toml`
- note: readback after the T1/T2 lock install
- ran: 2026-11-05T02:11:35Z on root@157.230.91.33:/opt/prediction-market-bot
- exit code: 0
- command (allowlisted, scripts/box_tasks.py): `PYTHONPATH=src:. venv/bin/python scripts/t3_lock_stagger.py readback`

```
T3 LINES WRAPPED: 17
  nhl_staked_t1            0 14 * * *
  nhl_staked_t2            4,34 15-23 * * *
  nhl_staked_t2            4,34 0-1 * * *
  nhl_staked_t3            6,16,26,36,46,56 17-23 * * *
  nhl_staked_t3            6,16,26,36,46,56 0-2 * * *
  pregame_shadow_t1        5 */6 * * *
  pregame_shadow_t2        10 * * * *
  pregame_shadow_t3        8,18,28,38,48,58 * * * *
  mlb_pregame_shadow_t1    7 */6 * * *
  mlb_pregame_shadow_t2    12 * * * *
  mlb_pregame_shadow_t3    3,13,23,33,43,53 * * * *
  nba_pregame_shadow_t1    11 */6 * * *
  nba_pregame_shadow_t2    16 * * * *
  nba_pregame_shadow_t3    1,11,21,31,41,51 * * * *
  nba_player_points_t1     21 4,10,16,22 * * *
  nba_player_points_t2     27 * * * *
  nba_player_points_t3     14,24,44,54 * * * *
T3 LINES NOT WRAPPED: 0
SKIP ROWS (logs/t3_skips.jsonl): 32  by runner: {"mlb_pregame_shadow_t3": 1, "nba_player_points_t3": 10, "nba_pregame_shadow_t3": 18, "nhl_staked_t3": 2, "pregame_shadow_t3": 1}  last: 2026-11-05T02:11:01Z

```
