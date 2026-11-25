# Box task `box_memory_read` — 20261125T0605Z_box_memory_read

- request: `04_EXECUTION/BOX_TASKS/requests/20261125T0605Z_box_memory_read.toml`
- note: SW-9: headroom check before 128.5 data offload crons (operator asked: will it overload the box?)
- ran: 2026-11-25T06:00:35Z on root@157.230.91.33:/opt/prediction-market-bot
- exit code: 0
- command (allowlisted, scripts/box_tasks.py): `PYTHONPATH=src:. venv/bin/python scripts/box_memory_read.py --since '24 hours ago'`

```
== meminfo / load ==
  MemTotal:         984676 kB
  MemAvailable:     430036 kB
  SwapTotal:       2097148 kB
  SwapFree:        1890980 kB
  loadavg: 0.44 0.54 0.82 2/139 1725477

== bot python processes now (5) ==
  pid 1725399 scripts/demo_cancel_sweeper.py                             rss  176.0 MB  peak  267.3 MB  swap    0.0 MB
  pid 1666576 /opt/prediction-market-bot/venv/bin/python src/prediction_ rss   21.2 MB  peak  148.0 MB  swap   69.5 MB
  pid 1725477 scripts/box_memory_read.py                                 rss   13.2 MB  peak   13.2 MB  swap    0.0 MB   <-- 2 copies running
  pid 1723378 scripts/web_dashboard.py                                   rss   10.6 MB  peak  312.8 MB  swap   79.1 MB
  pid 1725476 scripts/box_memory_read.py                                 rss    1.8 MB  peak    1.8 MB  swap    0.0 MB   <-- 2 copies running

== OOM kills since '24 hours ago': 8 ==
  python               kills 8   largest anon-rss at kill 144.1 MB

== lock skips (logs/t3_skips.jsonl): 479  {"nba_pregame_shadow_t3": 253, "nba_player_points_t3": 21, "nhl_staked_t3": 92, "mlb_pregame_shadow_t3": 1, "pregame_shadow_t3": 24, "nhl_staked_t2": 46, "nba_pregame_shadow_t2": 39, "nba_player_points_t2": 2, "pregame_shadow_t2": 1} ==

```
