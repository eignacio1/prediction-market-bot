# Session handoff W58.2
Status: PARTIAL | main @ b14ea3d (PRs #174, #176) | CI green, Deploy success | NBA shadow arm built, deployed, cron armed; no rows until regular season (~10-18/19), cells still NOT_IMPLEMENTED.

Next: ~10-19 confirm first T1 rows in `exp_output/PREGAME_SHADOW/NBA_NBA_*_T1.jsonl`, then PR flipping cells via `promote_cell_status(..., SHADOW, superseding_reference="EXP-038")`.

Operator decisions: (1) extend ADR-0070 to NBA/NHL; (2) preseason carve-out (skipped, not logged) — keep or log; (3) add NBA to `web_dashboard._season_state`.
Possible defect to register (GG-495..497 reserved, unverified): `_shadow` settled count reads `outcome` vs `y`.
