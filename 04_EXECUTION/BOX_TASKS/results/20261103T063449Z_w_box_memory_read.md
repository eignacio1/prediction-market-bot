# Box task `box_memory_read` — 20261103T063449Z_w_box_memory_read

- request: `04_EXECUTION/BOX_TASKS/requests/20261103T063449Z_w_box_memory_read.toml`
- note: Wave 98 close read (strategic window, read-only)
- ran: 2026-11-03T06:35:09Z on root@157.230.91.33:/opt/prediction-market-bot
- exit code: 0
- command (allowlisted, scripts/box_tasks.py): `PYTHONPATH=src:. venv/bin/python scripts/box_memory_read.py --since '24 hours ago'`

```
== meminfo / load ==
  MemTotal:         984676 kB
  MemAvailable:     333940 kB
  SwapTotal:       2097148 kB
  SwapFree:        1723968 kB
  loadavg: 2.08 2.05 2.41 3/148 439941

== bot python processes now (7) ==
  pid 438320  scripts/run_nba_pregame_shadow.py --bands T1               rss  172.0 MB  peak  365.7 MB  swap   80.9 MB   <-- 2 copies running
  pid 439876  scripts/demo_cancel_sweeper.py                             rss  144.4 MB  peak  223.0 MB  swap    0.0 MB
  pid 195670  /opt/prediction-market-bot/venv/bin/python src/prediction_ rss   20.0 MB  peak  147.6 MB  swap   70.6 MB
  pid 439941  scripts/box_memory_read.py                                 rss   13.1 MB  peak   13.1 MB  swap    0.0 MB   <-- 2 copies running
  pid 438862  scripts/web_dashboard.py                                   rss    4.6 MB  peak  116.8 MB  swap   59.9 MB
  pid 438309  scripts/run_nba_pregame_shadow.py --bands T1               rss    1.8 MB  peak    3.2 MB  swap    0.2 MB   <-- 2 copies running
  pid 439940  scripts/box_memory_read.py                                 rss    1.8 MB  peak    1.8 MB  swap    0.0 MB   <-- 2 copies running

== OOM kills since '24 hours ago': 142 ==
  python               kills 122 largest anon-rss at kill 257.2 MB
  systemd              kills 19  largest anon-rss at kill 1.8 MB
  (sd-pam)             kills 1   largest anon-rss at kill 0.2 MB

== lock skips (logs/t3_skips.jsonl): 0  {} ==

```
