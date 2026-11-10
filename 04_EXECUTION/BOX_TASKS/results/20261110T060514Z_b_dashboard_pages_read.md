# Box task `dashboard_pages_read` — 20261110T060514Z_b_dashboard_pages_read

- request: `04_EXECUTION/BOX_TASKS/requests/20261110T060514Z_b_dashboard_pages_read.toml`
- note: PR 457 deploy check (SW-9)
- ran: 2026-11-10T06:07:14Z on root@157.230.91.33:/opt/prediction-market-bot
- exit code: 0
- command (allowlisted, scripts/box_tasks.py): `for u in / /api/data /visual /project; do printf '%-10s ' "$u"; curl -s -o /dev/null -w '%{http_code} %{size_download}B %{time_total}s' --max-time 60 "http://127.0.0.1:8050$u"; echo; done; printf 'museweb sections on /visual: '; curl -s --max-time 60 http://127.0.0.1:8050/visual | grep -o 'id=.musew`

```
/          200 88255B 0.083686s
/api/data  200 8206694B 0.258617s
/visual    200 3351859B 39.858290s
/project   200 101397B 56.536589s
museweb sections on /visual: 1
backlog sections on /visual: 1
NRestarts=0
MemoryCurrent=111575040
MemoryMax=134217728
ActiveState=active

```
