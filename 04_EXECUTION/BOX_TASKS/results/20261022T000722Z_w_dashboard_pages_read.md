# Box task `dashboard_pages_read` — 20261022T000722Z_w_dashboard_pages_read

- request: `04_EXECUTION/BOX_TASKS/requests/20261022T000722Z_w_dashboard_pages_read.toml`
- note: Window: /visual live after #312
- ran: 2026-10-22T00:08:53Z on root@157.230.91.33:/opt/prediction-market-bot
- exit code: 0
- command (allowlisted, scripts/box_tasks.py): `for u in / /api/data /visual /project; do printf '%-10s ' "$u"; curl -s -o /dev/null -w '%{http_code} %{size_download}B %{time_total}s' --max-time 60 "http://127.0.0.1:8050$u"; echo; done; printf 'museweb sections on /visual: '; curl -s --max-time 60 http://127.0.0.1:8050/visual | grep -c 'id="musew`

```
/          200 88255B 0.002540s
/api/data  200 8920760B 16.379224s
/visual    200 275470B 0.297219s
/project   000 0B 47.178539s
museweb sections on /visual: 0
NRestarts=0
MemoryCurrent=1875968
MemoryMax=134217728
ActiveState=active

```
