
## W121.4 - dashboard panels (Sonnet)
The Live Terminal now shows the new router maps beside the current one (how often they agree, and the rows where they differ), D6 cell names on hover, the weekly look, and box disk. All live on the box. The weekly Mac copy job is installed and first runs Sunday 3am. One catch: the page can't show the Mac copy's result when it runs on the box (GG-1958) - the window picks the fix. Still zero real money at risk. PLUMBING.

## W121.1 — the weekly look now runs (Sonnet)
The weekly check on whether any betting pattern has earned a route now exists and ran once on the box's real rows. Result: no pattern has earned a route yet, on any sport. The three new candidate routers have no settled games yet, so this first look says nothing about them. Nothing runs on its own until you say "approve evidence_weekly_install". No real money, nothing placed. One small gap logged: the box has no task to pull new code, so I did it by hand over ssh. Next look Tuesday 11-24.

## W122.4 — MLB board priced, opening-day dry run (plain English)
- We can now price the whole MLB game board (who wins, run line, totals, team totals) from our pitch data, and it ran clean on a replayed 2026 day: 12 game cells each wrote a row. Nothing is live; it waits for the 2027 schedule.
- Against Kalshi's own closing prices (Aug–Sep 2026) our prices are the weaker ones on every family. So the engine feeds the tree as an input; it is not a bet by itself.
- Why 2026 left no game rows: the schedule feed went stale, the runner quit without a trace, and the crons were armed late. Now it checks itself daily and records every quit.
- Still zero real money at risk. Open stray branches from earlier waves (not mine, not merged): the NBA injury-report data branch and about nine old wave branches. Your call on routing.

## W122.3 - NFL (plain English)
The ask was to price 17 NFL markets we weren't pricing. 16 of them are in-game markets, and we have no live NFL feed, so they can't be priced yet. That needs its own build. The 17th, passing yards before kickoff, was fixable: we now record its price a day before kickoff, which is where its band sits. It's live on the box. We'll know it worked after Sunday's games (NFL cells with a price: 12 now, 13 expected). No real money touched.

## W122.1 — NBA player points (plain English)
The bot now prices NBA player-points markets with the same game engine it uses for rebounds, assists and threes, and logs them without placing orders. They started logging on the box at 17:39Z today. On games it hadn't seen, the points forecasts beat a simple base-rate guess at every line, though they run a little low on the easy lines. The count of fully wired prop cells did not move yet (still zero): the points cells are missing one layer, the market-state leaves in the main tree map. Fixing that is a design choice for you, not a bug. No money at risk, nothing live.
- B-TBD (auto): W123.2 H2 timing NOT SUPPORTED (H-EDGE-2 parked for R&D); 6h drift slope +0.017 [-0.024,+0.056]; CLV +0.86c vs fee 1.08c
- W123.4 (auto): W123.4 H4 execution: two-sided quoting NOT SUPPORTED (0 of 18 cells net > 0, spread minus fee negative everywhere); parked for R&D
- W123.4 (auto): W123.4 H4 execution: two-sided quoting NOT SUPPORTED (0 of 18 cells net > 0, spread minus fee negative everywhere); parked for R&D
- W123.3 (auto): W123.3 H3 news latency NOT SUPPORTED on NBA injury/starter news (+0.3-0.5c vs 1.9c cost); confirmations, NFL inactives underpowered
- W123.3 note: 7 old unmerged session branches sit on origin (oldest 14 days); they need your routing call, not merged by me.
- W123.1 (auto): W123.1: H1 NOT SUPPORTED on 18 judged non-headline families; 18 prop families UNDERPOWERED (no fit window)
