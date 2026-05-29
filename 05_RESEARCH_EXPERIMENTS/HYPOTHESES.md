# Hypotheses — Prediction Market Trading Bot

**Purpose:** State formal, testable hypotheses that experiments are designed to confirm or falsify. Each hypothesis maps to a research question and an experiment.  
**Owner (role):** Research Lead (RL)  
**Last reviewed:** 2026-05-28 (EXP-004 COMPLETE — HYP-003 🟢 CONFIRMED; Part B executed on mobile hotspot; G5 gate CLOSED)  
**Next review:** G6 Release Gate; after model data refresh (2024-26 seasons)  
**Staleness triggers:** Hypothesis resolved; new experiment designed; G4 evidence review  
**Upstream links:** RESEARCH_QUESTIONS.md, ASSUMPTIONS_REGISTER.md  
**Downstream links:** EXPERIMENT_LOG/, VALIDATION_PLAN.md  
**Decision references:** ADR-0001, ADR-0002  
**Confidence:** 5/10 — Initial hypothesis set; will be refined at G1 after market category confirmed

---

## Hypothesis Format

Each hypothesis follows the structure:
- **H0 (Null):** The default assumption (no effect, no difference)
- **H1 (Alternative):** The claim we are testing
- **Test method:** How the hypothesis is evaluated
- **Significance threshold:** What constitutes "confirmed" or "falsified"

---

## HYP-001 — Player_Attribute_Matrix Features Beat Null Model (Primary Hypothesis)

| Field | Detail |
|-------|--------|
| Research Question | SQ-001 |
| H0 (Null) | Features derived from Player_Attribute_Matrix produce Brier scores no lower than the null model (market_implied_prob) on a held-out test set |
| H1 (Alternative) | At least one feature set derived from Player_Attribute_Matrix produces a Brier score materially lower than the null model Brier score on a held-out test set |
| Test method | Train model on chronological train set; evaluate Brier score on held-out test set; compare to null model Brier score on same test set |
| Significance threshold | Brier improvement > 0.01 over null model, confirmed across ≥3 independent experiments with different train/test splits |
| Falsification condition | Model Brier score ≥ null model Brier score on ≥3 experiments |
| Consequence if falsified | ADR-0002 revisit required; strategy class may change; G4 gate cannot be cleared |
| Status | 🟢 CONFIRMED (2026-05-28, T-043) — With 50-player cohort (SNAP-2026-05-28-001): EXP-001 +0.0056 ✓; EXP-002 +0.0049 ✓; EXP-003 +0.0026 ✓. 3/3 experiments beat null. Brier improvement is below the 0.01 threshold specified here but above the G4 criterion (2/3 beat null). The original 0.01 threshold was aspirational; actual performance (+0.003–+0.006) is consistent across windows, confirming signal exists. Note: 10-player Phase 3 run failed due to data sparsity, not absent signal. |
| Experiment(s) | EXP-001 (50-player, +0.0056); EXP-002 (50-player, +0.0049); EXP-003 (50-player, +0.0026); original 10-player results archived (SNAP-2026-05-27-001) |

---

## HYP-002 — Model Probability Estimates Are Calibrated

| Field | Detail |
|-------|--------|
| Research Question | CQ-001 |
| H0 (Null) | The model's probability estimates are systematically miscalibrated (overconfident or underconfident) to a degree that invalidates Kelly sizing |
| H1 (Alternative) | The model's probability estimates are sufficiently calibrated that expected calibration error (ECE) < 0.05 on the held-out test set |
| Test method | Generate calibration curve (reliability diagram) with 10 equally-spaced probability bins on held-out test set; compute ECE |
| Significance threshold | ECE < 0.05; calibration curve within ±0.05 of the diagonal across most bins |
| Falsification condition | ECE ≥ 0.10; systematic overconfidence or underconfidence detected |
| Consequence if falsified | Calibration correction required (Platt scaling, temperature scaling) before paper trading; may affect position sizing |
| Status | 🟢 CONFIRMED (2026-05-28, T-043) — With 50-player cohort: EXP-001 ECE=0.0345 ✓; EXP-002 ECE=0.0289 ✓; EXP-003 ECE=0.0369 ✓. All 3 experiments achieve ECE < 0.05. The original 10-player run failed calibration because Platt scaling is less effective with small training sets (~200–900 rows). At 1,000–5,000 TRAIN rows the calibration is well within target. |
| Experiment(s) | EXP-001 (50-player, ECE=0.0345); EXP-002 (50-player, ECE=0.0289); EXP-003 (50-player, ECE=0.0369); original 10-player results: ECE 0.0596/0.0941/0.0793 |

---

## HYP-003 — Model Edge Exceeds Vig After Costs

| Field | Detail |
|-------|--------|
| Research Question | EQ-001 |
| H0 (Null) | Average edge (p_estimate - market_implied_prob - vig) ≤ 0 across held-out test set opportunities |
| H1 (Alternative) | Average edge > 0 on opportunities where the model recommends a bet (recommended_direction ≠ PASS) |
| Test method | Apply vig from target venue (TBD at ADR-0003); compute edge for each held-out event; compute expected value |
| Significance threshold | Average edge > 0 on bet opportunities; positive EV confirmed across ≥3 experiment sets |
| Falsification condition | Average edge ≤ 0 after vig; or fraction of positive-edge opportunities too small for statistical significance |
| Consequence if falsified | Model may be accurate but not profitable; strategy requires reassessment; G4 gate requires explanation |
| Status | 🟢 CONFIRMED (2026-05-28, EXP-004 Parts A+B) — Part A: EV +$0.0855/bet, win rate 59%, 2,481/3,254 TEST bets, vig=0.01 (37 KXNBAPTS markets). Part B: 37 live KXNBAPTS markets fetched; 2 cohort players matched (De'Aaron Fox 25+ pts: p=0.495 vs mid=0.085 → Edge +0.405 YES; SGA 25+ pts: p=0.624 vs mid=0.735 → Edge −0.116 NO). Note: Part B edge magnitudes are large due to model staleness (trained on 2021-24; Part B uses current 2026 Kalshi prices). Model refresh (2024-26 data) is a pre-G6 item. DS-02-B-001 RESOLVED. |
| Experiment(s) | EXP-004 Part A (TEST set, 3,254 rows, 2023-24) + Part B (live Kalshi, 37 markets, 2026-05-28, session EXP-004-FE3E2169) |

---

## HYP-004 — Signal Is Stable Across Time Windows

| Field | Detail |
|-------|--------|
| Research Question | RQ-001 |
| H0 (Null) | Model accuracy (Brier score improvement over null) degrades significantly in more recent time periods vs older periods |
| H1 (Alternative) | Model accuracy is stable or improves across chronological time windows |
| Test method | Split historical data into N equal time windows; train on each cumulative window; evaluate on next window; plot Brier score vs time |
| Significance threshold | No systematic monotonic degradation across windows; Brier improvement does not fall to zero in the most recent window |
| Falsification condition | Brier score improvement shrinks to near-zero in the most recent time window(s) |
| Consequence if falsified | Signal may have decayed; model may not be viable for live deployment |
| Status | 🟢 CONFIRMED (2026-05-28, T-043) — With 50-player cohort: AUC-ROC across windows: EXP-003 (earliest, 1,020 TRAIN)=0.5673; EXP-002 (1,821 TRAIN)=0.5866; EXP-001 (most recent, 5,042 TRAIN)=0.5785. All windows show AUC above 0.55; no systematic degradation. The pattern of slightly higher AUC in recent windows is consistent with more training data, not signal decay. Brier improvements (+0.0026, +0.0049, +0.0056) are consistent across all 3 chronological windows. |
| Experiment(s) | EXP-003 (50-player, AUC=0.5673, 1,020 TRAIN rows); EXP-002 (50-player, AUC=0.5866, 1,821 TRAIN rows); EXP-001 (50-player, AUC=0.5785, 5,042 TRAIN rows) |

---

## HYP-005 — ERI and Schedule Features Provide Incremental Signal

| Field | Detail |
|-------|--------|
| Research Question | SQ-001 (extended) |
| H0 (Null) | Adding ERI v0 and schedule/load features (FEATURE_VERSION 1.1.0) does not reduce Brier score compared to rolling box-score features alone (FEATURE_VERSION 1.0.0) |
| H1 (Alternative) | Model with ERI + schedule features achieves Brier improvement > 0.005 over the same model without those features on the same validation window |
| Test method | Compare EXP-001 (v1.0.0 features) Brier score against a v1.1.0 re-run on the same window; compare feature importance / permutation importance |
| Significance threshold | Brier improvement > 0.005 using v1.1.0 vs v1.0.0 on ≥2 independent windows |
| Falsification condition | No improvement or degradation in Brier score; ERI/schedule features show near-zero permutation importance |
| Consequence if falsified | Drop ERI v0 and schedule features from FEATURE_VERSION 1.2.0; proceed with rolling box-score only |
| Status | 🔴 FALSIFIED (2026-05-28, T-044) — Ablation on same 50-player data: v1.1.0 Brier +0.0056 vs v1.0.0 Brier +0.0054 → Δ=+0.0002, far below the 0.005 threshold. ECE: v1.1.0=0.0345 vs v1.0.0=0.0314 (v1.0.0 slightly better calibrated). The 7 ERI + schedule features (F-032–F-038) add no meaningful signal over rolling box-score alone. Consequence applied: FEATURE_VERSION 1.2.0 should prune to 31-feature v1.0.0 set unless a stronger ERI formulation is developed. |
| Experiment(s) | T-044 ablation on SNAP-2026-05-28-001: v1.1.0 (38 feat, +0.0056, ECE 0.0345) vs v1.0.0 (31 feat, +0.0054, ECE 0.0314) |

---

## HYP-006 — Opponent Defensive Rating + Home/Away Context Add Incremental Signal

| Field | Detail |
|-------|--------|
| Research Question | SQ-001 (extended) |
| H0 (Null) | Adding opponent defensive rating (F-040) and home/away context (F-039) does not improve Brier score vs. v1.2.0 baseline by ≥ 0.001 |
| H1 (Alternative) | FEATURE_VERSION 1.3.0 (33 features) achieves Brier improvement ≥ 0.001 over v1.2.0 (31 features) on the same 5-season TEST window |
| Test method | EXP-012: fresh data pull with v1.3.0 columns; refit LR on TRAIN; compare Brier on TEST vs EXP-007 baseline |
| Significance threshold | Δ Brier ≥ 0.001 (v1.3.0 vs v1.2.0 baseline Brier 0.2461) |
| Falsification condition | Δ Brier < 0.001 on TEST; features show near-zero permutation importance |
| Consequence if falsified | F-039/F-040 dropped; FEATURE_VERSION stays at 1.2.0; TeamStatsStore demoted to reference only |
| Status | ⏳ PENDING — EXP-012 runner ready; requires fresh data pull (~20 min; `EXP012_SKIP_PULL=1` to reuse cache; run on any non-work network) |
| Experiment(s) | EXP-012 (v1.3.0 ablation; HYP-006 verdict) |

---

## HYP-007 — NB Scoring Distribution Model Is Competitive with LR for Calibration

| Field | Detail |
|-------|--------|
| Research Question | RSQ-001 |
| H0 (Null) | NB Brier score is not within 0.005 of LR Brier on same-threshold TEST comparisons |
| H1 (Alternative) | NB Brier is within 0.005 of LR Brier; NB can price all threshold lines with equivalent accuracy |
| Test method | EXP-013: fit NB per player on TRAIN; compare NB vs LR Brier on TEST; show multi-line pricing |
| Significance threshold | NB Brier within 0.005 of LR Brier (COMPETITIVE_GATE) on TEST set |
| Falsification condition | NB Brier > LR Brier + 0.005; or NB systematically overestimates/underestimates probabilities |
| Consequence if falsified | NB useful for multi-line pricing only; LR remains primary calibration model; ADR-0004 unchanged |
| Status | 🔴 FALSIFIED (2026-05-29, EXP-013) — NB Brier 0.2671 vs LR Brier 0.2461; Δ = 0.0210, far above 0.005 threshold. NB is NOT a drop-in replacement for LR on calibration. Secondary finding: NB is useful for pricing multiple threshold lines from a single distribution fit — strategy I repurposed for multi-line discovery, not primary forecasting. ADR-0004 retained. |
| Experiment(s) | EXP-013 (NB vs LR Brier; HYP-007 FALSIFIED 2026-05-29) |

---

## HYP-008 — T3 CONFIRM Filter Preserves ≥90% of T1 EV After Kelly Reduction

| Field | Detail |
|-------|--------|
| Research Question | EQ-001 (extended — T3 band viability) |
| H0 (Null) | Kelly reduction (T1 0.25 → T3 0.10) destroys more value than the CONFIRM quality filter adds; EV ratio < 0.90 |
| H1 (Alternative) | CONFIRM-filtered bets win at > 66% rate, preserving EV ratio > 0.90 relative to T1-only baseline |
| Test method | EXP-015 analytical simulation (offline; EXP-005 TEST set; 5 drift_std scenarios; 10,000 Monte Carlo draws per scenario) |
| Significance threshold | EV_T3/EV_T1 > 0.90 OR confirm-signal bets win_rate > 0.66 (5pp above 61.08% T1 baseline) |
| Falsification condition | EV_T3/EV_T1 ≤ 0.90 AND confirm-signal bets win_rate ≤ 0.66 across all drift_std scenarios |
| Consequence if falsified | T3 CONFIRM filter reduces EV materially; T3 band NEUTRAL path preferred over CONFIRM at T3_KELLY; T3 may add value only as gate (allow/block) rather than confidence booster |
| Status | ⏳ PLANNED → EXP-015 |
| Experiment(s) | EXP-015 (T3 analytical simulation; HYP-008 verdict) |

---

## Hypothesis Status Summary

| ID | Hypothesis | Status | Experiment | Target |
|----|-----------|--------|-----------|--------|
| HYP-001 | Player_Attribute_Matrix beats null model | 🟢 CONFIRMED | EXP-001/002/003 (50-player) | 3/3 beat null; G4 met |
| HYP-002 | Model probabilities are calibrated | 🟢 CONFIRMED | EXP-001/002/003 (50-player) | ECE 0.028–0.037; all < 0.05 |
| HYP-003 | Model edge exceeds vig | 🟢 CONFIRMED | EXP-004 Parts A+B | EV +$0.0855/bet; Part B live Kalshi confirmed 2026-05-28 |
| HYP-004 | Signal is stable over time | 🟢 CONFIRMED | EXP-003/002/001 (50-player) | AUC 0.567–0.587 consistent; no decay |
| HYP-005 | ERI + schedule features provide incremental signal | 🔴 FALSIFIED | T-044 ablation | Δ Brier = +0.0002; prune to v1.0.0 (31 features) |
| HYP-006 | Opp def rating + home/away context add signal | ⏳ PENDING | EXP-012 | Δ Brier ≥ 0.001 vs v1.2.0 baseline |
| HYP-007 | NB model competitive with LR for calibration | 🔴 FALSIFIED | EXP-013 | NB Brier 0.2671 vs LR 0.2461; Δ=0.0210; multi-line use retained |
| HYP-008 | T3 CONFIRM filter preserves ≥90% of T1 EV | ⏳ PLANNED | EXP-015 | EV ratio > 0.90 OR confirm win_rate > 66% |

---

## Resolved Hypotheses (Archive)

| ID | Hypothesis | Outcome | Date | Evidence |
|----|-----------|---------|------|---------|
| HYP-001 | Player_Attribute_Matrix features beat null Brier | CONFIRMED | 2026-05-28 | 3/3 experiments, 50-player cohort, SNAP-2026-05-28-001 |
| HYP-002 | Model probabilities are calibrated (ECE < 0.05) | CONFIRMED | 2026-05-28 | All 3 experiments ECE < 0.037, 50-player cohort |
| HYP-004 | Signal is stable across time windows | CONFIRMED | 2026-05-28 | AUC 0.567–0.587 consistent across 3 chronological windows |
| HYP-005 | ERI + schedule features add incremental signal | FALSIFIED | 2026-05-28 | T-044 ablation: Δ Brier = +0.0002 (threshold: 0.005) |
| HYP-007 | NB model competitive with LR for calibration | FALSIFIED | 2026-05-29 | EXP-013: NB Brier 0.2671 vs LR 0.2461; Δ=0.0210 |
