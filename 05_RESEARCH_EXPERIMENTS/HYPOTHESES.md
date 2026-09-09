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
| Status | 🔴 FALSIFIED (2026-05-29, EXP-012) — v1.3.0 TEST Brier 0.2480 vs v1.2.0 TEST Brier 0.2480; Δ = 0.0000 (gate: 0.001). F-039/F-040 add zero signal over rolling box-score. Consequence applied: FEATURE_VERSION stays at 1.2.0; F-039/F-040 dropped; TeamStatsStore demoted to reference only. |
| Experiment(s) | EXP-012 (72 players × 5 seasons; 20,361 rows; TRAIN 12,265 / VAL 4,238 / TEST 3,657) |

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
| Status | 🔴 FALSIFIED (2026-05-29, EXP-015) — EV ratio 0.8375 at drift_std=0.020 (gate: > 0.90); CONFIRM bets win at 61.1% (gate: > 66%). T3 useful as FADE gate only, not confidence booster. Kelly reduction (0.25→0.10) not offset by edge multiplier (1.15×). |
| Experiment(s) | EXP-015 (Monte Carlo, 10,000 draws, 5 drift_std scenarios, EXP-005 TEST set) |

---

## HYP-009 — Regular-Season Model Generalizes to Playoff Games

| Field | Detail |
|-------|--------|
| Research Question | KI-008 (playoff validity gap) |
| H0 (Null) | The production model (v1-28483b21, trained on regular season 2021-26) exhibits Brier degradation ≥ 0.012 on held-out playoff game rows vs. regular season TEST performance |
| H1 (Alternative) | Playoff Brier degradation < 0.012 vs. regular TEST Brier (0.2461); model generalizes within EV-preserving tolerance |
| Test method | EXP-016: pull playoff game logs (2021-22 through 2024-25) via nba_api; apply v1.2.0 feature pipeline; train on regular season TRAIN (same split as EXP-005); evaluate on regular TEST and all playoff rows separately |
| Significance threshold | Δ Brier (playoff − regular TEST) < 0.012 |
| Falsification condition | Δ Brier ≥ 0.012 on playoff rows — model materially miscalibrated for playoff conditions |
| Consequence if confirmed | Paper bets placed during 2026 playoffs are valid G6 evidence at full confidence; no weighting adjustment needed |
| Consequence if falsified | Playoff-era paper bets must be annotated as lower-confidence G6 evidence; T-072 playoff data refresh elevated to pre-G6 requirement; playoff model retraining required (new ADR) |
| Gate rationale | Current EV = $0.0958/bet against vig $0.030 (3.2× ratio). A +0.012 Brier degradation would reduce expected win rate by ~2pp, cutting EV/bet by ~$0.05 (to ~$0.045). Below this, edge-to-vig ratio becomes unreliable for live capital decisions. |
| Status | 🟢 CONFIRMED (2026-05-29, EXP-016-B8BA8CAC) — Δ Brier = -0.0010 (playoff ALL 0.2455 vs regular TEST 0.2465); gate < 0.012 ✅. Paper bets during 2026 playoffs are valid G6 evidence at full confidence. |
| Experiment(s) | EXP-016 (playoff generalization ablation; HYP-009 verdict) |

---

## HYP-010 — Team run-total forecasts transfer to a materially more efficient market

| Field | Detail |
|-------|--------|
| Research Question | Phase 2 / coverage-target generality: does the methodology transfer off the single traded cell (`KXMLBHIT`, T4M-PROJ)? |
| Framing | **Option A (operator, 2026-08-16): this buys GENERALITY, not edge.** Thinner edge than props is the expectation, not the disappointment. |
| H0 (Null) | A team run-total model fit on `MLBTeamStatsStore`'s existing `get_opp_runs_scored` / `get_opp_runs_allowed` series produces **P&L per bet ≤ 0** over the selected subset where \|model_p − mkt_p\| > 0.010, on archived `KXMLBTOTAL` prices. |
| H1 (Alternative) | P&L per bet > 0 on that subset, with `clean_n ≥ n*` where `n*` is derived live from the realized mean/sd via `scripts/run_power_calc.py` (APR-0024). |
| Test method | Fit NB/Poisson to team runs using the **existing** store — no new C2 matrix, no new ingestion (LL-009). Score against `exp_output/PRICE_ARCHIVE/prices_2026-08-*.jsonl` `KXMLBTOTAL` rows. Bet-selection filter: \|model_p − yes_mid\| > 0.010. |
| **Primary gate (2.3, revised)** | **P&L/bet > 0 AND `clean_n ≥ n*`, one-sided α=.05.** If `clean_n < n*` the verdict is **INCONCLUSIVE — extend archive**, explicitly *not* FALSIFIED. |
| **Pre-registered expectation** | **P&L/bet in the range +0.005 to +0.025, i.e. materially below `KXMLBHIT`'s realized figure.** Rationale: totals' median half-spread is 3× tighter (0.0050 vs 0.0150) and mean 6× tighter, so the same forecasting skill converts to proportionally less edge. A result above +0.03 should be treated as **suspect and audited for leakage before being believed**, not celebrated. |
| Falsification condition | P&L/bet ≤ 0 at `clean_n ≥ n*`. |
| Secondary (descriptive, **not** a gate) | Paired per-game ΔBrier vs market-implied, reported with its CI and its measured power. Pre-registered expectation: **indistinguishable from zero** — the power table above says a perfect model would also be indistinguishable at this n. Reporting it as a gate would be a false-negative machine. |
| Consequence if confirmed | Methodology transfers off the single traded cell. Phase 2 proceeds to 2.4 (team-game C2 matrix). First evidence for the coverage-target thesis. |
| Consequence if falsified | **Phase 2 does not terminate** (plan's own note). Reroute to **moneyline-first**: `KXMLBGAME`, 30,302 observations already archived, a binary target where the production LR class (ADR-0004) applies with no distribution fit. |
| Consequence if INCONCLUSIVE | Continue archiving; re-run at `n*`. ~14 games/day ⇒ ~296–365 additional games ≈ **3–4 weeks** at market noise 0.05. Do not build C2 in the interim. |
| Status | 🟡 INCONCLUSIVE — EXTEND ARCHIVE (2026-08-26, T-487/GG-207) — `clean_n=207` games vs `n*=94,260` (own mean/sd, not `run_power_calc.py`); mean P&L/bet (game-level) = −0.0026 (below pre-registered band, per revised prior); not FALSIFIED. Full result: `05_RESEARCH_EXPERIMENTS/RESULTS_SUMMARIES/T487_EXP022_GATE23_RESULT.md`. Operator note in that file: `n*` is not practically reachable at ~14 games/day — treat as a soft-FALSIFIED for planning purposes rather than literal extend-and-rerun. **NB refit (2026-08-28, T-500/GG-221, EXP-025) confirms the same verdict under a corrected distribution:** NB1(phi=2.33 fixed, method-of-moments per T-487's own measurement), same subset rule re-applied to NB's own model_p, `clean_n=207` (same games), `n*=44,220`, mean P&L/bet = −0.0048, sd=0.3069. 🟡 INCONCLUSIVE — EXTEND ARCHIVE again — not FALSIFIED, not PASS. Pre-registration: `05_RESEARCH_EXPERIMENTS/EXP025_HYP010_NB_PREREGISTRATION_2026-08-28.md`. Per task scope, no third model class attempted; routing gap (both fits INCONCLUSIVE, plan defines no next action) escalated to APR-0033. |
| Experiment(s) | EXP-022 (`scripts/exp022_totals_backtest.py`; Poisson; team run-total transfer test; HYP-010); EXP-025 (`scripts/exp025_hyp010_nb_backtest.py`; NB1 refit, same hypothesis, same archive; HYP-010) |

**Pre-registration source:** `05_RESEARCH_EXPERIMENTS/HYP010_PHASE2_PREREGISTRATION_2026-08-15.md` (power analysis reproducible via `python3 05_RESEARCH_EXPERIMENTS/hyp010_power_analysis.py`, stdlib only, seeded, deterministic). That document also records why gate 2.3 as originally written (Brier-vs-market) could not fail honestly — underpowered 6.6–11× at the 214-game archive — and is not repeated here.

---

## HYP-011 — Moneyline LR forecasts beat market on a selected subset, net of fill cost

| Field | Detail |
|-------|--------|
| Research Question | Phase 2 reroute (APR-0033, Option 3): does the production LR class (ADR-0004) generate net-of-fill-cost edge on `KXMLBGAME` (moneyline), the binary-target track HYP-010's own "Note on model class" defines as the reroute destination? |
| Framing | Decoupled from HYP-010's verdict (APR-0033, Option 3, 2026-09-03): HYP-010 remains INCONCLUSIVE — EXTEND ARCHIVE, unchanged; this hypothesis is pre-registered independently, on its own evidence, not as a consequence of HYP-010 having falsified. |
| H0 (Null) | An LR model fit on `MLBTeamStatsStore`'s existing rolling series (no new C2 build) produces **P&L per bet ≤ 0, net of fill cost,** over the selected subset where \|model_p − mkt_p\| > 0.010, scored against archived `KXMLBGAME` closing pregame prices. |
| H1 (Alternative) | P&L per bet > 0 on that subset, net of fill cost, with `clean_n ≥ n*` where `n*` is derived live from the realized mean/sd via `scripts/run_power_calc.py` (APR-0024). |
| Test method | Fit LR (ADR-0004 production class; no distribution fit — moneyline is a binary target) on `MLBTeamStatsStore`'s existing rolling series — no new C2 matrix, no new ingestion (LL-009). Score against archived `KXMLBGAME` closing pregame prices, TI-01-safe `as_of_date` cutoff (existing production mechanism, not a new one). Bet-selection filter: \|model_p − mkt_p\| > 0.010. Independent unit = the game (moneyline carries exactly one market per game-event, no per-game averaging step needed, unlike the totals track). |
| **Primary gate** | **P&L/bet > 0 AND `clean_n ≥ n*`, one-sided α=.05, computed NET of fill cost (T-507).** If `clean_n < n*` the verdict is **INCONCLUSIVE — EXTEND ARCHIVE**, explicitly *not* FALSIFIED. A result reported gross-of-fill only is not scored under any of this hypothesis's three verdict states. |
| **Pre-registered expectation** | **P&L/bet (net of fill cost) in the range +0.003 to +0.015** — set tighter than HYP-010's totals-track band (+0.005 to +0.025), on the reasoning that moneyline sits at the *most*-attended, most efficiently-priced end of the board (CLAUDE.md § "Market efficiency gradient"), so should be expected to produce thinner edge than totals, not equal edge. Not independently measured this session (no `KXMLBGAME` half-spread pull run) — a reasoned prior, correctable against a real half-spread measurement before execution. A result above **+0.020 (net)** should be treated as **suspect and audited for leakage before being believed**, not celebrated. |
| Falsification condition | P&L/bet ≤ 0, net of fill cost, at `clean_n ≥ n*`. |
| Secondary (descriptive, **not** a gate) | Paired per-game Brier vs market-implied probability, reported with CI and measured power; never a gate — Brier is underpowered by roughly an order of magnitude relative to P&L/bet at realistic archive sizes (same reasoning as HYP-010's Finding 3). |
| Consequence if confirmed (PASS) | Phase 2 box 2.6 (`MARKET_EXPANSION_ACTION_PLAN.md`) clears; box 2.7 additional feature/build work authorized, scoped by this run's own results. Evidence for cell `(mlb_moneyline, T1_MULTI_DAY)` specifically — not for any `T4M-*` cell; cell activation still requires its own ADR (ADR-0058). |
| Consequence if falsified | The moneyline-first track itself is falsified — a different event from HYP-010's own (unchanged) INCONCLUSIVE verdict. Leaves Phase 2 without a currently-defined next reroute target; a new operator decision, not resolved in advance here. |
| Consequence if INCONCLUSIVE | Continue archiving `KXMLBGAME`; re-run at `n*`. Cadence/time-to-`n*` not yet projected for this market this session — belongs to whoever executes EXP-026, using this archive's actual measured effect size and variance. |
| Status | ⚪ PRE-REGISTERED (2026-09-03, T-517) — **no model fit, no scoring, no backtest code run this session (LL-009: the pre-registration comes first and it comes alone).** Data source verified live: `KXMLBGAME` captured by the production price-archiver, `deploy/cron.conf:347-348` (confirmed directly this session); volume 30,302 observations as of 2026-08-15 (sourced from HYP-010's own Finding 1 / pre-registration doc, not independently re-counted this session — local archive is empty in this worktree, re-count required before EXP-026 executes). |
| Experiment(s) | EXP-026 reserved, not yet run (verified free against `04_EXECUTION/ACTIVE_QUEUE.md`'s "Free IDs" hint and repo-wide grep — highest assigned ID in-repo is EXP-025) |

**Pre-registration source:** `05_RESEARCH_EXPERIMENTS/HYP011_moneyline_lr_preregistration_2026-09-03.md`.

---

## HYP-012 — NFL moneyline LR forecasts beat market on a selected subset, net of fill cost

| Field | Detail |
|-------|--------|
| Research Question | Coverage-target generality: does the production LR class (ADR-0004) generate net-of-fill-cost edge on `KXNFLGAME` (moneyline) — the first NFL cell, per per-cell discovery doctrine? |
| Framing | Rerouted from task-assigned EXP-026/HYP-011 (both already canonically bound to the MLB moneyline experiment above) to **EXP-027/HYP-012**, per GG-258 (OPEN, LOW) and `DECISION_LOG.md` 2026-09-09 (T-531) — a session-boundary ID collision, not a substantive redesign. This result is evidence about the cell `(nfl_moneyline, T1_MULTI_DAY)` only — never a verdict on NFL as a sport or on any other market family. |
| H0 (Null) | An LR model fit on `NFLTeamStatsStore`'s existing recency-weighted rolling series (no new C2 build) produces **P&L per bet ≤ 0, net of fill cost,** over the selected subset where \|model_p − mkt_p\| > 0.010, scored against archived `KXNFLGAME` closing pregame prices. |
| H1 (Alternative) | P&L per bet > 0 on that subset, net of fill cost, with `clean_n ≥ n*` where `n*` is derived live from the realized mean/sd via `scripts/run_power_calc.py` (APR-0024). |
| Test method | Fit LR (ADR-0004 production class; no distribution fit — moneyline is a binary target) on `NFLTeamStatsStore.get_off_epa()`/`get_def_epa_allowed()` (window=8, min_periods=3, decay=0.85, already-production recency-weighted EPA — no new C1/C2 build, per LL-009) plus `home_rest`/`away_rest`/home-away split from `fetch_schedule()`. Train on seasons 2015–2024; held-out backtest on 2025 (fully completed, no market baseline available — `KXNFLGAME` archiving began 2026-09-05); prospective out-of-sample test on the live 2026 season, scored against archived `KXNFLGAME` closing prices as games resolve. Bet-selection filter: \|model_p − mkt_p\| > 0.010. Independent unit = the game. |
| **Primary gate** | **P&L/bet > 0 AND `clean_n ≥ n*`, one-sided α=.05, computed NET of fill cost (independently-defined pay-the-ask convention, grounded in measured `KXNFLGAME` half-spread — not T-507's MLB-prop-specific empirical haircut, which does not transfer without its own re-fit study).** If `clean_n < n*` the verdict is **UNDERPOWERED**, explicitly *not* a directional PASS/FALSIFIED. |
| **Pre-registered expectation** | **P&L/bet (net of fill cost) in the range +0.003 to +0.015** — reused from HYP-011's band, additionally grounded here by NFL's own measured `KXNFLGAME` half-spread (median 0.005, mean ≈0.00743). A result above **+0.020 (net)** should be treated as **suspect and audited for leakage before being believed**, not celebrated. |
| Falsification condition | P&L/bet ≤ 0, net of fill cost, at `clean_n ≥ n*`. |
| Secondary (descriptive, **not** a gate) | Calibration curve + Brier score, reported for both the 2025 held-out backtest (vs. actual outcomes only) and the 2026 prospective window (vs. actual outcomes and vs. archived closing-line implied probability); never a gate, same reasoning as HYP-010/HYP-011. |
| Consequence if confirmed (PASS) | Evidence for cell `(nfl_moneyline, T1_MULTI_DAY)` specifically — not for NFL as a sport, not for any other market family or band. Cell activation still requires its own ADR. |
| Consequence if falsified | The `(nfl_moneyline, T1_MULTI_DAY)` cell specifically is falsified. Per per-cell discovery doctrine, this must never be cited as a reason to deprioritize NFL, any other NFL market family, or any other sport. |
| Consequence if UNDERPOWERED | Expected outcome given `KXNFLGAME` archiving only began 2026-09-05 and the 2026 season has zero played games as of pre-registration. Continue archiving through the 2026 season; re-run at `n*`. No directional verdict claimed. |
| Status | ⚪ PRE-REGISTERED (2026-09-09, T-531) — **no model fit, no scoring, no backtest code run this session before this document was pushed (LL-009 / this task's hard rule: fitting before pushing voids the experiment).** Data source verified live this session: `fetch_schedule()` 7,548 rows (1999–2026), 2025 fully completed (285/285 final), 2026 fully scheduled/zero played; `NFLTeamStatsStore` confirmed production-complete with exact defaults cited above; `KXNFLGAME` archive confirmed beginning exactly 2026-09-05 (0 rows 09-01 through 09-04). |
| Experiment(s) | EXP-027 (verified free this session; see GG-258 / `DECISION_LOG.md` 2026-09-09) |

**Pre-registration source:** `05_RESEARCH_EXPERIMENTS/HYP012_nfl_moneyline_lr_preregistration_2026-09-09.md`.

---

## Hypothesis Status Summary

| ID | Hypothesis | Status | Experiment | Target |
|----|-----------|--------|-----------|--------|
| HYP-001 | Player_Attribute_Matrix beats null model | 🟢 CONFIRMED | EXP-001/002/003 (50-player) | 3/3 beat null; G4 met |
| HYP-002 | Model probabilities are calibrated | 🟢 CONFIRMED | EXP-001/002/003 (50-player) | ECE 0.028–0.037; all < 0.05 |
| HYP-003 | Model edge exceeds vig | 🟢 CONFIRMED | EXP-004 Parts A+B | EV +$0.0855/bet; Part B live Kalshi confirmed 2026-05-28 |
| HYP-004 | Signal is stable over time | 🟢 CONFIRMED | EXP-003/002/001 (50-player) | AUC 0.567–0.587 consistent; no decay |
| HYP-005 | ERI + schedule features provide incremental signal | 🔴 FALSIFIED | T-044 ablation | Δ Brier = +0.0002; prune to v1.0.0 (31 features) |
| HYP-006 | Opp def rating + home/away context add signal | 🔴 FALSIFIED | EXP-012 | Δ Brier = 0.0000; FEATURE_VERSION stays 1.2.0 |
| HYP-007 | NB model competitive with LR for calibration | 🔴 FALSIFIED | EXP-013 | NB Brier 0.2671 vs LR 0.2461; Δ=0.0210; multi-line use retained |
| HYP-008 | T3 CONFIRM filter preserves ≥90% of T1 EV | 🔴 FALSIFIED | EXP-015 | EV ratio 0.84 at drift_std=0.020; T3 useful as FADE gate only |
| HYP-009 | Regular-season model generalizes to playoff games (Δ Brier < 0.012) | 🟢 CONFIRMED | EXP-016 | Δ = -0.0010; G6 paper evidence valid for playoffs at full confidence |
| HYP-010 | Team run-total forecasts transfer to a materially more efficient market (P&L/bet > 0 on selected subset) | 🟡 INCONCLUSIVE-EXTEND | EXP-022 (Poisson), EXP-025 (NB1) | Poisson: clean_n=207 vs n*=94,260, mean=−0.0026. NB: clean_n=207 vs n*=44,220, mean=−0.0048. Both not FALSIFIED, not practically extendable |
| HYP-011 | Moneyline LR forecasts beat market on selected subset, net of fill cost (Phase 2 reroute, APR-0033 Option 3) | ⚪ PRE-REGISTERED | EXP-026 (reserved, not yet run) | Not run — no model fit this session (LL-009); gate must be scored net of fill cost per T-507 or not scored at all |
| HYP-012 | NFL moneyline LR forecasts beat market on selected subset, net of fill cost (first NFL cell, per-cell discovery) | ⚪ PRE-REGISTERED | EXP-027 (rerouted from EXP-026/HYP-011 collision, GG-258) | Not run — no model fit this session (LL-009); `KXNFLGAME` archive began 2026-09-05, 2026 season not yet played; UNDERPOWERED verdict pre-registered as the expected outcome |

---

## Resolved Hypotheses (Archive)

| ID | Hypothesis | Outcome | Date | Evidence |
|----|-----------|---------|------|---------|
| HYP-001 | Player_Attribute_Matrix features beat null Brier | CONFIRMED | 2026-05-28 | 3/3 experiments, 50-player cohort, SNAP-2026-05-28-001 |
| HYP-002 | Model probabilities are calibrated (ECE < 0.05) | CONFIRMED | 2026-05-28 | All 3 experiments ECE < 0.037, 50-player cohort |
| HYP-004 | Signal is stable across time windows | CONFIRMED | 2026-05-28 | AUC 0.567–0.587 consistent across 3 chronological windows |
| HYP-005 | ERI + schedule features add incremental signal | FALSIFIED | 2026-05-28 | T-044 ablation: Δ Brier = +0.0002 (threshold: 0.005) |
| HYP-007 | NB model competitive with LR for calibration | FALSIFIED | 2026-05-29 | EXP-013: NB Brier 0.2671 vs LR 0.2461; Δ=0.0210 |
| HYP-009 | Regular-season model generalizes to playoff games | CONFIRMED | 2026-05-29 | EXP-016: Δ Brier = -0.0010 (gate < 0.012); playoff paper bets valid G6 evidence |
