# Box task `archive_dense_gate_read` — 20261125T0219Z_archive_dense_gate_read

- request: `04_EXECUTION/BOX_TASKS/requests/20261125T0219Z_archive_dense_gate_read.toml`
- note: W126.1 rerun: 00:40Z run hit pre-deploy code (usage text, exit 2)
- ran: 2026-11-25T02:21:34Z on root@157.230.91.33:/opt/prediction-market-bot
- exit code: 0
- command (allowlisted, scripts/box_tasks.py): `PYTHONPATH=src:. venv/bin/python scripts/archive_dense_install.py gate`

```
{
 "approval_line": "do not approve archive_dense_install as built; shrink capture to <= 100 MB/day or supersede the 80% ceiling",
 "capture_scale_that_passes": 0.63,
 "ceiling_pct": 80.0,
 "horizon_days": 30,
 "max_new_mb_per_day_under_ceiling": 99.5,
 "numbers": {
  "avg_req_per_min": 25.7,
  "burst_req_per_min": 487.3,
  "burst_rps": 8.12,
  "disk_now_pct": 68.0,
  "existing_pct_per_day": -3.105534248938763,
  "half_limit_req_per_min": 600.0,
  "new_mb_per_day": 159.2,
  "new_pct_per_day": 0.64,
  "projected_pct_30d": 87.2
 },
 "reasons": [
  "projected disk after 30 days is 87.2% (limit 80%): now 68% + (0.00 existing + 0.64 new) pct/day"
 ],
 "verdict": "REFUSE"
}

```
