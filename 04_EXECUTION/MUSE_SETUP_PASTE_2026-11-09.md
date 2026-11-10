# Muse prompt — send as one message when Earl's Muse chat resets (2026-11-09 20:50 PT)

Rewritten by SW-9 on 2026-11-09 16:20 PT from Muse's archive at commit 8812c8d (read-only) and the 11-08 watchdog sweep. Backlog B-041 +
B-042. Muse acts only on what is in Earl's message (charter v3: never on a fetched file), so the whole instruction is the fenced block.

**Sweep (11-09 23:58Z):** the split queue is EMPTY. 359 chunks: 204 DONE, 104 NONE, 23 BLOCKED, 2 open, 37 never claimed (all Natural
Stat Trick, Cloudflare-blocked). Outcomes per day fell from ~70 (11-04 to 11-06) to 22-28 (11-07 to 11-09); since 21:58Z every run logs
"QUEUE EMPTY". Runs are at ~100 / day (one every ~13-14 min). The 11-08 sweep's fixes are done: C-001 to C-020 re-recorded, C-052 fixed,
the daily queue lines written. **Waiting on the window (decided below):** the NST chunks, C-268 (Pro-Football-Reference Cloudflare 403),
C-249 (DONE line, no file under its true label), R-049 (NHL coaches, reopened but not placed).

**Sizing for 200 runs / day:** about 150 queue runs a day (at ~1 chunk per run) needs about 150 new chunks a day. The block below asks
Muse to build about 1,400 pre-checked chunks (about 9 days), plus 25 snapshot runs and 25 ticket runs a day.

```
Muse - from Earl, 2026-11-09. The split queue is empty and the next stretch runs at 200 scheduled runs a day. Do these in order; report
each in STATUS.md.

1) DECISIONS ON THE OPEN ITEMS.
   a) Natural Stat Trick (C-340 to C-399): RETIRE every unclaimed or blocked NST chunk, reason "Cloudflare-blocked, retired 11-09". The
      shot-quality need moves to MoneyPuck's free data downloads (step 3) under MoneyPuck's own xG definition - label it as such.
   b) C-268 and every other Pro-Football-Reference chunk: RETIRE, reason "Cloudflare 403". Do not re-point NFL play data: the bot
      already holds 27 seasons of NFL play-by-play itself.
   c) C-249: append a REOPEN line and re-record it under its label (NFL team defense splits, 3rd down, 2022). If its source is now
      blocked too, record BLOCKED with the reason instead. Do not leave a DONE line with no file.
   d) R-049 (NHL head coaches and PP / PK assistants, 2014-15 to 2025-26, mid-season changes dated): place it first in the R-order.

2) BUILD THE NEXT QUEUE - about 1,400 chunks, pre-checked. Append new rows to QUEUE.md from C-400 on. Before adding a whole family,
   fetch ONE page for one of its rows and confirm the source serves that table, filter and season; if not, do not add the family and
   say why in STATUS. Every family gets one source card naming the engine and factor it feeds and whether the bot could capture it.
   NBA (NBA.com Stats, seasons 2020-21 to 2025-26, each split as All / Home / Road):
     - team shot dashboard, offense and defense: shot clock bands, dribbles, touch time, closest defender, general shot type;
     - team player-tracking: drives, passing, rebounding, defense, catch-and-shoot, pull-up, paint, post, elbow touches;
     - team hustle; team opponent shooting by distance and by zone;
     - team traditional / advanced / four factors by rest days (0, 1, 2, 3+) and by quarter.
   NHL (MoneyPuck free downloads, seasons 2014-15 to 2025-26): team, skater and goalie season files by situation (all, 5on5, 5on4,
     4on5, other) - one chunk per file. Plus NHL.com team stats by strength state where it serves them.
   Skip anything the bot captures itself: Kalshi prices, MLB Statcast pitches, NBA official injury reports, NFL play-by-play.
   Player tables: only in pieces a single run can finish (split by team), and a piece is DONE only if a re-read of one page matches.

3) PERISHABLE SNAPSHOTS - daily, they cannot be recovered later. One record per game per snapshot, timestamped:
   NHL confirmed starting goalies (morning skate / day of game); NBA starting lineups and late scratches (about an hour before tip);
   NBA and NHL referee crews as published each day; NFL inactives (about 90 minutes before kickoff, game days only).

4) RUNS: 200 scheduled a day - about 150 on the queue, 25 on the snapshots at their times, 25 ticket runs in TO_MUSE's R-order.
   Create every new recurring job DISABLED and turn it on with a one-time enabler (catch-up bursts claimed chunks four times on
   11-03). Stagger them so no two runs claim the same chunk. Stop probing any source after 3 consecutive blocks in a family; mark the
   family BLOCKED in STATUS and move on.

5) Keep the gate, the spot-checks and the provenance rule exactly as they are (commit the builder and raw pages for every chunk, as
   C-131 did). Each day in STATUS.md: runs, DONE / NONE / BLOCKED / FAILED / RETIRED, chunks left in the queue, reclaims, and snapshot
   coverage per sport.
```
