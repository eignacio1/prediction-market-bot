# W90.1 — hold-out scan on the W89.7 history (true start times, time split)

Date 2026-10-27. Method: 89.2's `longshot_bias/calib.py` unchanged; `holdout_scan.py` adds a median time split per (sport, family). Cells chosen on the earlier half, side fixed from discovery, tested on the later half net of k007 at the quote, game-clustered interval, HELD OUT iff the hold-out lower bound > 0.
When it applies: a cell needs >= 30 games and >= 5 expected events on each side (calib.MIN_EVENTS / MIN_EXPECTED).

## Result: NO CANDIDATES, and the scan is UNDERPOWERED (not a null)

| measure | value |
|---|---|
| snapshot rows (first two-sided hourly candle per ticker per tier) | 9,689 |
| discovery cells | 1,850 |
| testable cells (>= 30 games, >= 5 expected each side) | 1 |
| BH-flagged (q = 0.10) | 0 |
| candidates / held out of sample | 0 / 0 |

Games per family in the candle sample: NBA game 118, spread 67, team total 52, total 66; NHL game 246, spread 67, team total 67, total 67; NFL game 121, spread 68, team total 67, total 67. After the median split a cell has at most ~30 games on the discovery side and it is spread over tier x price bucket x book; the 30-game floor is almost never reached. The fetch drew a deterministic outcome-independent sample (4 strikes per event, 3-minute budget per family), which is what caps n. This says the sample cannot detect an edge of the size 89.2 flagged; it does not say there is none.

## Survivors for Wave 91 to pre-register as ride trees

**None held out of sample.** Nothing here supports a ride cell.

## Not done (registered as gaps)

- 89.2's three named MLB candidates (KXMLBHIT T0-2h 20-25c YES; KXMLBF5TOTAL T6-24h 90-95c YES; KXNFLTOTAL D1 5-10c NO) were not re-tested: the MLB PRICE_ARCHIVE is on the box only.
- GG-1253 (MLB HHMM-as-ET against the schedule) not checked.
- Prop families: no candles fetched.
- One NFL event unmatched (LACDET, no_team_pair).

Files: `out/holdout_summary.json` (the cells csv is gitignored and header-only: no candidates). Code: `holdout_scan.py`; tests: `tests/test_w90_1_holdout_scan.py`.
