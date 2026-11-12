# EXP-036 (NHL) — superseding addendum: a losing look closes the FADE arm, not the cell (W111.1, 2026-11-12)

**Supersedes the registry consequence of rule 1 (a)/(b) in `EXP036_NHL_PREGAME_SHADOW_PREREGISTRATION_2026-10-02.md`. The frozen file is NOT edited.** Everything else in it stands: cells,
definitions, bootstrap spec, judged n, looks, and the label the engine computes. The label is still reported exactly as defined,
as `verdict_preregistered`.

## What changes
Where the frozen file says a `RULED_OUT` label sets the registry cell to `RULED_OUT` and ends the cell, read instead (ADR-0077, ADR-0078):
- The look closes the **FADE** arm (model-disagreement entry) for that cell only. RIDE, MOMENTUM, POT_OF_GOLD and NO_BET stay open.
- The cell stays **SHADOW** and keeps logging; the shadow writer is not gated on registry status.
- A `CANDIDATE-PENDING-CAPACITY` label opens nothing by itself.
- The closed arm is provisional; the operator reopens it.

## Authority
Operator, 2026-11-10 21:41 PT: "Does a quant - that finds through rigorous testing and scaffolding that a certain betting pattern doesn't beat the "market" keep going? no he fucking routes it to the correct path so that loss still WINS." 22:03 PT: "every single "closed" cell will get reopened once I feel the project is at a suitable state." 22:10 PT: the scoring engine closing cells is a problem the windows must catch.
See `03_DECISIONS/ADR-0077_multi-arm-routing-doctrine.md`, `03_DECISIONS/ADR-0078_per-arm-cell-state-closed-arms.md`, DECISION_LOG 2026-11-10 22:03 / 22:10 PT.
