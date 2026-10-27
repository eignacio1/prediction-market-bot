# W87.1 — every scorer reconciled with the quant core (Part A)

**Pillar: PROOF.** Measure: scoring paths reconciled with the core 2 → 9 (named below). Scoring infrastructure, not a factor (ADR-0075 stage/granularity index do not apply).
Harness: `scripts/quant_reconcile.py`; pinned by `tests/test_w87_quant_reconcile.py`. Input: one frozen seeded snapshot (seed 7; 511 probabilities incl. 0, 1, 0.1/0.2/0.3/0.5/0.7/0.9, 0.57, 0.58, 0.29; 40 seeded clusters; 2,000 random quotes). TOL = 1e-6.
Verdicts: MATCH (re-pointable) · ROUNDING (old path rounds output to 4 dp; equal after rounding) · DEFINITION (two definitions, both written down, pre-registration's named) · BUG (none found).

## Reconciliation table (old value vs core value, same input)
| path | case | old | core | diff | verdict | reason |
|---|---|---|---|---|---|---|
| pregame_shadow/fees.py e_net | 2000 random quotes, max over YES and NO | 0 | 0 | 0 | MATCH | same formula p - ask - fee(ask) / (1-p) - (1-bid) - fee(1-bid) |
| scripts/nhl_shadow_eval.py edge_net | 2000 random quotes, max over YES and NO | 0 | 0 | 0 | MATCH | same formula p - ask - fee(ask) / (1-p) - (1-bid) - fee(1-bid) |
| t4_fill_status.py cluster_bootstrap_ci | 40 clusters, lo | -0.0468 | -0.0468 | 1.46e-05 | ROUNDING | old path rounds to 4 dp (output formatting); algorithm identical |
| t4_fill_status.py cluster_bootstrap_ci | 40 clusters, hi | 0.329 | 0.329 | 2.5e-05 | ROUNDING | old path rounds to 4 dp (output formatting); algorithm identical |
| pregame_shadow/scoring.py cluster_bootstrap_ci | 40 clusters, lo | -0.0482 | -0.0482 | 0 | MATCH | same percentile algorithm, same B and seed |
| pregame_shadow/scoring.py cluster_bootstrap_ci | 40 clusters, hi | 0.334 | 0.334 | 0 | MATCH | same percentile algorithm, same B and seed |
| t4_fill_status.py cluster_bootstrap_ci | edge cases | None for <2 clusters, empty clusters dropped | single cluster returns a point interval | nan | DEFINITION | re-point must keep the wrapper's guard (<2 non-empty clusters -> None); E2/E3 print None today |
| analytics/calibration_diagnostics.py ece/reliability/murphy | 5 bins; ECE, reliability, resolution, bin counts | 0 | 0 | 0 | MATCH | same int(p*bins) binning with p=1 folded into the top bin |
| analytics/calibration_diagnostics.py ece/reliability/murphy | 10 bins; ECE, reliability, resolution, bin counts | 0 | 0 | 0 | MATCH | same int(p*bins) binning with p=1 folded into the top bin |
| analytics/calibration_diagnostics.py ece/reliability/murphy | 20 bins; ECE, reliability, resolution, bin counts | 0 | 0 | 0 | MATCH | same int(p*bins) binning with p=1 folded into the top bin |
| analytics/calibration_diagnostics.py ece/reliability/murphy | 25 bins; ECE, reliability, resolution, bin counts | 0 | 0 | 0 | MATCH | same int(p*bins) binning with p=1 folded into the top bin |
| analytics/calibration_diagnostics.py irls_logistic | slope, snapshot incl. p=0 and p=1 | 0.156 | 0.156 | 1.84e-05 | DEFINITION | logit clamp EPS=1e-9 on p=0 and p=1 rows differs from the core's clamp, and the stopping tolerance differs; both fit the same model. The pre-registrations use the core's (slope, intercept) |
| analytics/calibration_diagnostics.py irls_logistic | intercept, snapshot incl. p=0 and p=1 | 0.483 | 0.483 | 0.000131 | DEFINITION | logit clamp EPS=1e-9 on p=0 and p=1 rows differs from the core's clamp, and the stopping tolerance differs; both fit the same model. The pre-registrations use the core's (slope, intercept) |
| c7_monitoring/monitor.py _compute_ece | 10 bins, snapshot incl. 0.3/0.7/0.57/0.58 | 0.111 | 0.113 | 0.00274 | DEFINITION | np.linspace edges are inexact floats (linspace(0,1,11)[3] = 0.30000000000000004), so p=0.3 lands in bin 2 here and bin 3 in the core's int(p*n). Matters for probabilities rounded to 0.1/0.01. Not re-pointed: live drift ladder, c7 not owned by 87.1 |
| scripts/demo_fill_forward_report.py _clustered | cluster ratio-estimator mean | 0.142 | 0.142 | 0 | MATCH | same pooled mean |
| scripts/demo_fill_forward_report.py _clustered | one-sided 95% half-width: analytic vs bootstrap | 0.16 | 0.17 | 0.0104 | DEFINITION | analytic ratio-estimator (Z=1.645, one-sided) vs percentile bootstrap (two-sided 95%). Both cluster by game. The forward-test rule in its own pre-registration uses the analytic one; keep it |
| pregame_shadow/scoring.py _best_side_e_net | 4000 quote/outcome pairs; rows where the side differs | 2 | 0 | 2 | DEFINITION | scoring picks the side by GROSS edge (p-ask vs (1-p)-(1-bid)); core net_edge picks by NET edge. The pre-registered EXP-036/037 realised E_net uses the gross choice; keep it |

## Paths with no independent computation
- `c5_execution/shadow_flat_stake.py`: reads the runner's logged `e_net_yes_k007` / `e_net_no_k007` and takes the larger side with gate > 0.0. It computes no edge itself; the logged values come from `pregame_shadow/fees.e_net`, which MATCHES the core (row 1). Same side rule as the core (larger NET edge). Nothing to register; order logic untouched.

## Definition differences (both written down; which the pre-registrations use)
1. **Monitor ECE** (`c7_monitoring/monitor.py`): `np.linspace` bin edges are inexact floats, so p = 0.3 (and 0.7 etc.) falls one bin lower than the core's `int(p * n)`. Snapshot ECE 0.1107 vs 0.1134. The ADR-0004 drift ladder uses the monitor's; every pre-registered calibration number uses the core's. GG-1180.
2. **IRLS logistic** (`analytics/calibration_diagnostics.irls_logistic`): slope/intercept differ by 1.8e-5 / 1.3e-4 on p = 0 and 1 rows (logit clamp EPS=1e-9 vs the core's clamp, stopping tolerance). Pre-registrations use the core's `slope_intercept`. GG-1181.
3. **Realised E_net side choice** (`pregame_shadow/scoring._best_side_e_net`): picks the side by GROSS edge; core `net_edge` by NET edge. Differs on 2 of 4,000 quote/outcome pairs on the snapshot. EXP-036/037 realised E_net uses the gross choice. Kept. GG-1182.
4. **Forward-test CI** (`scripts/demo_fill_forward_report`): analytic game-clustered ratio estimator, one-sided Z = 1.645, vs the core's percentile bootstrap. Means are equal (diff 0). The forward-test rule uses the analytic one. Kept. GG-1183.
5. **t4_fill_status edge cases**: `None` below 2 non-empty clusters; the core returns a point interval for one cluster. Any re-point keeps the guard.

## Bugs
None. Nothing in the core needed fixing.

## GG-1100
`distance_to_optimum.d3()` now reads the pre-registration files themselves: dirs `12_EXPLORATORY/`, `03_DECISIONS/`, `05_RESEARCH_EXPERIMENTS/`; counts a file whose name or title says "challenger" and whose Status line (else title) opens PROPOSED, ACCEPTED or FROZEN. D3 on this checkout: **1 → 3** (EXP-040, EXP-041, NFL QB-shrunk challenger). Tests: `test_d3_reads_prereg_files_frozen_and_title_status`, `test_d3_on_this_repo_counts_exp041`.

## Part B: re-pointed and absorbed (PR "W87.1 Part B")

Rule: re-point only where Part A said MATCH (< 1e-6); one path per commit; each has an old-vs-new equality test on a frozen seeded snapshot (`tests/test_w87_repoint.py`); the old function stays as a thin wrapper.

| # | Path | Now calls | Test | Result |
|---|---|---|---|---|
| B1 | `pregame_shadow/fees.fee_k007` | `quant.money.fee_k007` | 1,001 prices, bit-equal | re-pointed |
| B2 | `scripts/nhl_shadow_eval.edge_net` | `quant.money.net_edge` when k == 0.07 (other k keeps the local formula) | 2,000 quotes, <1e-12; k=0.035 unchanged | re-pointed |
| B3 | `pregame_shadow/scoring.cluster_bootstrap_ci` | `quant.inference.cluster_bootstrap` | 40 clusters, B=2000 and B=300, tuple-equal to a frozen copy of the old code; empty -> NaN | re-pointed |

Absorbed into the core (`src/prediction_market_bot/quant/`, known-answer tests in `tests/test_w87_quant_absorb.py`; the `12_EXPLORATORY` files are now wrappers exposing the same function objects):
- `ladder.py` (parse_ticker, survival_points, fit_normal, keynum pmf/survival, fit_keynum, decompose),
- `coherence.py` (fee, monotonic, adjacent_monotonic, same_contract, exclusive_set, dominates, sized),
- `dtmc.py` (bin_of, estimate, summarise, cluster_bootstrap, simulate).

Each technique: known-answer test (above); applies/does-not-apply is in each function's docstring (carried over from 86.2/86.3); measured result on our data is in `ladder_implied/results_W86.md` and `fill_dtmc/results_W86.md` (unchanged here, this block adds no new measurement).

### NOT re-pointed, and why
- `t4_fill_status.cluster_bootstrap_ci`: ROUNDING row. Matches only after its 4-dp rounding and it has guards the core lacks (None for < 2 clusters, drops empty clusters). A safe wrapper is possible but it feeds the T4 fill report; deferred to a follow-up (not done for time, not for a numerical reason).
- `analytics/calibration_diagnostics.ece / reliability / brier_murphy`: MATCH, deferred for time (ceiling), not for a numerical reason.
- `demo_fill_forward_report._clustered`: pooled mean matches, but its CI is the analytic one the forward-test rule uses (GG-1183); kept.
- `c7_monitoring/monitor._compute_ece` (GG-1180), `irls_logistic` (GG-1181), `scoring._best_side_e_net` (GG-1182): DEFINITION differences, registered, left alone.
- Not examined in Part A and still unexamined: `run_sensitivity_tests._ece`, `train_model_v2b._compute_ece`, `ab_harness_t4._brier`, `train_nfl_pregame.brier`, `t4_structure_model.brier_gain`.

Note: `quant/ladder.py` needs scipy. scipy is not declared in `pyproject.toml` (it arrives through scikit-learn); nothing else in `src/` imports it. Nothing imports `quant.ladder` from a runner.

Box read-back: no runner imports the re-pointed functions except through the nightly shadow evaluators; the post-merge read-back is recorded in the handoff.
