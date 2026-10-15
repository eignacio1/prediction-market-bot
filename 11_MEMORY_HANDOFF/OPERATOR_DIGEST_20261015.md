
## W73.3 — NFL engine scaffold (DEPTH)
We built one football simulator that prices the winner, the spread, the total and each team's total from the same set of simulated games. It scores the same as the existing models, not better, so no accuracy was gained. Its value is that props, parlays and live pricing can now be added on top. The extra claim that it would handle key scores like 3 and 7 better did not hold up. No orders, no money, no sizing changed. Distance-to-optimum measure D4 (NFL) moved from none to scaffold stage.

## W73.1 — practice-money order test (EXECUTION)
The practice-order test had switched itself off for about 13 hours: its safety check counted old failures from before a fix. I corrected the check and turned the test back on; it is placing orders again. No real money was ever involved. The basketball practice orders were already running, so I did not build a second system for them. The first finished results are hockey only, and far too few to judge anything. A pattern worth watching: orders priced to the market's current book fill much less often than the simple ones.
