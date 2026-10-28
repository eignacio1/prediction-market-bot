# NBA board engine — PLAN (frozen before any fit)

**EXPLORATORY. Never a verdict.** W93.3, T-1393. Pillar DEPTH (+PROOF), measure **D4** (NBA: data layer -> whole board priced from one engine, scaffold). Writes only under `12_EXPLORATORY/nba_board/`. No model, runner, arm, cell, order or ledger is touched. Deviations go in a dated section at the bottom.

## 1. Model class — simulated, and why
**Monte Carlo of the two scores from one shared draw** (not an analytic bivariate normal).
- Why simulated: ML, every spread strike, every total strike, both team totals and any parlay must be pure functions of the same sample, so coherence holds by construction and parlay correlation is read off the draws rather than assumed. An analytic normal would price the ladders but make P(win) and P(cover 0) two separate formulas; discreteness (integer scores, overtime) is free in a sample.
- Per game: `P ~ N(mu_poss, s_p)` possessions (shared by both teams — this is what induces positive score correlation), `e_h, e_a ~ N(0, s_e)` independent efficiency noise in points per 100 possessions, `pts_h = round(P*(ppp_h+e_h)/100 + hca/2)`, `pts_a = round(P*(ppp_a+e_a)/100 - hca/2)`. A regulation tie is resolved by 5-minute overtime periods (each side scores `N(mu/9.6, ...)`) until it breaks, so totals include overtime as the data does.
- Score correlation is **measured, not assumed**: it is an output of (`s_p`, `s_e`) and is reported next to the empirical correlation of the held-out score residuals.

## 2. Means (factors in)
Team rating for stat c in {pace, ortg, drtg} at game G = `(sum of the team's same-season games completed before G + K*prior) / (n + K)`; the as-of rule is the existing `tip_latest + COMPLETION_BUFFER <= tip_earliest(G)` predicate (B1/B2 point-in-time, `nba_factors`/`nba_point_in_time`). `prior` = the team's previous-season full-season mean (league mean of that season if the team has none). `K` is chosen from {10, 20, 40} on the calibration season only. This is what lets us price from game 1 of a season, which the existing 10-game minimum could not. `mu_poss = mean(pace_h, pace_a)`, `ppp_h = (ortg_h + drtg_a)/2`, `ppp_a = (ortg_a + drtg_h)/2`; `hca` = mean margin residual of the calibration season. B3/B7/B9 factors are NOT in the means this block (no dated evidence they improve a *price*; 93.1/93.2 plug in next wave); each is reported with its stage in the results.

## 3. Shape parameters (2) — fitted on calibration data only
`s_p`, `s_e` by moment matching on the calibration season's out-of-sample residuals: Var(margin resid) fixes `s_e`, Var(total resid) then fixes `s_p`. Then verified by simulation (sim SDs vs target). Fixed seed, common random numbers.

## 4. Evaluation — rolling origin
Test seasons T in 2021..2026 (regular season), ratings from games before each game, shape on T-1, score T. Ladders (paired, identical strikes for engine and comparator): centre `c = floor(mu)+0.5` for margin, total, home pts, away pts; strikes `c+{-6,-3,0,+3,+6}`. Comparator = a Gaussian with the same means and the same residual SDs (so any difference is shape/discreteness, not inputs). Metrics per family (ML, spread, total, team total): pooled-strike Brier, delta Brier engine-minus-Gaussian by game-cluster bootstrap (B=2000), calibration slope/intercept of logit(outcome) on logit(p).

## 5. Against Kalshi (Part B)
Archive rows (KXNBA{GAME,SPREAD,TOTAL,TEAMTOTAL}, box PRICE_ARCHIVE since 2026-10-28) -> prevailing mid at the last archive snapshot before tip; settlements from public GET; engine priced from as-of ratings. Paired Brier engine vs market per family with game-cluster bootstrap intervals; implied-distribution comparison via `quant.ladder` (centre, width); market-anchored skill weight `w` in `p = (1-w)*market + w*engine` fitted by least squares with a bootstrap interval. **Where n is too small, said plainly; the decision is never "edge" at this n.**

## 6. Decision rule (frozen)
Non-inferiority margin +0.0010 Brier for engine vs Gaussian comparator (upper 95% limit < +0.0010 = MATCHES, < 0 = BEATS, else NO). Engine vs Kalshi is descriptive unless the interval excludes 0 with the stated n.

## 7. Non-goals
No registry/runner/ledger/cron/order/sizing change. No availability (93.1) or geometry (93.2) in the means. Props not priced this block.
