# EXP-028 — Pre-game MLB hit-prop model on the frozen 2024–2026 matrix — PRE-REGISTRATION

**Task:** T-594 (Wave 41, pregame-model-mlb) · **Date:** 2026-09-30 · **Status:** FROZEN on push. No model has been fit at the time of writing.
**Owner files this wave:** `src/prediction_market_bot/c3_forecasting/pregame_hits_model.py`, `tests/test_pregame_hits_model.py`, `exp_output/EXP-028/`, this document, the results summary.

> Everything below is fixed in advance. Changing a parameter, split, metric, threshold, feature or verdict label after seeing any result is on the standing DO-NOT list. If a claim below turns out to have been badly specified, the correction goes in the results summary as a stated deviation; the frozen verdict stands.

## 0. Substrate (Deliverable 0)

| item | value |
|---|---|
| file | `exp_output/MLB/mlb_feature_matrix.csv` (gitignored artifact; absent from a fresh worktree) |
| source of the copy | **shared-tree copy, not regenerated** — copied byte-for-byte into this worktree's gitignored `exp_output/MLB/` |
| sha256 | `b2a845a6fb35cfc8c0ec7589524313aeabd20e2140a353409e984f44979114a4` (identical for shared-tree original and worktree copy) |
| shape | 132,184 rows × 45 columns — **matches** the wave brief exactly; header line count 132,185 |
| span | 2024-03-20 → 2026-07-17; `feature_version 1.1.0`; `snapshot_id SNAP-T187A`; `ingested_at` 2026-06-24 → 2026-07-18 |
| predecessor 40.3 / `bfd4c4d` | Commit `bfd4c4d` ("T-592: correct shrunk-coverage range…") is **not on `origin/main` and not on any branch**; it is contained only in worktree `20260930T005212Z-provenance-allowlist`. It is the T4M-PROJ provenance-allowlist work and this wave does not depend on it. **Not landed here; not duplicated** — 41.1's job. |

The module refuses to run unless the sha256 above matches.

## 1. What one row is, and which market family the matrix can serve (Deliverable 1, evidence)

* **One row = one batter-game** (`player_id` × `game_id`): 861 players, 6,318 games, ≈20.9 rows/game, all `Regular Season`. One (player_id, game_id) pair is duplicated (Danny Jansen, game 746942, 2024-06-26, rows `ab=0` and `ab=4`); both rows of that pair are dropped.
* **Columns (45):** identifiers/context (11: `player_id … opponent_team_abbr`); outcome box-score counts (10: `ab h doubles triples hr rbi bb k hbp sf`); provenance (5); `temporal_cutoff`; 9 batter rolling-10 features; `days_rest`, `b2b_flag`; `opp_runs_allowed_l10`; 4 opposing-starter features; `park_factor_hits`; run/version stamps; `train_test_label`.
* **Missingness (share NaN, 2024 / 2025 / 2026):** batter-rolling family 3.8 / 3.9 / 5.8 % (first three games of a player's window); `days_rest` 1.3 / 1.3 / 1.9 %; `opp_runs_allowed_l10` 1.8 / 1.9 / 3.1 %; `opp_sp_era/k9/bb9_l5` 14.2 / 14.0 / 19.5 %; everything else 0 %.
* **Leakage audit (done before design):** recomputing `ba_l10` for a sample player from `h`/`ab` reproduces the stored value on 95.6 % of rows using games *strictly before* the current one, and on 13.9 % when the current game is included ⇒ features are pre-game. The 1,152 rows where `temporal_cutoff == game_date` are doubleheader second games (`days_rest = 0`); none has `temporal_cutoff > game_date`.
* **Market family it can serve:** **player hits, `KXMLBHIT`, threshold ≥1 hit** — and only that. A batter-game table with no lineup slot, no team run totals, no final score, no starting-pitcher handedness cannot price moneyline, run line, game total or team total; those would need team-level scores the matrix does not carry.
* **What it cannot serve — the market baseline.** The matrix has **no market price column**. The only bulk price source, `exp_output/PRICE_ARCHIVE/prices_*.jsonl`, holds KXMLBHIT quotes for game dates **2026-08-01 → 2026-09-30 (60 dates)**; the matrix ends 2026-07-17. **Priced-and-featured overlap = 0 rows.** Paper-ledger `mid_price_at_entry` exists for the dates in between but only for rows the bot bet on (selection-biased) and carries GG-166 outcome corruption; it is not used.

## 2. Hypothesis

**H1.** A logistic model on the pre-game features below assigns P(≥1 hit) more accurately than climatology on games it has never seen (2026-01-01 → 2026-07-17). **H1 is a skill claim, not an edge claim.**
**H-edge.** The model beats the market's implied probability. **This cannot be tested on this substrate (overlap = 0) and is pre-registered as NOT TESTABLE, not as pending.** No outcome of this experiment can therefore be reported as edge.

## 3. Target, population, outcome source

* **Target** `y = 1[h ≥ 1]`, from the matrix's box-score `h` (MLB Stats API, ingested; a `boxscore_rederived`-class source — decoupled from the paper ledger).
* **Population** (all conditions applied identically to every split): drop the duplicated pair above; `ab ≥ 1`; `ba_l10` non-null.
* **Disclosed selection look-ahead:** `ab ≥ 1` is known only after the game. It approximates "was in the lineup and batted", which is when a KXMLBHIT market has a defined outcome; it inflates the base rate (≈0.58 vs ≈0.55 unconditional) and makes *absolute* calibration on this population uninterpretable. It is applied identically to model and every baseline, so paired ΔBrier is valid; absolute Brier is descriptive only.

## 4. Splits (by DATE; holdout named and sealed)

| split | dates (inclusive) | rows (population) | games | base rate |
|---|---|---|---|---|
| TRAIN | 2024-01-01 → 2024-12-31 | 46,514 | 2,386 | 0.5810 |
| VALIDATION | 2025-01-01 → 2025-12-31 | 46,528 | 2,387 | 0.5824 |
| **HOLDOUT (sealed)** | **2026-01-01 → 2026-07-17** | 27,732 | 1,414 | 0.5751 |

Counts above were read from the matrix by row filter only (no fitting). The holdout is **not virgin data**: `train_test_label = TEST` in the matrix marks the same 2026 window as the test set of the earlier T-183 model, and prior sessions have looked at 2026 aggregates. What is guaranteed for *this* experiment is that no model, hyperparameter, feature or threshold here is selected using it. It is scored **exactly once**, by the frozen final model.

Protocol: (a) fit each candidate `C` on TRAIN, choose `C` by VALIDATION Brier; (b) **refit on TRAIN+VALIDATION** with the chosen `C`; (c) score the holdout once.

## 5. Features, mapped to `01_SPEC/PREGAME_FEATURE_ARCHITECTURE.md` factor classes

| class | populated? | features |
|---|---|---|
| **player** | yes | `ba_l10_shrunk` (ADR-0047 form; raw `ba_l10` excluded as collinear), `slg_l10`, `obp_l10`, `h_l10_mean`, `k_rate_l10`, `bb_rate_l10`, `hr_rate_l10`, and derived `ab_l10_mean` = mean of the player's previous ≤10 games' `ab`, `shift(1)`, `min_periods=3`, ordered by (`game_date`, `game_id`) — a role/lineup-slot proxy. (`ops_l10` excluded: exact `slg+obp` collinearity.) |
| **team** | thinly | `opp_runs_allowed_l10` (opponent run prevention). Own-team strength: **not populated.** |
| **matchup** | partially | `opp_sp_era_l5` (clip 0–15), `opp_sp_k9_l5` (clip 0–20), `opp_sp_bb9_l5` (clip 0–15) + one indicator `opp_sp_missing` (1 when the three are NaN; they co-miss). Platoon (M1), lineup slot (M5), bullpen (M4): **not populated.** |
| **external** | partially | `is_home_game`, `days_rest` (clip 0–10), `b2b_flag`. `park_factor_hits` **deliberately excluded** (ADR-0064 PROPOSED; the governance scan lists the park-factor defect as unfixed). Weather, travel, umpire: **not populated.** |
| **sport** | intercept only | the LR intercept is the league base rate. |
| **qualitative** | **no** | no source or encoding for MLB. |

Imputation: TRAIN(+VAL at refit) column medians for NaNs in continuous features; `opp_sp_missing` carries the missingness signal. Standardise with train(+val) mean/sd. No interactions, no feature selection.

## 6. Model class and baselines

* **Model:** L2 logistic regression (`sklearn`, `lbfgs`, `max_iter=1000`), `C ∈ {0.01, 0.1, 1, 10}` chosen by VALIDATION Brier. No other model class, no re-tuning.
* **B0 — climatology:** constant = TRAIN+VAL base rate P(h≥1). Primary baseline.
* **B1 — shrunk-BA binomial (descriptive, non-market):** `1 − (1 − ba_l10_shrunk)^{ab_l10_mean}`. Tells us whether the multi-feature tree adds anything over the one-line rule of thumb.
* **B2 — market-implied probability:** **NOT TESTABLE** (§1). Recorded as a measured zero-row overlap, not omitted.

## 7. Metric, decision rule, threshold

* **Primary metric:** game-clustered paired ΔBrier = mean over holdout rows of `Brier(B0) − Brier(model)`, positive = model better, cluster = `game_id`, 95 % percentile CI from 5,000 cluster-bootstrap resamples (`seed=17`); Δlog-loss with `seed=18`. Implemented by **importing** `scripts/ab_harness_t4.py` primitives (`_block_bootstrap_mean_ci`, `_brier`, `_logloss`, `N_BOOT`, `EPS`, `MIN_*`), which in turn is T-583's harness. **Disclosed deviation:** `run_gate` itself cannot be invoked — its input contract requires a Kalshi `ticker`, a market `p_incumbent` and a ticker-derived date, none of which exist for matrix rows, and fabricating them is prohibited. A test asserts `run_gate` refuses these rows. The verdict rule below is the harness's rule, verbatim.
* **Decision rule (harness rule, fixed):** `DEFENSIBLE_IMPROVEMENT` iff ΔBrier CI lower bound > 0 **and** Δlog-loss point estimate > 0; `HARMFUL` iff ΔBrier CI upper bound < 0; otherwise the harness label `INCONCLUSIVE`, which this experiment reports as **NO DETECTABLE DIFFERENCE** (ADR-0066 precedent). If the interval spans zero the verdict is NO DETECTABLE DIFFERENCE, whatever the point estimate.
* **Ceiling on claims:** because H-edge is NOT TESTABLE, the strongest permissible sentence is "*detectable skill over climatology; edge over the market not established*". Nothing here supports sizing, activation, or a band assignment.

## 8. Controls (both pre-registered)

1. **Backward placebo (T-569 discipline).** Score the *same frozen model's* features at game T against the same player's outcome at game T−11 (11 rows earlier in that player's chronological sequence — outside the 10-game window, so the feature row contains no information about that game's result), paired against B0 with the same cluster bootstrap. Pre-stated interpretation: because player skill is time-symmetric, a persistent-skill model is *expected* to score well backward. If backward ΔBrier ≥ 50 % of forward ΔBrier (or its CI overlaps the forward CI), the forward gain is attributed to **time-symmetric persistent skill — the component a market already prices** — and is reported as not evidence of a forward-specific information edge. If it is < 50 % with a CI excluding the forward point estimate, that is reported as a forward-specific component.
2. **Within-date label permutation null (machinery check).** Permute `y` across rows within each game-date (seed 2028); the model's ΔBrier vs B0 must have a CI containing 0. If it does not, the harness/bootstrap or the pipeline leaks and **all results are void**.

## 9. Falsifiable predictions (written before any fit)

| # | prediction | rule |
|---|---|---|
| P1 | H1 holds: `DEFENSIBLE_IMPROVEMENT` vs B0 on holdout | §7 |
| P2 | point ΔBrier vs B0 in (+0.002, +0.012) (climatology Brier ≈ 0.243) | point estimate |
| P3 | vs B1: NO DETECTABLE DIFFERENCE or a gain < 25 % of P2's | §7 rule, descriptive |
| P4 | Backward placebo retains ≥ 50 % of the forward gain (persistent skill) | §8.1 |
| P5 | Permutation null CI contains 0 | §8.2 |
| P6 | Market comparison NOT TESTABLE (overlap 0) | §1 — already verified |

A missed prediction is reported as missed. There is no second specification, no re-windowing, no re-segmentation by band, threshold, month or player subset, and no rescue analysis.

## 10. Pre-declared follow-ups (outside this wave's scope)

Establishing B2 needs a matrix **extension** covering 2026-08-01 → 2026-09-30 built from the public MLB Stats API with `scripts/generate_mlb_features.py`, joined to the price archive by real tickers — then `run_gate` can be used unmodified. That is a separate task; it would also be the first *genuinely unseen* holdout for the frozen model produced here.
