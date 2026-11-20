# Box task `candidate_arms_read` — 20261120T1621Z_b_candidate_arms_read

- request: `04_EXECUTION/BOX_TASKS/requests/20261120T1621Z_b_candidate_arms_read.toml`
- note: W122.2 part C: rows carrying candidate arms per sport after deploy
- ran: 2026-11-20T16:21:54Z on root@157.230.91.33:/opt/prediction-market-bot
- exit code: 0
- command (allowlisted, scripts/box_tasks.py): `PYTHONPATH=src:. venv/bin/python scripts/candidate_arms_read.py`

```
{
 "candidates": {
  "NBA|nba_depth": {
   "arms": {
    "FADE": 150,
    "MODEL_FADE": 382,
    "MOMENTUM": 72,
    "NO_BET": 5432,
    "RIDE": 81
   },
   "errors": 0,
   "map_versions": [
    "v1+nba_depth"
   ],
   "rows": 6117,
   "same_as_v1": 6046,
   "sha12": [
    "14cb271e963a"
   ]
  },
  "NBA|router_v2": {
   "arms": {
    "MODEL_FADE": 581,
    "MOMENTUM": 78,
    "NO_BET": 5260,
    "RIDE": 198
   },
   "errors": 0,
   "map_versions": [
    "v2"
   ],
   "rows": 6117,
   "same_as_v1": 5295,
   "sha12": [
    "79f46cb4ae1f"
   ]
  },
  "NFL|router_v2": {
   "arms": {
    "NO_BET": 231,
    "RIDE": 566
   },
   "errors": 0,
   "map_versions": [
    "v2"
   ],
   "rows": 797,
   "same_as_v1": 480,
   "sha12": [
    "79f46cb4ae1f"
   ]
  },
  "NHL|nhl_v2": {
   "arms": {
    "MOMENTUM": 10,
    "NO_BET": 1160,
    "RIDE": 108
   },
   "errors": 0,
   "map_versions": [
    "nhl_v2"
   ],
   "rows": 1278,
   "same_as_v1": 795,
   "sha12": [
    "646eb3fcf347"
   ]
  },
  "NHL|router_v2": {
   "arms": {
    "MOMENTUM": 10,
    "NO_BET": 1160,
    "RIDE": 108
   },
   "errors": 0,
   "map_versions": [
    "v2"
   ],
   "rows": 1278,
   "same_as_v1": 795,
   "sha12": [
    "79f46cb4ae1f"
   ]
  }
 },
 "read_utc": "2026-11-20T16:21:29Z",
 "rows_in_window": {
  "NBA": 22212,
  "NFL": 1088,
  "NHL": 3496
 },
 "window_hours": 72
}

```
