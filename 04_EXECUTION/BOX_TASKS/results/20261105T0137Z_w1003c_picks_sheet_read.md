# Box task `picks_sheet_read` — 20261105T0137Z_w1003c_picks_sheet_read

- request: `04_EXECUTION/BOX_TASKS/requests/20261105T0137Z_w1003c_picks_sheet_read.toml`
- note: W100.3 read-only retry after deploy
- ran: 2026-11-05T01:43:02Z on root@157.230.91.33:/opt/prediction-market-bot
- exit code: 0
- command (allowlisted, scripts/box_tasks.py): `PYTHONPATH=src:. venv/bin/python scripts/picks_sheet_read.py`

```
sheet 2026-11-04 built 2026-11-04T22:47:29.660532+00:00 n_picks=2614 games=134
picks/game: median 8.0 max 74 min 1
by arm: NBAMIN_NBA_PLAYER_POINTS_T1=77, NBAMIN_NBA_PLAYER_POINTS_T2=17, NBA_NBA_GAME_TOTAL_T1=287, NBA_NBA_GAME_TOTAL_T2=136, NBA_NBA_MONEYLINE_T1=30, NBA_NBA_MONEYLINE_T2=24, NBA_NBA_PLAYER_POINTS_T1=281, NBA_NBA_PLAYER_POINTS_T2=282, NBA_NBA_SPREAD_T1=382, NBA_NBA_SPREAD_T2=317, NBA_NBA_TEAM_TOTAL_T1=311, NBA_NBA_TEAM_TOTAL_T2=65, NFLQB_NFL_MONEYLINE_T1=2, NFL_NFL_GAME_TOTAL_T1=19, NFL_NFL_MONEYLINE_T1=2, NFL_NFL_SPREAD_T1=17, NFL_NFL_TEAM_TOTAL_T1=24, NHL_GAME_TOTAL_T1=6, NHL_GAME_TOTAL_T2=91, NHL_GAME_TOTAL_T3=80, NHL_MONEYLINE_T1=13, NHL_MONEYLINE_T2=17, NHL_MONEYLINE_T3=15, NHL_PUCK_LINE_T1=32, NHL_PUCK_LINE_T2=50, NHL_PUCK_LINE_T3=37
picks with stored reasons: 2353/2614
  no-reason cause: 259 x no reasons available
  no-reason cause: 2 x no reasons available (this arm's model does not expose per-factor contributions)
results: open=2614
demo orders: placed=2609; skip: not_listed_on_demo=2; skip: one_sided_or_crossed_book=1; skip: mid_gap_above_threshold=1; no order row=1
games where arms disagree: 2
  biggest: KXNBATEAMTOTAL-26NOV04ATLWAS 74 picks over 37 tickers
  biggest: KXNBAPTS-26NOV04PHIDET 69 picks over 35 tickers
  biggest: KXNBASPREAD-26NOV04PHIDET 65 picks over 33 tickers
note: nba_engine_v1: no pick in window
note: nba_engine_v2: no pick in window
note: nba_engine_v3: no rows file yet
sample: NBA_NBA_MONEYLINE_T1 | NBA nba moneyline ATL: YES | bot 0.8351 vs 0.57 | edge 0.2479 | ['home team points allowed per game, last 30 = 124.5: supports this pick (12.2 pts)', 'away team points scored per game, last 30 = 120.633: supports this pick (6.8 pts)', 'home team points scored per game, last 30 = 113.533: works against this pick (3.6 pts)']
sample: NBA_NBA_MONEYLINE_T2 | NBA nba moneyline ATL: YES | bot 0.8351 vs 0.59 | edge 0.2282 | ['home team points allowed per game, last 30 = 124.5: supports this pick (12.2 pts)', 'away team points scored per game, last 30 = 120.633: supports this pick (6.8 pts)', 'home team points scored per game, last 30 = 113.533: works against this pick (3.6 pts)']
sample: NBA_NBA_MONEYLINE_T1 | NBA nba moneyline WAS: NO | bot 0.8351 vs 0.43 | edge 0.2479 | ['home team points allowed per game, last 30 = 124.5: supports this pick (12.2 pts)', 'away team points scored per game, last 30 = 120.633: supports this pick (6.8 pts)', 'home team points scored per game, last 30 = 113.533: works against this pick (3.6 pts)']

```
