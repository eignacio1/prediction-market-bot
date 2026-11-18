# Router v2 (pooled + sequential leaf map): pre-registration (W116.1 / B-094)

**Frozen:** 2026-11-18T00:49Z, committed before any forward row is scored. **Last reviewed:** 2026-11-17.
**Frozen artifacts:**
- `src/prediction_market_bot/decision_trees/leaf_maps/leaf_map_v2.json`, sha256
  `79f46cb4ae1fded6d01f5e8e59cb816848294b550061566c3b8779e7721bad5b`. It was fit on all 106,430 W110.5 rows through
  2026-11-11: 365 seen leaves, 900 keys, **0 armed**.
- The rule in `decision_trees/evidence/pipeline.py` with the `Config` below.

Any change to either starts a new pre-registration; this one is never edited.
**v1 stays the frozen test:** `LEAF_MAP_FORWARD_PREREGISTRATION_2026-11-12.md` is untouched, and the router default is
`PM_LEAF_MAP_VERSION=v1`. v2 is logged only once the operator approves turning it on.
**Serves:** OPERATOR_DIRECTIVES D-01 (every route optimized by decision trees). Measures: PROOF P1/P2, DEPTH D6 layer 5.

## The rule (frozen)
A leaf = (sport, market type, band, favoured-side price bin, move bin). Each Tuesday 10:00 UTC look, every arm in
(RIDE, FADE, MODEL_FADE, MOMENTUM) is updated in two ways:
- **Pooled posterior.** An empirical-Bayes Gaussian tree: sport > family > band > bin > move. DerSimonian-Laird tau per
  depth, floor 0.005; root N(0, 0.10²). Game-clustered moderated variance (k = 10), times the family design effect.
  NFL nodes get the nflverse long-history prior with transfer sd 0.03.
- **E-process per node** at depth >= 2. A mixture likelihood ratio against net = 0, with the prior fixed from earlier
  looks only. Increments under 5 games carry forward. The increment variance is max(plug-in, binary net=0 variance),
  `null_var="binary"`, the W116.1 validity fix.

A leaf takes arm a only when **P(net_a > 0) >= 0.90 AND the mean of the e-processes over its path nodes >= 10**
(alpha 0.10). Among arms that pass, it takes the highest posterior mean; otherwise NO_BET. The path *average* is
stricter than "any node on the path" and is what keeps the bound valid per leaf path whatever the number of looks
(Ville). Forward looks continue the shipped e-processes; they never restart them.

## Forward rows and scoring (as v1)
- **Rows:** shadow rows with `start_time_utc` at or after the freeze, deduped (`retro_route.dedupe`), settled. No
  orders, no stakes, no kelly_fraction change. These are paper rows, not fills (GG-527).
- **Net:** per contract after the Kalshi taker fee at the taker price, held to settlement (`retro_route.side_net`).
  90% game-clustered bootstrap (2000 resamples, seed 116).
- **Arm scoring:** a leaf's arm is scored only on rows that start after the look at which it earned the arm.

## Tests and judged n
1. **v2 vs v1, per sport:** paired net per row on the same forward rows, NO_BET counted as 0. Judged at 60 forward
   games per sport, scored once.
2. **Each arm v2 earns:** judged at 15 forward games after the arm was earned.

Benjamini-Hochberg at q = 0.10 across the tests of type 2 that reach their n. The e-process claim itself needs no
correction: it is always valid per path.

## Reading the result (a routing result)
- If v2 beats v1 per sport with the interval above 0, v2 becomes the candidate default (a new decision; not automatic).
- If v2 does not beat v1, v2 is hypothesis closed (EXP-W116.1-v2, parked for R&D). v1 is not changed by this test.
- An earned arm whose forward lower bound is <= 0 is routed to no bet at the next map.

## Pre-registered expectation (modal, stated before data)
On the W110.5 data v2 arms nothing. Power calendar: at today's posterior means no leaf can earn an arm within 104
weeks; at a true +0.05 per contract the first could earn one around 2027-01-20.
- **Modal outcome:** v2 logs NO_BET on essentially every forward row through the 2026-27 NFL season.
- 0 to 3 leaves earn an arm by 2027-03-31.
- Test 1 shows v2 ahead of v1 by roughly v1's loss (W116.1 held out: +0.0064 per row [−0.0009, +0.0138]). That is the
  value of abstaining, not of a found arm.

## Out of scope
Orders, sizing, live ledgers, model changes, and the filter level (settled rows have no filter column: GG-1938).
