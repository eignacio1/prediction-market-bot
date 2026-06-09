# ADR-0018 — Band Exit Mechanics: Symmetric Filter-Out for All Execution Bands

**Status:** ACCEPTED — APR-0018 signed 2026-06-09  
**Date:** 2026-06-09 SESSION 40  
**Decisions logged:** true  
**Author:** Claude Code (GG-017 resolution path)  
**Approved by:** DS (Earl Ignacio) — 2026-06-09 SESSION 40  
**Supersedes:** Nothing — extends ADR-0014 (per-band decision trees) with symmetric exit logic  
**Related:** GG-017, ADR-0014 (per-band decision trees), ADR-0010 (Kelly hierarchy), ADR-0016 (fee-adjusted edge gate), ADR-0013 (T4 band budget)

---

## Context

ADR-0014 specified per-band decision trees for T1–T5 covering entry mechanics only. The system currently holds all positions to market expiry regardless of subsequent signal behavior. Kalshi supports SELL YES and BUY NO — the full bilateral decision-space is unused.

**Operator mandate (Earl Ignacio, 2026-06-09):** Each execution band requires symmetric entry AND exit logic. No figure can be arbitrary. Exit logic cannot use entry logic inverted — it needs its own time-weighted, regression-tested, math-confirmed derivation for every threshold and every band.

This ADR defines the mathematical framework and derivation methodology for band exit mechanics. **No numeric threshold or sizing parameter is specified in this document.** Every parameter is derived via EXP-019, defined in full below. Code implementing exit mechanics is blocked until EXP-019 produces and validates each parameter via the methodology here.

---

## 1. Exit Signal — Correct Formulation

### Entry signal (established)

```
entry fires when:  p_model > mip_entry + MIN_EDGE + taker_fee(mip_entry)
```

Model probability exceeds market implied probability by the net transaction cost. The market is underpricing the outcome relative to the model.

### Exit signal (symmetric inverse of entry, not inverse of Kelly)

```
exit fires when:  mip_current > p_current + EXIT_NET_COST_BAND
```

Market implied probability now exceeds the model's current estimate by the net exit cost. The market is now *overpricing* the outcome relative to the model. Holding a YES position where the market prices YES above the model's estimate is equivalent to holding a bet with negative expected edge.

**Why this is not the Kelly-inverse computation:**  
The Kelly fraction governs *how much* to bet given a known edge. The exit signal governs *whether the edge has reversed*. Entry fires on edge existence; exit fires on edge reversal. Kelly determines position size in both cases, but it is downstream of the signal — not the signal itself.

### Time-weighted `p_current`

`p_current` is not the entry model probability re-evaluated. It is a fresh Poisson estimate conditioned on current game state:

```
k_needed      = ceil(threshold - pts_so_far)          # contracts still needed
λ_remaining   = adj_pace × time_remaining_min          # expected remaining points
p_current     = P(X ≥ k_needed | Poisson(λ_remaining))  # via Poisson CDF
```

Where `adj_pace` incorporates opponent defensive rating (ADR-0015 adj_λ formula) applied to the remaining time window.

This estimate is time-weighted in two ways:
1. **`λ_remaining` shrinks as time passes.** Near expiry, `p_current` converges toward 0 or 1 depending on score trajectory — the exit signal becomes sharper over time without any time-gate override.
2. **`k_needed` decreases as pts_so_far accumulates.** A player accelerating toward the threshold raises `p_current`; a player falling behind lowers it, potentially triggering exit.

Both effects are already captured by the same Poisson CDF used in T4 entry evaluation (`game_state_model.py`). There is no separate time-weighting formula — time is embedded in the model.

### Per-band `p_current` method

| Band | `p_current` method | Information available at exit time |
|------|--------------------|------------------------------------|
| T1 | Poisson CDF (live game state) — same T4 model applied to T1 tickers | All in-game data: pts_so_far, time_remaining, live pace, adj_λ |
| T2 | Poisson CDF (live game state) + injury status update | Same as T1 plus any updated injury/availability information |
| T3 | Poisson CDF (live game state) | Same as T1; T3 CONFIRM/FADE is now historical at exit time |
| T4 | Poisson CDF (live game state) | Native T4 computation — no change |
| T5 | Arithmetic certainty (`k_needed ≤ 0` or Poisson p ≥ T5_YES_CERTAINTY) | Same as T4; T5 positions exited if arithmetic certainty inverts |

All bands use the same Poisson CDF machinery during exit evaluation. The T4 live cycle is the universal exit evaluator for all open positions regardless of originating band.

---

## 2. Noise Buffer — Derivation Methodology

### Why a buffer is required

`p_current` is not exact — it is a Poisson CDF estimate with uncertainty in `λ_remaining`. If `mip_current` exceeds `p_current` by only a fraction of the estimation error, the exit signal is noise. The noise buffer prevents churning on estimation uncertainty.

### Derivation methodology (per band)

The methodology is identical to that used for T4_MIN_DELTA_P=0.08 (DECISION_LOG 2026-06-03, ADR-0010):

**Step 1 — Compute σ_λ at the band's typical exit operating window.**

σ_λ is the standard deviation of `λ_remaining` given realistic uncertainty in pace estimation. It is a function of time remaining and the number of game samples over which pace is estimated.

| Band | Typical exit window | Time remaining at exit | σ_λ basis |
|------|--------------------|-----------------------|-----------|
| T1 | In-game, Q1–Q4 (T4 cycle evaluates T1 positions) | Full game range | Wider at Q1, narrows through Q4 — compute at Q2 midpoint as representative |
| T2 | In-game, Q1–Q4 | Full game range | Same as T1 |
| T3 | In-game, Q1–Q4 (T3 pre-tip rationale expired once game starts) | Full game range | Same as T1 |
| T4 | Q3/Q4 (typical T4 firing window per ADR-0010) | 12–24 min remaining | σ_λ ≈ 0.5 (from ADR-0010 derivation) |
| T5 | Final 3 minutes | 0–3 min remaining | Near-deterministic; σ_λ approaches 0 |

σ_λ at Q2 midpoint (T1/T2/T3 representative): derive from 10-game rolling pace estimate variance. ADR-0010 derived T1 σ_λ = 2.055 for the pre-game estimate. For in-game Q2 (≈24 min elapsed, 24 min remaining): pace has been observed for 24 minutes. σ_λ_ingame = σ_λ_pregame × √(24/48) ≈ 2.055 × 0.707 ≈ 1.45. EXP-019 must validate this analytical estimate against observed pace variance in actual game data.

**Step 2 — Compute σ_p via Poisson CDF sensitivity.**

```
σ_p = |dP/dλ| × σ_λ

where dP/dλ = d/dλ [P(X ≥ k | Poisson(λ))]
             = P(X = k-1 | Poisson(λ))       # Poisson CDF derivative identity
             = exp(-λ) × λ^(k-1) / (k-1)!
```

This is evaluated at the representative λ and the threshold-specific k for each band. The derivative is maximized near `λ = k` (player on threshold pace) and diminishes for extreme thresholds — matching the intuition that edge estimation uncertainty is highest near the threshold.

**Step 3 — Set NOISE_BUFFER_BAND.**

```
NOISE_BUFFER_BAND = max(2 × σ_p, EXIT_NET_COST_BAND)
```

Where `EXIT_NET_COST_BAND` is the minimum market-vs-model divergence for exit to be profitable (Component 3 below). The noise buffer must exceed both the statistical noise floor (2σ_p) and the economic floor (exit cost).

EXP-019A must:
- Compute `σ_p` analytically at the representative operating window for each band (Step 2 formula)
- Validate the analytic `σ_p` against observed `p_current` variance in paper position trajectories
- Confirm that `NOISE_BUFFER_BAND = max(2σ_p, EXIT_NET_COST_BAND)` minimizes false exits in simulation
- Document the derivation chain so each numeric value traces to a formula, not an assumption

No NOISE_BUFFER_BAND value is specified in this ADR. EXP-019A produces all five per-band values.

---

## 3. Full vs Partial Exit Sizing — Derivation Methodology

### Decision framework

Given an exit signal fires (`mip_current > p_current + NOISE_BUFFER_BAND + EXIT_NET_COST_BAND`):

The optimal exit quantity is the amount that equates the Kelly-optimal position size under current information to the current holding. Kelly-optimal under current information:

```
f_star_current = max(0, (p_current - mip_current) / (1 - mip_current)) × kelly_fraction_band × capital_base_band
```

Note: `p_current < mip_current` when exit fires, so `f_star_current < 0` before the max. The max clamps to 0 — Kelly says "hold nothing."

Three cases:

| Case | Condition | Action |
|------|-----------|--------|
| **Full exit** | `f_star_current ≤ 0` (Kelly wants zero or short) | Exit all `holding` contracts. Evaluate NO entry separately via standard entry pipeline. |
| **Partial exit** | `0 < f_star_current < holding_usd` | Exit `holding_usd - f_star_current` worth of contracts. Retain `f_star_current`. |
| **Hold** | `f_star_current ≥ holding_usd` | Exit signal below threshold; Kelly still supports current size. |

### Why the Kelly fraction cannot simply be inverted from entry

At entry time, `kelly_fraction_band` was applied to the pre-game capital base under pre-game uncertainty (σ_λ_pregame). At exit time, `capital_base_band` has changed (other positions deployed, some closed), and `σ_λ_current` is different from the pre-game value. Applying the same Kelly fraction to a different capital base under different uncertainty produces a different `f_star_current` than the entry size — this is correct, not an inconsistency.

The exit sizing is not "reverse the entry." It is "what would Kelly size this position to be if I were entering fresh, given everything known right now?" The difference between that size and the current holding is what exits.

### Regression validation required (EXP-019B)

EXP-019B must validate the Kelly-optimal exit sizing against alternatives on paper position trajectories:

**Regression target:** `E[log(final_wealth)]` under three exit sizing policies:
1. Full exit always when signal fires
2. Partial exit to `f_star_current` (Kelly-inverse, proposed)
3. Fixed-fraction exit (50% of holding, as baseline)

**Inputs per position:** `p_current`, `mip_current`, `p_entry`, `mip_entry`, `kelly_fraction_band`, `time_remaining_min`, `pts_so_far`, `threshold`

**Acceptance criterion:** Policy 2 (Kelly-inverse) must produce statistically distinguishable improvement in `E[log(wealth)]` over Policy 1 (full exit) at n ≥ 50 exit events per band (or combined across bands if per-band n is insufficient). If Policy 2 is not statistically superior to Policy 1 at the required n, default to Policy 1 (full exit) — simpler is better when the improvement is unconfirmed.

---

## 4. Cost Model — Per-Band Derivation Methodology

### Exit cost formula

```
EXIT_NET_COST_BAND = taker_fee(mip_current) + spread_cost_band(time_remaining_min)
```

Where:
- `taker_fee(mip_current) = 0.07 × mip_current × (1 - mip_current)` — ADR-0016 formula, evaluated at current (not entry) market price
- `spread_cost_band(time_remaining_min)` — bid/ask spread per contract, which varies with time-to-expiry and band operating window

### `spread_cost_band` derivation methodology

The spread characterization is the most data-dependent component. In paper mode, Kalshi order responses do not return bid/ask spreads — only the mid-price (taker fill). Before EXP-019C can derive per-band spread models, the data collection mechanism must be built:

**Data collection requirement:** During every T4 cycle, record the current bid and ask for each active ticker alongside `mip`. Write to `logs/spread_observations.jsonl` with fields: `ticker`, `timestamp_utc`, `bid`, `ask`, `mid`, `time_remaining_min`, `pts_so_far`, `threshold`. This data is required for EXP-019C.

**EXP-019C methodology:** Once spread data is collected from ≥ 3 game nights:

```
spread_cost_band(time_remaining_min) = α_band + β_band × exp(-γ_band × time_remaining_min)
```

Where α (baseline spread), β (near-expiry spread premium), γ (decay rate) are fitted per band via nonlinear least squares regression on the observed `(spread, time_remaining)` pairs. The near-exponential form reflects market-maker inventory behavior: spreads are wide when positions are thin (overnight T1) or near-expiry (T5), and narrowest during active game-time markets (T4 Q3/Q4).

Per-band hypotheses about spread behavior (to be validated by EXP-019C):

| Band | Expected spread profile | Basis |
|------|------------------------|-------|
| T1 | Wide pre-game (thin overnight), narrows at tip-off, widens post-game | Market maker activity tracks game proximity |
| T2 | Similar to T1; injury-overlay adjustments may widen spreads on affected tickers | Thin market for injury-adjusted contracts |
| T3 | Moderate pre-tip; narrows as game approaches | Active market as bettors position |
| T4 | Narrowest in Q2–Q3 active scoring period; widens in final minutes | Highest market activity mid-game |
| T5 | Widest in final 3 minutes | Near-resolution inventory risk for market makers |

EXP-019C produces the α, β, γ coefficients per band. These replace any flat-estimate in `spread_cost_band(time_remaining_min)`.

### Full EXIT_NET_COST_BAND

```
EXIT_NET_COST_BAND = taker_fee(mip_current) + spread_cost_band(time_remaining_min)
```

This is not a constant — it varies with `mip_current` and `time_remaining_min` at every exit evaluation. The NOISE_BUFFER_BAND (Section 2) must be derived using the typical `EXIT_NET_COST_BAND` at the band's representative operating point (not a worst-case estimate), to avoid setting the noise buffer so high that legitimate exits are blocked.

---

## 5. Qual Enhancer: T3 FADE/CONFIRM

T3 signal modulates exit threshold — it does not gate it. Modulation is symmetric with how T3 modulates entry edge (ADR-0014):

```
effective_buffer = NOISE_BUFFER_BAND × qual_multiplier_exit

where:
  T3 FADE:    qual_multiplier_exit = 0.85   (market momentum confirms model's bearish re-estimate; exit more readily)
  T3 NEUTRAL: qual_multiplier_exit = 1.00
  T3 CONFIRM: qual_multiplier_exit = 1.15   (pre-tip momentum still argues for the position; raise exit bar slightly)
```

The multipliers are symmetric with ADR-0014 entry multipliers (CONFIRM=1.15, FADE=0.75 on entry edge). The exit-specific values (0.85/1.00/1.15) are to be validated by EXP-019A: confirm that T3 FADE positions that exited outperformed T3 FADE positions that held, and vice versa for T3 CONFIRM.

T3 signal is frozen at entry time for positions already open. T3 re-evaluates in the pre-tip window, not mid-game. At exit evaluation time, the T3 signal for an existing position is the signal that was applied at entry — it reflects the pre-tip momentum assessment, which is now historical context, not a live signal.

---

## 6. Universal Exit Evaluator — Execution Architecture

### All bands, one evaluator

All open positions (T1–T5) are eligible for exit evaluation in every `_run_cycle()` of the T4 live cycle. The T4 cycle already has the live Poisson model, current game state, and Kalshi price feed — it is the correct locus for exit evaluation across all bands.

T1 positions are the most important to exit when signals reverse. They are the largest positions (ADR-0010: T1_KELLY=0.10 on full bankroll) and they hold through the entire game. A T1 YES position on a player who picks up 4 early fouls in Q1 should be evaluated for exit as soon as the live game state reflects the change — not held to the 06:00 UTC resolve cron.

### Cycle order

```
_run_cycle():
    [1] EXIT EVALUATION (runs first)
        For each open position in all_open_positions (T1 + T2 + T3 + T4 + T5):
            p_current = GameStateModel.compute(game_state, player, threshold)
            exit_signal = mip_current > p_current + NOISE_BUFFER_BAND[position.band]
            if exit_signal:
                exit_cost = taker_fee(mip_current) + spread_cost_band[position.band](time_remaining)
                net_exit_benefit = (mip_current - p_current) × stake - exit_cost
                if net_exit_benefit > 0:
                    apply_qual_multiplier(position.t3_signal)
                    exit_quantity = compute_exit_quantity(f_star_current, holding)
                    execute_exit(position, exit_quantity)
    
    [2] ENTRY EVALUATION (runs after exits settled)
        Existing T4 entry logic — unchanged
        Capital freed by exits is immediately available for entries in this cycle
```

Exit precedes entry in every cycle. Capital freed by exits is available for new entries in the same cycle without any lag. Exit and entry on the same ticker in the same cycle is permitted — a T1 YES exit followed by a T4 NO entry on the same player-threshold is two independent decisions through the same entry pipeline.

### Pre-game market drift exit (Phase 2 — not in initial implementation)

Between T1 placement (22:00 UTC) and tip-off, there is no live game state — the Poisson model cannot compute `p_current` from game events. If Kalshi prices move significantly against an open T1 position pre-tip (market makers incorporating injury news, lineup changes, or late-breaking information), a market-drift exit may be warranted. This is a different flavor of exit signal:

```
pre_game_exit_signal = (mip_current - mip_entry) > MARKET_DRIFT_THRESHOLD
```

Pre-game exit runs in the PIPE-03 late window (01:30 UTC) or a new PIPE-03.5 pre-tip window. It does not require live game state — only current Kalshi prices and the entry record. `MARKET_DRIFT_THRESHOLD` derivation requires its own EXP (not EXP-019) — deferred to Phase 2 after initial in-game exit mechanics are validated.

---

## 7. EXP-019 — Full Experimental Protocol

EXP-019 is the gate experiment that produces all numeric parameters for this ADR. No parameter goes into production without EXP-019 validation.

### EXP-019A — Noise Buffer Derivation and Validation

**Objective:** Derive `NOISE_BUFFER_BAND` per band via analytical Poisson sensitivity analysis, then validate against paper position trajectory data.

**Analytical derivation (pre-data):**
1. For each band, identify representative exit operating window (time remaining, pts_so_far distribution)
2. Compute σ_λ at the representative window: for T4, σ_λ ≈ 0.5 (from ADR-0010); for T1/T2/T3 in-game, derive from pace variance over elapsed game time
3. Compute `σ_p = |dP/dλ| × σ_λ` at representative λ and threshold-specific k (formula in Section 2)
4. Derive `EXIT_NET_COST_BAND` at typical operating point (Section 4 formula)
5. Set candidate `NOISE_BUFFER_BAND = max(2σ_p, EXIT_NET_COST_BAND)` per band

**Empirical validation (post-data):**

Using paper portfolio trajectories (minimum 3 game nights of T4 live data with per-cycle `p_current` logs):

- For each position that was held to expiry, reconstruct whether the exit signal would have fired at any cycle using candidate `NOISE_BUFFER_BAND`
- Compare: `E[P&L | exit at first signal fire]` vs `E[P&L | hold to expiry]`
- Acceptance criterion: exit-at-signal produces strictly better average P&L than hold-to-expiry at ≥ 60% of signal-fire events. False exit rate (exit fires but hold would have been correct) ≤ 40%.
- If the analytically-derived buffer fails acceptance: adjust buffer upward by σ_p increments until acceptance criterion met. Document each adjustment.

**Output:** `NOISE_BUFFER_BAND` for each of T1, T2, T3, T4, T5 with derivation chain: formula → input values → computed σ_p → EXIT_NET_COST at representative point → max → candidate value → empirical validation result → final value.

### EXP-019B — Exit Sizing Validation (Full vs Partial)

**Objective:** Validate that Kelly-inverse partial exit (`f_star_current` target) produces better `E[log(wealth)]` than full exit, or establish that full exit is the correct default.

**Method:**
1. Retrospectively apply both policies to paper position book (all resolved positions from G3+)
2. For each position where exit signal would have fired: compute `f_star_current` at signal time, simulate P&L under Policy 1 (full exit) and Policy 2 (partial to `f_star_current`)
3. Compare `E[log(wealth)]` across all exit events under each policy

**Sample size requirement:** n ≥ 50 exit events per band (combined across bands if per-band n is insufficient at G3 data volume). If n < 50 at first run, accumulate data from G4 and G5 before finalizing.

**Acceptance criterion:** Policy 2 must produce mean `E[log(wealth)]` improvement ≥ 0.001 over Policy 1 at the n required. If not met: default to Policy 1 (full exit always). Simplicity wins when improvement is unconfirmed.

**Output:** Exit sizing policy per band (Policy 1 or 2), with empirical P&L comparison table.

### EXP-019C — Spread Characterization

**Prerequisite:** Spread observation logging activated (bid/ask recorded per cycle to `logs/spread_observations.jsonl`). Minimum 3 game nights of data.

**Method:**
1. For each active ticker in each cycle, fit `spread(time_remaining_min) = α + β × exp(-γ × time_remaining_min)` via nonlinear least squares on observed (spread, time_remaining) pairs
2. Fit separately per band operating window (T1: full game range; T4: Q3/Q4; T5: final 3 min)
3. Validate fit quality: R² ≥ 0.70 on held-out data

**Output:** (α, β, γ) coefficients per band. If R² < 0.70, report the empirical mean spread per band and time-remaining bucket (10-min buckets) as a lookup table instead of the parametric model.

**Acceptance criterion for cost model:** Fitted spread model must not underestimate spread by more than 20% at the 90th percentile of observed spreads. Conservative (overestimated) spread estimates produce false negatives (exit blocked when it should fire) — acceptable. Underestimation produces false positives (exit fires but spread larger than modeled, hurting P&L) — unacceptable.

### EXP-019 Timeline

| Sub-experiment | Data prerequisite | Earliest runnable |
|---|---|---|
| EXP-019A analytic | None — analytic derivation only | After ADR-0018 ACCEPTED |
| EXP-019A validation | 3 game nights T4 cycle logs with `p_current` per position per cycle | After G5 (estimated G4 + G5 Finals games) |
| EXP-019B | Same as EXP-019A validation | After G5 |
| EXP-019C | Spread observation logging active + 3 game nights | After spread logging deployed + 3 games |

---

## 8. Implementation Targets — All Bands

All implementation is blocked until ADR-0018 ACCEPTED (DS sign-off). EXP-019A analytic derivation begins post-acceptance; all other targets blocked until EXP-019A validation complete.

| Component | File | Change |
|---|---|---|
| Exit evaluation | `c4_risk_engine/risk.py` | `evaluate_exit(position, p_current, mip_current, t3_signal, time_remaining_min) → ExitDecision` — encapsulates exit signal, noise buffer lookup, cost model, qual multiplier. Band-agnostic; takes `band` from position record. |
| Position exit execution | `c5_execution/paper_trader.py` | `exit_position(ticker, contracts, price, reason, band) → dict` — closes partial or full; records `exit_reason`, `exit_price`, `exit_contracts`, `exit_pnl_realized`, `exit_trigger_p`, `exit_t3_signal`, `exit_time_remaining_min`. |
| Live exit cycle | `run_t4_live.py` | `_run_cycle()` extended: exit evaluation loop runs before entry loop; iterates all open positions from all bands; calls `evaluate_exit()` + `exit_position()`. |
| Sell order interface | `c5_execution/venue_adapter.py` | `sell_order(ticker, contracts) → OrderResult` — SELL YES endpoint. KalshiClient: routes to `/portfolio/orders` with side=SELL. Paper/demo mode: mid-price fill, no actual API call. |
| Spread observation logging | `run_t4_live.py` | Each cycle: write `(ticker, timestamp_utc, bid, ask, mid, time_remaining_min)` to `logs/spread_observations.jsonl`. Required for EXP-019C. |
| Exit constants | `c4_risk_engine/execution_bands.py` | `NOISE_BUFFER_BAND: dict[str, float]` — populated post-EXP-019A. `SPREAD_COST_MODEL: dict[str, Callable]` — parametric or lookup from EXP-019C. All values initialized to `None` until EXP-019 produces them; `evaluate_exit()` raises `NotImplementedError` if any band's constants are None. |
| Position record schema | `paper_portfolio.json`, `paper_portfolio_t4.json` | New fields on all closed positions from exit path: `exit_reason`, `exit_price`, `exit_contracts`, `exit_pnl_realized`, `exit_trigger_p`, `exit_t3_signal`, `exit_time_remaining_min`. |
| Tests | `tests/` | `TestExitEvaluation`: exit signal fires when `mip > p_current + buffer`; cost model blocks unprofitable exits; T3 FADE lowers buffer, T3 CONFIRM raises it; kill switch prevents exit; full exit when f_star ≤ 0; partial exit when 0 < f_star < holding; hold when f_star ≥ holding; all-band positions evaluated in cycle; exit runs before entry; spread logging writes correctly. |

---

## 9. Kill Switch Interaction

Exit evaluation is subject to all kill switch tiers without exception:

- **Band-level kill switch** (T4 budget exhausted): halts new entries AND exit evaluations for that band's positions. Positions opened under that band hold to expiry.
- **System-level kill switch**: halts all activity. No exits execute post-kill-switch.

Rationale: the kill switch is a governance halt. It exists because the system's behavior in the current state is uncertain enough to require human review. Selective exit after a kill switch fires would partially circumvent the halt and introduce position changes that occur without human oversight. No exceptions.

---

## 10. What This ADR Does NOT Change

- Any currently open position — no retroactive exits; G3 positions hold to expiry as-is
- Kelly entry sizing for any band — unchanged
- MIN_EDGE gate — unchanged
- Kill switch thresholds — unchanged
- `adj_lambda` formula (ADR-0015) — unchanged
- Fee formula (ADR-0016) — reused for exit cost calculation
- ADR-0001 through ADR-0017 — all unchanged
- `arb/` folder — REFERENCE ONLY; APR-0010 required before incorporation (ADR-0002)

---

## Gate for Activation (Summary)

```
ADR-0018 ACCEPTED (DS sign-off)
    → EXP-019A analytic derivation (NOISE_BUFFER_BAND formula, no data required)
    → Implement exit evaluation + logging infrastructure (T-146, T-147)
    → Data collection: spread observations + p_current per-cycle logs (3 game nights)
    → EXP-019A validation: confirm analytic NOISE_BUFFER_BAND against paper trajectories
    → EXP-019B: full vs partial exit sizing validation (n ≥ 50 exit events)
    → EXP-019C: spread characterization and cost model fitting
    → All parameters filled in execution_bands.py
    → GG-017 RESOLVED
    → Exit path designated ACTIVE for paper mode
```

Live capital exit mechanics require Phase 8 ADR (same gate structure as T4 ACTIVE designation).
