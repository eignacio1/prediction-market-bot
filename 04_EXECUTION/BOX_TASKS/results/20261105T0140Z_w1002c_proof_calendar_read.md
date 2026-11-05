# Box task `proof_calendar_read` — 20261105T0140Z_w1002c_proof_calendar_read

- request: `04_EXECUTION/BOX_TASKS/requests/20261105T0140Z_w1002c_proof_calendar_read.toml`
- note: W100.2 retry c, after box pull
- ran: 2026-11-05T01:42:36Z on root@157.230.91.33:/opt/prediction-market-bot
- exit code: 255
- command (allowlisted, scripts/box_tasks.py): `PYTHONPATH=src:. venv/bin/python scripts/proof_calendar.py --emit`

```

[stderr]
Read from remote host 157.230.91.33: Connection reset by peer
client_loop: send disconnect: Broken pipe

```
