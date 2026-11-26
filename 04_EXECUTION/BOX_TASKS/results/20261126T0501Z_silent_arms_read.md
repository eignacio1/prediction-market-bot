# Box task `silent_arms_read` — 20261126T0501Z_silent_arms_read

- request: `04_EXECUTION/BOX_TASKS/requests/20261126T0501Z_silent_arms_read.toml`
- note: (none)
- ran: 2026-11-26T05:02:00Z on root@157.230.91.33:/opt/prediction-market-bot
- exit code: 0
- command (allowlisted, scripts/box_tasks.py): `PYTHONPATH=src:. venv/bin/python -m prediction_market_bot.pregame_shadow.silent_arms`

```
[IDLE   ] MLB game-market shadow: no games in the last 12h, nothing expected (last game 2026-10-29, none scheduled after)
[OK     ] NFL shadow: 1 game(s) started in the last 12h, rows written
[OK     ] NFL QB challenger shadow: 1 game(s) started in the last 12h, all served inside their T1 window (12-48h pre-start)
[OK     ] NFL passing-yards pre-kickoff snapshot (W81.3): 1 game(s) started in the last 12h, all served inside their T1 window (0-0.5h pre-start)
[OK     ] NHL shadow: 14 game(s) started in the last 12h, rows written
[OK     ] NBA engine v1 (EXP-044): 9 game(s) started in the last 12h, rows written
[OK     ] NBA engine v2 (EXP-044b): 9 game(s) started in the last 12h, rows written
[OK     ] NBA engine v3 (EXP-044c): 9 game(s) started in the last 12h, rows written
[IDLE   ] NBA preseason shadow: no games in the last 12h, nothing expected (last game 2026-10-17, none scheduled after)
[OK     ] NBA regular-season shadow: 9 game(s) started in the last 12h, rows written
[OK     ] NBA player points shadow: 9 game(s) started in the last 12h, rows written
[OK     ] NBA player points minutes+injury challenger (EXP-040): 9 game(s) started in the last 12h, rows written
[IDLE   ] T1 MLB paper pipeline: no games in the last 30h, nothing expected (last game 2026-10-29, none scheduled after)
[IDLE   ] T4 MLB live: no games in the last 3h, nothing expected (last game 2026-10-29, none scheduled after)
[OK     ] NBA player props EXP-047: 9 game(s) started in the last 12h, rows written
[IDLE   ] NBA player props EXP-047-C1 (lineup-cross): no games in the last 12h, nothing expected (no games on the schedule (offseason or no slate))
[OK     ] NBA player props EXP-047-C2: 9 game(s) started in the last 12h, rows written
[OK     ] NBA player props EXP-047-S (shrunk means): 9 game(s) started in the last 12h, rows written
[OK     ] Ride/fade board (decisions): 24 game(s) started in the last 12h, rows written
[OK     ] Arm orders (demo forward test): 24 game(s) started in the last 12h, rows written
[SILENT ] NBA combo pot-of-gold shadow (W126.4) is SILENT: 9 game(s) started in the last 12h but no rows found (looked back 12h) (last row none found)
[SILENT ] NBA combo RFQ demo execution (W130.3) is SILENT: 9 game(s) started in the last 12h but no rows for 23.8h (last row 2026-11-25 05:13Z)
[IDLE   ] NHL in-play shadow pricer (W129.7): no games in the last 3h, nothing expected (no games on the schedule (offseason or no slate))
[OK     ] nba_player_box_2026: data/raw/nba/players_2026.json ok (1231 games)

```
