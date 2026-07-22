# T-367 — Live AB_WINDOW re-pull results: real per-row AB sum vs fixed AB_WINDOW=37

**Date:** 2026-07-21
**Status:** Complete. Live re-pull run, H1 sweep re-run with real per-row AB sums, diffed against the k=37-fixed baseline.

## What this checked

T-365 (2026-07-15) found `run_t359_gg105_interaction_model.py`'s `AB_WINDOW=37` — the
assumed effective sample size behind each player's `ba_l10`, used as the shrinkage-weight
denominator in the H1 sweep that fed APR-0025's k=40 recommendation — was a stated
assumption ("~35-40 AB" midpoint), not a fitted value, and was not replaceable from any
data already on disk (the real 10-game rolling AB sum, `mlb_features.py:191`, is a
transient pandas Series, never persisted). This task performed the live re-pull T-365
registered as a follow-on: 75 `fetch_batter_game_log` calls (one per unique `player_id` in
the epoch-3 clean cohort, not per row), reconstructed each row's real 10-game rolling AB
sum as of its `game_date` using the identical `.shift(1).rolling(10, min_periods=3).sum()`
formula, and re-ran the H1 shrinkage sweep with real per-row AB counts substituted for the
fixed constant.

Network reachability to the MLB Stats API was confirmed live (HTTP 200) before starting.
All 75 players fetched successfully (0 failures, 0 rows fell back to the AB_WINDOW=37
default). Script: `scripts/run_t367_ab_window_repull.py`. Raw output:
`exp_output/T367-AB-WINDOW-REPULL/ab_window_repull_results.json`. Per-player game logs
cached at `exp_output/T367-AB-WINDOW-REPULL/game_logs_cache.json` (re-runs read from cache,
no repeat API calls).

## Finding: AB_WINDOW=37 was a good assumption. Real distribution centers almost exactly on it.

Across the 666 joined rows, the real 10-game rolling AB sum as of each row's `game_date`:

| Stat | Value |
|---|---|
| mean | 37.30 |
| median | 38.0 |
| stdev | 3.97 |
| min | 15.0 |
| max | 45.0 |
| % of rows with real AB sum < 37 | 39.5% |

The fixed constant (37) sits within 0.3 AB of the real cohort mean and 1 AB of the real
median — the "~35-40 AB midpoint" heuristic from T-333/T-344 was, in this cohort, close to
exactly right, not merely a plausible guess.

## Sweep comparison: real ab_sum vs k=37-fixed, full cohort (n=666)

| k | Fisher p (k=37-fixed, T-359) | Fisher p (real ab_sum, this task) | Verdict (both) |
|---|---|---|---|
| 0 | <0.0001 (4.77e-06) | <0.0001 (4.77e-06) | ANTI-PREDICTIVE (identical — k=0 has no shrinkage term, AB_WINDOW is unused) |
| 20 | 1.96e-05 | 1.01e-05 | ANTI-PREDICTIVE (both) |
| 40 | 0.0045 | 0.0035 | ANTI-PREDICTIVE (both) |
| 80 | 0.0797 | 0.0797 | ANTI-PREDICTIVE (both, values coincide to the digit shown) |
| 160 | 0.1552 | 0.1552 | INCONCLUSIVE (both, values coincide to the digit shown) |

Win-rate gaps (pos-edge / neg-edge) track the same pattern at every k: e.g. k=40 gives
0.546/0.659 (fixed) vs 0.544/0.660 (real) — a difference in the third decimal place, not a
directional change anywhere in the sweep.

## Disposition

- **T-359's monotonic-attenuation finding is confirmed, not an artifact of the AB_WINDOW=37
  assumption.** Every verdict (ANTI-PREDICTIVE at k=0/20/40/80, INCONCLUSIVE at k=160) and
  every Fisher-p value reproduces under real per-row AB counts within noise. The anti-predictive
  direction still survives at every tested k, exactly as APR-0025 disclosed — this re-pull adds
  no reversal and no new caveat to that picture.
- **APR-0025's k=40 recommendation and its already-completed sign-off/deployment (ADR-0047,
  epoch 8, 2026-07-18) are unaffected.** This was a retrospective validation of the T-359
  research sweep that preceded APR-0025, not a check on the production `ba_l10_shrunk`
  computation itself — production already uses each player's real `ab_sum` (not a fixed
  constant) per ADR-0047, and this task doesn't touch that code path.
- **No further action required on AB_WINDOW=37 specifically.** The assumption that prompted
  T-365/T-367 turned out, on live verification, not to have been a material risk in this
  cohort. Closing T-367 as complete.

## Reuse note

`build_real_ab_lookup()` in `scripts/run_t367_ab_window_repull.py` reproduces
`mlb_features.py:191`'s rolling formula rather than importing it, because the production
function (`_compute_rolling_batter_features`) computes `ab_sum` as a local variable and
never returns it as an output column (confirmed in T-365) — there was nothing importable to
reuse for this specific value. The monotonicity/Fisher-test machinery itself
(`e17.edge_monotonicity()`, `bm.to_mlb_positions()`) is reused unmodified from
`run_exp017_mlb`/`run_band_monitor`, per this project's standing GG-100 discipline.
