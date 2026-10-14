# NFL engine — factor taxonomy and free-source map (W73.2 Part A)

**Date:** 2026-10-14 · **Doctrine:** ADR-0073 stage 1 · **Pillar/measure:** DEPTH D4 (NFL none -> data layer), D1 · **Decisions logged:** true
**Rules:** public pages only (syndicate32.com landing page read 2026-10-14; no login, no paywalled content). Its factor *list* is a target to rebuild from free data, never its numbers. No paid service; a factor only a paid source supplies is a registered GAP.

Every field name below was read from the real nflverse release files on 2026-10-14 (release tags in `nflverse/nflverse-data`), not recalled. Fill rates are measured on the named season.

## Premise corrections (the block prompt was imprecise on these)
- **Man/zone coverage and pressure are in `pbp_participation`, not FTN.** FTN charting (2022+) carries blitzers, pass rushers, play action, motion, RPO, screen, QB out of pocket, throw-away, drops, contested/catchable ball, created reception, hash, backfield and box counts. Coverage lives in `pbp_participation.defense_man_zone_type` / `defense_coverage_type` / `was_pressure` / `time_to_throw` / `route` / `offense_formation` / `offense_personnel` / `defense_personnel` / `number_of_pass_rushers`.
- **`pbp_participation` has NO 2026 file** (tag lists 2016-2025 plus `_old_2023`). Current-season coverage/pressure/personnel features cannot be built from it. -> GAP-1.
- `games.parquet` (schedules tag) is a rolling file: spread/total/moneyline, rest, roof/surface/temp/wind, referee, head coaches and starting QBs are all in it, and it is **overwritten** (updated 2026-10-14T23:36Z), so it needs a snapshot per build to be point-in-time.

## Syndicate32 public factor classes -> free source

| # | Factor class (S32 public page) | Free source and fields | First season | Available relative to kickoff | Status |
|---|---|---|---|---|---|
| F1 | Opponent-adjusted team profile (OASIS: scoring efficiency, unit context) | `pbp`: `epa`, `wp`, `success`-style flags, `posteam`/`defteam`, `down`, `ydstogo`, `score_differential`, `qtr`; adjusted by us from opponent splits | 1999 | After each game (use games strictly before G) | OK |
| F2 | Passing unit | `pbp`: `qb_dropback`, `air_yards`, `cpoe`, `cp`, `pass_location`, `pass_length`, `sack`, `qb_hit`; `pfr_advstats` week pass/def: `times_pressured`, `times_hurried`, `times_blitzed`, `passing_bad_throws`, `passing_drops` | pbp 1999; pfr_advstats 2018 | After each game | OK |
| F3 | Rushing unit | `pbp`: `rush_attempt`, `run_gap`, `run_location`, `epa`, `yards_gained`, `rusher_player_id`, `tackled_for_loss`; `ftn`: `n_defense_box`, `is_qb_sneak`; participation `defenders_in_box` | pbp 1999; box 2016/2022 | After each game | OK |
| F4 | Protection / pressure | `participation`: `was_pressure`, `time_to_throw`, `number_of_pass_rushers`; `ftn`: `n_blitzers`, `n_pass_rushers`, `is_qb_fault_sack`; `pbp`: `qb_hit`, `sack_player_id`; `pfr_advstats`: `times_pressured_pct` | participation 2016; ftn 2022 | After each game | OK; 2026 participation GAP-1 |
| F5 | Coverage (man / zone / specific) and QB efficiency per dropback against each | `participation`: `defense_man_zone_type`, `defense_coverage_type`, `route`, `defense_personnel`, joined to `pbp` on (`nflverse_game_id`,`play_id`) for `epa`/`cpoe`/`qb_dropback` | man/zone fill 0.39 of plays in 2020 (pass plays), 1.00 in 2023 and 2025; **0.00 in 2016** (2017-19 unmeasured; Part B manifest measures every season) | After each game | OK 2020+; GAP-1 for 2026 |
| F6 | Personnel and formation (offense/defense) | `participation`: `offense_formation`, `offense_personnel`, `defense_personnel`, `offense_players`, `defense_players` (fill 0.72-1.00 by season); `ftn`: `n_offense_backfield`, `is_motion`, `is_no_huddle`, `starting_hash` | 2016 | After each game | OK; 2026 GAP-1 (ftn 2026 exists) |
| F7 | Special teams | `pbp`: `kickoff_attempt`, `punt_attempt`, `field_goal_attempt`, `kick_distance`, `field_goal_result`, `return_yards`, `punt_blocked`, `kicker_player_id`, `punter_player_id`, `special_teams_play`, `st_play_type`; snap counts `st_snaps` | 1999 | After each game | OK |
| F8 | Injuries / availability | `injuries`: `report_status`, `practice_status`, `report_primary_injury`, `position`, `gsis_id`, by (season, week, team); `depth_charts`: `dt`, `pos_abb`, `pos_slot`, `pos_rank`; `snap_counts`: `offense_pct`, `defense_pct` (who actually plays); `weekly_rosters` | injuries 2009; depth_charts 2001; snaps 2012 | Injury report: Wed-Fri before kickoff (no timestamp in file -> GAP-3); depth chart: has `dt`; snaps: after game | OK with PIT caveat |
| F9 | Play callers / coaching | `games`: `home_coach`, `away_coach` (head coach only) | 1999 | Known pre-game | PARTIAL: offensive/defensive coordinator and actual play caller are NOT in any free nflverse table -> GAP-2 |
| F10 | Penalties | `pbp`: `penalty`, `penalty_type`, `penalty_team`, `penalty_yards`; crew via `officials` | 1999; crew 2015+ (measured in Part B) | After each game; crew assignment pre-game | OK (derived: team and crew penalty rates) |
| F11 | Rest | `games`: `home_rest`, `away_rest` (fill 1.00); also derivable from `gameday` | 1999 | Pre-game (schedule) | OK |
| F12 | Home field / venue | `games`: `location`, `stadium_id`, `roof`, `surface`, `div_game`; fill 1.00 | 1999 | Pre-game | OK |
| F13 | Fair values vs market (spread, ML, total) | `games`: `spread_line`, `total_line`, `home_moneyline`, `away_moneyline`, odds columns (historical closing); Kalshi/archived mids from our own `exp_output/PRICE_ARCHIVE` | 1999 (lines) | Closing line lives in games.parquet: it is a **post-hoc** value, not an as-of-kickoff snapshot -> reported, never a feature (GAP-4) | OK as comparison only |
| F14 | Live game state | `pbp`: `game_seconds_remaining`, `score_differential`, `yardline_100`, `down`, `ydstogo`, `posteam_timeouts_remaining`, `wp`, `vegas_wp` | 1999 | Within game | Out of scope stage 1 (pre-game first, ADR-0068) |
| F15 | Historical backtests with game-condition filters | Derived from the store itself: any column above as a filter | — | — | Falls out of the store; no extra source |

## Factors the granularity bar names that S32's public page does not show

| # | Factor | Free source and fields | First season | Available | Status |
|---|---|---|---|---|---|
| G1 | Weather | `games`: `temp`, `wind`, `roof` (temp/wind fill 0.74 in 2018, 0.38 in 2022, 0.67 in 2025 - roofed games are null); `pbp.weather` string (e.g. "Sunny Temp: 83° F, Humidity: 72%, Wind: NE 9 mph"); humidity/precip only in the string | 1999 (temp/wind) | Stored values are observed/at-game, **not** pre-kickoff forecasts -> leakage risk, GAP-5 | PARTIAL |
| G2 | Officials / referee crew | `officials`: `official_name`, `position`, `official_id` per game; `games.referee` | 2015-ish (measured in Part B) | Crew is assigned days before; file has no assignment timestamp | OK, PIT caveat (GAP-3 class) |
| G3 | Travel / time zone / short week | derived from `games.gametime`, `gameday`, `location`, stadium_id + a team home table | 1999 | Pre-game | OK (derived) |
| G4 | QB identity and QB change | `games`: `home_qb_id`, `away_qb_id` (fill 1.00 history; **0.34 in 2026** for unplayed games) -> use depth chart / injuries pre-game | 1999 | Starter known late | PARTIAL |
| G5 | Qualitative (PRF-style: form, role-fit, motivation, rumors) | None free and structured | — | — | Out of this layer; existing PRF framework handles later |

## Gaps (to be registered as GG-730..GG-734 at Part A push; none to be bought)
- **GAP-1 / GG-730:** `pbp_participation` has no 2026 file -> coverage, pressure, personnel for the current season unavailable from it. Mitigation: FTN 2026 (blitzers/rushers/motion) and pbp-derived features until nflverse publishes it. Check the release each build.
- **GAP-2 / GG-731:** no free table of offensive/defensive coordinators or the actual play caller. Head coach only.
- **GAP-3 / GG-732:** `injuries` and `officials` carry no publication timestamp (injuries are keyed by week only). Rule adopted: a row is usable for game G only if `week` < G's week, OR it is week-of and G kicks off on Sunday or later (Thursday games excluded for week-of injuries). Conservative; tested.
- **GAP-4 / GG-733:** `games` lines are final/closing values in a rolling, overwritten file, not as-of-kickoff snapshots. Usable as a market comparison; never as a model input. Snapshot the file per build from now so 2026 lines become point-in-time going forward.
- **GAP-5 / GG-734:** no free historical weather *forecast* archive confirmed. Stored temp/wind are at-game values. Treated as a labelled leakage-risk feature (`weather_is_observed=true`) until a forecast source is verified.

## Coverage summary
15 Syndicate32 public factor classes + 5 granularity-bar additions = 20 classes. Buildable from free data today: 15 fully or with a labelled caveat; PARTIAL: F9, G1, G4; out of stage 1: F14 (live), G5 (qualitative). D1 classes buildable (matchup, personnel/availability, team, venue, weather, qualitative): 5 of 6 have a free source; qualitative has none structured.
