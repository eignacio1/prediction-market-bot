# NFL engine — data layer (W73.2 Part B, ADR-0073 stage 1)

**Decisions logged:** true (DECISION_LOG 2026-10-14, W73.2 Part A and Part B)
**Built:** 2026-10-15T00:12:25Z (manifest `build_as_of`). **Pillar:** DEPTH. **Measure:** D4 (NFL engine stage).
**D4 line for NFL:** `none -> event-level data layer built` (source: `event_store_manifest.json`, 165 files, 0 failures; `nfl_store_checks` 0 failures; 23 tests pass).
Nothing here touches an order, a stake, a ledger row or `kelly_fraction`. No paid source; no secret; no operator step.

## What is built

One reproducible build of the free nflverse-data releases, keyed and timestamped, with a point-in-time (PIT) contract.

| Piece | Where |
|---|---|
| Builder | `src/prediction_market_bot/c1_signal_ingestion/nfl_event_store.py` (`python -m ...nfl_event_store`) |
| PIT contract | `.../nfl_point_in_time.py` (`PointInTime.view`, `.assert_no_leak`, `.pregame_context`) |
| Row/null/key/cross-source checks | `.../nfl_store_checks.py` (`python -m ...nfl_store_checks --report`) |
| Tests | `tests/test_nfl_point_in_time.py` (12 synthetic + 1 real-store), `tests/test_nfl_store_checks.py` (10) |
| Scheduled rebuild | `.github/workflows/nfl_event_store.yml` — Tuesdays 09:43 UTC and `workflow_dispatch`; public repo, free minutes |
| Raw data | `exp_output/NFL_EVENTS/raw/<source>/…parquet`, **git-ignored** (about 550 MB) |
| Committed artefact | `02_ARCHITECTURE_DESIGN/NFL_ENGINE/event_store_manifest.json` |

**Keys.** Play-level sources: `(game_id, play_id)`. Player-game sources (snaps, PFR): `(game_id, team, pfr_player_id)`. Player-week sources: `(season, week, team, player)` — injuries and rosters; depth charts use `(season, snapshot, team, player_id, depth_slot)` because the 2025+ schema is timestamped, not weekly. Every row carries `_source` and `_as_of` (UTC time the file was retrieved). Source columns are never dropped or rewritten; canonical columns are added beside them.

**Manifest.** Per file: rows, source column count, `source_sha256` of the downloaded bytes, bytes, `Last-Modified`, `ETag`, key null counts, `as_of`. A change in upstream bytes shows as a changed hash in a committed diff. The manifest is written only by a full build; a partial build (`--only`, `--min-season`) never overwrites it. A past-season file missing from a declared range is a build failure (a silent hole is worse than a red build); the in-progress season may be absent before kickoff.

## Coverage

| Source | Seasons | Files | Rows | Notes |
|---|---|---|---|---|
| `pbp` (plays) | 1999–2026 | 28 | 1,293,470 | 2026 to date (week 6) |
| `participation` | 2016–2025 | 10 | 478,989 | **no 2026 file** (GG-730); man/zone coverage type 0% filled 2016–17, ~38% 2018–22, ~100% 2023+; formation 72% |
| `ftn` (charting) | 2022–2026 | 5 | 198,653 | 2026 present |
| `snaps` | 2012–2026 | 15 | 331,982 | **2012 file is empty (0 rows)**, published that way upstream |
| `injuries` | 2009–2026 | 18 | 92,180 | 2015–2024 carry `date_modified`; 2025–26 do not (GG-732) |
| `depth_charts` | 2001–2026 | 26 | 2,073,471 | 2001–2024 weekly schema; 2025+ timestamped (`dt`, 221 snapshots in 2025–26) |
| `rosters` (weekly) | 2002–2026 | 25 | 921,692 | |
| `pfr_pass` / `pfr_rush` / `pfr_rec` / `pfr_def` | 2018–2026 | 9 each | 5,606 / 19,085 / 36,986 / 64,563 | player-game advanced stats |
| `officials` | 2015–2026 | 1 snapshot | 22,012 | 3,045 games; rolling file |
| `schedules` | 1999–2026 | 1 snapshot | 7,548 games | rolling file; closing lines (GG-733) |

Cross-source coverage (all measured, all checked on every build): every `pbp` game exists in the schedule (100% in all 28 seasons); `ftn` plays are 100% found in `pbp`; `participation` plays are 98.3–98.6% found in `pbp` for 2016–2022 and 100% for 2023–2025 (floor in checks: 97%).

## Point-in-time contract

*Query "as of kickoff of game G" can never return a row from G or from a game that kicks off later, nor a row that could not have been public at kickoff.*

- **Kickoff** = `gameday` + `gametime` (US Eastern → UTC, DST-aware). 259 games (all 1999) have no `gametime`; they are imputed to 00:00 ET on gameday (earliest possible, the conservative direction) and flagged `kickoff_imputed`. A game with no resolvable kickoff makes the contract refuse to load.
- **`post_game` rows** (plays, participation, charting, snaps, PFR, officials) are usable for G only if the source game's kickoff + **4 h** is ≤ G's kickoff. The 4 h buffer is longer than any real game, so a 1 pm game is never "known" at a 4:25 pm kickoff.
- **`weekly` rows** (injuries, rosters; no publication time): usable if the row's (season, week) is earlier than G's, or the same week and G kicks off Sunday or Monday. Thursday, Friday and Saturday games exclude week-of rows. Unknown week is never usable.
- **`dated` rows** (2025+ depth charts): usable iff `dt` < G's kickoff (strict). Weekly-schema files fall back to the weekly rule.
- **G's own schedule row** reaches a model only via `pregame_context`, a whitelist: teams, date/time, venue, roof, surface, rest days, divisional flag, head coaches, and `referee` only for Sunday/Monday games. It excludes scores, closing lines (GG-733), observed temp/wind (GG-734) and starting QB ids.
- **Tests.** Synthetic: ET→UTC with DST, imputed gametime, the 4 h buffer (the 1 pm game excluded for the 4:25 pm kickoff), first game of the data sees nothing, a property test over every game (no game sees itself or a later kickoff), weekly Thursday vs Sunday, Saturday playoff, dated strictness at exactly kickoff, whitelist. **Positive control:** the leaky filters a careless query would write ("same week or earlier", "everything but G") are shown to leak on the same fixture and `assert_no_leak` is shown to catch them, so a passing test cannot be a test that detects nothing. Real store: 18 sampled completed games (3 each from 2012, 2016, 2020, 2022, 2024, 2025) are queried against all seven historical sources, with a real-frame positive control (the full-season pbp frame is flagged).

## Checks (per source per season, every build)

Rows > 0; key columns present; key nulls ≤ ceiling; duplicate keys ≤ ceiling; `season` column equals the file's season; completed-season rows ≥ per-source minimum; cross-source coverage floors. Thresholds were set from measurement and live as named constants with a reason beside each in `nfl_store_checks.py`. Documented tolerances (everything else is zero):

| Source | Tolerance | Measured |
|---|---|---|
| `snaps` 2012 | 0 rows allowed | upstream file is empty |
| `rosters` | key null ≤ 0.1%; dup ≤ 7% | 0.07%; 5.9% (2002–2015 list a player twice in a week) |
| `depth_charts` | key null ≤ 5%; dup ≤ 5% | 3.9% (2025+ unsigned players have no `gsis_id`); 4.5% (weekly schema repeats) |
| `injuries` | dup ≤ 0.05% | 0.03% (two duplicated lines, 2024) |

## Gaps (all registered; none bought)

| GG | Gap | State after Part B |
|---|---|---|
| GG-730 | no 2026 `pbp_participation` | confirmed (2026 file 404 on 2026-10-15); 2026 is inside the declared range and tolerated as absent only because it is the in-progress season, so the weekly build picks the file up the week nflverse publishes it, with no edit |
| GG-731 | no coordinator / play-caller table | unchanged; head coach only |
| GG-732 | no publication time for injuries / officials | narrowed: injuries 2015–2024 carry `date_modified` (full fill) — stored, not used; the contract stays on the conservative weekly rule until its meaning is verified; 2025–26 and officials have none |
| GG-733 | `games.parquet` lines are overwritten closing values | mitigated going forward: every build uploads its schedule snapshot to the rolling release `nfl-games-snapshots`; history before 2026-10-15 is not recoverable |
| GG-734 | no free weather forecast archive | unchanged; observed temp/wind excluded from `pregame_context` |

## What this does not do

It is a data layer, not a model. No feature is built from it, no forecast is written, no cell is registered (those are stage 2 and later of ADR-0073). Depth charts of the weekly era give the depth chart but not the *inactive list on game day* (the injury report is the nearest free proxy). The first real use of the PIT contract is the stage-2 feature builder, which must go through `PointInTime.view` rather than filtering by hand.

## Operator decisions

- None required.
