
## W109.1 — NBA betting architecture (depth)
- The NBA side of the bot now has all eight pieces of the betting architecture built and tested (it was four).
- We ran one full end-to-end test on NBA moneylines for last season and compared it to what Kalshi was charging an hour before tip.
- Result: Kalshi's price was more accurate than ours, and betting our disagreements would have lost money on paper. This matches an earlier NBA finding.
- Only Feb-Apr 2026 Kalshi history exists, so this used 397 games. No real money, no live bets involved.
- The count of NBA factors "applied" did not move, since nothing showed an edge.
## W109.2 - NHL architecture
Hockey now has five more of the eight building blocks in place and tested, so the architecture score for NHL went from 2 to 7 (the eighth needs player-type data hockey doesn't have). We also ran one real test: does a team playing on back-to-back nights change how many goals get scored? On three held-out seasons the answer was no usable signal, and the safety check correctly refused to bet on it. Still zero real money at risk; nothing changed in live trading.
- W109.5 (auto): W109.5 dashboard memory (#464) and MLB Features Sync off-season skip (#462) merged; MemoryMax 384M install (#468) prepared, awaits operator approval by name.

## W109.6 — demo-fill test stalled (2026-11-11)
The practice-money test that places pretend orders had stopped on Nov 5 and nobody was told. Cause: a safety switch tripped on old, known-bad data, then stayed off by itself every day after. I fixed the check so it ignores that old data, and added a warning that now fires if orders stop for a day while the models are still running. The warning is already showing on the live system.
I did NOT turn the test back on. One decision for you: approve the re-arm task `demo_fill_rearm` (I recommend yes). Heads-up: the test restarts with almost no clean data, so it needs time to build up. No real money was ever at risk.

## W110.2 — NBA factors (plain English)
- The NBA model can now use five more kinds of information when it prices games: who is missing from a lineup, travel and rest, referee crews, and our player-profile data.
- Tested on last season's games: knowing who is out helps predict point spreads and team totals. Travel and referees add nothing. Nothing helps picking the winner.
- Caveat: we have no last-season market prices for spreads and totals, so this shows the factors predict outcomes, not that they beat the market.
- Still zero real money at risk; no orders or sizing touched.

**W110.1 (NFL weather + matchup).** Moved DEPTH: NFL weather (forecast only, never realised) and matchup crosses are now built, tested and exported as filters for the router. Scored per leaf, net after costs, none of 82 leaves earned an arm (about 2 expected by chance). Momentum can't be scored yet: we have no opening-line history. Still zero real money at risk. No decisions needed from you.

## W110.4 — same-game parlays (research only)
We tested whether the NBA game simulator prices "several things happen together" bets correctly, using 1,075 finished games. It does well when linking a team result (win, total points) to a player's points. It does badly for one player's points and threes or rebounds together, and for two teammates' points. Kalshi has a same-game NBA combo product, but none is open right now, so there was no live price to compare against. No orders, no money, nothing running changed. Next step for the parlay idea is giving players a shared minutes/pace factor.

## W110.5 retro-route (PROOF)
We replayed every settled paper row (about 106,000 across NFL, NBA, NHL and MLB postseason) through the betting routes: ride the market, fade it, follow the move, or sit out. Each situation was sent to its best route using the earlier 70% of games, then checked on the later 30%. Most situations have too little data yet and default to sitting out. Riding the market beat fading it in every market family with data. One NHL moneyline situation looks strong, but it rests on only 11 games, so it is a lead and not a result. No pre-registrations were drafted, nothing went live, and no real money is involved.
