# W85.2 results: the accepted gate, replayed on the orders already placed

Pillar: EXECUTION. Measure: orders per market per band per game today; then what the accepted gate would leave.
Source: read-only snapshot of the box (HEAD 174838aa) taken 2026-10-22T23:35Z: `logs/demo_fill_policy.jsonl`,
`exp_output/PREGAME_SHADOW/*` + `settled/*`, `data/shadow/nhl/*` + `settled/*`, `FORWARD_TEST/markouts/markouts.jsonl`.
Script: `12_EXPLORATORY/gate_replay/replay.py` (stdlib, no outcomes used for any parameter). Raw output: `replay_W85_2.json`.
Join: 44,608 `shadow_order ok=true` events (both arms pooled); 0 unmatched to a forecast row. These are **orders, not fills**.

## 1. Orders per market per band per game (today)

| Sport | Orders | Positions (market x band) | Orders / position | Share of orders on far strikes (\|mid-0.5\|>0.25) |
|---|---|---|---|---|
| NFL | 12,756 | 3,101 | 4.11 | 0.524 |
| NBA | 24,438 | 6,643 | 3.68 | 0.517 |
| NHL | 6,855 | 1,438 | 4.77 | 0.560 |
| MLB | 559 | 265 | 2.11 | 0.526 |

Orders per game by cell range from ~7 (moneyline) to ~136 (NBA spread, T1); per-cell rows are in the JSON (`cells`). Every placed order
had positive net edge by the shadow arm's own gate, so the far-strike column is the share of positive-edge orders on far strikes:
a little over half sit on strikes more than 25 points from the 50% line.

**Do they move together within a game?** Yes on totals: within a (game, family) ladder, the majority side holds 0.95-1.00 of the
orders for game totals (NFL, NBA, NHL; MLB 0.87-0.96). Team totals, run/puck lines, spreads and player points are
looser (0.60-0.98 by cell; NBA spreads ~0.60, NBA team totals ~0.65-0.73, NFL team totals 0.81-0.86). Moneyline is ~0.50 because two outcomes of one market are separate tickers. A ladder of
totals strikes is one view of one distribution repeated, i.e. one exposure, not N independent bets.

## 2. The accepted gate in replay

Skill weight: **no `models/*heldout*` file carries a market-referenced Brier or a model-minus-market disagreement.** They
compare to climatology only (MLB 0.2456 vs 0.2486; NFL 0.2185 vs 0.2476; NBA and NHL files hold climatology/LR comparisons only). Under the rule as written, where no
held-out comparison to the market exists the weight is 0, i.e. the market's price. **Result at the rule: w = 0 for every
model, and the gate keeps 0 orders** (zero skill means no order: the post-shrink edge is `-half_spread - fee`, never above the error bar).

Error bar: no held-out disagreement spread exists either. Substitute, flagged: sd of (p_yes - mid) per (sport, market type) over
ledger rows (uses no outcomes).

Sensitivity (counts only; nothing was selected from outcomes; kept = first qualifying order per market x band):

| w | NFL kept (of 12,756) | NBA (of 24,438) | NHL (of 6,855) | MLB (of 559) | ladder exposures NFL/NBA/NHL/MLB |
|---|---|---|---|---|---|
| 0 (rule) | 0 | 0 | 0 | 0 | 0/0/0/0 |
| 0.1, 0.25 | 0 | 0 | 0 | 0 | 0/0/0/0 |
| 0.5 | 15 | 208 | 0 | 26 | 8/47/0/12 |
| 1.0 (no shrink) | 882 | 1,613 | 24 | 152 | 144/236/19/35 |

Even with no shrink at all, the one-position + error-bar + ladder rules cut 12,756 NFL orders to 882 positions in 144 ladder exposures.
Per-band numbers: `replay_W85_2.json` (`gate`).

## 3. DESCRIPTIVE ONLY: settlement minus price, as-if-filled at the limit

Not a result, not used to choose anything. Settled orders only (90 games, game-clustered 95% interval, ratio estimator).

| Set | n | games | mean (per contract) | 95% interval |
|---|---|---|---|---|
| all dropped, w=0 | 11,388 | 90 | +0.034 | -0.020 to +0.088 |
| kept, w=1.0 | 1,610 | 37 | +0.070 | -0.050 to +0.190 |
| dropped, w=1.0 | 9,778 | 90 | +0.028 | -0.026 to +0.082 |
| kept, w=0.5 | 131 | 11 | +0.203 | +0.080 to +0.326 |

The w=0.5 row rests on 11 games and was a sensitivity point, not a choice. Intervals overlap zero except there; fills were not
modelled, so these are not P&L.

## Caveats
- Orders pooled over both ADR-0072 arms; ok=true orders only; fill status not joined here (E1-E3 unchanged this wave).
- MLB has few placed orders (most MLB orders were rejected), so MLB rows are thin.
- First-qualifying-row rule is applied over placed orders in `ts_utc` order, not over all forecast rows.
- Ladder = (game, market family, side). Strike distance is measured against the market's own mid.
- Stage reached (ADR-0075): none of this is a factor; it is an execution gate, scaffold only (see Part B).
