# Session Handoff — 2026-10-02T23:57Z

<!-- session-meta
task_id: T-608
tier: STANDARD
timestamp: 2026-10-02T23:57:00Z
commit: 574b85e
one_line_summary: EXP-037 (T-608) 47.2: NFL+MLB pregame shadow code, models, pre-regs built; NFL-only branch green, NOT landed, nothing on VPS.
gg_touched: none
adr_touched: ADR-0070
plan_deliverable_moved: no
-->

**Trigger:** operator-initiated window close. No D7 results summary written; DECISION_LOG/GG log untouched (47.1 owns them).

## Strategic Decisions This Session
| Decision | Where |
|---|---|
| ADR-0070 PROPOSED (probit-Platt deviates from ADR-0004) | a90b506 |
| NFL landing decoupled from MLB/doc work (separate branch) | exp037-nfl-land |

## State
- `session/exp037-nfl-land` @ fc4180d (pushed): origin/main + NFL work; full suite 3592 passed, 28 skipped. Only 2 existing files touched, both additive.
- `session/20261002T222218Z-fly-nfl-pregame` @ 574b85e (pushed): adds D0 report, ADR-0070, MLB model/runner/pre-reg, `--include-postseason`. No full suite run on it.
- NOT on main. VPS = 1e097e0, no EXP-037 cron block installed. No NFL T2/T3 or MLB cell flips; 4 NFL T1 cells flipped to SHADOW on branch only.
- D6(a): no stuck postseason positions; no resolver fix needed.

## One thing pending
Operator go-ahead to push `session/exp037-nfl-land` to main.

## Then
1. VPS: `git log --oneline HEAD..origin/main`, import-graph check, pull if additive; no t4-mlb restart, no pip.
2. `--refresh` seed, dry-run each cron line, install block from `deploy/cron_exp037_pregame_shadow.conf`, paste `crontab -l` + first-firing proof.
3. Full suite on session branch, land MLB; add `--include-postseason` to T1 cron; relax MLB NOT_IMPLEMENTED pin (tests/test_market_type_registry.py ~102).
4. After 2026-10-04: NFL T2/T3 rows, flips. Check 47.3 summary before NHL flips.
5. D7 summary with GAPS FOUND (list in prior chat: ADR-0070 number check, T1=T2=T3 features, Gaussian tie mass, kmult inferred, 9 aged T4/17 aged T1-T2 open positions, t4 resolved ledger unwritten since 09-28, stale players_2026.json, MLB 406/empty cache GG-084, fork-A git cherry list guessed).

## Resume
`scripts/new_session_worktree.sh "exp037-land-deploy"` then read this file.
