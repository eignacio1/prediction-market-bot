# Box task `demo_fill_rearm` — 20261112T063046Z_demo_fill_rearm

- request: `04_EXECUTION/BOX_TASKS/requests/20261112T063046Z_demo_fill_rearm.toml`
- note: SW-9: clear ARM_ORDERS=dry override (report trips none); arm orders authorized by operator 2026-11-11 16:51 PT. Demo only.
- ran: 2026-11-12T06:43:35Z on root@157.230.91.33:/opt/prediction-market-bot
- exit code: 0
- command (allowlisted, scripts/box_tasks.py): `PYTHONPATH=src:. venv/bin/python scripts/demo_fill_rearm.py apply`

```
override file:
ARM_ORDERS=dry

epoch-gated report trips now: none
REARMED: override moved to demo_fill.override.env.20261112T064334Z.removed

```
