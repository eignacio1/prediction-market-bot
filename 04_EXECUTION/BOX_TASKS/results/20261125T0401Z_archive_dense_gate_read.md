# Box task `archive_dense_gate_read` — 20261125T0401Z_archive_dense_gate_read

- request: `04_EXECUTION/BOX_TASKS/requests/20261125T0401Z_archive_dense_gate_read.toml`
- note: W127.4 Part C: gate verdict after the prints cut
- ran: 2026-11-25T04:05:24Z on root@157.230.91.33:/opt/prediction-market-bot
- exit code: 0
- command (allowlisted, scripts/box_tasks.py): `PYTHONPATH=src:. venv/bin/python scripts/archive_dense_install.py gate`

```
{
 "approval_line": "approve archive_dense_install",
 "capture_scale_that_passes": 1.0,
 "ceiling_pct": 80.0,
 "horizon_days": 30,
 "max_new_mb_per_day_under_ceiling": 99.5,
 "numbers": {
  "avg_req_per_min": 26.7,
  "burst_req_per_min": 475.3,
  "burst_rps": 7.92,
  "disk_now_pct": 68.0,
  "existing_pct_per_day": -3.105534248938763,
  "half_limit_req_per_min": 600.0,
  "new_mb_per_day": 30.5,
  "new_pct_per_day": 0.122,
  "projected_pct_30d": 71.7
 },
 "reasons": [],
 "verdict": "PASS"
}

```
