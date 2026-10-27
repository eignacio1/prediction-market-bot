
## W87.2 — kill switch on every order path (PARTIAL)
- The kill switch now watches the MLB T1 book and all shadow books on the box. The MLB T4 book joins once t4-mlb restarts; it was left running because a game was live.
- Every order now asks the switch first, but it is only logging what it would have blocked. Nothing is refused yet.
- Next: after one full game day, read that log, explain every would-halt, then flip to enforce in a separate PR.
- GG-1082 and GG-441 stay open until enforcement is on and read back on the box.
- No limits, stakes or orders changed. No real money involved.

## W88.2 (partial)
Still zero real money at risk. We found why the MLB game-market tracker went quiet: its data feed stopped refreshing after the season's last game, and that is fixed. Shadow records now carry when the price was read. Not done: switching the safety stop from "log only" to "enforcing". It waits for tonight's game to end. Nothing needs you for it.
## W88.1 — how bad can a losing streak get, and what does "ready for real money" mean
- Measured how large a one-in-a-hundred bad game and bad stretch could be for the MLB books. The T4 book's bad stretches stay inside the 20% stop at flat stakes; the T1 book's do not, even with no edge. Samples are small (14–99 extreme games), so treat these as rough.
- Wrote a DRAFT rule for what "ready for real money" means, per book and sport (ADR-0076). Nothing takes effect until you accept it. No real money, no stake or limit changed.
- Your call: accept, change or reject ADR-0076 (recommendation: accept, leaving the blank limits blank until a stake size is proposed).
- Pillar moved: PROOF (G6 rule 0 → draft).

## W88.3 — frozen models vs the market
Today we checked three of the bot's pre-game models against what the market actually priced, on games they had not seen. None beat the market: hockey and basketball are slightly worse than the market, baseball is a tie. So the safety gate would place no bets from them, which is the correct answer. No real money at risk, nothing live changed. Two models (player points, football QB) could not be scored yet and are listed as such.

## W89.3 — which factors does the betting line not price? (NFL)
No change to money: still zero real capital at risk. We tested whether three kinds of football information (who is available, venue, weather) tell us anything the betting line has not already absorbed. The line has absorbed most of it. A forward test of the weather-and-venue idea on totals did not beat the line, and none of the three clears the cost of trading. This is a "not yet" on weather, not a "never": our baseline for scoring is weak and wind forecasts were mostly missing. NBA was not tested because the price history it needs is not stored yet. Moves the depth pillar: measured factors 1 to 3, clearing costs 0 to 0. Recommendation: keep building (better scoring baseline first), nothing to pre-register.
