# ADR-0028 — Segmented Per-Band Promotion Thresholds

**Status:** ACCEPTED — DS sign-off 2026-06-22  
**Amends:** APR-0017 (G6 Multi-Dimensional Evidence Standard, 2026-06-01) + APR-0019 (Per-Bucket Evidence Amendment, 2026-06-09)  
**Does NOT supersede:** APR-0017 or APR-0019 in full. Both remain operative in all sections not explicitly modified below.  
**Registered by:** T-148 (DECISION_LOG 2026-06-22 SESSION 65)  
**Analysis input:** T-148 regression analysis (DECISION_LOG 2026-06-09 SESSION 43); T-153 fill-realism haircut (DECISION_LOG 2026-06-12 SESSION 59); GG-022 (partially resolved — APR-0017 amendment deferred)  
**Drafted:** 2026-06-22 SESSION 65  
**Effective:** Upon DS sign-off; applies to all G6 evidence collected under APR-0017 / APR-0019

---

## Why This Amendment Is Required

### Gap 1 — Fill-realism adjustment never mandated in Tier 2 criteria (GG-022, OPEN)

APR-0017 Tier 2 criteria (T2-B: Rolling EV > 0; T2-D: P&L slope > 0) evaluate nominal paper P&L. Nominal paper P&L assumes fills at `mid ± vig/2`. Real taker fills occur at `mid ± spread/2`, where `spread > vig`.

T-153 measured fill-realism impact on G1–G4 data (n=5,166 Kalshi observations):
- T1 + T4 combined haircut: **−$86.31 (p50)** / −$135.81 (mean) on $3,274.20 staked  
- Haircut as % staked: **2.64% (p50)** / 4.15% (mean)  
- GG-022 verdict: **HIGH materiality**

G6 is a live-capital promotion decision. A system that is EV-positive on paper fills but EV-negative after realistic fill costs is not commercially viable. APR-0017's T2-B and T2-D criteria as written evaluate the wrong quantity for live capital deployment.

The T-153 decision log (2026-06-12 SESSION 59) explicitly noted: "APR-0017 amendment still required (DS ruling needed) before G6 Tier 2 thresholds can be recalibrated to haircut-adjusted P&L." GG-022 remained PARTIALLY RESOLVED pending this amendment. **This ADR resolves GG-022 in full.**

### Gap 2 — T4 Tier 2 thresholds implicit, not formally derived

APR-0019 established per-bucket independence and per-bucket calibration floors (T1 ≥66, T4 ≥50). The G6 gate checklist (T-172) carried T4 Tier 2 thresholds (T2-A ≤ 20pp, T2-C ≤ 0.265) derived from the checklist author's judgment, not from a formal ADR derivation.

T4 uses a live Bayesian GameStateModel with no validated ECE or Brier baseline. Inheriting T1's numeric thresholds without derivation from T4's own properties violates the APR-0017 design principle: every pass/fail criterion must be derived from what it is actually measuring.

Additionally, T4 has a two-leg fill structure (entry ask + exit bid) with a higher per-bet fill cost than T1's one-leg entry. T2-B (EV > 0) and T2-D (P&L slope > 0) applied to T4 must use T4's two-leg haircut, not T1's one-leg formula.

### Gap 3 — No aggregate portfolio P&L/capital goal

APR-0017 + APR-0019 require each active bucket to pass Tier 2 independently. There is no single portfolio-level criterion. This is insufficient for promotion decisions for two reasons:

1. **Volume asymmetry**: T1 produces ~13 bets/game (Finals) vs T4's ~1,000 bets/game. At design throughput, T4 dominates portfolio capital deployed. A T4 EV slightly above zero at a barely-adequate sample could be statistical noise. Per-bucket Tier 2 does not detect whether the portfolio as a whole is generating expected value.

2. **Fill cost interaction**: T1 and T4 have different fill cost structures and different bet volumes. Their individual post-haircut EVs do not sum simply to a portfolio EV. An aggregate criterion directly measures what G6 is actually deciding: does deploying capital across all active bands generate a positive expected return?

The 2026-06-12 DS ruling (DECISION_LOG SESSION 56c) explicitly required "one aggregate P&L/capital goal at portfolio level" as a G6 gate. APR-0017 + APR-0019 provide no such criterion.

---

## Design Principle (inherited from APR-0017)

Every pass/fail criterion must be a rate, a slope, or a proportion. Counts appear only as derived minimums for statistical power, with derivation shown.

**Additional principle added by this ADR:** Every criterion that measures P&L or EV must specify whether it uses nominal paper P&L or fill-realism-adjusted P&L, with explicit justification. Silence on this question is not permitted.

---

## Modifications to APR-0017 / APR-0019

### Modification 5 — Fill-realism mandate for Tier 2 evaluation (resolves GG-022)

**Supersedes:** APR-0017 § Tier 2 header's implicit nominal-P&L assumption.

**New rule:**

> **Tier 2 criteria that measure P&L, EV, or cumulative returns — specifically T2-B (EV) and T2-D (P&L slope) in all active buckets — evaluate fill-realism-adjusted figures, not nominal paper P&L. Fill-realism adjustment uses the T-153 methodology at p50 central estimate.**

**Derivation:** G6 authorizes live capital deployment. The commercial question is whether the system generates positive expected value under live execution conditions. Live fills incur real bid-ask spread costs. Paper fills at `mid ± vig/2` understate the actual cost of execution. The p50 estimate is the central estimate — it neither assumes best-case (maker fills, zero spread) nor worst-case (mean spread). T1 caveat: resting T1 orders may execute as maker fills (zero spread cost); the T-153 p50 haircut is therefore an upper bound on T1 fill costs and a conservative pass condition. This is the correct direction: if a system passes T2-B at the conservative p50 haircut, it meets the EV bar under realistic assumptions.

**Fill-realism haircut formulas (from T-153 methodology):**

T1 one-leg entry (taker fill):
```
haircut_per_win = size × (spread_bucket(mid) / 2 − vig / 2)
```
where `spread_bucket(mid)` is the p50 spread from T-153's three-bucket model:
- mid < 0.30: p50 spread = (derived from G4 observations)
- mid 0.30–0.70: p50 spread = (derived from G4 observations)  
- mid > 0.70: p50 spread = (derived from G4 observations)

The exact bucket values are sourced from `scripts/run_t153_haircut.py` and re-derived at each G6 evaluation from the available spread data (requires ≥ 1,000 observations per bucket for stability). Do not hardcode bucket values — re-derive.

T4 two-leg exit (entry ask + exit bid):
```
haircut_two_leg = entry_mid × (spread_bucket(entry_mid) / 2) + exit_mip × (spread_bucket(exit_mip) / 2)
```

**Application:** Run `scripts/run_t153_haircut.py` on the complete G6 paper period data immediately before APR-0008 is drafted. The haircut output from that run is authoritative for G6 Tier 2 T2-B and T2-D evaluation.

**What does NOT change:** T2-A (calibration deviation — based on predicted vs realized win rates, not P&L) and T2-C (Brier score) are not P&L metrics and are unaffected by this modification.

---

### Modification 6 — T4 Tier 2 thresholds — formal derivation

**Supersedes:** The implicit T4 Tier 2 threshold values in G6_GATE_CHECKLIST.md that were unanchored to a formal derivation.

**Derivation basis:** T4 uses a live Bayesian GameStateModel. Properties:
- No validated ECE baseline (unlike T1's 0.0247 from ADR-0004)
- Live inference under partial information (score updates during game)
- Observed win rate in G3: 51.4% (n=1,115) — closer to null than T1's expected 60%
- Two-leg exit structure with higher per-bet fill cost than T1

**T4 Tier 2 criteria (formally derived):**

#### T2-A (T4): Calibration deviation ≤ 20pp, slope ≤ 0
*Unchanged from APR-0019 — included here for completeness of formal derivation record.*

**Derivation:** T1's T2-A tolerance = 15pp = 6× TEST ECE (0.0247). T4 has no TEST ECE baseline. Conservative multiplier: use 8× a proxy ECE. Without a validated ECE, use the monitored L1 drift threshold (0.265 Brier, see T2-C below) to bound the implied ECE via ECE ≤ Brier. At Brier = 0.265, worst-case ECE (perfectly-binned but miscalibrated) ≈ 0.265. 8× is too loose; instead anchor at: T4 operates at near-null win rate (51.4% vs expected 60%), suggesting wider inherent variance. Set tolerance at T1_tolerance × (T1_expected_win_variance / T4_expected_win_variance)^0.5 = 15pp × (0.60×0.40 / 0.514×0.486)^0.5 ≈ 15pp × 1.04 ≈ 16pp. Round up generously to **20pp** to account for live-inference noise and absent ECE baseline. Slope criterion (≤ 0) is derivation-independent: calibration must not be worsening.

#### T2-B (T4): Fill-realism-adjusted rolling EV > 0, slope ≥ 0

**Level threshold derivation:** The level criterion is EV > 0 after T4's two-leg haircut. The EV threshold of 0 is non-arbitrary: it is the commercial validity floor. A system with EV ≤ 0 post-haircut loses money in expectation under realistic execution conditions. The threshold is not raised above 0 because T4 flat-sizing (1 contract/bet) already operates at minimal nominal size; a thin positive post-haircut EV confirms edge exists even after execution costs.

**Slope criterion:** Same derivation as T1 T2-B: slope ≥ 0 (non-deteriorating) is the minimum. A system whose post-haircut EV is positive but declining toward zero across game nights is a system losing its edge over time — this is the broken-system case that APR-0016 missed.

**Application:** T4's two-leg haircut formula (Modification 5) applies. Eligible bets only (APR-0019 Modification 3 definition applies equally to T4).

#### T2-C (T4): Brier ≤ 0.265, slope ≤ 0

**Level threshold derivation:** T4 has no TEST-set Brier baseline analogous to T1's 0.2480. The monitoring L1 threshold (0.265) is the appropriate ceiling for two reasons: (1) L1 is calibrated as the first alert level for the monitoring system — a model that has drifted enough to trigger L1 alert is a model that should not proceed to G6; (2) 0.265 is conservative relative to T1's TEST Brier (0.2480) but is the right anchor when no TEST baseline exists for the production model. The ceiling is applied identically to T4 as to T1 — if the L1 threshold is appropriate as a model health guard for T1, it applies equally to T4's live inference.

**Slope criterion:** Brier slope ≤ 0 (non-increasing). Same derivation as T1 T2-C: each game night's T4 predictions should not be getting worse.

#### T2-D (T4): Fill-realism-adjusted P&L slope > 0

**Derivation:** Positive slope of the cumulative post-haircut T4 P&L over game nights is the direct measure of whether T4 generates value over time. The threshold of > 0 is non-arbitrary — anything ≤ 0 means T4's expected P&L per game night is zero or negative, which is the definition of a system that should not receive live capital. The two-leg haircut formula applies.

**Statistical floor for T4 slope criterion:** ≥ 5 game nights (explicitly derived here — see Modification 7).

---

### Modification 7 — Minimum game nights: explicit for T4

**Adds to:** APR-0019, as a clarification of the game-night floor.

**New rule:**

> The ≥ 5 game night floor (APR-0017 § Statistical Validity Floor, "Minimum game nights: 5") applies equally to T4 slope criteria (T2-A slope, T2-B slope, T2-D slope, and T3-B drawdown slope for the T4 pool). T4 slope criteria cannot be evaluated with fewer than 5 game nights of T4-resolved data, for the same df ≥ 3 reason as T1.

**Derivation:** T4 slope criteria (T2-A, T2-B, T2-D, T3-B) all use linear regression on (game_night_index, metric_value). Slope t-test requires df = n − 2 ≥ 3, meaning n ≥ 5 data points. This is identical to T1's derivation. APR-0019 did not explicitly state the floor for T4; this modification closes the gap.

**Implication:** Even though T4's bet-count floor (≥ 50) is trivially met in one game, the slope-based Tier 2 criteria for T4 require ≥ 5 game nights of resolved data. Both floors must be met simultaneously.

---

### Modification 8 — Aggregate portfolio P&L/capital goal (T-AGG)

**Adds to:** APR-0017 § Tier 2, as a new portfolio-level criterion evaluated after all per-bucket criteria pass.

**New criterion: T-AGG — Aggregate Portfolio EV (Portfolio Level)**

This criterion is evaluated AFTER all per-bucket Tier 2 and Tier 3 criteria pass. It is a necessary additional condition — per-bucket Tier 2 passing is not sufficient for T-AGG; T-AGG is evaluated independently.

#### T-AGG-A — Portfolio EV Level

**Pass condition:** Combined fill-realism-adjusted EV per dollar staked across **all active bands** > 0 at G6 evaluation.

**Metric:** `portfolio_EV = Σ_bands (post_haircut_P&L) / Σ_bands (total_staked)`

- Numerator: sum of T-153-adjusted P&L across all resolved positions in all active bands (T1 + T4, and any other bands active at G6)
- Denominator: sum of all amounts staked across all active bands
- Eligible positions only (APR-0019 Modification 3 ineligibility rules apply)

**Derivation of level threshold (> 0):** The aggregate EV must be positive after fill costs. This is the commercial case for deploying live capital: the portfolio as a whole makes money in expectation. The threshold cannot be set higher without a structural derivation, and setting it at 0 is the minimum non-trivial bar. Setting it lower than 0 would permit a loss-generating portfolio to proceed to live capital — this would violate G6's purpose.

**Why per-bucket passing is not sufficient:** If T1 has EV = +$0.05/bet at 13 bets/game and T4 has EV = +$0.001/bet at 1,000 bets/game, and the combined portfolio's T4-dominated aggregate EV after haircut is −$0.002/bet, the portfolio loses money in expectation even though both buckets pass their individual criteria. T-AGG catches this scenario. Conversely, if T4 barely passes its individual T2-B (EV = +$0.001/bet post-haircut) but this implies a portfolio EV < 0 given T1's smaller positive contribution, T-AGG fails and G6 is blocked.

#### T-AGG-B — Aggregate P&L Slope

**Pass condition:** Slope of the cumulative aggregate post-haircut P&L curve over game nights > 0 (linear regression; requires ≥ 5 game nights).

**Derivation:** Same logic as T1's T2-D: a positive net-positive P&L achieved by early lucky bets is not sufficient. The system must demonstrate that each game night, in expectation, the portfolio gains. A negative or zero aggregate slope means the portfolio is not generating value over time.

**Metric construction:** At each game night index n, compute cumulative aggregate post-haircut P&L = Σ over all bands of T-153-adjusted P&L for all eligible positions resolved through night n. Fit a linear regression on (n, cumulative_P&L). The slope coefficient must be > 0.

---

### Modification 9 — YES-only gate interaction with T1 Tier 2

**Adds to:** APR-0019 § Direction-Specific Evidence (monitoring note), as a clarification.

**New rule:**

> As of 2026-06-12 (DS ruling, SESSION 56c), the YES-only diagnostic gate (`PAPER_YES_ONLY`) is active for T1 PIPE-03 runs as a continuous diagnostic leg. All T1 bets placed after this date are YES-direction only. For the regular-season paper period (2026-27 NBA / MLB 2026 onwards), **T1 Tier 2 criteria (T2-A through T2-D) are evaluated exclusively on YES-direction eligible bets**. NO-direction counterfactuals are logged as `yes_only_gate_filtered` C6 events and preserved for analysis but do not contribute to G6 evidence.

**Derivation:** This is not a new restriction — it is a clarification of the natural consequence of an active YES-only gate. When the gate is operative, all T1 C4 evaluations that proceed to placement are YES-direction. The Tier 2 criteria must evaluate the deployed model, not a hypothetical model that would also place NO bets. Evaluating T2-A (calibration) or T2-B (EV) on a mixed sample that includes NO-bet counterfactuals (never actually placed) would contaminate the evidence.

**Deactivation path:** If the DS rescinds the YES-only gate (requiring a DS ruling), T1 Tier 2 reverts to evaluating both YES and NO direction eligible bets. This is tracked as a standing modification that lifts automatically when the gate is rescinded.

---

## Summary of Modifications

| Modification | Amends | Change |
|---|---|---|
| 5 — Fill-realism mandate | APR-0017 T2-B, T2-D (all buckets) | T2-B and T2-D evaluate post-haircut P&L (T-153 p50); previously used nominal paper P&L |
| 6 — T4 Tier 2 thresholds | APR-0019 (implicit checklist values) | Formally derives T4 T2-A (20pp), T2-B (EV>0 post-haircut), T2-C (Brier ≤0.265), T2-D (slope>0 post-haircut) |
| 7 — T4 game-night floor | APR-0019 (unstated) | Explicitly applies ≥5 game nights to T4 slope criteria; same df≥3 derivation as T1 |
| 8 — T-AGG portfolio goal | APR-0017 (gap — no such criterion existed) | New portfolio-level criterion: aggregate post-haircut EV > 0 (T-AGG-A) and aggregate P&L slope > 0 (T-AGG-B) |
| 9 — YES-only gate / T1 T2 | APR-0019 Mod 4 | Clarifies that active YES-only gate means T1 Tier 2 evaluates YES-direction eligible bets only for the regular-season paper period |

**What does NOT change:**
- Tier 0 (T0-A, T0-B)
- Tier 1 (T1-A, T1-B, T1-C, T1-D)
- Per-bucket floors (T1 ≥66 eligible, T4 ≥50 eligible) from APR-0019
- Tier 3 (T3-A, T3-B, T3-C, T3-E)
- T2-A and T2-C criteria (calibration deviation, Brier) — not P&L metrics; unaffected by fill-realism mandate
- Minimum game nights floor: ≥5 (already in APR-0017; Modification 7 adds explicit T4 coverage)
- ADR-0024 (stop/pivot criterion)
- C4 risk limits, cron schedule, formal G6 approval gates (APR-0008/0009)

---

## Updated G6 Closure Condition

For G6 to close, ALL of the following must be met:

1. **Tier 0** — T0-A (EXP-017 Part B CONFIRMED_POSITIVE on ADR-0024 adequate sample) + T0-B (already met)
2. **Statistical floors** — T1 ≥66 eligible bets + T4 ≥50 eligible bets + ≥5 game nights (both buckets)
3. **Tier 1** — T1-A, T1-B, T1-C, T1-D all pass
4. **Tier 2 (T1)** — T2-A, T2-B (post-haircut), T2-C, T2-D (post-haircut) all pass, evaluated on YES-only eligible bets
5. **Tier 2 (T4)** — T2-A, T2-B (post-haircut, two-leg), T2-C, T2-D (post-haircut, two-leg) all pass
6. **T-AGG** — aggregate portfolio post-haircut EV > 0 (T-AGG-A) + aggregate P&L slope > 0 (T-AGG-B)
7. **Tier 3** — T3-A, T3-B, T3-C, T3-E all pass
8. **Formal gate prerequisites** — ADR-0005, T-117, GG-014 (confirmed), GG-020, APR-0008, APR-0009

No partial promotion. All conditions must pass simultaneously.

---

## Broken-System Tests for New Criteria

| Criterion | Broken system that passes | Mitigation |
|---|---|---|
| Mod 5 (haircut mandate) | System with EV = +$0.05/bet on paper fills, EV = −$0.02/bet after realistic costs — passes T2-B without haircut | Fixed: T2-B evaluates post-haircut EV; positive only if positive after fill costs |
| Mod 6 (T4 thresholds) | T4 with EV = +$0.003/bet pre-haircut, EV = −$0.01/bet post two-leg haircut — "passes" if haircut not applied | Fixed: T4 T2-B explicitly requires two-leg haircut |
| Mod 8 T-AGG-A | T1 EV = +$0.10 (13 bets/game), T4 EV = +$0.001 (1,000 bets/game) → aggregate = +$0.0012 but well below fill-cost breakeven | Note: if both bucket T2-Bs pass post-haircut, aggregate T-AGG-A is likely met by construction for these values. T-AGG catches the case where T4 BARELY passes per-bucket but aggregate is negative after costs — specific scenario: T4 EV = +$0.001 but haircut = 0.015 → T4 negative → per-bucket T2-B fails → G6 already blocked. T-AGG adds defense-in-depth for portfolio-level interactions. |
| Mod 8 T-AGG-B | Lucky early runs give positive aggregate P&L but slope is negative | Fixed: slope criterion requires P&L to be increasing over game nights, not just positive at endpoint |
| Mod 9 (YES-only) | Include NO counterfactuals (never placed) in T1 T2-B to inflate n and dilute negative-EV NO bets into the average | Fixed: only placed (YES-direction) eligible bets count toward T1 Tier 2 |

---

## GG-022 Resolution Status

**GG-022** ("Paper-Fill Realism: APR-0017 Amendment Required") status changes to **RESOLVED** upon DS sign-off on this ADR. Modification 5 is the required APR-0017 amendment.

---

## Operator Sign-Off

**Review checklist:**

- [ ] Mod 5 — Fill-realism mandate: T2-B and T2-D evaluate post-haircut P&L at T-153 p50 estimate — acceptable
- [ ] Mod 5 — T1 haircut is upper bound (resting orders may be maker fills, zero cost) — conservative direction confirmed
- [ ] Mod 6 — T4 T2-A: calibration deviation ≤ 20pp, slope ≤ 0 (formally derived) — acceptable
- [ ] Mod 6 — T4 T2-B: fill-realism-adjusted EV > 0, slope ≥ 0 (two-leg haircut) — acceptable
- [ ] Mod 6 — T4 T2-C: Brier ≤ 0.265, slope ≤ 0 (L1 threshold as ceiling without T4 TEST baseline) — acceptable
- [ ] Mod 6 — T4 T2-D: fill-realism-adjusted P&L slope > 0 (two-leg haircut) — acceptable
- [ ] Mod 7 — T4 game-night floor: ≥5 nights (df ≥ 3, same as T1) — acceptable
- [ ] Mod 8 — T-AGG-A: aggregate post-haircut EV > 0 — acceptable
- [ ] Mod 8 — T-AGG-B: aggregate P&L slope > 0 over ≥5 game nights — acceptable
- [ ] Mod 9 — T1 Tier 2 evaluates YES-direction eligible bets while YES-only gate is active — acceptable
- [ ] G6 closure condition (all 8 items) — acceptable
- [ ] GG-022 status: RESOLVED upon sign-off — acceptable

**Sign-off:** _______________  
**Date:** _______________  
**Role:** DS — Earl Ignacio
