
## W121.4 - dashboard panels (Sonnet)
The Live Terminal now shows the new router maps beside the current one (how often they agree, and the rows where they differ), D6 cell names on hover, the weekly look, and box disk. All live on the box. The weekly Mac copy job is installed and first runs Sunday 3am. One catch: the page can't show the Mac copy's result when it runs on the box (GG-1958) - the window picks the fix. Still zero real money at risk. PLUMBING.

## W121.1 — the weekly look now runs (Sonnet)
The weekly check on whether any betting pattern has earned a route now exists and ran once on the box's real rows. Result: no pattern has earned a route yet, on any sport. The three new candidate routers have no settled games yet, so this first look says nothing about them. Nothing runs on its own until you say "approve evidence_weekly_install". No real money, nothing placed. One small gap logged: the box has no task to pull new code, so I did it by hand over ssh. Next look Tuesday 11-24.

## W122.4 — MLB board priced, opening-day dry run (plain English)
- We can now price the whole MLB game board (who wins, run line, totals, team totals) from our pitch data, and it ran clean on a replayed 2026 day: 12 game cells each wrote a row. Nothing is live; it waits for the 2027 schedule.
- Against Kalshi's own closing prices (Aug–Sep 2026) our prices are the weaker ones on every family. So the engine feeds the tree as an input; it is not a bet by itself.
- Why 2026 left no game rows: the schedule feed went stale, the runner quit without a trace, and the crons were armed late. Now it checks itself daily and records every quit.
- Still zero real money at risk. Open stray branches from earlier waves (not mine, not merged): the NBA injury-report data branch and about nine old wave branches. Your call on routing.
