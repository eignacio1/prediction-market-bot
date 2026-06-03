# ADR-0013: T4 Throughput-Aware Capital Budget

**Status:** ACCEPTED  
**Date:** 2026-06-02 SESSION 20  
**Decisions logged:** true  
**Supersedes:** Partially supersedes ADR-0010 for T4/T5 Kelly formula application (see § Relationship to ADR-0010)  
**Approval:** Operator sign-off required before T4_BAND_WEIGHT and T4_EXPECTED_TOTAL_EDGE stubs are replaced with calibrated values. ADR is accepted as architecture; constants are stubs pending G1 calibration.

---

## Context

T4 (in-play Bayesian band) evaluates approximately 1,000 market opportunities per game — player × threshold × 45s poll cycle across ~200 game cycles. The standard Kelly formula in C4 is:

```
bet_size = edge × kelly_fraction × bankroll
```

For `KELLY_T4=0.20`, `bankroll=$618`, typical `edge=0.05`:
```
bet_size = 0.05 × 0.20 × $618 = $6.18/bet
```

At ~1,000 T4 evaluations/game with a 15–20% fire rate (~150–200 bets), total T4 capital demand is ~$930–$1,236 — exceeding the entire bankroll. Without a budget constraint, T4 exhausts the portfolio's deployable capital (~$371) after ~60 bets, leaving 140+ approved bets unfunded per game.

This is KI-026, registered SESSION 19. `PAPER_T4_VIRTUAL=true` is the correct interim mode — it bypasses the problem by staging bets without bankroll deduction. This ADR establishes the architecture that makes `PAPER_T4_VIRTUAL=false` (T4 ACTIVE) viable at any capital scale.

---

## Decision

**T4 RiskEngine receives `t4_band_budget` as its `bankroll` parameter, not the full portfolio bankroll.**

```
t4_band_budget = deployable_capital × T4_BAND_WEIGHT
deployable_capital = portfolio_bankroll × (1 − RESERVE_MANDATE_PCT)
```

Kelly then operates within the band allocation:
```
bet_size = edge × KELLY_T4 × t4_band_budget
```

This scales correctly with capital ceiling and is capital-ceiling agnostic:

| Bankroll | T4_BAND_WEIGHT | t4_band_budget | bet_size (edge=0.05) |
|----------|---------------|----------------|----------------------|
| $618     | 0.10          | $37.08         | $0.37 → floored to $1 (paper) |
| $10,000  | 0.10          | $600           | $6.00 |
| $100,000 | 0.10          | $6,000         | $60.00 |
| $1,000,000 | 0.10        | $60,000        | $600.00 |

---

## Architecture

### Band budget model

```
deployable_capital = bankroll × (1 - RESERVE_MANDATE_PCT=0.40)
t4_band_budget     = deployable_capital × T4_BAND_WEIGHT
bet_size_i         = edge_i × KELLY_T4 × t4_band_budget
```

### Two-tier kill switch hierarchy

This ADR establishes a band-level kill switch independent of the system-level kill switches:

**Band-level (T4-specific):**
- Trigger: `t4_deployed_game >= t4_band_budget`
- Effect: T4 stops firing bets. Evaluation continues (log data only). Other bands (T1/T2/T3) are unaffected.
- Reset: Per-game-night. Resets to zero at next game start.

**System-level (unchanged from ADR-0012):**
- MAX_DAILY_LOSS_PCT=0.15: daily loss exceeds 15% of initial bankroll → KILL_SWITCH all bands
- max_drawdown_pct=0.20: realized drawdown exceeds 20% → KILL_SWITCH all bands

### PAPER_T4_VIRTUAL mode behaviour

**PAPER_T4_VIRTUAL=true (calibration mode, current default):**
- `t4_deployed_game` is tracked and logged with every VIRTUAL fire
- Band budget ceiling is NOT enforced
- Purpose: collect empirical data to calibrate T4_BAND_WEIGHT and T4_EXPECTED_TOTAL_EDGE
- All VIRTUAL log lines include `budget_track=$X.XX/Y.YY`

**PAPER_T4_VIRTUAL=false (T4 ACTIVE mode):**
- Band budget ceiling IS enforced
- When `t4_deployed_game + approved_size > t4_band_budget`: log `T4 BAND_BUDGET_EXHAUSTED`, skip fire, continue evaluating
- T4 ACTIVE is gated on calibrated constants (see § Activation Gates)

### Relationship to ADR-0010

ADR-0010 established band Kelly fractions: T3=0.07, T1=0.10, T2=0.13, T4=0.20, T5=0.25.

These fractions expressed *relative sizing* between bands, all operating against the full bankroll. ADR-0013 changes what `bankroll` means for T4/T5: it is now `t4_band_budget`, not the full portfolio. ADR-0010 Kelly fractions remain valid as *intra-band edge scaling* — they govern how much of the band budget is committed per unit of edge. T4=0.20 still sizes more aggressively per unit edge than T3=0.07; the change is that both operate on their respective band budgets rather than the full portfolio.

ADR-0010 is NOT superseded for T1/T2/T3, which continue operating on the full deployable capital under the existing reserve mandate.

---

## Parameters

### T4_BAND_WEIGHT (STUB — calibrate from G1)

**Current value:** `0.10`  
**Derivation:** Placeholder. Must be replaced with empirically derived value from G1 PAPER_T4_VIRTUAL data.

**Calibration procedure (post-G1):**
1. Extract total would-be deployment from `logs/audit_t4.jsonl`:
   ```bash
   grep '"T4 VIRTUAL"' logs/t4_live.log | grep -o 'budget_track=\$[0-9.]*' | tail -1
   ```
   Or from audit log: sum of all `approved_size` values across VIRTUAL fires in one game.
2. Decide target maximum T4 exposure per game as % of portfolio (operator decision: start at 10%).
3. `T4_BAND_WEIGHT = target_max_t4_exposure / (bankroll × (1 - RESERVE_MANDATE_PCT))`
4. Log derivation in DECISION_LOG before replacing stub.

**ADR-0013 is ACCEPTED as architecture; T4_BAND_WEIGHT stub replacement requires operator sign-off.**

### T4_EXPECTED_TOTAL_EDGE (STUB — calibrate from G1)

**Current value:** `5.0`  
**Derivation:** Placeholder. Represents the sum of all edges across T4 fires in one game.

**Calibration procedure (post-G1):**
1. From `logs/audit_t4.jsonl`: sum all `edge` values from VIRTUAL fires in one game.
2. Replace stub with that value.
3. This parameter is informational — it enables capacity planning (expected total deployed = T4_EXPECTED_TOTAL_EDGE × KELLY_T4 × t4_band_budget) but is not used in the sizing formula.

---

## Implementation

**File:** `src/prediction_market_bot/run_t4_live.py`

Changes:
- Import `RESERVE_MANDATE_PCT` from `risk.py`
- Constants `T4_BAND_WEIGHT`, `T4_EXPECTED_TOTAL_EDGE` (stubs)
- `_compute_t4_band_budget(portfolio)` function
- `_make_engines(t4_band_budget)` — receives band budget, passes as `bankroll` to RiskEngine
- `_run_cycle(...)` — accepts `t4_band_budget` and `t4_deployed_usd`; returns updated `t4_deployed_usd`
- Main loop: initializes band budget once per session, accumulates `t4_deployed_game`, logs budget status per cycle

No changes to `risk.py` (C4 interface unchanged). The band budget is an operational concern of the T4 runner, not a risk policy change.

**Verification:** Run `scripts/run_t4_budget_sim.py` before G1 to verify budget behaviour under parametric game simulation.

---

## Activation Gates

T4 ACTIVE (`PAPER_T4_VIRTUAL=false`) requires ALL of the following:

1. **This ADR accepted** (architecture confirmed)
2. **T4_BAND_WEIGHT calibrated** from G1+ PAPER_T4_VIRTUAL data (stub replaced, derivation logged in DECISION_LOG, operator sign-off)
3. **T4_EXPECTED_TOTAL_EDGE calibrated** from G1+ data
4. **EXP-018** — T4_MIN_DELTA_P calibration experiment complete (GG-007 item 1)
5. **DS-02 ADR** — ESPN API formally named as T4 data source, superseding ADR-0011's NBA CDN reference

---

## Risks

| Risk | Mitigation |
|------|-----------|
| T4_BAND_WEIGHT too small → budget exhausted early, most opportunities missed | Calibrate from G1 data. Start conservative (0.10); increase with evidence |
| T4_BAND_WEIGHT too large → T4 crowds out T1 capital | RESERVE_MANDATE_PCT=0.40 ensures T1 reserve is held before T4 budget is computed. T4 operates only on deployable capital × weight |
| Stale stub values remain in production → wrong sizing | T4 ACTIVE is gated on calibration; PAPER_T4_VIRTUAL=true is the default; stubs cannot silently enter live mode |
| Multi-game night: single budget shared across games | t4_band_budget is computed at session start. If multiple games run in one T4 session, budget is shared. Acceptable at current Finals scale (1 game/night). Revisit for regular season (10+ games/night) |

---

## Rejected Alternatives

**Priority queue with per-cycle sorting:** Evaluate all opportunities per cycle, rank by edge, fire top N within budget. Rejected — requires holding all opportunities before acting on any, conflicts with streaming 45s-cycle architecture and 50ms compute budget.

**Reduce KELLY_T4 fraction to achieve small bet sizes:** Confuses edge sensitivity (what kelly_fraction governs) with throughput capacity (what band weight governs). A kelly_fraction of 0.001 to hit $0.37/bet makes the fraction meaningless as a model-calibration parameter.

**Separate T4 portfolio account:** Operational complexity, account management overhead, not compatible with paper trading architecture.

---

## Operator Sign-Off

| Role | Sign-off | Date |
|------|----------|------|
| DS (architecture accepted — stubs pending calibration) | Earl Ignacio | 2026-06-02 |
| DS (T4_BAND_WEIGHT calibrated — stub replaced) | _pending G1 data_ | — |
| DS (T4_EXPECTED_TOTAL_EDGE calibrated — stub replaced) | _pending G1 data_ | — |
