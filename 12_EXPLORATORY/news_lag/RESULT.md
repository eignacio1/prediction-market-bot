# W107.2 / B-060 — Does Kalshi's NBA line lag public injury news?

**Plain English.** On the data we have, there is no lag we could trade. We joined 228 official NBA injury reports
(2026-10-21 to 2026-11-09) to Kalshi's ~20-minute NBA moneyline price archive (KXNBAGAME, YES mid, 128 games priced) and
looked at 276 status changes. After news that makes a team worse (a player goes Out/Doubtful), the team's price moves
about +0.5c in the news direction by the first snapshot after the report (n=50, 95% CI -0.2c to +1.4c) and +0.8c by one
hour (n=40, CI -0.1c to +1.8c); questionable-to-active news moves +0.2c (n=53, CI -0.3c to +0.7c). All status changes
pooled: +0.3c at 20 min (n=105, CI -0.0c to +0.8c), +0.5c at 60 min (n=77, CI +0.1c to +1.1c). The move that still comes
*after* the first snapshot is about zero (20 to 60 min: -0.1c, n=77, CI -0.3c to +0.1c), so whatever the market does with
this news, it has done by the first 20-minute snapshot. Against 106.2's cost wall (taker 1.5-2.3c per contract each way
on game lines) every one of these is a NO, even at the best horizon. Pre-news drift is +0.2c (n=147, CI +0.0c to +0.3c):
a small anticipation or leak, not a tradable window.

**What 20-minute resolution can and cannot show.** It shows a lag of tens of minutes, and it shows there is none of
that size. It cannot see a lag shorter than one snapshot (~20 min): a price that fully adjusts in 2 minutes looks
identical to one that adjusts in 19. So "no lag of 20+ minutes, and the average total move is under the cost wall" is
established; "no lag at all" is not. If the sub-20-minute move were much bigger than what we see at +20 min, the +20 min
mean would already contain it, so the *size* ceiling is fair, but the *window* a fast trader could exploit is unmeasured.

**Not measured / caveats.** Status type only (no star vs rotation split: no local minutes source); moneyline only (no
totals, spreads, team totals, props); no NHL goalie or lineup news; many events are unmatched to a priced game (top
unmatched: SAS@DAL, MEM@GSW, GSW@DEN, CHI@MIL, HOU@SAS: likely Kalshi code differences or games before the archive
window); 190 events stamp at hour 0 ET, probably list re-publication; the filename stamp differs from the header time by
up to 15 min (the header is used). `to_questionable` and `out_to_active` have n <= 2 and are unscorable. No fills are
involved, so the pre/post 2026-11-06 demo-epoch rule does not apply.

**What the burst capture would settle.** `scripts/news_burst_capture.py` records every open NBA game line's top of book
every ~20 s for 30 minutes starting 5 minutes before each of three injury-report windows a night (one listing call per
sweep, one short process under a lock, public GETs only, 40 MB/day cap). After about two weeks of game nights it would say
how many minutes the line takes to absorb a status change and what the move is at 1, 2, 5, 10 minutes, which is the
only way to find out whether a sub-20-minute window exists at all. Given the move size here (<1c against a 1.5-2.3c
wall) the prior is that it does not clear cost; the capture is cheap insurance, not a bet on edge.
It is PREPARED and NOT RUN: it installs only through the allowlisted task `news_burst_capture_install`, on the
operator's named approval.

Files: `quant/news_lag.py`, `12_EXPLORATORY/news_lag/run_study.py`, `study_results.json` (this folder).
