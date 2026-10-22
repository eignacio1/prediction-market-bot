# W84.3 — NHL depth lane: shot quality, goalie workload, special teams (EXPLORATORY)

Purpose (Hard Rule 12): **DEPTH**. Measures: D5(b) NHL stages, D5(a) NHL components. No live model, order, stake, registry cell or pre-registration touched.
Code: `12_EXPLORATORY/nhl_engine/{factors,run_w84_3,part_b}.py`; test `tests/test_nhl_factors_pit.py`. Raw outputs: `results/part_b.json`.

## Scope actually run (stated plainly)
- Event store compiled for **seasons 2021–2025 only** (start years). 2018–2020 and 2026 were not fetched (time). 2021 is xG burn-in; factors exist for 2022–2025 (5,592 game rows incl. playoffs; n per season ≈1,400).
- xG per shot: logistic on distance, angle, shot type, strength state; **season t scored by a model fit on seasons < t**. Empty-net and shootout shots dropped.
- Rolling window = each team's previous 20 games, `shift(1)`; windows carry across season boundaries. PIT assertion (window ⊆ `PointInTime.completed_before`) passed on 200 sampled games.
- Goalie workload uses the **previous game's** starter (rest days, starts in last 7 days, last-10 GSAx). The starter for THIS game is not known pre-game from the store (GG-1010) and is not used.
- Kalshi: `KXNHLGAME` hourly candles, 3,330 settled markets, **2025-26 season only** — so Part B's only out-of-sample season is 2025, which is also the frozen model's own holdout.

## Granularity index (per factor)
| Factor | Split | Rank vs same-point history | Matchup cross | Market map | Application | Stage |
|---|---|---|---|---|---|---|
| Shot quality (xG share 5v5, H1/H5) | 5v5 only, rolling 20 | **not built** (n_prior is cumulative across seasons, so a same-week-of-season rank needs a season-relative counter) | home xG share − away xG share | KXNHLGAME home ML | stacked on market in Part B | H5 **applied**, H1 interpreted (shooter-level quality not built) |
| Goalie workload (H2) | prev-start rest / starts7 / GSAx10 | not built | home − away prev-goalie GSAx | KXNHLGAME | in Part B blend | **applied** (signal ≈ 0: r = 0.006–0.05 with home win) |
| Special teams (H4) | PP xG/60 and PK xGA/60, rolling | not built | home PP × away PK | KXNHLGAME | in Part B blend | **applied** |
| Rest (H6) | days since previous game | not built | home − away | KXNHLGAME | in Part B blend | interpreted |

Univariate correlation with home win (diff features, regular season, no-OT-ties excluded): xG share 0.244/0.192/0.160/0.161 (2022–25); special-teams net 0.183/0.190/0.108/0.024; rest 0.04–0.08; goalie GSAx ≈ 0. Decaying correlation of the first two is worth watching — one season of decline is not a trend.
Matchup cross (exploratory, no CI): home PP-xG/60 top tercile × away PK-xGA/60 worst tercile, n = 557, home win 0.621 vs 0.537 base. Not tested out of sample; the terciles were cut on all years; treat as a lead.

## Part B — does the factor add to the pre-game price beyond `nhl_pregame_v1`? (2025, out of sample)
Factor model (xG share, special-teams net, goalie GSAx, rest; standardised diffs, L2) fit on **2022–2024 only**. Market = home-team `KXNHLGAME` mid at puck drop − 1h. Verdict rule fixed before the 2025 look (see `run_w84_3.py` docstring).

| Quantity | Value |
|---|---|
| n (regular season, decisive, quote + factor + frozen p all present) | **1,306** (market outcome agreed with box score on 100%) |
| Brier: market / frozen v1 / factor alone | 0.2442 / 0.2473 / 0.2452 |
| 5-fold CV Brier, blend − market | **+0.0012**, 95% CI [−0.0006, +0.0030] (blend no better) |
| Stacked coefficient on factor logit (with logit market) | **0.37**, 95% CI [−0.09, +0.80] |
| Stacked extra weight on frozen v1 (beyond market) | 0.22, 95% CI [−0.27, +0.68] |
| Median bid–ask spread | 0.01 |

**Verdict: too few to tell.** The coefficient CI includes 0 but its upper end (0.80) exceeds the 0.5 "does not add" bar, and the CV blend is not better than the market. Reading: the market is better calibrated than both the frozen model and this factor model; the factor has positive point weight on top of the price but the interval cannot exclude zero at n = 1,306. Not a basis for any change to `nhl_pregame_v1`.
Caveats: single season; market mid is not an executable price; coefficients bootstrap 1,000×, CV folds random not temporal.

## Stage and measure movement (source: `SEATS/nhl.toml`, `ARCHITECTURE_COMPONENTS.toml`, this file)
- D5(b) NHL: aggregated 7 / interpreted 0 / applied 0 → **aggregated 2 (H3, H7) / interpreted 2 (H1, H6) / applied 3 (H2, H4, H5)** of 12. "Applied" follows CLAUDE.md D5 (a tested path from the fact to a price, against the market); the seat file's own header defines applied more strictly (conditioned on by a model that logs forecasts) — by that definition applied is still 0. Flagged for the strategic window.
- D5(a) NHL: 0/8 → **1/8** (`cross_reference_compatibility`: one PIT-asserted frame joining the three factor classes). `temporal_evolution` not counted: no cross-season stability test.

## Gaps found / not fixed
Starting goalie unknown pre-game (GG-1010), travel (1011), officials/coaches (1012), injuries (1013), qualitative/PAM (1014) — all already registered; none closed. Kalshi NHL history store `exp_output/KALSHI_HISTORY_NHL/` is local and untracked (large; rebuildable from the fetch).
