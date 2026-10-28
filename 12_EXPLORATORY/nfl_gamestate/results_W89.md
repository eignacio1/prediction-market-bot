# W89.4 results -- NFL game-state chain, one simulation, whole board (EXPLORATORY, offline, not a verdict)

Plan: `PLAN.md` (frozen before held-out scores were read). Code: `chain.py`, `study.py`, `test_chain.py`; `src/prediction_market_bot/quant/absorbing.py` (+ `tests/test_quant_absorbing.py`). Raw numbers: `results.json`. Data: nflverse play-by-play 2016-2025 and schedules with closes (free). 2000 simulated games per real game; 272 regular-season games per held-out season; CIs are 95%, game-cluster bootstrap.
Held-out: 2024 (chain trained 2016-2023), 2025 (trained 2016-2024). Ratings point-in-time.

## One-line result
One play-level absorbing chain, tilted per matchup by a point-in-time points-per-drive rating, yields a joint (home, away) score distribution that prices moneyline, spread ladder, total ladder and team totals consistently. It is **statistically the same as a same-mean Gaussian** (|Brier diff| <= 0.003) and **worse than the market close** on moneyline and spread in both seasons. Expected first result; no edge claim.

## Quant bar
1. **Known answer:** `test_chain.py::test_estimator_recovers_planted_absorption` -- the estimator recovers a planted 3-state chain's absorption probabilities within 0.015; `tests/test_quant_absorbing.py` checks the algebra against gambler's ruin and the tilt (row sums, monotone). 5 tests pass.
2. **When it applies:** an absorbing chain fits a process that resets at a known terminal event (a drive) and whose next step depends on a small state. It does NOT fit score-state or clock-driven behaviour (kneel-downs, two-minute drill, late field goals), which is exactly where it misses (below).
3. **Measured on our data (chain-implied vs observed expected drive points at 1st-and-10, held-out):**

| Season | n plays | observed | chain | diff (obs - chain) | 95% CI |
|---|---|---|---|---|---|
| 2024 | 13,548 | 2.914 | 2.761 | +0.153 | [0.059, 0.248] |
| 2025 | 13,229 | 2.950 | 2.807 | +0.143 | [0.040, 0.245] |

The chain under-states scoring from 1st-and-10 by ~0.15 points per drive (trained on earlier, lower-scoring seasons; the league scored more). Real bias, not noise.

## Key numbers (|margin| frequency, simulated vs actual)
| |m| | 2024 sim | 2024 act | 2025 sim | 2025 act |
|---|---|---|---|---|
| 3 | 0.071 | 0.136 | 0.070 | 0.151 |
| 6 | 0.050 | 0.103 | 0.049 | 0.040 |
| 7 | 0.075 | 0.074 | 0.074 | 0.096 |
| 10 | 0.052 | 0.052 | 0.051 | 0.037 |
| 14 | 0.043 | 0.018 | 0.042 | 0.040 |

**The quant-bar claim "reproduces 3, 7, 10" is only partly met:** 7 and 10 are within sampling noise (n=272 games, binomial SD ~0.014-0.022); **3 is missed in both seasons by about half** (0.07 vs 0.14-0.15). The chain has no end-of-game logic, so it under-produces the late field goal that makes a 3. Said plainly: the shape is not recovered at the most important key number.
Sim also under-produces overtime (3.4% vs 5.2-5.9% actual) and totals sit 0.3-0.9 below the line (see JSON).

## Board vs the market close (paired Brier, sim minus other; negative = sim better)
| Family | Season | n | Brier sim / market | sim - market (CI) | sim - same-mean Gaussian (CI) |
|---|---|---|---|---|---|
| Moneyline | 2024 | 272 | 0.221 / 0.200 | +0.021 [0.006, 0.035] | +0.001 [0.000, 0.002] |
| Moneyline | 2025 | 272 | 0.229 / 0.212 | +0.018 [0.005, 0.030] | -0.000 [-0.001, 0.001] |
| Spread | 2024 | 268 | 0.263 / 0.251 | +0.011 [-0.002, 0.026] | -0.002 [-0.004, -0.001] |
| Spread | 2025 | 271 | 0.269 / 0.250 | +0.019 [0.007, 0.032] | -0.002 [-0.004, -0.000] |
| Total | 2024 | 269 | 0.254 / 0.250 | +0.005 [-0.007, 0.016] | +0.003 [0.001, 0.005] |
| Total | 2025 | 272 | 0.258 / 0.250 | +0.008 [-0.003, 0.020] | +0.001 [-0.001, 0.003] |

Reading by the frozen rule: **worse** than the market on moneyline (both seasons) and spread (2025); **not distinguishable** on spread 2024 and total (CIs contain 0, point estimates +0.005 to +0.011, above the +0.005 "matched" margin so we do NOT call them matched). Against the same-mean Gaussian, the simulation is identical to within 0.003 -- the chain adds no distributional shape the Gaussian lacks, which is W73.3's finding again (`12_EXPLORATORY/nfl_engine/results.md`). The centre (team rating) is what separates it from the market, not the shape.

**Shape-only ladder:** re-centring the simulated margin on the market line and reading it at strikes line +/- {0.5, 2.5, 3, 3.5, 6.5, 7, 10}, the Brier gap to a market-centred Gaussian is +0.000 to +0.003 at every strike in both seasons (JSON `ladder`). The full (not re-centred) simulation is +0.009 to +0.022 worse at every strike: **the loss is the centre, not the shape.** There is no detectable shape advantage and no strike where the simulation is better.

**Team totals:** no free team-total market. Descriptive only: home-score PIT in 5 bins = [51, 49, 51, 62, 59] (2024), [50, 48, 57, 62, 55] (2025): mild under-dispersion/low-bias (too few draws in the top bins' complement; expected from the +0.15 scoring bias).

## What this does and does not show
- Shows: the whole board (ML, spread ladder, total ladder, team totals) can be read from ONE joint simulation, offline, internally consistent, from free data. That is the D4 structure.
- Does NOT show any edge. The simulation is worse than the close at the centre and the same as a Gaussian in shape; its first-order misses are known (3 key number, scoring level, OT).
- Not run: props (no joined free per-game outcome), parlays, 2025 Kalshi KXNFLGAME candles (location unpinned), frozen `nfl_pregame_v1` comparator (the same-mean Gaussian stands in). Next block.

## Stage per factor (ADR-0075)
| Factor | aggregated | interpreted | applied (to a price, vs market) |
|---|---|---|---|
| Down / distance / field position | yes | yes (chain, values) | yes -- measured above, no edge |
| Team strength (off/def points per drive, PIT) | yes | yes | yes -- the centre loses to the close |
| Drive outcomes, clock, possession alternation | yes | yes | yes |
| Matchup (coverage/personnel), availability, QB, weather, venue, officials, coaching, qualitative | not in this engine | -- | -- |

Granularity index: only the split (down/distance/field) and the application exist here; rank-vs-history, matchup cross and market map are not built.

## Proposed rows for the window (not written to SEATS/ or the registry)
- D4 NFL: "event data layer + scaffold" -> **"whole board read off one joint simulation, offline (ML, spread, total, team totals); worse than close at the centre"**. Do not move the `[[engine]]` artifact: the existing `12_EXPLORATORY/nfl_engine/engine.py` is statistically equivalent and nothing here beats it.
- Next DEPTH move with the cheapest evidence: add score-state and late-game clock behaviour (fixes the 3 spike, OT, scoring-level drift), then put QB/availability into the rating.
