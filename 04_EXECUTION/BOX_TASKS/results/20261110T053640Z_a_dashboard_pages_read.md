# Box task `dashboard_pages_read` — 20261110T053640Z_a_dashboard_pages_read

- request: `04_EXECUTION/BOX_TASKS/requests/20261110T053640Z_a_dashboard_pages_read.toml`
- note: visual dashboard refresh check (SW-9)
- ran: 2026-11-10T05:36:58Z on root@157.230.91.33:/opt/prediction-market-bot
- exit code: 0
- command (allowlisted, scripts/box_tasks.py): `for u in / /api/data /visual /project; do printf '%-10s ' "$u"; curl -s -o /dev/null -w '%{http_code} %{size_download}B %{time_total}s' --max-time 60 "http://127.0.0.1:8050$u"; echo; done; printf 'museweb sections on /visual: '; curl -s --max-time 60 http://127.0.0.1:8050/visual | grep -o 'id=.musew`

```
/          200 88255B 0.006363s
/api/data  200 8206694B 0.297245s
/visual    200 4466696B 0.094119s
/project   200 100603B 0.165681s
museweb sections on /visual: 1
backlog sections on /visual: 1
NRestarts=0
MemoryCurrent=132685824
MemoryMax=134217728
ActiveState=active

```
