# Box task `data_offload_probe` — 20261125T062104Z_data_offload_probe

- request: `04_EXECUTION/BOX_TASKS/requests/20261125T062104Z_data_offload_probe.toml`
- note: 128.5 reachability + RSS/runtime per scraper (retry)
- ran: 2026-11-25T06:30:19Z on root@157.230.91.33:/opt/prediction-market-bot
- exit code: 0
- command (allowlisted, scripts/box_tasks.py): `systemd-run --scope -q -p MemoryMax=150M -p MemorySwapMax=0 /bin/true; echo systemd_run_rc=$?; PYTHONPATH=src:. venv/bin/python scripts/data_offload.py probe`

```
systemd_run_rc=0
{
 "families": [
  {
   "bytes": 22841,
   "error": "",
   "family": "nhl_goalie_logs",
   "items": 25,
   "peak_rss_mb": 26.0,
   "requests": 25,
   "seconds": 24.1,
   "stop": "request cap",
   "wall_seconds": 25.2
  },
  {
   "bytes": 5185,
   "error": "",
   "family": "nhl_officials",
   "items": 24,
   "peak_rss_mb": 26.9,
   "requests": 25,
   "seconds": 23.7,
   "stop": "request cap",
   "wall_seconds": 24.8
  },
  {
   "bytes": 5594685,
   "error": "",
   "family": "moneypuck",
   "items": 16,
   "peak_rss_mb": 26.0,
   "requests": 16,
   "seconds": 30.8,
   "stop": "byte cap",
   "wall_seconds": 31.8
  },
  {
   "bytes": 369353,
   "error": "",
   "family": "savant",
   "items": 25,
   "peak_rss_mb": 26.0,
   "requests": 25,
   "seconds": 72.4,
   "stop": "request cap",
   "wall_seconds": 73.9
  },
  {
   "bytes": 0,
   "error": "RuntimeError: giving up after 3 tries: https://statsapi.mlb.com/api/v1/schedule?sportId=1&startDate=2026-03-01&endDate=2026-03-31&gameType=R%2CF%2CD%2CL%2CW: HTTP Error 406: Not Acceptable",
   "family": "mlb_boxscore",
   "items": 0,
   "peak_rss_mb": 26.0,
   "requests": 3,
   "seconds": 14.5,
   "stop": "error",
   "wall_seconds": 15.9
  }
 ],
 "reach": [
  {
   "name": "nba_stats",
   "seconds": 0.2,
   "status": 403
  },
  {
   "name": "nba_cdn",
   "seconds": 0.0,
   "status": 403
  },
  {
   "name": "pfr",
   "seconds": 0.0,
   "status": 403
  },
  {
   "bytes_first_read": 4096,
   "challenge": false,
   "name": "umpscorecards",
   "seconds": 0.4,
   "status": 200
  },
  {
   "bytes_first_read": 4096,
   "challenge": false,
   "name": "kofsports",
   "seconds": 0.2,
   "status": 200
  }
 ],
 "ts": "2026-11-25T06:27:25Z"
}

```
