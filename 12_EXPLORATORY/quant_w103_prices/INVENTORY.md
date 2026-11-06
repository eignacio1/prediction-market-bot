# W103.2 Part A — what the Kalshi price archive holds (read 2026-11-06 ~00:55Z, box, read-only)

Source: `exp_output/PRICE_ARCHIVE/prices_*.jsonl` on the box (98 daily files, 2026-08-01 .. 2026-11-06, 3,379,822 rows; 1.7 GB with `depth_*`). One streaming aggregate, nothing written to the archive.

**Row = one quote snapshot of one market**: `run_ts, series_ticker, ticker, event_ticker, status, yes/no bid/ask, last_price, previous_price, volume, volume_24h, open_interest, close_time, expiration_time, yes_mid, half_spread` (`yes_mid` present on 3,375,442 rows).

| Series (23) | rows | tickers | events (games) | days | first .. last |
|---|---|---|---|---|---|
| KXMLBHIT | 532,614 | 38,546 | 762 | 90 | 08-01 .. 10-29 |
| KXNFLSPREAD | 349,141 | 3,675 | 136 | 62 | 09-05 .. 11-06 |
| KXMLBTEAMTOTAL | 338,576 | 11,214 | 801 | 90 | 08-01 .. 10-29 |
| KXNFLTEAMTOTAL | 293,170 | 3,733 | 136 | 62 | 09-05 .. 11-06 |
| KXNFLTOTAL | 257,557 | 2,724 | 136 | 62 | 09-05 .. 11-06 |
| KXMLBTOTAL | 256,821 | 9,518 | 800 | 90 | 08-01 .. 10-29 |
| KXMLBF5TOTAL | 153,832 | 5,537 | 791 | 90 | 08-01 .. 10-29 |
| KXMLBSPREAD | 153,442 | 6,473 | 801 | 90 | 08-01 .. 10-29 |
| KXNBATEAMTOTAL | 131,295 | 2,933 | 73 | 10 | 10-28 .. 11-06 |
| KXMLBGAME | 123,790 | 1,630 | 815 | 90 | 08-01 .. 10-29 |
| KXNBASPREAD | 122,188 | 2,486 | 75 | 10 | 10-28 .. 11-06 |
| KXNBATOTAL | 107,899 | 2,323 | 75 | 10 | 10-28 .. 11-06 |
| KXMLBF5SPREAD | 87,728 | 3,164 | 791 | 90 | 08-01 .. 10-29 |
| KXNHLTOTAL | 74,486 | 812 | 82 | 10 | 10-28 .. 11-06 |
| KXMLBF7 | 69,384 | 2,388 | 796 | 90 | 08-01 .. 10-29 |
| KXMLBF5 | 65,793 | 2,373 | 791 | 90 | 08-01 .. 10-29 |
| KXMLBF3 | 62,442 | 2,373 | 791 | 90 | 08-01 .. 10-29 |
| KXNHLTEAMTOTAL | 54,855 | 700 | 70 | 10 | 10-28 .. 11-06 |
| KXNFLGAME | 49,682 | 300 | 150 | 62 | 09-05 .. 11-06 |
| KXNHLGAME | 37,446 | 204 | 102 | 10 | 10-28 .. 11-06 |
| KXNHLSPREAD | 34,357 | 556 | 82 | 10 | 10-28 .. 11-06 |
| KXNBAGAME | 23,324 | 194 | 97 | 10 | 10-28 .. 11-06 |

Sports: MLB (90 days, season ended 10-29), NFL (62 days, live), NBA and NHL (10 days only — started 10-28).

## What CAN be measured
- **Snapshot cadence: median gap 20.0 minutes in every series** (about 2,100 snapshots per MLB series, 949 NFL, 384 NBA/NHL). Horizons therefore available: **next snapshot (~20 min)**, **~60 min (3 snapshots)**, and **to the end of the series**.
- Per-market price paths over days (pre-game drift) and over the game day.

## What CANNOT be measured (stated plainly)
1. **5- and 15-minute horizons (the block's wording).** The cadence is 20 minutes; there is no snapshot in between. Not interpolated (an interpolated price is a price nobody could trade). Replaced by ~20 and ~60 minutes.
2. **Pre-game vs in-play, directly.** Every row has `status = active` (the archive never shows a closed or settled state) and `close_time` / `expiration_time` sit days after the game (the MLB, NFL rows are ">48 h to close_time" on 98%+ of rows), so no field says "the game has started". The only available split is a **calendar proxy**: the date embedded in the ticker (e.g. `26NOV16LACBAL`) vs the snapshot's date — **prior days** (certainly pre-game) vs **game day** (pre-game hours and in-play mixed; the game's start time is not in the row). A true in-play measure needs a game-start time joined from another source (the NFL/NBA/NHL/MLB event feeds) — a registered gap, not attempted here.
3. **Settled outcomes.** There is no result field. The archive's last snapshot of a market is a **settlement proxy** only when it already sits at <=0.03 or >=0.97; markets still undecided at their last snapshot are excluded, never guessed. Proxy coverage is reported in RESULT.md.
4. **Tradeable reversion.** `yes_mid` moves include bid-ask bounce; a reversion in mid is not a reversion one can capture. Handled by a tight-book robustness split and by stating every result gross of cost.
5. **NBA and NHL**: 10 days is too few games for a verdict; they get an estimate and a flag, not a read.
6. **GG-1771 (mirror-priced NO fills)** does not touch this block: it reads quote snapshots only, no fills or P&L.
