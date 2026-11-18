
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
