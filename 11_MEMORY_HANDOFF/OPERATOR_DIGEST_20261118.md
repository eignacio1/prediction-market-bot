
## W116.2 close - your approvals (2026-11-18 01:25Z)
- I recorded both of your approvals: the placement policy, and raising the demo caps. Neither is on yet.
- The caps go up once the fix that stops demo stakes from tripping the safety halt lands. That fix is written and waiting.
- The placement policy turns on only after enough orders that logged their spread have settled to fit its table.
- Both code changes are held up by one broken line in the shared backlog file, which another terminal owns. Once that's fixed, they merge.
- Still no real money and nothing changed in sizing.
## W116.1 — router v2 (Opus)
The new way of deciding which bets have earned their arm is built, tested and frozen, but it is not merged yet. On past games
it would have placed no bets at all, and today that beats the old router, which loses a little per bet. It is switched off,
and turning it on just for logging is your call (in the queue). We also found and fixed a flaw that let the old version of
this test claim a winner almost every time when nothing was there. The merge is stuck on a backlog file the strategic window
owns (GG-1955), not on this work. No real money anywhere.

## W116.3 — D6 finish (parked)
- The crash that made the betting router error on thousands of NBA/NFL/NHL rows is fixed and live; re-running the old failures on today's code, none crash.
- Still 3 of 117 cells wired end to end, all NBA. NFL cells wait because none of its factor splits held up in testing; NHL waits on its data store reaching the box.
- The NHL data store was shrunk to fit the box (about 320 MB instead of 2 GB). Installing it needs your OK by name (`nhl_event_store_install`), and the box is low on free memory.
- The last code change can't merge: main's backlog file has two items at order 16, which turns every code PR red. The strategic window fixes that (GG-1955).
- No real money; Kelly still 0.

## W117.0 cleanup (B-098)
All four parked Wave 116 changes (#505, #506, #507, #508) are now live on main, each only after its tests passed. The box is running the new code. Old branches went from 16 to 10 plus main; the ones with unsaved work, the two data branches, and anything with an open PR were kept. Nothing was installed on the box: the NHL data-store install is waiting for your approval by name. No real money moved; this was housekeeping only.

## W117.2 — NHL history as a head start (no real money, nothing live changed)
We tested whether a season of free NHL closing lines helps the router learn faster. It does, a little: the first bet it can justify
moves 1 to 7 weeks earlier, but still not before 2027. Using coarser buckets did not help; it made things slower.
Two ideas closed as tests, not as markets: the closing line under-reacting to its own movement (all three markets), parked for later.
Riding the books' favourite on Kalshi loses about 5.5 cents per contract after fees; Kalshi already prices like the books.
One ask for Monday: a free 2026-27 closing-line source, so puck lines and totals can be checked against Kalshi too.

**W117.3 (NBA wiring).** The count of bet types fully wired through all seven layers went from 3 to 4, all NBA. We can now price NBA moneylines and team totals from the game simulation, and the checks agree with the spread-implied odds. The box health alarm that said a cron job was missing was a false alarm from a bug in the check itself; fixed, and the box now reads healthy (one warning: disk 87%). No real money at risk. Next: NBA moneyline/spread/team totals need more rows before the tree can pick an arm.

## W118.2 — NBA depth splits (B-101)
We built five new NBA factors (pace and net rating, shot-zone matchup, lineup status, home/road gap, referee crew) and tested each one on the last five weeks of logged NBA forecasts, which are paper rows, not real fills.
None passed the strict significance test. The best lead is shot-zone matchup on spreads, which looked positive but is far too thin to trust yet.
Lineup status and referee crew could not be judged, because their data only starts 11-10. They are parked, not closed, and we re-test in about four weeks.
Nothing is wired into the bot yet (that is 118.3). Still zero real money at risk.
