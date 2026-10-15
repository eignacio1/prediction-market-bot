# Session Handoff — W75.2 (2026-10-15)

<!-- session-meta
task_id: W75.2
tier: STANDARD
one_line_summary: NFL factor chain end to end (F5/F6 coverage x personnel): builder, sport-neutral rate layer, frozen plan, one fit through ML/spread/total/team total; result inert
vision_pillar: DEPTH
gap_measure: D5(b) NFL applied; D4 NFL point-in-time
gap_delta: D5(b) NFL +1 class applied (F5/F6, applied result = null: MATCHES, no gain); D4 NFL factor classes PIT 0->1 (tests/test_nfl_factors_pit.py, 3 pass). Source: 12_EXPLORATORY/nfl_engine/results_stage2.json
pattern_sweep: n/a (no defect fixed; own-code fixes: eb_k single-column cell, write-fence scan on factors.py)
surface_delta: 0
-->

Status: DONE | PR #263 squash-merged 3c4535e, CI green (test pass). No running component, no Deploy decision needed (exploratory + tests + docs only); t4-mlb untouched.

## Result
F5/F6 stage reached: aggregated, interpreted, APPLIED. 2020-2025 rolling origin, 1,612 games. dBrier vs engine arm B (arm C, prior-season tendencies): ML +0.00009, spread +0.00008, total -0.00003, team total +0.00003; all CIs span 0, all MATCHES (non-inferior), none improved. Term moves a team mean ~0.1 pt; beta flips sign across seasons. Verdict: real trait, inert price input. 2025 ML market comparison (n=182) reported, not judged.
Motion direction: GAP (GG-800). Shell coverage ~55-61% of plays (GG-801). GAP-1 (no 2026 participation file, GG-730) blocks only arm D.

## Reusable
factors.py FactorSpec + rate_layer.py Factor Protocol; next class = new spec + Factor, same study script. Candidate: pressure vs protection.

## Operator decisions
None required. Note: ADR-0075 ladder has no stage for tested-and-null (see W75.3 item 1).

## Notes
origin/main ACTIVE_QUEUE had stray conflict markers (nested from a prior merge); resolved while rebasing.
