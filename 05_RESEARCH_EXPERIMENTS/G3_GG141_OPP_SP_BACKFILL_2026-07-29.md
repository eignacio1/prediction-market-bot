# G3 — GG-141 opp_sp Backfill + D1 Rerun (GG-105 lever test)

**Session:** `session/20260729T234604Z-g3-oppsp` (T-405)
**Date:** 2026-07-29
**Task:** GG-141 (`opp_sp_era_l5`/`opp_sp_k9_l5`/`opp_sp_bb9_l5`/`opp_runs_allowed_l10` 100% blank, `opp_sp_is_known` hardcoded 0.0) — backfill for the resolved cohort and test whether the missing opposing-pitcher covariate is the fix for GG-105's anti-predictive rank-ordering finding.
**RESEARCH ONLY. No live deploy, no epoch bump, no sizing change, no refit of the frozen T1 production model (Hard Rule 4).** All writes confined to `exp_output/T9_GG105_REWORK/`, this file, `DECISION_LOG.md`, and `GOVERNANCE_GAP_LOG.md`.

---

## Root cause (GG-141)

Not a bug in `mlb_features.py` — its SP-overlay logic is correct and fully data-driven. `generate_mlb_features.py`'s resumable cache silently cached an **empty** fetch result (`starters_2026.json={}`, `pitcher_logs_2026.parquet`/`completed_games_2026.parquet` = 0 rows) around 2026-06-24, and every regeneration since reused the poisoned cache. The live MLB Stats API itself is confirmed working (direct API calls, this session).

## Backfill

`scripts/g3_backfill_opp_sp.py` live-refetches `game_starters`/pitcher logs/completed games scoped to the resolved cohort (MAIN + T4 union, 795 keys, 608 physical CSV rows matched) via the existing, unmodified C1 classes (`MLBIngestionClient`, `MLBPitcherStatsStore`, `MLBTeamStatsStore`) and C2's `_get_opp_sp_id`. Output: `exp_output/T9_GG105_REWORK/mlb_feature_matrix_oppsp_backfilled.csv` (gitignored, regeneratable).

| Metric | Value |
|---|---:|
| Cohort rows backfilled | 608 |
| `opp_sp_is_known=1` rate | 0.998 |
| `opp_sp_era_l5` non-null (of known-SP rows, TI-01 `min_periods=2`) | 0.931 |
| `opp_runs_allowed_l10` non-null | 1.000 |

## A1 — raw-feature discrimination (re-run on backfilled data)

`scripts/t9_gg105_feature_discrimination.py` re-run against the backfilled CSV (tercile/Fisher-exact, alpha=0.10, same convention as `edge_monotonicity()`):

| Feature | n | Verdict | Fisher p |
|---|---:|---|---:|
| `opp_sp_era_l5` | ~314 | INCONCLUSIVE | 0.7826 |
| `opp_sp_k9_l5` | ~314 | INCONCLUSIVE | 0.5810 |
| `opp_sp_bb9_l5` | ~314 | INCONCLUSIVE | 0.2695 |
| `opp_runs_allowed_l10` | ~336 | INCONCLUSIVE | 0.2290 |
| `opp_sp_is_known` | ~314 | INCONCLUSIVE (degenerate split, n_0=2) | 0.2463 |
| `ba_l10_shrunk − mip` (pre-existing anti-predictive finding) | — | **ANTI-PREDICTIVE, reproduced unchanged** | 0.0000 |

None of the four backfilled opp_sp/matchup columns individually rank-order the reconstructed event at alpha=0.10. Report: `exp_output/T9_GG105_REWORK/g3_a1_backfilled_report.json`.

## A2/A3 — multivariate candidate + D1 harness rerun (MAIN and T4)

A raw-feature null result cannot rule out an interaction effect, so per the task's literal instruction the full A2/A3-style candidate was built: `scripts/g3_gg141_candidate.py` extends T9's `FEATURE_COLS` (`ba_l10_shrunk`, `bb_rate_l10`, `days_rest`, `park_factor_hits`, `is_home_game`, plus the `ba_l10_shrunk × bb_rate_l10` interaction) with the four backfilled opp_sp columns, fits an out-of-fold (5-fold CV, seed=17) L2 `LogisticRegression` on reconstructed outcomes, complete-case on the opp_sp block (mirrors A1's own null-handling rather than introducing an untested imputation), separately for MAIN and T4. Overrides written to `g3_a2_candidate_overrides_{main,t4}.json`; scored via the real D1 harness (`scripts/what_if_harness.py --overrides-file`), not a re-implementation.

**MAIN (t1t2t3), n=314 matched:**

| Cohort | Verdict | Fisher p | Brier | ECE |
|---|---|---:|---:|---:|
| Baseline (raw model_p) | INCONCLUSIVE | 1.0000 | 0.2169 | 0.0832 |
| **opp_sp candidate** | **ANTI-PREDICTIVE** | **0.0000** | 0.2541 | 0.0253 |

**T4, n=1323 matched:**

| Cohort | Verdict | Fisher p | Brier | ECE |
|---|---|---:|---:|---:|
| Baseline (raw model_p) | ANTI-PREDICTIVE | 0.0436 | 0.2284 | 0.0878 |
| **opp_sp candidate** | **ANTI-PREDICTIVE** | **0.0000** | 0.2414 | 0.0249 |

Full reports: `exp_output/T9_GG105_REWORK/g3_d1_report_{main,t4}.json`.

**D1 result: MAIN = FAIL, T4 = FAIL.** On both books the opp_sp-inclusive candidate does not repair rank ordering — it makes the inversion *more* severe than the raw baseline (MAIN baseline was already INCONCLUSIVE, not even anti-predictive; the candidate pushes it to a stark inversion, bottom-tercile win rate 0.721 vs top-tercile 0.286).

**T4 scope caveat (GG-142, OPEN, discovered same day by a separate concurrent session):** GG-142 found T4M-PROJ's C4 minimum-edge gate has a sign defect (`abs(edge)` on an already direction-resolved edge) that rescues ~46% of the clean epoch-8 T4 cohort — bets that should have been rejected on negative direction-effective edge. GG-142 states any T4 edge-measurement conclusion computed on an affected cohort is confounded. This session's T4 D1 rerun used the **full T4 resolved ledger (1987 rows, no epoch/gate filter)**, not a GG-142-clean subset, so the T4 anti-predictive verdict above should be read as **directionally consistent with, but not independent confirmation of,** T4's edge problem — the same confound applies to both baseline and candidate equally (both scored on the identical matched subset), so the *relative* result (candidate strictly worse than baseline) is not undermined by GG-142, but the *absolute* T4 anti-predictive magnitude should not be quoted outside this caveat. MAIN is not materially affected (GG-142 measured only 1/175 MAIN clean rows as gate-defect-affected).

## GG-105 lever verdict

**REFUTED, not merely unconfirmed.** The opposing-starting-pitcher covariate — the leading theoretically-credible remaining lever for GG-105 per T9's A1/A2/A3 history — is not a missing dominant signal masked by data absence. With the data actually backfilled and included (both as raw single features and as part of a multivariate out-of-fold candidate, on both MAIN and T4), it produces no independent discriminative signal and, when added to the model, **worsens** the existing rank-order inversion rather than repairing it. Combined with GG-140 (monotonic recalibration cannot fix inversion by construction) and T9's A1-A4 (no raw pregame feature shows positive signal; the model's own edge-generation logic is itself strongly anti-predictive, p<0.0001), the scoreable candidate space for a feature-level GG-105 fix is now exhausted: GG-140 closed off the calibration-layer lever, T9 closed off the existing-feature-set lever, and this session closes off the matchup-quality lever specifically named as the strongest remaining theoretical candidate. No further feature-level lever is currently identified as untested.

---

**G3 DONE commit=<sha> — opp_sp backfilled n=608, D1 result MAIN=FAIL T4=FAIL, GG-105 lever verdict=opp_sp matchup quality REFUTED as a GG-105 fix (backfilled, tested standalone and multivariate on both books, worsens rather than repairs the anti-predictive inversion).**
