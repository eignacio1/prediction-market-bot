# Muse - Monday 2026-11-23 message (kept current by the window until Earl sends it)

Approved by Earl 2026-11-20 07:49 PT ("Yes for both"). New families go in Earl's message, never in a file Muse fetches.
Reserve list R1-R11 added 2026-11-23 16:35 PT (operator 16:23 PT: "ensure we have enough tickets for Muse so that it doesn't even have a 0% chance of running out"); sending the message is the approval.
State checked 2026-11-24 00:30 UTC: CLAIMS.md still has 1,711 QUEUE chunks; every run since 11-20 11:09 UTC is "QUEUE EMPTY" followed by
rule 12(i) re-verification of old DONE chunks (C-809..C-818). The 11-20 watchdog entry ordering season-back extensions was not acted on.

```
Muse - from Earl, week of 2026-11-23.

0) FIRST, BEFORE ANYTHING ELSE: stop re-verification. The queue has been empty since 2026-11-20 11:09 UTC and every run since has
   re-checked old DONE chunks (C-809..C-818) instead of extending the queue. My 2026-11-16 rule says extend first. Create the season-back
   chunks now, numbered after C-1711, as QUEUE rows in CLAIMS.md, and work them:
   (a) NBA player shot dashboards: 2022-23, then 2021-22, 2020-21, ... ;
   (b) NBA player tracking: 2023-24, then 2022-23, ... ;
   (c) NBA league matchups: 2023-24, then 2022-23, ... ;
   each family one season further back at a time, same tables and filters as its existing chunks, each season pre-checked with one page,
   NONE with the page when the source has no data for that season. MoneyPuck: skip (already back to 2014-15).
   Check: STATUS.md shows the new chunk range and "QUEUE EMPTY" stops appearing.
1) NEW FAMILY - NBA STARTING LINEUPS AND REFEREE CREWS, 2024-25 AND 2025-26 (historical, free box scores). One record per game: date, game
   id, home / away, each team's five starters as published in the official box score, and the three officials (crew chief, referee, umpire)
   with their names verbatim. Source: the league's own box scores (or another free box-score source with a card); one-page pre-check per
   season; NONE with the page if a season is missing. Why: the bot's lineup and referee splits are thin because our daily snapshots only
   start 2026-11-10; two seasons of history lets them be tested now. Chunk it by month.
2) NEW FAMILY - NHL CURRENT-SEASON CONSENSUS CLOSING LINES, 2026-27 (KofSports: free, no login, closing only). One record per game: date,
   teams, moneyline, puck line and total at close, as published. Pull the season to date, then daily. Why: the Kalshi-vs-books test needs
   about 700 games with a consensus close for puck line and total.
3) STANDING RESERVE - approved by me now, worked in this order whenever unclaimed chunks fall under 150 (after item 0's extensions are
   queued). Each family: one-page pre-check first; NONE with the page if the source is paywalled, needs a login, or has no data; then move
   to the next family. Chunk sizes as written; counts are estimates. Free sources only, no login, respect each site's limits.
   R1  NBA team on/off court, per team-season, 2013-14 onward (stats.nba.com team on/off pages) - ~30 x 13 = ~390 chunks.
   R2  NBA starting lineups and referee crews (item 1's family) extended back to 2016-17, by month - ~80 more chunks.
   R3  NBA play types (Synergy tables on stats.nba.com: every play type, offense and defense, team and player), per season, 2015-16
       onward - ~480 chunks.
   R4  NBA hustle stats and player defense dashboards (by shot range), per season, from each table's first season - ~90 chunks.
   R5  NHL officials per game (referees and linesmen, from the league's free game pages), by month, 2014-15 onward - ~100 chunks.
   R6  NHL line combinations and goalie game logs (Natural Stat Trick, free), per team-season, 2014-15 onward - ~800 chunks.
   R7  NFL team tendencies by personnel grouping: personnel usage, motion rate, play-action rate, pass rate by down and formation (Sharp
       Football Stats free tables), per team-season, 2018 onward - ~500 chunks.
   R8  MLB Statcast leaderboards (Baseball Savant), per season 2015 onward, batters and pitchers where both exist: expected stats, sprint
       speed, catcher framing, outs above average, pitch movement, active spin, bat tracking (2023 onward) - ~200 chunks.
   R9  MLB umpire scorecards per game (umpscorecards), by month, 2015 onward - ~80 chunks.
   R10 MLB batting orders and starting lineups per game (Baseball-Reference box scores), per team-season, 2015 onward - ~330 chunks.
   R11 MLB splits leaderboards (FanGraphs free: vs LHP / RHP, home / away, by month), batters and pitchers, per season 2015 onward
       - ~150 chunks.
   When R1-R11 are done, extend every family one season further back until its source has no data (NONE with the page). Re-verification
   only when every family has hit NONE. Your picker checks this every time unclaimed chunks fall under 150, before writing QUEUE EMPTY.
Same rules otherwise. Daily snapshots continue unchanged. Free sources only, ever.
```
