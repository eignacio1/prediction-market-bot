
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
