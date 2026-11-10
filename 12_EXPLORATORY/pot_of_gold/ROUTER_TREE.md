# The router decision tree as it stands (W106.1, written 2026-11-10, from code and tables on this branch)

For the operator. One function, `router.route()`, looks at one market and sends it to exactly one of five places.
Nothing here places a real order; kelly is 0; orders exist only on the demo book and only for cells that passed a
held-out test.

```
             one priced market (family, time-to-start, bid, ask)
                              |
                 +------------v------------+
                 | DISQUALIFY?             |  no two-sided book / already started / date-only game day /
                 +------------+------------+  price under 1c or over 99c            --> NO_BET
                              |
        +---------------------+------------------------+
        |                     |                        |
   FADE (model)          RIDE (market cells)     POT_OF_GOLD (longshot cells)
   needs measured        needs a HELD_OUT /      needs a HELD_OUT / FORWARD_PASSED
   skill + net edge      FORWARD_PASSED cell     cell with net lower bound > 0
        |                     |                        |
        +----------+----------+------------------------+
                   |
        any two on OPPOSITE sides? --yes--> NO_BET ("conflict")
                   | no
        same side: name it RIDE > POT_OF_GOLD > FADE  (others recorded as "agrees")
                   | nobody claimed
              MOMENTUM_FOLLOW / MOMENTUM_FADE  (measured 1h-move cell)  --> else NO_BET
```

## The branches, in plain English
| Branch | Idea | Cells today | Orderable today |
|---|---|---|---|
| FADE | Our model disagrees with the price and has measured skill in that family. | skill records, not a cell table | only where a skill record exists |
| RIDE | The market is right or biased in a known, measured way; take its side. | 18 (10 calibration, 5 move, 2 ladder, 1 retired) | **2**: MLB totals ladder, 0-2h, tight book (net lower bound +3.4c and +9.5c) |
| POT_OF_GOLD | Lottery-ticket buyers overpay for longshots and underpay for near-certainties; take the other side. | 17 | **0** |
| MOMENTUM | After a big move, follow or fade it, if a measured cell says which. | needs a transition table | none supplied |
| NO_BET | Nothing measured claims it. The default, and the answer for most markets. | | |

## POT_OF_GOLD cells (all pre-registered 2026-11-05, all IN_SAMPLE)
Net is per contract after fees. "Mean" is the in-sample average; "lower" is the lower confidence bound the gate
uses. **No cell has a held-out number yet**, so none can order. Most lower bounds are negative, which is the honest
state: the pattern shows in the mean and is not yet distinguishable from zero.

| Family | Time | Price | Route | Side | n | Mean | Lower | Status |
|---|---|---|---|---|---|---|---|---|
| KXMLBF5 | 2-6h | 10-15c | fade longshot | NO | 18 | +7.1c | -4.1c | IN_SAMPLE |
| KXMLBF5SPREAD | 2-6h | 10-15c | buy longshot | YES | 21 | +5.1c | -9.4c | IN_SAMPLE |
| KXMLBF5SPREAD | 0-2h | 5-10c | fade longshot | NO | 18 | +2.2c | -13.8c | IN_SAMPLE |
| KXMLBF5TOTAL | 2-6h | 85-90c | take favourite | YES | 39 | +1.8c | -8.4c | IN_SAMPLE |
| KXMLBF5TOTAL | 0-2h | 90-95c | take favourite | YES | 93 | +0.4c | -4.8c | IN_SAMPLE |
| KXMLBF5TOTAL | 2-6h | 90-95c | take favourite | YES | 34 | +5.5c | **+5.1c** | IN_SAMPLE |
| KXMLBF7 | 6-24h | 10-15c | fade longshot | NO | 197 | +0.7c | -3.4c | IN_SAMPLE |
| KXMLBSPREAD | 0-2h | 10-15c | buy longshot | YES | 94 | +3.0c | -4.3c | IN_SAMPLE |
| KXMLBSPREAD | 2-6h | 10-15c | buy longshot | YES | 35 | +0.5c | -11.2c | IN_SAMPLE |
| KXMLBTEAMTOTAL | 0-2h | 5-10c | buy longshot | YES | 97 | +1.5c | -3.7c | IN_SAMPLE |
| KXMLBTEAMTOTAL | 0-2h | 85-90c | take favourite | YES | 76 | +3.0c | -4.8c | IN_SAMPLE |
| KXMLBTEAMTOTAL | 0-2h | 90-95c | take favourite | YES | 18 | +1.8c | -9.4c | IN_SAMPLE |
| KXMLBTOTAL | 6-24h | 10-15c | fade longshot | NO | 28 | +8.1c | **+0.7c** | IN_SAMPLE |
| KXMLBTOTAL | 2-6h | 85-90c | take favourite | YES | 54 | +6.0c | -1.8c | IN_SAMPLE |
| KXMLBTOTAL | 2-6h | 90-95c | take favourite | YES | 40 | +3.8c | -1.6c | IN_SAMPLE |
| KXNFLSPREAD | D1 | 1-5c | fade longshot | NO | 25 | +2.8c | **+2.6c** | IN_SAMPLE |
| KXNFLTOTAL | D1 | 95-99c | take favourite | YES | 37 | +0.5c | -5.2c | IN_SAMPLE |

Three cells have a positive lower bound in-sample (bold). In-sample positives found by searching a grid are the
cells most likely to be selection noise; each needs to survive a held-out test before it can order. That is the
next step for this tree, and it needs settled markets that do not exist yet.

## What changed with this block
- `router.py` gained the POT_OF_GOLD branch and the precedence rule above (pre-registered first in
  `ROUTER_PRECEDENCE.md`). With the shipped table it routes 0 live markets; the wiring is proven on fixtures.
- The ride board runner needed one small change: a POT_OF_GOLD route carries its own cell so the order gate reads
  the cell's real status (otherwise it would look up a ride cell, find none, and fall to paper regardless).
  Fail-closed either way.
- Data epoch note: all P&L here predates the NO-side fill fix of 2026-11-06T01:03:42Z only through settlement
  prices, not fills; no demo fills are used in these cells.
