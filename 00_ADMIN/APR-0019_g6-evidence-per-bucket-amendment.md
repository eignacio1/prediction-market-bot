# APR-0019 — G6 Evidence Standard Amendment: Per-Bucket Evidence Separation

**Status:** ACCEPTED — DS sign-off 2026-06-09  
**Amends:** APR-0017 (G6 Multi-Dimensional Evidence Standard, 2026-06-01)  
**Does NOT supersede:** APR-0017 in full. APR-0017 remains operative in all sections not explicitly modified below.  
**Approved by:** [pending — DS: Earl Ignacio]  
**Drafted:** 2026-06-09 SESSION 43  
**Analysis source:** T-148 regression analysis (DECISION_LOG 2026-06-09 SESSION 43)  
**Effective:** Upon DS sign-off; applies retroactively to all paper bets resolved under APR-0017

---

## Why This Amendment Is Required

APR-0017's Statistical Validity Floor (§ "Minimum resolved bets: 66") was derived under a T1-only assumption:

> *"The 66-bet floor was derived assuming the Finals paper window (1 game/night, ~38 markets, T1-only)."*

T4 was activated as a live paper band (PAPER_T4_VIRTUAL=false) on 2026-06-03 and produced **1,115 resolved bets in a single game** during Finals G3. T4 and T1 are structurally different inference problems:

| Property | T1 (pregame) | T4 (in-play) |
|---|---|---|
| Model | Poisson CDF, static pregame λ | Live Bayesian GameStateModel + adj_λ |
| Evidence type | Pre-game point probability | Posterior updates under partial information |
| ECE baseline | 0.0247 (validated, ADR-0004) | No validated ECE baseline yet |
| Bets per game | ~13 (Finals constraint) | ~1,115 (G3 observed) |
| Error distribution | Characterized | Uncharacterized pre-production |

**Pooling T1 and T4 bets toward a shared calibration floor conflates evidence from structurally different models.** APR-0017's T2-A formula was derived for T1's ECE distribution specifically. Applying it to a mixed pool where 98.8% of bets (1,115 of 1,128) are T4 means the calibration gate evaluates the live Bayesian model, not the pregame Poisson model — while the evidence standard was written for the latter.

**A secondary issue identified by EXP-018:** APR-0017 does not define which bets are eligible for Tier 2 evaluation. Without an explicit eligibility rule, bets with incomplete model inputs at prediction time (KI-011: injury blindness) are counted toward the evidence standard — contaminating the EV and calibration signals that Tier 2 is designed to measure.

---

## Modifications to APR-0017

### Modification 1 — Replace "Minimum resolved bets: 66" with per-bucket floors

**Supersedes:** APR-0017 § Statistical Validity Floor, "Minimum resolved bets: 66" (including all text in that subsection).

**New text:**

#### Per-Bucket Calibration Floors

The statistical validity floor is derived independently for each active execution bucket. T1 and T4 cannot share a floor because they use different models with different error distributions.

##### T1 Calibration Floor: ≥ 66 resolved eligible bets

**Derivation (unchanged from APR-0017):**

T2-A formula at α = 0.10 (one-sided, accepting moderate power given Finals constraint), power = 0.80, δ = 15pp, p̂ = 0.60:

```
n = (z_α/2 + z_β)² × p̂q̂ / δ²
  = (1.282 + 0.842)² × 0.60 × 0.40 / 0.15²
  = 4.512 × 0.24 / 0.0225
  ≈ 66
```

*Note: full-power derivation at α = 0.05 gives n = 84. APR-0017's conservative 66 floor (α = 0.10) is retained — it was accepted with the understanding that T2-A calibration will have moderate rather than high power given the Finals series constraint. If 84 T1 eligible bets are available before G6 is called, all tier evaluations use 84 as the floor.*

**Current status:** T1 has 82 resolved bets as of Finals G3 (2026-06-08). T1 floor met.

##### T4 Calibration Floor: ≥ 50 resolved eligible bets

**Derivation:**

T4 uses a live Bayesian model with no validated ECE baseline. Without a TEST-set ECE reference, the T2-A calibration deviation parameter must be set more conservatively. T4 in-play inference operates under:
- Partial information (score state is updated but full game has not resolved)
- Wider model output variance than static pregame Poisson
- A live win rate of 51.4% (G3, n=1,115) — closer to the null than T1's expected 60%

**Parameter choices for T4 T2-A formula:**
- α = 0.05 (two-sided), power = 0.80 → z_α/2 = 1.960, z_β = 0.842
- δ = 20pp (conservative tolerance; wider than T1's 15pp because T4's live inference has higher inherent noise and no ECE baseline to anchor the tolerance)
- p̂ = 0.514 (observed T4 G3 win rate; expected win rate under positive edge)
- q̂ = 0.486

```
n = (1.960 + 0.842)² × 0.514 × 0.486 / 0.20²
  = 7.854 × 0.2498 / 0.04
  = 1.961 / 0.04
  ≈ 49 → ceil to 50
```

**Floor: ≥ 50 T4 resolved eligible bets.**

*Note: T4 trivially exceeds this floor after one game (~1,115 bets/game). The T4 floor is not the binding G6 constraint — it is a formal lower bound for statistical validity. The binding T4 G6 constraint is Tier 2 criteria (T2-A through T2-D) evaluated on ≥50 eligible bets.*

---

### Modification 2 — Tier 2 applies per-bucket independently

**Supersedes:** APR-0017 § Tier 2 header, which implies a unified Tier 2 evaluation pool.

**New rule:**

> **Tier 2 criteria (T2-A, T2-B, T2-C, T2-D) are evaluated independently for each active execution bucket. T1 Tier 2 is evaluated exclusively on T1-eligible bets. T4 Tier 2 is evaluated exclusively on T4-eligible bets. Evidence from different buckets is never pooled.**

**Rationale:** T1 and T4 use different model classes (Poisson CDF vs. live Bayesian update). Calibration deviation, EV, Brier, and P&L slope have different expected distributions for each. Pooling conflates two measurement problems into one floor that was designed for only one.

**G6 closure condition:** G6 cannot close until **all active buckets** pass their per-bucket Tier 2 criteria independently. Currently active buckets: T1, T4. T2 and T3 are SKELETON status — Tier 2 criteria do not apply until they are activated.

**If a bucket fails Tier 2 while other buckets pass:** G6 promotion is blocked. The failing bucket must be deactivated (scoped to SKELETON) or its model retrained and re-evaluated before G6 can close. A partial promotion (some buckets go live) is not permitted under APR-0008/0009 — the evidence standard applies to the deployed system as a whole.

---

### Modification 3 — Eligible bets definition

**Adds to:** APR-0017, as a new subsection inserted before § Statistical Validity Floor.

**New text:**

#### Eligible Bet Definition

**Eligible bets** = paper bets where all model inputs required for that bet's prediction were complete and uncontaminated at the time the prediction was made.

Bets placed when model inputs were known to be incomplete or contaminated are **ineligible** for Tier 2 evaluation. They may be logged and tracked as a separate cohort but do not count toward Tier 2 pass/fail criteria.

**Current documented contamination source:** KI-011 (injury blindness). When T1 places a bet on a player who was injured or had a significant rest/availability change that was not captured in the L10 rolling window at prediction time, that bet's outcome is determined by factors the model had no information about. Including such bets in calibration or EV measurement conflates model failure with data incompleteness.

**Operationalization:** A bet is ineligible if any of the following apply at prediction time:
1. Player was injured or placed on injury report within 48h of game tip-off, and T2 overlay was not operational at the time of bet placement (KI-011 is the formal tracker for this failure mode).
2. Player was not in the starting lineup for a rest/load-management decision documented post-hoc, and this information was unavailable to T1 at prediction time.
3. Any other condition where the primary model input (pts_l10_mean, adj_λ, opp_def_l10) is demonstrably stale or inapplicable due to external information absent from the model at prediction time.

**Source of ineligibility determinations:** DS review of each excluded bet. Ineligibility must be documented with bet identifier, exclusion reason, and the specific KI-NNN or evidence basis. Post-hoc outcome-based exclusion (excluding bets because they lost) is not permitted.

**EXP-018 ruling (DECISION_LOG 2026-06-09):** The 6 injury-contaminated bets excluded from T1 Tier 2B evaluation are a documented application of this rule. The injury-filtered EV (+$0.0202/bet, n=60) is the operative T1 Tier 2B evidence.

---

### Modification 4 — YES/NO direction-specific evidence tracking

**Adds to:** APR-0017 § Tier 2, as a new monitoring note.

**New text:**

#### Direction-Specific Evidence (Monitoring)

EXP-018 (2026-06-08) found structural asymmetry between YES and NO bet performance: YES bets +$0.0733/bet (n=24), NO bets −$0.0440/bet (n=42). This asymmetry survives injury filtering — it is not an artifact of data contamination.

**Governance status:** This asymmetry is NOT a current G6 blocker. It is a model calibration concern registered for the dark period model retrain (T-072). Possible mechanism: Poisson CDF may systematically overestimate P(over) at high threshold markets, creating apparent NO-edge that does not materialize.

**Monitoring requirement:** As paper bets accumulate through G4/G5, track YES and NO direction P&L separately. If the NO-bet EV deficit persists or worsens at n ≥ 30 NO bets (with injury filter applied), escalate to an open question for dark period model diagnostic before G6. If YES-only EV is positive and NO EV is neutral or negative at G6 evaluation, DS may exclude NO bets from T1 Tier 2B calculation and note this in the G6 evidence report — subject to the same ineligibility documentation requirement as Modification 3.

---

## Summary of Changes to APR-0017

| Section | Change type | What changes |
|---|---|---|
| Statistical Validity Floor — Minimum resolved bets | **Superseded** | Replaces unified 66-bet floor with per-bucket floors: T1 ≥ 66 eligible (unchanged derivation), T4 ≥ 50 eligible (new derivation) |
| Tier 2 header | **Clarified** | Explicit: Tier 2 evaluated independently per active bucket; no cross-bucket pooling |
| G6 closure condition | **Strengthened** | All active buckets must pass Tier 2 independently; no partial promotion |
| Pre-§ Statistical Validity Floor | **New section added** | Eligible bet definition; ineligibility criteria; DS documentation requirement |
| Tier 2 (new monitoring note) | **New section added** | YES/NO direction-specific EV tracking; escalation trigger if NO asymmetry persists |

**What does NOT change:** Tier 0 (T0-A/B), Tier 1 (T1-A/B/C/D), Tier 3 (T3-A/B/C), minimum game nights (≥5), all numeric thresholds in Tier 1 and Tier 3, C4 risk limits, cron schedule, G6 formal approval gates (APR-0008/0009).

---

## Broken-System Tests for New Rules

| New rule | Broken system that passes | Mitigation |
|---|---|---|
| Per-bucket Tier 2 | T4 fires 50,000 bets/season at chance-level performance; T1 has 84 strong bets → pools to apparent success | Fixed by: T1 and T4 evaluated independently. T4 must show positive EV on T4 bets alone. |
| Eligible bets | Operator excludes all losing NO bets as "injury contaminated" | Fixed by: ineligibility requires documented KI-NNN basis, pre-bet-time information only, DS approval per bet. Outcome-based exclusion prohibited. |
| YES-only evaluation | Operator excludes NO bets for direction performance reasons, not data completeness | Fixed by: direction-based exclusion requires separate evidence (structural model issue documented via T-072 diagnostic) plus DS sign-off at G6 evaluation. Cannot be done silently. |

---

## Operator Sign-Off

**Review checklist:**

- [ ] T1 calibration floor: ≥66 eligible T1 bets (derivation unchanged from APR-0017) — acceptable
- [ ] T4 calibration floor: ≥50 eligible T4 bets (derived via T2-A at α=0.05, δ=20pp, p̂=0.514) — acceptable
- [ ] Per-bucket Tier 2 independence: T1 and T4 Tier 2 evaluated separately, no pooling — acceptable
- [ ] G6 closure requires all active buckets to pass Tier 2 — acceptable
- [ ] Eligible bets definition: complete model inputs at prediction time; ineligibility requires documented basis, no outcome-based exclusion — acceptable
- [ ] KI-011 injury exclusion (EXP-018, n=6): applied per eligible bets definition — acceptable
- [ ] YES/NO direction tracking: monitoring only, not a current G6 gate — acceptable
- [ ] APR-0017 remains operative in all non-amended sections — acceptable

**Sign-off:** Earl Ignacio  
**Date:** 2026-06-09  
**Role:** DS — Earl Ignacio
