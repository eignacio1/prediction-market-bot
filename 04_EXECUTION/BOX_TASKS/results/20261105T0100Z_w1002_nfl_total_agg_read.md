# Box task `nfl_total_agg_read` — 20261105T0100Z_w1002_nfl_total_agg_read

- request: `04_EXECUTION/BOX_TASKS/requests/20261105T0100Z_w1002_nfl_total_agg_read.toml`
- note: W100.2 Part B: per-game aggregates for the NFL totals decomposition (read-only)
- ran: 2026-11-05T01:09:28Z on root@157.230.91.33:/opt/prediction-market-bot
- exit code: 2
- command (allowlisted, scripts/box_tasks.py): `PYTHONPATH=src:. venv/bin/python scripts/nfl_total_rows_read.py --agg`

```

[stderr]
usage: nfl_total_rows_read.py [-h] [--dir DIR]
nfl_total_rows_read.py: error: unrecognized arguments: --agg

```
