# Box task `box_memory_read` — 20261126T0452Z_box_memory_read

- request: `04_EXECUTION/BOX_TASKS/requests/20261126T0452Z_box_memory_read.toml`
- note: (none)
- ran: 2026-11-26T04:52:39Z on root@157.230.91.33:/opt/prediction-market-bot
- exit code: 0
- command (allowlisted, scripts/box_tasks.py): `PYTHONPATH=src:. venv/bin/python scripts/box_memory_read.py --since '24 hours ago'`

```
== meminfo / load ==
  MemTotal:         984676 kB
  MemAvailable:      40060 kB
  SwapTotal:       2097148 kB
  SwapFree:         897212 kB
  loadavg: 3.17 2.63 2.62 5/167 1795577

== bot python processes now (19) ==
  pid 1783874 scripts/run_nba_pregame_shadow.py --bands T3               rss  227.0 MB  peak  752.6 MB  swap  565.3 MB   <-- 3 copies running
  pid 1795497 scripts/demo_cancel_sweeper.py                             rss  218.2 MB  peak  263.4 MB  swap   16.0 MB
  pid 1795501 -m prediction_market_bot.nba_engine.live                   rss  131.4 MB  peak  273.5 MB  swap  153.5 MB   <-- 4 copies running
  pid 1795500 scripts/run_nfl_inplay_shadow.py                           rss   37.6 MB  peak   77.3 MB  swap   27.0 MB   <-- 3 copies running
  pid 1795577 scripts/box_memory_read.py                                 rss   13.1 MB  peak   13.1 MB  swap    0.0 MB   <-- 2 copies running
  pid 1795331 scripts/thin_market_depth_capture.py                       rss   11.6 MB  peak   90.7 MB  swap   88.4 MB   <-- 2 copies running
  pid 1785396 /opt/prediction-market-bot/venv/bin/python src/prediction_ rss    6.9 MB  peak  147.5 MB  swap   79.5 MB
  pid 1769711 /opt/prediction-market-bot/venv/bin/python src/prediction_ rss    6.0 MB  peak  193.7 MB  swap  113.5 MB
  pid 1793653 scripts/web_dashboard.py                                   rss    2.9 MB  peak  291.0 MB  swap   84.4 MB
  pid 1783861 scripts/run_nba_pregame_shadow.py --bands T3               rss    1.8 MB  peak    3.1 MB  swap    0.2 MB   <-- 3 copies running
  pid 1795325 scripts/thin_market_depth_capture.py                       rss    1.8 MB  peak    3.2 MB  swap    0.2 MB   <-- 2 copies running
  pid 1795491 scripts/run_nfl_inplay_shadow.py                           rss    1.8 MB  peak    3.2 MB  swap    0.2 MB   <-- 3 copies running
  pid 1795492 -m prediction_market_bot.nba_engine.live                   rss    1.8 MB  peak    3.2 MB  swap    0.2 MB   <-- 4 copies running
  pid 1795499 -m prediction_market_bot.nba_engine.live                   rss    1.8 MB  peak    1.8 MB  swap    0.0 MB   <-- 4 copies running
  pid 1795576 scripts/box_memory_read.py                                 rss    1.8 MB  peak    1.8 MB  swap    0.0 MB   <-- 2 copies running
  pid 1769709 timeout 21600 /opt/prediction-market-bot/venv/bin/python s rss    1.6 MB  peak    1.8 MB  swap    0.0 MB
  pid 1795496 -m prediction_market_bot.nba_engine.live                   rss    1.6 MB  peak    1.8 MB  swap    0.0 MB   <-- 4 copies running
  pid 1783864 scripts/run_nba_pregame_shadow.py --bands T3               rss    1.0 MB  peak    2.0 MB  swap    0.2 MB   <-- 3 copies running
  pid 1795495 scripts/run_nfl_inplay_shadow.py                           rss    1.0 MB  peak    1.9 MB  swap    0.2 MB   <-- 3 copies running

== OOM kills since '24 hours ago': 20 ==
  python               kills 20  largest anon-rss at kill 207.4 MB

== lock skips (logs/t3_skips.jsonl): 540  {"nba_pregame_shadow_t3": 292, "nba_player_points_t3": 21, "nhl_staked_t3": 102, "mlb_pregame_shadow_t3": 1, "pregame_shadow_t3": 24, "nhl_staked_t2": 52, "nba_pregame_shadow_t2": 44, "nba_player_points_t2": 2, "pregame_shadow_t2": 1, "nfl_inplay_shadow": 1} ==

```
