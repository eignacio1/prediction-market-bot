# Box task `box_memory_read` — 20261105T020020Z_w_box_memory_read

- request: `04_EXECUTION/BOX_TASKS/requests/20261105T020020Z_w_box_memory_read.toml`
- note: Wave 100 close / window handoff read (read-only)
- ran: 2026-11-05T02:00:39Z on root@157.230.91.33:/opt/prediction-market-bot
- exit code: 0
- command (allowlisted, scripts/box_tasks.py): `PYTHONPATH=src:. venv/bin/python scripts/box_memory_read.py --since '24 hours ago'`

```
== meminfo / load ==
  MemTotal:         984676 kB
  MemAvailable:     223552 kB
  SwapTotal:       2097148 kB
  SwapFree:        1501328 kB
  loadavg: 2.76 4.93 7.74 4/156 541930

== bot python processes now (13) ==
  pid 533346  scripts/run_nba_pregame_shadow.py --bands T3               rss  146.6 MB  peak  334.0 MB  swap   80.8 MB   <-- 3 copies running
  pid 534205  scripts/run_nba_player_points_shadow.py --bands T3         rss  130.9 MB  peak  314.6 MB  swap   88.6 MB   <-- 3 copies running
  pid 541756  scripts/demo_cancel_sweeper.py                             rss  125.9 MB  peak  241.0 MB  swap   13.0 MB
  pid 484688  /opt/prediction-market-bot/venv/bin/python src/prediction_ rss   19.2 MB  peak  149.3 MB  swap   69.6 MB
  pid 541930  scripts/box_memory_read.py                                 rss   13.1 MB  peak   13.1 MB  swap    0.0 MB   <-- 2 copies running
  pid 530278  /opt/prediction-market-bot/venv/bin/python src/prediction_ rss    6.2 MB  peak  170.0 MB  swap  112.4 MB
  pid 540830  scripts/web_dashboard.py                                   rss    3.8 MB  peak  133.3 MB  swap   56.4 MB
  pid 533333  scripts/run_nba_pregame_shadow.py --bands T3               rss    1.8 MB  peak    3.2 MB  swap    0.2 MB   <-- 3 copies running
  pid 534190  scripts/run_nba_player_points_shadow.py --bands T3         rss    1.8 MB  peak    3.1 MB  swap    0.2 MB   <-- 3 copies running
  pid 541929  scripts/box_memory_read.py                                 rss    1.8 MB  peak    1.8 MB  swap    0.0 MB   <-- 2 copies running
  pid 530277  timeout 21600 /opt/prediction-market-bot/venv/bin/python s rss    1.6 MB  peak    1.9 MB  swap    0.0 MB
  pid 533335  scripts/run_nba_pregame_shadow.py --bands T3               rss    1.0 MB  peak    2.1 MB  swap    0.2 MB   <-- 3 copies running
  pid 534193  scripts/run_nba_player_points_shadow.py --bands T3         rss    1.0 MB  peak    2.1 MB  swap    0.2 MB   <-- 3 copies running

== OOM kills since '24 hours ago': 45 ==
  python               kills 43  largest anon-rss at kill 205.9 MB
  systemd              kills 2   largest anon-rss at kill 0.0 MB

== lock skips (logs/t3_skips.jsonl): 30  {"nba_pregame_shadow_t3": 16, "nba_player_points_t3": 10, "nhl_staked_t3": 2, "mlb_pregame_shadow_t3": 1, "pregame_shadow_t3": 1} ==

```
