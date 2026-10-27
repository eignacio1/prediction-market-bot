# W90.2 — router replay (DESCRIPTIVE; nothing live)

Block 90.2 · claim T-1330..T-1339 / GG-1330..GG-1339 · code `src/prediction_market_bot/decision_trees/router.py`, tests `tests/test_decision_router.py`, replay `run_replay.py`, raw `out/replay.json`.
Doctrine: `02_ARCHITECTURE_DESIGN/DECISION_ROUTING.md`. No runner, cell, model, ledger, gate or pre-registration touched.

## What was replayed
The first two-sided pre-start snapshot per (ticker, time-to-start tier) of the local price archive (MLB and NFL, 2026-08-01 to 2026-10-27), joined to Kalshi settlements fetched from the public markets endpoint. **164,354 situations.** Evidence supplied: W88.3 skill records (MLB 0.0018, NFL 0.0, NHL/NBA 0.0), and the 11 W89.2 survivor cells as the ride table. 90.1's `ride.py` is not on main, so this is the stub interface.

## Traffic per tree
| Tree | Situations | Share |
|---|---|---|
| NO_BET | 160,516 | 97.66% |
| RIDE | 3,838 | 2.34% |
| FADE | 0 | 0% |
| MOMENTUM_FOLLOW / MOMENTUM_FADE | 0 | 0% |

NO_BET reasons: 152,176 no tree claims it; 7,795 NFL game day (date-only ticker); 545 no two-sided book. FADE: 0 by evidence, and a stress run (every situation given a confident synthetic `model_p` of 0.99 or 0.01) also produced 0 FADE traffic, because no sport has measured skill. **No tree received traffic without measured evidence: the defect check passes.**

## Settlement minus price on RIDE traffic (descriptive, in-sample — NOT evidence)
The ride table was built from this same archive, so these numbers cannot show edge; they show the router sends traffic to the cells it was told about. Entry at mid, no fee, no spread, routed side, game-clustered 95% interval (1,000 resamples).

| View | n | games | mean | 95% interval |
|---|---|---|---|---|
| All routed RIDE, settled | 2,661 | 993 | +0.0568 | [+0.0424, +0.0718] |
| First half in time | 1,330 | 474 | +0.0475 | [+0.0263, +0.0686] |
| Second half in time | 1,331 | 521 | +0.0660 | [+0.0417, +0.0883] |

The time split is a descriptive stability look, not a hold-out: the cells were selected on the whole sample. By family the sign is positive in all 8 families routed (KXMLBHIT n=1,846 / 358 games, +0.050 [+0.029, +0.073]; KXMLBF5TOTAL n=218, +0.061; KXNFLTOTAL n=154, +0.049; others n of 42–179); see `out/replay.json`. Overlapping book views of one cell are counted once per situation. Mid-entry figures are larger than W89.2's net-of-spread-and-fee figures by construction.

## Quant bar
1. Known-answer tests: 10 in `tests/test_decision_router.py` (default no-bet, ride on a known cell, ride refused at a non-positive lower bound, FADE gated by skill, conflict → NO_BET, agreement → RIDE, T3 overlay, disqualifiers, momentum only with a table, empty-evidence invariant).
2. Applies to pre-game, two-sided, priced markets with an evidence record; not in-play, one-sided or date-only game-day tickers.
3. Measured result: traffic table above (n = 164,354) and the RIDE view with intervals.

## Limits
- NBA and NHL are not replayed: no price archive (GG-1330).
- FADE was not replayed against shadow ledgers (they live on the box and carry no settlement); it is evidence-gated to 0 regardless (GG-1333).
- Everything RIDE is in-sample (GG-1334). Out-of-sample belongs to 90.1's pre-registration.
