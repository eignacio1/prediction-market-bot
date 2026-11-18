# ADR-0072 Addendum PROPOSAL — per-arm placement policy and the demo arm-book cap raise (2026-11-17)

**Status: APPROVED by the operator 2026-11-17 PT ("Yes - I provide my approvals."), both decisions. Nothing is on yet:** decision 1 waits for the frozen table (spread-logged orders, 30+ per side); decision 2 waits for GG-1942. Originally PROPOSED; Written by W116.2 (B-095). The frozen ADR-0072 file and the 2026-11-12 arm-orders
addendum are not edited. Both switches ship OFF (`deploy/demo_fill.env` carries comment lines only; the code defaults are off).
Measure: EXECUTION — E1 / E2 / E3 per arm and per placement option; D6 layer 7 (execution with fills measured).
DEMO money only, flat demo stakes, `kelly_fraction` 0 everywhere, no real capital (Hard Rule 2).

## What would change (two separate decisions)

**1. `ARM_PLACEMENT_POLICY=on`.** Today every router-arm demo order rests at our side's touch and is cancelled after 60 s. With the
switch ON, `c5_execution/placement/policy.py` reads a FROZEN table (`config/placement_policy.json`, written by a reviewed commit from
`placement.model.option_table`, never by the running bot; Hard Rule 4). For each arm, or arm and leaf, the table names one of
rest_touch / rest_inside / cross / no_place. A cell the table does not name, or names without support, stays at rest_touch. With no
table, every cell stays at rest_touch. The order row logs `placement` and its reason.

**2. `ARM_BOOK_CAPS=raised`.** The demo arm book has its own caps in `arm_sizing`, separate from risk.py (W116.2 A1, 580cce8): base 5
orders per event / $50 a day / $25 per arm budget (the default). The raised set (25 / $2,500 / $1,500) sits behind the switch. Raised,
the book would place about 2,200 demo orders a day instead of about 50: on the box read, `size_zero: day` skipped 9,093 orders and
`daily_breaker` 690. **Precondition: GG-1942.** The exposure gate does not treat `ARM_ORDERS` as an advisory book. With
GATE_MODE=enforce, about $200 of open demo stake would breach `max_drawdown_pct` 0.20 on the $1,000 shadow notional and halt every
book. Fix that first; then raise the caps.

## The evidence today (box read 2026-11-18T00:59Z, code fb8000c deployed 00:54Z; post-epoch all sides only, GG-1771)

The join: outcome lookups failed **0 of 486** (before: 244 of 432); 432 resolved, 54 pending, 0 void. All three arms are on
rest_touch; arm n at rest_inside is 0. The pre-epoch YES-only rows contain no arm orders, because arm orders started 11-12.

| Arm | Orders | Fills, P(fill) [95%] | E2 per filled contract (before / after fees) | E3 win rate, fills vs non-fills | Selection term [95%], n filled/unfilled | Net per order: rest_touch | Net per order: cross (assumed spread) |
|---|---|---|---|---|---|---|---|
| RIDE | 279 | 39, 0.140 [0.104, 0.185] | +0.006 / −0.008 | 0.69 vs 0.81 | −0.058 [−0.195, +0.080], 39/217, supported | +0.001 [−0.019, +0.020] n=256 | +0.023 [−0.023, +0.069] n=256 |
| MOMENTUM | 96 | 20, 0.208 [0.139, 0.300] | +0.088 / +0.075 | 0.50 vs 0.50 | +0.041 [−0.222, +0.305], 16/60, not supported | +0.018 [−0.030, +0.066] n=76 | +0.020 [−0.091, +0.131] n=76 |
| FADE | 111 | 6, 0.054 [0.025, 0.113] | +0.117 / +0.106 | 0.33 vs 0.38 | −0.102 [−0.499, +0.296], 6/94, not supported | +0.007 [−0.015, +0.029] n=100 | +0.183 [+0.089, +0.277] n=100 |

Markouts (held-side mid minus fill price, mean): RIDE h1 −0.013 (n 37), close +0.002 (n 30); MOMENTUM h1 −0.010 (n 20); FADE h1 −0.006
(n 6). The h5 / h30 n are below 10.

**What the numbers can and cannot carry.**
- The cross column assumes a spread of 2¢ (NHL 6¢; W94.3C). None of the 486 orders logged its spread, because the logging landed in
  fb8000c. Every order from now on carries it, and the table must be re-fitted on those orders before it is frozen.
- The intervals treat orders as independent. They are not: many orders sit on the same game on one or two slates, so the true
  intervals are wider. FADE cross +0.18 is a counterfactual on 94 orders that did not fill, from few games.
- On rest_touch, RIDE's fills win less often than its non-fills (0.69 vs 0.81). The point estimate says the fills are adversely
  selected, but the interval includes zero.

## The comparison and its judged n (pre-registered here; frozen when approved)

- **Unit:** one router-arm demo order, post-epoch, resolved. **Statistic:** realized net per order placed (won − price − exact fee if
  filled, else 0), per arm and per option.
- **Freeze:** the table is refit from orders that carry a logged spread, with at least 30 resolved orders on each side of every cell it
  names (`MIN_N` 30), and committed as `config/placement_policy.json` before the switch turns on.
- **Judged at:** 100 resolved orders per (arm, option) the table chose after ON, compared with the frozen estimate and with the
  rest_touch orders that cell placed before ON. Never read below 100. Report: an interval clustered by game.
- **Routing result, not a stop:** if an option's realized net has a 95% upper bound below its rest_touch baseline, the next frozen
  table routes that cell back to rest_touch or no_place. This closes only that hypothesis (EXP id assigned at freeze, parked for R&D);
  no arm or cell closes.
- **Not supported by this data:** rest_inside on the arm path (GG-1943), any depth conditioning (GG-1944), queue position, and size
  above the $1 demo stake. Cross assumes the far touch holds the stake: true at $1 in 95.7–98.4% of samples (W94.3C), not at size.

## What stays
Kill switch (NFR-03), exposure gate, per-event and same-game-cluster caps, the 60 s cancel for resting options, epoch rules,
client-order-id namespace, and the zero-orders alarm all stay as they are. `kelly_fraction` 0. DEMO host only.
