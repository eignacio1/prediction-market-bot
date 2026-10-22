# Box task `dashboard_pages_read` — 20261022T013619Z_w_dashboard_pages_read

- request: `04_EXECUTION/BOX_TASKS/requests/20261022T013619Z_w_dashboard_pages_read.toml`
- note: Window: Wave 83 close
- ran: 2026-10-22T01:37:40Z on root@157.230.91.33:/opt/prediction-market-bot
- exit code: 0
- command (allowlisted, scripts/box_tasks.py): `for u in / /api/data /visual /project; do printf '%-10s ' "$u"; curl -s -o /dev/null -w '%{http_code} %{size_download}B %{time_total}s' --max-time 60 "http://127.0.0.1:8050$u"; echo; done; printf 'museweb sections on /visual: '; curl -s --max-time 60 http://127.0.0.1:8050/visual | grep -o 'id=.musew`

```
/          200 88255B 0.055313s
/api/data  200 8920641B 14.531203s
/visual    200 276171B 0.214105s
/project   200 99809B 45.250696s
museweb sections on /visual: 1
NRestarts=0
MemoryCurrent=133885952
MemoryMax=134217728
ActiveState=active

```
