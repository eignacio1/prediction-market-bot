
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
