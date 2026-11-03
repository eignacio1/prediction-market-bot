# W97.4 — the NHL engine prices the whole board (results)

Exploratory; no order, gate, registry cell or running component. Code: `src/prediction_market_bot/nhl_engine/` (PR #390 inputs/goals, PR #394 model + scoring). Scripts: `w97_4_build.py`, `run_w97_4.py`, `run_w97_4_kalshi.py`. Raw: `results/heldout_w97_4.json`, `results/kalshi_w97_4.json`.

## What was built
One fitted model gives each game's two regulation-goal rates (point-in-time 5v5 xG for/against, power play / penalty kill, rest, previous-starter goalie proxy, in-season league-level recalibration). One joint simulated score distribution per game then prices moneyline, puck line at each strike, total at each strike and both team totals, so every ladder is coherent by construction (tested). Overtime / shootout: a regulation tie is broken by exactly one credited goal, as the Kalshi rules read; `p_home_ot` fitted 0.52–0.54.

## Distribution choice (measured, held-out seasons 2023–25)
- Poisson vs negative binomial: the method-of-moments dispersion is infinite in every test season (var/mean of regulation goals 0.96–1.02), so NB equals Poisson identically. **Poisson.**
- Score correlation is **negative**, not positive: corr(home, away regulation goals) −0.116 (2022), −0.117 (2023), −0.090 (2024), −0.075 (2025). A shared positive factor cannot represent it. Engine uses independence plus a tie-odds multiplier.
- Realized regulation ties run 20.7% / 20.7% / 24.8% (2023–25) against ~17% under independent Poisson. A tie-odds multiplier (fitted on train) is implemented and tested (known-answer: recovers the set odds, ladders stay monotone). **Measured effect on the totals level miss: negligible** (mean P(over 5.5) 0.530 / 0.517 / 0.555 predicted vs 0.573 / 0.537 / 0.573 realized). The remaining totals under-prediction (~2–4 pts) is not explained by tie share; the likely carrier is late-game scoring and empty-net goals, which this engine does not model. Registered as a limitation, not fixed.
- Applies when: goal counts are near-Poisson and team scores are weakly negatively correlated (NHL). Does not apply to a sport with overdispersed, positively correlated scoring.

## Held-out Brier vs results (train strictly earlier seasons; model / climatology of the train base rate)
| Family | 2023 | 2024 | 2025 |
|---|---|---|---|
| ML | .2357/.2486 | .2368/.2470 | .2457/.2499 |
| Home puck line −1.5 | .2209/.2241 | .2301/.2293 | .2070/.2117 |
| Total 4.5 | .1680/.1671 | .1839/.1864 | .1580/.1566 |
| Total 5.5 | .2478/.2452 | .2491/.2509 | .2442/.2447 |
| Total 6.5 | .2500/.2491 | .2448/.2465 | .2484/.2492 |
| Home team total 2.5 | .2223/.2319 | .2310/.2346 | .2321/.2350 |
| Home team total 3.5 | .2378/.2439 | .2358/.2404 | .2375/.2415 |

Beats climatology on moneyline, team totals every season, puck line in 2 of 3. **Totals sit at climatology** (no skill, no harm). n = 1,312 games per season; intervals not yet computed for the held-out table (calibration bins not produced — registered below).

## This season vs Kalshi (n too small to conclude)
Archive snapshots since 2026-10-28 05:03Z, last snapshot ≥15 min before puck drop, mid of bid/ask; outcomes from final scores. **33 finished games, 726 market rows** (66 ML, 132 spread, 198 total, 330 team total).

| | Brier engine | Brier market | adv (market−engine), game-clustered | 95% CI |
|---|---|---|---|---|
| All | .1849 | .1792 | −0.0057 | [−0.0126, +0.0013] |
| ML | .2189 | .2119 | −0.0070 (se .0100) | wide |
| Spread | .1913 | .1831 | −0.0082 (se .0075) | wide |
| Total | .1762 | .1712 | −0.0050 (se .0037) | |
| Team total | .1807 | .1759 | −0.0048 (se .0033) | |

Skill weight (accepted market-anchored gate, `bayes_skill`, tau 0.005): **0.0** on every family; posterior P(engine > market) = 0.10 overall. Every point estimate has the engine behind the market, none distinguishable from zero at 33 games. Prior comparison (W84.3, 2025, n=1,306 ML): market / frozen v1 / factor 0.2442 / 0.2473 / 0.2452 — "too few to tell" there too. The market snapshots are archive-cadence (20 min), not a closing line; timing mismatch is a caveat.

## EXP-046: **not earned**
The rule was: freeze only if the engine is no worse than the market on some family or beats it held-out. On the only market comparison with a clean pre-drop price (33 games), the engine trails on all four families (point estimates), and there is no held-out market price for the 2023–25 seasons (store `KALSHI_HISTORY_NHL` is not present). Beating climatology is not beating the market. Re-open when ≥ ~200 finished games carry archive quotes (the archive keeps accumulating), judged n then set from the measured per-game sd (0.020 here).

## Defect found and fixed — flat first-season league baseline
`league_rate_prior` used a flat 2.20 goals-per-60 for the whole first season in the frame (real ≈ 2.7), inflating every first-season feature ~25% and leaving train-fit rates ~8% low on later seasons; 2023 totals were clearly worse than climatology before the fix (TOTAL 4.5: .1875 vs .1671). Now an expanding in-season rate over strictly earlier puck drops, shrunk to the default (known-answer test added). Pattern sweep: see the handoff.

## Factor stage (ADR-0075)
| Factor class | Stage |
|---|---|
| 5v5 team xG for/against (matchup cross: offence × opposing defence) | applied (in the price) |
| Special teams (PP/PK × opponent penalty rate) | applied |
| Rest / back-to-back | applied |
| Goalie (previous starter's decayed, shrunk GSAx/shot) | interpreted — coefficients unstable across fits (gs_own −1.1…+1.4); probable starter not in the store pre-drop (GG-1010) |
| Venue, officials, coaching, injuries/scratches, travel, qualitative | not built (GG-1010–1014) |

## Limits and not done
- Calibration bins and game-clustered intervals for the held-out table: not produced.
- Real-data point-in-time truncation test (rebuild with later seasons removed): not run; the synthetic leakage tests (PR #390) are the evidence. The xG model is out-of-time per season (no xG leakage by construction).
- 131 games with empty shift records remain in the store (`fetch_failures.json`, all `kind: shifts, error: empty`); they are excluded where shifts are needed.
- Muse cards R-047/R-067/R-080 were not found in the repo.
- No Kalshi market was traded or sized; nothing here touches the shadow arm.
