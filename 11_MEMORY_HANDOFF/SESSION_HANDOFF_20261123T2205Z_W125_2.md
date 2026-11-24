# Handoff W125.2 (parked, operator asleep) - 2026-11-23 22:05 PT

**Status:** PARTIAL. Parts 0 and B done and merged. Part A reader merged, result not read yet. Part C not started.

## Done (merged to main)
- PR #556 (124.4 dense capture) merged. Install NOT run.
- PR #559: `scripts/router_error_read.py` (read-only ERROR/UNROUTED breakdown by cause, cell, sport, day; box task `router_error_read`) + healthcheck 11 counts both `shadow_order` and `arm_order` (GG-2006 part B), tests both directions.

## Open
- **Part A (GG-2007):** box result for `router_error_read` not landed yet (first run hit the box before #559 deployed; retry request pushed). Next window: read the newest `04_EXECUTION/BOX_TASKS/results/*router_error_read.md`, fix each cause with a regression test or register it. Trace shows 0 ERROR rows in last 3 days for NFL/NHL sample games, so likely historical.
- **Part C (B-104):** run read of Fable's branch `session/20261117T010353Z-w115-3-d6-one-game` (1ce79c5) not done. Trace findings: NFL layer 7 missing = W117.1 A3 NO_BET routing (strategy, register as GG, do not change silently); NBA_MONEYLINE and NBA_PLAYER_POINTS have no model p; NFL_MONEYLINE T1-T3 and NHL_MONEYLINE|T1 have routed rows with arm 0; trace host printed arm_orders_mode "off" (verify for cron).
- D6 before: 17 (NBA 7, NFL 4, NHL 6, MLB 0). After: re-run `d6_read` post-deploy, not yet run.
- GG-2006 / GG-2007 status and ACTIVE_QUEUE row not yet updated.

## operator decisions
- Budget gate dry run for `archive_dense_install`: **REFUSE**. Projected 30-day disk 86.2% vs 80% limit (now 67.0%, +0.64 pct/day, 159 MB/day). Source: `04_EXECUTION/BOX_TASKS/results/20261124T0550Z_archive_dense_readback.md`. Options: shrink capture (fewer runs or shorter horizon) or raise the limit by superseding decision. Recommend: do not install at 86%. No approval line given.

## measure moved
D6: no change yet. E1: router ERROR rows per day, before/after pending Part A.
surface_delta: +1 box task (`router_error_read`, read-only; registry entry check pending). pattern_sweep: healthcheck order counting swept; other consumers of `shadow_order` only not yet grepped. directive_conflicts: none found.
