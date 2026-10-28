# W93.3 results — NBA engine: one model prices the whole board

**EXPLORATORY. Never a verdict. No edge claim is made.** T-1393, pillar DEPTH (+PROOF). Plan frozen in `PLAN.md`. Code: `src/prediction_market_bot/nba_engine/` (library only), tests `tests/test_nba_engine.py`, studies `study_a.py` / `study_b.py`, raw output `part_a.json` / `part_b.json`.

## 1. What was built
A **simulated** (Monte Carlo) joint distribution of the two scores, drawn once per game. Moneyline, every spread strike, every total strike and both team totals are pure functions of the same sample, so the four families are coherent by construction and parlay correlation can be read off the draws. Simulation was chosen over an analytic bivariate normal because discreteness (integer scores, overtime) is free in a sample and one sample prices everything.

- Possessions `P ~ N(mu_poss, s_p)` shared by both teams; efficiency noise `e_h, e_a ~ N(0, s_e)` independent; ties go to overtime.
- Means: as-of team pace / ortg / drtg (point-in-time, B1/B2), shrunk toward the previous season (K chosen from {10, 20, 40} on the calibration season; K=10 won in every test season).
- **Score correlation is measured, not assumed.** Simulated correlation is 0.30–0.44 against an empirical held-out residual correlation of 0.24–0.35: the engine over-states it by about 0.06–0.09 (partly overtime). Simulated total SD is 20.2–20.8 against an empirical 18.7–19.4; simulated margin SD matches. This is a known flaw, not fixed this block.

## 2. Part A — held-out seasons (rolling origin, test seasons 2021–2026, regular season, n = 7,230 games)
Comparator: a Gaussian with the same means and the same residual SDs, so any difference is shape/discreteness, not inputs. Game-cluster bootstrap, B = 2000. Decision rule frozen in PLAN §6.

| Family | Engine Brier | Gaussian Brier | Δ (engine − Gaussian) | 95% interval | Verdict | Engine calibration slope |
|---|---|---|---|---|---|---|
| Moneyline | 0.22406 | 0.22457 | −0.00051 | [−0.00082, −0.00019] | BEATS | 1.83 (intercept −0.16) |
| Spread | 0.23622 | 0.23632 | −0.00010 | [−0.00018, −0.00001] | BEATS | 0.99 |
| Total | 0.24134 | 0.24195 | −0.00061 | [−0.00091, −0.00032] | BEATS | 1.06 |
| Team total | 0.23064 | 0.23106 | −0.00043 | [−0.00058, −0.00027] | BEATS | 1.03 |
| ALL | 0.2342 | 0.2346 | −0.00040 | [−0.00054, −0.00025] | BEATS | 1.05 |

Reading: the engine beats its Gaussian twin on shape by a very small margin (≈ 0.0004 Brier). Spread, total and team-total are calibrated (slopes 0.99–1.06). **The moneyline is underconfident (slope 1.83)**; the Gaussian has the same flaw (1.89), so it comes from the shared inputs (heavy shrinkage ratings), not from the simulation shape. Reported, not fixed.

*When it applies:* the simulation shape pays where discreteness and a shared possession count matter (totals, team totals, ladders near the mean). Measured: ΔBrier −0.0004, interval above, n = 7,230 games.

## 3. Part B — against this season's Kalshi prices (DESCRIPTIVE ONLY)
**n is too small for any paired Brier, interval or skill weight. Stated plainly:**

| Input requested | What exists | n |
|---|---|---|
| Archive pre-game rows since 10-28 | 3 snapshots (05:08Z, 05:28Z, 05:48Z on 10-28), 4,008 NBA rows, 33 games, KXNBAGAME / SPREAD / TOTAL / TEAMTOTAL | 3 snapshots |
| 89.7 candles since 10-01 | **No NBA candles on the box** (`KALSHI_HISTORY/markets` holds only `KXNFLGAME`) | 0 |
| Settlements (public GETs) | The only game that could have finished (26OCT27 POR@LAL) still shows all 113 markets `active`, empty result | **0 settled games** |

Consequences: **paired Brier engine vs market: n = 0, not computed. Market-anchored skill weight `w` (accepted 10-21): unestimable, n = 0.** Nothing here supports or refutes edge.

Also: the event store has **no 2026-27 schedule or team_box** (CLI `--min-season 2027` produced nothing). Engine prices therefore use prior-only ratings (2026 full-season means), i.e. what game 1 would use, and understate early-season information. Calibration for the 2027 prices comes from season 2026.

### What was done instead: implied-distribution comparison
For each game the market's last-snapshot ladder was fitted with `quant.ladder.fit_normal` and compared with the engine's distribution. 32 games with a moneyline price (the 26OCT27 game was live or finished at snapshot time and is excluded); spread and total ladders could be fitted for only **12** of them (thin or absent ladders elsewhere).

| Quantity | Value |
|---|---|
| Games with moneyline price / full spread+total ladder | 32 / 12 |
| Engine − market home win prob, mean (mean abs) | +0.035 (0.085) |
| Correlation, engine vs market home win prob | 0.84 |
| Market moneyline vs its own spread-implied home win prob, mean abs gap | 0.008 (the market is internally coherent) |
| Margin mean, engine − market: mean (SD of diff) | +1.53 (2.70), corr 0.92 |
| Margin SD, engine vs market | 15.24 vs 13.16 |
| Total mean, engine − market: mean (SD of diff) | +2.03 (4.74), corr 0.81 |
| Total SD, engine vs market | 20.11 vs 18.79 |

Reading, as findings to examine and not conclusions: the engine leans toward the home side by about 3.5 points of win probability and its distributions are wider than the market's. The wider SD is partly the known correlation/total-SD over-statement above and partly a possible ladder-fit artifact (strikes limited to 3–97%, truncation). The engine's prior-only ratings mean it cannot yet see 2026-27 roster changes the market has priced in; the disagreement may be the engine being stale, not the market being wrong. The home/away assignment assumes the AWAYHOME event-ticker convention. Wide spreads on 10-31 events make those mids unreliable.

## 4. Factor stages and granularity index (ADR-0075)
| Factor | Stage | In the means? | Notes |
|---|---|---|---|
| B1 (pace/ortg/drtg as-of ratings) | applied | yes | tested path from fact to price; score vs market pending settlements |
| B2 (point-in-time rest/schedule rule) | applied (as-of gate) | gate only | used to enforce completion-buffered as-of cut |
| B9 | applied | yes | — |
| B3 | interpreted | no | not in the means; no dated evidence it improves a price |
| B7 (lineups, from 92.3) | aggregated / interpreted | no | not in the means this block |
| Availability (93.1), geometry (93.2) | pending | no | plug in next wave |

Granularity-index parts for what is applied: split = team ratings by offence/defence/pace; rank vs history = season-prior shrinkage only (no same-point-in-season ranking yet); matchup cross = ortg×opposing drtg only; market map = ML / spread / total / team total; application = simulation to price. Subtle crosses and tails (lineup-conditional, rest-conditional) are not built.

## 5. Measures moved
- **D4 NBA:** data layer → whole board priced from one engine (scaffold, tested). Source: `tests/test_nba_engine.py` (5 pass), `part_a.json`.
- **Markets priced from one joint distribution:** 0 → 4 (moneyline, spread, total, team total). Props and parlays not priced.
- **Brier against this season's Kalshi prices:** n = 0 (no settlements).

## 6. Gaps registered
No 2026-27 schedule/team_box in the event store; no NBA candles (89.7); archive has 3 snapshots and no settlements. See GOVERNANCE_GAP_LOG (GG-1393..GG-1395).
