# Box task `nhl_event_store_readback` — 20261119T0125Z_nhl_event_store_readback

- request: `04_EXECUTION/BOX_TASKS/requests/20261119T0125Z_nhl_event_store_readback.toml`
- note: W119.1 Part A/B read
- ran: 2026-11-19T01:24:03Z on root@157.230.91.33:/opt/prediction-market-bot
- exit code: 0
- command (allowlisted, scripts/box_tasks.py): `PYTHONPATH=src:. venv/bin/python scripts/nhl_event_store_install.py readback`

```
CRONTAB BLOCK (1 lines):
# BEGIN W116.3 NHL EVENT STORE REFRESH LINE
29 13 * * * ( flock -n 9 || { printf '{"ts":"\%s","runner":"nhl_event_store_refresh","event":"SKIP_LOCKED","reason":"previous run still holding /tmp/nhl_event_store_refre
# END W116.3 NHL EVENT STORE REFRESH LINE
  box_players_2025.parquet  994297 bytes  mtime 2026-11-19T01:10Z
  box_players_2026.parquet  247941 bytes  mtime 2026-11-19T01:11Z
  events_2025.parquet  8444576 bytes  mtime 2026-11-19T01:10Z
  events_2026.parquet  2099944 bytes  mtime 2026-11-19T01:11Z
  fetch_failures.json  5300 bytes  mtime 2026-11-19T01:07Z
  games_2025.parquet  253636 bytes  mtime 2026-11-19T01:10Z
  games_2026.parquet  233542 bytes  mtime 2026-11-19T01:11Z
  recon.json  433603 bytes  mtime 2026-11-19T01:11Z
  rosters_2025.parquet  1007721 bytes  mtime 2026-11-19T01:10Z
  rosters_2026.parquet  254673 bytes  mtime 2026-11-19T01:11Z
  schedule_games.json  981334 bytes  mtime 2026-11-19T01:06Z
  shifts_2025.parquet  5445684 bytes  mtime 2026-11-19T01:10Z
  shifts_2026.parquet  1149251 bytes  mtime 2026-11-19T01:11Z

LOG TAIL (logs/nhl_event_store_refresh.log), error lines in last 500: 0
  1200/1737 games, interval=0.50s, failures=0
  1400/1737 games, interval=0.50s, failures=0
  1600/1737 games, interval=0.50s, failures=50
{"ts": "2026-11-18T14:16:58Z", "runner": "nhl_event_store_refresh", "seasons": [2025, 2026], "fetch": {"schedule_games": 2738, "finished": 1737, "fetched": 1737, "failures": 50}, "fetch_s": 2704.6, "compiled": {"games": {"2025": 1394, "2026": 1344}, "events": {"2025": 443569, "2026": 109939}, "shifts": {"2025": 1052125, "2026": 219635}, "box_players": {"2025": 55758, "2026": 13720}, "rosters": {"2025": 55758, "2026": 13720}}, "compile_s": 166.3}
schedule: 2738 counting games, 1737 finished, 50 to fetch
{"ts": "2026-11-19T01:11:22Z", "runner": "nhl_event_store_refresh", "seasons": [2025, 2026], "fetch": {"schedule_games": 2738, "finished": 1737, "fetched": 50, "failures": 50}, "fetch_s": 36.6, "compiled": {"games": {"2025": 1394, "2026": 1344}, "events": {"2025": 443569, "2026": 109939}, "shifts": {"2025": 1052125, "2026": 219635}, "box_players": {"2025": 55758, "2026": 13720}, "rosters": {"2025": 55758, "2026": 13720}}, "compile_s": 244.3}

```
