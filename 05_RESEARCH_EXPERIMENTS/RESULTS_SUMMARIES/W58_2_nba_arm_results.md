# W58.2 — NBA game-market arm (shadow only): results

Branch `session/20261007T011627Z-w58-2-nba-arm`. Shadow only: no order, stake or kelly.

## Part A — Kalshi discovery (2026-10-06, public GET, `scripts/nba_kalshi_discovery.py`)

Raw output: `exp_output/NBA/discovery.json` (open + unopened states).

| Series | Fee type | Open markets / events | Event dates |
|---|---|---|---|
| KXNBAGAME (moneyline) | quadratic_with_maker_fees | 76 / 38 | 2026-10-06 to 2026-10-20 |
| KXNBASPREAD | quadratic_with_maker_fees | 186 / 7 | 2026-10-06 to 2026-10-07 |
| KXNBATOTAL | quadratic_with_maker_fees | 147 / 7 | 2026-10-06 to 2026-10-07 |
| KXNBATEAMTOTAL | quadratic | 0 / 0 (not yet listed) | none |
| KXNBAGAMES, KXNBASUMMERGAME | quadratic | 0 / 0 | none |

Ticker grammar (event = `<SERIES>-<YY><MON><DD><AWAY><HOME>`, all team codes 3 letters, all 30 teams seen, no drops):
- moneyline `KXNBAGAME-26OCT13INDOKC-OKC`
- spread `KXNBASPREAD-26OCT06BKNCHA-BKN38` (floor_strike 37.5)
- total `KXNBATOTAL-26OCT07MININD-256` (floor_strike 255.5)

Findings: preseason games are listed (2026-27 regular season not yet). Team total has zero listings, so its cells can only be registered NOT_IMPLEMENTED. Spread and total only list the next day or two, moneyline lists about two weeks ahead.

## Data source reachability (2026-10-06)
- ESPN NBA scoreboard: HTTP 200 from Mac and from VPS. Chosen source for schedule, start times and scores.
- stats.nba.com and cdn.nba.com: 403 from the VPS.

Date convention: the ticker date is the ET game date (KXNBAGAME-26OCT13INDOKC expires 2026-10-14T03:00Z, i.e. the evening of 10-13 ET). Kalshi gives no start time, so tip-off comes from the ESPN schedule.

## Part B — registry (this PR)
`NBA_MONEYLINE/SPREAD/GAME_TOTAL/TEAM_TOTAL` added with series KXNBAGAME/KXNBASPREAD/KXNBATOTAL/KXNBATEAMTOTAL, sport `nba`, existing `_NBA_GRAMMAR`; T1/T2/T3 cells NOT_IMPLEMENTED (12 cells). `tests/test_nba_game_registry.py` parses the three real sample tickers and all 30 team codes in both positions for every series.
