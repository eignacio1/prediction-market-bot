# W91.2 Part B — the ladder ride (measured)

**Applies when:** a strike sits on a ladder of >=4 same-event, same-kind strikes (totals, team totals, spreads) and its quote is read pre-game; the ladder price is a leave-one-out normal fit (`quant/ladder_loo.py`). Does not apply to short ladders, props, or in-play quotes.

**Data:** local PRICE_ARCHIVE (NFL + MLB totals / team totals / spreads), one snapshot per ladder per clock hour, pre-game only, strikes with mid 0.05–0.95. Settlements fetched via public Kalshi GETs (2,762 events, 35,756 tickers). NBA / NHL are NOT covered: no price archive for them (GG-1330).

**Trigger:** ladder price L beats the quote net of crossing the spread and k007. Net = fee k007 + spread cost. Intervals: game-clustered bootstrap. Split by game date at 2026-09-11 (first half = select, second half = score).

## Whole-sample result (108,279 triggers, 2,191 games)
| measure | mean | 95% CI |
|---|---|---|
| settles toward ladder, s·(y−mid) | +0.029 | [0.020, 0.039] |
| quote moves toward ladder +1h | +0.0133 | [0.0121, 0.0146] (1,952 games) |
| quote moves toward ladder +3h | +0.0108 | [0.0095, 0.0124] (1,846 games) |
| net P&L per bet, taking the strike | +0.007 | [−0.002, 0.017] |

Gross convergence is real; net of cost it is not distinguishable from zero over the whole sample. First half net P&L −0.006 [−0.017, 0.004]; second half +0.013 [−0.000, 0.026].

## Who corrects whom (n = 61,344 with a +3h follow-up)
Strike moves toward ladder +0.0108; ladder moves toward strike −0.0009. The strike corrects; the ladder does not move to it. The strike moved more than the ladder in 49.7% of cases (the mean is carried by large strike moves).

## Cells (series × tier × gap size × book), BH q=0.10 on first half
36 cells testable (>=20 games) in the first half; 7 selected; **2 HELD_OUT**, 5 FAILED (one FAILED for lack of a second-half sample).

| cell | first-half mean | second-half mean [95% CI] | games | status |
|---|---|---|---|---|
| KXMLBTOTAL T0-2h net 2–5c tight | +0.065 | +0.087 [0.034, 0.142] | 117 | HELD_OUT |
| KXMLBTOTAL T0-2h net 5c+ tight | +0.122 | +0.217 [0.095, 0.341] | 30 | HELD_OUT |
| KXMLBTEAMTOTAL T0-2h net 5c+ tight | +0.177 | +0.107 [−0.007, 0.233] | 42 | FAILED |
| KXMLBTEAMTOTAL T0-2h net 2–5c tight | +0.067 | +0.022 [−0.029, 0.074] | 140 | FAILED |
| KXMLBSPREAD T0-2h (3 cells) | +0.07 to +0.26 | −0.015 to +0.036, CIs span 0 | 16–48 | FAILED |

Full list: `ladder_ride_cells.json` (kind LADDER). Summary: `ladder_ride_summary.json`.

## Caveats (read before trusting the two HELD_OUT cells)
- All selected cells are T0-2h with a tight book, MLB only. NFL cells selected nothing.
- Archive quotes are snapshots; displayed size/fill at the quoted price is unmeasured here. P&L assumes a fill at bid/ask. EXECUTION (fills) is a separate question.
- The 5c+ cell has 30 second-half games. Do not read its point estimate as expected size.
- Many strikes per game share one game cluster; intervals cluster on game, but 36 cells x one split is a single OOS look, not a forward test.
- Status HELD_OUT is out-of-sample on a time split of the same archive; it is not FORWARD_PASSED.

## Table
`ride_cells.toml` is unchanged (contract: window moves statuses at wave close). Recommended: add the two KXMLBTOTAL cells as kind LADDER, status HELD_OUT.

**Stage (ADR-0075):** ladder-vs-strike gap = interpreted; applied only for the two HELD_OUT MLB total cells (a tested path from fact to price against the market, OOS once).
