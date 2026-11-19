# Box task `candidate_arms_read` — 20261119T0615Z_candidate_arms_read

- request: `04_EXECUTION/BOX_TASKS/requests/20261119T0615Z_candidate_arms_read.toml`
- note: W120.2: count after the 06:10Z shadow cycle (final)
- ran: 2026-11-19T06:15:59Z on root@157.230.91.33:/opt/prediction-market-bot
- exit code: 0
- command (allowlisted, scripts/box_tasks.py): `PYTHONPATH=src:. venv/bin/python scripts/candidate_arms_read.py`

```
{
 "candidates": {
  "NBA|nba_depth": {
   "arms": {
    "MODEL_FADE": 13,
    "NO_BET": 58
   },
   "errors": 0,
   "map_versions": [
    "v1+nba_depth"
   ],
   "rows": 71,
   "same_as_v1": 71,
   "sha12": [
    "14cb271e963a"
   ]
  },
  "NBA|router_v2": {
   "arms": {
    "MODEL_FADE": 13,
    "NO_BET": 48,
    "RIDE": 10
   },
   "errors": 0,
   "map_versions": [
    "v2"
   ],
   "rows": 71,
   "same_as_v1": 61,
   "sha12": [
    "79f46cb4ae1f"
   ]
  },
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
 "read_utc": "2026-11-19T06:15:32Z",
 "rows_in_window": {
  "NBA": 26516,
  "NFL": 1003,
  "NHL": 2908
 },
 "window_hours": 72
}

```
