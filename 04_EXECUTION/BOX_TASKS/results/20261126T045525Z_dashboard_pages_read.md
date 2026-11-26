# Box task `dashboard_pages_read` — 20261126T045525Z_dashboard_pages_read

- request: `04_EXECUTION/BOX_TASKS/requests/20261126T045525Z_dashboard_pages_read.toml`
- note: SW-9 last task: confirm the box serves the updated Visual Dashboard (8e9e0497) and the Live Terminal
- ran: 2026-11-26T04:55:48Z on root@157.230.91.33:/opt/prediction-market-bot
- exit code: 0
- command (allowlisted, scripts/box_tasks.py): `for u in / /api/data /visual /project; do printf '%-10s ' "$u"; curl -s -o /dev/null -w '%{http_code} %{size_download}B %{time_total}s' --max-time 60 "http://127.0.0.1:8050$u"; echo; done; printf 'museweb sections on /visual: '; curl -s --max-time 60 http://127.0.0.1:8050/visual | grep -o 'id=.musew`

```
/          200 106128B 0.224271s
/api/data  200 8866351B 0.520543s
/visual    200 3584476B 0.964036s
/project   200 108425B 0.059358s
museweb sections on /visual: 1
backlog sections on /visual: 1
NRestarts=0
MemoryCurrent=98070528
MemoryMax=402653184
ActiveState=active

```
