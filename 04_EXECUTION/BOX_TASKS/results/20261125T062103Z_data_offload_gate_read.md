# Box task `data_offload_gate_read` — 20261125T062103Z_data_offload_gate_read

- request: `04_EXECUTION/BOX_TASKS/requests/20261125T062103Z_data_offload_gate_read.toml`
- note: 128.5 gate read (retry after deploy lag)
- ran: 2026-11-25T06:27:24Z on root@157.230.91.33:/opt/prediction-market-bot
- exit code: 0
- command (allowlisted, scripts/box_tasks.py): `PYTHONPATH=src:. venv/bin/python scripts/data_offload_install.py gate`

```
{
 "approval_line": "approve data_offload_install",
 "ceiling_pct": 80.0,
 "horizon_days": 30,
 "max_new_mb_per_day_under_ceiling": 99.5,
 "numbers": {
  "disk_now_pct": 68.0,
  "existing_pct_per_day": -0.9999845681393806,
  "new_mb_per_day": 12.0,
  "new_pct_per_day": 0.048,
  "projected_pct_30d": 69.4
 },
 "per_night_caps_mb": {
  "mlb_boxscore": 2.0,
  "moneypuck": 5.0,
  "nhl_goalie_logs": 2.0,
  "nhl_officials": 2.0,
  "savant": 1.0
 },
 "reasons": [],
 "verdict": "PASS"
}

```
