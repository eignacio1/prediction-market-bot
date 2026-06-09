# ADR-0018 — Band Exit Mechanics: Symmetric Filter-Out for All Execution Bands

**Status:** DRAFT — pending DS (Earl Ignacio) sign-off before ACCEPTED  
**Date:** 2026-06-09 SESSION 40  
**Decisions logged:** true  
**Author:** Claude Code (GG-017 resolution path)  
**Approval required:** DS (Earl Ignacio)  
**Supersedes:** Nothing — extends ADR-0014 (per-band decision trees) with symmetric exit logic  
**Related:** GG-017, ADR-0014, ADR-0010 (Kelly hierarchy), ADR-0013 (T4 band budget), DECISION_LOG 2026-06-09

---

## Context

ADR-0014 specified per-band decision trees for T1–T5: probability method, sizing, edge gate, kill switches. Exit mechanics were not specified. The system currently holds all positions to market expiry regardless of subsequent signal behavior.

**Operator mandate (Earl Ignacio, 2026-06-09):**  
> "Each bucket not only has a filter into — but should have a filter out of, all using quantifiable strategies (with qual enhancers)."

Prediction markets are bilateral instruments. Kalshi supports SELL YES and BUY NO on any open position. The full decision-space — symmetric entry AND exit per band — has not been exploited.

**This ADR governs exit mechanics universally across T1–T5.** It defines the mathematical framework for each component; calibration of band-specific parameters is deferred to EXP-019 (regression analysis against each band's math).

---

## Architectural Principle

**Each band's filter-out is the inverse of its filter-in, operating on the same mathematical framework.**

- Entry: `Kelly_optimal(p_entry, mip_entry, band) > 0` AND `net_edge > MIN_EDGE` → open position
- Exit: `Kelly_optimal(p_current, mip_current, band) < holding_size` → reduce to `Kelly_optimal`, or fully exit if `Kelly_optimal ≤ 0`
- Same probability method (Poisson CDF for T1–T4; arithmetic for T5). Same Kelly hierarchy. Same cost deduction. Same qual enhancers — entry amplifiers become exit amplifiers when signal reverses.

The exit decision is fully quantifiable from the same data already available to the entry path. No rule-based overrides, no time gates — math decides.

---

## Component 1 — Exit Trigger

### Formula

For each open position on ticker `T` with direction `D` (YES or NO):

```
p_current  = Poisson_CDF(threshold, adj_lambda(game_state))   # live T4 estimate
f_star     = kelly_optimal(p_current, mip_current, band_kelly_fraction)
holding    = current_stake / (1 - mip_entry)                  # contracts held

exit_signal = f_star < holding
```

Where `kelly_optimal` is:
```
f_star = max(0, (p_current - mip_current) / (1 - mip_current)) * band_kelly_fraction * capital
```

When `f_star = 0`: Kelly says hold nothing — full exit candidate.  
When `0 < f_star < holding`: Kelly says hold less — partial exit candidate.  
When `f_star ≥ holding`: Kelly says hold current size or more — no exit.

### Per-Band Kelly Fractions (from ADR-0010)

| Band | Kelly Fraction | Probability Method | Entry capital base |
|------|---------------|--------------------|--------------------|
| T1 | 0.10 | Poisson CDF (pre-game adj_λ) | Full deployable bankroll |
| T2 | 0.13 | Poisson CDF (adj_λ + injury overlay) | Full deployable bankroll |
| T3 | 0.07 | Poisson CDF (T1 base, T3 applies CONFIRM/FADE multiplier) | Kelly of T1 position size |
| T4 | 0.20 | Poisson CDF (live game state, flat paper sizing active) | T4 band budget |
| T5 | 0.25 | Arithmetic certainty (p≥0.85 / p≤0.15) | T4 band budget (shared) |

The same fraction governs both entry sizing and the exit `kelly_optimal` computation. If T1 entered at Kelly=0.10, the exit threshold evaluates at Kelly=0.10. There is no band-specific EXIT_THRESHOLD constant — the Kelly formula IS the threshold.

### Noise Buffering

Because `p_current` has estimation uncertainty, `f_star` fluctuates within a band around the true value. A materiality buffer prevents churning on estimation noise:

```
exit_signal = f_star < holding - EXIT_BUFFER_BAND
```

`EXIT_BUFFER_BAND` is the minimum meaningful reduction in Kelly position before triggering exit. It is band-specific and must be derived via regression analysis in EXP-019. Pre-calibration stub values:

| Band | EXIT_BUFFER_BAND (stub) | Derivation basis |
|------|------------------------|-----------------|
| T1 | 0.05 × initial_stake | T1 has the widest pre-game uncertainty (σ_λ=2.055); small fluctuations in p_current are noise |
| T2 | 0.04 × initial_stake | Narrower than T1 (injury overlay adds directional signal confidence) |
| T3 | 0.06 × initial_stake | Wider buffer: T3 positions are sized small; exit overhead cost is proportionally higher |
| T4 | 0.03 × initial_stake | T4 has the tightest uncertainty (live score state; σ_λ≈0.5 in Q3/Q4); exits are more confident |
| T5 | 0.02 × initial_stake | Arithmetic certainty regime; uncertainty is near-zero; exits are near-binary |

**These are stubs.** EXP-019 must replace all five via regression analysis before any exit path is designated ACTIVE. The regression inputs: (kelly_fraction, min_edge, p_entry, mip_entry, Δp_signal, time_to_expiry_min). The regression target: optimal exit timing that maximizes E[log(wealth)] across simulated position trajectories.

---

## Component 2 — Exit Sizing

### Kelly-Inverse Position Sizing

Exit sizing is not a separate formula — it is the same Kelly framework applied to the current state:

```
target_holding = kelly_optimal(p_current, mip_current, band_kelly_fraction)
exit_contracts = max(0, holding - target_holding)
```

Three cases:

| Case | Condition | Action |
|------|-----------|--------|
| Full exit | `target_holding ≤ 0` | Sell all `holding` contracts; optionally open NO position if `kelly_optimal(1-p_current, ...)` > 0 |
| Partial exit | `0 < target_holding < holding` | Sell `holding - target_holding` contracts; retain `target_holding` |
| Hold | `target_holding ≥ holding` | No exit; entry evaluation continues normally |

### NO Position After Full Exit

If after a full exit, Kelly is positive on the NO side (`p_current < mip_current - MIN_EDGE - fee`), the system may open a NO position. This is governed by the same entry filter as any other trade — it goes through the full entry pipeline, not a special exit path. The exit and the new NO entry are independent events.

### Regression Analysis Required (EXP-019)

The Kelly-inverse formula is mathematically exact for a single isolated position. In the context of a multi-position book with correlated outcomes (multiple players in the same game), the optimal partial exit fraction may deviate from the single-position formula. EXP-019 must validate:

1. Does Kelly-inverse partial exit improve E[log(wealth)] vs hold-to-expiry across the G3 position book?
2. What is the optimal EXIT_BUFFER_BAND per band (minimize churn while capturing genuine reversals)?
3. At what `Δp_signal` magnitude does partial exit produce better outcomes than full exit?

---

## Component 3 — Cost Model

### Formula

Exit only fires if net benefit exceeds transaction cost:

```
E_holding_loss = (p_entry - p_current) × stake          # expected loss from holding
exit_cost      = taker_fee(mip_current) + spread_cost   # cost to execute the exit

net_exit_benefit = E_holding_loss - exit_cost
exit_executes = net_exit_benefit > 0
```

Where:
```
taker_fee(mip) = 0.07 × mip × (1 - mip)   # ADR-0016 formula
spread_cost    = bid_ask_spread × contracts  # from live Kalshi bid/ask data
```

In paper mode (no real bid/ask data): `spread_cost = SPREAD_ESTIMATE_BAND × contracts`, where `SPREAD_ESTIMATE_BAND` is a per-band stub pending real data characterization in EXP-019:

| Band | SPREAD_ESTIMATE_BAND (stub) | Rationale |
|------|-----------------------------|-----------|
| T1 | 0.06 | Night-before thin liquidity; widest spreads |
| T2 | 0.05 | Same-day, slightly more liquid |
| T3 | 0.04 | Pre-tip; market makers active |
| T4 | 0.04 | In-play; active market; spread varies with score state |
| T5 | 0.08 | Near-expiry; spreads widen as uncertainty resolves |

**Note on T5:** T5 spread is widest near expiry because the outcome is near-certain and market makers reduce inventory risk. This is reflected in `SPREAD_ESTIMATE_BAND = 0.08` for T5 — making the cost model naturally more conservative about exits late in the game. No time gate is needed; the cost model captures this quantitatively. If the net_exit_benefit still exceeds cost despite wide T5 spreads, the exit is justified.

**Note on time-to-expiry:** Spread widens as contracts approach expiry. EXP-019 should characterize `spread_cost ~ f(time_to_expiry_min)` per band operating window and fit this into the cost model, replacing the flat stub.

---

## Component 4 — Qual Enhancer: T3 FADE

T3 FADE amplifies the exit decision; it does NOT gate it.

```
if t3_signal == "FADE":
    exit_threshold_multiplier = 0.85   # 15% reduction in required net_exit_benefit
elif t3_signal == "CONFIRM":
    exit_threshold_multiplier = 1.15   # 15% increase — CONFIRM signal argues against exit
else:  # NEUTRAL
    exit_threshold_multiplier = 1.00
```

Effective gate: `net_exit_benefit > 0 × exit_threshold_multiplier`.

T3 CONFIRM makes the system slightly more reluctant to exit (confidence in the entry signal is reinforced). T3 FADE makes the system slightly more willing to exit (pre-tip momentum was already pointing the wrong way). Neither overrides the quantitative exit trigger — they modulate the threshold symmetrically with how they modulate the entry edge (ADR-0014).

---

## Component 5 — Universal Exit Evaluator

**All open positions from any band (T1–T5) are eligible for exit evaluation.** T4's live Poisson cycle is the real-time evaluator for all bands during game hours. T1 positions (largest, placed night-before) are the most important to exit when signals reverse — they are not exempt from exit consideration.

### Exit Evaluation Architecture

```
run_t4_live.py:_run_cycle():
    1. [EXIT PATH — runs first, before entry evaluation]
       For each open position (from any band: T1, T2, T3, T4, T5):
           p_current = GameStateModel.compute(game_state, player, threshold)
           f_star = kelly_optimal(p_current, mip_current, band_kelly_fraction_for_position)
           if f_star < holding - EXIT_BUFFER_BAND[band]:
               if cost_model(p_current, mip_current, holding) > 0:
                   apply qual enhancer (t3_signal)
                   execute exit (partial or full per Kelly-inverse sizing)
    
    2. [ENTRY PATH — runs after exits settled]
       Evaluate new entry signals on all tickers (existing T4 logic)
```

Exit runs before entry so that capital freed by exits is available for new entries in the same cycle. Exit and entry on the same ticker in the same cycle is permitted — if a T1 YES position exits and Kelly is positive on the NO side at current price, a NO entry may follow.

### Pre-Game Exit: Market Drift

Between T1 placement (22:00 UTC) and tip-off (~23:00 UTC), there is no live game state. If `mip_current` drifts significantly against an open T1 position pre-game (market makers incorporating new information), a market-drift exit may be appropriate:

```
pre_game_exit_signal = (mip_current - mip_entry) > MARKET_DRIFT_THRESHOLD
```

`MARKET_DRIFT_THRESHOLD` is stub pending EXP-019 calibration. Pre-game exit evaluator runs as part of PIPE-03 late window (01:30 UTC) rather than in T4 live cycle (game not yet started). This is a Phase 2 implementation — initial ADR-0018 scope covers in-game (T4 cycle) exits only.

---

## Implementation Targets — All Bands

| Component | File | Change |
|---|---|---|
| Position exit method | `c5_execution/paper_trader.py` | `exit_position(ticker, contracts, price, reason, band)` — closes partial or full position; records `exit_reason`, `exit_price`, `exit_contracts`, `exit_pnl_realized`, `exit_trigger_p` in the position's closed record. |
| Exit evaluation logic | `c4_risk_engine/risk.py` | `evaluate_exit(position, p_current, mip_current, t3_signal) → ExitDecision(contracts_to_exit, reason)` — encapsulates Kelly-inverse + cost model + qual enhancer. Callable from any band's execution path. |
| Live exit cycle | `run_t4_live.py:_run_cycle()` | Before entry loop: iterate `trader.open_positions` (all bands), call `risk_engine.evaluate_exit()`, call `trader.exit_position()` when exit fires. |
| VenueAdapter sell interface | `c5_execution/venue_adapter.py` | `sell_order(ticker, contracts) → OrderResult` — sells YES contracts (exits long). KalshiClient implements against SELL endpoint. Paper mode: no-op with mid-price fill. |
| Position record schema | `paper_portfolio.json` / `paper_portfolio_t4.json` | New fields on closed positions: `exit_reason: str`, `exit_price: float`, `exit_contracts: int`, `exit_pnl_realized: float`, `exit_trigger_p: float`, `exit_t3_signal: str`. |
| Exit constants | `c4_risk_engine/execution_bands.py` | `EXIT_BUFFER_BAND: dict[str, float]` — per-band stub values (pending EXP-019). `SPREAD_ESTIMATE_BAND: dict[str, float]` — per-band stub values (pending EXP-019). |
| Tests | `tests/` | `TestExitPosition` — Kelly-inverse sizing (full/partial/hold cases), cost model blocks unprofitable exits, T3 FADE amplifies threshold, T3 CONFIRM raises threshold, kill switch prevents exit, NO position opened after full exit, all-band position eligibility, exit runs before entry in cycle. |

---

## Experiments Required

| Experiment | Scope | Gate |
|---|---|---|
| **EXP-019A** | Regression: EXIT_BUFFER_BAND per band vs simulated position trajectories | Must PASS before any band's exit path designated ACTIVE |
| **EXP-019B** | Regression: SPREAD_ESTIMATE_BAND per band vs real Kalshi bid/ask data | Must PASS before G6 live capital (paper spread estimates are acceptable for paper exit path) |
| **EXP-019C** | Kelly-inverse partial exit validation vs hold-to-expiry on paper position book | Validates that partial exits improve E[log(wealth)] on the actual paper book |

EXP-019 data collection begins from the first game where exit mechanics are active in paper mode.

---

## Kill Switch Interaction

Exit evaluation is subject to all existing kill switch tiers:
- **Band-level kill switch** (e.g., T4 budget exhausted): halts new entries AND exit evaluations for that band.
- **System-level kill switch**: halts all activity including exits.

If a band's kill switch has fired, positions opened under that band hold to expiry — the kill switch is a global halt and exit attempts are not a workaround. This is correct: the kill switch exists to stop all activity when limits are breached; selective exit after kill switch would partially circumvent the halt.

---

## What This ADR Does NOT Change

- Current open positions — no retroactive exits; no G3 or earlier positions touched
- Kelly entry sizing for any band — unchanged
- MIN_EDGE gate — unchanged
- Kill switch thresholds — unchanged
- ADR-0001 through ADR-0017 — all unchanged
- `arb/` folder — reference only, APR-0010 required (ADR-0002)

---

## Gate for Activation

**Status: DRAFT.** All implementation is blocked until DS sign-off.

Post sign-off implementation sequence:
1. `exit_position()` in `paper_trader.py` (T-146)
2. `evaluate_exit()` in `risk.py` (T-146)
3. Exit cycle in `run_t4_live.py:_run_cycle()` (T-147)
4. `sell_order()` in `VenueAdapter` / `KalshiClient` (T-147)
5. EXP-019A/B/C data collection begins (paper mode)
6. EXIT_BUFFER_BAND and SPREAD_ESTIMATE_BAND replaced with regression-derived values
7. GG-017 status updated to RESOLVED
