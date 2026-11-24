<!-- session-meta
task_id: W125.3
tier: STANDARD
timestamp: 2026-11-24T06:42:00Z
commit: 2d411f8
one_line_summary: W125.3: H-EDGE-5 NOT SUPPORTED (closed, parked for R&D); pot of gold 0 of 18 judged leaves EARNED; combo markets registered.
gg_touched: none
adr_touched: none
plan_deliverable_moved: no
vision_pillar: PROOF, BREADTH
gap_measure: P2, B4
gap_delta: P2 +2 verdicts (RESULT.md, RESULT_W125.md @ PR 563); B4 registered +4 combo families, logging +0
pattern_sweep: grep MarketType / _SPORT_BY_MARKET_TYPE / seat cells across src/ scripts/ tests/ 02_ARCHITECTURE_DESIGN/ -> registry, seat, claude_md, runtime and doc tests pass (195)
surface_delta: 0 (no cron/service/workflow; 4 NOT_IMPLEMENTED MarketTypes, 2 offline scripts)
-->

# Handoff W125.3 — H-EDGE-5 + pot of gold per leaf (Last reviewed 2026-11-24)

**Merged:** PR 563 (squash). Branch `session/20261124T011322Z-w125-3-flb`.

## Strategic Decisions This Session
| Decision | Where |
|---|---|
| H-EDGE-5 NOT SUPPORTED; hypothesis closed (EXP-H-EDGE-5, parked for R&D) | DECISION_LOG 11-24, HYPOTHESIS_DOCTRINE II.1 |
| Pot of gold: 0 of 18 judged leaves EARNED; 15 routed away | HYPOTHESIS_DOCTRINE II.5, `RESULT_W125.md` |

## What changed
- `h5_flb/`: PREREG, run_h5.py, RESULT.md. NBA ML [.90,.98) is a LEAD at n 63 (UNDERPOWERED), judge forward on 2026-27.
- `pot_of_gold/score_w125.py` + `out/w125/`; FLB bucket is a field on every leaf. 9 new tests.
- Combo markets exist on Kalshi: 4 MarketTypes registered NOT_IMPLEMENTED, seat cells added.

## Caveats
- Settlements joined only through 11-20; re-run `score_w125.py` after a refresh.
- B-024 backlog "why" line still needs the doctrine wording; ROLLING_BACKLOG.json not edited.
- Real capital: none. Kelly 0 everywhere.

**One thing pending:** operator ruling on the B-024 wording edit.
**Resume:** `/session-start`, then read `12_EXPLORATORY/pot_of_gold/RESULT_W125.md`.
