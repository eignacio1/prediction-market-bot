# Box task `state_of_the_bot_read` — 20261126T0227Z_state_of_the_bot_read

- request: `04_EXECUTION/BOX_TASKS/requests/20261126T0227Z_state_of_the_bot_read.toml`
- note: W130.5: fresh read on deployed #602
- ran: 2026-11-26T02:39:15Z on root@157.230.91.33:/opt/prediction-market-bot
- exit code: 0
- command (allowlisted, scripts/box_tasks.py): `PYTHONPATH=src:. venv/bin/python scripts/state_of_the_bot.py`

```
# STATE OF THE BOT - read 2026-11-26T02:31:42Z

Measured by `scripts/state_of_the_bot.py` (read-only) on host `earlgrey` (the box when run by the box task). Checkout: `18cb9acb 2026-11-25T18:27:02-08:00 W130.5: fresh d6 / silent-arms / state reads`. No line below is written from memory;
a section that could not be read says so. Data epoch for orders: 2026-11-06T01:03:42Z.

## NBA

**Arms logging** (rows with a timestamp; silent-arms status)

| arm | status | games in window | rows 24h | rows 7d | last row |
|---|---|---|---|---|---|
| nba_engine_v1 | ok | 7 | 918 | 4896 | 2026-11-26T02:02Z |
| nba_engine_v2 | ok | 7 | 918 | 4896 | 2026-11-26T02:03Z |
| nba_engine_v3 | ok | 7 | 918 | 4896 | 2026-11-26T02:07Z |
| nba_preseason_shadow | idle | 0 | 0 | 0 | n/a |
| nba_shadow | ok | 7 | 6173 | 37961 | 2026-11-26T02:24Z |
| nba_player_points_shadow | ok | 7 | 3255 | 17323 | 2026-11-26T02:24Z |
| nba_player_points_minutes_shadow | ok | 7 | 850 | 4538 | 2026-11-26T02:24Z |
| nba_props_exp047 | ok | 7 | 15273 | 79343 | 2026-11-26T00:42Z |
| nba_props_exp047_c1 | idle | 0 | 0 | 0 | n/a |
| nba_props_exp047_c2 | ok | 7 | 14941 | 14941 | 2026-11-26T00:42Z |
| nba_props_exp047_s | silent | 7 | 0 | 0 | n/a |
| nba_combo_shadow | idle | 0 | 0 | 0 | n/a |

**Demo orders** (arm-order log, post-epoch, YES side for fills)

| arm | orders 24h/7d/epoch | would 7d | skips 7d | refused epoch |
|---|---|---|---|---|
| ERROR | 0/0/0 | 0 | 0 | 0 |
| FADE | 26/322/635 | 0 | 107 | 0 |
| MODEL_FADE | 77/715/887 | 0 | 490 | 45 |
| MOMENTUM | 23/426/732 | 0 | 338 | 0 |
| NO_BET | 0/0/0 | 0 | 35034 | 0 |
| RIDE | 2/286/610 | 0 | 431 | 2 |
- fills: 25 filled of 25 looked up (1686 placed YES-side); settled 25; P&L per filled contract before fees 0.100 on 25 settled
- D6: not computed (sport not in read)

## NFL

**Arms logging** (rows with a timestamp; silent-arms status)

| arm | status | games in window | rows 24h | rows 7d | last row |
|---|---|---|---|---|---|
| nfl_shadow | ok | 1 | 1676 | 15522 | 2026-11-26T00:38Z |
| nfl_qb_challenger | ok | 1 | 30 | 192 | 2026-11-26T00:14Z |
| nfl_passyds_snap | ok | 1 | 306 | 2296 | 2026-11-26T02:02Z |

**Demo orders** (arm-order log, post-epoch, YES side for fills)

| arm | orders 24h/7d/epoch | would 7d | skips 7d | refused epoch |
|---|---|---|---|---|
| ERROR | 0/0/0 | 0 | 0 | 0 |
| FADE | 0/0/15 | 0 | 0 | 0 |
| MOMENTUM | 0/0/1 | 0 | 0 | 0 |
| NO_BET | 0/0/0 | 0 | 15522 | 0 |
| RIDE | 0/0/47 | 0 | 0 | 0 |
- fills: 3 filled of 3 looked up (18 placed YES-side); settled 3; P&L per filled contract before fees 0.497 on 3 settled
- D6: not computed (sport not in read)

## NHL

**Arms logging** (rows with a timestamp; silent-arms status)

| arm | status | games in window | rows 24h | rows 7d | last row |
|---|---|---|---|---|---|
| nhl_shadow | ok | 12 | 437 | 3545 | 2026-11-26T02:28Z |
| nhl_inplay_shadow | idle | 0 | 0 | 0 | n/a |

**Demo orders** (arm-order log, post-epoch, YES side for fills)

| arm | orders 24h/7d/epoch | would 7d | skips 7d | refused epoch |
|---|---|---|---|---|
| ERROR | 0/0/0 | 0 | 0 | 0 |
| FADE | 0/45/50 | 0 | 49 | 0 |
| MODEL_FADE | 4/92/117 | 0 | 63 | 0 |
| MOMENTUM | 0/35/42 | 0 | 9 | 0 |
| NO_BET | 0/0/0 | 0 | 2419 | 0 |
| RIDE | 11/344/394 | 0 | 451 | 0 |
| UNROUTED | 0/0/0 | 0 | 0 | 0 |
- fills: 0 filled of 0 looked up (316 placed YES-side); settled 0; P&L per filled contract before fees n/a on 0 settled
- D6: not computed (sport not in read)

## MLB

**Arms logging** (rows with a timestamp; silent-arms status)

| arm | status | games in window | rows 24h | rows 7d | last row |
|---|---|---|---|---|---|
| mlb_shadow | idle | 0 | 0 | 0 | n/a |
| t1_mlb | idle | 0 | n/a | n/a | 2026-11-25T22:15:27.672000+00:00 |
| t4_mlb | idle | 0 | n/a | n/a | 2026-10-29T03:10:34.714537+00:00 |

**Demo orders** (arm-order log, post-epoch, YES side for fills)

- no arm-order rows for this sport
- D6: not computed (sport not in read)

## Cross-sport arms (ride board, arm-order router)

**Arms logging** (rows with a timestamp; silent-arms status)

| arm | status | games in window | rows 24h | rows 7d | last row |
|---|---|---|---|---|---|
| ride_board | ok | 20 | 24442 | 172664 | 2026-11-26T02:29Z |
| arm_orders | ok | 20 | n/a | n/a | 2026-11-26T02:31:26+00:00 |

**Demo orders** (arm-order log, post-epoch, YES side for fills)

- no arm-order rows for this sport
- D6: not computed (sport not in read)

Fills lookup: 1881 read-only GETs - BUDGET EXHAUSTED, fills may be understated.
D6 overall: **18/129** read 2026-11-26T02:31:42Z (138614 arm-order rows, 300178 ledger rows).

## Installs pending (registry status = paused: built, registered, not running)

- `cron|7 */6 * * *|scripts/run_mlb_pregame_shadow.py --bands T1 --refresh` - MLB game-market pre-game shadow arm: evaluates and logs forecasts for its band, no orders (T1).
- `systemd|t4-mlb.timer` - Timer unit for t4-mlb; enabled but dead since 2026-07-04, the service runs persistently instead.
- `workflow|nhl_goalie_probe.yml` - Read-only probe every 10 minutes in the NHL evening window timing when api-web.nhle.com first shows a confirmed starting goalie (EXP-036 T3); appends to the dat
- `workflow|post_game_resolve.yml` - Post-game resolve job; schedule paused since 2026-07-29 (T-399), manual dispatch only.
- `cron|55 21,22,23 * * *|scripts/news_burst_capture.py --interval 20 --minutes 30` - W107.2 B-060: 30-min ~20 s top-of-book burst of open NBA game-line markets around the injury-report publish window, to measure a news lag the 20-min archive can
- `cron|29 13 * * *|scripts/run_nhl_event_store_refresh.py` - W116.3 / B-092 (GG-1953): daily refresh of the NHL event store (current + previous season; resumable fetch of public NHL API games, streamed two-season compile,
- `cron|17 14 * * *|scripts/run_disk_retention.py` - W118.4 / B-102: daily disk retention -- gzip-compress (sha256 round trip, never delete) old evidence files whose readers read .gz (KALSHI_HISTORY raw stores, mi
- `cron|2,22,42 6-16 * * *|scripts/archive_dense_capture.py --mode props` - W124.4 dense capture (props from first listing, 06-16 UTC gap). PROOF P3: W123 H1/H3/H4 could not be judged on thin data. Public Kalshi endpoints, no orders. PA
- `cron|3-58/5 * * * *|scripts/archive_dense_capture.py --mode games` - W124.4 dense capture (5-min game-family snapshots in the 3 h before start). PROOF P3: W123 H1/H3/H4 could not be judged on thin data. Public Kalshi endpoints, n
- `cron|1-56/5 * * * *|scripts/archive_dense_capture.py --mode prints` - W124.4 dense capture (public trade prints forward). PROOF P3: W123 H1/H3/H4 could not be judged on thin data. Public Kalshi endpoints, no orders. PAUSED until t
- `cron|0 10 * * 2|scripts/run_evidence_weekly.py` - W121.1: weekly evidence look (Tuesday 10:00 UTC cut) -- per-leaf per-arm pooled posterior and e-process for v1 and every candidate map, carried forward from the
- `cron|41 * * * *|scripts/nba_combo_shadow.py` - W126.4 (B-024) pot-of-gold combo arm: prices every open Kalshi NBA same-game combo from the engine's joint draws and logs engine P, product-of-legs P, legs pric
- `cron|17 18 * * *|scripts/combo_rfq_demo.py` - W130.3 (EXP-COMBOORD-001) pot-of-gold combo arm, execution leg: once a day sends RFQs in the Kalshi DEMO on kept NBA same-game combos (no flags, no teammate-poi
- `cron|17 9 * * *|scripts/data_offload.py --scope` - W128.5 data offload: MoneyPuck, NHL API (goalie logs, officials), Baseball Savant CSVs and MLB boxscores fetched by the server instead of Muse chunks. DEPTH D4 
- `cron|10 14,17,20,23 * 3-10 *|scripts/mlb_board_daily.py` - W129.3 MLB daily board: prices the day's slate with the MLB engine from SYNCED off-box inputs (no network) so shadow rows carry engine_p / engine_gap (EXP-MLBEN
- `cron|*/2 17-23,0-6 * * *|scripts/nhl_inplay_shadow.py` - W129.7: NHL in-play shadow pricer (T4NHL-ARITH). Polls the NHL public live feed every 2 minutes in the game window, prices the open Kalshi NHL game / spread / t
- `cron|*/2 17-23,0-6 * * *|scripts/run_nfl_inplay_shadow.py` - W130.1: NFL in-play shadow pricer (T4NFL-ARITH and T4NFL-FLOW). Polls the ESPN live plays feed every 2 minutes in the game window, prices the open Kalshi NFL ga

## Last wave's verdicts (first_look_verdicts_read.py, newest engine JSON)

~~~
engine file: engine_20261125T135336Z.json  generated: 2026-11-25T13:49:01Z
summary: {"cells": 49, "logging": 49, "with_outcomes": 46, "reached_look": 25}
cells with a released verdict: 25 of 49

cell | n | d-Brier vs market [95% CI] | d-Brier vs climatology [95% CI] | verdict | next look
NFL_NFL_GAME_TOTAL_T1 | 60 | -0.0161 [-0.0294, -0.0027] | +0.0024 [-0.0079, +0.0128] | RULED_OUT | first look reached
NFL_NFL_GAME_TOTAL_T2 | 60 | -0.0157 [-0.0299, -0.0011] | +0.0024 [-0.0073, +0.0131] | RULED_OUT | first look reached
NFL_NFL_GAME_TOTAL_T3 | 60 | -0.0140 [-0.0279, +0.0007] | +0.0023 [-0.0074, +0.0128] | SHADOW | first look reached
NFL_NFL_MONEYLINE_T1 | 60 | -0.0061 [-0.0343, +0.0254] | +0.0174 [-0.0150, +0.0476] | SHADOW | first look reached
NFL_NFL_MONEYLINE_T2 | 60 | -0.0070 [-0.0360, +0.0250] | +0.0174 [-0.0166, +0.0487] | SHADOW | first look reached
NFL_NFL_MONEYLINE_T3 | 60 | -0.0075 [-0.0364, +0.0239] | +0.0174 [-0.0166, +0.0487] | SHADOW | first look reached
NFL_NFL_SPREAD_T1 | 60 | -0.0076 [-0.0217, +0.0078] | +0.0049 [-0.0112, +0.0200] | SHADOW | first look reached
NFL_NFL_SPREAD_T2 | 60 | -0.0084 [-0.0232, +0.0078] | +0.0049 [-0.0113, +0.0202] | SHADOW | first look reached
NFL_NFL_SPREAD_T3 | 60 | -0.0080 [-0.0231, +0.0082] | +0.0061 [-0.0105, +0.0212] | SHADOW | first look reached
NFL_NFL_TEAM_TOTAL_T1 | 60 | -0.0071 [-0.0148, +0.0009] | +0.0023 [-0.0052, +0.0092] | SHADOW | first look reached
NFL_NFL_TEAM_TOTAL_T2 | 60 | -0.0076 [-0.0151, +0.0006] | +0.0023 [-0.0054, +0.0096] | SHADOW | first look reached
NFL_NFL_TEAM_TOTAL_T3 | 60 | -0.0070 [-0.0148, +0.0015] | +0.0030 [-0.0052, +0.0107] | SHADOW | first look reached
NFLQB_NFL_MONEYLINE_T1 | 60 | -0.0096 [-0.0296, +0.0122] | +0.0446 [+0.0150, +0.0744] | SHADOW | first look reached
NBA_NBA_GAME_TOTAL_T1 | 150 | -0.0037 [-0.0122, +0.0040] | +0.0107 [-0.0107, +0.0310] | SHADOW | first look reached
NBA_NBA_GAME_TOTAL_T2 | 150 | -0.0113 [-0.0194, -0.0035] | +0.0090 [-0.0115, +0.0310] | RULED_OUT | first look reached
NBA_NBA_GAME_TOTAL_T3 | 150 | -0.0140 [-0.0238, -0.0042] | +0.0179 [-0.0020, +0.0380] | RULED_OUT | first look reached
NBA_NBA_MONEYLINE_T1 | 150 | -0.0226 [-0.0456, -0.0001] | +0.0375 [+0.0062, +0.0672] | RULED_OUT | first look reached
NBA_NBA_MONEYLINE_T2 | 150 | -0.0267 [-0.0472, -0.0067] | +0.0400 [+0.0098, +0.0702] | RULED_OUT | first look reached
NBA_NBA_MONEYLINE_T3 | 150 | -0.0274 [-0.0483, -0.0075] | +0.0423 [+0.0118, +0.0720] | RULED_OUT | first look reached
NBA_NBA_SPREAD_T1 | 150 | -0.0138 [-0.0257, -0.0024] | +0.0132 [-0.0052, +0.0323] | RULED_OUT | first look reached
NBA_NBA_SPREAD_T2 | 150 | -0.0186 [-0.0295, -0.0075] | +0.0124 [-0.0058, +0.0303] | RULED_OUT | first look reached
NBA_NBA_SPREAD_T3 | 150 | -0.0155 [-0.0260, -0.0047] | +0.0175 [-0.0009, +0.0364] | RULED_OUT | first look reached
NBA_NBA_TEAM_TOTAL_T1 | 150 | -0.0037 [-0.0114, +0.0045] | +0.0126 [-0.0029, +0.0274] | SHADOW | first look reached
NBA_NBA_TEAM_TOTAL_T2 | 150 | -0.0111 [-0.0173, -0.0047
~~~

## Red signals

- arm SILENT: NBA player props EXP-047-S (shrunk means) is SILENT: 7 game(s) started in the last 12h but no rows found (looked back 12h) (last row none found)
- box: SURFACE BUDGET RED: SILENT ARM NBA player props EXP-047-S (shrunk means): NBA player props EXP-047-S (shrunk means) is SILENT: 7 game(s) started in the last 12h but no rows found (looked back 12h) (last row none found)

## Raw health / budget / deploy reads

~~~
=== VPS Health Check (W72.3) ===
=== HEALTHY: 0 faults, 0 warning(s) ===

as of 2026-11-26T02:38:55Z · box HEAD a796fa98 · 95 live components (+0 registry-live NOT installed, excluded) · 0 unreviewed · 0 stale/down/behind · no alarm: 0 unexplained, 9 with a written reason
  registry vs box: 0 installed-but-unmirrored · 0 mirrored-but-not-installed · units 0/0
  healthcheck: HEALTHY: 0 faults, 0 warning(s) · deploy: deployed @ 2026-11-26T02:36:50Z
  systemd|pmbot-web-dashboard.service    active/running   run a796fa98 · 0.0h behind HEAD · restarts 0
  systemd|t4-mlb.service                 active/running   run 18cb9acb · 0.0h behind HEAD · restarts 0
  SURFACE BUDGET RED: SILENT ARM NBA player props EXP-047-S (shrunk means): NBA player props EXP-047-S (shrunk means) is SILENT: 7 game(s) started in the last 12h but no rows found (looked back 12h) (last row none found)

DEPLOY TRUTH (W72.3 / GG-661, GG-668: merge != deploy != activation; alarm-only):
  OK deploy status: deployed at 2026-11-26T02:36:50Z
  OK box HEAD a796fa98 behind origin/main fdd06d01: 1 file(s) a service uses (src/prediction_market_bot/decision_trees/props_arm_orders.py) unpulled for 2.9 min (alarm > 45 min; check logs/vps_deploy.log for a red gate or dirty-tree abort)
  OK t4-mlb runs box HEAD code (a796fa98; started 2026-11-26T02:30:34Z)
  OK pmbot-web-dashboard runs box HEAD code (a796fa98; started 2026-11-26T02:36:49Z)
~~~


```
