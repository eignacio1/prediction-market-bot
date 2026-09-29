# T-581 — EXP-027 EPA Splits: Results Summary

**Verdict: no detectable improvement. Candidate stays unwired; ADR-0066 drafted, recommendation is not to accept.**

## 1. Are the splits resident?
Partly. Raw nflverse `stats_team_week_{season}.csv` (one row per team-game) carries `passing_epa` and `rushing_epa`. `NFLIngestionClient` fetched them but `_normalize_team_stats_df` reduced them to `off_epa` and discarded them; no store or cache holds them (T-575's "reach the C1 team-stats table intact" is inaccurate). Recovered from the same source file, no new data source. Coverage: 2014–2025 complete (32 teams; 267 games/season 2014–19, 269 in 2020, 285 in 2021–25; every game_id has exactly 2 rows; 0 NaN in either split), 2026 weeks 1–3 (48 games). `off_epa == passing_epa + rushing_epa` to 3.6e-15.

## 2. Build (offline, unwired)
Opt-in `include_splits` on `fetch_team_stats`/`fetch_team_stats_bulk`; store retains splits when present; four new accessors. Default path unchanged (T-526: 42 pass; new T-581 tests: 5 pass). Script: `scripts/exp027_epa_splits_candidate_eval.py`; result: `exp_output/NFL/exp027_epa_splits_candidate_result.json` (seed 20260929, 2000 bootstrap resamples).

## 3. Holdout (train 2015–2024 n=2734, test 2025 n=284, temporal)
Season holdout chosen because features are recency-weighted and games are ordered in time; a random split would leak.

| | Incumbent | Candidate 14f | Diff 95% CI |
|---|---|---|---|
| Accuracy | 0.606 | 0.616 | +0.011 [−0.007, +0.032] |
| Brier | 0.2210 | 0.2203 | −0.0007 [−0.0020, +0.0005] |
| ECE | 0.066 | 0.069 | +0.002 [−0.022, +0.026] |

Splits-only (10f) ablation: same picture (Brier 0.2203, diff CI [−0.0020, +0.0005]). Rolling origin 2020–2025 (n 268–285 each): Brier diffs from −0.0007 to +0.0011, all CIs span zero; the candidate is better only in 2025. Calibration curves (5 bins) are in the JSON.

## 4. Closing line (2026 only; archive covers 2026 only)
n=48: market 0.2335 · incumbent 0.2400 · candidate 0.2453 Brier; accuracy 0.646 / 0.542 / 0.542. Neither model beats the closing price; n is too small to rank models.

## 5. Caveat that governs everything above
EXP-027 is UNDERPOWERED (n\*≈2,610 vs clean n 14–16). More features do not change that. T-575 ranked this item 4 for that reason, and the result here is consistent with it.

## Needs your decision
- Scheduling NFL T1 (no cron entry added or proposed here).
- Whether to source historical nflverse moneyline columns as a multi-season closing-line benchmark (would turn the 48-game comparison into a ~1,400-game one; a new data source, so out of this block's scope).
