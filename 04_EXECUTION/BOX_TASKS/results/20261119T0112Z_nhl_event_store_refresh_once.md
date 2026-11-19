# Box task `nhl_event_store_refresh_once` — 20261119T0112Z_nhl_event_store_refresh_once

- request: `04_EXECUTION/BOX_TASKS/requests/20261119T0112Z_nhl_event_store_refresh_once.toml`
- note: W119.1: refresh pass 1 (prior 0613Z run was cancelled)
- ran: 2026-11-19T01:11:23Z on root@157.230.91.33:/opt/prediction-market-bot
- exit code: 0
- command (allowlisted, scripts/box_tasks.py): `( flock -n 9 || { echo LOCKED; exit 0; }; BOT_ENV=paper PYTHONPATH=src:. nice -n 10 venv/bin/python scripts/run_nhl_event_store_refresh.py >> logs/nhl_event_store_refresh.log 2>&1; tail -n 3 logs/nhl_event_store_refresh.log ) 9>/tmp/nhl_event_store_refresh.lock`

```
{"ts": "2026-11-18T14:16:58Z", "runner": "nhl_event_store_refresh", "seasons": [2025, 2026], "fetch": {"schedule_games": 2738, "finished": 1737, "fetched": 1737, "failures": 50}, "fetch_s": 2704.6, "compiled": {"games": {"2025": 1394, "2026": 1344}, "events": {"2025": 443569, "2026": 109939}, "shifts": {"2025": 1052125, "2026": 219635}, "box_players": {"2025": 55758, "2026": 13720}, "rosters": {"2025": 55758, "2026": 13720}}, "compile_s": 166.3}
schedule: 2738 counting games, 1737 finished, 50 to fetch
{"ts": "2026-11-19T01:11:22Z", "runner": "nhl_event_store_refresh", "seasons": [2025, 2026], "fetch": {"schedule_games": 2738, "finished": 1737, "fetched": 50, "failures": 50}, "fetch_s": 36.6, "compiled": {"games": {"2025": 1394, "2026": 1344}, "events": {"2025": 443569, "2026": 109939}, "shifts": {"2025": 1052125, "2026": 219635}, "box_players": {"2025": 55758, "2026": 13720}, "rosters": {"2025": 55758, "2026": 13720}}, "compile_s": 244.3}

```
