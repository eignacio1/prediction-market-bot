<!-- session-meta
task_id: T-1270
tier: STANDARD
timestamp: 2026-10-27T04:45:00Z
commit: 1a741d5
one_line_summary: W89.4 NFL absorbing-chain sim prices ML/spread/total/team totals from one joint distribution; worse than close, Gaussian-equivalent, no edge
gg_touched: none
adr_touched: none
plan_deliverable_moved: no
vision_pillar: DEPTH
gap_measure: D4 (NFL) + families priced from one joint distribution
gap_delta: NFL D4 scaffold -> whole board from one joint sim, offline; families 0 -> 4 (12_EXPLORATORY/nfl_gamestate/results.json). No edge.
pattern_sweep: n/a (no defect fixed; start_state and safe_out bugs were in this session's own new code)
surface_delta: 0
-->

# SESSION_HANDOFF W89.4 — NFL game simulation (DONE)

PR #344 merged as 1a741d5 (first CI run failed the exploratory-fence test; fixed, rerun green). Offline exploratory; nothing live.

## Strategic Decisions This Session
None — implementation-only.

## Result
Play-level absorbing chain (160 states x 8 absorbing classes), point-in-time team ratings, 2000 sims/game, 272 REG games in each of 2024 and 2025.
- Brier sim minus market: moneyline +0.021 / +0.018 (CI excludes 0); spread +0.011 / +0.019; total +0.005 / +0.008. Never better than market.
- Versus same-mean Gaussian: |diff| <= 0.005, so no shape information.
- Key numbers 7, 10 reproduced; 3 at about half the real frequency. Chain under-scores by ~0.15 pts/drive; OT 3.4% vs 5-6%.
- Detail: `12_EXPLORATORY/nfl_gamestate/results_W89.md`.

## Proposed seat row (window applies)
D4 NFL: "whole board from one joint sim, offline; worse than close at centre". Leave the `[[engine]]` artifact alone. Next cheapest DEPTH move: score-state and late-clock logic, then QB/availability.

## Pending
Kalshi 2025 KXNFLGAME comparison, frozen `nfl_pregame_v1` comparator, props/parlays. Post-merge Test Suite on 1a741d5 was cancelled (superseded by later pushes), so no Deploy summary exists for it; t4-mlb decision: none recorded, this change touches no deployed code.

Resume: read `results_W89.md`, then ACTIVE_QUEUE row 89.4.
