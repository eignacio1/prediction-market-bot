
## W73.3 — NFL engine scaffold (DEPTH)
We built one football simulator that prices the winner, the spread, the total and each team's total from the same set of simulated games. It scores the same as the existing models, not better, so no accuracy was gained. Its value is that props, parlays and live pricing can now be added on top. The extra claim that it would handle key scores like 3 and 7 better did not hold up. No orders, no money, no sizing changed. Distance-to-optimum measure D4 (NFL) moved from none to scaffold stage.

## W73.1 — practice-money order test (EXECUTION)
The practice-order test had switched itself off for about 13 hours: its safety check counted old failures from before a fix. I corrected the check and turned the test back on; it is placing orders again. No real money was ever involved. The basketball practice orders were already running, so I did not build a second system for them. The first finished results are hockey only, and far too few to judge anything. A pattern worth watching: orders priced to the market's current book fill much less often than the simple ones.

## W73.2 — NFL data layer (plain English)
We now have a full, automatically refreshed library of NFL play-by-play, player, injury and schedule data, back to 1999, all from free public sources. A built-in guard makes sure any future model can only see information that was public before kickoff, so it can't accidentally "peek" at the result. It rebuilds itself every Tuesday and was tested end to end today. No bets, no money, no settings touched. This moves the NFL "depth" measure from nothing to a working data foundation. Nothing needed from you.
## B74-A S1 — full hygiene audit (PLUMBING)
I checked the whole codebase and the live system and wrote it up in HYGIENE_AUDIT_20261015.md. The verdict is sound with issues, and it is better than on 10-13. Two issues are serious. The emergency stop is split in two and the two halves can disagree. Four football positions have stayed open 4-7 days after their games. Twenty-two items are logged as GG-745..766. One test failed, but I ran it on the wrong library version, so I can't yet say it is a real problem. I changed no code. The next session reviews the runtime map and builds the dashboard panels.
- T-985 (auto): Seat interface (4 sports) + NFL/NBA tension registers + ARCHITECTURE_COMPONENTS; D4/D5 now generated
