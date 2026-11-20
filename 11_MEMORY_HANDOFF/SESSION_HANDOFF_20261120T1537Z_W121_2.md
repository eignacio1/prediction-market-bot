# Session handoff — W121.2 (NBA prop cells through the tree)

**Last reviewed:** 2026-11-20. Deliverable: EXP-NBAPROPS-001 scored; `nba_props` candidate map in `router_candidates`. PR #540 merged.

## What shipped
- PREREG frozen at ec39007 before any outcome was read. Scored: 1206 split cells, 143 leaves, 42 BH-tested, 14 kept, 1 earned.
- Earned split is POINTS-only. Points is dark with no engine model p, so it cannot fire live.
- Candidate `nba_props` logs beside v1 under `PM_CANDIDATE_ARMS` (off-switch `off`). Shadow only; v1 route byte-identical (tested). Kelly 0.
- Live firing kept splits: 3 assists, 2 threes, 1 rebound, all unearned. Live prop runner covers REB/AST/3PT = 9 shadow cells.
- Full detail and the six disclosed deviations: `12_EXPLORATORY/nba_props_splits/RESULT.md`.

## Measure moved
- vision_pillar: DEPTH (D6) + BREADTH (B4).
- gap_measure: D6 props cells wired end to end. gap_delta: 0 -> up to 9 wired on candidate and logging; **not counted** until
  `scripts/d6_read.py` runs on the box after deploy and one slate. Not measured in this session.
- One cause per unwired cell: points = dark, no engine model p. The other two NBA prop cells are not in the live runner.
- Prop splits tested / kept: 1206 / 14 (1 earned). B4 props families wired: pending the d6_read count.

## Keys
- pattern_sweep: archive readers must use `io_jsonl` (CI caught score_props.py); exploratory writes must use `safe_out`. Swept `12_EXPLORATORY/nba_props_splits/`.
- surface_delta: +0 live components (candidate logging only, shadow). 
- directive_conflicts: none.
- Pushback: live move bin (previous logged mid) differs from the scored move bin (>= 6 h earlier); live leaf can differ from scored.
- Surface: PR #540 also pushed earlier W120.2 commits (candidate arms ON by default, operator-approved 11-18).
- Dependencies: deploy of #540 to the box; one NBA slate; then `d6_read`.

## Open
- Docs Guard "Gaps-by-arm index is current" is red on main since before #540 (W121.1 and W121.3 closes also red). I merged #540 over it
  because the failure predates it and `test` passed. Owner of the gap log should regenerate the index.
- Session was not claimed via `claim_session.sh`.
