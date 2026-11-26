# Box task `nfl_inplay_readback` — 20261126T0252Z_nfl_inplay_readback

- request: `04_EXECUTION/BOX_TASKS/requests/20261126T0252Z_nfl_inplay_readback.toml`
- note: W130.1: confirm the installed line and health before the 11-26 18:00Z kickoff (read-only).
- ran: 2026-11-26T02:52:54Z on root@157.230.91.33:/opt/prediction-market-bot
- exit code: 0
- command (allowlisted, scripts/box_tasks.py): `PYTHONPATH=src:. venv/bin/python scripts/nfl_inplay_install.py readback`

```
CRONTAB BLOCK (1 lines):
# BEGIN W130.1 NFL INPLAY SHADOW LINE
*/2 17-23,0-6 * * * ( flock -n 9 || { printf '{"ts":"\%s","runner":"nfl_inplay_shadow","event":"SKIP_LOCKED","reason":"previous run still holding /tmp/nfl_inplay_shadow.l
# END W130.1 NFL INPLAY SHADOW LINE
  data/shadow/nfl_inplay: (none yet)

LOG TAIL (logs/nfl_inplay.log), error lines in last 500: no log
  (no log yet)

```
