# ADR-0014 — Per-Band Decision Tree Mechanics: T1–T5 Quantitative Specification

**Status:** ACCEPTED  
**Date:** 2026-06-03 SESSION 23  
**Decisions logged:** true  
**Author:** Claude Code (T-130)  
**Approval required:** DS (Earl Ignacio) sign-off before this document is ACCEPTED  
**Supersedes:** Scatter of decision-tree detail across ADR-0010, ADR-0013, execution_bands.py, game_state_model.py, execution_bands_orchestrator.py  
**Supplements:** ADR-0010 (Kelly fractions), ADR-0013 (T4 band budget), ADR-0011 (Phase 8 paper scope)  
**Related:** GG-007 (T4_MIN_DELTA_P uncalibrated), GG-009 (taker fee not in edge), T-131 (fee-adjusted edge ADR)

---

## Context

T-130 mandates: formally specify the quantitative computation per execution band. What model inputs feed the decision. What method generates the probability estimate. What sizing rule applies (Kelly / flat / arithmetic). What kill switch tier governs the band.

This information has been implemented incrementally across six separate files and is not consolidated in any single document. Before T4 ACTIVE designation and before G6, a single authoritative decision record must exist. This ADR is that record.

**Scope:** T1 through T5. Each band is specified at its current activation status. SKELETON bands are specified as designed — their mechanics are documented here to prevent drift during the dark period. "Tentative" callouts flag where DS confirmation is required before activation.

---

## Decision: Per-Band Decision Trees

### T1 — Kelly on Deployable Capital (ACTIVE)

**Activation status:** ACTIVE (paper trading)

**Model inputs:**
- `pts_l10_mean` — 10-game rolling scoring mean for the player (primary λ estimate)
- `rest_days` — days since last game
- `home_away` — binary home court indicator
- Full 78-feature LR+Platt feature vector (ADR-0004)
- `kalshi_threshold` — the specific points threshold being evaluated (required by Path B, T-129)

**Probability estimation method:**
Poisson CDF per threshold: `p_T1 = Poisson.CDF(threshold, pts_l10_mean)` (Path B, T-129).
This is threshold-specific — a separate p_T1 is computed for each Kalshi market threshold for a given player. The old method (single player-level scalar applied to all thresholds) was superseded by T-129 per GG-008.

**Edge computation:**
`edge = p_T1 - market_implied_probability(mip) - vig_allowance`

Edge gate: `edge ≥ MIN_EDGE_TO_APPROVE = 0.02` (pre-fee; see GG-009 / T-131 for fee correction obligation before G6).

**Sizing rule:** Kelly on deployable capital.
```
deployable_capital = bankroll × (1 - RESERVE_MANDATE_PCT=0.40)
bet_size = edge × T1_KELLY=0.10 × deployable_capital
```
Cap: `min(bet_size, max_single_event_exposure_usd=$500.00)`

**Kill switch tier:** System-level only.
- `MAX_DAILY_LOSS_PCT=0.15` — daily loss exceeds 15% of initial bankroll → KILL_SWITCH all bands
- `max_drawdown_pct=0.20` — realized drawdown exceeds 20% → KILL_SWITCH all bands
- No band-level budget constraint for T1.

**Reserve mandate:** After T1 batch places all bets, ≥40% of starting bankroll must remain uncommitted. At paper scale: log `RESERVE_MANDATE_WARNING` if violated (non-blocking). At live capital scale: block T1 bets (enforced before G6 capital release per ADR-0010 §3).

---

### T2 — Kelly on Deployable Capital (SKELETON — tentative fractions)

**Activation status:** SKELETON. BLOCKED on DS-04 (injury data source, T-075).

**Model inputs:**
- T1 cached output (p_T1 per player/threshold) — T2 does not re-run LR model
- Injury/lineup overlay from DS-04 (not yet sourced — this is the blocking dependency)
- `injury_overlay_adjustment` — Δp applied to T1 estimate based on player availability

**Probability estimation method:**
T1 probability plus injury adjustment: `p_T2 = p_T1 ± Δp_injury`
Δp_injury formula: TBD — requires DS-04 data and derivation methodology before T2 activation. Currently `injury_overlay = "not_applied"` (run_t2_sameday.py:130 stub).

**Edge computation:** Same formula as T1 applied to p_T2.

**Sizing rule:** Kelly on deployable capital.
```
bet_size = edge × T2_KELLY=0.13 × deployable_capital
```
Same cap as T1.

**⚠ TENTATIVE:** T2_KELLY=0.13 is tentative per ADR-0010. Derivation: 2.1× premium over the variance-scaled ratio (derived 0.061). This premium is a working estimate — unvalidated injury overlay uncertainty. The band activation ADR (required before T2 goes ACTIVE) must confirm or revise this fraction with calibration evidence from DS-04 data.

**Kill switch tier:** System-level only (no band-level budget).

---

### T3 — Conditional Kelly, CONFIRM/FADE/NEUTRAL overlay (SKELETON — tentative fractions)

**Activation status:** SKELETON. Can run on cron (no real-time infra required) but has not been activated.

**Architectural role:** T3 is NOT an independent bet source. It is a momentum overlay on T1/T2. T3 cannot fire without an active T1 (or T2) signal — it either confirms, fades, or is neutral on the pre-existing direction.

**Model inputs:**
- Cached T1/T2 forecast: direction, edge, p_T1/T2, mip at T1/T2 fire time
- Current live market price: `current_mip` at pre-tip scan time
- Momentum signal: `Δprice = current_mip - t1_mip` (price drift direction vs. model direction)

**Signal computation:**
- `CONFIRM`: price drift agrees with model direction (market moved toward model)
- `FADE`: price drift disagrees with model direction (market moved against model)
- `NEUTRAL`: price drift below significance threshold or indeterminate

**Probability estimation method:**
T3 does NOT re-estimate p. It reads T1/T2 probability and uses price drift as a confidence modifier. T3 `edge` = edge recalculated against current_mip (same p_T1/T2, updated market price).

**Sizing rule (multi-band interaction — execution_bands_orchestrator.py):**
```
min_kelly = min(kelly_fractions of all active bands)
```
- T3 CONFIRM + T1/T2 actionable → PROCEED; `final_kelly = min_kelly`; `final_edge = t3.edge`
- T3 FADE + T1/T2 actionable → HOLD (no bet placed; wait for next 15-min scan cycle)
- T3 NEUTRAL + T1/T2 actionable → PROCEED; `final_kelly = governing_band_kelly` (T2 or T1)

In practice with only T1 active: min_kelly = min(T1=0.10, T3=0.07) = 0.07 on T3 CONFIRM.

**Q1 DECIDED — DS 2026-06-03 SESSION 23: Option X (no multiplier). Current code is correct.**

Regression test (`scripts/run_t3_multiplier_regression.py`) run before sign-off. Findings:
- T3 bets at KELLY_T3=0.07 represent 2–4% of the Kelly-optimal fraction across all tested scenarios (p_model 0.52–0.62, c 0.48–0.54). The 1.0–1.30 multiplier range covers <5% of the full-Kelly optimal in every scenario.
- Kelly-optimal multiplier for these parameter combinations is 3–6× — far outside the tested range and far outside the current design's 0.07 fraction.
- Growth rate delta at true_bonus=0 is positive for any m>1 only because the system is operating far below full Kelly — not a signal that a multiplier adds genuine signal value. The 1.15× figure from DECISION_LOG 2026-05-29 retroactive has no derivation basis.
- **Correct implementation:** No multiplier. Current orchestrator code (`final_edge = t3.edge`, no adjustment) is correct. Revisit when ≥50 T3 CONFIRM paper events are available to estimate empirical true_bonus distribution.

**⚠ TENTATIVE:** T3_KELLY=0.07 is tentative per ADR-0010 (2.2× premium over derived 0.032). Requires DS confirmation before T3 activation.

**Kill switch tier:** System-level only.

---

### T4 — Flat for Paper / Kelly on Band Budget for Live (PAPER VALIDATION)

**Activation status:** PAPER VALIDATION. `PAPER_T4_VIRTUAL=false, PAPER_T4_FLAT_SIZING=true` as of 2026-06-03 SESSION 22. Real bets are placed; sizing is flat to decouple execution count from capital.

**Model inputs:**
- ESPN API boxscore (45s polling, `site.api.espn.com`): `period`, `displayClock`, `player.points` for all tracked players
- Pre-staged T1 forecast: `p_T1`, `mip_T1`, `direction` per player/threshold
- Derived: `λ_live = pace × time_remaining` where `pace = pts_so_far / elapsed_min`

**Probability estimation method:**
Bayesian Poisson update:
```
p_T4 = Poisson.CDF(threshold, λ_live)
```
where `λ_live = pace × time_remaining_min`

**Gate:** `|p_T4 - p_T1| ≥ T4_MIN_DELTA_P = 0.08`
T4 only fires when the live game state moves the probability at least 8 percentage points from the pre-game estimate. Calibration of T4_MIN_DELTA_P is required by EXP-018 before T4 ACTIVE designation (currently STUB quality per GG-007).

**Signal quality constraint (ADR-0010):**
T4 λ uncertainty (σ_λ) only drops below T1's σ_λ=2.055 after game minute 36 (Q4). Before Q4, T4 has higher λ uncertainty than T1. At paper scale this is acceptable. Phase 8 ACTIVE gate requires EXP-018 to calibrate T4_MIN_DELTA_P by game phase (time-varying threshold or hard `T4_MIN_ELAPSED_MIN` constant).

**Sizing rule:**

*Paper mode (current — `PAPER_T4_FLAT_SIZING=true`):*
```
bet_size = 1 contract at MIP price (Kalshi minimum $0.01)
```
Purpose: validate execution layer independently of capital sizing. Decouples throughput measurement from Kelly formula.

*Live mode (when `PAPER_T4_FLAT_SIZING=false` — not yet active):*
```
t4_band_budget = bankroll × (1 - RESERVE_MANDATE_PCT=0.40) × T4_BAND_WEIGHT=0.10 [STUB]
bet_size = edge × KELLY_T4=0.20 × t4_band_budget
```
Cap: `min(bet_size, max_single_event_exposure_usd=$500.00)`

T4_BAND_WEIGHT=0.10 is a stub. Calibration procedure: extract total VIRTUAL would-be deployment from `logs/t4_live.log` after G1; derive T4_BAND_WEIGHT = target_max_exposure / (bankroll × 0.60). Operator sign-off required before replacing stub (ADR-0013).

**Kill switch tier:** Two-tier.
1. Band-level: `t4_deployed_game ≥ t4_band_budget` → T4 stops placing bets; evaluation continues; reset per game night.
2. System-level: MAX_DAILY_LOSS_PCT + max_drawdown_pct as above.

In `PAPER_T4_FLAT_SIZING=true` mode: the $500 pool (`PAPER_T4_POOL_USD`) is the paper-mode band limit.

**T4 ACTIVE gates (all required before `PAPER_T4_FLAT_SIZING=false`):
1. T4_BAND_WEIGHT calibrated from G1 data (stub replaced, derivation logged, DS sign-off)
2. T4_EXPECTED_TOTAL_EDGE calibrated from G1 data
3. EXP-018 — T4_MIN_DELTA_P calibration by game phase
4. DS-02 ADR — ESPN API formally named as T4 data source (superseding ADR-0011's NBA CDN reference)

---

### T5 — Kelly on Band Budget, Arithmetic Certainty Gate (SKELETON)

**Activation status:** SKELETON. Phase 8+. Code exists in `game_state_model.py` and `run_t4_live.py` but does not place bets at paper validation scale.

**Model inputs:**
- Same ESPN feed as T4 (shared poll cycle)
- `time_remaining_min` — game clock converted to decimal minutes
- `pts_so_far` — current player points in game
- `threshold` — the Kalshi threshold being evaluated
- `pts_needed = threshold - pts_so_far` — arithmetic points remaining to cross threshold

**Probability estimation method:**
**Arithmetic certainty — NOT probabilistic.** T5 does not compute a Poisson CDF. It evaluates a deterministic condition:

```
if pts_needed ≤ 0 AND time_remaining_min ≤ T5_TIME_THRESHOLD_MIN=3.0:
    # Player already crossed threshold — YES is near-certain
    p_T5 = T5_YES_CERTAINTY = 0.85

if pts_needed > pace_required_to_cross AND time_remaining_min ≤ T5_TIME_THRESHOLD_MIN=3.0:
    # Arithmetic says player cannot reach threshold — NO is near-certain
    p_T5 = 1 - T5_NO_CERTAINTY = 0.15  (i.e., 85% confidence in NO)
```

Where `pace_required_to_cross` is derived from current game pace and time remaining. If neither condition is met, T5 does NOT fire (no NEUTRAL action — T5 is binary or silent).

T5_YES_CERTAINTY=0.85 and T5_NO_CERTAINTY=0.85 are calibration constants grounded by Poisson arithmetic (SESSION 14). EXP-019 is required before T5 ACTIVE to validate these thresholds against historical Q4 ≤3 min game-state data (GG-007 item 2).

**Sizing rule:** Kelly on band budget.
```
bet_size = edge × KELLY_T5=0.25 × t4_band_budget
```
KELLY_T5=0.25 is justified because the arithmetic certainty gate (p ≥ 0.85) is the primary risk control — Kelly then sizes from a high-confidence starting point.

**Band budget architecture (Q2 DECIDED — DS 2026-06-03):**
Shared budget is design intent, not a fallback. Bands are bucket filters with independent kill switches and specific validity math. No dedicated per-band budget allocation. If T5 is starved by T4 depletion, the root cause is T4_MIN_DELTA_P miscalibration (T4 firing too aggressively on low-quality early-game signals) — fix EXP-018, not the budget architecture. GG-010 registered and resolved on this basis.

**Kill switch tier:** Band-level kill switch (budget exhaustion, per game) + system-level kill switches. T4 and T5 share the in-play band budget (`t4_band_budget`). The kill switch halts in-play execution when the budget is exhausted; both bands stop.

**T5 ACTIVE gates (all required before T5 ACTIVE):**
1. T4 ACTIVE (T5 requires T4's infrastructure)
2. EXP-019 — T5_YES_CERTAINTY / T5_NO_CERTAINTY calibration against historical Q4 data

---

## Summary Table

| Band | Status | P Method | Sizing Rule | Kill Switch Tier | Open Questions |
|------|--------|----------|-------------|------------------|----------------|
| T1 | ACTIVE | Poisson CDF(threshold, pts_l10_mean) | Kelly × 0.10 × deployable_capital | System-level | GG-009 fee correction (T-131) |
| T2 | SKELETON | T1 p ± injury Δp | Kelly × 0.13 × deployable_capital | System-level | DS-04 not sourced (T-075); fractions tentative |
| T3 | SKELETON | T1/T2 p, price drift as modifier | min(0.07, active_band_kelly) × deployable_capital | System-level | Fractions tentative; revisit with ≥50 CONFIRM events |
| T4 | PAPER VALIDATION | Poisson CDF(threshold, pace×t_rem) | FLAT 1-contract (paper); Kelly × 0.20 × band_budget (live) | Band + system | EXP-018 (T4_MIN_DELTA_P); T4_BAND_WEIGHT stub (G1 calibration) |
| T5 | SKELETON | Arithmetic certainty gate | Kelly × 0.25 × shared band_budget | Band (shared T4) + system | EXP-019; GG-007 |

---

## Open Questions — RESOLVED

### Q1: T3 CONFIRM edge multiplier — RESOLVED 2026-06-03

Option X (no multiplier). Regression test confirms 1.15× is arbitrary; revisit at ≥50 CONFIRM events. See T3 section above for full derivation summary.

### Q2: T5 band budget architecture — RESOLVED 2026-06-03

Option A (shared budget). DS decision: no dedicated band budgets by design. Kill switches + validity math are the mechanism. See T5 section above.

---

## Governance Actions Triggered by This ADR

1. **GG-010 (T5 budget) registered and RESOLVED** — DS decision 2026-06-03: shared budget is design intent; no architectural change needed.
2. **T2 and T3 fractions remain tentative** — flagged here; require DS confirmation at activation ADR
3. **T-131 ADR (fee-adjusted edge)** — affects T1/T4 MIN_EDGE gate; must complete before G6 EXP-017 re-run
4. **GG-009 resolution** — all per-band edge computations above assume gross edge; net edge after taker fee = gross_edge - 0.07×P×(1−P). At P=0.50, fee=0.0175 = 87% of MIN_EDGE. This ADR's edge gate numbers are gross; T-131 corrects them.

---

## Implementation

This ADR is documentation only. No code changes are required. All mechanics described here are already implemented (T1/T4/T5) or are SKELETON (T2/T3). This document consolidates them into a single authoritative record.

Code changes triggered indirectly:
- Q1 (T3 multiplier): No code change required. Current orchestrator code is correct.
- Q2 (T5 budget): No code change required. Current shared-budget design is correct.
- When T-131 is resolved: update edge gate thresholds across all bands.

---

## Operator Sign-Off

| Role | Decision | Sign-off | Date |
|------|----------|----------|------|
| DS — T3 CONFIRM multiplier (Q1) | Option X — no multiplier; current code correct; regression test conducted | Earl Ignacio | 2026-06-03 |
| DS — T5 band budget architecture (Q2) | Option A — shared budget is design intent; no dedicated band budgets | Earl Ignacio | 2026-06-03 |
| DS — Full ADR acceptance | ACCEPTED | Earl Ignacio | 2026-06-03 |
