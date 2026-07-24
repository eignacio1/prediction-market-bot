# Iteration MC Progress — append-only

Completion log for `ITERATION_PLAN_MC_REMEDIATION_2026-07-22.md`'s 4-window parallel
workstream (A/B/C/D). One line per completed task, append-only (see `.gitattributes`
`merge=union` for this file — do not edit existing lines in place).

Format: `<TASK> DONE commit=<sha> — <one-line summary>`

---

A1 DONE commit=ef6b00e — shrinkage flag=ENABLE_A1_SHRINKAGE_CANDIDATE (env A1_SHRINKAGE_CANDIDATE_ENABLED=1), column=ba_l10_shrunk_a1_candidate, K=400 (holdout-tuned, plateau K~300-750), PRIOR=0.2512 (unchanged from ADR-0047), files=src/prediction_market_bot/c2_feature_store/mlb_features.py, scripts/tune_a1_shrinkage_k.py
# Iteration MC Remediation — Progress Log

Append-only. One line per completed sub-item, per `ITERATION_PLAN_MC_REMEDIATION_2026-07-22.md`.

- B1 DONE commit=78f2967 — GG=135 (renumbered from session-local GG-134, which collided with a concurrent session's own GG-134 at commit 6b21f52)
- B2 DONE commit=78f2967 — frontier file=05_RESEARCH_EXPERIMENTS/MC_SURVIVABLE_EDGE_FRONTIER_2026-07-23.md, survivable-edge=MAIN +0.169%/bet (at current sizing, ~27x best observed cohort mean) / T4 ≈ -0.0005%/bet (already survives near-zero edge, edge-limited not ruin-limited)
