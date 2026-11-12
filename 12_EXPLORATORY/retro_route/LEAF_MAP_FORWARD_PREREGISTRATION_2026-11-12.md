# Leaf-map forward test: pre-registration (W111.3 / B-079)

**Frozen:** 2026-11-12T00:25Z, committed before any forward row is scored. **Last reviewed:** 2026-11-12.
**Frozen artifact:** `src/prediction_market_bot/decision_trees/leaf_map.json`, sha256 `14cb271e963ae760c89592e8fa4c5b18c9cf2e6dbd755f62f523d12056da73ec` (fit on the earliest 70% of games, W110.5; 365 leaves, 113 routed non-thin). Any change to the map starts a new pre-registration; this one is never edited.
**Serves:** OPERATOR_DIRECTIVES D-01 (every route optimized by decision trees), D-08 (pot of gold routed in). Measure: PROOF P1/P2 and D6 layer 5.

## What is tested
For each of the 113 routed leaves, the arm the map assigns (RIDE / FADE / MODEL_FADE / MOMENTUM), taken on every forward shadow row that falls in that leaf. Plus three family leads, taken on every forward row of the family: RIDE on NFL moneyline, MODEL_FADE on NHL puck line, FOLLOW MOVE on NHL moneyline (held-out leads from W110.5, not verdicts). Total tests: 116.
Pot of gold and open-based momentum (Part B) are scored per leaf as a reference, not tested here and not used to choose arms.

## Forward rows
Shadow rows (`PREGAME_SHADOW` ledgers, `data/shadow/nhl`) whose `start_time_utc` is at or after the freeze time above, deduped as in `quant/retro_route.dedupe`, settled. Rows logged earlier are fit or held-out data, never forward. **No orders, no stakes, no kelly_fraction change.** Paper rows, not fills (GG-527); the ADR-0072 demo test is unchanged and separate.

## Scoring rule
Net per contract after the exact Kalshi taker fee at the taker price (ask for YES, 1 minus bid for NO), held to settlement (`retro_route.side_net`). Mean pooled over rows; 90% game-clustered bootstrap interval (2000 resamples, seed 111); one-sided p for mean > 0. The leaf's arm is the one in the frozen map; the leaf is looked up by the frozen leaf key (sport, market type, band, favoured-side price bin, move bin).

## Judged n
- **Per leaf:** 15 forward games with at least one row in the leaf. Below that the leaf is reported as "not yet judged" and counts for nothing.
- **Family lead:** 40 forward games in the family.
- **Pooled:** all routed leaves together, 60 forward games per sport; reported per sport.
- Scored once per test when its n is reached (no peeking at the interval before then). A look at a test is its first look at that n; a later look needs a new pre-registration.

## Multiplicity
Benjamini-Hochberg at q = 0.10 across all 116 tests that reach their judged n.

## Reading the result (a routing result, not a verdict on a market)
- Lower bound above 0 and BH-rejected: the leaf keeps its arm and is a candidate for a stake proposal (needs its own pre-registration, ADR-0076 gates; none here).
- Otherwise: the leaf's arm is **closed (routed)**; it goes to no bet or to the arm with the best forward net, decided by the next map. Nothing is ruled out.

## Pre-registered expectation
Most leaves will not reach 15 forward games before the season thins them (NFL ends in January; NHL and NBA run to spring). Modal outcome: a minority of leaves judged, none BH-significant at the first look, family leads wide. Stated before the data.

## Out of scope
Orders, sizing, live ledgers, model changes, factor filters as splits (not supplied per row by any runner yet: D6 layer 3 stays open).
