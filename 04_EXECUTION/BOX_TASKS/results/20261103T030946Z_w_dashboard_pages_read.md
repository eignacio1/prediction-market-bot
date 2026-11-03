# Box task `dashboard_pages_read` — 20261103T030946Z_w_dashboard_pages_read

- request: `04_EXECUTION/BOX_TASKS/requests/20261103T030946Z_w_dashboard_pages_read.toml`
- note: Wave 97 close read (strategic window)
- ran: 2026-11-03T03:10:24Z on root@157.230.91.33:/opt/prediction-market-bot
- exit code: 0
- command (allowlisted, scripts/box_tasks.py): `for u in / /api/data /visual /project; do printf '%-10s ' "$u"; curl -s -o /dev/null -w '%{http_code} %{size_download}B %{time_total}s' --max-time 60 "http://127.0.0.1:8050$u"; echo; done; printf 'museweb sections on /visual: '; curl -s --max-time 60 http://127.0.0.1:8050/visual | grep -o 'id=.musew`

```
/          200 88255B 0.378368s
/api/data  200 8265296B 0.832416s
/visual    200 2492157B 1.148039s
/project   200 103158B 0.079715s
museweb sections on /visual: 1
backlog sections on /visual: 1
NRestarts=0
MemoryCurrent=57929728
MemoryMax=134217728
ActiveState=active

```
