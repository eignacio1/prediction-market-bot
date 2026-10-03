# W51.1 Kill-switch truth — results (2026-10-03)

Read-only on the VPS. Premises P1-P4 all confirmed.

## D1 — Ledger (`logs/paper_portfolio_mlb.json`)
| Field | Value |
|---|---|
| initial_bankroll_usd | 1000.00 |
| bankroll_usd | 733.7471 |
| total_realized_pnl | -106.0099 |
| open positions | 17 (all T1, all `aged_open`/`api_no_result_48h`) |
| open stake (sum size_usd) | 160.243 |
| open game_date range | 2026-07-01 .. 2026-07-26 (entered 07-01T11:02Z .. 07-26T11:00Z) |
| closed positions | 468 |
| last_updated | 2026-08-06T00:05:01Z |

- Kill-switch definition (realized): 106.0099 / 1000 = **10.60%**
- Dashboard definition: (1000 - 733.7471) / 1000 = **26.63%**
- Identity: 733.7471 = 1000 - 106.0099 - 160.243 (exact). 26.63% = 10.60% realized + 16.02% open stake.

## D2 — Cron log / kill-switch state
- `[C4] Bankroll $733.75 | Daily loss $0.00 | Drawdown 10.6%` on every run through 2026-10-03 (first-C4 lines early file show 0.0%). No `Drawdown` line above 10.6% for this book.
- `KILL_SWITCH` in `paper_mlb_cron.log`: 0. `risk_eval_kill_switch` in `audit.jsonl`: 18 events, latest 2026-06-10 (daily-loss trigger, pre-ledger-reset); `audit_mlb_t4.jsonl` matches are T4 contamination/halt strings, not a T1 drawdown trip.
- Persistence: no T1 kill-switch state is persisted; each run recomputes from the file. T4 file flag `logs/t4_mlb_kill_switch.flag` absent. `t4-mlb` active.

## D3 — Why the file stopped being written
`PaperTrader._save()` (`c5_execution/paper_trader.py:328`) is the only writer and runs only inside mutations (`open_position`, `exit_position`, resolution paths). A 0-bet run does not write. Since 2026-08-06 there are no bets (kelly 0.0 under ADR-0048; latest run: 0 placed, 10 rejected by C4) AND no resolutions: **frozen because something broke** (resolver), compounded by nothing new being opened.

## D4 — Open positions
`resolve_mlb_cron.log`: 17,064 `HTTPError: 406` from statsapi.mlb.com; every run ends `No positions settled yet`; T4 `0 resolved of 9 (GG-048)`. Kalshi historical endpoint: all 17 `finalized` (16 result `scalar`, 1 `yes`). Resolver gap: GG-440. Nothing resolved/closed/edited.

## D5 — VERDICT: (d)
Not tripped, and correctly not tripped by the realized definition (10.60% < 20%); dashboard metric was wrong (26.63%). But the realized figure is 58 days stale and excludes $160.24 of stake already settled on Kalshi; if all 17 lost, realized = 26.6% > 20% (GG-441). Not (c): the engine as defined was not required to trip on the data it holds.

## D6 — Fix
Branch `session/20261003T201912Z-w51-killswitch-truth` @ `6cbe62f`, pushed, NOT merged (merge to main redeploys and restarts t4-mlb, GG-432). Dashboard tile + rail show realized drawdown, open stake separate, FROZEN label after 72h. 178 dashboard tests pass (`test_w51_1_drawdown_truth.py` added; `Live Terminal.html` mirrored for byte-fidelity tests).

## Gaps
GG-440 (resolver 406), GG-441 (kill switch blind to settled-unresolved stake), GG-442 (dashboard metric; fixed on branch). GG-431's stale-panel source is the same file age (2026-08-06T00:05Z + 58d20h = 2026-10-03T20:05Z) but is a separate panel; not fixed here.
