# Session handoff - W124.3 H-EXEC-4 (fills net of fee actually charged)
**Common rules first line (origin/main):** "# Wave 124 common rules". Branch `session/20261124T002040Z-w124-3-exec-fills`.
**Outcome:** PREREG frozen and committed (0ebd092) before any post-freeze fill was read. Status COLLECTING. Part C = schedule only.
- Part A: `exec_fills/PREREG.md` (population after 2026-11-20T20:00Z, net after fee charged, CV + pairing + EB pooling, OBF spend, rule).
- Part B: DESCRIPTIVE only, and not net-of-fee: per-fill rows are on the box only; variance reduction per tool not measurable yet.
- Part C: first eligible look 2026-12-01 (needs >= 7 days of forward fills). `SCHEDULE.md` + `schedule.json`.
- Part D: registry row H-EXEC-4 updated to COLLECTING. `exec_fills.py` + 7 known-answer tests (pass locally).
**Flags:** 124.1 not on main, so local helpers (swap when it merges). n dates are ESTIMATES (W123.4 rate). Design factor 2 assumed.
**Needs window:** a read-only allowlisted box task exporting per-fill join records (code PR); without it no look can run.
directive_conflicts: none found. surface_delta: +0 runtime (analysis script and tests only). pattern_sweep: fee-from-fill rule
(`join.fee_of_fill`) reused, no second fee path added. gap_measure: EXECUTION E2 - no number moved (no per-fill net on this machine);
forward look date set 2026-12-01.
