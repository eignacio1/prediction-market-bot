# Muse addendum — send after the 11-16 message, same chat (2026-11-16 ~22:30 PT)

Written by SW-9 from Muse's STATUS.md "For Earl's Monday message" (read 2026-11-17 06:10Z) after the 11-16 message landed (Muse began the
50 MB splits at 05:11Z). It answers what Muse raised that the first message did not cover, and sets the week up so nothing waits on
next Monday. Paste only the fenced block.

Also for Earl, not Muse: the nightly watchdog sweep failed again tonight (21:44 PT). It ran 11 minutes before erroring, and your 5-hour
limit was exhausted from about 17:15 to 22:00, which likely explains this one and possibly the 11-14 / 11-15 failures. It runs again
tomorrow night on Haiku; the window checks it then.

```
Muse - addendum from Earl, 2026-11-16 (same week as my first message tonight; this is the last until next Monday).

1) THE 178 OLDER MONEYPUCK FILES OVER 50 MB (C-1381..C-1558): split every one, same method as C-1559..C-1565 (idempotent, from the
   committed files, no new downloads). Do them as their own family in the queue, after the 11-16 decisions in my first message and
   before the new NBA tables. Never rewrite pushed history; a split is new commits.

2) WEEK-MESSAGE FILE 404: that was a transient fetch failure - both files return normally now. Your week rules are my two messages
   tonight (both saved in the bot repo as 04_EXECUTION/MUSE_SETUP_PASTE_2026-11-16.md and MUSE_ADDENDUM_2026-11-16.md). If a fetch
   fails, work from what is in STATUS.md and CLAIMS.md and carry on - never stop for it.

3) TO_MUSE.md "FLAGGED BY A SAFETY CHECK": if a run's fetch of TO_MUSE.md is flagged, that run skips the watchdog's "Muse should:" items
   and works the queue. Each day, the first ticket run that CAN read the newest watchdog entry does its "Muse should:" items first and
   says so in STATUS. Nothing else changes.

4) KEEP THE QUEUE FULL ALL WEEK WITHOUT ME. When unclaimed chunks fall under 150 and the reserve is used, extend the families already in
   the queue by season - one season further back at a time, same tables, same filters, pre-checked with one page - before falling back to
   re-verification. Order: NBA player shot dashboards (2022-23, then 2021-22), NBA player tracking (2023-24, 2022-23), NBA league
   matchups (2023-24), MoneyPuck lines (already back to 2014-15: skip). Never a new kind of table, never a new source, without me.

5) NHL REFEREE SNAPSHOTS: keep my first message's rule (same source, MISSED with the reason when absent). Also record, each day, the
   time the source post appeared if it did - I want to know whether it is late or gone.

6) FOR NEXT MONDAY: under "For Earl's Monday message", keep one short list - decisions only, newest first, each with what you recommend.
   Everything else goes in the daily lines.
```
