# Session Handoff — W75.3 (2026-10-15)

<!-- session-meta
task_id: W75.3
tier: STANDARD
one_line_summary: Seat interface (4 sports) + NFL/NBA tension registers + ARCHITECTURE_COMPONENTS; D4/D5 now generated
vision_pillar: DEPTH
gap_measure: D5
gap_delta: D5a NFL 0->3/8, NBA 0->2/8 (evidence-counted on main); D5b NFL 7 agg/2 interp/4 applied of 16, NBA 0/2/4 of 8; D4 NFL data layer+engine+test, others none (scripts/distance_to_optimum.py, 2026-10-15)
pattern_sweep: n/a (docs/scripts/tests only)
surface_delta: none (no src change)
-->

Status: DONE | PRs #260 (Part A) and #261 (Part B) merged, CI green.

## Generator output
- D4  NFL: data layer + engine scaffold + scaffold test · NBA: none · NHL: none · MLB: none
- D5a NFL 3/8 (decision_trees, structural_tensions, seat_interface) · NBA 2/8 (structural_tensions, seat_interface) · NHL 0/8 · MLB 0/8
- D5b NFL 7 aggregated/2 interpreted/4 applied of 16 · NBA 0/2/4 of 8 · NHL, MLB stubs

## Hand count vs evidence count
Window hand count said NFL ~1 component and ~2 applied factors. Evidence gives NFL 3/8 (the two new ones are this block's own) and 4 applied factor rows (3 classes: team, rest, QB). NFL temporal_evolution is deliberately "none" so D5a is not inflated.

## Operator decisions
1. ADR-0075 §2 stage ladder (aggregated > interpreted > applied) cannot express a tested-and-rejected factor (NFL-T7). Not decided in-session; needs a definition change or a terminal "tested-no" stage.
2. NBA registry says game cells are not_implemented while nba_model.py dispatches those markets (NBA-T1): registry or code is wrong.
3. Registered tensions but did not register GG ids; the window should assign them if wanted.

## Notes
Seat files are v0 drafts for a football/basketball eye to correct. Forward-test "1 vs 29" is NHL treatment vs control (W73.1), not MLB. strategic-handoff.md gained a tension-review step (step 5b).
