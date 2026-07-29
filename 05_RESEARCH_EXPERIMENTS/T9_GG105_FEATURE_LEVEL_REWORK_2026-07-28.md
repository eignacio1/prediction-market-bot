# T9 — GG-105 Feature-Level Rework (Part A) + Sizing-Bucket Addendum Pointer (Part B)

**Session:** `session/20260729T050047Z-t9-rework` (T-400)
**Date:** 2026-07-28/29
**Precondition gate (confirmed before starting):** `ITERATION_MC_PROGRESS.md` showed A2 DONE (gate=FAIL), B3 DONE (ADR-0048 drafted), C1 BLOCKED (precondition A2=PASS not met, GG-140 registered), T8 DONE (open items for T9 registered). All four confirmed present verbatim before proceeding.
**No live epoch bump. No live sizing change. No file touched outside `exp_output/T9_GG105_REWORK/`, this file, `03_DECISIONS/ADR-0048_...md` (addendum §8 only), and `DECISION_LOG.md`.**

---

## Part A — rank-ordering edge search

### A1 — feature-level discrimination check

**Why a new script instead of the D1 harness directly:** `scripts/what_if_harness.py`'s own SCOPE LIMITATION docstring states the resolved-ledger schema (`paper_portfolio_mlb.json` closed_positions) persists only the final scalar `model_p`, never the raw per-bet features that fed it — so D1 cannot test whether an *individual raw feature* rank-orders outcomes, only whether a post-hoc transform of the already-computed `model_p` does (which A2/A3, prior session, already showed FAILs). To answer A1's actual question, `scripts/t9_gg105_feature_discrimination.py` joins MAIN's real resolved ledger to the historical C2 feature matrix pulled from the VPS (`exp_output/MLB/mlb_feature_matrix.csv`, 17,145 rows, 2026-03-26 onward) on `(player_id, game_date)` — the only join key both sides carry — reusing the exact tercile/Fisher-exact machinery from `exp_retrospective_core.edge_monotonicity()`, keyed on the raw feature value instead of `fee_net_edge` and tested against the reconstructed underlying event indicator (`1 iff (direction=="YES")==(outcome=="WIN")`, same convention as `_calibration_records()`) instead of bet WIN/LOSS, since WIN/LOSS flips sign with bet direction while the underlying event does not.

**Join integrity:** 143 of 17,002 unique `(player_id, game_date)` keys (~0.8%) in the feature matrix are ambiguous — genuine doubleheader-style duplicates with two different `temporal_cutoff` snapshots and differing `ba_l10`/`ba_l10_shrunk` values, and the resolved ledger carries no `game_id` to disambiguate which game a bet belongs to. These were **dropped from the feature index entirely** (not guessed), matching the discipline `what_if_harness.py`'s own overrides join already applies to unmatched/ambiguous keys. Of MAIN's 436 deduplicated resolved positions, 313 (72%) matched a feature row; 123 (28%) had no feature-matrix row for that `(player_id, game_date)` at all (older/edge-case ingestion gaps) and were excluded, not imputed.

**Result (n=313, alpha=0.10, same convention as `edge_monotonicity()`):**

| Feature | Verdict | Fisher p |
|---|---|---:|
| ba_l10, ba_l10_shrunk, slg_l10, obp_l10, ops_l10, h_l10_mean, k_rate_l10, hr_rate_l10, days_rest, park_factor_hits | INCONCLUSIVE | 0.17–0.78 |
| is_home_game, b2b_flag | INCONCLUSIVE | 0.50 |
| bb_rate_l10 | **ANTI-PREDICTIVE** (not significant at 0.05) | 0.072 |
| **ba_l10_shrunk − mip** (market-relative proxy for the live model's own edge logic) | **ANTI-PREDICTIVE** | **<0.0001** (event rate 0.663 bottom tercile → 0.286 top tercile) |

**Two data-gap findings, not modeling findings:**
- **order-slot** (requested by A1) has no pregame C2 column at all — `batting_slot` exists only as a T4 live in-game field (CLAUDE.md's T4 thesis), not a MAIN pregame feature. Untestable from this data source without new C2 work.
- **matchup/opponent** (requested by A1) is a **dead column set**: `opp_sp_era_l5`, `opp_sp_k9_l5`, `opp_sp_bb9_l5`, `opp_runs_allowed_l10` are 100% blank across **all 17,145 rows** of the full historical matrix (not just the 313 joined) — scaffolded into the C2 schema, never populated by ingestion. `opp_sp_is_known` is present but is a hardcoded constant `0.0` in every row. **This should be registered as its own governance gap (GG-141, below) — the single most theoretically load-bearing candidate category (pitcher-matchup quality) has never actually been computed.**

**Reading:** no individual raw pregame feature in the current C2 output shows positive monotonic signal against real resolved outcomes. The one signal that *is* strong (`ba_l10_shrunk − mip`, p<0.0001) is exactly backwards — confirming GG-105/GG-140's defect lives at the feature/model layer, one level below where A2/A3 (calibration-transform) had already shown it, not merely surviving through calibration.

### A2 — candidate proposal

A fixed-weight blend of `model_p` toward `mip` is **provably** still a monotonic transform of the existing (broken) edge: if `new_p = a·model_p + (1-a)·mip`, then `new_edge = new_p - mip = a·(model_p - mip) = a·old_edge` — a positive rescaling that cannot change rank order. This closes off the "just shrink harder toward market" instinct as a non-starter, by the same logic the session premise already applies to Platt/isotonic/temperature.

Given A1, the only two live levers are:
1. **New signal (opponent-pitcher matchup quality)** — the theoretically strongest candidate, but **not scoreable this session**: the underlying data is 100% absent historically (A1's dead-column finding). This is a C2 data-engineering task, not a same-session modeling exercise.
2. **A genuinely non-monotonic model-class change, scoreable today** — an L2-regularized logistic regression fit directly on reconstructed outcomes (not a transform of the live `model_p` at all), using `bb_rate_l10` (the only feature with even a weak independent read) plus its interaction with `ba_l10_shrunk`, with `days_rest`/`park_factor_hits`/`is_home_game` as controls. Out-of-fold (5-fold CV, seed=17) predictions used throughout to avoid in-sample overfit on n=313. **Flagged going in as a weak-prior candidate** (`bb_rate_l10` didn't clear p<0.05 in A1) — proposed because it's the only scoreable lever left, not because it was expected to pass.

Script: `scripts/t9_gg105_a2_a3_candidate.py`. Overrides written: `exp_output/T9_GG105_REWORK/a3_candidate_overrides.json` (312 keys — one player_id|game_date|threshold collision across two positions, harmless, D1 harness matched on the resulting keyset).

### A3 — score via D1 harness

`python3 scripts/what_if_harness.py --book t1t2t3 --overrides-file exp_output/T9_GG105_REWORK/a3_candidate_overrides.json` — full report: `exp_output/T9_GG105_REWORK/a3_d1_report.json`.

| Cohort | n | Verdict | Fisher p | Brier | ECE |
|---|---:|---|---:|---:|---:|
| Baseline (raw model_p, this matched subset) | 313 | INCONCLUSIVE | 1.0000 | 0.2244 | 0.0545 |
| **A2 candidate** | 313 | **ANTI-PREDICTIVE** | **0.0000** | 0.2527 | 0.0196 |

Candidate terciles (by candidate `fee_net_edge`, bottom→top): win rate 0.702 / 0.375 / 0.352 — inverted, and more severely than baseline. Calibration slope collapses to essentially 0 (b=-0.002, CI [-0.91, 1.11]). Brier (0.2527) is worse than `ADR-0046`'s `BRIER_BASELINE_MLB=0.2190` (ECE alone, 0.0196, would have cleared `ECE_BASELINE_MLB=0.0680`, but Brier and the monotonicity verdict both fail decisively).

**Gate: FAIL.** Do not deploy — per instruction, and per the result. The weak prior did not survive contact with out-of-fold scoring; if anything the interaction concentrated noise into a worse inversion than the raw model_p shows on this same subset.

### A4 — MAIN vs T4 strategic recommendation

**Evidence assembled:**
- GG-140 (prior sessions): monotonic recalibration (Platt, isotonic) exhausted — cannot fix an inverted rank ordering by construction.
- A1 (this session): no individual raw C2 feature shows positive signal; the model's own edge-generation logic, tested directly against raw features, is strongly anti-predictive (p<0.0001) — the defect is upstream of calibration, confirmed one level deeper.
- A2/A3 (this session): the one cheaply-scoreable non-monotonic candidate also FAILs, decisively (worse inversion than baseline, worse Brier).
- The one theoretically strong remaining lever (opponent-pitcher matchup quality) is blocked on a live C2 data gap, not a modeling question — real but slow-moving work, not iterable via D1 today.
- MC survivable-edge frontier (`MC_SURVIVABLE_EDGE_FRONTIER_2026-07-23.md`, cited in ADR-0048 §1.2): MAIN needs **+0.169%/bet** just to hold 1yr P(kill) ≤ 10% at current sizing — ~27× the best-ever observed cohort mean (+0.006%/bet) — i.e. MAIN's real variance geometry alone is close to ruin-guaranteed *regardless of edge sign* (GG-135). T4's real σ is ~26× smaller; it is edge-limited, not ruin-limited (frontier ≈ -0.0005%/bet — it already survives near-zero edge structurally).

**Recommendation: no-go on further MAIN/T1 rank-ordering modeling iteration under the current C2 feature set; go on shifting near-term alpha-development effort to T4.** Every cheap lever on MAIN (monotonic recalibration, and now a scoreable non-monotonic feature interaction) has been tried against the real ledger and failed, and the one lever that remains theoretically credible (matchup quality) requires new data engineering, not more modeling attempts against data that has already been exhausted. Compounding this, MAIN's variance geometry means even a hypothetical future MAIN fix would need to clear a ~27× bar just to survive sizing, versus T4's structurally much lower bar. This does not mean stop pursuing the C2 matchup-data gap — it should be registered and picked up on its own timeline — but it should not be the thing another modeling session spends cycles on this week.

**Parallel, lower-priority track:** register the C2 matchup-data gap (opponent starting pitcher quality never populated, A1 finding) as its own governance item so it doesn't silently disappear — this is genuinely new information a future feature-engineering session could act on, distinct from "try another transform of what we already have."

---

## Part B — sizing-bucket foundation

**Already substantially built by a prior session (Window B3, `session/20260728T234000Z-b3-sizing`):** `03_DECISIONS/ADR-0048_edge-conditional-variance-aware-sizing.md`, PROPOSED, operator-confirmed on its two flagged judgment calls 2026-07-28. It already satisfies:
- **B-1** (sizing as `f(validated_edge × inverse_variance)`, boundaries read off the B2 frontier, not invented): §3 lookup tables for both MAIN and T4, keyed on validated per-bet edge.
- **B-3** (hard activation gate baking in the Part-A-equivalent + B2 frontier + D2 MC precondition): §4-§5, `kelly_fraction(band) = 0 unless GG-105 monotonicity gate has passed for that band`, plus a mandatory fresh D2 (`mc_empirical_bootstrap.py`) re-run before any reactivation.
- **B-4** (T4-first rationale from the MC): §3 T4 table + narrative — T4 is "edge-limited, not ruin-limited," ~26× lower σ than MAIN, large sizing headroom once its own GG-105 gate passes.

**Gap found and closed this session (B-2):** ADR-0048's §3 aux-cascade only specified Kelly fraction and drawdown-kill width. It did not address the per-bet exposure cap, the daily-loss breaker, or the ADR-0026 portfolio deployment invariant — all three explicitly required by this task's B-2. Rather than duplicate or rewrite an already operator-reviewed PROPOSED document, appended **§8 (Addendum, 2026-07-28)** to ADR-0048 specifying:
- **8.1** — per-bet exposure cap is a market-depth ceiling (`min(kelly_stake, max_single_event_exposure_usd)`), independent axis from Kelly fraction, but must be re-checked for bindingness at the table's higher-multiplier rows as bankroll grows.
- **8.2** — the daily-loss breaker (`MAX_DAILY_LOSS_PCT=0.15`) is not automatically correct at higher Kelly/cadence multipliers (daily variance scales with both); any future D2 reactivation run above the default table rows must simulate the daily P&L distribution and re-derive the breaker width if 0.15 no longer sits at a sane percentile.
- **8.3** — the ADR-0026 deployment invariant is a cross-band aggregate, not a per-band table row, but binds tighter as the cadence multiplier rises (more simultaneous, larger positions); any row with cadence multiplier > 1.0× requires a portfolio-level capital-in-flight simulation against `max_portfolio_deployment_pct` in the same D2 re-run.

No live wiring, no epoch bump, no parameter change — addendum text only, same PROVISIONAL/NON-OPERATIONAL status as the rest of ADR-0048.

---

## Artifacts

- `scripts/t9_gg105_feature_discrimination.py` (A1)
- `scripts/t9_gg105_a2_a3_candidate.py` (A2/A3)
- `exp_output/T9_GG105_REWORK/a1_report.json`, `a3_candidate_overrides.json`, `a3_d1_report.json`
- `03_DECISIONS/ADR-0048_edge-conditional-variance-aware-sizing.md` §8 (addendum)
- This file
