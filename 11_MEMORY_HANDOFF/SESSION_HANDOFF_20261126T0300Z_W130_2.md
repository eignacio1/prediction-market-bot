# Handoff W130.2 - NBA props kept leaves place flat DEMO orders (EXP-NBAPROPS-002)
COMMON_RULES_W130.md first line quoted: "# Wave 130 common rules". Branch session/20261126T020332Z-w130-2-props-orders, PR #601.

## What shipped (nothing is running; default OFF)
- PREREG committed BEFORE any order: 12_EXPLORATORY/nba_props_orders/PREREG.md (594a5cd). Flat $1.00 demo stake, kelly 0, RIDE backs the
  favourite / FADE the other side, band + time to tip recomputed at order time, ADR-0072 placement (60 s cancel), one order per
  (leaf, market, UTC day). Caps with their own derivations: $51 per event (ceil(1120 rows / 22 games) x $1), $408 per day (x 8 games).
  Judged n* = 734 games, pooled only, no per-leaf verdict. Descriptive look 2027-01-31; verdict look at n* or 2027-04-15. Modal outcome:
  low fill rate, E2 interval spans zero, fills win less than non-fills (adverse selection).
- decision_trees/props_arm_orders.py (new; arm_orders.py untouched). Switch PROPS_ARM_ORDERS off/dry/on. Gates: switch, demo host,
  kill switch, eligibility (14 kept triples), side, band/tip, idempotency, listing, caps, cash, placement. Every skip has its own reason.
- scripts/run_props_arm_orders.py (runner, sweeps overdue cancels), scripts/props_arm_orders_read.py (skip counts, per-leaf and pooled
  E1/E2/E3 via placement/join, pre-epoch YES-only vs post-epoch all sides separate, voids counted).
- tests/test_w130_2_props_arm_orders.py: 21 known-answer tests, fake venue: fill, partial, reject, void (player sits), each skip, caps.
- Part C: deploy/cron.props_arm_orders (:47), paused RUNTIME_REGISTRY entry (check: 114/114, 0 unreviewed), scripts/props_arm_orders_install.py
  (budget gate, backup, one BEGIN/END block), box tasks props_arm_orders_{install,readback,uninstall,dry}. Approval line = queue item 10.

## Operator approval needed (exact task name)
`props_arm_orders_install` - "I approve the box-task request that runs props_arm_orders_install, which adds a crontab line on the paper box."

## NOT done / honest gaps
- Dry run on today's slate NOT done: the Mac has no demo creds and no PREGAME_SHADOW_EXP047 ledgers (runner printed `fills skipped: OSError`,
  0 rows). Next step SW-10: after merge run box task `props_arm_orders_dry` (orders stay off) and read the counted skip reasons.
- POINTS rows: RESULT.md said points was dark before W122.1; confirm points ledgers have rows on the box before counting on the 8 POINTS leaves.
- MERGED: PR #601 (e4c0b12), CI green on head 70df7fd. Box deploy read 2026-11-26T02:58Z (another window's request, box HEAD e3a53a35 includes #601): deploy docs_only, box HEAD = origin/main, t4-mlb and dashboard on box HEAD. t4-mlb decision: NOT NEEDED (the change adds a paused cron line and a runner; no code t4-mlb loads). My own deploy_truth_read and props_arm_orders_dry requests (fdd06d0) had not run by 02:58Z; the dry-run skip counts are NOT yet read.
- t4-mlb box deploy read + decision not done (needs post-merge box read). Session claim refused by claim_session.sh from this branch
  (GG-419, 4 commits not on main); claim from a clean origin/main worktree.
- Future-data dependence: every metric needs NBA games after install. Nothing here can be scored today.
- CLAUDE.md "Right now" window-maintained lines are RED (stale). Not mine to fix.

directive_conflicts: none. Read OPERATOR_DIRECTIVES.md (D-05 no "no edge" respected; D-20 plumbing: the window runs the install readbacks, he only approves).
surface_delta: +1 paused cron (props_arm_orders), +4 box tasks, +1 runtime registry entry; 0 live until approved. SURFACE BUDGET gate in install.
pattern_sweep: grep for the arm_orders pattern in src/ scripts/ tests/ deploy/: the new module reuses ao.side_for / submit_context; test_box_tasks writers set updated.
vision_pillar: EXECUTION (E1/E2/E3 props) + DEPTH D6 layers 6-7. gap_measure: E1 props fills 0. gap_delta: 0 now (built, not live); moves on approval.
