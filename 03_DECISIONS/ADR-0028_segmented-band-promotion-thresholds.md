# ADR-0028 — Segmented Per-Band Promotion Thresholds

**Status:** ACCEPTED — DS sign-off Earl Ignacio, 2026-06-22 SESSION 72 (initial draft 2026-06-22; DS sign-off declined 2026-06-22; rework 2026-06-22; accepted 2026-06-22 SESSION 72)  
**Amends:** APR-0017 (G6 Multi-Dimensional Evidence Standard, 2026-06-01) + APR-0019 (Per-Bucket Evidence Amendment, 2026-06-09)  
**Does NOT supersede:** APR-0017 or APR-0019 in full. Both remain operative in all sections not explicitly modified below.  
**Registered by:** T-148 (DECISION_LOG 2026-06-22 SESSION 65)  
**Analysis input:** T-148 regression analysis (DECISION_LOG 2026-06-09 SESSION 43); T-153 fill-realism haircut (DECISION_LOG 2026-06-12 SESSION 59); GG-022 (partially resolved — APR-0017 amendment deferred)  
**Drafted:** 2026-06-22 SESSION 65  
**Reworked:** 2026-06-22 SESSION 65 — T4 criteria and T-AGG moved from G6 to T4 Activation Gate (see Rework Note below)  
**Effective:** Upon DS sign-off; applies to all G6 evidence collected under APR-0017 / APR-0019

---

## Rework Note (2026-06-22)

Initial draft required T4 Tier 2 (Mods 6, 7) and T-AGG (Mod 8) for G6 closure. DS feedback: "the segmentation for the promotion bands are still not fully aligned with the current structure per band."

Root misalignment identified: The BAND_REGISTRY shows all T4 strategies are BLOCKED (Strategy K, C — Phase 8+, `requires_realtime=True`). T4 cannot generate real paper evidence during Phase 6/7 paper trading. APR-0019 established T4 as a G6 "active bucket" based on G3 virtual paper bets that predate BAND_REGISTRY enforcement. That premise is no longer structurally correct.

**Correction:** G6 is the T1 live capital gate. The only currently ACTIVE evidence-generating bucket is T1 (Strategy A, PIPE-02). T4 Tier 2 and T-AGG are moved to a separate "T4 Activation Gate" — a Phase 8 pre-requisite required before T4 strategies can be promoted from BLOCKED to ACTIVE.

**APR-0019 amendment:** APR-0019 Mod 1 (per-bucket independence) and Mod 2 (separate T1/T4 floors) remain operative. This ADR narrows the scope of those buckets in the G6 gate: at G6, only T1 is an active bucket. T4 becomes a separate gate. APR-0019's other provisions (Mods 3–5: eligible bets definition, YES/NO direction monitoring, injury-contaminated exclusion) remain fully operative.

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

APR-0019 established per-bucket independence and per-bucket calibration floors (T1 ≥66, T4 ≥50). The G6 gate checklist (T-172) carried T4 Tier 2 thresholds derived from the checklist author's judgment, not from a formal ADR derivation.

T4 uses a live Bayesian GameStateModel with no validated ECE or Brier baseline. Inheriting T1's numeric thresholds without derivation from T4's own properties violates the APR-0017 design principle: every pass/fail criterion must be derived from what it is actually measuring.

Additionally, T4 has a two-leg fill structure (entry ask + exit bid) with a higher per-bet fill cost than T1's one-leg entry.

**Note (rework):** This gap is real and must be resolved before T4 can be activated. However, it belongs to the T4 Activation Gate (Phase 8 pre-requisite), not to G6. G6 is a T1 gate; formal T4 threshold derivation is required at Phase 8, not Phase 6/7.

### Gap 3 — No aggregate portfolio P&L/capital goal

APR-0017 + APR-0019 require each active bucket to pass Tier 2 independently. There is no single portfolio-level criterion. The 2026-06-12 DS ruling (DECISION_LOG SESSION 56c) explicitly required "one aggregate P&L/capital goal at portfolio level" as a G6 gate.

**Note (rework):** T-AGG requires combined T1+T4 evidence. Since T4 is BLOCKED at G6, T-AGG cannot be evaluated at G6. T-AGG is moved to the T4 Activation Gate where both buckets are simultaneously active and generating live evidence. At G6, the T1 bucket's individual Tier 2 criteria (T2-B, T2-D) are the portfolio-level EV gate — they are sufficient because T1 is the only active capital-deploying bucket.

---

## Design Principle (inherited from APR-0017)

Every pass/fail criterion must be a rate, a slope, or a proportion. Counts appear only as derived minimums for statistical power, with derivation shown.

**Additional principle added by this ADR:** Every criterion that measures P&L or EV must specify whether it uses nominal paper P&L or fill-realism-adjusted P&L, with explicit justification. Silence on this question is not permitted.

---

## Modifications to APR-0017 / APR-0019

### Modification 5 — Fill-realism mandate for Tier 2 evaluation (resolves GG-022)

**Scope:** G6 gate (T1 bucket) + T4 Activation Gate (T4 bucket). Both gates evaluate P&L/EV criteria on fill-realism-adjusted figures.

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

T4 two-leg exit (entry ask + exit bid) — applied at T4 Activation Gate:
```
haircut_two_leg = entry_mid × (spread_bucket(entry_mid) / 2) + exit_mip × (spread_bucket(exit_mip) / 2)
```

**Application at G6:** Run `scripts/run_t153_haircut.py` on the complete G6 paper period data immediately before APR-0008 is drafted. The haircut output from that run is authoritative for G6 Tier 2 T2-B and T2-D evaluation (T1 bucket only).

**Application at T4 Activation Gate:** Run `scripts/run_t153_haircut.py` on the complete T4 paper period data immediately before the T4 Activation Gate is evaluated. Two-leg formula applies.

**What does NOT change:** T2-A (calibration deviation — based on predicted vs realized win rates, not P&L) and T2-C (Brier score) are not P&L metrics and are unaffected by this modification.

---

### Modification 6 — T4 Tier 2 thresholds — formal derivation [T4 ACTIVATION GATE]

**Scope:** T4 Activation Gate (Phase 8 pre-requisite). Does NOT apply to G6 — T4 is BLOCKED at Phase 6/7.

**Supersedes:** The implicit T4 Tier 2 threshold values in G6_GATE_CHECKLIST.md that were unanchored to a formal derivation.

**Derivation basis:** T4 uses a live Bayesian GameStateModel. Properties:
- No validated ECE baseline (unlike T1's 0.0247 from ADR-0004)
- Live inference under partial information (score updates during game)
- Observed win rate in G3: 51.4% (n=1,115) — closer to null than T1's expected 60%
- Two-leg exit structure with higher per-bet fill cost than T1

**T4 Tier 2 criteria (formally derived):**

#### T2-A (T4): Calibration deviation ≤ 20pp, slope ≤ 0

**Derivation:** T1's T2-A tolerance = 15pp = 6× TEST ECE (0.0247). T4 has no TEST ECE baseline. Without a validated ECE, anchor at: T4 operates at near-null win rate (51.4% vs expected 60%), suggesting wider inherent variance. Set tolerance at T1_tolerance × (T1_expected_win_variance / T4_expected_win_variance)^0.5 = 15pp × (0.60×0.40 / 0.514×0.486)^0.5 ≈ 15pp × 1.04 ≈ 16pp. Round up generously to **20pp** to account for live-inference noise and absent ECE baseline. Slope criterion (≤ 0) is derivation-independent: calibration must not be worsening.

#### T2-B (T4): Fill-realism-adjusted rolling EV > 0, slope ≥ 0

**Level threshold derivation:** EV > 0 after T4's two-leg haircut (Mod 5). The EV threshold of 0 is non-arbitrary: it is the commercial validity floor. A system with EV ≤ 0 post-haircut loses money in expectation under realistic execution conditions.

**Slope criterion:** Slope ≥ 0 (non-deteriorating). A system whose post-haircut EV is positive but declining toward zero is losing its edge over time.

**Application:** T4's two-leg haircut formula (Modification 5) applies. Eligible bets only (APR-0019 Modification 3 applies equally to T4).

#### T2-C (T4): Brier ≤ 0.265, slope ≤ 0

**Level threshold derivation:** T4 has no TEST-set Brier baseline. The monitoring L1 threshold (0.265) is the appropriate ceiling: L1 is calibrated as the first alert level — a model that has drifted enough to trigger L1 should not pass the T4 Activation Gate. Slope criterion: Brier slope ≤ 0 (non-increasing).

#### T2-D (T4): Fill-realism-adjusted P&L slope > 0

**Derivation:** Positive slope of the cumulative post-haircut T4 P&L over game nights is the direct measure of whether T4 generates value over time. The threshold of > 0 is non-arbitrary — ≤ 0 means T4's expected P&L per game night is zero or negative. Two-leg haircut formula applies.

**Statistical floor for T4 slope criterion:** ≥ 5 game nights (see Modification 7).

---

### Modification 7 — Minimum game nights: explicit for T4 [T4 ACTIVATION GATE]

**Scope:** T4 Activation Gate. Does NOT apply to G6.

**Adds to:** APR-0019, as a clarification of the game-night floor for T4.

**New rule:**

> The ≥ 5 game night floor (APR-0017 § Statistical Validity Floor) applies equally to T4 slope criteria (T2-A slope, T2-B slope, T2-D slope, and T3-B drawdown slope for the T4 pool). T4 slope criteria cannot be evaluated with fewer than 5 game nights of T4-resolved data, for the same df ≥ 3 reason as T1.

**Derivation:** T4 slope criteria (T2-A, T2-B, T2-D, T3-B) all use linear regression on (game_night_index, metric_value). Slope t-test requires df = n − 2 ≥ 3, meaning n ≥ 5 data points. This is identical to T1's derivation. APR-0019 did not explicitly state the floor for T4; this modification closes the gap.

**Implication:** Even though T4's bet-count floor (≥ 50) is trivially met in one game, the slope-based Tier 2 criteria for T4 require ≥ 5 game nights of resolved data. Both floors must be met simultaneously.

---

### Modification 8 — Aggregate portfolio P&L/capital goal (T-AGG) [T4 ACTIVATION GATE]

**Scope:** T4 Activation Gate. Does NOT apply to G6.

**Rationale for scope assignment:** T-AGG requires combined T1+T4 evidence. At G6, T4 is BLOCKED. T-AGG can only be evaluated when both T1 and T4 are simultaneously generating live evidence — i.e., after T4 has been activated to Phase 8 paper mode but before T4 strategies receive live capital. T-AGG evaluates the portfolio-level case for deploying live capital across both bands. This is a T4 Activation Gate requirement, not a G6 requirement.

**Adds to:** APR-0017 § Tier 2, as a new portfolio-level criterion evaluated after all per-bucket criteria pass at the T4 Activation Gate.

**New criterion: T-AGG — Aggregate Portfolio EV (Portfolio Level)**

This criterion is evaluated AFTER all per-bucket Tier 2 and Tier 3 criteria pass at the T4 Activation Gate. Per-bucket Tier 2 passing is not sufficient for T-AGG; T-AGG is evaluated independently.

#### T-AGG-A — Portfolio EV Level

**Pass condition:** Combined fill-realism-adjusted EV per dollar staked across **all active bands** > 0 at T4 Activation Gate evaluation.

**Metric:** `portfolio_EV = Σ_bands (post_haircut_P&L) / Σ_bands (total_staked)`

- Numerator: sum of T-153-adjusted P&L across all resolved positions in all active bands (T1 + T4, and any other bands active at T4 gate evaluation)
- Denominator: sum of all amounts staked across all active bands
- Eligible positions only (APR-0019 Modification 3 ineligibility rules apply)

**Derivation of level threshold (> 0):** The aggregate EV must be positive after fill costs. This is the commercial case for deploying live capital across both T1 and T4: the portfolio as a whole makes money in expectation. Setting it lower than 0 would permit a loss-generating portfolio to proceed to live T4 capital.

**Why per-bucket passing is not sufficient:** If T1 has EV = +$0.05/bet at 13 bets/game and T4 has EV = +$0.001/bet at 1,000 bets/game, and T4 dominates portfolio capital deployed, the combined portfolio EV after haircut may be negative even though both buckets individually pass. T-AGG catches this scenario.

#### T-AGG-B — Aggregate P&L Slope

**Pass condition:** Slope of the cumulative aggregate post-haircut P&L curve over game nights > 0 (linear regression; requires ≥ 5 game nights).

**Derivation:** Same logic as T1's T2-D: a positive net-positive P&L achieved by early lucky bets is not sufficient. The portfolio must demonstrate that each game night, in expectation, the aggregate gains.

**Metric construction:** At each game night index n, compute cumulative aggregate post-haircut P&L = Σ over all bands of T-153-adjusted P&L for all eligible positions resolved through night n. Fit a linear regression on (n, cumulative_P&L). The slope coefficient must be > 0.

---

### Modification 9 — YES-only gate interaction with T1 Tier 2 [G6 SCOPE]

**Scope:** G6 gate (T1 Tier 2 only).

**Adds to:** APR-0019 § Direction-Specific Evidence (monitoring note), as a clarification.

**New rule:**

> As of 2026-06-12 (DS ruling, SESSION 56c), the YES-only diagnostic gate (`PAPER_YES_ONLY`) is active for T1 PIPE-03 runs as a continuous diagnostic leg. All T1 bets placed after this date are YES-direction only. For the regular-season paper period (2026-27 NBA / MLB 2026 onwards), **T1 Tier 2 criteria (T2-A through T2-D) are evaluated exclusively on YES-direction eligible bets**. NO-direction counterfactuals are logged as `yes_only_gate_filtered` C6 events and preserved for analysis but do not contribute to G6 evidence.

**Derivation:** When the gate is operative, all T1 C4 evaluations that proceed to placement are YES-direction. The Tier 2 criteria must evaluate the deployed model, not a hypothetical model that would also place NO bets. Evaluating T2-A (calibration) or T2-B (EV) on a mixed sample that includes NO-bet counterfactuals (never actually placed) would contaminate the evidence.

**Deactivation path:** If the DS rescinds the YES-only gate (requiring a DS ruling), T1 Tier 2 reverts to evaluating both YES and NO direction eligible bets.

---

## Summary of Modifications

| Modification | Amends | Change | Gate scope |
|---|---|---|---|
| 5 — Fill-realism mandate | APR-0017 T2-B, T2-D (all buckets) | T2-B and T2-D evaluate post-haircut P&L (T-153 p50); previously used nominal paper P&L | G6 (T1) + T4 Activation Gate (T4) |
| 6 — T4 Tier 2 thresholds | APR-0019 (implicit checklist values) | Formally derives T4 T2-A (20pp), T2-B (EV>0 post-haircut), T2-C (Brier ≤0.265), T2-D (slope>0 post-haircut) | T4 Activation Gate only |
| 7 — T4 game-night floor | APR-0019 (unstated) | Explicitly applies ≥5 game nights to T4 slope criteria; same df≥3 derivation as T1 | T4 Activation Gate only |
| 8 — T-AGG portfolio goal | APR-0017 (gap — no such criterion existed) | New portfolio-level criterion: aggregate post-haircut EV > 0 (T-AGG-A) and aggregate P&L slope > 0 (T-AGG-B) | T4 Activation Gate only |
| 9 — YES-only gate / T1 T2 | APR-0019 Mod 4 | Clarifies that active YES-only gate means T1 Tier 2 evaluates YES-direction eligible bets only for the regular-season paper period | G6 (T1 only) |

**What does NOT change:**
- Tier 0 (T0-A, T0-B)
- Tier 1 (T1-A, T1-B, T1-C, T1-D)
- Per-bucket floors (T1 ≥66 eligible, T4 ≥50 eligible) from APR-0019 — T4 floor now applies at T4 Activation Gate
- Tier 3 (T3-A, T3-B, T3-C, T3-E)
- T2-A and T2-C criteria (calibration deviation, Brier) — not P&L metrics; unaffected by fill-realism mandate
- ADR-0024 (stop/pivot criterion)
- C4 risk limits, cron schedule, formal G6 approval gates (APR-0008/0009)

---

## Updated G6 Closure Condition

**G6 is a T1 live capital gate.** T4 is BLOCKED (BAND_REGISTRY: Strategy K BLOCKED, Phase 8+). T4 criteria belong to the T4 Activation Gate (see below). For G6 to close, ALL of the following must be met:

1. **Tier 0** — T0-A (EXP-017 Part B CONFIRMED_POSITIVE on ADR-0024 adequate sample) + T0-B (already met)
2. **Statistical floor** — T1 ≥66 eligible bets + ≥5 game nights (T1 slope regression df ≥ 3)
3. **Tier 1** — T1-A, T1-B, T1-C, T1-D all pass
4. **Tier 2 (T1)** — T2-A, T2-B (post-haircut, T-153 p50, one-leg), T2-C, T2-D (post-haircut) all pass; evaluated on YES-direction eligible bets while YES-only gate is active (Mod 9)
5. **Tier 3** — T3-A, T3-B, T3-C, T3-E all pass
6. **Formal gate prerequisites** — ADR-0005, T-117, GG-014 (confirmed), GG-020, APR-0008, APR-0009

No partial promotion. All conditions must pass simultaneously.

---

## T4 Activation Gate (Phase 8 Pre-Requisite) — TAXONOMY RESOLVED BY ADR-0029

> **SUB-BAND TAXONOMY NOW DEFINED — see ADR-0029 (ACCEPTED, Tier A frozen, DS sign-off 2026-06-22 SESSION 67).**
>
> T4 is not a monolithic bucket. DS directive 2026-06-22: "In-game trading is the most diverse section — can be the most complex or simple dependent on the route. It can't just be clumped as one aggregate bucket." T4 spans the full execution range from pre-staged resting orders through multi-minute model-driven holds (rich Bayesian update). T-179/ADR-0029 resolved this into **10 information-class sub-bands** (T4-MICRO carved out to ADR-0030 as a no-`model_p` strategy class). Each sub-band carries its own SLA, compute budget, Kelly framework, signal type, and model requirements.
>
> **Gate structure (Tier A, frozen by ADR-0029):** the T4 Activation Gate is **per-sub-band** — each of the 10 sub-bands clears its own gate independently and freezes its then-current values under its own activation ADR (APR-XXXX). The single-bucket criteria below are retained as the **structural template** each sub-band's gate instantiates.
>
> **Still pending (NOT cleared by the ADR-0029 sign-off):**
> - The per-sub-band Tier 2 criteria, statistical floors, T-AGG, and all numeric values are **Tier B (provisional)** under ADR-0029 — directional until each sub-band's own Phase 8 Activation Gate, revisable via DECISION_LOG (not a superseding ADR).
> - **ADR-0028's own DS sign-off (T-148) is still pending** — accepting ADR-0029 resolved the *taxonomy* dependency, not ADR-0028's own acceptance.

**This gate must be satisfied before any T4 strategy (Strategy K or equivalent) can be promoted from BLOCKED to ACTIVE.** It is independent of G6 — G6 may close before this gate opens. This gate applies when T4 strategies are operating in live paper mode at Phase 8.

For the T4 Activation Gate to clear, ALL of the following must be met:

1. **Statistical floor** — T4 ≥50 eligible bets + ≥5 game nights (Mod 7)
2. **T4 Tier 2** — T2-A (≤20pp calibration deviation, slope ≤0), T2-B (post-haircut two-leg EV>0, slope≥0), T2-C (Brier ≤0.265, slope ≤0), T2-D (post-haircut two-leg P&L slope>0) — all pass (Mod 6, Mod 7)
3. **T-AGG** — T-AGG-A (aggregate portfolio post-haircut EV > 0) + T-AGG-B (aggregate portfolio P&L slope > 0 over ≥5 game nights) — both pass (Mod 8)
4. **Formal prerequisites** — BLOCKED→ACTIVE promotion ADR for Strategy K + DS sign-off (APR-XXXX) + real-time C5 infrastructure ADR + kill switch SLA revision to <5s (per Strategy K notes: "Kill switch 60s SLA is 12x too slow for T4/T5; requires <5s")
5. **ADR-0019 Tier 2 activation gate** — EXIT_MECHANICS_ACTIVE confirmed active and T-152/T-153 empirical validation complete

Passing G6 (T1 live capital) does NOT automatically satisfy the T4 Activation Gate. These are independent gates with independent evidence requirements.

---

## Broken-System Tests for New Criteria

| Criterion | Broken system that passes | Mitigation |
|---|---|---|
| Mod 5 (haircut mandate) | System with EV = +$0.05/bet on paper fills, EV = −$0.02/bet after realistic costs — passes T2-B without haircut | Fixed: T2-B evaluates post-haircut EV; positive only if positive after fill costs |
| Mod 6 (T4 thresholds) | T4 with EV = +$0.003/bet pre-haircut, EV = −$0.01/bet post two-leg haircut — "passes" if haircut not applied | Fixed: T4 T2-B explicitly requires two-leg haircut at T4 Activation Gate |
| Mod 8 T-AGG-A | T1 EV = +$0.10 (13 bets/game), T4 EV = +$0.001 (1,000 bets/game) → aggregate EV positive per-bucket but combined post-haircut aggregate may be negative | Fixed: T-AGG-A directly measures combined portfolio EV; both buckets must be simultaneously active at T4 Activation Gate |
| Mod 8 T-AGG-B | Lucky early runs give positive aggregate P&L but slope is negative | Fixed: slope criterion requires P&L to be increasing over game nights, not just positive at endpoint |
| Mod 9 (YES-only) | Include NO counterfactuals (never placed) in T1 T2-B to inflate n and dilute negative-EV NO bets into the average | Fixed: only placed (YES-direction) eligible bets count toward T1 Tier 2 at G6 |

---

## GG-022 Resolution Status

**GG-022** ("Paper-Fill Realism: APR-0017 Amendment Required") status changes to **RESOLVED** upon DS sign-off on this ADR. Modification 5 is the required APR-0017 amendment.

---

## Operator Sign-Off

**Review checklist:**

- [x] Rework rationale — T4 removed from G6 (BLOCKED/Phase 8+); T4 criteria moved to T4 Activation Gate — acceptable
- [x] Mod 5 — Fill-realism mandate: T2-B and T2-D evaluate post-haircut P&L at T-153 p50 estimate, scoped to G6 (T1) and T4 Activation Gate (T4) — acceptable
- [x] Mod 5 — T1 haircut is upper bound (resting orders may be maker fills, zero cost) — conservative direction confirmed
- [x] Mod 6 — T4 T2-A: calibration deviation ≤ 20pp, slope ≤ 0 (formally derived); T4 Activation Gate scope — acceptable
- [x] Mod 6 — T4 T2-B: fill-realism-adjusted EV > 0, slope ≥ 0 (two-leg haircut); T4 Activation Gate scope — acceptable
- [x] Mod 6 — T4 T2-C: Brier ≤ 0.265, slope ≤ 0 (L1 threshold as ceiling without T4 TEST baseline); T4 Activation Gate scope — acceptable
- [x] Mod 6 — T4 T2-D: fill-realism-adjusted P&L slope > 0 (two-leg haircut); T4 Activation Gate scope — acceptable
- [x] Mod 7 — T4 game-night floor: ≥5 nights (df ≥ 3, same as T1); T4 Activation Gate scope — acceptable
- [x] Mod 8 — T-AGG-A: aggregate post-haircut EV > 0; T4 Activation Gate scope — acceptable
- [x] Mod 8 — T-AGG-B: aggregate P&L slope > 0 over ≥5 game nights; T4 Activation Gate scope — acceptable
- [x] Mod 9 — T1 Tier 2 evaluates YES-direction eligible bets while YES-only gate is active; G6 scope — acceptable
- [x] G6 closure condition (6 items, T1-only) — acceptable
- [x] T4 Activation Gate conditions (5 items) — acceptable
- [x] GG-022 status: RESOLVED upon sign-off — acceptable

**Sign-off:** Earl Ignacio  
**Date:** 2026-06-22  
**Role:** DS — Earl Ignacio

---
**Partially superseded by ADR-0076 (2026-10-27):** the G6 definition (per book and sport, cell wins at its judged n) is now `ADR-0076_g6-per-book-sport-qualification-and-tail-derived-limits.md`. Body above is unchanged.
