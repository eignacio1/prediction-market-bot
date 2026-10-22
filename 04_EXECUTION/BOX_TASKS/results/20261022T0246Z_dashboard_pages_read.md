# Box task `dashboard_pages_read` — 20261022T0246Z_dashboard_pages_read

- request: `04_EXECUTION/BOX_TASKS/requests/20261022T0246Z_dashboard_pages_read.toml`
- note: W84.1 Part A after-read
- ran: 2026-10-22T02:46:38Z on root@157.230.91.33:/opt/prediction-market-bot
- exit code: 0
- command (allowlisted, scripts/box_tasks.py): `for u in / /api/data /visual /project; do printf '%-10s ' "$u"; curl -s -o /dev/null -w '%{http_code} %{size_download}B %{time_total}s' --max-time 60 "http://127.0.0.1:8050$u"; echo; done; printf 'museweb sections on /visual: '; curl -s --max-time 60 http://127.0.0.1:8050/visual | grep -o 'id=.musew`

```
/          200 88255B 0.007356s
/api/data  200 8319650B 0.012994s
/visual    200 287933B 0.016627s
/project   200 99906B 0.246877s
museweb sections on /visual: 1
NRestarts=0
MemoryCurrent=101527552
MemoryMax=134217728
ActiveState=active

```
