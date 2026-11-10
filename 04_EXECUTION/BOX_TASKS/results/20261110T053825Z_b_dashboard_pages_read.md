# Box task `dashboard_pages_read` — 20261110T053825Z_b_dashboard_pages_read

- request: `04_EXECUTION/BOX_TASKS/requests/20261110T053825Z_b_dashboard_pages_read.toml`
- note: visual dashboard refresh check 3 (SW-9)
- ran: 2026-11-10T05:38:44Z on root@157.230.91.33:/opt/prediction-market-bot
- exit code: 0
- command (allowlisted, scripts/box_tasks.py): `for u in / /api/data /visual /project; do printf '%-10s ' "$u"; curl -s -o /dev/null -w '%{http_code} %{size_download}B %{time_total}s' --max-time 60 "http://127.0.0.1:8050$u"; echo; done; printf 'museweb sections on /visual: '; curl -s --max-time 60 http://127.0.0.1:8050/visual | grep -o 'id=.musew`

```
/          200 88255B 0.045508s
/api/data  200 8206682B 0.254425s
/visual    200 4466696B 0.406946s
/project   200 100604B 0.013961s
museweb sections on /visual: 1
backlog sections on /visual: 1
NRestarts=0
MemoryCurrent=134037504
MemoryMax=134217728
ActiveState=active

```
