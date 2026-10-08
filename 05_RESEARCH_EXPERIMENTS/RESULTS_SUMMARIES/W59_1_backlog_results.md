# W59.1 — Gap backlog results (2026-10-08)

**Status: PARTIAL.** Parts A, B, D done. Part C (GG-498, `deploy/cron.conf` mirror) NOT done: the operator declined a long single-terminal run.

## OPEN before -> after
176 -> 151 (25 closed). Parity 173 headers = 173 status lines; uniqueness check passes.

## Counts per class
| Class | Count | Where |
|---|---|---|
| RESOLVED (evidence in code/git/VPS) | 21 | Part A 17 + GG-200, GG-318, GG-329 + 1 pre-step |
| CLOSED-AS-DUPLICATE | 4 | GG-305->GG-230, GG-343->GG-309, GG-351->GG-230, plus Part A |
| SUPERSEDED | see archive | Part A |
| STILL OPEN, dated state + next action | 151 | all annotated "W59.1" |

Most remaining gaps are open design, data, or operator-decision items. Many carry "not re-verified this session" — those were not closed on a document's say-so. `scripts/retire_resolved_gaps.py` now also retires CLOSED-AS-DUPLICATE/SUPERSEDED (11 tests pass).

## 15 most important still-open gaps, by what they block
**Scores / G6 evidence**
1. GG-300 — 95.6% of the clean T4M-PROJ cohort has no independent fill confirmation.
2. GG-301 — calibration headline reverses sign on the Kalshi-confirmed-fill subset (n=34).
3. GG-297 — 139 of 140 "OPEN" T4M-PROJ positions are canceled/zero-fill.
4. GG-204 — ADR-0028 G6 closure condition unclosable as written (T1 clean_n=0).
5. GG-320 — T4M-PROJ fails ADR-0068 C5 (band placement); operator decision.
6. GG-296 — shard-3 demand figure is a ring-buffer artifact.

**Data integrity**
7. GG-166 / GG-170 — game_date corruption/instability feeding resolution.
8. GG-414 — T4 resolved ledger unwritten since 2026-09-28.
9. GG-189 — 46 stuck-open positions, outcome-store gap.
10. GG-333 — EXP-035 candle instrument VOID.

**Ops / safety**
11. GG-441 — kill switch realized-loss-only and in-memory (operator decision).
12. GG-038 — kill-switch SLA 60s too slow for T4.
13. GG-321 — perishable attribution evidence (reflog/journal).
14. GG-498 — live crontab diverges from `deploy/cron.conf` (run_mlb_pregame 45 18 live vs 30 16 repo; EXP-037 and NHL shadow blocks absent).
15. GG-046 — T4 commercial validation hypothesis untested.

## Needs an operator decision
GG-320 (band placement), GG-441 (kill-switch persistence), GG-423 (staleness under zero Kelly), GG-306/GG-309/GG-345 (CLAUDE.md edits), GG-350 (dirty shared tree), GG-347 (unattributed restarts).

## Notes for later (registered, not fixed)
Stale "Gaps by Arm" index at top of the live log; GG-495..497 left to 59.2/W58.2.
