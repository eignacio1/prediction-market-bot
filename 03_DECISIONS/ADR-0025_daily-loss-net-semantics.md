# ADR-0025 — Formalize Net Semantics for Daily-Loss Accumulation

**Status:** ACCEPTED — 2026-06-12  
**Decision makers:** DS (Earl Ignacio)  
**Amends:** ADR-0012 (percentage-based daily loss limit) — formalizes net-accumulation semantics not specified there; ADR-0012 remains in force  
**Supersedes:** —  
**Related:** ADR-0012, KI-018, T-156, G3 incident (gross vs net divergence)

---

## Context

### What ADR-0012 left unspecified

ADR-0012 replaced the zombie `max_daily_loss_usd = $1,000` with `MAX_DAILY_LOSS_PCT = 0.15` and established that the threshold derives from `initial_bankroll`. It did not specify whether `current_daily_loss` accumulates on a **gross** basis (every losing trade adds, wins ignored) or a **net** basis (wins offset losses within the same day).

This gap matters. At G3, a profitable high-churn night produced:

| Metric | Value |
|--------|-------|
| Gross daily loss (sum of all losing trades) | $317.76 |
| Net daily P&L (Σ all trades) | −$198.84 |
| Kill-switch verdict under gross semantics | HALT |
| Kill-switch verdict under net semantics | NO HALT |

Under gross accumulation, a night where the system made money in aggregate would have triggered the kill switch. The kill switch is meant to detect single-session catastrophic loss, not aggregate trade volume. Gross semantics conflate the two.

### What the implementation already does

`PaperTrader._accumulate_daily_loss()` (introduced before ADR-0012 was written) implements net semantics:

```python
def _accumulate_daily_loss(self, pnl: float) -> None:
    self._reset_daily_loss_if_new_day()
    self._state["daily_net_pnl"] = round(
        self._state.get("daily_net_pnl", 0.0) + pnl, 4)
    self._state["current_daily_loss"] = round(
        max(0.0, -self._state["daily_net_pnl"]), 4)
```

`current_daily_loss = max(0, −daily_net_pnl)`. Wins offset losses; the kill switch fires only when the session is net negative by ≥ 15% of `initial_bankroll`. This is the correct semantics but was undocumented.

T-156 adds the first direct tests for this method and registers this ADR to make the contract explicit.

---

## Decision

**Net semantics are the intended and correct accumulation model for `current_daily_loss`.**

Formally:

```
daily_net_pnl(t)    = Σ pnl_i  for all trades i closed on calendar day t
current_daily_loss  = max(0.0, −daily_net_pnl(t))
kill_switch_fires   = current_daily_loss ≥ initial_bankroll × MAX_DAILY_LOSS_PCT
```

### Rationale

1. **The kill switch guards session-level net loss, not gross turnover.** A system that wins $200 and loses $150 in the same session is up $50 net. The daily kill switch must not fire — the system is performing correctly. Gross semantics would fire it.

2. **High-frequency evaluation bands amplify the gross/net divergence.** At ~1,000 evaluations per game, churn is intrinsic to system design. A gross accumulator would routinely fire the kill switch on profitable high-volume nights.

3. **Net semantics are consistent with the drawdown kill switch.** The drawdown check (`max_drawdown_pct`) operates on realized bankroll, which is inherently net. Two kill switches with incompatible semantics would create confusing audit trails.

### Cross-day isolation

`_reset_daily_loss_if_new_day()` zeros both `current_daily_loss` and `daily_net_pnl` at the first operation after a calendar-day boundary. Day N net P&L does not carry into day N+1. A profitable day N does not suppress or offset losses on day N+1.

### Threshold anchor

The kill-switch threshold is anchored to `initial_bankroll_usd` (the bankroll at session start), not the current bankroll. This prevents a feedback loop where a losing session makes the threshold progressively smaller, compounding difficulty.

---

## Test coverage (T-156)

`tests/test_t156_daily_loss.py` — 28 tests added:

| Class | Coverage |
|-------|----------|
| `TestAccumulateDailyLoss` | Single loss/profit, net semantics (offset/full/excess), additive accumulation, no-touch invariants for bankroll and total_realized_pnl |
| `TestResetDailyLossIfNewDay` | Same-day no-op, new-day reset (loss + net_pnl + date), no-touch invariants, missing-key edge case |
| `TestCrossDayTransitions` | Cross-day isolation (loss day N, fresh day N+1; win day N, loss day N+1; net_pnl independence) |
| `TestKillSwitchThresholdBoundary` | MAX_DAILY_LOSS_PCT constant, threshold derivation, below/at/above boundary, net recovery below threshold, initial_bankroll anchor |

---

## Consequences

**Positive:**
- The net-semantics contract is now explicit and testable.
- Kill switch behavior on profitable high-churn nights is deterministic and correct.
- 28 new tests lock the accumulation behavior; any future accidental reversion to gross semantics will fail immediately.

**Negative / risks:**
- None. This ADR formalizes existing behavior; no code changes required.

---

## G6 obligation (inherited from ADR-0012)

`MAX_DAILY_LOSS_PCT = 0.15` must be reconsidered at G6 when live bankroll is established. Net semantics do not change this obligation — the threshold value still requires formal review.
