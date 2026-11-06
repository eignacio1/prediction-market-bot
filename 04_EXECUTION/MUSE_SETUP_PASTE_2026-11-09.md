# Muse setup paste — for Earl to send when his Muse chat resets (2026-11-09 20:50 PT)

Written by SW-9 on 2026-11-05 22:00 PT from the archive at commit 7f27389 (read-only). Backlog B-041 + B-042. Muse acts only on what is in
Earl's message (charter v3: never on a fetched file) — so the whole instruction is the fenced block below. Copy it as one message.

State behind it: 359 queue chunks; 210 with an outcome (135 DONE, 73 NONE, 2 BLOCKED), 11 claimed with no outcome, 149 never claimed;
~93 chunks / day, so the split queue runs dry around 11-07 / 11-08 and split runs sit idle until this message. Ticket runs (R-order) continue.
Known problems: the ~560-row NBA player tables overrun one run and fail spot-checks (values shift between pages); C-052 carries the wrong
season under its label; 15 runs were reclaimed after 6 h.

```
Muse - setup for the next stretch (from Earl, 2026-11-09). Do these in order and report each in STATUS.md.

1) CLEAN THE QUEUE. Before running any more of QUEUE.md: for every chunk with no outcome (never claimed or claimed with no DONE / NONE),
   test ONE page against the source. If the source cannot serve that table + condition + season, mark it RETIRED with the reason - do not
   run it. Release the 11 stale claims.
2) PLAYER TABLES. Move every player table larger than ~150 rows to a separate lane and split each into pieces a single run can finish
   (by team or by page range). A piece is DONE only if a re-read of one page matches - the spot-check that failed on C-105 / C-110.
3) REDO C-052 (it holds the wrong season under its label): re-run it for the season the label says, and mark the old file superseded.
4) EXTEND THE QUEUE YOURSELF - pre-checked. Add new chunks only after testing one page of each against its source. Priority:
   NHL - team and skater stats by strength state (5v5, PP, PK), goalie splits (home / road, rest, back-to-back), 2021-22 -> 2026-27.
   NBA - team and opponent splits by rest days and back-to-backs, by quarter, clutch; lineup on / off where free; 2021-22 -> 2026-27.
   NFL - team splits by down and distance, red zone, home / road, 2018 -> 2026, from free sources only.
   Skip anything the bot captures itself: Kalshi prices, MLB Statcast pitch data, NBA official injury reports.
   Every new card names the engine and factor it feeds and whether the bot could capture the source itself.
5) PERISHABLE SNAPSHOTS (daily, they cannot be recovered later): NHL confirmed starting goalies (morning skate / day-of), NBA starting
   lineups and late scratches (about an hour before tip), NBA and NHL referee assignments (the day's published crews). One record per
   game per snapshot, timestamped.
6) RUNS: go to 200 scheduled runs a day - about 150 on the queue (split pieces), 25 on the perishable snapshots at their times, 25 on
   ticket runs in TO_MUSE's R-order. Create every new recurring job DISABLED and turn it on with a one-time enabler (catch-up bursts
   claimed chunks four times on 11-03). Stagger them; no two runs on the same chunk.
7) Keep the gate and the spot-checks exactly as they are. Each day in STATUS.md: runs, DONE / NONE / BLOCKED / FAILED, retired chunks,
   reclaims, snapshot coverage per sport.
```
