# Index entry: run success by box count (loaded ≥8 vs light ≤7) — W80.3

Run: `12_EXPLORATORY/nfl_engine/granularity_index/` (`run_box_entry.py`, `part_b_interpret.py`, `part_b_apply.py`; results in `results/`). Data: nflverse pbp + FTN box count, regular season, 2022–2026 to week 6 of 2026. Rush = run plays excluding kneels, scrambles, two-point tries. 57,274 rushes; 56,577 (98.8%) have a box count.

**Stage reached: applied — result: no gain beyond season-long ratings; application too few to tell.**

## 1. Split
League success rate: 0.420 loaded vs 0.408 light; stuffed rate (yards ≤ 0) 0.245 loaded vs 0.174 light. Defenses show a light box about 91% of the time (range 0.63–1.0), so the loaded bucket is thin per team.

## 2. Rank against history
Every unit gets rank in league and rank against the 160 unit-seasons of 2022–2025 (`rank`). 2026 example: JAX, TB and MIN are the top three light-box defenses by success allowed (MIN 0.304, rank 1 of 32, 5th of 160 historically).

**The operator's example, tested.** "#2 loaded, #26 light" is the pattern the stability gate exists for. Split-half stability, CI lower bound > 0 = trait:
- Loaded-box splits: **not a trait** at g=8 or g=12 (CIs span 0; k = ∞, so deviations shrink fully to league mean). A team's #2 loaded rank is mostly noise at current n.
- Light-box stuffed rate: **a trait**. Offense: r_SB 0.35, CI [0.14, 0.51] at g=8 (160 unit-seasons). Defense: 0.33, CI [0.07, 0.53] at g=12.
- Light-box success rate: not a trait (offense marginal).
So the "gets tackled behind the line on 75% of runs against light boxes" half of the example is the stable, usable signal; the loaded-box half is not yet.

## 3. Matchup cross
`cross` combines the offense's shrunk deviation with the opponent's in each bucket, weighted by how often the defense shows it. 2026 deltas are small: success rate within about ±1.9 points (max +0.018 NE vs MIN wk14; min −0.019 BUF vs MIA), stuffed delta max about +0.026.

**Part B interpretation** (2022–2025, leave-one-season-out, game-cluster bootstrap, n=1,746 team-games): weighted MSE base 0.011375, with cross 0.011380; gain −4.6e-06, CI [−1.2e-05, +3.1e-06]; corr(d, residual) = −0.003; sd(d)=0.0066. **The cross adds nothing beyond season-long ratings on rush success.** Team rushing yards was not tested.

## 4. Market map
KXNFLRSHYDS (285 events / 9,083 settled), KXNFLRSHATT, KXNFLMOSTRSHYDS, KXNFLLONGRSH, KXNFLTEAMTOTAL (125 / 3,016), KXNFLSPREAD (430 / 10,805), KXNFLTOTAL (430 / 8,472), KXNFLTEAMYDS.

## 5. Application (read-only, 77.2's method)
Kalshi 2025 thin sample: 116 candle tickers for rushing yards and team total; 58 had a pre-game candle (mid about 30 min before kickoff); n = 57 markets (43 RSHYDS, 14 TEAMTOTAL), 51 games. Slope of family-demeaned logit price on d: 6.1, CI [−44.9, 58.7]. Slope of outcome residual (y − p) on d: −12.7, CI [−37.8, 15.1]. **Too few markets to tell**; with sd(d) near 0.005 the design could not detect a realistic effect. `last_price_dollars` is post-game and was not used as a price.

## Operator question 1 — how would a bet be placed pre-game?
1. Compute the entry's cross for the game (offense deviation × opposing defense deviation, trait-gated buckets only). Here the usable piece is the light-box stuffed rate.
2. Convert the delta into a shift of the rushing model's expected rushing yards or attempts for that team, via the engine's rate layer. This conversion has not been calibrated; today's measured effect is zero.
3. Compare the shifted distribution to the Kalshi rushing-yards or team-total price from the market map; an edge needs model p to exceed market-implied p plus vig by the cell's pre-registered margin.
4. Size and place only through a registered cell (none exists for this; demo and shadow only, kelly_fraction 0). Not done here.

## Operator question 2 — how would it be decided mid-game? (design only)
The box count is a per-play fact, so in-play the entry becomes a live state read: after each play, update the team's observed loaded/light show frequency and success against the pre-game prior (a Bayesian update with the same shrink constants), and re-price the remaining-rushing distribution. A mid-game bet requires (a) the live box count from a feed with latency below the market's repricing time (FTN and participation are post-game, so no free live source today: registered gap), and (b) the horizon test of ADR-0068: a shallow in-play tree must be paid for in measured speed. Nothing is built for this.

## Result
Machine built and tested; the example taken through all five parts. Honest finding: the loaded-box rank is noise at current sample sizes, the light-box stuffed rate is a stable trait, and neither yet moves rushing prices measurably.
