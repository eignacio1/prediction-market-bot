# Box task `dashboard_pages_read` — 20261110T053730Z_b_dashboard_pages_read

- request: `04_EXECUTION/BOX_TASKS/requests/20261110T053730Z_b_dashboard_pages_read.toml`
- note: visual dashboard refresh check 2 (SW-9)
- ran: 2026-11-10T05:37:52Z on root@157.230.91.33:/opt/prediction-market-bot
- exit code: 0
- command (allowlisted, scripts/box_tasks.py): `for u in / /api/data /visual /project; do printf '%-10s ' "$u"; curl -s -o /dev/null -w '%{http_code} %{size_download}B %{time_total}s' --max-time 60 "http://127.0.0.1:8050$u"; echo; done; printf 'museweb sections on /visual: '; curl -s --max-time 60 http://127.0.0.1:8050/visual | grep -o 'id=.musew`

```
/          200 88255B 0.135815s
/api/data  200 8206682B 0.250992s
/visual    200 4466696B 0.506250s
/project   200 100603B 0.039401s
museweb sections on /visual: 1
backlog sections on /visual: 1
NRestarts=0
MemoryCurrent=97333248
MemoryMax=134217728
ActiveState=active

```
