# W75.5 — The NFL book closes (GG-746, GG-751, GG-763a)

**Status:** DONE (code merged in PR #262 at 7ab0c75; read back on the box 2026-10-15). **Pillar:** EXECUTION E2 / PROOF.
**Measure:** NFL positions open past game end + 24 h: 4 -> 0 (source: box `logs/paper_portfolio_t1_nfl_game_market.json`, 2026-10-15).

## Root cause (one line)
Nothing recurring booked the NFL game-market paper portfolio; the only booking was a one-time hand run on 10-07, and four positions were not yet final then.

## Fix
`position_sweep.sweep_open_positions` runs from the existing 09:30 `run_pregame_shadow_settle.py --refresh` cron for the NFL prefix (no new cron, service or workflow). `scripts/book_nfl_game_market_adr0071.py` is now a thin wrapper over it. Booking goes through `PaperTrader.settle_position_from_venue` (ADR-0071); no ledger row edited by hand.

## The four bookings
| Position | Game | Result | P&L |
|---|---|---|---|
| POS-BC7EBF8BB9 | CIN-MIA 10-11 | LOSS | -1.0 |
| POS-5606773C7E | CIN-MIA 10-11 | LOSS | -1.0 |
| POS-0EED4809E1 | TB-DAL 10-08 | WIN | +1.6316 |
| POS-515DEC8556 | TB-DAL 10-08 | WIN | +1.5 |

Realized P&L -160.6598 -> -159.5282. Backup `logs/paper_portfolio_t1_nfl_game_market.pre_w75_5_<UTC>.json`; report `logs/w75_5_nfl_booking_report.json`.

## Pattern sweep (box, 2026-10-14)
- Live books clean: `paper_portfolio.json`, `_g1_archive`, `_mlb`, `_t4`: 0 open. `_mlb_t4`: 7 open, none past game end. NFL: 0 open.
- Late opens only in non-live artifacts: `paper_portfolio.INVALIDATED_20260601.json` (3 NBA, 06-03) and `...manual_backup_20260923T000959Z.json` (42 NFL). Excluded from the invariant by name markers.
- NHL and MLB postseason arms have no paper portfolios (shadow ledgers settled by cron).

## 11-02 look
No effect. The look scores shadow ledgers, not the paper book; no pre-registered count or rule changes.

## GG-751 typed settlement
`SettleResult` FINAL / NOT_FINAL / LOOKUP_FAILED (`pregame_shadow/settle_result.py`). A missing final inside game date 00:00Z + 30 h + 24 h is NOT_FINAL; past it, LOOKUP_FAILED. Applied in `nfl_settlement`, `nba_settlement`, `mlb_settlement`, `nfl_espn_results.fetch_nfl_final_result`. Settle scripts exit 3 on any LOOKUP_FAILED. Not changed: `nhl_shadow_settle.py` (outside the named modules) — candidate follow-up.

## GG-763a ties
Pre-registration is explicit: moneyline tie = y=0.5. Shadow code matches; now tested. The paper path's tie refusal (GG-257) is a distinct, intentional mechanism. Nothing for the operator.

## Invariant
`assert_open_past_game_end` in `scripts/assert_ledger_invariants.py` (id OPE): any open position more than 24 h after game end, across all discovered live books. Alarm-only. Box read-back: books=6 open=7 violations=0.

## Read-back (box, 2026-10-15)
Box contains 7ab0c75. `run_pregame_shadow_settle.py --refresh` printed `position_sweep: open_before 0, booked 0, open_after 0`; invariants run clean; NFL portfolio open = 0.
Tests: 10 new, full local suite 4158 passed. Post-merge CI on 7ab0c75 failed one test on an MLB statsapi read timeout (network, unrelated); failed job re-run. A separate Deploy job summary was not observed for this merge; t4-mlb restart decision: none made by me (no change to t4 code).
