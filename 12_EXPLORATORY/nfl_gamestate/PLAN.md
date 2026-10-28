# W89.4 -- NFL game-state chain -> one simulation prices the whole board (EXPLORATORY, offline)

Pre-registration, written before any held-out score was read. Nothing here is live: no model, runner, ledger, gate or registry cell.
Purpose (Hard Rule 12): DEPTH, measure D4 (NFL: data layer + scaffold -> whole board priced from one engine, offline) and the number of families priced from one joint distribution.

## Design
- Chain: play-level absorbing chain. Transient state = down x ydstogo bucket (<=2, 3-5, 6-9, 10, 11+) x yardline_100 bucket (<=5, 6-10, 11-20, 21-35, 36-50, 51-65, 66-80, 81+). Absorbing = TD, FG, safety, opp-TD, missed FG, punt, turnover, turnover on downs. End-of-half drives censored.
- Estimated on nflverse play-by-play of seasons strictly before the test season. Sparse rows (<15 visits) borrow the nearest field-position bucket, same down/distance.
- Team strength enters point-in-time as off/def points-per-drive ratings (365-day half-life, 80-drive league prior, fitted home-field constant). One scalar theta per offense-vs-defense pairing exponentially tilts every row (`quant.absorbing.exp_tilt`, value = chain's own expected drive points) so the chain's expected points per drive match the rating.
- Game: drives resampled from per-theta banks, possession alternates, clock runs two halves, simplified OT (ties allowed). 2000 sims/game.
- Held-out: 2024 (train 2016-2023), 2025 (train 2016-2024). Regular season only.

## Pre-registered readouts (frozen)
1. Key numbers: sim vs actual frequency of |margin| in {1,2,3,4,6,7,10,14}. Expected: sim smoother than actual at 3 and 6 (no score-state or end-game behaviour). Reported descriptively.
2. Quant bar (c): chain-implied vs observed expected drive points at first-and-10, held-out, game-cluster bootstrap CI.
3. Board vs market, at the nflverse close: moneyline, spread, total. Paired Brier (sim minus market, and sim minus same-mean Gaussian), game-cluster bootstrap 95% CI. Pushes dropped. Expected modal outcome: sim does NOT beat the market (diff >= 0); shape not centre is the interesting part.
4. Shape-only ladder: sim distribution re-centred on the market line, read at strikes line +/- {0.5,2.5,3,3.5,6.5,7,10}, vs a Gaussian at the market line with training-season sd. Expected: no reliable difference except possibly near 3 and 7.
5. Team-total PIT (home): descriptive only, no team-total market in the free data.
Not run: props, parlays (no free per-game outcome joined), 2025 Kalshi KXNFLGAME candles (location unpinned; next block), frozen `nfl_pregame_v1` comparator (next block).

## Verdict rules
- A family is "matched" only if the paired Brier CI vs the market contains 0 and the point estimate is within +0.005; "worse" if the CI is entirely above 0; "better" only if entirely below 0 (not expected). Two held-out seasons are reported separately and pooled; n is ~270 games per season, so intervals are wide and a null is the likely reading.
- D4 stage is claimed only as: "whole board (ML, spread, total, team totals) read off one joint simulation, offline" -- not as an edge claim.

## Known limitations (stated up front)
No score-state or garbage-time dependence; no two-minute-drill clock behaviour; simplified OT; no injuries/QB/weather in the ratings (team rating is aggregate points per drive); the market close is more informed than anything here.
