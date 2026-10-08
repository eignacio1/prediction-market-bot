
## W59.3 — NBA readiness, NHL goalie check, ADR-0070
- Still zero real money at risk; nothing here changes any bet or stake.
- NBA: practice-game (preseason) readings are now saved separately and clearly marked as not counting toward results. The dashboard knows NBA season starts Oct 20.
- Hockey goalies: the league's data does not name the starting goalie before the game, so we cannot follow the original plan. One decision for you: switch to using the expected starter at every stage. Wording is in the results document, Part B.
- The paperwork approving the new forecasting method (ADR-0070) is now signed off and covers hockey and basketball too.
- Small leftover: the dashboard hides the NBA row until real data exists; it should say "no data yet". Logged as T-732.

## W59.1 - the gap log gets true
Every open item in the issue log was re-checked against fresh evidence; 45 were closed, the rest carry a dated status and a next step. The server's schedule file in the repo now matches what actually runs. No money, orders or sizing were touched. Two things to look at: the player-hits strategy is net negative since the last reset, and several thousand closed positions were never re-checked with the venue.

**W59.2 — calibration correctness (plain English).** The dashboard's "when do we get our first real look" dates now come from each sport's actual schedule: football's first look is about 2 November, hockey cannot reach its sample target this season, and baseball has no date until its 2027 schedule is published. The first look is now locked to exactly the first 60 settled games, so a late-settling game can't change it. I checked all 1,229 settled football and baseball markets against Kalshi's own results: every one agrees, none were changed. Still zero real money at risk. Your decisions needed: how to order "the first 60 games", a hockey seed, whether hockey's target stands, and whether baseball needs a baseline.

## W60.1 — Is the active test cohort real? (2026-10-08)
Short answer: mostly no. Of the 1,952 recorded paper bets in the current cohort, only 107 (about 5%) correspond to an order the practice exchange actually filled. The rest were never executed, though our books still scored them as if they were. The 107 that did fill are losing about 40 cents per bet. Nothing real is at risk (still paper money), but the 30-bet progress toward going live is built on mostly unfilled orders. Also fixed: the Monday job that could silently overwrite the results file now refuses to. Your call: should the go-live count include only filled orders, and should the bot check fill status at entry going forward?
