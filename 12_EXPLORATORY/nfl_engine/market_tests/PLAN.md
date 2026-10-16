# NFL market-side tests — PLAN (W77.2). FROZEN before any computation. EXPLORATORY, never a verdict.

Pillar DEPTH, measure D5(b): each applied NFL factor gets a market-side verdict (team/QB base, F5/F6, F8, engine). Writes only via `_fence.safe_out`. Closing lines are a market COMPARISON/target only, never a model input (FACTOR_TAXONOMY GAP-4 / GG-733). Charter rules bind. No registry, runner, ledger, cron, order, sizing or model change; no running component.

## Question
Per factor, is the "no gain" in outcome Brier (W73.3, W75.2, W76.2) (i) REAL-AND-PRICED, (ii) INVISIBLE to the test (underpowered), (iii) REAL-NOT-PRICED, or (iv) NOT REAL?

## Part A.1 — Power (frozen method)
For each family (ML, spread, total, team total) and each test (n = games and ladder strikes the stage used: 1,612 games, T in 2020..2025):
1. Minimum detectable ΔBrier at 80% power, alpha 0.05 two-sided, from the stage's own paired per-game ΔBrier SD (read from results_stage*.json bootstrap CIs: SD = CI half-width/1.96*sqrt(n)).
2. Injection simulation: take engine arm-B means, add a known true shift equal to F8's measured size (mean |shift| 0.45 pts, max 3.3; F5/F6 mean ~0.2) to the DATA-GENERATING mean only (sim outcomes drawn from the shifted engine), score arm B (unshifted) vs the arm that includes the shift, 500 repeats, game-cluster bootstrap decision rule identical to the stages (BEATS / MATCHES / NO). Report detection rate = P(BEATS). If < 50%, "no gain" is stated as NOT informative.

## Part A.2 — Closing-line regression (frozen)
Target: nflverse schedules `spread_line`, `total_line`, de-vigged `home_moneyline`/`away_moneyline` (free), REG games 2019..2025. Inputs point-in-time only: engine v0 arm-B mean margin/total (rolling origin as in the stages) plus each factor's term (F5/F6 term, F8 term, difference home−away for spread; sum for total). Model: close = a + b0·engine_v0 + Σ_k b_k·term_k; b_k ≈ share of factor k the market prices (1 = fully, 0 = ignores). Game-cluster bootstrap 95% CIs (B=2000, seed 20261014). Also report b0 and R² of engine v0 vs close (how much the base is priced). Moneyline: same with logit(de-vigged p).

## Part B.3 — Timing (frozen)
Kalshi price archive (`exp_output/KALSHI_HISTORY`, KXNFLGAME only, PARTIAL, 2025-26 season; spreads/totals NOT FETCHED). For games with F8 non-null: mid path before vs after the final injury report / inactives (~90 min pre-kickoff), signed by F8 direction; per-game paired difference. If candle coverage is insufficient, state what is missing and size it (markets × series to fetch). Free data only.

## Part B.4 — Answer rule (frozen)
Per factor: REAL-AND-PRICED if b_k CI contains 1 or excludes 0 with point estimate ≥0.5 and outcome test power ≥ 50%; INVISIBLE if power < 50% and b_k CI is wide (spans 0 and 1); REAL-NOT-PRICED if b_k CI excludes 0.5 downward and the outcome test is powered; NOT REAL if powered and b_k and outcome both ≈ 0. Then the band/timing recommendation (T1 days ahead vs T2 same-day vs inactives window) and the keep-building / chase-timing / move-to-thinner-markets recommendation — recommended, not decided.

## Modal expectation (pre-fit)
Outcome test is underpowered for F8-sized terms (detection ≪ 50%); F8 coefficient on the close is near 1 for Sunday games (injury reports are public and lines move), so modal verdict REAL-AND-PRICED or INVISIBLE, not REAL-NOT-PRICED. Game markets efficient on public injury news; any edge is timing or thinner markets.

## Data locations (local, gitignored; not in this worktree)
nflverse raw under `exp_output/NFL_EVENTS/raw/` exists in sibling worktrees (e.g. `PM-worktrees/20261015T050530Z-w75-2-nfl-stage2`, `...w73-2-nfl-data-layer`), team stats `exp_output/NFL_EVENTS/aux/team_stats.parquet`, Kalshi candles in the main tree `exp_output/KALSHI_HISTORY/candles/KXNFLGAME.jsonl`.
