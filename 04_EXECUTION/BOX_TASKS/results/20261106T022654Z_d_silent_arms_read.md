# Box task `silent_arms_read` — 20261106T022654Z_d_silent_arms_read

- request: `04_EXECUTION/BOX_TASKS/requests/20261106T022654Z_d_silent_arms_read.toml`
- note: W104 close (SW-9)
- ran: 2026-11-06T02:27:35Z on root@157.230.91.33:/opt/prediction-market-bot
- exit code: 0
- command (allowlisted, scripts/box_tasks.py): `PYTHONPATH=src:. venv/bin/python -m prediction_market_bot.pregame_shadow.silent_arms`

```
[IDLE   ] MLB game-market shadow: no games in the last 12h, nothing expected (last game 2026-10-29, none scheduled after)
[OK     ] NFL shadow: 1 game(s) started in the last 12h, rows written
[OK     ] NFL QB challenger shadow: 1 game(s) started in the last 12h, all served inside their T1 window (12-48h pre-start)
[OK     ] NFL passing-yards pre-kickoff snapshot (W81.3): 1 game(s) started in the last 12h, all served inside their T1 window (0-0.5h pre-start)
[OK     ] NHL shadow: 10 game(s) started in the last 12h, rows written
[OK     ] NBA engine v1 (EXP-044): 1 game(s) started in the last 12h, rows written
[OK     ] NBA engine v2 (EXP-044b): 1 game(s) started in the last 12h, rows written
[OK     ] NBA engine v3 (EXP-044c): 1 game(s) started in the last 12h, rows written
[IDLE   ] NBA preseason shadow: no games in the last 12h, nothing expected (last game 2026-10-17, none scheduled after)
[OK     ] NBA regular-season shadow: 1 game(s) started in the last 12h, rows written
[OK     ] NBA player points shadow: 1 game(s) started in the last 12h, rows written
[OK     ] NBA player points minutes+injury challenger (EXP-040): 1 game(s) started in the last 12h, rows written
[IDLE   ] T1 MLB paper pipeline: no games in the last 30h, nothing expected (last game 2026-10-29, none scheduled after)
[IDLE   ] T4 MLB live: no games in the last 3h, nothing expected (last game 2026-10-29, none scheduled after)
[OK     ] nba_player_box_2026: data/raw/nba/players_2026.json ok (1231 games)

```
