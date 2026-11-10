# W108.2 / B-063 — news lag at trade-print resolution (NBA injury reports)

**Plain English.** There is no tradeable window after public NBA injury news. On the moneyline, the price moves about +0.4c in the news direction within 1 minute (95% CI +0.02 to +1.04c, 282 events / 119 games) and is done by minute 2; a taker who buys the favoured side at a real print 1 minute after the report nets **-1.77c per contract after the exact taker fee** (gross -0.33c; CI on net -1.89 to -1.65c), and about the same at 2 and 5 minutes. The fee (~1.75c) is 4x the whole move. Price did not move before the report either (-30..-5 min: +0.15c, CI -0.01 to +0.40; last 5 min: -0.01c), so there is no sign of leakage ahead of the PDF, and shifted-by-2h placebo events show nothing (+/-0.05c). Totals show a bigger, slower move (about +1.0c abs at 30 min, but placebo is +0.64c, so the news excess is ~0.35c and the pre-news drift is the same size) — also far under cost. **Recommendation: do not install `news_burst_capture_install`** for NBA injury news; at 1-minute resolution the lag is shorter than we can act on and smaller than cost. Revisit only for a news type with moves >=3c (not seen here).

## Method / n
1,881 NBA injury PDFs (15-min cadence, 2026-10-21..11-09) -> 290 first-appearance events (>=35 min of pre-tip market after the report). Kalshi public trade prints (block trades dropped), window -3h..+31 min, moveS vs last print before the report, game-clustered bootstrap. Taker cost = print price + exact fee (`money.fee_rate`), no exit cost (upper bound). Code: `quant/trade_path.py` (+tests), `run_study_w108_2.py`, `analyze_w108_2.py`; outputs `study_results_w108_2.json`, `summary_w108_2.json`.

## Not measured (stated plainly)
- **Spreads: 0 events matched** (ticker matching bug or market-list window; unmatched list in the JSON). Not measured.
- Late scratches / starting-goalie news: no timestamped source in hand. Not measured.
- Moneyline lag50/lag100 medians (0.15 / 0.94 min) rest on only 18 events with |move|>=2c; treat as indicative.
- Totals use absolute move (direction ambiguous), which is biased upward; the placebo comparison is the honest read.
- Report stamps are 15-min grid times, so "minute 0" may precede true publication by up to 15 min.
