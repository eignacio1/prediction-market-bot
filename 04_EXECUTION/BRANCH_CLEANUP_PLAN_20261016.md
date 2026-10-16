# Branch cleanup plan — 2026-10-16 (strategic window; executed by block 79.4)

Operator, 2026-10-15 23:08 PT: "good lord we need a branch cleanup soon. What the fuck is going on there".

**Why there are 148 remote branches.** Every session pushes its own `session/*` branch, and none is ever deleted: the repo
setting `delete_branch_on_merge` is **false**, so even squash-merged PR branches stay. The window classified every branch on
2026-10-16 ~06:20 UTC. It could not act: this cloud session's GitHub proxy refuses ref deletes, tag creation and repository
settings writes (exact refusals in DECISION_LOG 2026-10-15 23:2x PT). A terminal on the operator's machine runs it (79.4).

**Rules.** (1) Never touch `main` or the head branch of an OPEN PR. (2) Never touch a branch whose last commit is under 3 days
old, or one claimed in `SESSION_CLAIMS.md` in the last 24 h. (3) A branch with work not on main is first preserved as the tag
`archive/<branch>` (same SHA), then deleted: nothing is lost, and `git push origin archive/<b>:refs/heads/<b>` restores it.
(4) A landed branch is either an ancestor of main, or the head of a merged PR whose head SHA is unchanged since the merge.
(5) The terminal recomputes all of this at run time with the same rules; this file is the expected answer to diff against.

## Group A — landed: delete (109)

| Branch | Why |
|---|---|
| `claude/peaceful-heisenberg-51g2ee` | ancestor of main |
| `exp036-prereg-2026-10-02` | ancestor of main |
| `hook-timeout-fix` | PR merged, head unchanged since |
| `session/20260824T233617Z-t484-phase2-input` | PR merged, head unchanged since |
| `session/20260825T043355Z-t493-adr0058-t1-reopen` | PR merged, head unchanged since |
| `session/20260826T045926Z-t497-t1-flat-stake-wrapper` | PR merged, head unchanged since |
| `session/20260922T235033Z-gg291-live-settlement` | ancestor of main |
| `session/20260922T235038Z-calibration-model-vs-market` | ancestor of main |
| `session/20260923T005823Z-efficiency-gradient-ranking` | ancestor of main |
| `session/20260923T005826Z-mlb-final-week-accrual` | ancestor of main |
| `session/20260923T234404Z-ledger-integrity-audit` | ancestor of main |
| `session/20260923T234421Z-t4-latency-thesis` | ancestor of main |
| `session/20260924T045058Z-cohort-verification` | ancestor of main |
| `session/20260925T015621Z-feature-space-audit` | ancestor of main |
| `session/20260925T015808Z-cohort-salvage-or-declare` | ancestor of main |
| `session/20260929T001556Z-t4-game-state-signal` | ancestor of main |
| `session/20260929T002124Z-gg303-activate-section0` | ancestor of main |
| `session/20260929T050106Z-t4-ab-harness` | ancestor of main |
| `session/20260929T052132Z-absent-attribute-pricing` | ancestor of main |
| `session/20260930T005221Z-pregame-feature-architecture` | ancestor of main |
| `session/20260930T050100Z-pregame-model-mlb` | ancestor of main |
| `session/20260930T050107Z-provenance-preservation` | ancestor of main |
| `session/20260930T053609Z-exp028-market-gate` | ancestor of main |
| `session/20261002T214039Z-sync-and-diagnose` | ancestor of main |
| `session/20261003T195850Z-cleanup-1003` | ancestor of main |
| `session/20261003T201912Z-w51-killswitch-truth` | ancestor of main |
| `session/20261003T201919Z-w51-nhl-team-codes` | ancestor of main |
| `session/20261005T065535Z-w54-gg432-mlb-arm` | ancestor of main |
| `session/20261005T234924Z-w56-mlb-ops` | ancestor of main |
| `session/20261005T234924Z-w56-mlb-ops-d4` | ancestor of main |
| `session/20261005T234929Z-w56-live-terminal` | ancestor of main |
| `session/20261005T235001Z-w56-visual-dashboard` | ancestor of main |
| `session/20261007T001931Z-w57-mlb-hits-dark` | ancestor of main |
| `session/20261007T001932Z-w57-books-truth` | PR merged, head unchanged since |
| `session/20261007T001955Z-w57-mlb-settle` | ancestor of main |
| `session/20261007T011627Z-w58-2-nba-arm` | ancestor of main |
| `session/20261007T011639Z-w58-3-calibration-engine` | ancestor of main |
| `session/20261008T003241Z-w59-2-calibration-correctness` | ancestor of main |
| `session/20261008T003250Z-w59-3-nba-nhl-readiness` | PR merged, head unchanged since |
| `session/20261008T003250Z-w59-3-nba-nhl-readiness-b` | PR merged, head unchanged since |
| `session/20261008T020449Z-w60-1-fill-truth` | ancestor of main |
| `session/20261008T020512Z-w60-3-dashboard-gaplog` | PR merged, head unchanged since |
| `session/20261008T020605Z-w60-2-nba-engine` | ancestor of main |
| `session/20261009T001930Z-w61-3-exploratory-track` | PR merged, head unchanged since |
| `session/20261009T001940Z-w61-1-gg527-fills-only` | ancestor of main |
| `session/20261009T002011Z-w61-2-verdict-readiness` | PR merged, head unchanged since |
| `session/20261009T061305Z-w62-2-exploratory-part2` | ancestor of main |
| `session/20261009T061313Z-w62-3-gate-t1-fills-nba` | PR merged, head unchanged since |
| `session/20261009T061336Z-w62-1-mlb-shadow-silent-arm` | PR merged, head unchanged since |
| `session/20261009T153630Z-w63-3-distance-fills` | ancestor of main |
| `session/20261009T153650Z-w63-1-mlb-full` | PR merged, head unchanged since |
| `session/20261009T173216Z-w64-1-nfl-qb-challenger` | PR merged, head unchanged since |
| `session/20261009T173222Z-w64-2-demo-fill-policy` | ancestor of main |
| `session/20261009T173234Z-w64-3-nba-player-points` | PR merged, head unchanged since |
| `session/20261011T022501Z-w65-1-nba-player-points` | ancestor of main |
| `session/20261011T022509Z-w65-2-forward-test-on` | PR merged, head unchanged since |
| `session/20261011T022519Z-w65-3-nfl-qb-challenger` | PR merged, head unchanged since |
| `session/20261011T061249Z-w66-2-demo-404` | PR merged, head unchanged since |
| `session/20261011T061249Z-w66-2-demo-404-b` | PR merged, head unchanged since |
| `session/20261011T061303Z-w66-3-nba-points-nfl-injury` | ancestor of main |
| `session/20261011T061317Z-w66-1-github-zero` | PR merged, head unchanged since |
| `session/20261011T154246Z-w67-2-forward-test-day1` | ancestor of main |
| `session/20261011T154250Z-w67-1-nba-points-nfl-injury` | ancestor of main |
| `session/20261011T154250Z-w67-1-silent-arm-points` | ancestor of main |
| `session/20261011T154307Z-w67-3-github-zero` | PR merged, head unchanged since |
| `session/20261011T191107Z-w68-2-shadow-stakes` | PR merged, head unchanged since |
| `session/20261011T191118Z-w68-3-nfl-totals-weather` | PR merged, head unchanged since |
| `session/20261012T235159Z-w69-3-nba-minutes` | ancestor of main |
| `session/20261012T235209Z-w69-2-nba-opening-night` | PR merged, head unchanged since |
| `session/20261013T010653Z-w70-1-rearm-nfl-audit` | PR merged, head unchanged since |
| `session/20261013T010659Z-w70-2-exp040` | PR merged, head unchanged since |
| `session/20261013T010705Z-w70-3-main-green` | PR merged, head unchanged since |
| `session/20261013T233400Z-w71-2-nba-opening-night` | PR merged, head unchanged since |
| `session/20261013T233401Z-w71-3-nba-availability` | PR merged, head unchanged since |
| `session/20261014T004112Z-w72-2-ledger-safety` | PR merged, head unchanged since |
| `session/20261014T004119Z-w72-1-readback-guards` | PR merged, head unchanged since |
| `session/20261014T004128Z-w72-3-deploy-truth` | PR merged, head unchanged since |
| `session/20261014T234416Z-w73-2-nfl-data-layer` | PR merged, head unchanged since |
| `session/20261014T234421Z-w73-3-nfl-engine-scaffold` | PR merged, head unchanged since |
| `session/w62-3-partb` | PR merged, head unchanged since |
| `session/w65-3-d1-manifest` | PR merged, head unchanged since |
| `session/w67-3-partA2-remove-push-trigger` | PR merged, head unchanged since |
| `session/w67-3-partB-cache-split` | PR merged, head unchanged since |
| `session/w68-1-ci-restore` | ancestor of main |
| `session/w68-2-part-b` | PR merged, head unchanged since |
| `session/w69-1-close` | PR merged, head unchanged since |
| `session/w70-2-exp040-injury-url` | PR merged, head unchanged since |
| `session/w73-1-turnoff` | PR merged, head unchanged since |
| `session/w73-1-turnoff-b` | PR merged, head unchanged since |
| `w52/gg432-deploy` | ancestor of main |
| `w52/landing` | ancestor of main |
| `w52/live-terminal` | ancestor of main |
| `w52/resolver-406` | PR merged, head unchanged since |
| `w55-3b-mlb-games-cache-sync` | PR merged, head unchanged since |
| `w58-1-docs` | ancestor of main |
| `w58-1-nhl-goalie-probe` | PR merged, head unchanged since |
| `w59-1-gg498-cron-mirror` | PR merged, head unchanged since |
| `w59-2-part-d` | ancestor of main |
| `w60-2-gg530` | PR merged, head unchanged since |
| `w61-3-part-b` | PR merged, head unchanged since |
| `w61-3-part-c` | PR merged, head unchanged since |
| `w62-1-silent-arm` | PR merged, head unchanged since |
| `w62-1-silent-arm-venv` | PR merged, head unchanged since |
| `w65-2-canary-cands` | PR merged, head unchanged since |
| `w65-2-canary-mve` | PR merged, head unchanged since |
| `w70-3-partb` | PR merged, head unchanged since |
| `w72-2-atomic-audit` | PR merged, head unchanged since |
| `w72-2-followups` | PR merged, head unchanged since |
| `w72-3-partb` | PR merged, head unchanged since |

## Group B — work not on main: tag `archive/<branch>`, then delete (33)

| Branch | Why |
|---|---|
| `session/20260903T002904Z-record-signoffs-20260903` | 42d PR closed/merged-then-moved |
| `session/20260903T184908Z-apr0033-accept-and-reroute` | 42d no PR |
| `session/20260904T000244Z-rerecord-adr-signoffs` | 42d no PR |
| `session/20260904T000252Z-gg242-filename-sweep` | 42d no PR |
| `session/20260905T162347Z-hyp011-moneyline-lr-run` | 41d no PR |
| `session/20260905T221723Z-t500-nfl-price-capture` | 40d no PR |
| `session/20260905T221739Z-nfl-readiness-audit` | 40d no PR |
| `session/20260905T221746Z-t4-nfl-nhl-scaffolding` | 40d no PR |
| `session/20260909T153928Z-gg255-mlb-t1-game-market-run-script` | 36d no PR |
| `session/20260910T012346Z-gg267-per-row-model-provenance` | 35d no PR |
| `session/20260918T142949Z-install-closeout-fix` | 28d no PR |
| `session/20260918T142949Z-install-closeout-fix-v2` | 24d no PR |
| `session/20260924T045012Z-clv-harness` | 22d no PR |
| `session/20260929T050111Z-exp027-epa-splits` | 17d no PR |
| `session/20260929T052125Z-gg312-parity-checker` | 17d no PR |
| `session/20260930T001333Z-evidence-boundary` | 16d no PR |
| `session/20260930T001343Z-t4-ledger-durability` | 16d no PR |
| `session/20260930T001400Z-gap-ledger-triage` | 16d no PR |
| `session/20260930T005212Z-provenance-allowlist` | 16d no PR |
| `session/20260930T050102Z-nfl-ingestion-widen` | 16d no PR |
| `session/20260930T053611Z-t4-structure-enhancer` | 16d no PR |
| `session/20260930T053614Z-reality-reconciliation` | 16d no PR |
| `session/20261001T012448Z-live-terminal-landing` | 15d no PR |
| `session/20261001T015004Z-multileg-coherence` | 15d no PR |
| `session/20261001T015005Z-archive-self-sufficiency` | 15d no PR |
| `session/20261002T192711Z-kalshi-nonsports-control` | 13d no PR |
| `session/20261002T192711Z-kalshi-nonsports-control-w46` | 13d no PR |
| `session/20261002T222218Z-fly-nfl-pregame` | 13d no PR |
| `session/20261003T000917Z-eyes-and-nhl` | 13d PR closed/merged-then-moved |
| `session/20261012T235158Z-w69-1-forward-readback` | 3d PR closed/merged-then-moved |
| `session/exp037-nfl-land` | 13d no PR |
| `session/exp037-nfl-land-rebased-0e` | 13d no PR |
| `w52/nhl-goalie-probe` | 12d no PR |

## Group C — keep (6)

| Branch | Why |
|---|---|
| `data/nhl-goalie-probe` | young 1.3d |
| `session/20260915T003401Z-nfl-capture-gap-0912` | open PR |
| `session/20260918T142928Z-gg291-threshold-backfill` | open PR |
| `session/20260923T005837Z-vig-grounding-from-archive` | open PR |
| `session/20260924T045227Z-resolved-filter` | open PR |
| `w761` | young 0.2d |

## Result — executed by W79.4, 2026-10-16 (~13:50-14:15Z)

**Counts.** Remote branches 167 -> 35 (167 is the run-time count: the plan's 148 plus branches W77-W79 added since; the 35 are `main`, 33 kept branches and W79.4's own). Remote tags 1 -> 37 (33 Group-B `archive/*`, 3 closed-PR `archive/*`, 1 pre-existing). Local branches 237 -> 117. Worktrees 168 -> 67. `delete_branch_on_merge` false -> **true** (read back true).

**Run-time diff against the plan.** Group B: identical (33). Group A: plan 109, run-time 97 deleted. The 12 difference is rule 2 (13 branches listed; one was already covered by the plan's own count): `session/20261013T233400Z-w71-2`, `...233401Z-w71-3`, `...004112Z-w72-2`, `...004119Z-w72-1`, `...004128Z-w72-3`, `...234416Z-w73-2`, `...234421Z-w73-3`, `session/w73-1-turnoff` (all under 3 days old by last-commit date; the plan listed them as landed but they are inside its own age rule), `w72-2-atomic-audit`, `w72-2-followups`, `w72-3-partb`. Group C: plan 6, run-time 36 = those young branches plus every branch pushed since the plan (W75-W79 session branches, open PR heads #277/#278, `data/nhl-goalie-probe`). `w761` no longer exists. They are not deleted; auto-delete stops new ones, and the next sweep removes them once past 3 days.

**Stale PRs.** #133 closed (GG-276 resolved by T-549; Saturday dow-6 NFL cron entry on main). #144 closed (GG-291 resolved by T-564; main stamps `kalshi_threshold` at open). #146 closed (APR-0036, T566 results, spread script and exp_output byte-identical on main). All three branches tagged `archive/<branch>` at the PR head SHA, tag SHAs verified by `git ls-remote`, then deleted. **#149 left open for the window:** T-574's `shared_tree_behind_origin` / `closed_wave_fences` landed via T-579, but `scripts/assert_service_activation.py`, its test, the T574 results note and the CLAUDE.md edit are not on main.

**This machine.** 101 clean, landed, non-protected worktrees removed (no `--force`); kept: 33 unlanded, 9 with uncommitted changes, 7 under a day old, W79/#277/#278 worktrees, detached ones, and the non-PM-worktrees paths. `sweep_stray_branches.sh --execute` deleted the landed local branches it could; it refused (`git branch -d`, never `-D`) on branches still checked out in kept worktrees and on 7 landed `session/*` branches whose remote refs are now gone (`w71-2`, `w71-3`, `w72-1`, `w72-3`, `w73-3`, `w75-4` and one more of the same kind): "not fully merged" against a deleted upstream. They are ancestors of `origin/main`; a `-D` would be safe, left for a later sweep.

**Refused:** nothing by GitHub or the harness.
