# H3 news latency — operationalisation (W123.3). Last reviewed: 2026-11-20
Addendum to HYPOTHESIS.md §3 H3, written 2026-11-20 BEFORE any price around an event was read. Only structure counts were read
(event counts below). The H3 decision rule is unchanged: SUPPORTED if a move larger than one round cost is still to come at +5 min,
on at least 30 events, with a game-clustered 90% interval excluding zero; NOT SUPPORTED if the move is done within a minute or is
smaller than the cost; otherwise UNDERPOWERED with n and n needed.

Data: Muse archive `eignacio1/sports-intel-archive` pinned at bf892b818874f2a86f721cc8c5a053ea71dcc4fd: `L3-snapshots/nba/lineups-2026-11-10..19`
(10 files, 792 rows, 72 games), `L3-snapshots/nfl/inactives-2026-11-12/15/16/19` (4 files, 15 rows). Copied to data/. No injury-report
family exists apart from the NBA lineup rows' `late_scratches` / `out_list` text; NFL injury reports are not in the archive (data limit).

Event types (unit = event; one per game per type unless stated):
- NBA_CONFIRM: first non-null `confirmed_at_utc` in a game (time = that stamp).
- NBA_STARTER_CHANGE: a game's starter set differs from the previous snapshot of the same game (time = that snapshot's `status_at_utc`;
  the true change is somewhere in the interval since the previous snapshot, so the time is an UPPER bound on when it was public).
- NBA_INJURY: a distinct `late_scratches` line (ESPN injury report text with an ET clock time), deduplicated across snapshots; date = the
  earliest snapshot's date; touches that player's team game that day. Subtypes RULED_OUT vs DAY_TO_DAY. Time is ET converted to UTC.
- NFL_INACTIVES: `announced_at_utc` per game.
Markets: the game moneyline (KXNBAGAME / KXNFLGAME) on the home-team YES ticker; spread and total markets are touched but not scored.
Prices: Kalshi public trades (`/trade-api/v2/markets/trades`, read-only, min_ts/max_ts). p(t) = last trade price at or before t, only if that
trade is within 10 minutes before t, else missing. Events need p at t0 (pre) and at +1, +5, +15, +30 min; an event missing any is dropped
and counted (reported as the funnel).
Statistics: unsigned (direction of the news is not known): m(L) = |p(t0+L) - p(t0)|. Still-to-come at L: R(L) = |p(t0+30) - p(t0+L)|.
Placebo: same game, same window shape, pre-event windows with no event of any type in that game within ±2 h; R_placebo(L) median is
subtracted. D_R(5) is the primary: mean over events of R(5) minus placebo. 90% bootstrap, 2,000 draws, clustered by game.
Round cost = half-spread at the nearest archive snapshot (exp_output/PRICE_ARCHIVE) + taker fee 0.07·p·(1-p), per contract.
SUPPORTED needs D_R(5) interval lower bound > 0 AND the point estimate > round cost AND n >= 30 events (per event type). The minutes-to-reprice
distribution: per event, the first L in {1,5,15,30} where |p(t0+30) - p(t0+L)| <= one round cost.
NOT SUPPORTED (type): D_R(5) <= round cost with n >= 30, or the median minutes-to-reprice is <= 1. UNDERPOWERED otherwise.
Counts read before this was frozen: NBA games 72, with confirm 60, starter-set changes 102 (snapshot pairs), distinct late-scratch lines 248,
NFL inactive rows 15.
