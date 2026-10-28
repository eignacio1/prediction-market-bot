# Decision Routing — which tree gets which situation (W90.2)

**Status:** ACCEPTED by the operator as written, 2026-10-27 ("Accept - proceed in full"). Nothing here is wired to a runner, cell, model or ledger; wiring needs its own pre-registration.
**Pillar / measure:** DEPTH — D5(a) `filtering_mechanisms` and `decision_trees`.
**Operator, 2026-10-26 22:08 PT:** "that's the meaning of having filtering mechs appropriately identifying the correct decision trees and routing mechanisms for execution"
**Code:** `src/prediction_market_bot/decision_trees/router.py` (pure function). **Replay:** `12_EXPLORATORY/router_replay/`.

## In plain English

Every time the bot looks at a market, it has to answer one question before it prices anything: *what kind of situation is this?* The router answers it. It sends each situation to exactly one of five places:

- **FADE** — our model, or one of its factors, says the line is wrong, so we bet against the line.
- **RIDE** — nobody claims the line is wrong because of a model. The market's own price level has been *measured* to be wrong in a known direction (toward its favourite) in this family, at this time before the game, at this price, with this kind of book. We bet with the measured bias.
- **MOMENTUM-FOLLOW / MOMENTUM-FADE** — Strategy J: the price has been moving, and either the move continues (follow) or reverts (fade). The tree is built in the router, but it only routes if a measured transition table is supplied.
- **NO-BET** — the default. A situation goes anywhere else only by *earning* it with a measured number.

The rule that keeps the router honest: **a tree gets traffic only when a measured quantity, with a source, says it should.** No measured skill, no FADE traffic. No ride-table cell with a net-of-fee lower bound above zero, no RIDE traffic. No measured transition table, no MOMENTUM traffic. Everything else is NO-BET, with a reason code saying why.

What the measurements say today:

- **FADE gets no traffic.** The W88.3 paired Brier test (market minus model) puts model skill at about zero everywhere: NHL skill weight 0.0, NBA 0.0, MLB 0.0018, NFL 0.0 (no interval). Until a model beats its market with a confidence interval, the router will not send it a bet. That is the correct behaviour, not a bug.
- **RIDE gets a small amount of traffic.** W89.2 found 11 cells out of 1,258 testable that survive the fee, in-sample. These are candidates, not proven edges, and the router's replay on them is labelled "not evidence" for that reason.
- **MOMENTUM gets none.** No transition table exists, and W89.2 Part B (overreaction after moves of 5c or more) found 0 survivors, so there is no momentum-fade edge to route to.
- **News timing is not a routing condition.** There is no measurement of its effect, so using it would be inventing a threshold. It is registered as a gap.

## Precedence

1. A situation with a disqualifier (no two-sided book, in-play, date-contaminated, price extreme) is NO-BET before any tree is consulted.
2. If RIDE and FADE both claim the market on the **same side**, route to RIDE (the tree with a measured net edge) and flag that FADE agreed.
3. If they claim **opposite sides**, NO-BET with reason `conflict`. Two measured signals disagreeing is information, not a coin flip.
4. MOMENTUM yields to RIDE and FADE on the same market; it only routes alone.

**T3 (ADR-0014):** CONFIRM / FADE / NEUTRAL is an *overlay on the FADE tree only*, not a tree of its own. T3 compares `current_mip − t1_mip` to the model's side: CONFIRM (price moved toward the model) proceeds, FADE (moved against it) holds, NEUTRAL proceeds. The router applies it as: FADE route + T3 FADE → NO-BET (`t3_hold`). It does not touch RIDE. (Note the naming collision: the T3 verdict "FADE" is a *hold*; the FADE tree is a *bet*. Reason codes keep them apart.)

## Routing conditions

Every condition is a measured quantity with its source.

| Condition | Measured quantity | Source | Threshold | Today |
|---|---|---|---|---|
| FADE eligible | Model skill vs market, per sport and family: `skill_weight = clip(1 − Bm/Bk, 0, 1)` and the 95% CI lower bound of (market − model) Brier | W88.3 `12_EXPLORATORY/market_history/results_W88.md`; `position_gate.skill_weight` | weight > 0 **and** CI lower bound > 0 | NHL, NBA, MLB, NFL all fail → 0 traffic |
| FADE side | Sign of `model_p − market_mid` | the model | edge net of fee > 0 (`quant.money.net_edge`) | n/a |
| RIDE eligible | A ride-table cell for (family, time-to-start tier, price bucket, book class) with net-of-fee lower bound > 0 | W89.2 `12_EXPLORATORY/longshot_bias/results_W89.md`; 90.1 `ride.py` once on main | cell lower bound > 0 | 11 candidate cells (in-sample) |
| Book state | Book class (tight = half-spread ≤ 1c, else wide) | archive `half_spread`; encoded in the ride-table key | part of the cell key, not a separate threshold | — |
| Time to start | Tier (T0-2h, T2-6h, T6-24h, T>24h) | `longshot_bias/calib.py: tier`, from the market's true start time | part of the cell key | — |
| Price level | Price bucket (5c) | `calib.py: bucket` | part of the cell key | — |
| MOMENTUM eligible | A measured transition table (move size, horizon → continuation/reversion rate, with interval) | none exists; W89.2 Part B found 0 survivors | table supplied and lower bound > 0 | none → 0 traffic |
| Recent movement | 1h mid move | archive `yes_mid` | used only as input to a supplied MOMENTUM table | — |
| News timing | — | not measured | **not a condition** | gap registered |
| Disqualifiers | No two-sided book; in-play (start passed); NFL D0 date-only tickers (contaminated); price outside the table's range | `calib.py`; W89.2 | hard NO-BET | — |

## What this does not do

It does not size, place or log anything, and it is not wired to any cell. It is a pure function of (situation, evidence). Whether any tree's traffic is worth betting is a separate, pre-registered question; the router only makes sure no tree is *asked* to bet without a measurement behind it.
