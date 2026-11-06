# MLB engine data layer — design (W105.3, B-018)

**Purpose / measure:** DEPTH · D4 MLB (event-level data layer 0 → started; ADR-0073: MLB's finest grain is the pitch). Free sources only ($0). Built off the box; nothing installed or scheduled on the box.

## 1. Source inventory (each tested with one request)

| Source | Grain | Access | Licence / terms | Rate limit | Size | Verdict |
|---|---|---|---|---|---|---|
| **Baseball Savant / Statcast search CSV** (`baseballsavant.mlb.com/statcast_search/csv`) | every pitch, ~90 columns (type, velocity, spin, location, zone, outcome, launch speed/angle, wOBA value/denominator, score state) | plain HTTPS GET, no key | MLB Advanced Media public data; free for non-commercial research, attribution expected. Re-check terms before any commercial redistribution. | none published; 25,000-row cap per query, so we fetch one request per game date and flag capped days; we pause 1 s between requests | ~2.9 MB gzip/day raw, ~720k pitches/season | **PRIMARY.** Works. |
| **MLB Stats API** (`statsapi.mlb.com/api/v1/...`) | schedule, boxscore, play-by-play, rosters | plain HTTPS GET | MLB data, same terms family | none published | KB per call | **Cross-check only** (box scores for pitch-count / score validation). |
| **Retrosheet** | play-by-play event files, game logs (no pitch locations/velocity) | bulk download | free with attribution notice | n/a | ~MB per season | Fallback for history before Statcast (2015) and for game logs; not needed this wave. |
| **Chadwick Bureau register** (`people-*.csv`, GitHub) | player id crosswalk (MLBAM, Retrosheet, FanGraphs, BBRef) | static CSV, 16 shards | ODC-By | n/a | ~25 MB | **Id resolution.** Cached to parquet. |

**Stats API 406 on the VPS — does it matter?** No for this design. The store is built off-box (the Mac), where the Stats API answers normally; the box never calls the raw sources. The box reads only compact derived tables (section 6). If a later wave moves ingest onto the box, the 406 (a header/User-Agent rejection, observed on the box only; the schedule endpoint answered 200 from there) must be diagnosed first, but it is not on this design's path.

## 2. Schema

Stored under `<store>/tables/` as parquet (gitignored; raw CSVs under `<store>/raw/<year>/<date>.csv.gz`).

- **pitches** — one row per pitch; key `(game_pk, at_bat_number, pitch_number)`; ~42 kept columns (ids, teams, inning/outs/count/baserunners, pitch type, velocity/spin/extension, movement, plate location, zone, description, events, launch speed/angle, woba_value/denom, run expectancy delta, running score) plus derived flags `is_swing`, `is_whiff`, `is_fastball`, `out_of_zone` (zone ≥ 11), `in_zone` (1–9).
- **pa** — one row per plate appearance: the last pitch of an at-bat that carries an `events` value.
- **games** — one row per `game_pk`: date, teams, final score (from the last pitch's post-score), pitch count, home/away starter (the pitcher in inning 1).
- **lineups** — first nine distinct batters per side with batting slot.
- **Player ids** are MLBAM ids (`pitcher`, `batter`); the Chadwick register maps them to other systems.

**Dropped at ingest (leaky):** `pitcher_days_until_next_game`, `batter_days_until_next_game` — they encode the *future* schedule.

## 3. Point-in-time rule

A feature row keyed `(player, as_of_date)` is computed from pitches with `game_date` **strictly before** `as_of_date`. Implementation: per-player-per-date sums, exclusive cumulative sum (shifted by one date). Consequences: doubleheader games never feed each other; a player's first appearance has empty history (NaN rates, zero counts). Tests: truncation invariance (features built from data cut at date D equal the full build restricted to ≤ D), perturbation (rewriting all future pitches changes no earlier row), and a doubleheader case.

**Known soft spot:** the Part C lineup is the first nine distinct batters of the game as played (known only after first pitch); a pre-lineup-card version needs the posted lineup. Noted in the result file.

## 4. Storage size per season (measured, W105.3)

Per regular season: ~712k pitches (2024: 195 game days, 2025: 197), ~2,430 games. Raw gzip CSV: **~0.95 MB per game day, 176 MB (2024) and 189 MB (2025)**; no day reached the 25,000-row cap. Cleaned parquet tables for BOTH seasons (pitches, PA, games, lineups, both PIT tables, id register): **61 MB total**. The PIT tables alone are 41.5k pitcher-date and 96.8k batter-date rows, a few MB. Fits a laptop; the raw pitch table does not belong in the box's 961 MB RAM, the PIT tables do.

## 5. Checks (implemented in `checks.py`)

Duplicate pitches on the key; pitch count per game vs Stats API box score `pitchesThrown` on a sample; final score vs box score runs; id resolution against the Chadwick register.

## 6. How the box would later read this

The box never touches the raw store. A weekly off-box job writes compact derived tables (PIT pitcher/batter tables as of the next slate date, ~KB–MB parquet/CSV) and ships only those; the box loads them with plain pandas. Nothing in this wave installs, schedules or syncs anything on the box (surface_delta: none).
