# Remote branch cleanup, W117.0 (2026-11-18)

Remote branches before: 16 heads (12 listed after the four W116 PR branches auto-deleted on merge, plus main). After: 10 + main.
Rule: DELETE only if PR merged or `git cherry origin/main <b>` has no "+" line, and no open PR. `+` = unlanded commits.

## DELETED
| Branch | Tip | Last commit | PR | + | Reason |
|---|---|---|---|---|---|
| session/20261112T000254Z-w111-1-fade-arm-routing | 7a299f7 | 2026-11-11 | #482 MERGED | 6 | PR merged, no open PR (cherry "+" is squash-merge noise) |
| session/20261118-gg1942-arm-advisory (#508) | 450c50f -> e2d5bae | 2026-11-18 | MERGED | - | auto-deleted on squash-merge |
| session/20261118-w116-2-report (#505) | f66b6ad | 2026-11-18 | MERGED | - | auto-deleted on squash-merge |
| session/w116-1-evidence-opus (#506) | 29dd6b6 | 2026-11-18 | MERGED | - | auto-deleted on squash-merge |
| w116-3-nhl (#507) | 632530d | 2026-11-18 | MERGED | - | auto-deleted on squash-merge |

## KEPT
| Branch | Tip | Last commit | PR | + | Reason |
|---|---|---|---|---|---|
| data/nba-injury-reports | 813cd8c | 2026-11-17 | none | 102 | named keep (data branch) |
| data/nhl-goalie-probe | f98bdca | 2026-10-14 | none | 17 | named keep (data branch) |
| session/20260924T045227Z-resolved-filter | 649440a | 2026-09-24 | #149 OPEN | 7 | named keep (#149) |
| session/20261110T054159Z-w108-5-dashboard-stale | 18ba466 | 2026-11-09 | #458 OPEN (#455 merged) | 4 | open PR #458 |
| sw9-routed-labels | 01a28e8 | 2026-11-10 | #477 OPEN | 0 | open PR #477 |
| session/20261106T052413Z-w105-5-ride-board | 2c5910b | 2026-11-05 | #445 CLOSED | 2 | unlanded commits |
| session/20261110T051528Z-w108-2-news-lag-prints | 98eca18 | 2026-11-09 | none | 2 | unlanded commits |
| session/20261111T003914Z-w109-5-dashboard-mem | d3d32b9 | 2026-11-10 | #461 CLOSED | 4 | unlanded commits |
| session/20261117T010343Z-w115-1-evidence | 73c3fa8 | 2026-11-16 | none | 1 | unlanded commit |
| w106-1-graft | 8afa6e6 | 2026-11-09 | none | 8 | unlanded commits |

Branches kept with unlanded commits: 8 (the 2 data branches, #149, and 5 others; #458 and #477 are open-PR keeps).

## Local worktrees
Removed (clean, remote branch deleted): PM-worktrees/gg1942, PM-worktrees/20261117T010348Z-w115-2-placement (+ their local branches). `git worktree prune` run.
Not removed: ~165 older worktrees whose remote branches were never pushed or are still kept; 25 of them have uncommitted changes (dirty), e.g. 20261003T000917Z-eyes-and-nhl (13), 20260905T221739Z-nfl-readiness-audit (8), 20260930T005212Z-provenance-allowlist (7), 20260930T053614Z-reality-reconciliation (7), 20261011T061249Z-w66-2-demo-404 (7), 20261022T233152Z-w85-2-gate (7), 20261005T235001Z-w56-visual-dashboard (6). Listed, not touched.
