# NHL engine - factor taxonomy and free-source map (W83.3 Part B)

**Date:** 2026-10-21 - **Doctrine:** ADR-0073 stage 1, ADR-0075 stages - **Pillar/measure:** DEPTH D1 (NHL 0 -> 12 classes mapped, counted not built), D4 (data layer), D5(b) - **Decisions logged:** false (DECISION_LOG row deferred to session-end)
**Rules:** free sources only; nothing bought; nothing here is a model. Fields were read from the real store (`exp_output/NHL_EVENTS/`, manifest `event_store_manifest.json`) and from live GETs of the public NHL API on 2026-10-21. Seasons are labelled by starting year (2015 = 2015-16). Template: `NBA_ENGINE/FACTOR_TAXONOMY.md`.

**Point-in-time (PIT)** is the `nhl_point_in_time.py` contract: a post-game row about game G' is usable for G iff `start_latest(G') + buffer <= start_earliest(G)` (buffer 4h regular season, 9h playoffs); schedule facts are public in advance; season-static tables are refused. The NHL schedule carries the real `startTimeUTC`, so no start is imputed.
**Stage** is the ADR-0075 stage today: *aggregated* (the fact is in the store, point-in-time) / *interpreted* (measured as a trait or against a target) / *applied* (a tested path from the fact to a price). **No NHL factor is interpreted or applied by this block.** The legacy shadow arm (`nhl_pregame.py`, EXP-036) is a separate, thinner model and is not read from this store.

| # | Factor class | Free source and fields | First season | PIT availability | ADR-0075 stage today |
|---|---|---|---|---|---|
| NHL-1 | Skater quality (shooting, on-ice volume) | `events`: `shooter_id`, `shot_type`, `x`, `y`, `zone`, `type` (goal / shot-on-goal / missed / blocked), `home_skaters`/`away_skaters`; `box_players`: `goals`, `assists`, `sog`, `hits`, `blocked`, `takeaways`, `giveaways`, `toi_s`, `plus_minus` | 2015 | post_game | aggregated (xy/shot-type/shooter presence per season in the manifest) |
| NHL-2 | Goalie quality (save, workload, starter) | `box_players` (`group=goalies`): `shots_against`, `saves`, `goals_against`, `starter`, `toi_s`; `events`: `goalie_id` on shots | 2015 | post_game. The *confirmed starter before puck drop* is not in the store (W52.D: verdict "cannot tell", GG-401) | aggregated post-game; pre-game starter **GAP-1** |
| NHL-3 | Line / pair deployment | `shifts`: `player_id`, `period`, `start_s`, `end_s`, `duration_s`, `team_id` (line combinations are derivable by overlapping shifts) | 2015 (completeness per season in manifest) | post_game | aggregated (raw shifts; combinations not derived) |
| NHL-4 | Special teams (power play / penalty kill, penalties drawn / taken) | `events`: `situationCode` fields (`away_skaters`, `home_skaters`, goalie-in-net flags), `penalty_player_id`, `penalty_type`, `penalty_minutes`; `box_players`: `pp_goals`, `pim` | 2015 | post_game | aggregated |
| NHL-5 | Pace / shot volume and quality | `events`: shot attempts both sides by strength state, location (`x`, `y`, `zone`); `box` team `sog` | 2015 | post_game | aggregated |
| NHL-6 | Rest / schedule density (back-to-back, games in N nights) | `games`: `start_time_utc`, `game_date_et`, teams | 2015 | schedule (public in advance) | aggregated |
| NHL-7 | Venue / home ice, neutral sites | `games`: `venue`, `neutral_site`, `home_team_id` | 2015 | schedule | aggregated |
| NHL-8 | Travel distance / time zone | none in the store: schedule has venue name only, no coordinates or time zone | 2015 | schedule | **GAP-2** (small free job: a hand-built 32-arena table; not built) |
| NHL-9 | Officials (referees, linesmen) | free: `GET /v1/gamecenter/<id>/right-rail` -> `gameInfo.referees`, `linesmen` (verified for 2015-16 and 2024-25 games). **Not in this store**: needs a fourth fetch kind | 2015 | post_game; crew-assignment timestamp absent | **GAP-3** (free, unfetched; assignment time not recoverable) |
| NHL-10 | Coaches, scratches (healthy scratches = lineup availability) | free: same `right-rail` payload: `awayTeam/homeTeam.headCoach`, `.scratches[]`. Not in this store | 2015 | post_game (scratches known pre-game in practice, but no timestamp) | **GAP-3** (same fetch) |
| NHL-11 | Injuries / availability | none free with history. Current injuries exist on public pages only; no point-in-time history | - | snapshot-only | **GAP-4** (needs daily snapshots going forward; none exists today) |
| NHL-12 | Qualitative (matchup, scheme, intangible) and PAM-derived attributes | none free as structured history; PAM not piped | - | not defined | **GAP-5** |

## Registered gaps
| Gap | GG | What is missing | Why not free-fixable today |
|---|---|---|---|
| GAP-1 | GG-1010 | Confirmed starting goalie before puck drop | The boxscore `starter` flag is post-game; a timestamped pre-game capture does not exist (W52.D, GG-401). Needs repeated captures on the box, not a download |
| GAP-2 | GG-1011 | Travel / venue geometry | No coordinates or time zones in any loaded table; a 32-arena table is a small free job outside this block's ceiling |
| GAP-3 | GG-1012 | Officials, head coaches, scratches | Free (`right-rail`) but a separate ~14.7k-file fetch; assignment timestamps are not recoverable, so officials cannot be used strictly pre-tip |
| GAP-4 | GG-1013 | Injury history | No free historical feed; daily snapshots would start from the day they begin |
| GAP-5 | GG-1014 | Structured qualitative and PAM-derived factors | No free feed; PAM not piped into the NHL engine |

Not purchased: nothing. No paid source was needed to map any class.

## Count
12 classes mapped (D1 NHL: 0 -> 12). By ADR-0075 stage: aggregated 7 (NHL-1 to NHL-7; NHL-2's pre-game starter is GAP-1), gap 5 (NHL-8 to NHL-12). Interpreted 0, applied 0.
