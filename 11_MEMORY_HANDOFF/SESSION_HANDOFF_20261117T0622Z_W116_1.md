# Handoff — W116.1 (B-094, QUANT, Opus) — PARKED at session limit

Status: PARTIAL. Parked safely: nothing merged, no live file touched, `router.py` / `leaf_map.json` / v1 pre-reg unchanged.
Branch: `session/w116-1-evidence-opus` @ 7625503 (pushed). The old branch `session/20261117T010343Z-w115-1-evidence` on the
remote still holds Fable's pre-rebase 73c3fa8; it was not force-pushed. Continue from the new branch.
Worktree: PM-worktrees/20261117T010343Z-w115-1-evidence (local HEAD = 7625503).
Corpus: the exact W110.5 snapshot is in session scratch d4678954…/scratchpad (106,430 rows). Not PM-scratch/w111_3.

## Result (12_EXPLORATORY/evidence_design/RESULT.md)
- v2 pooled abstains: 0/356 leaves armed on fit, 0/365 on the full corpus, 0 held-out bets. **v2 does not win on evidence.**
- v1 per-leaf held out: −0.0064/row [−0.0138, +0.0009]; NFL −0.0201 [−0.0369, −0.0054].
- Ride every favourite: −0.0256 [−0.0394, −0.0129].
- v2 − v1: +0.0064 [−0.0009, +0.0138]. That is the value of routing to no bet.
- **Validity defect fixed.** Fable's e-process used the plug-in variance, which collapses on binary payoffs. On a binary
  null it made false claims 275/300 (92%); after the null-variance floor, 2/300, with a planted +0.10 found 79/100. One
  MLB leaf had log E 32.9 on 15 games.
- Power at a true net of +0.05/contract: v2 84 leaves (first 2027-01-20), v1 BH 46 (first 2027-02-17). At today's
  means: none.
- Tests: tests/test_evidence_w115.py, 14/14 pass locally. CI has not run.

## Remaining (in order)
1. `leaf_map.py`: `PM_LEAF_MAP_VERSION` env (default v1; v2 loads `leaf_maps/leaf_map_v2.json`). Add `posterior=None` and
   `source=None` to `LeafDecision`. v2 records have no thin/fit/test/bh, so use `rec.get`. Add a test.
2. Freeze the v2 pre-registration (template: 12_EXPLORATORY/retro_route/LEAF_MAP_FORWARD_PREREGISTRATION_2026-11-12.md).
   State the path-averaged e-process and `null_var="binary"`.
3. Register GG-1936 (no free NBA/NHL closing-line history), GG-1937 (Kalshi history needs candle parsing; box KXNFLGAME
   candles, 358 MB) and GG-1938 (settled rows carry no filter column). Add a new GG for the e-process validity defect,
   fixed on the branch.
4. Run `precheck_changed.py`, open the PR, merge on green, read `deploy_truth_read`, record the t4-mlb restart decision.
5. Update the queue row. Add "Needs your decision": "turn router v2 on for logging (v1 stays the frozen test)". Given 0
   armed leaves, v2 logging would log NO_BET everywhere: say so.
6. Read OPERATOR_DIRECTIVES.md. Fill directive_conflicts.

pattern_sweep: the plug-in variance in a sequential test — only evidence/pipeline.py uses `log_e_increment`. Not swept
further (grep `var_cr()` in src/quant next session).
surface_delta: 0 (no runtime component).
directive_conflicts: not yet read (session limit).
vision_pillar: PROOF / DEPTH-D6. gap_measure: leaves with an arm held out, v1 113 fit / 1 interval above 0 vs v2 0.
gap_delta: v2 validity restored (false claims 92% → 0.7%); no pillar number moved.
