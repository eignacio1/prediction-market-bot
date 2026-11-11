# SESSION_HANDOFF — W110.2 / B-068 NBA factors interpreted → applied

```
session-meta:
  block: W110.2 (B-068), STANDARD, single deliverable
  status: DONE (applied paths); market comparison PARTIAL (data limit)
  vision_pillar: DEPTH
  gap_measure: D5(b) NBA applied
  gap_delta: 5 → 10 of 17 factors (SEATS/nba.toml: B10, B12, B13, P1, P2 promoted; B11 stays interpreted). Source: 02_ARCHITECTURE_DESIGN/SEATS/nba.toml @ 58c1cb1
  pattern_sweep: n/a (no defect fixed)
  surface_delta: none (no cron, service or workflow added; new library module + exploratory scripts only)
```

- PR #475 merged @58c1cb1, CI green (run 42968426246). Box read requested: 04_EXECUTION/BOX_TASKS/requests/20261111T055822Z_deploy_truth_read.toml (result lands under BOX_TASKS/results/; not read this session).
- Code: src/prediction_market_bot/nba_engine/factors_applied.py + tests/test_nba_factors_applied.py (11 known-answer tests). Study: 12_EXPLORATORY/nba_applied_w110/ (RESULT_W110_2.md is the record).
- Result (n=2268 held-out games, paired vs v2_core, realized outcomes): usage/lineup cross improves spread −0.0041 [−0.0063,−0.0019] and team total −0.0017 [−0.0026,−0.0009]; geometry and officials null; PAM hindsight-only, small; no family helps ml.
- **Limits:** Kalshi has no 2025-26 spread/total/team-total quotes (Oct 2026 only), so these are not market-edge claims; ml market comparison not rerun (deltas positive, 109.1 base already lost). PAM records all recorded_at 2026-05-28 → hindsight; officials crew time unpublished (GG-1390) → upper bound. 7×4 comparisons uncorrected.
- Registered-not-fixed: none new. Untracked `12_EXPLORATORY/12_EXPLORATORY/` in the primary tree predates this session (not mine; not touched).
- Next: B11 absorber × play-type cross (W83 null, needs profile data); score spread/total/team-total vs Kalshi once 2026-27 quotes accrue (forward, point-in-time PAM).
- Operator decisions: none.
