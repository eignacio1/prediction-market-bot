# Box task `candidate_arms_read` — 20261119T0608Z_candidate_arms_read

- request: `04_EXECUTION/BOX_TASKS/requests/20261119T0608Z_candidate_arms_read.toml`
- note: W120.2: count after the 06:10Z shadow cycle
- ran: 2026-11-19T06:09:37Z on root@157.230.91.33:/opt/prediction-market-bot
- exit code: 0
- command (allowlisted, scripts/box_tasks.py): `PYTHONPATH=src:. venv/bin/python scripts/candidate_arms_read.py`

```
{
 "candidates": {
  "NFL|router_v2": {
   "arms": {
    "NO_BET": 21,
    "RIDE": 52
   },
   "errors": 0,
   "map_versions": [
    "v2"
   ],
   "rows": 73,
   "same_as_v1": 21,
   "sha12": [
    "79f46cb4ae1f"
   ]
  }
 },
 "read_utc": "2026-11-19T06:09:13Z",
 "rows_in_window": {
  "NBA": 27269,
  "NFL": 1003,
  "NHL": 2908
 },
 "window_hours": 72
}

```
