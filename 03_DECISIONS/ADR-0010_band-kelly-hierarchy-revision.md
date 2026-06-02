# ADR-0010 — Band Kelly Fraction Hierarchy Revision

**Status:** ACCEPTED — 2026-06-02  
**Decision makers:** DS (Earl Ignacio)  
**Supersedes:** Kelly fraction values established retroactively via DECISION_LOG.md (2026-05-29 retroactive entry); DECISION_LOG.md SESSION 13 band Kelly direction entry  
**Superseded by:** —  
**Related:** ADR-0004 (model class — LR+Platt; establishes why T1 fraction must account for calibration uncertainty), ADR-0006 (exposure-based risk framework), GG-008 (all-threshold loop misspecification), T-129 (Path B Poisson CDF fix)  
**Note:** ADR-0009 §6 designated the shadow model promotion ADR as "ADR-0010." That designation is advisory — ADRs are numbered sequentially and shadow promotion will be ADR-0011.

---

## Context

### The original hierarchy

The original Kelly fraction schedule (DECISION_LOG.md 2026-05-29 retroactive entry) was:

| Band | Kelly | Rationale |
|------|-------|-----------|
| T1 | 0.25 | Quarter-Kelly; ADR-0004 calibration (ECE 0.0342) validated at G4 |
| T2 | 0.20 | Reduced vs T1; injury/lineup overlay adds uncertainty to T1 estimate |
| T3 | 0.10 | Momentum signal is T1 confirmation only; half of T1 |
| T4 | 0.05 | No historical calibration for live Bayesian model |
| T5 | 0.15 | Higher than T4; near-certainty gate warrants more |

This hierarchy placed T1 as the primary sizing band (0.25) and treated T4/T5 as supplementary (0.05 / 0.15).

### What GG-008 revealed

**GG-008 (registered 2026-06-02)** revealed a structural misspecification in the T1 inference path: `run_paper_trade.py` computes `p_est` once per player from a 78-feature LR model that does not include `kalshi_threshold` as a feature. The same `p_est` is then applied to every Kalshi threshold market for that player, producing phantom edge on thresholds far from the player's scoring mean.

Monte Carlo validation (50k runs, Poisson ground truth): expected P&L **-$528 (-58%)** on the Finals G1 portfolio, 6.4% win rate. Only one of 25 positions (KAT YES 20) showed genuine edge — the threshold where p_est happens to approximate the true Poisson probability.

This means **T1 p_est is a player-level scalar masquerading as a threshold-specific probability.** It is not miscalibrated in the traditional sense — ADR-0004 ECE 0.0342 holds at the mean threshold — it simply lacks the threshold dimension.

### Numerical derivation of Kelly fractions

After Path B, T1 and T4 are both Poisson-based. Signal quality is measured by the standard error of the λ estimate (σ_λ) — the uncertainty in the Poisson rate parameter used to compute p(score ≥ threshold). Lower σ_λ → better signal → higher justified Kelly fraction.

**T1 λ uncertainty (pre-game):**  
T1 uses `pts_l10_mean` as λ. NBA scoring std dev ≈ 6.5 pts/game. L10 rolling average std error = 6.5 / √10 = **2.055 pts**.

**T4 λ uncertainty (in-game):**  
T4 uses `pace × time_remaining` where pace = pts_so_far / elapsed_min. Under Poisson scoring, σ_pace = √(pts_so_far) / elapsed, so σ_λ_T4 = √(pace / elapsed) × remaining.

| Game clock | Elapsed | Remaining | σ_λ_T4 | T4 better than T1? |
|-----------|---------|-----------|--------|---------------------|
| Q1 (6m) | 6 | 42 | 11.07 | No — 5.4× worse |
| Halftime | 24 | 24 | 3.16 | No — 1.5× worse |
| Q3 end | 36 | 12 | 1.29 | Yes — 1.6× better |
| Q4 (42m) | 42 | 6 | 0.60 | Yes — 3.4× better |
| Q4 (46m) | 46 | 2 | 0.19 | Yes — 10.8× better |

**Key finding: T4 is only strictly better than T1 after minute 36 (Q4).** Before then, the in-game λ estimate has higher uncertainty than the pre-game L10 mean. T4_MIN_DELTA_P = 0.08 does not resolve this — early-game signals have high σ_p (~0.28-0.98) so 93% pass the 0.08 filter as noise. The T4=0.20 fraction is justified for **Q4 execution only** (the dominant firing window after the filter).

Clean-signal threshold (SNR ≥ 2, σ_p < 0.04): reached at minute 46 for a 20-pt player. This defines T4's effective firing window for Phase 8 ACTIVE. **EXP-018 must calibrate T4_MIN_DELTA_P by game phase before Phase 8 ACTIVE designation.**

**Variance-scaled Kelly derivation:**  
Using T4 late-Q4 (σ_λ ≈ 0.50 pts) as the reference and k_T4 = 0.20:

```
k_band = k_T4 × (σ_λ_T4_ref / σ_λ_band)
```

| Band | σ_λ | Derived k | Proposed k | Ratio |
|------|-----|-----------|------------|-------|
| T1 | 2.055 | 0.049 | **0.10** | 2.0× premium |
| T2 | ~1.64 (est) | 0.061 | **0.13** | 2.1× premium |
| T3 | n/a | 0.032 | **0.07** | 2.2× premium |
| T4 | 0.50 (ref) | 0.20 | **0.20** | anchor |
| T5 | ~0 | design | **0.25** | certainty gate |

**Why the 2× premiums for T1/T2/T3 over pure variance-scaling:**  
The pure variance ratio gives ~0.05 for T1. The 2× premium to 0.10 is justified by:  
(1) Path B significantly improves T1 vs. the old LR scalar — Poisson CDF per threshold is architecturally correct; 0.049 would undervalue this fix;  
(2) `pts_l10_mean` has non-stationarity uncertainty beyond the L10 std error (trending performance, opponent strength variation, rest effects) that the simple σ formula doesn't capture;  
(3) 0.10 is still a 60% reduction from the original 0.25, which is the appropriate directional move.

**T2 and T3 fractions are tentative.** The T2 derivation assumes injury overlay reduces σ_λ by 20% — unvalidated. T3 assumes momentum = 65% of T1 signal weight — unvalidated. Both require proper derivation before band activation. The 2× premium over the pure ratio is a conservatively high estimate at this stage.

**T5 derivation from certainty gate:**  
At T5_YES_CERTAINTY = 0.85, representative cases:
- p_T5=0.90, market=0.80: f* = 0.60, quarter-Kelly (0.25×) = 0.15 → $150 on $1k bankroll  
- p_T5=0.88, market=0.75: f* = 0.52, quarter-Kelly = 0.13 → $130 on $1k bankroll  

Quarter-Kelly (0.25) applied to T5 is appropriate: the certainty gate (p > 0.85) is the primary risk control; Kelly formula then sizes from there. Actual bankroll exposure per T5 bet = 13-20% at paper scale — within single-event cap.

**Architecturally correct comparison:**

| Band | Signal quality | Threshold-specific? | Calibration basis |
|------|---------------|---------------------|-------------------|
| T1 (Path B) | Poisson, pre-game λ | Yes — after Path B | pts_l10_mean; σ_λ=2.055; non-stationary |
| T4 | Poisson, live game-state λ | Yes | Current pace × t_rem; σ_λ→0 in Q4 |
| T5 | Arithmetic certainty | Yes | Deterministic arithmetic; not probabilistic |

**T4 is strictly better than T1 in Q4 (the dominant T4 firing window).** The existing hierarchy — T1=0.25, T4=0.05 — was inverted at the time when T4 is actually firing. Capital was being allocated proportionally to the inferior signal in the relevant game window.

### Path B and the fix constraint

T-129 (Path B) replaces `p_est` with `Poisson_CDF(threshold, pts_l10_mean)` per-threshold in `run_paper_trade.py`. This corrects GG-008 for the T1/pre-game pipeline. It does **not** change the band Kelly fractions — that requires this ADR.

ADR sequencing invariant (CLAUDE.md): this ADR must be accepted before T-129 code is deployed. T-129 changes which bets fire; this ADR changes how much capital is allocated to each. Both must be consistent at deployment.

---

## Decision

### 1. Revised Kelly fraction schedule

| Band | Old Kelly | New Kelly | Status | Rationale |
|------|-----------|-----------|--------|-----------|
| T1 | 0.25 | **0.10** | ACTIVE | Pre-game seeding; LR model is player-level not threshold-specific (GG-008); higher model uncertainty warrants lower fraction |
| T2 | 0.20 | **0.13** | SKELETON | Injury overlay on T1 LR model; same threshold-specificity limitation; modest premium over T1 for injury information; tentative — **requires DS confirmation before T2 activation** |
| T3 | 0.10 | **0.07** | SKELETON | Momentum signal is T1 confirmation only; below T1; tentative — **requires DS confirmation before T3 activation** |
| T4 | 0.05 | **0.20** | PAPER (this session) | Poisson CDF is threshold-specific by construction; primary in-play signal; game-state grounded; lower uncertainty than T1 for threshold prediction |
| T5 | 0.15 | **0.25** | PAPER (this session) | Near-certain arithmetic; deterministic not probabilistic; highest-certainty classification gates entry; highest sizing warrants highest Kelly |

T2 and T3 fractions are **tentative** — they are listed here for architecture consistency but do not take effect until those bands are activated. The band activation ADR (required before T2/T3 go ACTIVE) must explicitly confirm or revise these fractions with calibration evidence. The 2× premium over the pure variance-scaled derivation (T2: 0.13 vs. derived 0.061; T3: 0.07 vs. derived 0.032) is a working estimate that should be replaced with empirical derivation before activation.

### 2. T4 game-phase constraint

**T4=0.20 applies only when T4 is the higher-quality signal than T1.** Numerical derivation shows T4 σ_λ < T1 σ_λ only after game minute 36 (Q4). Before Q4, T4 has higher λ uncertainty than T1.

**Paper prototype (this session):** No explicit game-phase gate required. At paper scale the downside is bounded. T4 execution will be observed empirically across Finals games.

**Phase 8 ACTIVE gate:** Before T4 is designated ACTIVE (live capital, Phase 8), EXP-018 must calibrate T4_MIN_DELTA_P by game phase. Options include: (a) time-varying MIN_DELTA_P (larger early, smaller late), (b) hard `T4_MIN_ELAPSED_MIN` constant restricting T4 to Q3/Q4, (c) empirical evidence from paper data showing the early-game noise profile. The Phase 8 ACTIVE ADR must include this derivation or explicitly carry this as a known limitation with a bound on capital risk.

### 3. Capital reserve mandate

**Before T1 cron fires (PIPE-03), total open T4/T5 position collateral plus the pending T1 batch must not exceed 60% of starting bankroll.** Equivalently: ≥40% of starting bankroll must remain uncommitted after T1 bets are placed.

Rationale: T4/T5 now carry higher Kelly fractions (0.20 / 0.25). If T1 commits most of the bankroll before game time, in-play execution is capital-constrained at precisely the moment T4/T5 have their highest-quality signal (live game state). The reserve mandate ensures T4/T5 have capital to act.

Implementation note: at paper trading scale ($1,000), 40% reserve = $400 floor. With T1 Kelly now at 0.10 and typical 15–25 bets/night at paper scale, T1 batch exposure is well below the 60% ceiling. The reserve mandate is primarily a production safeguard — it will bind more often at live capital scale where T4/T5 exposure is larger. The check must be implemented in the risk engine before live capital (G6 gate).

For the current paper prototype: **implement the reserve mandate as a logged warning only.** If T1 batch would exceed 60%, log `RESERVE_MANDATE_WARNING` to C6 with the overage amount. Do not block T1 bets at paper scale — we need G6 evidence accumulation. Block T1 bets at live capital scale (to be enforced via ADR before G6 capital release).

### 3. DEFAULT_KELLY_FRACTION unchanged

`DEFAULT_KELLY_FRACTION = 0.25` in `risk.py` is used as the fallback for any position not dispatched from a band-aware execution path. It remains 0.25 — this is a safety boundary, not a band-specific constant. Band-specific fractions are passed explicitly by the execution pipelines.

---

## Options Considered

| Option | Description | Decision |
|--------|-------------|----------|
| **A — Invert T1/T4 hierarchy (chosen)** | T1=0.10, T4=0.20, T5=0.25; reserve mandate. Matches signal quality ordering. | ACCEPTED |
| B — Keep original hierarchy | Maintain T1=0.25, T4=0.05. Run Path B under old fractions. | Rejected — hierarchy is architecturally inverted now that GG-008 establishes T1 is not threshold-specific. Higher Kelly on the worse signal is indefensible. |
| C — Equal fractions across T1/T4/T5 | Set all to 0.15 as a neutral middle ground. | Rejected — flattens the signal-quality distinction; T5 arithmetic certainty warrants more than T1 probabilistic; T4 Poisson is demonstrably better than T1 for threshold markets. |
| D — Full Kelly recalibration experiment before changing fractions | Run EXP against real Finals data before committing to new fractions. | Rejected — we have no live T4/T5 data yet; the hierarchy change is theoretically motivated by GG-008, not empirically; EXP-018/019 are queued for dark period calibration. The T4/T5 fractions adopted here (0.20/0.25) are conservative enough that paper-scale risk is bounded. |

---

## Consequences

### Positive
- Kelly allocation now proportional to signal quality. Higher fraction on threshold-specific Poisson (T4) than player-level LR (T1).
- T5 arithmetic certainty correctly receives the highest fraction — the certainty gate is the primary risk control, and it already gates entry conservatively.
- Reserve mandate prevents T1 from crowding out T4/T5 capital at live scale.

### Negative / Trade-offs
- T1 Kelly drops from 0.25 to 0.10 — pre-game position sizes are smaller by 60%. Numerically, T1=0.10 is a 2× premium over the pure variance-derived 0.049 — on the conservative-high side because Path B is a meaningful improvement the pure ratio undervalues.
- T4=0.20 is justified for Q3/Q4 execution but numerically oversizes early-game (Q1/Q2) signals where σ_λ_T4 is 1.5–5× higher than σ_λ_T1. Mitigated at paper scale; requires EXP-018 before Phase 8 ACTIVE.
- T2/T3 fractions (0.13 / 0.07) are approximately 2× the variance-derived values (0.061 / 0.032). These bands are skeleton and inactive — the premiums are working estimates only and must be replaced with empirical derivation before activation.
- GG-007 (T4_MIN_DELTA_P and T5 certainty thresholds uncalibrated) remains OPEN. Higher T4/T5 Kelly combined with uncalibrated thresholds is a compounding risk — mitigated by (a) paper-only scope and (b) EXP-018/019 required before Phase 8 ACTIVE designation.

### Neutral
- Fundamental Kelly formula (C4 risk engine) unchanged. Only fraction values change.
- Max single-event exposure cap ($500) unchanged. Kelly output is capped before this limit regardless of band.
- G6 evidence gate (APR-0017) is based on resolved bets and slope metrics, not bet size — fraction change does not alter the gate criteria.

---

## Code Changes Required

This ADR authorizes the following code changes. **No changes may be made until DS sign-off.**

| File | Change | Notes |
|------|--------|-------|
| `src/prediction_market_bot/execution_bands.py` | T1 kelly_fraction: 0.25 → 0.10; T2: 0.20 → 0.13; T3: 0.10 → 0.07; module docstring updated | T2/T3 are skeleton — changes update constants only |
| `src/prediction_market_bot/c3_forecasting/game_state_model.py` | KELLY_T4: 0.05 → 0.20; KELLY_T5: 0.15 → 0.25; module docstring updated | |
| `src/prediction_market_bot/c4_risk_engine/risk.py` | Add reserve mandate check — `RESERVE_MANDATE_PCT = 0.40`; at PIPE-03 time log `RESERVE_MANDATE_WARNING` if T1 batch would exceed (1 - RESERVE_MANDATE_PCT) of bankroll; do NOT block at paper scale | `DEFAULT_KELLY_FRACTION` stays at 0.25 |
| EXECUTION_BANDS.md | Update band table with new fractions | Documentation |

---

## Implementation

| Task | Description | Status |
|------|-------------|--------|
| ADR-0010 sign-off | DS accepts this document | **PENDING — required before any code change** |
| T-129 code change | Execute fraction updates in execution_bands.py + game_state_model.py after sign-off | This session (after sign-off) |
| Reserve mandate | Add `RESERVE_MANDATE_PCT` check to risk.py (warning-only at paper scale) | This session |
| T2/T3 confirmation | ADR confirms or revises T2/T3 fractions with calibration evidence | Before T2/T3 activation (dark period or Phase 8) |

---

## Sign-off

**DS (Earl Ignacio):** Earl Ignacio — ACCEPTED Date: 2026-06-02

_This document is now immutable. Changes require a superseding ADR._
