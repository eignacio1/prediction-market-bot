# W91.1 results — ride cells, backward test (EXP-042)

Pre-registration: `05_RESEARCH_EXPERIMENTS/EXP042_RIDE_CELLS_PREREGISTRATION_2026-10-28.md`, sha256 `4efbc15f26e3fac39c43e48eea9cab19c28fabf60426c863ceccf5976f9cab35` (frozen at commit 252ea84).

## Verdict: the backward test is VOID. 0 of 11 cells tested out of sample.

The pre-registered overlap check ran first (2026-08-01..10-27, hourly-candle method vs the 20-min archive snapshot method, 1,902 matched (ticker, tier) observations):

| Family | Matched | Same 5c bucket | Mean diff | Mean abs diff |
|---|---|---|---|---|
| KXMLBF5TOTAL | 242 | 0.793 | +0.0064 | 0.0370 |
| KXMLBF5 | 261 | 0.778 | -0.0010 | 0.0307 |
| KXMLBF7 | 166 | 0.849 | -0.0121 | 0.0169 |
| KXMLBHIT | 234 | 0.885 | +0.0159 | 0.0177 |
| KXMLBSPREAD | 438 | 0.916 | +0.0008 | 0.0046 |
| KXMLBTEAMTOTAL | 250 | 0.732 | -0.0101 | 0.0245 |
| KXMLBTOTAL | 210 | 0.881 | +0.0030 | 0.0104 |
| KXNFLTOTAL | 101 | 0.812 | -0.0176 | 0.0244 |
| **ALL** | **1,902** | **0.838** | **-0.0002** | |

- (a) >=85% same bucket: **FAIL (83.8%)**. (b) |mean diff| <= 0.01: pass. (c) no cell had >=30 overlap games, so it was judged on (a)/(b) only.
- Per the pre-registration a failed condition voids the backward test; no pre-August date was scored and no backward fetch was run. Not re-tuned after seeing the failure.
- Caveat: the overlap sample is partial (wall-clock capped by the rate limit, below), so (a) rests on ~1,900 observations, not the full overlap.

## Fetch constraint
Kalshi public market-data GETs ran ~4 req/s combined across 8 parallel processes with frequent 429s. Every-strike candle fetch for a family's window is tens of thousands of markets; infeasible inside the block ceiling. Even without the VOID, no cell would have reached 30 games. Registered as a gap.

## GG-1253 (HHMM in tickers): validated
Ticker HHMM read as ET matches the `rules_primary` clock on 100% of F5TOTAL, F5, F7, SPREAD, TEAMTOTAL, TOTAL markets and 125,511/126,057 (99.57%) of KXMLBHIT. `occurrence_datetime - 3h` matches the other families but 0% for F5/F7. HHMM-as-ET is the start-time rule used by `backward_w91.py`.

## Status of the 11 cells
All 11: backward UNTESTED; `ride_cells.toml` status stays IN_SAMPLE (no move). RIDE stays empty. They rest on the forward test alone (archive rows after the freeze).

Earliest full-effect look dates (reporting only; PASS needs the half-effect judged n): 1: 2027-05-18; 2: 04-29; 3: 04-11; 4: 05-06; 5: 04-28; 6: ~2026-12-21; 7: 06-17; 8: 06-11; 9: 06-07; 10: 04-15; 11: 06-25. Cells 6, 7, 8, 9, 11 likely need the 2027 season's end or later for the half-effect n.

## Notes
- Pre-registration header says "Written ~01:00Z"; the actual clock at freeze was ~00:4xZ. Immaterial (before any new row was read), recorded for honesty.
- Modal outcome (<=2 HELD_OUT, 0 a result) was pre-registered; the realised outcome is VOID, which the registration anticipated as a possible branch.
