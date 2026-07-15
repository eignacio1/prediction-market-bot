# T-365 — AB_WINDOW=37 replacement feasibility (APR-0025 prep, Window 3)

**Date:** 2026-07-15
**Status:** Investigation only. No code changed, no re-sweep run. Registers follow-on work.

## Question

APR-0025 (`00_ADMIN/APR-0025_gg105-ba_l10-shrinkage-remediation.md`) explicitly flags that
`scripts/run_t359_gg105_interaction_model.py`'s `AB_WINDOW = 37` constant — the assumed
effective sample size behind each player's `ba_l10` used for empirical-Bayes shrinkage
weighting — is "a stated assumption, not a fitted value... should be replaced with each
player's real summed `ab_sum` in any implementation." This task checked whether that
replacement is feasible from data already on disk, ahead of Earl's APR-0025 sign-off decision.

## Finding: not replaceable from cached data. 0% of the epoch-3 cohort is matchable.

- `ba_l10` is computed in `src/prediction_market_bot/c2_feature_store/mlb_features.py:191`
  (`ab_sum = df["ab"].shift(1).rolling(window, min_periods=min_periods).sum()`), production
  defaults `DEFAULT_WINDOW=10` games, `MIN_PERIODS=3` (mlb_features.py:73-74) — i.e. the real
  denominator is a **10-game rolling AB sum**, not a fixed AB count; it will genuinely vary
  per player per game-date, plausibly both above and below 37.
- `ab_sum` is a **local pandas Series only** — never written back onto the feature-store
  output, never persisted to any cache/log/snapshot. Confirmed no `.parquet`, no feature-store
  snapshot files, no MLB box-score cache anywhere in the repo.
- `t4_mlb_cycle_log.jsonl` / `t4_mlb_resolved_ledger.jsonl` (the two sources
  `run_t359...` joins from) carry the pre-computed `ba_l10` ratio and in-game counters
  (`ab_so_far`, `ab_remaining`) only — no rolling-window AB sum field.
- The only source that has the real number is the C1 MLB Stats API
  (`fetch_batter_game_log`, `src/prediction_market_bot/c1_signal_ingestion/mlb_ingestion.py:357-411`),
  which requires a **live network call per player** (no recorded cassette/fixture exists in
  `tests/` — the only stand-in, `_batter_api_response()` in `tests/test_t181_mlb_c1.py`, is
  synthetic, not a captured real response).

## What a real fix would require

- The epoch-3 clean cohort (`logs/t4_mlb_resolved_ledger.jsonl`, `logic_epoch==3`) is
  **666 rows spanning 75 unique `player_id` values** — one live `fetch_batter_game_log` call
  per unique player (not per row) reconstructs that player's full-season game log, from which
  each row's real 10-game rolling AB sum as of its `game_date` can be re-derived with the
  same `.shift(1).rolling(10, min_periods=3).sum()` logic already in `mlb_features.py`.
  75 calls at the documented rate-limit floor (`DEFAULT_REQUEST_DELAY_S = 0.6`,
  `mlb_ingestion.py:40`) is a ~45s-minimum serial pull — mechanically small, but it is a
  fresh live external-API dependency, not a cache read, and was not run this session per
  the "prepare to wrap up" instruction that landed mid-investigation.

## Disposition

- **Not done this session.** No re-sweep exists using real per-row AB sums; the dose-response
  table in `exp_output/T359-GG105-INTERACTION-MODEL/interaction_model_results.json` (k=0/20/40/80/160
  against the fixed AB_WINDOW=37) remains the only sweep on file.
- **Directionally relevant to APR-0025's own caveat, not a blocker to it.** APR-0025 already
  discloses AB_WINDOW=37 as an unverified heuristic and does not pre-select k on the strength
  of a precise AB count — it recommends k=40 only as "lightest-touch value that already reaches
  conventional significance," a qualitative read of the sweep's shape (monotonic attenuation),
  not a claim that depends on 37 being exactly correct. A real ab_sum would very likely widen
  or tighten individual rows' effective shrinkage (some players' true rolling AB sum is above
  37, some below) but is unlikely to reverse the sweep's monotonic direction — that has not
  been tested and should not be asserted as confirmed.
- **Follow-on registered:** T-367 (see TODO_NEXT.md) — build the 75-call live pull, re-derive
  real per-row AB sums, re-run `run_t359_gg105_interaction_model.py`'s H1 sweep with per-row
  AB_WINDOW instead of the fixed constant, and diff the resulting Fisher-p / win-rate-gap table
  against the k=37-fixed baseline above. Best run as its own isolated-worktree session, live
  network access permitting — not a same-session extension of this memo.
