# Box task `dashboard_pages_read` — 20261022T222233Z_w_dashboard_pages_read

- request: `04_EXECUTION/BOX_TASKS/requests/20261022T222233Z_w_dashboard_pages_read.toml`
- note: Window: Wave 84 close
- ran: 2026-10-22T22:22:58Z on root@157.230.91.33:/opt/prediction-market-bot
- exit code: 0
- command (allowlisted, scripts/box_tasks.py): `for u in / /api/data /visual /project; do printf '%-10s ' "$u"; curl -s -o /dev/null -w '%{http_code} %{size_download}B %{time_total}s' --max-time 60 "http://127.0.0.1:8050$u"; echo; done; printf 'museweb sections on /visual: '; curl -s --max-time 60 http://127.0.0.1:8050/visual | grep -o 'id=.musew`

```
/          200 88255B 0.227238s
/api/data  200 8318739B 0.221602s
/visual    200 288680B 0.716498s
/project   200 100087B 0.064095s
museweb sections on /visual: 1
NRestarts=0
MemoryCurrent=55177216
MemoryMax=134217728
ActiveState=active

```
