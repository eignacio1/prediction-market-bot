# Session Handoff — 2026-11-18T01:35Z — W116.1 (B-094, QUANT, Opus)

<!-- session-meta
task_id: B-094
tier: STANDARD
timestamp: 2026-11-18T01:35:00Z
commit: 29dd6b6
one_line_summary: W116.1 router v2 built, measured, frozen; PR #506 (29dd6b6) red only on GG-1955 backlog duplicate, not merged
gg_touched: GG-1936, GG-1937, GG-1938, GG-1954
adr_touched: none
plan_deliverable_moved: no
vision_pillar: PROOF, DEPTH
gap_measure: P3 (router v2 next look pre-registered), D6 (layer: per-leaf held-out net per arm)
gap_delta: none on a pillar number; v2 sequential test validity restored, binary-null false claims 275/300 -> 2/300 (tests/test_evidence_w115.py, RESULT.md)
pattern_sweep: plug-in variance in a sequential test (e-process); grep src/ scripts/ tests/ 12_EXPLORATORY/ -> only evidence/ uses it; no other instance
surface_delta: 0
-->

**Status:** BUILT, NOT MERGED. Branch `session/w116-1-evidence-opus` @ 29dd6b6 (rebased on main 01:15Z), PR #506.
**Blocker:** CI run 44214100282 fails 3 tests, all `duplicate order 16 (B-018)` in main's `ROLLING_BACKLOG.json` (GG-1955).
The strategic window's ab392a8 "order fixed" did not clear it. This block may not edit that file. Diff vs main = my 16 paths only.

## Strategic decisions this session
| Decision | Why |
|---|---|
| Router v2 is not turned on; v1 stays the frozen test. Logging v2 is an operator decision (queue). | v2 arms 0 leaves held out |
| Not merged on red. | Rule: merge only on green |
| t4-mlb restart: NOT needed after merge. | Default `PM_LEAF_MAP_VERSION=v1` keeps v1 behaviour; MLB idle |

## Result (RESULT.md)
v2 0 held-out bets; v1 −0.0064/row [−0.0138, +0.0009]; ride favourites −0.0256 [−0.0394, −0.0129]; v2−v1 +0.0064 = value of
abstaining. Power at true +0.05: v2 84 leaves (first 2027-01-20), v1 46 (2027-02-17). Local precheck 916 passed.

directive_conflicts: D-34 (Sonnet cap) vs operator's Wave 116 Opus instruction (followed the operator); D-08 pot of gold not
scored (no longshots in W110.5 rows). D-02/D-03 wording respected.
Bet count vs G6: not re-checked this close-out (see live scan).

## One thing pending
Once `python3 scripts/rolling_backlog.py --check` passes on main: rebase, push, read CI green, `gh pr merge 506 --squash`,
file `04_EXECUTION/BOX_TASKS/requests/<UTC>_deploy_truth_read.toml`, mark GG-1954 RESOLVED, queue row ✅.

Resume: `cd PM-worktrees/20261117T010343Z-w115-1-evidence && git fetch && git rebase origin/main`.
