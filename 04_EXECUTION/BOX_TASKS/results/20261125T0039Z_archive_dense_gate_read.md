# Box task `archive_dense_gate_read` — 20261125T0039Z_archive_dense_gate_read

- request: `04_EXECUTION/BOX_TASKS/requests/20261125T0039Z_archive_dense_gate_read.toml`
- note: W126.1 after-merge read (#565)
- ran: 2026-11-25T00:40:05Z on root@157.230.91.33:/opt/prediction-market-bot
- exit code: 2
- command (allowlisted, scripts/box_tasks.py): `PYTHONPATH=src:. venv/bin/python scripts/archive_dense_install.py gate`

```
W124.4: install the three dense-capture cron lines that deploy/cron.archive_dense mirrors (props from first listing,
5-min game snapshots near start, public trade prints; public read-only endpoints; no order, stake or kelly).

Runs ON the box (via scripts/box_tasks.py), and only when the operator approves the task `archive_dense_install` by name.
Same mechanics as scripts/disk_retention_install.py (SURFACE BUDGET probe, crontab backup-or-abort, one BEGIN/END block, no
other line touched). The registry entries are `paused` until then: the operator's named approval IS the activation, so
this installer accepts those entries' keys whether paused or live (and no other paused key).

BUDGET GATE (Part C) -- the install REFUSES unless BOTH hold:
  1. projected disk after 30 days < 80%: now + (existing growth + new capture bytes/day) * 30.
     Existing growth is the box's own measured growth (disk_guard); new capture is the dry-run size x runs/day, at the
     peak-hour per-run size for every run of the day (an upper bound, not an average).
  2. request rate < half the documented public limit. Kalshi's Basic read tier is 200 tokens/s at 10 tokens a default
     request = 20 req/s (derived from docs.kalshi.com, not a Kalshi-stated req/s; GET /account/limits is the authority).
     Half = 10 req/s = 600 req/min. Checked on the worst case: all three modes bursting at once.

  install    budget probe -> budget gate -> backup -> append the missing lines inside `# BEGIN/END W124.4 DENSE CAPTURE`.
  uninstall  removes exactly that block (backup first).
  readback   the installed lines, the gate numbers, the log tail and the dense store sizes.

Exit code is 0 in every outcome except a crontab write that did not verify.


```
