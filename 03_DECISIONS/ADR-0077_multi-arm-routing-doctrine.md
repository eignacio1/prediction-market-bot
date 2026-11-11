# ADR-0077: Multi-arm routing — every route optimized by layered decision trees

**Status:** ACCEPTED 2026-11-10 21:45 PT by the operator (directives 21:35, 21:41, 21:45 PT, verbatim in DECISION_LOG; "Yes go add it")
**Date:** 2026-11-11 (SW-9) **Last reviewed:** 2026-11-11 **Pillar:** DEPTH + PROOF **Decisions logged:** true
**Relation:** extends ADR-0075 (betting architecture) and ADR-0068 (horizon); supersedes nothing. Re-scopes the CLAUDE.md edge condition
(`model_p > market + vig`) to the fade arm's entry rule.

## Decision
1. For every registered cell, a layered tree chooses the arm: ride the market, fade it, momentum, pot of gold, no bet. Layers: market
   state; factor filters; a per-cell tree whose depth follows ADR-0068; then risk / sizing; then execution.
2. The engine's probability is an input to the tree, not the bet.
3. A factor is applied (ADR-0075 stage "applied") when it is a tested split in the tree, scored per leaf on held-out net after costs for
   each arm. "Model vs market" Brier is reported at most; it is never the verdict on a factor, cell or strategy.
4. A pattern that does not beat the market is routed (often to ride or no bet), never abandoned. Frozen tests judge cells and leaves;
   they do not gate building.
5. New measure D6 (CLAUDE.md distance table): cells wired end to end through all seven layers.

## Why
Operator, 2026-11-10 21:41 PT: "my vision from DAY 1 was to build out the decision trees so we optimize every single route while using
tried and true math scaffolding and betting architecture. Does a quant - that finds through rigorous testing and scaffolding that a certain
betting pattern doesn't beat the "market" keep going? no he fucking routes it to the correct path so that loss still WINS." The project's
canonical file stated the beat-the-market rule as the strategy, and every session inherited it (window error log W48 / W50 / W52).

## Consequences
Wave 110 blocks score factors as tree splits (addendum 2026-11-11). Doctrine lives in `02_ARCHITECTURE_DESIGN/DOCTRINE.md`, reviewed
every wave close, with a freshness check at session start.
