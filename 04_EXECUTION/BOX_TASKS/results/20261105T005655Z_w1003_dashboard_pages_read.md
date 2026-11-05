# Box task `dashboard_pages_read` — 20261105T005655Z_w1003_dashboard_pages_read

- request: `04_EXECUTION/BOX_TASKS/requests/20261105T005655Z_w1003_dashboard_pages_read.toml`
- note: W100.3 read-only
- ran: 2026-11-05T00:57:32Z on root@157.230.91.33:/opt/prediction-market-bot
- exit code: 0
- command (allowlisted, scripts/box_tasks.py): `for u in / /api/data /visual /project; do printf '%-10s ' "$u"; curl -s -o /dev/null -w '%{http_code} %{size_download}B %{time_total}s' --max-time 60 "http://127.0.0.1:8050$u"; echo; done; printf 'museweb sections on /visual: '; curl -s --max-time 60 http://127.0.0.1:8050/visual | grep -o 'id=.musew`

```
/          200 88255B 0.147862s
/api/data  200 8247714B 0.434438s
/visual    200 2514268B 1.524731s
/project   200 102767B 0.036943s
museweb sections on /visual: 1
backlog sections on /visual: 1
NRestarts=0
MemoryCurrent=71090176
MemoryMax=134217728
ActiveState=active

```
