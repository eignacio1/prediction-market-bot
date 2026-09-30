# EXP-030 — T4M-PROJ structure enhancer: pre-registration (T-598, GG-320, GG-323)

Written and pushed BEFORE any model fit. No outcome from the sealed holdout has been examined. Only row/game counts were computed to choose the split. EXP-029 belongs to T-596, so this is EXP-030.

## Question
Does a deeper structure than the incumbent's three-scalar binomial (`p_hits_gte_threshold`) produce better-calibrated P(batter reaches threshold hits) on a sealed holdout, scored by T-583's unmodified `run_gate`? Scope: GG-320 only. Nothing here bears on rebanding, deactivating or sizing T4M-PROJ.

## Incumbent (not modified)
`p_hits_gte_threshold(h_so_far, threshold, ba_l10_shrunk, ab_remaining)` from `run_t4_mlb_live.py`, evaluated on the logged inputs. `p_incumbent` in every row is recomputed this way, not read from `p_t4`.

## Population (decision-time filters only)
- Cycle-log rows with ticker-derived game date 2026-07-18..2026-07-30 (first date `ba_l10_shrunk` exists through the last date before the epoch-12 label at 2026-07-31T08:00Z). `logic_epoch` label per row = `epoch_for_timestamp(ts)`.
- Ticker not in `scripts/t4_forbidden_cohort_manifest.json`; `ba_l10_shrunk` and `ab_remaining` present.
- Uncertain rows only: 0 < p_incumbent < 1 (rows already determined carry no information). The permutation control is drawn from this same filtered population.
- Outcome = `actual_hits >= threshold` from T-421 / T-503 decoupled stores, resolved tickers only. `resolution_source` `MLB_R` is mapped to the harness value `boxscore_rederived`. This mapping is an assumption of this experiment.
- Selection caveat: tickers absent from the forbidden manifest are those that were never ledgered. That is a selection-biased population. Results describe this population only.

## Split (fixed by date, from game counts only)
| Split | True game dates | Games | Rows | Tickers |
|---|---|---|---|---|
| train | 07-18..07-21 | 47 | 5,376 | 308 |
| validation | 07-22..07-24 | 20 | 1,426 | 276 |
| sealed holdout | 07-25..07-30 | 40 | 5,658 | 368 |

Harness cutoff = 2026-07-25 (train days strictly precede test days). The candidate receives all pre-cutoff rows and splits them internally by the dates above.

## Candidate (new module, `t4_structure_model.py`)
Class: L2-regularised logistic regression with the incumbent's logit as a fixed offset (a residual model). Inputs: logit(p_incumbent) as offset; threshold; h_needed; ab_remaining; batting_slot bucket (1-3, 4-6, 7-9); inning bucket (1-3, 4-6, 7+); ba_l10_shrunk; batter home/away parsed from the ticker. Regularisation strength C chosen on validation from {0.01, 0.1, 1.0} by Brier gain over the incumbent; ties go to the smaller C. After selection, refit on train+validation with the chosen C. Predictions clipped to [0.001, 0.999].

ADR-0068 factor-class mapping (honest): matchup = none; personnel = ba_l10_shrunk (batter quality) and batting_slot; venue = none (park not used); weather = none; qualitative = none; game state = inning, h_needed, ab_remaining only. This is a shallow candidate. A null here does not speak to deeper matchup, venue or weather trees.

Comparators reported alongside: incumbent, and climatology (train hit rate by threshold).

## Rules fixed in advance
- Primary metric: paired Brier gain (incumbent minus candidate) with the harness's game-clustered bootstrap (n_boot=5000, seed=17). Verdict is the harness verdict, taken unmodified.
- `run_gate` runs exactly once on the holdout. If it raises (for example InadequateCohortError, which needs at least 30 test games where candidate differs from incumbent), the refusal is reported verbatim and satisfied properly. Thresholds are not relaxed and the cohort is not re-cut.
- Permutation control on validation only (never on the holdout): 200 shuffles of train outcomes across tickers within threshold, refit at the chosen C, score validation Brier gain. One-sided. The real validation gain must exceed the 95th percentile of the permuted distribution to count as structure rather than fitting noise. If it does not, the result is reported as such regardless of the holdout verdict.
- If the holdout interval spans zero: NO DETECTABLE DIFFERENCE, stated plainly.
- No change to any parameter above after seeing holdout output. A DEFENSIBLE_IMPROVEMENT verdict yields at most an ADR marked PROPOSED, not an activation.

## Known limits recorded up front
Window is 13 days in July, one season phase. Game-state fields (score, outs, runners, pitcher) are not used, since they exist for only 0.9% of rows (GG-323). Tickers ledgered under the forbidden cohort are excluded, so the population is not the traded population.
