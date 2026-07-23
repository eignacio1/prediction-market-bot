# ADR-0035 — NBA Paper Portfolio Reset for 2026-27 Season

**Status:** ACCEPTED — DS sign-off Earl Ignacio 2026-06-30 SESSION 102 (see Sign-off table below; independently confirmed in `DECISION_LOG.md:53`). **Status field corrected 2026-07-22 (T-383/GG-056 close-out):** this header had gone stale, still reading "DRAFT — pending DS sign-off" for three weeks after the Sign-off table below was already filled in and `DECISION_LOG.md` already recorded ACCEPTED. The discrepancy let GG-056/APR-0027 (2026-07-17) treat this ADR's decision as still needing to be drafted, when it had already been decided 2026-06-30. This is a factual correction matching the pre-existing record, not a substantive change to the decision — no supersession required.
**Date:** 2026-06-30
**Gate:** Pre-NBA 2026-27 season activation (October 2026)
**Supersedes:** Nothing
**Amends:** Nothing (operational policy)
**Resolves:** Kill-switch state blocker (surfaced Session 102)

---

## Context

The NBA paper portfolio (`paper_portfolio.json`, tracked by `run_paper_trade.py`) accumulated 158 resolved bets across the 2025-26 NBA season (G2–G5), closing at:

- Bankroll: $751.10
- Initial bankroll: $1,000.00
- Cumulative realized drawdown: **24.9%**
- Total realized P&L: **−$248.90**

The `max_drawdown_pct` hard limit in `risk.py` is **20.0%** (GG-034 / ADR-0026 calibration,
2026-06-14).

`run_paper_trade.py` correctly computes and passes `current_drawdown_pct` to
`evaluate_forecast()` on every call (verified Session 102). This means on the **first NBA
paper evaluation in October 2026**, `current_drawdown_pct = 0.249 ≥ 0.20` triggers
`approval_status = KILL_SWITCH` — halting all new NBA paper bets before the 2026-27
accumulation phase begins.

The NBA paper system would arrive at the 2026-27 season opener dead on arrival.

---

## Why this is a paper-trading policy question, not a risk limit question

The kill switch logic is correct and must not be weakened for live capital. The issue is
that paper trading draws from the same risk engine with the same limits — by design
(paper trading should shadow live behavior), but with one asymmetry: a paper-portfolio
reset does not represent any real loss of capital. It resets a *validation dataset*, not
a *bankroll*.

The G6 commercial validation objective requires accumulating ≥500 unique markets
(ADR-0024 Tier 2) under the 2026-27 regular-season market regime. The existing 158 bets
are NBA Finals data — structurally insufficient per the ADR-0024 DS ruling (SESSION 51).
A fresh paper book for the 2026-27 season is not just permitted — it is required for the
validation to be structurally sound.

---

## Decision

**Reset the NBA paper portfolio book to a clean $1,000.00 baseline at the start of the
2026-27 NBA regular season (target: first scheduled game day, October 2026).**

Operational steps:
1. Before the first 2026-27 game night, backup `paper_portfolio.json` as
   `paper_portfolio.json.bak_s102_pre_2627` on the VPS.
2. Reset `paper_portfolio.json` to a clean state: `bankroll_usd = 1000.00`,
   `initial_bankroll_usd = 1000.00`, `total_realized_pnl = 0.0`, `open_positions = []`,
   `closed_positions = []`.
3. The `current_drawdown_pct` passed to `evaluate_forecast()` will be 0.0 on the first
   run. The kill switch will not fire. Normal evaluation resumes.

**The 158-bet historical record is preserved** in `paper_portfolio.json.bak_s102_pre_2627`
and in the C6 audit log (`logs/audit.jsonl`). EXP-017 analysis must treat this data as a
separate historical cohort (2025-26 NBA Finals / Finals window) and the 2026-27 fresh book
as the primary commercial validation leg per ADR-0024 Tier 2.

---

## What this ADR does NOT change

- `max_drawdown_pct = 0.20` in `risk.py` is unchanged. The kill switch threshold is
  correct for live capital and will remain operative for the 2026-27 paper season.
- Kill switch behavior under live capital (post-G6) must be re-evaluated via a separate
  ADR before activation (ADR-0005 scope).
- The MLB paper portfolio (`paper_portfolio_mlb.json`) is unaffected — it runs on a
  separate $1,000 book and has 0% drawdown.

---

## Alternatives considered

**B — Raise `max_drawdown_pct` for paper trading mode.** Rejected: weakening a
calibrated risk limit because paper state exceeded it inverts the causal logic. The limit
was calibrated correctly; the paper book exceeded it during a known structurally-inadequate
test period (NBA Finals). Raising the limit would introduce a paper/live divergence that
violates the shadow-trading principle and is harder to audit.

**C — Disable the drawdown check for BOT_ENV=paper.** Rejected: same reason as B.
The paper system shadowing live behavior is a first-order correctness property.

**D — Carry the drawdown forward into 2026-27.** Rejected: this would mean the first
paper evaluation immediately halts the NBA paper system. No G6 evidence would be
accumulated for the 2026-27 regular season. This is the failure mode that prompted the ADR.

---

## Pre-activation checklist (October 2026)

Before the first 2026-27 game night:

- [ ] Backup `paper_portfolio.json` to `.bak_s102_pre_2627` on VPS
- [ ] Reset `paper_portfolio.json` per the spec above
- [ ] Verify `run_paper_trade.py` produces `Drawdown 0.0%` on startup
- [ ] Confirm kill switch does NOT fire on first evaluation
- [ ] Log this action in DECISION_LOG with timestamp and operator sign-off
- [ ] Update MEMORY_BANK.md NBA portfolio baseline

---

## Decision log entry required

This ADR requires a DECISION_LOG entry at time of execution (October 2026), not at
sign-off today — the policy is decided now, the execution happens at season start.
The DECISION_LOG entry must reference this ADR and record the pre-reset portfolio
snapshot values.

---

## Sign-off

| Role | Name | Date | Notes |
|------|------|------|-------|
| DS   | Earl Ignacio | 2026-06-30 | Approved SESSION 102 |
| Operator | Earl Ignacio | 2026-06-30 | Approved SESSION 102 |

**Decisions logged:** true
