# W108.3 (B-064) — NBA / NFL / NHL props net of costs — PARTIAL: DATA FOUND, NOT YET MEASURED

**Plain English: no verdict for any sport. Part B (calibration and net of costs) was not run; the operator closed the session first.** "Props are / are not mispriced" is NOT stated for NBA, NFL or NHL. This is a gap, not a "no".

What is established:
- **The 106.3 premise was wrong in a useful way.** Settled markets do not only expose post-resolution prices. Kalshi's public batch endpoint `/markets/candlesticks` (up to 100 tickers per call, hourly, yes_bid / yes_ask / price OHLC, volume, open interest) returns pre-game quotes for settled prop markets. NBA/NFL/NHL props can be measured from public history with no archiver and no forward wait.
- **Inventory** (`PART_A_INVENTORY.md`): about 300k settled prop markets over 25 series (NBA 7 series, NFL 12, NHL 5 with settled history), mostly Nov 2025 – Nov 2026.
- **Candles fetched but unanalysed:** 7,227 market rows (a random sample of events per series, up to 50 markets each), in the session scratchpad only (not committed, not durable). Fetcher kept as `fetch_candles.py.txt` (rename to .py via a PR if reused).

Not done: entry-row construction, 70/30 split, fee and spread net, Holm. Open design point: the API gives only an expected-end time (`occurrence_datetime`), not tip-off. Proposed entry: last hourly candle with two-sided quotes at least 5h before `close_time` (games last under 5h), plus a second tier at 12h.

MEASURE MOVED: prop families measured net (NBA / NFL / NHL) 0 of 3; net-positive held-out cells: none measured. No pre-registration written.
Next: one block of about 60 min can finish Part B from the fetcher.


---

# W109.4 (B-064) -- props net of costs: Parts A, B, C (2026-11-11)

**Status: PARTIAL.** Pre-game quotes pulled and tested net of the exact fee and the quoted spread for 25 NBA / NFL / NHL prop series. **No cell is net-positive after multiplicity correction. Props are NOT shown to be mispriced after costs, for any of the three sports.** Two limits bind this answer, below: a ~5% sample, and no tip-off time in the API.

## What was done
- `src/prediction_market_bot/quant/props_candles.py` (tested, `tests/test_quant_props_candles.py`, 9 tests): polite cached fetch, cursor paging, live + historical settled lists, carried-forward two-sided quote with no look-ahead, scalar results dropped.
- **Finding that changes 108.3's recipe:** the batch candlestick endpoint returns EMPTY for settled markets older than the live cutoff. Those come only from `/historical/markets/{ticker}/candlesticks`, with fields `close` not `close_dollars`. The 108.3 fetcher would have silently returned nothing for most of the history.
- `fetch_props.py` (resumable) and `run_net.py` (analysis). Raw output `net_results.json`.

## Part A -- coverage (seeded sample of whole games per series, not the full inventory)
| Sport | series | markets pulled | with candles | quotes @C-5h | @C-8h | @C-12h | close dates |
|---|---|---|---|---|---|---|---|
| NBA | 7 | 1493 | 1493 | 1225 | 1171 | 1109 | 2025-11-20 to 2026-11-10 |
| NFL | 13 | 2861 | 2687 | 2380 | 2347 | 2315 | 2025-09-09 to 2026-11-10 |
| NHL | 5 | 933 | 933 | 446 | 320 | 176 | 2025-11-25 to 2026-11-10 |

Sample: 50 events x 3 markets per series (plus a 12 x 10 first pass), so roughly 3-5% of the ~300k settled markets. **Not the full inventory.** Quotes require a two-sided book (0 < bid <= ask < 1) no staler than 6h.

**Tip-off is not in the API, so T-60 / T-30 / T-5 minutes before the game could not be built.** Leads are 5h / 8h / 12h before `close_time` (C-5h etc). Close is the end of the game or earlier, and a game lasts <= ~3.5h, so C-5h is before tip-off; it is a hours-ahead quote, not a last-minute one. NHL FIRSTGOAL has almost no quote that early (those markets open late). The close-to-tip-off quotes that matter most for 109.3 are not measured here.

## Part B -- held-out net per contract
Entry at the ask (YES) or 1 - bid (NO); fee = `money.fee_rate(series, price)` with the series multiplier from `kalshi_fees.json` (the exact schedule, not the 0.07 rule of thumb). Games ordered by time; earlier 70% fit chooses the side; later 30% scored, game-clustered bootstrap 95% interval, one-sided cluster p, only where held-out games >= 30. Cells: family, family x band, family x band x liquidity, sport x band; each at three leads. 645 cells built, **22 testable**, all at the sport x lead x band level. Holm and BH (q=0.10) over those 22: **0 rejected.**

- Pooled sport results: every band with enough games has a NEGATIVE point estimate except NFL 10-30c buying NO at C-8h (+$0.013 per contract, interval -0.033 to +0.059, p=0.29, Holm-adj 1.0: indistinguishable from zero).
- Clearest negatives (interval excludes zero): buying YES on 10-30c in NBA (-$0.09 at C-5h, [-0.16,-0.01]) and NFL (-$0.06, [-0.10,-0.02]); buying YES at 70-90c in NFL (-$0.12 to -$0.13, all three leads). The cost of buying anything is the entry cost below plus whatever the market gets right.
- Tail bands <10c and >90c are reported in `net_results.json`; >90c has 5-8 held-out games and is descriptive only.
- NHL: only 1 testable cell (30-70c, -$0.083, p=0.93); the rest are under 30 games and DESCRIPTIVE.

## Verdicts per sport
- **NBA: props are NOT shown to be mispriced after costs.** No tested cell is positive; the mid-priced YES cells lose $0.04-0.07 per contract, within noise but on the wrong side.
- **NFL: props are NOT shown to be mispriced after costs.** The only positive point estimate (10-30c NO, +$0.013) is noise; cheap YES and 70-90c YES lose, mostly in the long-shot and the favourite ends.
- **NHL: undetermined, underpowered.** 1 of 25 pooled cells reached 30 games. Treat as no evidence either way.
- Consistent with 106.3 (MLB props 0 of 50 net) -- four sports, no net-positive prop family so far.

## Cost per family -- for 109.3's cells (entry cost per contract at C-5h, mean over sampled quotes; this is what edge must exceed)
| Family | games (C-5h) | quotes | half-spread | fee | entry cost / contract |
|---|---|---|---|---|---|
| KXNBA3PT | 47 | 188 | $0.043 | $0.0122 | **$0.055** |
| KXNBAAST | 47 | 171 | $0.033 | $0.0118 | **$0.045** |
| KXNBABLK | 42 | 125 | $0.066 | $0.0138 | **$0.080** |
| KXNBAPRA | 50 | 223 | $0.051 | $0.0148 | **$0.065** |
| KXNBAPTS | 48 | 175 | $0.046 | $0.0119 | **$0.058** |
| KXNBAREB | 48 | 190 | $0.059 | $0.0123 | **$0.071** |
| KXNBASTL | 47 | 153 | $0.058 | $0.0142 | **$0.072** |
| KXNFLANYTD | 40 | 175 | $0.031 | $0.0113 | **$0.042** |
| KXNFLFG | 52 | 210 | $0.049 | $0.0119 | **$0.061** |
| KXNFLFIRSTTD | 40 | 111 | $0.015 | $0.0048 | **$0.020** |
| KXNFLPASSATT | 52 | 188 | $0.020 | $0.0142 | **$0.034** |
| KXNFLPASSCOMP | 51 | 185 | $0.016 | $0.0122 | **$0.028** |
| KXNFLPASSINT | 52 | 176 | $0.013 | $0.0114 | **$0.024** |
| KXNFLPASSTDS | 46 | 178 | $0.018 | $0.0103 | **$0.029** |
| KXNFLPASSYDS | 44 | 203 | $0.032 | $0.0119 | **$0.044** |
| KXNFLRECYDS | 48 | 196 | $0.063 | $0.0130 | **$0.076** |
| KXNFLREC | 44 | 160 | $0.035 | $0.0116 | **$0.047** |
| KXNFLRSHATT | 52 | 224 | $0.018 | $0.0137 | **$0.031** |
| KXNFLRSHYDS | 48 | 206 | $0.042 | $0.0129 | **$0.055** |
| KXNFLTD | 47 | 168 | $0.006 | $0.0073 | **$0.013** |
| KXNHLAST | 33 | 100 | $0.043 | $0.0135 | **$0.056** |
| KXNHLFIRSTGOAL | 12 | 22 | $0.019 | $0.0038 | **$0.022** |
| KXNHLGOAL | 35 | 117 | $0.045 | $0.0112 | **$0.056** |
| KXNHLPTS | 34 | 135 | $0.022 | $0.0134 | **$0.036** |
| KXNHLSAVE | 44 | 72 | $0.034 | $0.0174 | **$0.052** |

Cost = mean half-spread + exact taker fee. Round trip (exit before settlement) roughly doubles the spread term; held to settlement it is paid once. Spreads are wide in NBA (4-8c) and thin in NFL anytime/first-TD and pass-count families (1-2c). Depth is not measured here and varies intraday; this is quote cost, not capacity.

## Pre-registration
**None written: no held-out cell is net-positive after Holm or BH.**

## Pillar / stage
PROOF (P2: prop families measured net) and BREADTH-adjacent (cost bars). ADR-0075 stage: **aggregated** (quotes and costs) and **interpreted** (the cost bar); not applied. Granularity index: this tests the price/band/liquidity split only; no matchup or personnel cross was tried.

## Limits
- ~5% sample; seeded, whole games kept together, but not stratified by season. The 2026-27 season is a minority of the NBA rows.
- C-5h is hours ahead of tip-off, not the last hour.
- Side chosen on the fit period only; many cells were looked at, which is why Holm / BH are on the 22 testable ones and the rest are descriptive.
- Quotes are candle closes (carried forward), not executable depth.
