# Box task `dashboard_pages_read` — 20261022T002052Z_w_dashboard_pages_read

- request: `04_EXECUTION/BOX_TASKS/requests/20261022T002052Z_w_dashboard_pages_read.toml`
- note: Window: /visual check after #316
- ran: 2026-10-22T00:22:24Z on root@157.230.91.33:/opt/prediction-market-bot
- exit code: 0
- command (allowlisted, scripts/box_tasks.py): `for u in / /api/data /visual /project; do printf '%-10s ' "$u"; curl -s -o /dev/null -w '%{http_code} %{size_download}B %{time_total}s' --max-time 60 "http://127.0.0.1:8050$u"; echo; done; printf 'museweb sections on /visual: '; curl -s --max-time 60 http://127.0.0.1:8050/visual | grep -o 'id=.musew`

```
/          200 88255B 0.002363s
/api/data  200 8923340B 28.544469s
/visual    200 276268B 0.440691s
/project   200 100065B 47.184413s
museweb sections on /visual: 1
NRestarts=0
MemoryCurrent=133726208
MemoryMax=134217728
ActiveState=active

```
