# Branch cleanup list (B-043, W101.3) - nothing deleted

Source of truth: `git ls-remote --heads origin` at 2026-11-05T02:25Z: 35 stray branches + main at the start of the block. Two more appeared during it - the live W101.1 and W101.2 session branches (and this block's own); they are in flight, so they are not on any list. Verified with `gh pr list --head <b> --state all`, `git rev-list origin/main..origin/<b>`, `git cherry`, and a file-by-file content compare against main.
Notes: **w897 is not a branch on origin** (the backlog line is stale). The backlog said 27 merged + 5 unmerged; the count today is 29 merged-PR branches (the extra ones since the backlog line was written include w96-2-frozen-repro #383), 2 no-PR branches, 2 data branches, #149, and #314.

## DELETE - merged PR (29): the PR head equals the branch tip, or main already holds every commit
Each tip SHA is recorded so a deletion can be undone with `git push origin <sha>:refs/heads/<name>`.

| branch | PR | tip |
|---|---|---|
| session/20261013T233400Z-w71-2-nba-opening-night | #242 merged | 8efad02b36 |
| session/20261013T233401Z-w71-3-nba-availability | #244 merged | 6c90431978 |
| session/20261014T004112Z-w72-2-ledger-safety | #248 merged | d2a4ce4e6f |
| session/20261014T004119Z-w72-1-readback-guards | #252,#246 merged | 6847fa32fa |
| session/20261014T004128Z-w72-3-deploy-truth | #247 merged | 3c48c45f3a |
| session/20261014T234416Z-w73-2-nfl-data-layer | #258,#254 merged | 145bca0ec1 |
| session/20261014T234421Z-w73-3-nfl-engine-scaffold | #255 merged | 78cbfa02bc |
| session/20261015T050519Z-w75-1-pam-core | #259 merged | 1910943c52 |
| session/20261015T050530Z-w75-2-nfl-stage2 | #263 merged | dae220079c |
| session/20261015T050555Z-w75-3-seat-tensions | #261,#260 merged | c86be6cdd6 |
| session/20261015T051115Z-w75-5-nfl-book-closes | #262 merged | 14a4dda61b |
| session/20261015T051206Z-w75-4-one-kill-switch | #264 merged | 3c8345a0fe |
| session/20261015T234908Z-w76-1-killswitch-drill | #267 merged | 1399e59515 |
| session/20261015T234927Z-w76-3-ledger-integrity | #265 merged | d45bad4444 |
| session/20261015T234931Z-w76-4-runtime-map-live | #266 merged | 45e8339b84 |
| session/20261016T004631Z-w77-1-fillfix-503-cash | #269 merged | 5bb031d57e |
| session/20261016T004638Z-w77-2-nfl-market-tests | #272 merged | 1c52e5ae25 |
| session/20261016T004648Z-w77-3-ledger-read-side | #270 merged | e4e6a956bf |
| session/20261016T051056Z-w77-2b-report-window | #273 merged | 5fe5d1a683 |
| session/20261016T053532Z-w78-3-nba-opening-night | #274 merged | 4f0dd9ca61 |
| session/20261030T153149Z-w96-2-frozen-repro | #383 merged | 324eeac768 |
| session/w73-1-turnoff | #253 merged | a2ca1b2365 |
| session/w78-1-gap-agent-visible | #276 merged | 15ec6bb38e |
| w72-2-atomic-audit | #251 merged | 960c6e21f6 |
| w72-2-followups | #250 merged | df3769845c |
| w72-3-partb | #249 merged | 20e9e951f6 |
| w78-3-partb | #275 merged | 3677ead108 |
| window/adr-0074-process-integrity | #257 merged | 56337a50fa |
| window/fix-main-isolation | #268 merged | 3900743fd5 |

Reasons worth a line: **w96-2-frozen-repro** has 3 commits not squash-identical to main, but its files (regen_nfl_board.py, repro.py, the test) are byte-identical on main and box_tasks.py on main is a superset. **w77-3-ledger-read-side** and **w78-1/w73-1** are plain ancestors of main.

## DELETE - no PR, nothing unlanded (2)

| branch | state | reason | tip |
|---|---|---|---|
| session/20261015T003528Z-b74a-s1-hygiene-audit | no PR | 0 commits ahead of main: already an ancestor of main. | 7950e43865 |
| session/20261020T045139Z-w81-3-partb | no PR | The work shipped: PASSYDS model, seat rows and registry cell landed via #306 (W82.1); the frozen model json/sha256, sanity report and snapshot script are byte-identical on main. What differs is older drafts of the fit script/results.md plus a session-end handoff file (`SESSION_HANDOFF_20261020T0630Z_W81_3.md`) that exists only on this branch; main has the "Session close: W81.3" commit. Recoverable by SHA 7e0c8a371a. | 7e0c8a371a |

## KEEP

| branch | why |
|---|---|
| data/nba-injury-reports | Live data branch: a GitHub Actions bot commits to it (last 2026-11-05); no common history with main by design; `scripts/nba_lineup_window_capture.py` reads it. |
| data/nhl-goalie-probe | Data-only branch (last probe 2026-10-14), no shared history with main; referenced in the repo's gap log and backlog. The probe has stopped writing since 10-14 - ask whether it should be re-run before deleting, but it holds the only copy of those probes. |
| session/20260924T045227Z-resolved-filter (#149, OPEN since 09-24) | **Holds unlanded work.** (1) `scripts/assert_service_activation.py` + its test: the GG-279 primitive; **GG-279 is still OPEN**, and no such script exists on main. (2) A CLAUDE.md correction: main's Step 3 text still says the gap-log split makes stale resolved rows "structurally impossible"; the branch's T-574 correction (not on main) says that is false. (3) T-574 results doc and handoff. (4) Operator-console detectors: branch differs from main's version (main is far ahead; do not merge #149 as is - it would revert files). Recommendation: land items 1-3 from a fresh branch off main, then close #149 and delete. That is a small PR, not a deletion decision. |

## OPERATOR CALL (one branch)

| branch | fact | lean |
|---|---|---|
| session/20261021T235008Z-w83-3-nhl-data-layer (#314 CLOSED) | #314 was closed "Superseded by #315 (rebased branch)"; #315 is on main (adaf813). Three files are byte-identical. The branch's versions of nhl_event_store.py and nhl_store_checks.py contain lines main lacks: a duplicate-shifts failure check, `COVERAGE_FLOOR`/`SOG_RECONCILE_FLOOR` constants, and an atomic tmp-file write. They may be deliberate drops in the rebase or lost in it; I could not tell from the history. | DELETE once a 5-minute check shows the dup-shift check is wanted or not (a one-line GG if wanted). Tip 8219b53bec keeps it recoverable. |

## Result if the operator approves as written
35 stray branches -> 2 data branches + #149 (until its three items land) = 3; -> 2 once #149 lands. Deleting the 29 + 2 + w83-3 = 32. Delete command is in the window's hands; this block deleted nothing.
