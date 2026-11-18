# Session Handoff — 2026-10-03T20:40Z

<!-- session-meta
task_id: T-646
tier: STANDARD
timestamp: 2026-10-03T20:40:30Z
commit: c12a47a
one_line_summary: 51.2 NHL silent drops: Kalshi SJ/TB/LA/NJ codes were dropped (379/1,595 mkts); parser+aliases+counters on unmerged branch c12a47a.
gg_touched: GG-403, GG-405
adr_touched: none
plan_deliverable_moved: no
-->

**Trigger:** wave complete. **Branch:** `session/20261003T201919Z-w51-nhl-team-codes` @ `c12a47a` — pushed, NOT merged.

## Strategic Decisions This Session
| Decision | Where |
|---|---|
| Unique-split parser rule + 4 aliases; any 3-letter code parses | DECISION_LOG 2026-10-03 T-646 |

## What changed
- `nhl_pregame.py`, `nhl_shadow_eval.py`: TEAM_ALIASES, `split_team_codes`, abstention counters (stdout + `run_log.jsonl`).
- `tests/test_nhl_team_codes.py` (real tickers); EXP-036 results note; GG-403 PARTIALLY RESOLVED, GG-405 counter half done.
- Full suite: earlier run 1598 passed / 28 skipped, only my own (since fixed) test failing; final rerun NOT confirmed at close-out.

## Pending
- Merge gated on operator (deploy restarts t4-mlb mid-postseason). After merge+deploy: confirm counters on a live run, then close GG-403.
- Unproven: 195-vs-240 shortfall attributed to this drop. Not registered: SemanticFloorViolation=1 in MLB T1 log.
- Out of scope, untouched: GG-401, 404, 407, 405 cron hours.

## Resume
`git -C <repo> fetch && git checkout session/20261003T201919Z-w51-nhl-team-codes && PYTHONPATH=src python3 -m pytest tests -q`
