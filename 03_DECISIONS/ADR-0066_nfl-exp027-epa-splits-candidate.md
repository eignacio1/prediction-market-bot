# ADR-0066: NFL EXP-027 Passing/Rushing EPA Splits — Candidate Model (PROPOSED, NOT ACCEPTED)

**Status:** PROPOSED — drafted only (T-581). Not accepted. Supersedes nothing. The incumbent EXP-027 feature set stays the default; the candidate is wired into no run path. No cron entry, `kelly_fraction`, cell status, or gating constant is changed by this document.

**Would supersede (only if accepted later):** the 6-feature EXP-027 / HYP-012 NFL moneyline feature set, per ADR-0004's frozen-model policy (a live C3 change requires a superseding ADR). **Model class is unchanged** (StandardScaler + CalibratedClassifierCV sigmoid cv=3 over LogisticRegression C=1, balanced, random_state 42); only the input features differ.

**Author:** Claude (session `exp027-epa-splits`, T-581) · **Date:** 2026-09-28

---

## Context

T-575's feature audit (item 4) noted that EXP-027 consumes only aggregate `off_epa` and `def_epa_allowed`, and that `passing_epa`/`rushing_epa` were "already fetched and simply never consumed." That is only partly accurate: the raw nflverse file carries the splits and `NFLIngestionClient` fetches them, but `_normalize_team_stats_df` collapsed them into `off_epa = passing_epa + rushing_epa` and discarded the parts, so they were not resident in the store or any cache. They are recoverable from the same nflverse source file (no new data source). Coverage in that file: 2014–2025 complete (all 32 teams, every REG+POST game, 0 NaN), 2026 weeks 1–3.

## Decision (proposed)

Add an opt-in `include_splits` path to C1 retention and four `NFLTeamStatsStore` accessors (`get_pass_epa`, `get_rush_epa`, `get_def_pass_epa_allowed`, `get_def_rush_epa_allowed`; same window 8 / min_periods 3 / decay 0.85 / TI-01 strict `game_date < as_of`), and a 14-feature candidate = the 6 incumbent features + the 8 split features. Default fetch and the incumbent path are byte-for-byte unchanged (47 tests pass, including T-526's 42).

The aggregate is exactly the sum of its splits (max abs residual 3.6e-15), so the 14-feature set is linearly redundant by construction; a 10-feature splits-only ablation (aggregates dropped) was run alongside.

## Evidence (offline; full detail in `05_RESEARCH_EXPERIMENTS/RESULTS_SUMMARIES/T581_exp027_epa_splits_results.md`)

Primary holdout: train 2015–2024 (n=2734), test season 2025 (n=284), temporal, same split as the incumbent's pre-registered backtest. 95% bootstrap intervals (2000 resamples, paired).

| | Incumbent | Candidate (14) | Diff (cand − inc), 95% CI |
|---|---|---|---|
| Accuracy | 0.606 [0.549, 0.662] | 0.616 [0.563, 0.669] | +0.011 [−0.007, +0.032] |
| Brier | 0.2210 [0.2057, 0.2375] | 0.2203 [0.2053, 0.2363] | −0.0007 [−0.0020, +0.0005] |
| ECE | 0.066 [0.046, 0.128] | 0.069 [0.047, 0.129] | +0.002 [−0.022, +0.026] |

Every difference interval spans zero. Rolling-origin 2020–2025 (six holdouts, n≈270–285 each): candidate Brier differs from incumbent by at most 0.0009 in absolute value and every interval spans zero; it is better in 1 of 6 seasons (2025), worse or equal in the other 5. **The honest reading is no detectable difference.**

Closing line (2026 Kalshi KXNFLGAME archive, n=48 games): market closing Brier 0.2335, incumbent 0.2400, candidate 0.2453. Neither model beats the market's closing price at this n, and the sample is far too small to rank the two models.

## What this does NOT fix

- **The small-n power problem.** EXP-027 was UNDERPOWERED because clean_n (14–16 for 2026) is far below n\* (≈2,610 from the observed edge variance). A richer feature set changes neither term of that inequality. T-575 ranked this item 4 for exactly this reason. Nothing here moves EXP-027 toward a verdict.
- It does not show the model beats the market. Both models sit at or behind the closing line on the only games where the comparison is computable.
- It does not address the efficiency-gradient concern: NFL moneylines are among the sharpest lines on the board.

## Activation prerequisites (if ever pursued)

1. Operator acceptance of this ADR (DS sign-off per ADR-0004).
2. **ADR-0042 D2 must be cleared** for the affected surface; T-583/37.1 is concurrently establishing whether that gate is runnable in this environment. Not assessed here.
3. Explicit operator authorization to schedule NFL T1 (no cron entry exists; none added here).
4. A pre-registered benefit threshold — on this evidence the expected benefit is not distinguishable from zero, so there is currently no case to activate.

## Recommendation

Do not accept on present evidence. Keep as a documented, tested, unwired candidate; revisit only if a larger closing-line sample (e.g. historical nflverse moneylines, a needs-your-decision item) makes a market-relative comparison meaningful.
