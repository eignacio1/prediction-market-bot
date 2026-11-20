# Box task `candidate_arms_read` — 20261120T1702Z_b_candidate_arms_read

- request: `04_EXECUTION/BOX_TASKS/requests/20261120T1702Z_b_candidate_arms_read.toml`
- note: W122.2 part C: pot_of_gold rows per sport
- ran: 2026-11-20T17:03:00Z on root@157.230.91.33:/opt/prediction-market-bot
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
    "NO_BET": 5479,
    "RIDE": 81
   },
   "errors": 0,
   "map_versions": [
    "v1+nba_depth"
   ],
   "rows": 6164,
   "same_as_v1": 6093,
   "sha12": [
    "14cb271e963a"
   ]
  },
  "NBA|nba_props": {
   "arms": {
    "NO_BET": 36,
    "RIDE": 11
   },
   "errors": 0,
   "map_versions": [
    "nba_props"
   ],
   "rows": 47,
   "same_as_v1": 36,
   "sha12": [
    "f6cff8645c3c"
   ]
  },
  "NBA|pot_of_gold": {
   "arms": {
    "NO_BET": 13
   },
   "errors": 0,
   "map_versions": [
    "pot_of_gold"
   ],
   "rows": 13,
   "same_as_v1": 13,
   "sha12": [
    "86a63cac71c5"
   ]
  },
  "NBA|router_v2": {
   "arms": {
    "MODEL_FADE": 581,
    "MOMENTUM": 78,
    "NO_BET": 5307,
    "RIDE": 198
   },
   "errors": 0,
   "map_versions": [
    "v2"
   ],
   "rows": 6164,
   "same_as_v1": 5342,
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
 "read_utc": "2026-11-20T17:02:40Z",
 "rows_in_window": {
  "NBA": 22259,
  "NFL": 1088,
  "NHL": 3391
 },
 "window_hours": 72
}

```
