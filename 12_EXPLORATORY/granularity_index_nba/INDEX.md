# NBA granularity index (W111.4 Part B) -- season 2024-25, 82 games, parts 1-4

Each entry: the split, its rank against every team-season (lineup-season) at the same games-played point, split-half stability (Spearman-Brown, bootstrap CI > 0 = trait), the matchup cross at 20/40/82 games, how often it occurs, the market map. Part 5 (application) is `nba_engine/filters.py` and the per-leaf scoring in Part C. Source: `build_index.py` over the NBA event store; entries in `entries/`.

| entry | unit shown | value | rank vs history | stable trait | split-half r |
|---|---|---|---|---|---|
| clutch_offence_ppp | 1610612743 | 1.297 | 9 of 270 | yes | 0.20 |
| clutch_defence_ppp | 1610612749 | 1.003 | 6 of 270 | no | 0.11 |
| trailing_big_q4_offence_ppp | 1610612739 | 1.360 | 1 of 270 | no | 0.03 |
| leading_big_q4_defence_ppp | 1610612750 | 1.044 | 44 of 269 | no | 0.21 |
| pace_seconds_per_possession | 1610612743 | 3.745 | 12 of 270 | yes | 0.91 |
| pace_after_made_shot | 1610612739 | 2.146 | 14 of 270 | yes | 0.78 |
| pace_after_missed_shot | 1610612749 | 1.938 | 4 of 270 | yes | 0.79 |
| ppp_after_live_ball_turnover | 1610612756 | 1.443 | 2 of 270 | yes | 0.34 |
| second_chance_ppp | 1610612750 | 1.326 | 6 of 270 | yes | 0.40 |
| turnover_rate | 1610612760 | 0.117 | 3 of 270 | yes | 0.87 |
| turnovers_forced_rate | 1610612760 | 0.171 | 3 of 270 | yes | 0.88 |
| three_attempt_rate | 1610612738 | 0.500 | 1 of 270 | yes | 0.98 |
| three_attempt_rate_allowed | 1610612753 | 0.327 | 70 of 270 | yes | 0.95 |
| free_throw_rate | 1610612753 | 0.240 | 56 of 270 | yes | 0.83 |
| first_four_minutes_ppp | 1610612739 | 1.255 | 6 of 270 | yes | 0.51 |
| lineup_onfloor_offence_ppp | 1626157-1628384-1628404-1628973-1630540 | 1.405 | 3 of 1477 | yes | 0.08 |
| lineup_onfloor_defence_ppp | 203924-1629014-1630166-1641739-1642270 | 0.845 | 2 of 1473 | yes | 0.07 |
| shooting_lineup_offence_ppp | 1610612741 | 1.258 | 9 of 187 | no | 0.18 |
| defensive_lineup_defence_ppp | 1610612756 | 0.990 | 5 of 154 | yes | 0.47 |
| shooters_vs_defenders_offence_ppp | 1610612738 | 1.237 | 10 of 119 | no | 0.20 |
| rim_fg_allowed | 1610612760 | 0.614 | 47 of 270 | yes | 0.85 |
| corner_three_make_rate | 1610612749 | 0.427 | 8 of 270 | yes | 0.25 |
| above_break_three_make_rate | 1610612739 | 0.372 | 24 of 270 | yes | 0.48 |
| midrange_make_rate | 1610612756 | 0.494 | 4 of 270 | yes | 0.77 |

Reading: a team-level `trait=no` entry (clutch defence, trailing-big offence, leading-big defence, shooting-lineup offence, shooters-vs-defenders) is noise at one season's sample; its cross shrinks to the league mean, so its leaf is routed on the market state alone. Lineup on-floor PPP is a trait statistically (n=1,477 lineup-seasons) but with r~0.08 it moves a price very little.

Data limits (GG-1895): possession lineups are quarter-box based; player_box.position blank on ~56% of rows so lineup types come from prior-season 3PA/36 and stl+blk/36; no tracking or coverage data.
