# Operator Digest — 2026-10-05

- W53.2 (auto): W53.2 read-only shadow audit: NHL+NFL log valid rows, crontab matches deploy; 12 MLB shadow cells unscheduled (GG-453).

## W54.2 — MLB shadow cells (plain English)
- The safety upgrade (GG-432) is live and checked on the server; the live MLB bot was not restarted.
- The 12 MLB "practice" checks (no money, no orders) are now scheduled on the server.
- They have not recorded anything yet. The MLB data site rejects the server's requests off and on, so the daily-data refresh stops itself rather than use old data.
- Still zero real money at risk.
- Your call: wait a few days and see if it clears, copy the data over from your Mac each day, or route the server's requests through a different network.

**W55.2 (plain English):** The big update from the last few days is now live and working on the dashboard. No real money is at risk and nothing about betting changed. The data tracker restarted itself overnight because the small server ran out of memory (too many jobs started at the same minute). I added extra memory to the server, which should stop it. A second fix, spreading the job start times apart, is written but not yet applied because the safety layer blocked me from changing the server directly. We'll know it worked after tomorrow night's 01:30 UTC run.

**W55.1 (ledger booking):** 26 old paper positions that Kalshi had already settled are now counted in the books. 16 of them were cancelled by Kalshi and are marked so they don't count toward the G6 gate. The MLB T1 book's losses now stand at 12.4% against a 20% stop, and the T4 book's at 13.5%. No real money was involved. One open item: the kill switch only reacts to losses once they're booked (GG-441).

**MLB shadow betting data (W55.3).** The MLB shadow tests were stuck because the server can't reach MLB's stats site. Fixed by refreshing the data on your Mac and copying it to the server; 69 pregame test rows are now being recorded. No real money or sizing changed. What you need to do: run `scripts/sync_mlb_games_cache.sh` from your Mac at least once a day, or these tests stop after 26 hours. Automating that is the next open item.
