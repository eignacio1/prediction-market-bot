<!-- session-meta
task_id: T-960
tier: STANDARD
timestamp: 2026-10-15T00:00:00Z
commit: 50ea8f9
one_line_summary: W73.2 Part A done and merged (NFL factor taxonomy, 20 classes, 15 buildable free); Part B (event store, PIT contract, DATA_LAYER.md) not started, exceeds the 90-min ceiling.
gg_touched: GG-730, GG-731, GG-732, GG-733, GG-734
adr_touched: none
plan_deliverable_moved: no
vision_pillar: DEPTH
gap_measure: D1
gap_delta: D1 NFL factor classes mapped to free sources: none -> 20 classes, 15 buildable today, 5 GAPs (GG-730..734). D4 NFL stays "none": no event store built yet. Source: 02_ARCHITECTURE_DESIGN/NFL_ENGINE/FACTOR_TAXONOMY.md, 2026-10-14.
-->

# SESSION HANDOFF W73.2 (2026-10-15)

Status: PARTIAL | branch session/20261014T234416Z-w73-2-nfl-data-layer @ 50ea8f9 (merge of PR #254) | PR #254 merged, no CI checks were configured on it (docs-only) | Part A done, Part B not started.

Result: FACTOR_TAXONOMY.md maps 20 factor classes to nflverse files and fields, with first season and point-in-time availability. 15 are buildable from free data now. 5 are GAPs, registered as GG-730..734 and none bought. The prompt's premise that coverage and pressure come from FTN is false: they come from `pbp_participation` (man/zone and pressure fill 1.00 in 2023+, 0.39 in 2020). Corrected in the doc.
Deploy: PR #254 was docs-only and triggered no Deploy run, so the VPS and t4-mlb were not touched. Restart decision: none needed.
MEASURE MOVED: D1 (NFL) none -> 20 classes mapped, 15 buildable (FACTOR_TAXONOMY.md, 2026-10-14). D4 NFL unchanged at none.
Why Part B was not started: it needs the build script, a manifest, a workflow, the PIT module with tests and DATA_LAYER.md. That is about 50 min on top of the time Part A used, past the 90-min hard ceiling.
Part B design inputs, already verified against the live files:
- Keys: pbp `(game_id, play_id)`; participation `(nflverse_game_id, play_id)`; FTN `(nflverse_game_id, nflverse_play_id)`; snaps `(game_id, team, pfr_player_id)`; injuries `(season, week, team, gsis_id)`. None has duplicates in 2025.
- Participation has no 2026 file (GG-730), so the store must tolerate its absence.
- `games.parquet` is rolling and overwritten, so snapshot it per build with an as_of (GG-733).
- Injuries and officials have no timestamp. Use the conservative week rule from GAP-3 (GG-732).
- Post-game sources are usable only for games strictly before G. Depth charts carry `dt`.
- Download pattern: https://github.com/nflverse/nflverse-data/releases/download/<tag>/<file>.parquet. `nfl_data_py` is not needed.
- The Actions pattern to copy is `.github/workflows/mlb_features_sync.yml`.
Next undone: Part B in a fresh block.
Operator decisions: none.
