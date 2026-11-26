
## W129.4 — the player-state tables (plain English)
The system now remembers how each NBA player's role looked just before every game since 2016: how much the team leaned on them, who was out, how many minutes to expect, and how often they miss games. Each fact is stamped with the moment it could first be known, so nothing from the future can leak into a test. About 366,000 player-games were filled in and 30 were checked by hand against box scores (28 matched exactly; the other 2 differ only because the NBA Cup final is left out on purpose). The next test (does a backup keep his extra minutes when the starter returns?) is written down in advance and has NOT been run. No money, no betting rules changed.
- W129.5 (auto): W129.5 merged (PR #592): D6 from one box source (18/129, static 0 beside it), distance table, hypothesis registry 42->73 rows, 0 unregistered.
## W129.6 — NFL in-play (plain English)
We can now read live NFL game state for free, and the server can reach it. A pricer that updates the pre-game line as the game unfolds beats a "never update" price, but it does not beat Kalshi's own live price (a tie). Kalshi reacts to a scoring play in about 2 minutes. Nothing is logging yet: the shadow logger and the 8 NFL in-play cells are not built, so breadth is unchanged. No real money involved. Next: build the logger; first live games are Thanksgiving.

## W129.2 — NBA props challenger (shrunk rates)
Plain English: the new way of estimating each player's scoring, rebounds, assists and threes — leaning on a player's past seasons until the current season has enough games — beat the current method on last season's games, in all four stats. The gain is biggest early in a season and gone once a player has 30+ games. It now runs quietly beside the current method, with no orders and no money. Last season is not fully fresh to us, so this season's live rows are the real test. One thing for you: the NBA props logger is still switched off on the box until you approve its install (`nba_engine_props_shadow_install`). Zero real money at risk.

## W129.1 — NHL goalie / ref depth (2026-11-26)
- The NHL depth filter is now running in shadow on every NHL game. It logs only; it places no orders and moves no money.
- The "we don't know the starter" problem is gone on paper: 0 of 351 games, down from 53 of 99.
- Catch: every one of those 351 games falls back to the goalie's usual-start history, so none of it is real signal yet. Confirmed starters need Muse's files on the box.
- I need one decision from you: put a read-only GitHub token on the box, or approve copying the small Muse files into the repo. Until then the first real look is blocked.
- Not finished: I did not read one slate's rows back from the box after the deploy. Do that first next window.
- Real money at risk: zero.
## W129.7 — NHL in-play (breadth)
The bot can now price NHL games while they are being played, using the live score, clock and power-play state. Three NHL in-play markets (moneyline, puck line, total) are registered in shadow mode. They place no orders, and real money at risk is still zero.
On 231 replayed games the in-play prices scored far better than pre-game-only prices. That checks the pricer uses game state correctly. It is not a comparison with Kalshi.
Nothing is logging yet. The install step is built but not run. Say "approve nhl_inplay_install" and it goes in before the next NHL slate. The budget check was green.
Pillar moved: BREADTH.

## W130.4 — NBA player archetypes, point-in-time (merged, PR #603)
Built a player-type label for 469 NBA players that only uses games played before the date asked, so it can be used live without leaking the future. It matches the old hindsight labels on the top pick 35% of the time, and the hindsight label shows up somewhere in the mix 72% of the time. Zubac reads rebounder/rim big; Wembanyama reads rim protector. Two types (PRF-10, PRF-13) can't be built from our data. It now logs as a shadow arm (no orders). Test is pre-registered; likely outcome is "not supported" or "underpowered" (~65%). One deadline: the factor table must be frozen before 2026-27 scoring or the test isn't judged. Handed to the next window. Note: CLAUDE.md window-maintained lines are dated 11-18 (RED).

## W130.2 — NBA props demo orders (EXECUTION)
Built and merged the code that lets the 14 kept NBA player-prop leaves place $1 demo orders, with every fill measured. It is OFF. Nothing is installed, no real money, Kelly 0. One thing needs you: approve `props_arm_orders_install` (queue item 10) to turn it on. I have not yet read the box dry run (the box hadn't run it); it is listed as pending. Nothing can be scored until NBA games pass after install.

**W130.3 — combos on a schedule (demo only).** The daily combo quote-and-order job is now installed on the box, with the same approval you gave. It trades one demo contract at a time, at most $6 of demo loss a day, and only when our price beats the quote by a clear margin. Two earlier combo fills settled: one won, one lost, too few to say anything. I also fixed a bug where it would accept a bad quote. First scheduled run is 18:17Z today; I'll read it and report. No real money touched.
