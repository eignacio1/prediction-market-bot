# RESULT W107.3 - does the NBA availability engine (v3) see news before Kalshi? (B-061)

**DESCRIPTIVE ONLY.** Analysis-only; EXP-044c's frozen spec and looks untouched. Threshold and lead definition fixed in `PREREG_W107_3.md` before any outcome was read. No score here is a verdict below judged n.

**Plain English:** On the 3 nights-plus of v3 data that exist (game dates 11-04 to 11-09, 170 events, 4,288 tickers), v3 differs from v2 by 3 points or more on 1,553 tickers (42 of 44 games), so "availability moved the price" is the common case, not a rare one. After v3 logged its price, Kalshi's line did not drift toward v3 any more than it drifted away: on moved tickers the market's mean move toward v3's direction was -0.06c (95% game-clustered CI -0.27c to +0.14c, 42 games), indistinguishable from the same measure on all tickers. The slot-to-quote window showed no market move toward v3 either (+0.05c), so there is no sign the market had already caught up or that v3 led it. On the 34 games already settled, v3's Brier is the same as the market's (difference +0.0007, CI -0.016 to +0.017) and nominally better than v2's (-0.016, CI -0.035 to +0.003, interval includes zero); the would-be taker net per contract is negative to flat with intervals spanning roughly +-10c (rule B, always v3 side: -1.4c, CI -10.4c to +7.7c). Answer: this data gives no evidence that the availability engine sees news before the market, and also cannot rule it out; v3 prices once per event about 72 minutes before tip, so it cannot show a time series of who moved first.

## Numbers
| Item | Value |
|---|---|
| Paired v3/v2 tickers, games | 4,288 / 44 |
| Moved (abs delta >= 0.03) tickers, games | 1,553 / 42 (spread 707, team total 631, game total 153, moneyline 62) |
| Median quote to tip; median injury-slot age at quote | 72 min; 153 min |
| Market move quote to tip-10m toward sign(delta), moved | -0.06c CI [-0.27, +0.14], n=1,545 |
| Same, all tickers | -0.03c CI [-0.14, +0.09], n=4,210 |
| Led / flat / against (moved, >=1c) | 229 / 1,037 / 279 |
| Brier v3 minus market, moved settled | +0.0007 CI [-0.016, +0.017], n=1,277 tickers, 34 games |
| Brier v3 minus v2, moved settled | -0.0157 CI [-0.035, +0.003] |
| Net per contract, taker, 106.2 fee model, rule A (ex-ante edge > 0), moved | -0.85c CI [-11.2, +9.5], n=1,047, 33 games |
| Net per contract, rule B (always v3 side), moved | -1.43c CI [-10.4, +7.7], n=1,275, 34 games |

Intervals are game-clustered bootstrap, 4,000 resamples. Settled-only; 11-09 games not yet settled are excluded (836 tickers).

## Coverage (Part C)
Box coverage read (run 02:07Z): v1, v2, v3 scheduled = logged before tip, missed 0, every night 11-05 to 11-09 (8, 36, 28, 28, 32 events). **D4 NBA coverage 3 of 3 confirmed since the catch-up install.** 11-04 is the pre-install night (v3 logged 38 of 56). Store last game date: 11-09, which is yesterday or later (B-017 fine on this read).

## Caveats
- One price per ticker per version; no intraday series, so "who moved first" is inferred from the market path after v3's quote, not from v3's own timeline.
- News time is a proxy: the injury slot's publication time.
- Delta between v3 and v2 is any difference, not only late-breaking news; no per-team status-change filter was possible (snapshots carry no player-to-team map).
- Small n (6 game dates, 34 settled games). 107.2's market-lag result was not awaited.
- Analysis script is unpushed in the scratchpad (a `.py` would need a PR); this document holds the outputs.

Stage reached (ADR-0075): availability and lineups = interpreted; not yet applied.
