# NBA engine - factor taxonomy and free-source map (W79.3 Part A)

**Date:** 2026-10-16 - **Doctrine:** ADR-0073 stage 1, ADR-0075 stages - **Pillar/measure:** DEPTH D1 (NBA 0 -> 13 classes mapped), D4, D5(b) - **Decisions logged:** true
**Rules:** free sources only; nothing bought. Every field below was read from the real store files on 2026-10-16 (`exp_output/NBA_EVENTS/raw/<table>/`, manifest `event_store_manifest.json`, build_as_of 2026-10-16T06:01:34Z). Seasons are labelled by ending year; first season = label 2016 (2015-16) unless stated. Template: `NFL_ENGINE/FACTOR_TAXONOMY.md`.

**Point-in-time (PIT) availability** is the `nba_point_in_time.py` contract: a post-game row about game G' is usable for G iff `tip_latest(G') + 4h <= tip_earliest(G)`; schedule facts are public in advance; snapshots count from the end of their date; season-static tables are refused.
**Stage** is the ADR-0075 stage today: *aggregated* (the fact is in the store, point-in-time) / *interpreted* (we measured whether it is a trait and whether it moves a price-relevant target) / *applied* (a tested path from the fact to a price, against the market). No NBA factor is *applied* by the engine yet; the seat factors B1-B4 already feed the legacy 14-feature pregame model (not this store).

| # | Factor class | Free source and fields | First season | PIT availability | ADR-0075 stage today |
|---|---|---|---|---|---|
| N1 | Pace / possessions | `team_box`: `field_goals_attempted`, `free_throws_attempted`, `rebounds_offensive`, `turnovers`, `minutes`; `possessions`: `possession_number`, `count_as_possession`, `start/end_seconds_remaining` | 2016 | post_game: after each game + 4h | **interpreted** (FACTORS_FIRST_READ: trait r=0.80; moves totals) |
| N2 | Offensive / defensive efficiency | `team_box`: `points`, plus N1 inputs both sides; `possessions`: `points`, `offense_team_id`, `possession_start_type`, `is_second_chance` | 2016 | post_game | **interpreted** (trait r=0.75 / 0.71; recent-vs-season form adds to margin) |
| N3 | Rest / schedule density | `schedule`: `game_date`, teams; `espn_schedule`: `date` (tip instant), `game_date_time` | 2016 | schedule (public in advance) | **interpreted** (not a team trait; back-to-back moves margin) |
| N4 | Home court / venue | `espn_schedule`: `venue_id`, `venue_full_name`, `neutral_site`, `attendance`, `venue_indoor` | 2016 | schedule (attendance is post-game only) | aggregated |
| N5 | Travel distance / time zone | `espn_schedule`: `venue_address_city`, `venue_address_state` only - NO coordinates or time zone in any free table loaded | 2016 | schedule | **GAP-4** (not built) |
| N6 | Player box score / minutes distribution | `player_box`: `person_id`, `minutes`, `field_goals_*`, `three_pointers_*`, `rebounds_*`, `assists`, `position`, `comment` (DNP reason text); 39 columns | 2016 | post_game | aggregated (legacy NBA-T3/B7 points+minutes studies ran on other sources, not this store) |
| N7 | Lineup / five-man unit | `lineups`: `home_player_1..5`, `away_player_1..5` per `action_number` (+ occurrence, see DATA_LAYER); `possessions`: `off_player_1..5`, `def_player_*` | 2016 | post_game | aggregated |
| N8 | Shot profile (location, type, distance) | `shots`: `shot_distance`, `x_legacy`, `y_legacy`, `action_type`, `sub_type`, `shot_result`, `shot_value`, `person_id`; `pbp`: `location`, `shot_distance` | 2016 | post_game | aggregated |
| N9 | Roster / rotation continuity | `game_rosters`: `player_id`, `team_id`, `game_id` (thinner 2016-17, see DATA_LAYER); derivable from `player_box` minutes | 2016 | post_game; the *active list for G itself* is not public until ~90 min pre-tip (not in store) | aggregated |
| N10 | Injuries / availability | `injuries` (ESPN daily snapshot): `status`, `athlete_id`, `injury_date`, `detail_return_date`, `type_name`, `as_of_date` | **2026-09-08** snapshots only | snapshot (date-only stamp counts from end of day) | aggregated for 2026-27 only; history **GAP-1**. Legacy availability studies (NBA-T3) interpreted, not applied |
| N11 | Officials / crew | `officials`: `official_id`, `first_name`, `last_name`, `game_id` (crew of 3-4); 99.77% coverage 2026 | 2016 | post_game; assignment timestamp absent, crews are posted ~9am on game day | aggregated, **GAP-2** (no assignment time, so crew cannot be used pre-tip safely) |
| N12 | Coaches | `coaches`: `coach_id`, `coach_name`, `is_assistant`, `coach_type`, `season` (season-level, no dates) | 2016 | **refused** (`season_static`: no tenure dates, firings invisible) | aggregated but unusable as-of; **GAP-3** |
| N13 | PAM / qualitative (player attributes, matchup, scheme, intangible) | none in this store. PAM (DS-01, NBA v4 port at `PAM/`) is the planned source; structured qualitative has no free historical feed | - | not defined | **GAP-5** (not piped) |

## Registered gaps (GG numbers re-claimed as GG-910..GG-914; W78.4 had reserved GG-895..899 unregistered)
| Gap | GG | What is missing | Why not free-fixable today |
|---|---|---|---|
| GAP-1 | GG-910 | Historical injury reports before 2026-09-08 | ESPN injuries endpoint serves the current list only; daily snapshots start on our build date. A point-in-time history needs snapshots taken daily from now (Wave 80 weekly-rebuild entry covers it only weekly; daily is needed) |
| GAP-2 | GG-911 | Officials-assignment timestamps | `officials` lists the crew after the game; no free source stamps when it was posted |
| GAP-3 | GG-912 | Coaches with tenure dates (firings/interims mid-season) | `coaches` is season-level; PIT contract refuses it |
| GAP-4 | GG-913 | Travel / venue geometry (arena coordinates, time zones, miles between consecutive games) | no coordinates in any loaded table; a hand-built 30-arena table is a small free job but was out of the 90-minute ceiling |
| GAP-5 | GG-914 | PAM-derived and structured qualitative factors | PAM not piped into the NBA engine; qualitative has no feed |

Not purchased: nothing. stats.nba.com is unreachable from this environment (BLOCKED, not scraped around); every class above is from the sportsdataverse and ESPN free endpoints.

## Count
13 classes mapped (D1 NBA: 0 -> 13). By ADR-0075 stage: interpreted 3 (N1-N3), aggregated 7 (N4, N6-N9, N10 for 2026-27, N11), partial/unusable-as-of 1 (N12), gap 2 (N5, N13).
