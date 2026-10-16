# NBA engine — event-level data layer (W78.4 Part B)

**Date:** 2026-10-16 · **Doctrine:** ADR-0073 stage 1 · **Pillar/measure:** DEPTH D4 (NBA) · **Decisions logged:** false (DECISION_LOG row deferred to session-end)
**Status:** Part B built and verified. **Part A (`FACTOR_TAXONOMY.md`) NOT written** - session limit; carried forward.

## Build
`python3 -m prediction_market_bot.c1_signal_ingestion.nba_event_store` (free sportsdataverse GitHub releases; no login).
Manifest: `event_store_manifest.json` (build_as_of 2026-10-16T06:01:34Z, 123 files, 0 failures; per-file rows, sha256, ETag, Last-Modified, key nulls).
Raw store `exp_output/NBA_EVENTS/` is git-ignored (~239 MB). Seasons 2016-2026 (label = ending year) for pbp, possessions, lineups, shots, team/player box, game rosters, officials, coaches, nba_stats schedule, ESPN schedule; ESPN 2027 schedule (1,206 games, first tip 2026-10-20T19:00Z); ESPN injury snapshots.
stats.nba.com is unreachable from here: reported as BLOCKED, not scraped around.

## Point-in-time contract (`nba_point_in_time.py`)
A game G' is usable for G iff `tip_latest(G') + 4h <= tip_earliest(G)`. Real tip instant from the ESPN schedule where (ET date, home, away) joins uniquely (92-99% of games per season); otherwise the Eastern calendar day bounds, flagged `tip_imputed`. Season-static tables are refused. Date-only snapshot stamps count from the end of that day. Tests: 14 synthetic (incl. positive control that naive filters leak and are caught, property test) + 4 real-store.

## Checks (`nba_store_checks.py`, fail-closed)
Rows, key nulls (0 in all files), duplicate-key ceilings, season column, per-source minimum rows, cross-source coverage. Real store: 123 files, 44 coverage checks, 0 failures.
Findings: lineups `action_number` repeats (~5.2%); shots ties 0.08% max; preseason/all-star games (~5.5%) have no box/officials and imputed tips; game_rosters thinner 2016-17; officials 2026 coverage 99.77%; injuries are daily snapshots only from 2026-09-08 (no free history).

## GAPs (to register in the claimed GG-895..899; none bought)
Historical injury reports; official-crew assignment timestamps; coach tenure dates; travel/venue geometry; PAM-derived factors; structured qualitative.

## D4 line - NBA
Before: none. After: event-level data layer with a point-in-time contract, 2015-16..2025-26 + 2026-27 schedule, checked. Stage: **aggregated** (no factor yet interpreted/applied by an engine). Weekly rebuild: propose next wave (no running component added; surface_delta 0).
