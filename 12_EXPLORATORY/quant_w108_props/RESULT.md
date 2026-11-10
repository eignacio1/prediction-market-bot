# W108.3 (B-064) — NBA / NFL / NHL props net of costs — PARTIAL: DATA FOUND, NOT YET MEASURED

**Plain English: no verdict for any sport. Part B (calibration and net of costs) was not run; the operator closed the session first.** "Props are / are not mispriced" is NOT stated for NBA, NFL or NHL. This is a gap, not a "no".

What is established:
- **The 106.3 premise was wrong in a useful way.** Settled markets do not only expose post-resolution prices. Kalshi's public batch endpoint `/markets/candlesticks` (up to 100 tickers per call, hourly, yes_bid / yes_ask / price OHLC, volume, open interest) returns pre-game quotes for settled prop markets. NBA/NFL/NHL props can be measured from public history with no archiver and no forward wait.
- **Inventory** (`PART_A_INVENTORY.md`): about 300k settled prop markets over 25 series (NBA 7 series, NFL 12, NHL 5 with settled history), mostly Nov 2025 – Nov 2026.
- **Candles fetched but unanalysed:** 7,227 market rows (a random sample of events per series, up to 50 markets each), in the session scratchpad only (not committed, not durable). Fetcher kept as `fetch_candles.py.txt` (rename to .py via a PR if reused).

Not done: entry-row construction, 70/30 split, fee and spread net, Holm. Open design point: the API gives only an expected-end time (`occurrence_datetime`), not tip-off. Proposed entry: last hourly candle with two-sided quotes at least 5h before `close_time` (games last under 5h), plus a second tier at 12h.

MEASURE MOVED: prop families measured net (NBA / NFL / NHL) 0 of 3; net-positive held-out cells: none measured. No pre-registration written.
Next: one block of about 60 min can finish Part B from the fetcher.
