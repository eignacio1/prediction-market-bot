# ADR-0072 Addendum — 2026-10-22 — DRAFT: a third forward-test arm that uses the position gate

**Status:** DRAFT. Not accepted. Nothing in this file is in force until the operator accepts it. Amends nothing in the accepted
ADR-0072 text or the 2026-10-20 and 2026-10-21 addenda (Hard Rule 3).
**Decisions logged:** false (the gate itself was accepted by the operator 2026-10-21 20:28 PT; this addendum only proposes where it is tested).

## Authorization this builds on
> "A real gate: one position per market per band; the model is pulled toward the market by its measured skill; an order goes in
> only when what is left clears the fee plus the model's measured error; a game's ladder counts as one exposure." (operator,
> accepted 2026-10-21 20:28 PT)

## What was measured (W85.2, snapshot 2026-10-22T23:35Z; `12_EXPLORATORY/gate_replay/results_W85.md`)
- 44,608 placed orders sit on 11,447 positions (market x band): 3.9 orders per position; NFL 4.1, NBA 3.7, NHL 4.8, MLB 2.1.
- About half of all placed orders (0.52) are on far strikes; within a game, totals ladders agree on side 0.95-1.00.
- No `models/*heldout*` file carries a market-referenced Brier or a model-minus-market disagreement. Under the accepted rule the
  skill weight is therefore 0 for every model, and the gate keeps 0 orders. The gate cannot send an order until a held-out
  comparison against the market exists.

## Proposal
1. The forward test gains **one arm** whose orders are chosen by `position_gate.py` (built, tested, unwired in W85.2). It would
   first be used by the NFL market-anchored challenger (W85.1).
2. **Control and treatment are untouched:** same seed, share, judged n, placement rule, switches and decisions as before.
3. The new arm inherits no verdict from the old arms and gets its own pre-registered look.
4. **Precondition before any wiring:** a held-out Brier against the market (and the disagreement spread) for the model the arm uses.
   Until then the arm would place nothing, which is the rule working, not a fault.
5. Wiring is a separate wave and a separate change to `shadow_flat_stake.py`, which W85.2 did not touch.

## Operator decision (one line)
Accept this as the third-arm design, or not? Recommendation: accept the design, wire nothing until the market-referenced held-out Brier exists.
