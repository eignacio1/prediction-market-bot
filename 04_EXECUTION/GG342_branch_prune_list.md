# GG-342 remote branch prune list (W89.6, 2026-10-26) — AWAITING OPERATOR OK

Method: `git cherry origin/main <branch>` (patch-id equivalence). Nothing deleted. Source: fetch --prune at 2026-10-27T04:30:47Z, `git branch -r --no-merged origin/main` = 36 branches.

## A. Content-landed (every commit has a patch-id twin on main) — safe to delete on your OK

| Last commit | Branch | Commits |
|---|---|---|
| 2026-10-13 | origin/session/20261013T233400Z-w71-2-nba-opening-night | 1 |
| 2026-10-13 | origin/session/20261014T004128Z-w72-3-deploy-truth | 1 |
| 2026-10-13 | origin/w72-2-atomic-audit | 1 |
| 2026-10-13 | origin/w72-2-followups | 1 |
| 2026-10-13 | origin/w72-3-partb | 1 |
| 2026-10-14 | origin/session/20261015T050555Z-w75-3-seat-tensions | 1 |
| 2026-10-14 | origin/session/20261015T051115Z-w75-5-nfl-book-closes | 1 |
| 2026-10-14 | origin/session/20261015T051206Z-w75-4-one-kill-switch | 1 |
| 2026-10-14 | origin/session/w73-1-turnoff | 1 |
| 2026-10-15 | origin/session/20261015T234927Z-w76-3-ledger-integrity | 1 |
| 2026-10-15 | origin/session/20261016T051056Z-w77-2b-report-window | 1 |
| 2026-10-15 | origin/session/20261016T053532Z-w78-3-nba-opening-night | 1 |
| 2026-10-15 | origin/session/w78-1-gap-agent-visible | 1 |
| 2026-10-15 | origin/w78-3-partb | 1 |
| 2026-10-15 | origin/window/fix-main-isolation | 1 |
| 2026-10-13 | origin/session/20261014T004119Z-w72-1-readback-guards | 2 |

Delete command (run only after OK): `git push origin --delete <branch-without-origin/>` per row.

## B. Carry commits not on main — KEEP, triage separately

| Last commit | Branch | Unlanded / total |
|---|---|---|
| 2026-10-13 | origin/session/20261014T004112Z-w72-2-ledger-safety | 1 / 1 |
| 2026-10-21 | origin/session/20261021T235008Z-w83-3-nhl-data-layer | 1 / 1 |
| 2026-10-26 | origin/session/20261027T040153Z-w89-2-longshot-bias | 1 / 1 |
| 2026-10-14 | origin/data/nhl-goalie-probe | 17 / 17 |
| 2026-10-14 | origin/session/20261014T234421Z-w73-3-nfl-engine-scaffold | 2 / 2 |
| 2026-10-14 | origin/window/adr-0074-process-integrity | 2 / 2 |
| 2026-10-15 | origin/session/20261015T234931Z-w76-4-runtime-map-live | 2 / 2 |
| 2026-10-15 | origin/session/20261016T004638Z-w77-2-nfl-market-tests | 2 / 2 |
| 2026-10-26 | origin/session/20261027T040537Z-w89-4-nfl-sim | 2 / 2 |
| 2026-10-26 | origin/session/w89-1-enforce-flip | 2 / 2 |
| 2026-10-26 | origin/session/w89-3-part-b | 2 / 2 |
| 2026-10-27 | origin/data/nba-injury-reports | 27 / 27 |
| 2026-10-19 | origin/session/20261020T045139Z-w81-3-partb | 3 / 3 |
| 2026-10-14 | origin/session/20261014T234416Z-w73-2-nfl-data-layer | 4 / 4 |
| 2026-10-14 | origin/session/20261015T050519Z-w75-1-pam-core | 5 / 5 |
| 2026-10-13 | origin/session/20261013T233401Z-w71-3-nba-availability | 6 / 6 |
| 2026-10-14 | origin/session/20261015T050530Z-w75-2-nfl-stage2 | 6 / 6 |
| 2026-10-15 | origin/session/20261015T234908Z-w76-1-killswitch-drill | 6 / 6 |
| 2026-10-15 | origin/session/20261016T004631Z-w77-1-fillfix-503-cash | 6 / 7 |
| 2026-09-24 | origin/session/20260924T045227Z-resolved-filter | 7 / 7 |
