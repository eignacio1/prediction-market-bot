
## W109.1 — NBA betting architecture (depth)
- The NBA side of the bot now has all eight pieces of the betting architecture built and tested (it was four).
- We ran one full end-to-end test on NBA moneylines for last season and compared it to what Kalshi was charging an hour before tip.
- Result: Kalshi's price was more accurate than ours, and betting our disagreements would have lost money on paper. This matches an earlier NBA finding.
- Only Feb-Apr 2026 Kalshi history exists, so this used 397 games. No real money, no live bets involved.
- The count of NBA factors "applied" did not move, since nothing showed an edge.
## W109.2 - NHL architecture
Hockey now has five more of the eight building blocks in place and tested, so the architecture score for NHL went from 2 to 7 (the eighth needs player-type data hockey doesn't have). We also ran one real test: does a team playing on back-to-back nights change how many goals get scored? On three held-out seasons the answer was no usable signal, and the safety check correctly refused to bet on it. Still zero real money at risk; nothing changed in live trading.
