# ADR-0072 (DRAFT) — Demo-venue fills: order-placement rule

**Status:** PROPOSED · **Switch:** OFF by default (`DEMO_FILL_PLACEMENT_RULE` unset = current behaviour) · **Date:** 2026-10-09 · **Wave:** 63.3
**Note:** number provisional; renumber at merge if ADR-0072 is claimed elsewhere. Nothing in this ADR is built or enabled.

## Design input (Part B evidence)

Source: `05_RESEARCH_EXPERIMENTS/RESULTS_SUMMARIES/W63_3_distance_generator_fill_markouts_results.md`. Read-only demo-venue GETs; game-clustered 95% CIs.

1. **Fills are adversely selected.** Settled win rate of CONFIRMED_FILLED vs never-filled orders: T1 MLB 28.2% vs 50.6%; T4 MLB 24.1% vs 48.7%. Price-adjusted settlement markout (win − price paid): filled −0.39 [−0.49, −0.28] / −0.25 [−0.37, −0.11]; never-filled +0.07 / +0.10.
2. **The filled set is the losers.** Orders are good-till-canceled limits at the model mid. They rest for a median of 5,873 s (T1) / 2,276 s (T4) and fill when the market moves against the held side. Post-fill markouts are negative at 1/5/30 min (T4 ≈ −0.17 at all three, CI excludes 0); markouts from submit are ≈0 — the loss is incurred between submit and fill.
3. **Stale pricing is a second factor.** The ledger mid sits below the venue mid by 0.12 (T1) to 0.16 (T4, filled) on the minority of rows with a two-sided book; limits sit 0.27–0.54 below the ask. A bid that far from the offer fills only when the book collapses toward it.
4. **Immediate fills are not the problem.** T4 fills ≤60 s: win rate 35% (CI wide, n=51), settle-at-fill-price −0.07 [−0.40, +0.15]; resting fills (>60 s): win 19%, −0.33 [−0.41, −0.24].

Interpretation: adverse selection of resting orders, compounded by model-mid prices that lag the venue book. Not a latency or take-vs-make fee effect.

## Candidate rules (to be tested, not adopted)
- **R1 cancel-after-N:** cancel unfilled orders after N s (evidence suggests N ≈ 60 s; immediate fills are the benign subset). Cheapest; removes the stale-resting population.
- **R2 price vs book:** price relative to the observed venue bid/ask rather than the model mid; skip when the book is one-sided or the mid gap exceeds a threshold.
- **R3 take vs make:** insufficient evidence; taker share is 3.5% (T1) / 24% (T4) and the taker subset is small.

Evidence best supports **R1, with R2 as a pre-condition**. This cannot be validated from existing data: it needs a forward test on the demo venue.

## Decision requested
None yet. A forward A/B (switch ON for a pre-registered share of orders) requires its own pre-registration and ADR acceptance. Until then the switch is OFF.

## Caveats
Demo book is thin/one-sided: venue-mid coverage is small (T1 n=6, T4 n=13 filled). Never-filled markouts from submit (+0.18 to +0.30) mostly reflect limit-to-book distance, not information, and are not used for the verdict. Never-filled orders are mostly ledger-derived (order GETs 404 for 301 of 551 sampled); ledger-limit vs order-limit matched 1 of 2 checked.
