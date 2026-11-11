# Box task `demo_fill_rearm` — 20261111T023921Z_demo_fill_rearm

- request: `04_EXECUTION/BOX_TASKS/requests/20261111T023921Z_demo_fill_rearm.toml`
- note: 109.6 verdict ARTIFACT (trip on pre-GG-1771 data); epoch-gated report trips none; demo-only plumbing per operator rule (SW-9)
- ran: 2026-11-11T02:39:46Z on root@157.230.91.33:/opt/prediction-market-bot
- exit code: 0
- command (allowlisted, scripts/box_tasks.py): `PYTHONPATH=src:. venv/bin/python scripts/demo_fill_rearm.py apply`

```
override file:
# TURNED OFF 2026-11-05T11:25:01.721637+00:00 by demo_fill_forward_report (treatment_markout_30m_worse_than_control). Delete this file to re-enable.
DEMO_FILL_PLACEMENT_RULE=off
SHADOW_FLAT_STAKE=off

epoch-gated report trips now: none
REARMED: override moved to demo_fill.override.env.20261111T023946Z.removed

```
