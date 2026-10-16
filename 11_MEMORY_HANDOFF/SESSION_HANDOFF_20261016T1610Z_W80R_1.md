# SESSION_HANDOFF — W80R.1 The box bridge (STANDARD)

<!-- session-meta
task_id: W80R.1
tier: STANDARD
timestamp: 2026-10-16
commit: 2fc1b58
one_line_summary: W80R.1: box bridge live (#283 + #284 fix); first honest box reads; budget probe's running-SHA defect found and fixed (GG-920, #285); capture installed on a false GREEN then uninstalled; budget now RED for a real reason (t4-mlb 11.2h behind on 2 imported files)
gg_touched: GG-920 (registered, IN PROGRESS)
adr_touched: none
plan_deliverable_moved: yes
vision_pillar: PLUMBING
gap_measure: cloud sessions can read the box; SURFACE BUDGET read; thin-market capture installed
gap_delta: box readable from cloud no -> yes (3 bridge runs, results in 04_EXECUTION/BOX_TASKS/results/); budget unread -> read (RED, real); capture no -> installed 15:56Z -> uninstalled 16:10Z (GREEN was false)
pattern_sweep: "which SHA is a service running": runtime_registry.probe_local (rev-list --before, wrong) vs deploy_truth.sha_at (deploy log, right) -> probe now calls sha_at; no other running-SHA estimator in src/scripts/deploy/.claude (vps_deploy.sh reads ActiveEnterTimestamp only to verify a restart). ssh-in-read-loop: box_tasks.yml only (deploy.yml uses a heredoc).
surface_delta: +1 (workflow|box_tasks.yml, live, registered); capture 0 net (installed then removed; registry entry stays paused)
-->

**Status: DONE (bridge) · capture PENDING the real red.**

PRs (all CI green, squash-merged): #283 bridge `8bb61cd` · #284 ssh stdin fix `d56a044` · #285 GG-920 deploy-log SHA + `capture_uninstall` `2fc1b58`. t4-mlb restart decision for each: not_needed (no t4 import changed).

Reachability at start: ssh absent; Kalshi public API **200** (now allowed); GitHub REST via MCP OK.

Box reads (results/*.md, bot-committed):
- 15:48 budget_read: GREEN — **false** (old probe).
- 15:56 capture_install: INSTALLED (on that false GREEN). deploy_truth: ALARM t4-mlb runs dc84fa6c; demo_fill_policy.py + paper_trader.py changed; 11.0h.
- 16:10 capture_uninstall: UNINSTALLED. budget_read: **RED — BEHIND t4-mlb, 11.22h**, healthcheck HEALTHY.
- nba_opening_preflight: regular-season ledgers absent (expected pre-10-20); EXP-038/039 crons armed; preseason rows logging (excluded from judged n by design); team totals 0 rows (GG-891). No blocker visible.

**Next (window):**
1. Restart t4-mlb in an idle window (standing authorization 2026-10-08), then run `budget_read` via the bridge. Also find out why the GG-432 restart did not fire for those two files.
2. Before re-installing, move the capture off `:21`. EXP-039's `21 4,10,16,22` block uses the same minute (GG-477 stagger).
3. Then `capture_install` + `capture_readback`.

Operator decisions: none.
