# Box task `dashboard_visual_markers_read` — 20261105T065337Z_a_dashboard_visual_markers_read

- request: `04_EXECUTION/BOX_TASKS/requests/20261105T065337Z_a_dashboard_visual_markers_read.toml`
- note: is /visual serving the compact picks panel
- ran: 2026-11-05T06:47:56Z on root@157.230.91.33:/opt/prediction-market-bot
- exit code: 0
- command (allowlisted, scripts/box_tasks.py): `printf 'compact picks panel markers on /visual (0 = old panel still served): '; curl -s --max-time 60 http://127.0.0.1:8050/visual | grep -o 'pk-tabs' | wc -l`

```
compact picks panel markers on /visual (0 = old panel still served): 6

```
