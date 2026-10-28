# Box task `silent_arms_read` — 20261027T051307Z_w_silent_arms_read

- request: `04_EXECUTION/BOX_TASKS/requests/20261027T051307Z_w_silent_arms_read.toml`
- note: Window: Wave 89 close
- ran: 2026-10-27T05:13:40Z on root@157.230.91.33:/opt/prediction-market-bot
- exit code: 0
- command (allowlisted, scripts/box_tasks.py): `PYTHONPATH=src:. venv/bin/python -m prediction_market_bot.pregame_shadow.silent_arms`

```
[SILENT ] MLB game-market shadow is SILENT: 1 game(s) started in the last 12h but no rows for 35.1h (last row 2026-10-25 18:07Z)
[OK     ] NFL shadow: 1 game(s) started in the last 12h, rows written
[OK     ] NFL QB challenger shadow: 1 game(s) started in the last 12h, all served inside their T1 window (12-48h pre-start)
[OK     ] NFL passing-yards pre-kickoff snapshot (W81.3): 1 game(s) started in the last 12h, all served inside their T1 window (0-0.5h pre-start)
[OK     ] NHL shadow: 3 game(s) started in the last 12h, rows written
[IDLE   ] NBA preseason shadow: no games in the last 12h, nothing expected
[OK     ] NBA regular-season shadow: 9 game(s) started in the last 12h, rows written
[OK     ] NBA player points shadow: 9 game(s) started in the last 12h, rows written
[OK     ] NBA player points minutes+injury challenger (EXP-040): 9 game(s) started in the last 12h, rows written
[OK     ] T1 MLB paper pipeline: 1 game(s) started in the last 30h, rows written
[IDLE   ] T4 MLB live: no games in the last 3h, nothing expected
[OK     ] nba_player_box_2026: data/raw/nba/players_2026.json ok (1231 games)

```
