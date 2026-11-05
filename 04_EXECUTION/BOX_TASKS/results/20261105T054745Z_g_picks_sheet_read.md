# Box task `picks_sheet_read` — 20261105T054745Z_g_picks_sheet_read

- request: `04_EXECUTION/BOX_TASKS/requests/20261105T054745Z_g_picks_sheet_read.toml`
- note: W101 close read (window)
- ran: 2026-11-05T05:48:43Z on root@157.230.91.33:/opt/prediction-market-bot
- exit code: 0
- command (allowlisted, scripts/box_tasks.py): `PYTHONPATH=src:. venv/bin/python scripts/picks_sheet_read.py`

```
sheet 2026-11-05 built 2026-11-05T05:37:13.274021+00:00 n_picks=3534 games=87
picks/game: median 28 max 156 min 1
by arm: NBAMIN_NBA_PLAYER_POINTS_T3=79, NBA_NBA_GAME_TOTAL_T2=28, NBA_NBA_GAME_TOTAL_T3=110, NBA_NBA_MONEYLINE_T1=8, NBA_NBA_MONEYLINE_T2=24, NBA_NBA_MONEYLINE_T3=10, NBA_NBA_PLAYER_POINTS_T2=139, NBA_NBA_PLAYER_POINTS_T3=298, NBA_NBA_SPREAD_T2=213, NBA_NBA_SPREAD_T3=173, NBA_NBA_TEAM_TOTAL_T2=17, NBA_NBA_TEAM_TOTAL_T3=137, NFLQB_NFL_MONEYLINE_T1=2, NFL_NFL_GAME_TOTAL_T1=19, NFL_NFL_MONEYLINE_T1=2, NFL_NFL_SPREAD_T1=16, NFL_NFL_TEAM_TOTAL_T1=24, NHL_GAME_TOTAL_T2=16, NHL_GAME_TOTAL_T3=17, NHL_MONEYLINE_T2=4, NHL_MONEYLINE_T3=4, NHL_PUCK_LINE_T2=12, NHL_PUCK_LINE_T3=12, nba_engine_v1=1012, nba_engine_v2=647, nba_engine_v3=511
picks with stored reasons: 3532/3534
  no-reason cause: 2 x no reasons available (this arm's model does not expose per-factor contributions)
results: open=3534
demo orders: placed=2296; no order row=1118; skip: mid_gap_above_threshold=97; skip: one_sided_or_crossed_book=11; skip: not_listed_on_demo=11; skip: transient error — max retries (4) exceeded=1
games where arms disagree: 22
  biggest: KXNBASPREAD-26NOV04MIALAC 156 picks over 33 tickers
  biggest: KXNBATEAMTOTAL-26NOV04MIALAC 137 picks over 35 tickers
  biggest: KXNBASPREAD-26NOV04LALSAC 120 picks over 33 tickers
sample: NBA_NBA_MONEYLINE_T2 | NBA nba moneyline ATL: YES | bot 0.8351 vs 0.59 | edge 0.2282 | ['home team points allowed per game, last 30 = 124.5: supports this pick (12.2 pts)', 'away team points scored per game, last 30 = 120.633: supports this pick (6.8 pts)', 'home team points scored per game, last 30 = 113.533: works against this pick (3.6 pts)']
sample: NBA_NBA_MONEYLINE_T3 | NBA nba moneyline ATL: YES | bot 0.8351 vs 0.56 | edge 0.2579 | ['home team points allowed per game, last 30 = 124.5: supports this pick (12.2 pts)', 'away team points scored per game, last 30 = 120.633: supports this pick (6.8 pts)', 'home team points scored per game, last 30 = 113.533: works against this pick (3.6 pts)']
sample: nba_engine_v2 | nba moneyline ATL: YES | bot 0.677 vs 0.59 | edge 0.0701 | ['home team offense (points per 100 possessions) vs league average = 108.975: supports this pick (13.3 pts)', 'away team defense (points allowed per 100 possessions) vs league average = 110.495: supports this pick (8.8 pts)', 'home team defense (points allowed per 100 possessions) vs league average = 114.943: supports this pick (3.8 pts)']

```
