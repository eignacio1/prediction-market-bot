# Box task `demo_fill_rearm_check` — 20261111T023817Z_demo_fill_rearm_check

- request: `04_EXECUTION/BOX_TASKS/requests/20261111T023817Z_demo_fill_rearm_check.toml`
- note: 109.6 artifact verdict; read-only pre-check (SW-9)
- ran: 2026-11-11T02:38:43Z on root@157.230.91.33:/opt/prediction-market-bot
- exit code: 0
- command (allowlisted, scripts/box_tasks.py): `PYTHONPATH=src:. venv/bin/python scripts/demo_fill_rearm.py check`

```
override file:
# TURNED OFF 2026-11-05T11:25:01.721637+00:00 by demo_fill_forward_report (treatment_markout_30m_worse_than_control). Delete this file to re-enable.
DEMO_FILL_PLACEMENT_RULE=off
SHADOW_FLAT_STAKE=off

epoch-gated report trips now: none
CHECK ONLY: nothing changed

```
