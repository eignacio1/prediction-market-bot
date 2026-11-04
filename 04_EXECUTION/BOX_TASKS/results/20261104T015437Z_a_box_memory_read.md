# Box task `box_memory_read` — 20261104T015437Z_a_box_memory_read

- request: `04_EXECUTION/BOX_TASKS/requests/20261104T015437Z_a_box_memory_read.toml`
- note: memory before the T3 lock install (window)
- ran: 2026-11-04T01:54:57Z on root@157.230.91.33:/opt/prediction-market-bot
- exit code: 0
- command (allowlisted, scripts/box_tasks.py): `PYTHONPATH=src:. venv/bin/python scripts/box_memory_read.py --since '24 hours ago'`

```
== meminfo / load ==
  MemTotal:         984676 kB
  MemAvailable:     439956 kB
  SwapTotal:       2097148 kB
  SwapFree:        1752828 kB
  loadavg: 0.88 0.73 0.91 3/148 480361

== bot python processes now (9) ==
  pid 480228  scripts/demo_cancel_sweeper.py                             rss  218.0 MB  peak  227.3 MB  swap    0.0 MB
  pid 480116  scripts/thin_market_depth_capture.py                       rss   20.4 MB  peak   60.1 MB  swap   39.9 MB   <-- 2 copies running
  pid 473580  /opt/prediction-market-bot/venv/bin/python src/prediction_ rss   19.4 MB  peak  190.3 MB  swap  100.5 MB
  pid 195670  /opt/prediction-market-bot/venv/bin/python src/prediction_ rss   19.3 MB  peak  147.6 MB  swap   70.5 MB
  pid 480361  scripts/box_memory_read.py                                 rss   13.2 MB  peak   13.2 MB  swap    0.0 MB   <-- 2 copies running
  pid 438862  scripts/web_dashboard.py                                   rss    3.3 MB  peak  116.8 MB  swap   60.1 MB
  pid 480111  scripts/thin_market_depth_capture.py                       rss    2.8 MB  peak    3.1 MB  swap    0.1 MB   <-- 2 copies running
  pid 480360  scripts/box_memory_read.py                                 rss    1.9 MB  peak    1.9 MB  swap    0.0 MB   <-- 2 copies running
  pid 473578  timeout 21600 /opt/prediction-market-bot/venv/bin/python s rss    1.6 MB  peak    1.8 MB  swap    0.0 MB

== OOM kills since '24 hours ago': 24 ==
  python               kills 21  largest anon-rss at kill 183.8 MB
  systemd              kills 2   largest anon-rss at kill 1.8 MB
  (sd-pam)             kills 1   largest anon-rss at kill 0.2 MB

== lock skips (logs/t3_skips.jsonl): 0  {} ==

```
