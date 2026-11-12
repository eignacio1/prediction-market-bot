# ADR-0078: Per-arm cell state — a losing look closes an arm, not a cell

**Status:** ACCEPTED 2026-11-10 22:03 / 22:10 PT by the operator's directive (verbatim below; Hard Rule 3: his directive is the acceptance)
**Date:** 2026-11-12 (W111.1, B-076) **Last reviewed:** 2026-11-12 **Pillar:** PROOF **Decisions logged:** true
**Relation:** implements ADR-0077 in the cell registry and the calibration engine; supersedes nothing. Does not edit any frozen pre-registration.

## Decision
1. `MarketTypeCell` carries `closed_arms` (per arm: reason, measured_date, citing decision). Default empty; every existing caller and
   every `CellStatus` value is unchanged.
2. A released look that loses to the market (the pre-registered label `RULED_OUT`) closes the FADE arm only. The cell stays SHADOW and
   keeps logging; RIDE, MOMENTUM, POT_OF_GOLD and NO_BET stay open. The calibration engine reports the frozen label unchanged as
   `verdict_preregistered` plus a `routing` field; it never changes registry status.
3. A winning look (CANDIDATE) opens nothing by itself; capacity and the operator decide.
4. `CellStatus.RULED_OUT` is reserved, in its human meaning, for a market that cannot be traded (no book, liquidity or data; DOCTRINE 1b).
   No scored look assigns it.
5. Closed arms are provisional. The operator reopens them, never a window or a block.
6. NFL_GAME_TOTAL T1 and T2 move from RULED_OUT (W99.2) to SHADOW with `closed_arms={FADE}`.
7. Frozen pre-registrations whose rule says RULED_OUT ends the cell are read through a superseding addendum placed beside them.

## Why
Operator, 2026-11-10 21:41 PT: "Does a quant - that finds through rigorous testing and scaffolding that a certain betting pattern doesn't
beat the "market" keep going? no he fucking routes it to the correct path so that loss still WINS." 22:03 PT: "every single "closed" cell
will get reopened once I feel the project is at a suitable state." 22:10 PT: the scoring engine closing cells is a problem the windows must catch.

## Consequences
P2 reads "verdicts, routed" (closed arms, not closed cells); B1 counts these two cells as logging. The shadow writer was never gated
by registry status, so rows keep flowing.
