# SESSION_HANDOFF — W79.1 Red to Green (STANDARD)

<!-- session-meta
task_id: W79.1
tier: STANDARD
timestamp: 2026-10-16T14:08:00Z
commit: 7485bb9
one_line_summary: W79.1: NFL QB silent-arm false alarm fixed (T1-only rule, PR #279), exact-cell ledger globs in every sport, dashboard rebuilt; SURFACE BUDGET still RED on t4-mlb behind HEAD
gg_touched: GG-892 (pattern sweep)
adr_touched: none
plan_deliverable_moved: yes
vision_pillar: BREADTH+PLUMBING
gap_measure: SURFACE BUDGET red items (silent arm NFL QB); silent-arm loaders safe from cross-arm masking, sports 1 -> 4
gap_delta: NFL QB silent arm RED -> OK/IDLE (rule fixed, 6 tests); budget red items 1 -> 1 (swap: QB arm cleared, t4-mlb BEHIND 8.3h now the only red)
pattern_sweep: GG-892 prefix-glob masking swept across MLB/NFL/NBA-preseason/NBA-shadow/NHL/QB loaders -> exact cell names via cell_files(); test_w79_1_game_cells_mirror_the_runner_cells pins them to the runners' CELLS; NBA points and EXP-040 globs were already specific
surface_delta: 0
-->

Status: PARTLY DONE — Part A done, Part B done except budget GREEN.

**Part A.** The NFL QB challenger is a T1-only arm (12-48h pre-start). The recency rule wanted a row within 12h of any kickoff, so a correct T1 row written 12h+ before the game read as SILENT after kickoff. False positive, not a dead arm. Fix: ArmSpec.t1_window_h; a game counts as served iff a row ts is inside its T1 window. PR #279 merged (CI pass), squashed as 7485bb9, on box (HEAD f9da112e, grep t1_window_h = 4). Read-back on box: QB arm [IDLE] (no NFL games in last 12h). Cleared by rule change + 6 regression tests, not by a fresh QB row; the next NFL kickoff is the live proof.
**Glob sweep.** All sports' loaders now use exact cell names; another arm's files cannot mask a dead one.

**Part B.**
- gg_burndown / /project Gap agent line: "OPEN now 185 · at first tick 186 (-1) · closed A/B/C 1/0/0 · triaged 56 · 3 ticks · last tick 2026-10-16T02:00Z · not ticking (queue: relaunch), last tick 11.9h ago". Gap agent not ticking; belongs to the gap agent owner, not this block.
- Visual Dashboard rebuilt: PMBot Visual Dashboard.html (148,759 bytes, built at f9da112), committed docs-only.
- 390px render (Playwright/Chromium, box dashboard via ssh tunnel): /project scrollWidth 390, Live Terminal (/) scrollWidth 390; no horizontal scroll, no overflowing elements.
- SURFACE BUDGET (scripts/runtime_registry.py live, 2026-10-16T14:07Z): RED. One item: systemd|t4-mlb.service running 03ad6df9, 8.33h behind box HEAD. Healthcheck HEALTHY, 0 unreviewed, 0 unmirrored.

**t4-mlb restart decision: NOT restarted.** deploy_restart_policy restarts only on a changed t4-mlb import; the only src change since 03ad6df9 is silent_arms.py (alarm-only, not imported by t4). The budget rule counts behind-HEAD hours regardless of imports, so it goes RED on any unrelated merge. Restarting out of policy is a live-component action outside this block. Owner: the window — either restart t4-mlb (service idle, no games) or make the budget rule import-aware. Suggest registering a GG for the rule mismatch.

Strategic Decisions: None - silent-arm semantics change only (T1-only arms judged by their window). DECISION_LOG row not appended.
One thing pending: window decides t4-mlb restart vs import-aware budget rule; gap agent needs relaunch.
Resume: ssh prediction-market-vps 'cd /opt/prediction-market-bot && venv/bin/python scripts/runtime_registry.py live'
