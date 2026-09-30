# T-592 (40.1) — Band Horizon Doctrine: landing, sweep, and C5 audit

**Status:** report only. No cell reassigned, activated or deactivated; no sizing touched. ADR-0068 remains PROPOSED (needs DS sign-off).

## D0 — Landing record
| Item | Before | After |
|---|---|---|
| origin/main | 0870f14 | ae49434 (via 9915f4a claim, c13e166 GG-320, ae49434 doctrine) |
| Doctrine files (CLAUDE.md, EXECUTION_BANDS.md, BAND_ASSIGNMENT_FRAMEWORK.md, ADR-0014, ADR-0068) | uncommitted in shared tree | landed unmodified in ae49434 |

**Wave 39 ancestry:** T-589 (fd3fc11), T-588 and T-590 were NOT all ancestors of origin/main. Merging T-589 (447c5df) conflicted in PLAN.md, TODO_NEXT.md and MEMORY_BANK.md. My resolution command was denied by the auto-mode classifier ("Permission for this action was denied by the Claude Code auto mode classifier. Reason: [Modify Shared Resources]."). I did not work around it and aborted the merge. **T-589 and T-590 remain unlanded; handed back to the operator.** Deploy risk: T-589 changes production `paper_trader.py` (`model_identity` mandatory); not deployed.

## D1 — Sweep
- Changed: `CLAUDE.md`, `EXECUTION_BANDS.md`, `BAND_ASSIGNMENT_FRAMEWORK.md`, `ADR-0014` (operator drafts, landed as-is); `EXECUTION_BANDS.md` ACTIVE-status row C1–C4 → C1–C5 (the only statement made wrong by the doctrine).
- Checked, left alone: remaining `01_SPEC/`, `02_ARCHITECTURE_DESIGN/` and nav/README files — no reversed complexity claim found.
- Doctrine text vs. measurement (disagreement, not edited): the doctrine says T1 is "the full 78-feature pipeline"; the live T1 model logs **18 features**. It also says T4S11 fires "thousands of evaluations per game"; measured T4 volume is hundreds of rows per game-day (GG-080).

## D2 — Criterion C5 across all 92 (MarketType, ExecutionBand) cells
Rule used: PASS needs a measured cadence consistent with the band's horizon and no unpaid stripping. MISFILED needs a measured contradiction. UNKNOWN is anything unmeasured.

**Counts: PASS 2 · MISFILED 1 · UNKNOWN 89.** (Registry status: 88 NOT_IMPLEMENTED, 2 BLOCKED, 1 ACTIVE, 1 DARK.)

| MarketType | Band | Registry | Horizon | Measured cadence | Tree depth (model inputs) | Verdict | Reason |
|---|---|---|---|---|---|---|---|
| mlb_player_prop_hits | T1 | NOT_IMPLEMENTED | 12–48h | daily cron 11:00 UTC (measured: cron log) | 18 features + threshold (model log: "18 features"; not 78) | **PASS** | deep-for-this-system tree at a once-daily cadence; no speed claim. Registry says NOT_IMPLEMENTED but cron runs it (discrepancy). Depth is 18, not the "78-feature" doctrine text |
| mlb_player_prop_hits | T2 | NOT_IMPLEMENTED | same-day | daily cron 19:30 UTC | 4 (p_t1, ba_l10, batting_slot, threshold) atop T1 | **PASS** | thin overlay at a same-day cadence; makes no latency claim. Registry says NOT_IMPLEMENTED but cron runs it |
| mlb_player_prop_hits | T3 | NOT_IMPLEMENTED | pre-tip (SLA 300s) | cron every 15 min, 20–23 & 0–3 UTC (900s vs 300s SLA) | ~4 (T1 p, T1 edge, T1 mid, live mid) | **UNKNOWN** | shallow, and cadence is slower than its own SLA; no advantage measured. Candidate MISFILED, not asserted. Registry says NOT_IMPLEMENTED but cron runs it |
| mlb_player_prop_hits | T4M-PROJ | ACTIVE | in-play (SLA 45s) | measured median 70s (min 45s, p90 99s; POLL_INTERVAL_S=45) | 3 scalars (h_so_far, ba_l10, ab_remaining) + threshold | **MISFILED** | shallow at a ~60s cadence; T-569 latency thesis NOT SUPPORTED (current feature set); 30 logged fields, 3 used. GG-320 |
| mlb_player_prop_hits | T4M-ARITH | BLOCKED | in-play (SLA 45s) | UNKNOWN (BLOCKED, not running) | not measured | **UNKNOWN** | BLOCKED; no live cadence |
| mlb_player_prop_hits | T4M-FLOW | BLOCKED | in-play (SLA 45s) | UNKNOWN (BLOCKED, not running) | not measured | **UNKNOWN** | BLOCKED; no live cadence |
| mlb_player_prop_hits | T5 | NOT_IMPLEMENTED | per EXECUTION_BANDS.md | UNKNOWN (BLOCKED, not running) | not measured | **UNKNOWN** | BLOCKED; no live cadence |
| nba_player_points | T4 | DARK | in-play (SLA 5s) | UNKNOWN (DARK) | not measured | **UNKNOWN** | DARK/frozen per operator directive; no live cadence |
| mlb_moneyline | T1 | NOT_IMPLEMENTED | 12–48h | UNKNOWN (no runner) | n/a (not built) | **UNKNOWN** | cell not built; no cadence or tree to measure |
| mlb_moneyline | T2 | NOT_IMPLEMENTED | same-day | UNKNOWN (no runner) | n/a (not built) | **UNKNOWN** | cell not built; no cadence or tree to measure |
| mlb_moneyline | T3 | NOT_IMPLEMENTED | pre-tip (SLA 300s) | UNKNOWN (no runner) | n/a (not built) | **UNKNOWN** | cell not built; no cadence or tree to measure |
| mlb_moneyline | T4 | NOT_IMPLEMENTED | in-play (SLA 5s) | UNKNOWN (no runner) | n/a (not built) | **UNKNOWN** | cell not built; no cadence or tree to measure |
| mlb_moneyline | T5 | NOT_IMPLEMENTED | per EXECUTION_BANDS.md | UNKNOWN (no runner) | n/a (not built) | **UNKNOWN** | cell not built; no cadence or tree to measure |
| mlb_run_line | T1 | NOT_IMPLEMENTED | 12–48h | UNKNOWN (no runner) | n/a (not built) | **UNKNOWN** | cell not built; no cadence or tree to measure |
| mlb_run_line | T2 | NOT_IMPLEMENTED | same-day | UNKNOWN (no runner) | n/a (not built) | **UNKNOWN** | cell not built; no cadence or tree to measure |
| mlb_run_line | T3 | NOT_IMPLEMENTED | pre-tip (SLA 300s) | UNKNOWN (no runner) | n/a (not built) | **UNKNOWN** | cell not built; no cadence or tree to measure |
| mlb_run_line | T4 | NOT_IMPLEMENTED | in-play (SLA 5s) | UNKNOWN (no runner) | n/a (not built) | **UNKNOWN** | cell not built; no cadence or tree to measure |
| mlb_run_line | T5 | NOT_IMPLEMENTED | per EXECUTION_BANDS.md | UNKNOWN (no runner) | n/a (not built) | **UNKNOWN** | cell not built; no cadence or tree to measure |
| mlb_game_total | T1 | NOT_IMPLEMENTED | 12–48h | UNKNOWN (no runner) | n/a (not built) | **UNKNOWN** | cell not built; no cadence or tree to measure |
| mlb_game_total | T2 | NOT_IMPLEMENTED | same-day | UNKNOWN (no runner) | n/a (not built) | **UNKNOWN** | cell not built; no cadence or tree to measure |
| mlb_game_total | T3 | NOT_IMPLEMENTED | pre-tip (SLA 300s) | UNKNOWN (no runner) | n/a (not built) | **UNKNOWN** | cell not built; no cadence or tree to measure |
| mlb_game_total | T4 | NOT_IMPLEMENTED | in-play (SLA 5s) | UNKNOWN (no runner) | n/a (not built) | **UNKNOWN** | cell not built; no cadence or tree to measure |
| mlb_game_total | T5 | NOT_IMPLEMENTED | per EXECUTION_BANDS.md | UNKNOWN (no runner) | n/a (not built) | **UNKNOWN** | cell not built; no cadence or tree to measure |
| mlb_team_total | T1 | NOT_IMPLEMENTED | 12–48h | UNKNOWN (no runner) | n/a (not built) | **UNKNOWN** | cell not built; no cadence or tree to measure |
| mlb_team_total | T2 | NOT_IMPLEMENTED | same-day | UNKNOWN (no runner) | n/a (not built) | **UNKNOWN** | cell not built; no cadence or tree to measure |
| mlb_team_total | T3 | NOT_IMPLEMENTED | pre-tip (SLA 300s) | UNKNOWN (no runner) | n/a (not built) | **UNKNOWN** | cell not built; no cadence or tree to measure |
| mlb_team_total | T4 | NOT_IMPLEMENTED | in-play (SLA 5s) | UNKNOWN (no runner) | n/a (not built) | **UNKNOWN** | cell not built; no cadence or tree to measure |
| mlb_team_total | T5 | NOT_IMPLEMENTED | per EXECUTION_BANDS.md | UNKNOWN (no runner) | n/a (not built) | **UNKNOWN** | cell not built; no cadence or tree to measure |
| mlb_partial_game | T1 | NOT_IMPLEMENTED | 12–48h | UNKNOWN (no runner) | n/a (not built) | **UNKNOWN** | cell not built; no cadence or tree to measure |
| mlb_partial_game | T2 | NOT_IMPLEMENTED | same-day | UNKNOWN (no runner) | n/a (not built) | **UNKNOWN** | cell not built; no cadence or tree to measure |
| mlb_partial_game | T3 | NOT_IMPLEMENTED | pre-tip (SLA 300s) | UNKNOWN (no runner) | n/a (not built) | **UNKNOWN** | cell not built; no cadence or tree to measure |
| mlb_partial_game | T4 | NOT_IMPLEMENTED | in-play (SLA 5s) | UNKNOWN (no runner) | n/a (not built) | **UNKNOWN** | cell not built; no cadence or tree to measure |
| mlb_partial_game | T5 | NOT_IMPLEMENTED | per EXECUTION_BANDS.md | UNKNOWN (no runner) | n/a (not built) | **UNKNOWN** | cell not built; no cadence or tree to measure |
| mlb_moneyline | T4M-ARITH | NOT_IMPLEMENTED | in-play (SLA 45s) | UNKNOWN (no runner) | n/a (not built) | **UNKNOWN** | cell not built; no cadence or tree to measure |
| mlb_moneyline | T4M-FLOW | NOT_IMPLEMENTED | in-play (SLA 45s) | UNKNOWN (no runner) | n/a (not built) | **UNKNOWN** | cell not built; no cadence or tree to measure |
| mlb_run_line | T4M-ARITH | NOT_IMPLEMENTED | in-play (SLA 45s) | UNKNOWN (no runner) | n/a (not built) | **UNKNOWN** | cell not built; no cadence or tree to measure |
| mlb_run_line | T4M-FLOW | NOT_IMPLEMENTED | in-play (SLA 45s) | UNKNOWN (no runner) | n/a (not built) | **UNKNOWN** | cell not built; no cadence or tree to measure |
| mlb_game_total | T4M-ARITH | NOT_IMPLEMENTED | in-play (SLA 45s) | UNKNOWN (no runner) | n/a (not built) | **UNKNOWN** | cell not built; no cadence or tree to measure |
| mlb_game_total | T4M-FLOW | NOT_IMPLEMENTED | in-play (SLA 45s) | UNKNOWN (no runner) | n/a (not built) | **UNKNOWN** | cell not built; no cadence or tree to measure |
| mlb_team_total | T4M-ARITH | NOT_IMPLEMENTED | in-play (SLA 45s) | UNKNOWN (no runner) | n/a (not built) | **UNKNOWN** | cell not built; no cadence or tree to measure |
| mlb_team_total | T4M-FLOW | NOT_IMPLEMENTED | in-play (SLA 45s) | UNKNOWN (no runner) | n/a (not built) | **UNKNOWN** | cell not built; no cadence or tree to measure |
| mlb_partial_game | T4M-ARITH | NOT_IMPLEMENTED | in-play (SLA 45s) | UNKNOWN (no runner) | n/a (not built) | **UNKNOWN** | cell not built; no cadence or tree to measure |
| mlb_partial_game | T4M-FLOW | NOT_IMPLEMENTED | in-play (SLA 45s) | UNKNOWN (no runner) | n/a (not built) | **UNKNOWN** | cell not built; no cadence or tree to measure |
| nfl_moneyline | T1 | NOT_IMPLEMENTED | 12–48h | UNKNOWN (no runner) | n/a (not built) | **UNKNOWN** | cell not built; no cadence or tree to measure |
| nfl_moneyline | T2 | NOT_IMPLEMENTED | same-day | UNKNOWN (no runner) | n/a (not built) | **UNKNOWN** | cell not built; no cadence or tree to measure |
| nfl_moneyline | T3 | NOT_IMPLEMENTED | pre-tip (SLA 300s) | UNKNOWN (no runner) | n/a (not built) | **UNKNOWN** | cell not built; no cadence or tree to measure |
| nfl_moneyline | T4 | NOT_IMPLEMENTED | in-play (SLA 5s) | UNKNOWN (no runner) | n/a (not built) | **UNKNOWN** | cell not built; no cadence or tree to measure |
| nfl_moneyline | T5 | NOT_IMPLEMENTED | per EXECUTION_BANDS.md | UNKNOWN (no runner) | n/a (not built) | **UNKNOWN** | cell not built; no cadence or tree to measure |
| nfl_spread | T1 | NOT_IMPLEMENTED | 12–48h | UNKNOWN (no runner) | n/a (not built) | **UNKNOWN** | cell not built; no cadence or tree to measure |
| nfl_spread | T2 | NOT_IMPLEMENTED | same-day | UNKNOWN (no runner) | n/a (not built) | **UNKNOWN** | cell not built; no cadence or tree to measure |
| nfl_spread | T3 | NOT_IMPLEMENTED | pre-tip (SLA 300s) | UNKNOWN (no runner) | n/a (not built) | **UNKNOWN** | cell not built; no cadence or tree to measure |
| nfl_spread | T4 | NOT_IMPLEMENTED | in-play (SLA 5s) | UNKNOWN (no runner) | n/a (not built) | **UNKNOWN** | cell not built; no cadence or tree to measure |
| nfl_spread | T5 | NOT_IMPLEMENTED | per EXECUTION_BANDS.md | UNKNOWN (no runner) | n/a (not built) | **UNKNOWN** | cell not built; no cadence or tree to measure |
| nfl_game_total | T1 | NOT_IMPLEMENTED | 12–48h | UNKNOWN (no runner) | n/a (not built) | **UNKNOWN** | cell not built; no cadence or tree to measure |
| nfl_game_total | T2 | NOT_IMPLEMENTED | same-day | UNKNOWN (no runner) | n/a (not built) | **UNKNOWN** | cell not built; no cadence or tree to measure |
| nfl_game_total | T3 | NOT_IMPLEMENTED | pre-tip (SLA 300s) | UNKNOWN (no runner) | n/a (not built) | **UNKNOWN** | cell not built; no cadence or tree to measure |
| nfl_game_total | T4 | NOT_IMPLEMENTED | in-play (SLA 5s) | UNKNOWN (no runner) | n/a (not built) | **UNKNOWN** | cell not built; no cadence or tree to measure |
| nfl_game_total | T5 | NOT_IMPLEMENTED | per EXECUTION_BANDS.md | UNKNOWN (no runner) | n/a (not built) | **UNKNOWN** | cell not built; no cadence or tree to measure |
| nfl_team_total | T1 | NOT_IMPLEMENTED | 12–48h | UNKNOWN (no runner) | n/a (not built) | **UNKNOWN** | cell not built; no cadence or tree to measure |
| nfl_team_total | T2 | NOT_IMPLEMENTED | same-day | UNKNOWN (no runner) | n/a (not built) | **UNKNOWN** | cell not built; no cadence or tree to measure |
| nfl_team_total | T3 | NOT_IMPLEMENTED | pre-tip (SLA 300s) | UNKNOWN (no runner) | n/a (not built) | **UNKNOWN** | cell not built; no cadence or tree to measure |
| nfl_team_total | T4 | NOT_IMPLEMENTED | in-play (SLA 5s) | UNKNOWN (no runner) | n/a (not built) | **UNKNOWN** | cell not built; no cadence or tree to measure |
| nfl_team_total | T5 | NOT_IMPLEMENTED | per EXECUTION_BANDS.md | UNKNOWN (no runner) | n/a (not built) | **UNKNOWN** | cell not built; no cadence or tree to measure |
| nfl_moneyline | T4NFL-ARITH | NOT_IMPLEMENTED | per EXECUTION_BANDS.md | UNKNOWN (no runner) | n/a (not built) | **UNKNOWN** | cell not built; no cadence or tree to measure |
| nfl_moneyline | T4NFL-FLOW | NOT_IMPLEMENTED | per EXECUTION_BANDS.md | UNKNOWN (no runner) | n/a (not built) | **UNKNOWN** | cell not built; no cadence or tree to measure |
| nfl_spread | T4NFL-ARITH | NOT_IMPLEMENTED | per EXECUTION_BANDS.md | UNKNOWN (no runner) | n/a (not built) | **UNKNOWN** | cell not built; no cadence or tree to measure |
| nfl_spread | T4NFL-FLOW | NOT_IMPLEMENTED | per EXECUTION_BANDS.md | UNKNOWN (no runner) | n/a (not built) | **UNKNOWN** | cell not built; no cadence or tree to measure |
| nfl_game_total | T4NFL-ARITH | NOT_IMPLEMENTED | per EXECUTION_BANDS.md | UNKNOWN (no runner) | n/a (not built) | **UNKNOWN** | cell not built; no cadence or tree to measure |
| nfl_game_total | T4NFL-FLOW | NOT_IMPLEMENTED | per EXECUTION_BANDS.md | UNKNOWN (no runner) | n/a (not built) | **UNKNOWN** | cell not built; no cadence or tree to measure |
| nfl_team_total | T4NFL-ARITH | NOT_IMPLEMENTED | per EXECUTION_BANDS.md | UNKNOWN (no runner) | n/a (not built) | **UNKNOWN** | cell not built; no cadence or tree to measure |
| nfl_team_total | T4NFL-FLOW | NOT_IMPLEMENTED | per EXECUTION_BANDS.md | UNKNOWN (no runner) | n/a (not built) | **UNKNOWN** | cell not built; no cadence or tree to measure |
| nhl_moneyline | T1 | NOT_IMPLEMENTED | 12–48h | UNKNOWN (no runner) | n/a (not built) | **UNKNOWN** | cell not built; no cadence or tree to measure |
| nhl_moneyline | T2 | NOT_IMPLEMENTED | same-day | UNKNOWN (no runner) | n/a (not built) | **UNKNOWN** | cell not built; no cadence or tree to measure |
| nhl_moneyline | T3 | NOT_IMPLEMENTED | pre-tip (SLA 300s) | UNKNOWN (no runner) | n/a (not built) | **UNKNOWN** | cell not built; no cadence or tree to measure |
| nhl_moneyline | T4 | NOT_IMPLEMENTED | in-play (SLA 5s) | UNKNOWN (no runner) | n/a (not built) | **UNKNOWN** | cell not built; no cadence or tree to measure |
| nhl_moneyline | T5 | NOT_IMPLEMENTED | per EXECUTION_BANDS.md | UNKNOWN (no runner) | n/a (not built) | **UNKNOWN** | cell not built; no cadence or tree to measure |
| nhl_puck_line | T1 | NOT_IMPLEMENTED | 12–48h | UNKNOWN (no runner) | n/a (not built) | **UNKNOWN** | cell not built; no cadence or tree to measure |
| nhl_puck_line | T2 | NOT_IMPLEMENTED | same-day | UNKNOWN (no runner) | n/a (not built) | **UNKNOWN** | cell not built; no cadence or tree to measure |
| nhl_puck_line | T3 | NOT_IMPLEMENTED | pre-tip (SLA 300s) | UNKNOWN (no runner) | n/a (not built) | **UNKNOWN** | cell not built; no cadence or tree to measure |
| nhl_puck_line | T4 | NOT_IMPLEMENTED | in-play (SLA 5s) | UNKNOWN (no runner) | n/a (not built) | **UNKNOWN** | cell not built; no cadence or tree to measure |
| nhl_puck_line | T5 | NOT_IMPLEMENTED | per EXECUTION_BANDS.md | UNKNOWN (no runner) | n/a (not built) | **UNKNOWN** | cell not built; no cadence or tree to measure |
| nhl_game_total | T1 | NOT_IMPLEMENTED | 12–48h | UNKNOWN (no runner) | n/a (not built) | **UNKNOWN** | cell not built; no cadence or tree to measure |
| nhl_game_total | T2 | NOT_IMPLEMENTED | same-day | UNKNOWN (no runner) | n/a (not built) | **UNKNOWN** | cell not built; no cadence or tree to measure |
| nhl_game_total | T3 | NOT_IMPLEMENTED | pre-tip (SLA 300s) | UNKNOWN (no runner) | n/a (not built) | **UNKNOWN** | cell not built; no cadence or tree to measure |
| nhl_game_total | T4 | NOT_IMPLEMENTED | in-play (SLA 5s) | UNKNOWN (no runner) | n/a (not built) | **UNKNOWN** | cell not built; no cadence or tree to measure |
| nhl_game_total | T5 | NOT_IMPLEMENTED | per EXECUTION_BANDS.md | UNKNOWN (no runner) | n/a (not built) | **UNKNOWN** | cell not built; no cadence or tree to measure |
| nhl_moneyline | T4NHL-ARITH | NOT_IMPLEMENTED | per EXECUTION_BANDS.md | UNKNOWN (no runner) | n/a (not built) | **UNKNOWN** | cell not built; no cadence or tree to measure |
| nhl_moneyline | T4NHL-FLOW | NOT_IMPLEMENTED | per EXECUTION_BANDS.md | UNKNOWN (no runner) | n/a (not built) | **UNKNOWN** | cell not built; no cadence or tree to measure |
| nhl_puck_line | T4NHL-ARITH | NOT_IMPLEMENTED | per EXECUTION_BANDS.md | UNKNOWN (no runner) | n/a (not built) | **UNKNOWN** | cell not built; no cadence or tree to measure |
| nhl_puck_line | T4NHL-FLOW | NOT_IMPLEMENTED | per EXECUTION_BANDS.md | UNKNOWN (no runner) | n/a (not built) | **UNKNOWN** | cell not built; no cadence or tree to measure |
| nhl_game_total | T4NHL-ARITH | NOT_IMPLEMENTED | per EXECUTION_BANDS.md | UNKNOWN (no runner) | n/a (not built) | **UNKNOWN** | cell not built; no cadence or tree to measure |
| nhl_game_total | T4NHL-FLOW | NOT_IMPLEMENTED | per EXECUTION_BANDS.md | UNKNOWN (no runner) | n/a (not built) | **UNKNOWN** | cell not built; no cadence or tree to measure |

## Registry vs. reality
The registry lists MLB hits T1/T2/T3 as NOT_IMPLEMENTED although cron runs all three (T1 daily 11:00 UTC, T2 daily 19:30, T3 every 15 min in the 20–23 and 0–3 UTC windows). Registered as a follow-up candidate, not fixed here.

## Other observations
- 2026-09-27 T1 run matched 0 players (`SemanticFloorViolation`, games_fetched=16).
- `CONTAMINATION_HALT` count in audit_mlb_t4.jsonl: 161,700 (expected at game end; not investigated).
- Q7 could not run in the worktree (caches missing).

## Closing paragraph
Of the 92 cells, **2 are demonstrably filed in a band their cadence and tree depth justify under C5** (MLB hits T1 and T2, both PASS on the narrow ground that they make no speed claim), **1 is demonstrably not** (T4M-PROJ), and **89 cannot be judged** because they are unbuilt, blocked, dark, or unmeasured (T3 is a candidate MISFILED: shallow, with a 900s cadence against a 300s SLA). The honest headline is that C5 currently validates 2 of 92 (2%), and the audit's main result is how little of the grid has been measured.
