# Box task `nfl_live_feed_probe` — 20261126T003419Z_nfl_live_feed_probe

- request: `04_EXECUTION/BOX_TASKS/requests/20261126T003419Z_nfl_live_feed_probe.toml`
- note: W129.6 Part A: prove ESPN NFL plays feed reachable from the box (read-only)
- ran: 2026-11-26T00:44:16Z on root@157.230.91.33:/opt/prediction-market-bot
- exit code: 0
- command (allowlisted, scripts/box_tasks.py): `PYTHONPATH=src:. venv/bin/python scripts/nfl_live_feed_probe.py`

```
{
 "probe": "nfl_live_feed",
 "ua": "requests default (no override)",
 "scoreboard": {
  "status": 200,
  "rtt_s": 0.217,
  "bytes": 287359,
  "err_head": "",
  "blocked": false,
  "events": 16,
  "states": [
   "STATUS_SCHEDULED"
  ]
 },
 "event_choice": "fallback_saved_game_401873067",
 "plays": {
  "status": 200,
  "rtt_s": 0.212,
  "bytes": 790673,
  "err_head": "",
  "blocked": false,
  "event": "401873067",
  "n": 173,
  "with_wallclock": 172,
  "with_start_down": 173
 },
 "situation": {
  "status": 200,
  "rtt_s": 0.199,
  "bytes": 393,
  "err_head": "",
  "blocked": false,
  "keys": [
   "$ref",
   "awayTimeouts",
   "distance",
   "down",
   "homeTimeouts",
   "isRedZone",
   "lastPlay",
   "yardLine"
  ]
 },
 "verdict": "REACHABLE"
}

```
