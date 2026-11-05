# Box task `dashboard_pages_read` — 20261105T064118Z_a_dashboard_pages_read

- request: `04_EXECUTION/BOX_TASKS/requests/20261105T064118Z_a_dashboard_pages_read.toml`
- note: is /visual serving the compact picks panel (#428)?
- ran: 2026-11-05T06:41:37Z on root@157.230.91.33:/opt/prediction-market-bot
- exit code: 0
- command (allowlisted, scripts/box_tasks.py): `for u in / /api/data /visual /project; do printf '%-10s ' "$u"; curl -s -o /dev/null -w '%{http_code} %{size_download}B %{time_total}s' --max-time 60 "http://127.0.0.1:8050$u"; echo; done; printf 'museweb sections on /visual: '; curl -s --max-time 60 http://127.0.0.1:8050/visual | grep -o 'id=.musew`

```
/          200 88255B 0.005868s
/api/data  200 8239423B 0.009364s
/visual    200 4481943B 0.225092s
/project   200 103546B 0.029634s
museweb sections on /visual: 1
backlog sections on /visual: 1
NRestarts=0
MemoryCurrent=102793216
MemoryMax=134217728
ActiveState=active

```
