# Muse prompt — send as one message when Earl's Muse chat resets (2026-11-16 ~20:50 PT)

Written by SW-9 on 2026-11-16 16:30 PT from Muse's archive (read-only, GitHub API at b6994a7, 2026-11-17 00:06Z), Muse's STATUS.md
"For Earl's Monday message", the 11-12 watchdog sweep, and the window's notes (04_EXECUTION/MUSE_MONDAY_2026-11-16_NOTES.md). Muse acts
only on what is in Earl's message (charter v3), so the whole instruction is the fenced block.

**The week (11-13 01:00Z → 11-17 00:06Z):** about 620 DONE, 29 NONE, 10 REOPEN, 1 MISSED. The NONE rate fell from ~1 in 3 (11-10) to
~1 in 20 once the dead NBA.com tracking slugs were behind it. Snapshots: every type has a file every day 11-12 → 11-16 (NBA lineups and
refs, NHL goalies and refs, NFL inactives on 11-12 / 11-15 / 11-16); NHL refs went down 11-13 (source post not found). The reserve fired
(MoneyPuck game-level, C-1378 → C-1751); the highest chunk claimed is C-1540, so **211 chunks remain - about 1.4 days**. Without a new
queue, Muse runs out around Wednesday and falls back to re-verification.

**Not Muse's doing, for Earl:** the watchdog sweep has failed to start every night since 11-13 (an Anthropic-side environment error,
"runner failed before Claude Code started (disk)"), so no mid-week fixes reached Muse since 11-12. And the 11-12 sweep notes Muse's runs
reported their fetch of TO_MUSE.md "flagged by a safety check", so even working sweeps may not land. This message is the reliable channel.

**Window's recommendations on Muse's open decisions are written into the block as decisions; change any before sending.**

```
Muse - from Earl, 2026-11-16. Strong week: about 620 chunks DONE and the NONE rate down to about 1 in 20. This is my only message until
next Monday. Do these in order; report each in STATUS.md.

1) DECISIONS ON WHAT YOU RAISED.
   a) SSH route: switch the standing route to GitHub's port 443 (ssh.github.com:443) for every push and fetch; keep port 22 only as a
      fallback. Record the change in STATUS.
   b) Big files: no committed file over 50 MB, ever. Split a claims file into parts (e.g. by month or by game range) before committing.
      C-1378 / C-1379 stand as compacted; split them too if they are over 50 MB.
   c) MoneyPuck game-level metric names: the shared form wins (metric name alone; game and situation go in applies_to / split). Re-record
      C-1378 and C-1380 in that form from their committed raw files - no new downloads.
   d) MoneyPuck game-level record ids: the family-standard `col-cNNNN-` prefix wins. Re-record C-1386 to that prefix from its committed
      files.
   e) C-743 / C-744: re-record to split "all", like the rest of the quarter family (C-658..C-661 precedent), from committed transcriptions.
   f) NHL referee snapshots (down since 11-13, "Scouting The Refs post not found"): keep trying the same source at each snapshot time
      and record MISSED with the reason when it is absent. Do not switch sources. If you find another free source that publishes NHL
      crews before puck drop, write a source card for it and put it under "For Earl's Monday message" - I decide next week.
   g) The open fixes from the 11-12 watchdog sweep stand, first: NHL goalie snapshot game_id as HOME-AWAY-YYYY-MM-DD; the daily STATUS
      line within an hour of the day's last snapshot run; re-read CLAIMS.md for an earlier claim before any DONE; the 26 "All" quarter
      chunks in the family form from committed transcriptions; the archive commit author name back to "Seat". Skip any already done and
      say so.

2) NBA.COM METHOD (the shot-clock and tracking NONEs were a reading problem, not a source problem).
   a) On NBA.com stats pages, read the JSON response the page itself requests - one request per filter value (e.g. per shot-clock band) -
      from inside the browser session, and record that request URL in provenance. Never the rendered table.
   b) 3 NONEs in one family for the same reason = pause that family (rule 5c below), move on, re-probe once a day with the JSON method.
   c) Re-verify every DONE chunk in the shot-clock family with the JSON method, C-400 first; a mismatch reopens it. The dead team slugs
      (catch-and-shoot, paint, post, elbow touches) get one JSON-method probe each; if the JSON serves them, re-open those chunks.

3) NEXT QUEUE - about 1,000 chunks for the week, pre-checked (fetch ONE page per family first; if it does not serve the table, filter
   and season, do not add the family and say why). Append from C-1752 on, after the MoneyPuck game-level family. Every family gets a
   source card naming the engine and factor it feeds. JSON method for everything on NBA.com.
   NBA, player level, one chunk per team (30 per table per season):
     - player shot dashboards: general shot type, shot clock, dribbles, closest defender, touch time - 2025-26 and 2024-25;
     - player tracking: drives, passing, rebounding, catch-and-shoot, pull-up, defense, speed / distance - 2025-26;
     - player hustle - 2025-26;
     - league matchups (offensive player vs defender: matchup minutes, partial possessions, points, FG) by offensive team - 2025-26
       and 2024-25.
   NBA, team level: 5-man lineups per team, 2024-25 (the current season is in the reserve already).
   NHL (MoneyPuck free downloads): line and pairing files by situation (all, 5on5, 5on4, 4on5), seasons 2014-15 to 2025-26.
   Skip anything the bot captures itself: Kalshi prices, MLB Statcast pitches, NBA official injury reports, NFL play-by-play, NHL
   play-by-play and shifts.

4) RUNS: unchanged - 200 a day: about 150 queue, 25 snapshot runs at their times, 25 ticket runs (when no ticket is placed, a ticket run
   works the queue under the same claim rules). No new recurring jobs.

5) STANDING RULES - unchanged from my 11-09 message: (a) under 150 unclaimed chunks, open the reserve - this week: player shot dashboards
   2023-24 and player tracking 2024-25, same per-team chunks; (b) queue truly empty: re-verify DONE chunks older than 7 days, then missing
   provenance, then a QUEUE EMPTY line - never invent a new kind of table; (c) 3 consecutive blocks in a family = BLOCKED with the reason,
   re-probe once a day; (d) a changed table shape is a new chunk version, never mapped onto old names; (e) stale claim after 6 hours:
   release and reclaim; gate failure: one retry, then BLOCKED; (f) never two runs on one chunk; (g) a snapshot source down at its time:
   one more try within the hour, then MISSED with the reason - never back-filled from another source; (h) anything you are unsure of goes
   under "For Earl's Monday message" and you carry on.

6) Gate, spot-checks and provenance exactly as now. Each day in STATUS.md: runs, DONE / NONE / BLOCKED / FAILED / RETIRED / REOPEN,
   chunks left, reclaims, and snapshot coverage per sport.
```
