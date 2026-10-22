# NHL engine — event-level data layer (W83.3)

The bar (ADR-0073, operator, verbatim): "the level of granularity is simply absurd - there's a clear bar that we aren't even remotely close to getting to."
This is the NHL data layer only: no model, no shadow arm, no registry cell. Free, unauthenticated NHL web API GETs (`api-web.nhle.com`, `api.nhle.com/stats`). No paid source.

## Build
- `src/prediction_market_bot/c1_signal_ingestion/nhl_event_store.py` — schedule walk, rate-limited resumable fetch (raw `.json.gz` cache per game and kind: pbp, box, shifts), `compile` to parquet per season: `games, events, shifts, box_players, rosters`, plus `recon.json`.
- Window: seasons 2015-16 .. 2026-27 (in progress). Store root `exp_output/NHL_EVENTS/` (git-ignored; rebuildable). Integrity record: `event_store_manifest.json` carries per-file sha256 (no separate sidecar).
- Fixed in-block: `write_cache` used one fixed `.tmp` name per file, so two concurrent fetchers collided (crash, plus spurious failures). Now unique per pid and thread; regression test added. Exact repeated shift rows from the source are dropped at compile.

## Point-in-time contract (`nhl_point_in_time.py`)
`PointInTime(as_of)` returns only games whose start plus a buffer (4h regular season, 9h playoffs) precedes `as_of`; anything later raises `LeakError`. Same shape as the NFL and NBA contracts.

## Checks (`nhl_store_checks.py`, fail-closed; 12 seasons, 0 failures)
Coverage floors, duplicates, null keys, goal and shots-on-goal reconciliation of play-by-play against box scores, detail shares. Floors were set from the first full measurement: shifts 0.95 (0.85 for the in-progress season); SOG reconcile 0.97 (2016 reads 0.979, 2025 reads 0.977); goals 0.995 (all seasons pass).

| Season | Games | Complete pbp+box | Shift charts missing | Shift key conflicts | Events |
|---|---|---|---|---|---|
| 2015 | 1321 | all | 0 | 0 | 413,912 |
| 2016 | 1317 | all | 0 | 0 | 413,339 |
| 2017 | 1355 | all | 0 | 0 | 434,744 |
| 2018 | 1358 | all | 0 | 0 | 433,203 |
| 2019 | 1212 | all | 0 | 0 | 382,738 |
| 2020 | 952 | all | 0 | 79 | 287,926 |
| 2021 | 1401 | all | 0 | 707 | 436,795 |
| 2022 | 1400 | all | 0 | 3 | 440,786 |
| 2023 | 1400 | all | 0 | 0 | 445,452 |
| 2024 | 1398 | all | 57 (source returns an empty chart) | 23 | 451,857 |
| 2025 | 1394 | all | 0 | 32 | 443,569 |
| 2026 | 151 finished of 1344 | all finished | 18 | 0 | 48,832 |

Detail fields: x/y, shooter, strength state on 100% of shots; shot type on ~72% (2024). Shift key conflicts are same-key rows with different times in the source; counted, not resolved.

## GAPs (GG-1010..GG-1014, none bought)
Pre-game starting goalie; travel; officials, coaches and scratches (free `gamecenter/<id>/right-rail`, not yet in the store — named follow-on, GG-1012/T-1061); injuries; qualitative/PAM. See `FACTOR_TAXONOMY.md`.

## D4 line - NHL
D4 NHL: none -> **data layer** (event-level store, no-look-ahead contract, fail-closed checks, manifest). Factor classes NHL-1..7 aggregated; interpreted 0; applied 0. Engine and engine_test remain "none".
