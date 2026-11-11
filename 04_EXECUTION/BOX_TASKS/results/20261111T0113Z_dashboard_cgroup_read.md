# Box task `dashboard_cgroup_read` — 20261111T0113Z_dashboard_cgroup_read

- request: `04_EXECUTION/BOX_TASKS/requests/20261111T0113Z_dashboard_cgroup_read.toml`
- note: W109.5 post-merge read of #462/#464
- ran: 2026-11-11T01:15:33Z on root@157.230.91.33:/opt/prediction-market-bot
- exit code: 0
- command (allowlisted, scripts/box_tasks.py): `cg=/sys/fs/cgroup/system.slice/pmbot-web-dashboard.service; echo '--- memory.events'; cat $cg/memory.events; echo '--- memory.peak'; cat $cg/memory.peak 2>&1; echo '--- memory.current / max'; cat $cg/memory.current $cg/memory.max; echo '--- memory.stat (anon, file, slab)'; grep -E '^(anon|file|slab|`

```
--- memory.events
low 0
high 0
max 5082
oom 0
oom_kill 0
oom_group_kill 0
--- memory.peak
134217728
--- memory.current / max
43839488
134217728
--- memory.stat (anon, file, slab)
anon 15949824
file 22634496
shmem 0
slab 458368
--- cpu.stat
usage_usec 25244979
user_usec 19526388
system_usec 5718590
core_sched.force_idle_usec 0
nr_periods 985
nr_throttled 28
throttled_usec 516318
nr_bursts 0
burst_usec 0
--- process RSS
 889510 22736       01:38 /usr/bin/python3 /opt/prediction-market-bot/scripts/web_dashboard.py --log-dir /opt/prediction-market-bot/logs/ --host 127.0.0.1 --port 8050

```
