# ADR-0071 — Kalshi Settlement Is the Resolution Source for Kalshi Paper Positions

**Status:** ACCEPTED
**Date:** 2026-10-04 23:50 PT (operator decision, DECISION_LOG 2026-10-05)
**Decisions logged:** true
**Author:** Session W54.3
**Approval:** operator (Earl Ignacio), 2026-10-04 23:50 PT
**Related:** GG-440 (resolver 406 / resolution source), GG-450 (cancelled markets), GG-228 (ledger-write provenance), GG-432 (PR #158, merged by a separate block), ADR-0016 (fees)
**Does not touch:** sizing, `kelly_fraction`, limits, order/position/fill code, ADR-0040/0048

## Context

The paper resolver booked outcomes from a stat feed (MLB statsapi, ESPN fallback) and compared a box-score line to the ticker threshold. That is a proxy for what Kalshi would have paid. Two failures followed: statsapi returns 406 to the VPS on a CDN cache MISS (W53.1), leaving positions open; and for games Kalshi cancelled or postponed, the proxy books a result real capital never received. 26 positions were affected on the day of this decision (17 T1, 9 T4M-PROJ; 16 sit on Kalshi-cancelled markets, 10 on postponed games replayed later).

## Decision

1. **Kalshi's own settlement is the source of truth** for any Kalshi paper position. `result` `yes`/`no` books WIN/LOSS from the position's direction, with the existing P&L math. Source: `/historical/markets/{ticker}`, then `/markets/{ticker}`.
2. **Cancelled markets** (`result = scalar`) are booked at Kalshi's `settlement_value_dollars` (YES value; `1 - value` for a NO position), with `cancelled = true`, outcome `CANCELLED`, `settlement_source = "kalshi"`. This is what real capital would have received. Cancelled rows are **excluded from G6 counts and from calibration/Brier**; they remain in realized P&L (the kill-switch input) because that money would have moved. They do not feed the same-day circuit breaker (historical bookkeeping, not a same-day loss).
3. **Postponed games** resolve on Kalshi's result for that ticker, whatever the replay date.
4. **statsapi/ESPN are a cross-check only.** The resolver logs `kalshi_stat_crosscheck_disagree` when they disagree; the feed cannot block, delay or change a booking.
5. **Live-ledger writes** that apply this rule retroactively require a backup of the ledger and a dry-run diff reviewed first (GG-228 provenance). Nothing in this ADR writes a live ledger.

## Consequences

- Positions no longer depend on a stat feed reachable from the VPS.
- `filter_clean` (scripts/run_band_monitor.py) drops `cancelled` rows, the single choke point for clean_n / G6 / power-calc / band-monitor calibration. Other readers of `closed_positions` (e.g. `build_t4_resolved_ledger.py`) are not yet audited for the flag; registered as follow-up.
- `win_rate` excludes cancelled rows.
- Any Kalshi payout rule not covered (e.g. a new result value) raises rather than guesses.
