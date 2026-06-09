# ADR-0018 — Band Exit Mechanics: Bayesian Filter-Out for Execution Bands

**Status:** DRAFT — pending DS (Earl Ignacio) sign-off before ACCEPTED  
**Date:** 2026-06-09 SESSION 40  
**Decisions logged:** true  
**Author:** Claude Code (GG-017 resolution path)  
**Approval required:** DS (Earl Ignacio)  
**Supersedes:** Nothing — extends ADR-0014 (per-band decision trees) with symmetric exit logic  
**Related:** GG-017, ADR-0014 (per-band decision trees), ADR-0013 (T4 band budget), DECISION_LOG 2026-06-09

---

## Context

ADR-0014 specified per-band decision trees covering entry mechanics for T1–T5: probability method (Poisson CDF), sizing (Kelly by band), edge gate (MIN_EDGE), kill switches. Exit mechanics were not specified — ADR-0014 implicitly treated positions as hold-to-expiry.

Prediction markets are bilateral instruments. Kalshi supports both BUY (entry) and SELL (exit) of YES/NO contracts for any open position. A system that can only enter is not exploiting the full decision-space that the venue provides.

**GG-017** (registered SESSION 40) documents the architectural gap: every band has filter-IN logic but no filter-OUT logic. When in-game Bayesian evidence reverses against an open position, the system holds with no mechanism to exit — even when the same math that fired the entry now argues against the position.

**Operator mandate (Earl Ignacio, 2026-06-09):**  
> "Each bucket not only has a filter into — but should have a filter out of, all using quantifiable strategies (with qual enhancers). Yes — let's absolutely build it out, no need to cancel or change anything that's already in right now."

### Motivating example from Finals G3 (2026-06-08)

Bridges: T1 YES bets placed (model forecast ~55%+ for >10 pts). Final stat: 2 pts. At halftime (6 pts pace, Knicks losing, Bridges on bench), `p_t4` would have dropped to <5%. System held all YES positions to expiry at a total loss. Exit mechanics would have recovered some or all of the stake once the signal reversed below the cost-of-exit threshold.

---

## Decision

**Each execution band has symmetric filter-IN and filter-OUT logic.** The same Bayesian/Poisson math that generates entry signals is evaluated in reverse for exit signals on open positions. The exit decision is fully quantifiable with the same data already available to the entry path.

### 1. Exit Trigger (when to consider exiting)

For each open YES position on ticker `T`:
```
exit_candidate = (p_t4 < p_t1 - EXIT_THRESHOLD) AND (p_t4 < MIP)
```
For NO positions, symmetric:
```
exit_candidate = (p_t4 > p_t1 + EXIT_THRESHOLD) AND (p_t4 > (1 - MIP))
```

**EXIT_THRESHOLD = 0.10** (initial paper calibration value — 2× T4_MIN_DELTA_P=0.08, providing margin above noise floor; must be calibrated from live exit data via EXP-019).

Rationale: if `p_t4` has dropped 10pp below the pre-game prior AND below the current market implied probability, the market is now pricing the outcome more accurately than our entry signal did. Holding compounds the expected loss.

### 2. Exit Instrument (how to exit)

**Primary: SELL YES contract** (close the long position directly).  
**Fallback: BUY NO contract** (hedge — used when SELL spread is wider than BUY NO spread).

Selection rule: compare `(ask_no - bid_no)` vs `(ask_yes - bid_yes)`. Use the side with the narrower spread. In paper mode, record the exit at mid-price (same fill model as entry).

### 3. Exit Sizing (how much to exit)

**Full exit by default.** On initial implementation, exit the entire open position when the trigger fires. Partial exit (sized by Kelly on the reversal magnitude) is a Phase 2 enhancement — adds complexity without enough data to calibrate the partial-exit Kelly fraction.

Partial exit formula (reserved for ADR amendment post-calibration):  
`exit_contracts = Kelly(f*, reversal_magnitude) × total_open_contracts`

### 4. Qual Enhancer: T3 FADE Signal

T3 FADE signal amplifies the exit decision — it does NOT gate it. If `t3_signal == "FADE"` AND exit trigger fires: proceed to cost model and execute. If `t3_signal == "FADE"` alone (without trigger): no exit (qual signal cannot override quantitative trigger).

This mirrors the T3 entry architecture: T3 modifies edge, it does not originate the bet.

### 5. Time Gate: Final-N-Minutes Illiquidity Protection

No exits in the final `EXIT_TIME_GATE_MINUTES = 3` minutes of regulation. Rationale: bid/ask spreads widen dramatically near market close (market makers reduce inventory risk). The spread cost of exit exceeds the expected loss from holding in most cases. EXIT_TIME_GATE_MINUTES aligns with T5's firing window (final 3 min) — positions in the T5 window are near-resolution and hold is correct behavior.

### 6. Cost Model: Only Exit When It Pays

Exit fires only if:
```
E[holding_loss] > spread_cost_of_exit
```
Where:
- `E[holding_loss] = (p_current - p_t4) × stake` — expected additional loss if model is right
- `spread_cost_of_exit = (ask - mid) × contracts` — cost to execute the exit at current ask

In paper mode: spread is estimated as `mid_price × VIG_SPREAD_ESTIMATE` where `VIG_SPREAD_ESTIMATE = 0.04` (calibration value — needs real bid/ask data at G6). If spread data is unavailable, fall back to EXIT_SPREAD_FLOOR = 0.02 (Kalshi taker fee baseline).

### 7. Kill Switch Interaction

Exit evaluation is part of the existing `_run_cycle()` loop. Exit orders are subject to the same T4 band kill switch: if `T4_BUDGET_EXHAUSTED`, no new entries OR exits — the kill switch halts the entire band. System-level kill switch halts everything including exit attempts. This is correct: the kill switch is a global halt, not a selective filter.

---

## Implementation Targets (Phase 6/7 paper scope)

| Component | Change |
|---|---|
| `paper_trader.py` | Add `exit_position(ticker, reason, price)` method. Records exit in closed position with `exit_reason`, `exit_price`, `exit_pnl`. |
| `VenueAdapter` / `KalshiClient` | Add `sell_order(ticker, contracts)` method. Routes to Kalshi SELL endpoint. Paper mode: no-op + return mid-price. |
| `run_t4_live.py:_run_cycle()` | Before entry evaluation loop: iterate open positions, compute `p_t4` for each, evaluate exit trigger + cost model. Exits precede entries. |
| `paper_portfolio_t4.json` | New fields per closed position: `exit_reason`, `exit_price`, `exit_pnl`, `exit_trigger_p`. |
| Tests | `TestExitPosition` class: trigger fires, cost model blocks, time gate blocks, qual enhancer amplifies, kill switch prevents. |

**Phase 8 additions (reserved for superseding ADR):**
- Live SELL order execution with real bid/ask spread data
- Partial exit sizing (Kelly on reversal magnitude)
- EXIT_THRESHOLD empirical calibration from paper exit data (EXP-019)

---

## What This ADR Does NOT Change

- Current open positions — no retroactive exits on any G3 or earlier positions
- T1 band — T1 positions run to expiry by design (no T4 live data during T1 window). Exit mechanics apply only when same-day T4 data is available for a T1 ticker.
- Kelly entry sizing — unchanged for all bands
- MIN_EDGE gate — unchanged
- Kill switch thresholds — unchanged
- Any ADR-0001 through ADR-0017 decisions

---

## Risks and Mitigations

| Risk | Mitigation |
|---|---|
| EXIT_THRESHOLD miscalibration → churning (exits on noise, re-enters) | Cost model prevents churn: exit only if E[holding_loss] > spread_cost. EXP-019 calibrates EXIT_THRESHOLD from paper exit data before T4 ACTIVE. |
| Spread estimate inaccurate in paper mode → wrong cost model decision | Conservative VIG_SPREAD_ESTIMATE=0.04 deliberately overestimates cost — biases system toward holding, not churning. Error is recoverable. |
| Exit logic adds latency to _run_cycle() (extra p_t4 computations) | Exit evaluation uses same GameStateModel call as entry path. Incremental cost is O(open_positions) Poisson CDF calls — sub-millisecond at current portfolio size. |
| Exit fires in final minutes → wide spread, bad fill | Time gate (EXIT_TIME_GATE_MINUTES=3) prevents this. T5 window is protected. |

---

## Gate for Activation

This ADR is DRAFT. Implementation is blocked until DS (Earl Ignacio) signs off. Once ACCEPTED:
1. Implement `exit_position()` in `paper_trader.py` (T-146)
2. Implement exit evaluation in `run_t4_live.py:_run_cycle()` (T-147)
3. Add `sell_order()` to `VenueAdapter` interface (paper no-op first)
4. Register EXP-019: EXIT_THRESHOLD calibration from paper exit data
5. GG-017 status updated to RESOLVED

---

## Decision Principles Applied

- **Symmetric decision trees** — entry and exit use the same mathematical framework; no asymmetric information usage.
- **Qual enhancers amplify, never originate** — T3 FADE amplifies exit decision; it cannot trigger an exit on its own.
- **Paper scope first** — live SELL execution deferred; paper mode proves the exit path before real fills.
- **Cost model prevents churn** — exit only when it economically makes sense; not on every signal reversal.
