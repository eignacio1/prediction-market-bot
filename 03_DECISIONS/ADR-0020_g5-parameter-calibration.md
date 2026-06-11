# ADR-0020: G5 Parameter Calibration — MIN_EDGE_TO_APPROVE and T4_MIN_DELTA_P

**Status:** ACCEPTED  
**Date:** 2026-06-10  
**Author:** Earl Ignacio (DS) + Claude Code (implementation)  
**Supersedes:** Partial supersession of ADR-0013 (T4 throughput) and ADR-0016 (fee-adjusted edge gate) for the specific threshold values only. All other terms of those ADRs remain in force.  
**Decisions logged:** true

---

## Context

Post-G4 empirical analysis identified two calibration failures driving systematic T4 losses and T1 NO-bet proliferation:

### Problem 1 — T1: Noise-level NO bets (MIN_EDGE_TO_APPROVE = 0.02)

EXP-017B (Part B) measured EV against actual Kalshi prices (n=96 markets, G4 data):
- EV/bet vs Kalshi: **-$0.0361**
- Mean edge vs market: **-0.0176**
- NO bets: EV/bet = **-$0.0553** (dominant loss driver)
- YES bets: EV/bet = **-$0.0125** (marginal)

The Poisson model generates ~1.7× more NO bets than YES bets (62 NO vs 36 YES per game night in G4). At MIN_EDGE = 0.02, the model approves NO bets whose apparent edge is largely noise relative to Kalshi's efficiently-priced NO markets. 

Monte Carlo comparison (G4 game date, 10,000 simulations):

| Metric | MIN_EDGE=0.02 (baseline) | MIN_EDGE=0.04 (proposed) | Δ |
|--------|--------------------------|--------------------------|---|
| Bets | 33 (10Y/23N) | 30 (10Y/20N) | -3 NO bets |
| Total staked | $863 (86.3%) | $836 (83.6%) | -$27 |
| T4/T5 reserve | $137 (13.7%) | $164 (16.4%) | +$27 |
| Analytical EV | $184.27 (+21.35% ROI) | $185.02 (+22.13% ROI) | +$0.75 |
| Avg EV/bet | $5.58 | $6.17 | +$0.59 |
| Kill switch risk | 0.26% | 0.23% | -0.03% |
| Worst case | -$328 | -$290 | +$38 |

Eliminated bets: KAT NO 30 (edge 0.038), KAT NO 25 (0.0344), Bridges NO 25 (0.0395). All are NO bets with sub-0.04 edge — the category driving the most loss in EXP-017B.

**Note (GG-004 caveat):** MC improvement is modest because MC compares against Poisson null, not Kalshi prices. The real improvement at G5+ will be measured by EXP-017B Part B repeated with expanded n. GG-004 remains OPEN.

### Problem 2 — T4: Calibration-gap firing below noise floor (T4_MIN_DELTA_P = 0.08)

T4 computes `delta_p = p_t4 - p_t1` where:
- `p_t4` = raw Poisson Bayesian update (no Platt scaling)
- `p_t1` = Platt-scaled pre-game forecast

This difference captures BOTH calibration gap (systematic model difference) AND live game-state signal. Empirical analysis of G4 trajectory data (n=2,193 records) reveals:

**Calibration gap at game start** (t=48 min remaining, 0 pts scored — pure model difference, no game-state signal):
- Calibration gap distribution: mean = 0.376, σ = 0.165
- Current T4_MIN_DELTA_P = 0.08 is at the **0th percentile** of this distribution
- **89% of tickers already exceed 0.08 at t=0 of game** (game start, no points scored)
- Result: T4 fires on calibration bias from the opening tip, not on live signal
- Budget exhausted by Q2 in G4 (confirmed by trajectory data ending at t=34.6 min for most tickers)

**Derivation methodology** (EXP-019A σ-methodology, matching NOISE_BUFFER_BAND derivation):
1. Noise floor = mean calibration gap at game start (FIRE records) = 0.376
2. One standard deviation above noise floor: 0.376 + 0.165 = 0.541
3. Rounded to nearest 0.05: **T4_MIN_DELTA_P = 0.50**

Cross-check against percentile landmarks:
- P75 of calibration gap = 0.526 → consistent
- P85 of calibration gap = 0.547 → consistent
- mean+1σ = 0.541 → governs

**Impact at T4_MIN_DELTA_P = 0.50 vs 0.08:**
- FIRE records passing threshold: 436/1232 (35%) vs 1232/1232 (100%)
- Early game (t≥42): 32% survive vs 100% — filters calibration-bias-driven Q1/Q2 firing
- Budget preservation rate: ~65% reduction in early-game budget draw
- Late game (t<24): 0/2 survive — Q3/Q4 late action requires separate architectural fix (see Architectural Concern below)

---

## Decision

### D1 — MIN_EDGE_TO_APPROVE: 0.02 → 0.04

**Change:** `MIN_EDGE_TO_APPROVE = 0.04` in `src/prediction_market_bot/c4_risk_engine/risk.py`

Rationale: Filters sub-0.04 NO bets that EXP-017B shows are loss-generating vs Kalshi prices. MC confirms marginal improvement in model-vs-null terms; real improvement is directional and awaits EXP-017B Part B with larger n (G5+).

This is a conservative single-step tightening. Further revision toward 0.06 may be warranted after G5 data depending on EXP-017B Part B results. Formally re-examine at G6.

### D2 — T4_MIN_DELTA_P: 0.08 → 0.50

**Change:** `T4_MIN_DELTA_P = 0.50` in `src/prediction_market_bot/c3_forecasting/game_state_model.py`

Rationale: Derived from mean+1σ of the calibration-gap distribution at game start (EXP-019A σ-methodology). Sets threshold above the noise floor of the T4 signal, requiring genuine live-state divergence beyond systematic model calibration difference.

---

## Architectural Concern (registered, not resolved by this ADR)

The band-aid nature of D2 is acknowledged:

**Root cause**: `delta_p = p_t4 - p_t1` mixes calibration gap with live signal. Even at T4_MIN_DELTA_P=0.50, Q3/Q4 records show |delta_p| ≈ 0.01-0.04 because the Kalshi market converges to the Bayesian p_t4 over the game. A massive Q4 reversal (G4: 29-pt lead → 1-pt tip-in) would also have small |delta_p| in late stages, so T4 would not fire even with budget available.

**Correct fix**: Compute incremental delta_p = p_t4_current - p_t4_t0 (change from game-start p_t4, not from p_t1). This isolates the live game-state signal from calibration bias. Estimated incremental threshold: mean+2σ ≈ 0.48 (from G4 trajectory data, 36 tickers).

**Action**: Registered as GG-025 (OPEN). New ADR required before architectural change. This fix is post-G6.

---

## Consequences

- T1 bet pool shrinks by ~3 NO bets per game night at G4 scale
- T4 early-game budget consumption rate drops ~65%; more budget available for Q3/Q4 convergence scenarios (dependent on GG-023 fix for full benefit)
- EXP-017B Part B must be re-run at G5 to validate MIN_EDGE change against actual Kalshi prices (GG-004 trigger)
- T4_MIN_DELTA_P calibration is still a band-aid; Q3/Q4 T4 effectiveness remains architecturally constrained until GG-025 ADR

---

## Formally revise at G6

Per the standing obligation in the 2026-05-29 retroactive DECISION_LOG entry: all hard limits must be formally revised via ADR at G6 when live bankroll is set. This ADR does not satisfy that obligation — it addresses in-paper calibration. The G6 formal revision remains required.
