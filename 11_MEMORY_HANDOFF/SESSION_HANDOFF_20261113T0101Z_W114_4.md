<!-- session-meta
task_id: B-086
tier: STANDARD
timestamp: 2026-11-13T01:01:00Z
commit: d9db05a
one_line_summary: W114.4: team-pool latents added to the NBA joint (default off); held-out teammate PTS x PTS gap not closed (+0.0230 -> +0.0224); fitted values not shipped (#501).
gg_touched: none
adr_touched: none
plan_deliverable_moved: no
vision_pillar: DEPTH
gap_measure: D4 NBA (teammate joint error by pair class)
gap_delta: D4 NBA unchanged; teammate PTS x PTS +0.0230 -> +0.0224 (CI overlaps), PTS x AST teammates +0.0108 -> +0.0078 (still >0)
pattern_sweep: n/a (no defect fixed)
surface_delta: none (no cron, service or registry cell)
directive_conflicts: none known
-->

# SESSION HANDOFF — W114.4 (B-086) — NBA joint teammate legs

Status: PARTIAL · Ticket B-086 · branch session/20261113T002228Z-w114-4-nba-team-pool @ d9db05a (squash-merged) · PR #501 merged on green CI (test job, run 43340910819)
Common rules read first: `# Wave 114 common rules`.

## Result
Built: `nba_engine/joint.py` gained a team-level rest-bucket shock (`s_pool`), shared minutes shock (`s_tmin`), assists loaded on teammates' makes (`gamma_ast`) and rebounds loaded on the opponent's misses (`gamma_reb`). All default 0, so pricing equals 113.3. Five known-answer tests (`tests/test_nba_joint.py`).
Measured (held-out 2025-26, 1,075 games, game-clustered 95% CI, `gap_ci.py`): the fitted pool did not close the teammate gap. Fitted values (`fit_joint_2024-25_w114.json`) are not shipped. Hypothesis closed (W114.4 team-pool latents, parked for R&D). Full tables: `12_EXPLORATORY/sgp_correlation/RESULT_W114_4.md`.

## MEASURE MOVED — teammate joint error (realised − engine covariance), 113.3 → 114.4 fitted
| Class | n | before | after |
|---|---|---|---|
| PTS x PTS teammates | 3,532 | +0.0230 [+0.0156,+0.0311] | +0.0224 [+0.0147,+0.0303] |
| PTS x AST teammates | 7,064 | +0.0108 [+0.0054,+0.0161] | +0.0078 [+0.0026,+0.0129] |
| REB x REB teammates | 3,532 | +0.0008 | −0.0008 [−0.0078,+0.0062] (already ~0) |
Game-level Brier ML / spread / total 0.21544 / 0.24966 / 0.25012, unchanged (not worse). 3-leg combos re-priced slightly worse with fitted values, so nothing changes in the pot-of-gold branch's input; 113.3's numbers stay the reference.
D4 NBA: unchanged.

## Stage per factor
Usage pool: aggregated and interpreted; applied = NO (no held-out gain). Next registered hypothesis: lineup-level (on/off) or game-script latent for the sign of teammate covariance.

## Caveats
Loss fits covariance gaps; top-3 players per team; lines at draw median; DNP legs dropped.

## Operator decisions
None.
