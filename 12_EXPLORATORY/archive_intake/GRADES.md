# Archive intake grades (W113.4, B-087)

Last reviewed: 2026-11-12. Archive: `eignacio1/sports-intel-archive` pinned at `cc7bf8501c381e36cac556a53cc86e9c9ce55acc` (read-only).
Grading = the bot recomputed a table family from its OWN free data and compared. Aggregate results only; no archive rows are copied into the repo.
Scripts: `grade_nba.py`, `grade_nhl.py` (this folder). Season = 2025-26 regular season. Nothing here feeds a model until a family is VERIFIED and wired through the index.

Grades: VERIFIED (recompute matched within the stated tolerance) · MISMATCH (recomputed, did not match; reason given) · UNCHECKABLE (no free source or no recompute written).

## NBA (source: bot NBA event store, 1230 regular-season games)

| Table family | Grade | Tolerance / result |
|---|---|---|
| Teams Opponent Shooting by distance, Location=All (540 values) | **VERIFIED** | per-game FGM/FGA within 0.15, FG% within 1.0 pt; 540/540 inside, max diff 0.05 (publication rounding). Distance bins use exact `hypot(x,y)/10` ft, not the store's rounded `shot_distance`. |
| Opponent Shooting, Home / Road split | **VERIFIED** for teams with balanced game counts; **MISMATCH** for neutral-site-affected teams | 97.8% (home) / 98.0% (road) inside 0.15; max diff ~1.1. Misses sit on teams whose home/road game counts differ between store and archive (neutral-site / international games labeled differently). |
| Teams Traditional, Home / Road (26 metrics x 30 teams) | **VERIFIED** except two items | 87.7% home / 85.0% road inside 0.06. **MISMATCH:** turnovers per game (0/30 match; archive higher, consistent with NBA.com counting team turnovers, definitional); games-played off by 1-2 on neutral-site teams, which spills into a few of their other metrics. |
| Teams Shooting by zone, quarter splits, Clutch, Four Factors, Advanced | UNCHECKABLE (this block) | Recomputable from x/y or box in principle; recompute not written. |
| Player tracking (drives, passing, rebounding, pull-up, closest defender, touch time), Hustle, Synergy play types, defense dashboard, matchups, lineups on/off | UNCHECKABLE | No free event-store source. |
| Referees (Basketball-Reference) | UNCHECKABLE | Not in the bot's free sources. |

## NHL (source: bot NHL event store; MoneyPuck teams season summary, situation=all, 32 teams)

| Metric | Grade | Result |
|---|---|---|
| games_played, goalsFor, takeawaysFor, giveawaysFor | **VERIFIED** | exact 32/32 (shootout events excluded, as MoneyPuck does) |
| shotsOnGoalFor (store shots-on-goal + goals), missedShotsFor, hitsFor, faceOffsWonFor | **VERIFIED** | all 32 within 1% and within 2 counts of the archive (event-feed revisions) |
| penaltiesFor | **MISMATCH** | neither "committed" nor "drawn" matches (diffs up to 34 and 52); MoneyPuck's definition unresolved |
| xGoals family, flurry/score-venue adjusted xG, danger-zone xG | UNCHECKABLE | proprietary MoneyPuck model |
| 5on5 table, other seasons | UNCHECKABLE (this block) | situation split not recomputed; only 2025-26 data is in the bot store |
| Scouting the Refs, head coaches | UNCHECKABLE | external tables, no bot source |

## NHL starting-goalie snapshots (the 112.4 Part B question)

Archive `L3-snapshots/nhl/goalies-2026-11-10/11/12`: 42/36/44 games, several snapshots a day (~15:57Z, 18:00Z, 20:00Z), per side Confirmed / Likely / Unconfirmed, `confirmed_at_utc` usually 1-2 h before the snapshot and sometimes 22-24 h.

Grade: **UNCHECKABLE with local data.** The bot has no pre-game goalie capture (starter is known only post-game; GG-1010; the `nhl_goalie_probe` workflow is the existing probe), the bot's NHL game store and Kalshi NHL history end in June 2026, and the snapshots carry no puck-drop time. So the timestamps cannot be compared with the bot's own capture or with Kalshi price moves on the same games. Needs a forward capture (bot-side goalie snapshots plus Kalshi candles for November games) before this can be graded. Stays REPORTED.

## Data-epoch note
No demo fills are used in this block, so the 2026-11-06T01:03:42Z NO-side pricing epoch does not apply.

## Tally
Table families graded: 4 NBA families + 2 NHL metric groups recomputed. VERIFIED 4 (NBA opponent shooting All, NBA Traditional mostly, NHL counts, NHL shots/hits/faceoffs); MISMATCH 3 items (NBA home/road neutral-site labeling, NBA turnovers definition, NHL penalties); UNCHECKABLE the rest (listed above).
