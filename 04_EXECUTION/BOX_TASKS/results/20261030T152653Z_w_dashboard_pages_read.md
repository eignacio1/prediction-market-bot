# Box task `dashboard_pages_read` — 20261030T152653Z_w_dashboard_pages_read

- request: `04_EXECUTION/BOX_TASKS/requests/20261030T152653Z_w_dashboard_pages_read.toml`
- note: Wave 95 close read (strategic window)
- ran: 2026-10-30T15:27:28Z on root@157.230.91.33:/opt/prediction-market-bot
- exit code: 0
- command (allowlisted, scripts/box_tasks.py): `for u in / /api/data /visual /project; do printf '%-10s ' "$u"; curl -s -o /dev/null -w '%{http_code} %{size_download}B %{time_total}s' --max-time 60 "http://127.0.0.1:8050$u"; echo; done; printf 'museweb sections on /visual: '; curl -s --max-time 60 http://127.0.0.1:8050/visual | grep -o 'id=.musew`

```
/          200 88255B 0.290968s
/api/data  200 8304250B 0.316677s
/visual    200 316855B 0.901558s
/project   200 102259B 0.062053s
museweb sections on /visual: 1
NRestarts=0
MemoryCurrent=55066624
MemoryMax=134217728
ActiveState=active

```
