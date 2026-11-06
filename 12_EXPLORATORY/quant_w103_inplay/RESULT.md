# W103.3 (B-046) — In-play score math: NBA diffusion, NHL jump process

**One line per sport (plain English)**
- **NBA:** Given the score and time left, a drifting random walk prices the game winner well. It beat the pre-game-only price at every quarter end (Brier 0.191 / 0.156 / 0.120 at Q1 / Q2 / Q3, against 0.205 with no score information), n = 1,229 held-out 2025-26 games. It is slightly too confident at the extremes, so a 95% price really wins about 93%.
- **NHL:** Poisson goal arrivals with power-play and empty-net adjustments, plus exact overtime and shootout settlement, price the winner well from the first intermission on (Brier 0.214 / 0.147 / 0.119 / 0.101 at end of P1 / end of P2 / 10 min / 5 min left in P3, against 0.250 with no score information), n = 1,312 held-out 2025-26 regular-season games. It under-prices regulation ties (model 17–19% against 24.8% actual) and goals, because real hockey scoring is lumpier than Poisson.
- **Against Kalshi's in-play line: not scored, n = 0 for both sports** (see Part C).

Nothing here touches an order, position, stake, ledger row or live model. Stage (ADR-0075): *applied* only up to a price. The comparison against the market, which is what makes it applied, did not happen.

## What was built
`src/prediction_market_bot/quant/inplay_nba.py`, `inplay_nhl.py`; known-answer and simulation tests (19) in `tests/test_quant_inplay_n{ba,hl}.py`; run scripts `nba_heldout.py`, `nhl_heldout.py` in this folder. The existing Markov modules (`dtmc.py`, `absorbing.py`) were checked and not reused (order-life models). PR #433.

## Common limitation (stated, binds every number below)
**No historical pre-game lines exist** (Kalshi sports series start 2026-10-28). The pre-game input is a walk-forward team rating, updated only after each game, standing in for the line. A real line is sharper, so these Briers describe the in-play math fed by a weak pre-game prior, and **do not say how it compares with the market**.

## Part A — NBA (training 2022-23 to 2024-25, 3,690 games; test 2025-26, 1,229 games; sigma² = 4.83 points²/min, home edge 2.05 fitted on training only)
| Checkpoint | Brier (95% CI) | Pre-game only | Mean p / home win rate |
|---|---|---|---|
| Q1 end (36 min left) | 0.191 (0.180–0.203) | 0.205 | 0.548 / 0.556 |
| Q2 end (24 left) | 0.156 (0.144–0.168) | 0.205 | 0.543 / 0.556 |
| Q3 end (12 left) | 0.120 (0.108–0.132) | 0.205 | 0.542 / 0.556 |

Spread (cover against a half-point line at the rated margin): Brier 0.222 / 0.182 / 0.134, mean p 0.496 / 0.492 / 0.488 against a cover rate of 0.491.
Calibration: the highest-probability bins run a little over-confident (Q3: model 0.977 → actual 0.968; model 0.143 → actual 0.28 in the 0.1 bin, n = 93). Likely cause: one pooled sigma² ignores late-game fouling/garbage-time structure. Not tuned on the test set. The overtime edge is not modelled (a regulation tie is split 50/50), and the home win rate counts OT.

## Part B — NHL (training 2021-22 to 2024-25, 5,248 games; test 2025-26 regular season, 1,312 games, one row per checkpoint)
Rates: pre-game goals per 60 from a walk-forward attack/defence rating. State multipliers were fitted on training seasons only. **Power play:** the power-play side scores 2.4x its baseline and the short-handed side 0.35x. **Empty net:** the trailing team scores 7.1x its baseline and the other side 2.7x. Overtime and shootout: 5-minute 3v3, shootout home share 0.508 (train).

| Checkpoint | Game win Brier (95% CI) | Pre-game only | Regulation tie: model / actual | Total over 5.5: model / actual |
|---|---|---|---|---|
| End P1 | 0.214 (0.205–0.225) | 0.250 | 0.168 / 0.248 | 0.512 / 0.573 |
| End P2 | 0.147 (0.137–0.158) | 0.250 | 0.174 / 0.248 | 0.533 / 0.573 |
| P3, 10 min left | 0.119 (0.108–0.131) | 0.250 | 0.187 / 0.248 | 0.521 / 0.573 |
| P3, 5 min left | 0.101 (0.090–0.111) | 0.250 | 0.194 / 0.248 | 0.519 / 0.573 |

- **Exact settlement:** regulation 3-way and the OT/SO-inclusive game win are returned separately, because Kalshi products settle on different definitions. This is verified in the tests, down to the horn.
- **Score effects: not modelled.** Training even-strength rates by lead: tied 2.52 / 2.40, home ahead 2.70 / 2.48, away ahead 2.64 / 2.54 (home / away goals per 60). The leader's rate is not lower; the effect is small, and the shot store supports it, so it is left as a registered next step.
- **Misses to know:** the tie under-prediction and the totals under-prediction show goals are over-dispersed relative to Poisson (and the rating proxy runs low on 2025-26 scoring). The game-win probabilities are better calibrated than the 3-way (bins within ~3 points except the top and bottom bins: model 0.88 → actual 0.825 at the end of P1, n = 177).
- **First run (kept for honesty):** v1 applied the fitted even-strength multiplier (0.84) to all remaining time, which double-counted the power-play mix already in the pre-game rate. Totals were badly under-priced (P1: model 0.407 / actual 0.573). Found by inspecting the diagnostic before anything was scored as a result; v2 sets the EV multiplier to 1.0 (model definition, not tuned on test outcomes). The v1 JSON is in the scratchpad and is not carried forward.
- State at checkpoints: P1 and P2 ends are even strength by construction (clock stopped); P3 10 min left has 214 power-play states of 1,312; P3 5 min left has 186 power-play and 37 empty-net states of 1,312, so the empty-net multiplier rests on 37 test rows at the 5-minute checkpoint (and 331+870 training goals).

## Part C — against the market: STOPPED, n = 0 each
- **Archive:** `PRICE_ARCHIVE/prices_*.jsonl` holds KXNBA{GAME,SPREAD,TOTAL,TEAMTOTAL} and KXNHL{GAME,SPREAD,TOTAL,TEAMTOTAL} from 2026-10-28, snapshots about every 20 minutes. Snapshots exist during live play.
- **NBA:** there is no 2026-27 NBA event store (pbp files end at 2025-26), so the score at a snapshot cannot be known. Not scored.
- **NHL:** the 2026-27 event store has 231 games with play-by-play but **only game-clock time, no wall-clock timestamps**, and snapshots come every ~20 minutes. Game length (intermissions, stoppages) varies by tens of minutes, so which score a given snapshot saw cannot be recovered reliably. Not scored.
- **What would unblock it:** log wall-clock (or capture ESPN/NHL live feed) timestamps beside in-play score during games; then Part C is a one-script job. Registered as a next step, not built here (out of block scope).
