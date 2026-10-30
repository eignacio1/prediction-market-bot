# W96.1 results — NBA engine first nights (Part A) and v3 (Part B)

Block: W96.1, backlog B-001 (engine lane, rank 2; Part B rank 3). Pillar: DEPTH + PROOF. Written 2026-10-30.

## Part A — first real nights: NOT READABLE YET (stated plainly)

- Source: `04_EXECUTION/BOX_TASKS/results/20261030T1440Z_w95_1_nba_engine_cron_readback.md` (14:35Z).
- Crons installed (daily refresh 12:33 UTC; runner every 10 min 16-23,0-4 UTC under flock). v1 (EXP-044) rows = 0; v2 (EXP-044b) rows = 0; no runner log yet. Store: 67 games, last_game_date 2026-10-28.
- No NBA game has tipped since the install, so no per-game / per-family row counts, no quote at tip-60, no runner-error count and no v2 memory reading exist to read back. Nothing here is a silent arm: a silent arm needs a tipped game.
- GG-1450 stays OPEN (resolves only on rows).
- Still required: after tonight's tips (games ~23:00Z+, rows by ~02:00Z) request box task `nba_engine_cron_readback` and read per-family rows for v1 and v2 per game, archive quote at tip-60, errors, v2 memory. A game that tipped without rows = silent arm, fix before anything new.
- Observe-only, not touched: B-017 (store two days behind), B-007 (517 MB runner on a 961 MB box).

## Part B — v3 candidate: availability + lineups over v2

Module `src/prediction_market_bot/nba_engine/engine_v3.py` (new; v1/v2 untouched). v2's core plus train-mean-centred factor shifts on margin and total (missing/NaN = neutral). Tests `tests/test_nba_engine_v3.py` (3 known-answer: centred margin shift recovered and missing is neutral; total factor routes to total only; no factors == v2 core).

Factors (stage per ADR-0075):
- Availability, `d_/s_exp_missing`: expected missing rotation-minute share from injury statuses at tip_earliest, lead 0; status→play rates fit on 2023–24 only. Stage: INTERPRETED for spread and team total (moves price, held-out); not applied (no forward arm logging).
- Lineups, `d_/s_lineup_net`: rotation-weighted prior-game player ratings (pre-tip; not the leaky in-game rating). Stage: INTERPRETED for spread and team total.
- Officials: NOT built. Crew is post-game in the archive with no assignment timestamp (GG-1390); a factor not known before the price is an upper bound, not a pricing input. Stage: aggregated only.

Design: rolling origin, TEST = seasons 2025, 2026 (n_test 1141 / 1130; n_train 2216 / 3357), v2 core refit on the same in-coverage training games, Platt on training predictions, scored at v1's own strikes, paired game-clustered bootstrap (2000 reps). Seasons before 2023 have no injury reports and are excluded. `study_v3.py`, output `study_v3_out.json`.

Brier delta vs v2 core (negative = better), pooled 2025–26, n_games 2271, 95% CI:

| family | avail | lineup | avail+lineup |
|---|---|---|---|
| spread | −0.00338 [−0.00548, −0.00130] | −0.00576 [−0.00809, −0.00336] | −0.00793 [−0.01074, −0.00514] |
| team_total | −0.00109 [−0.00182, −0.00035] | −0.00195 [−0.00283, −0.00112] | −0.00264 [−0.00362, −0.00161] |
| moneyline | +0.00113 [−0.00235, +0.00481] | +0.00086 [−0.00247, +0.00418] | −0.00072 [−0.00455, +0.00317] |
| total | +0.00011 [−0.00004, +0.00026] | +0.00014 [−0.00003, +0.00030] | +0.00022 [+0.00001, +0.00042] |
| ALL | −0.00125 [−0.00217, −0.00030] | −0.00223 [−0.00329, −0.00119] | −0.00313 [−0.00433, −0.00192] |

ALL for avail+lineup by season: 2025 −0.00252 [−0.00413, −0.00083]; 2026 −0.00374 [−0.00538, −0.00205]. v2 core absolute Brier pooled: ml 0.20639, spread 0.23664, team_total 0.23091, total 0.24179, ALL 0.23370.

Reading: v3 beats v2 on spread and team total (both seasons for lineup and avail+lineup; availability alone only in 2026); no distinguishable change on moneyline; slightly worse on total, so v3 is not carried for total. Multiplicity: 3 variants × 4 families + ALL, reported as-is; spread and team total survive a 12-contrast Bonferroni-style reading, ALL and the others are not claimed beyond that.

Fitted shifts (avail+lineup): T=2025 margin −22.6 pts per unit missing share, +3.34 per lineup-net unit; total −0.41 / +0.47. T=2026 margin −20.1 / +3.80; total −2.48 / +0.12.

### Granularity index, five parts per factor (honest status)

| part | availability | lineups |
|---|---|---|
| split | home–away difference and home+away sum, as above | same |
| rank vs history at same season point | NOT computed this block | NOT computed this block |
| matchup cross | NOT computed (no cross of missing share with opponent's rotation depth) | NOT computed |
| market map | spread and team total move; moneyline and total do not | same |
| application | held-out Brier gain above; no forward arm yet | same |

Rank-vs-history and matchup-cross are open DEPTH work, not claimed.

Caveats: two test seasons; 2–3 seasons of in-coverage training; injury reports exist only from 2022–23 and status rates are fit on 2023–24; live use needs an injury snapshot at tip-60 and rotation/ratings from a store that currently lags ~2 days (B-017).

When it applies: pre-tip pricing of spread and team-total lines for games where an injury report exists; not for moneyline or total.

## EXP-044c: NOT frozen, NOT installed (stated plainly)

v3 beats v2 on spread and team total, so the block's EXP-044c path is triggered. A forward arm needs a live runner (`live_v3`) that reads a tip-60 injury snapshot and rotation ratings from a store two days behind (B-017) on a box with 961 MB RAM and a 517 MB runner (B-007). That was not built or safely installable inside this block, and freezing a pre-registration with no runner to log it would only leave a frozen claim with no rows. Handed back as the next step: build `live_v3` (reusing `live_v2` helpers), freeze EXP-044c (claims spread and team total only; no claim for moneyline; total expected ≤ v2; same scoring as EXP-044) before its first row, register in RUNTIME_REGISTRY, install on a GREEN budget read.

## Part C (B-009): NBA engine prices player points — held-out result, with a leak found and removed

Module `src/prediction_market_bot/nba_engine/player_layer.py` (new, PR #387, merged; v1/v2 untouched, imported by no service, nothing installed). `shares_from_means`, `draw_split` (gamma-Dirichlet weights + multinomial per draw, so players' points plus a rest bucket sum exactly to the drawn team points), `fit_concentration` (beta-binomial ML), `p_at_least`. Tests `tests/test_nba_player_layer.py` (2 known-answer: known shares recovered within 0.004 and the sum constraint exact; concentration 120 recovered in 85–170). Study `study_partc.py`, output `study_partc_out.json` (row-level csv.gz kept local).

Design: folds as W69.3 (test 2025 = train 2023 / cal 2024; test 2026 = train 2023–24 / cal 2025); n_test_rows 25233 / 25556 (engine-joined 25210 / 25538), 2 seasons, ~2460 games; Platt on the calibration season; strikes 10/15/20/25; paired, game-clustered bootstrap (B = 20000), 95% intervals. Brier delta, negative = first arm better.

### The leak (stated plainly)
Arms `engine` and `sumonly` normalise each player's share over the players who played that game. Who played is known only after the game, and the base arm (EXP-039 spec) does not have it. Their gains therefore are **not** a pricing result. I added `engine_pt`, which forms the share as ridge mean / (mean of the team's sum of ridge means over its previous 10 games), so no teammate's presence enters.

| pooled 2025+26 | engine−base (leaky) | engine_pt−base (leak-free) |
|---|---|---|
| ALL strikes | −0.00340 [−0.00382, −0.00300] | +0.00001 [−0.00029, +0.00032] |
| strike 10 | −0.00652 [−0.00735, −0.00571] | −0.00070 [−0.00117, −0.00022] |
| strike 15 | −0.00360 [−0.00430, −0.00292] | +0.00001 [−0.00046, +0.00050] |
| strike 20 | −0.00193 [−0.00251, −0.00135] | +0.00072 [+0.00029, +0.00116] |
| strike 25 | −0.00155 [−0.00204, −0.00104] | +0.00002 [−0.00034, +0.00039] |
| star (pts10≥15) ALL | −0.00458 [−0.00568, −0.00348] | +0.00078 [−0.00012, +0.00169] |
| star strike 20 | −0.00531 [−0.00728, −0.00333] | +0.00266 [+0.00113, +0.00423] |

By season, leak-free ALL: 2025 +0.00049 [+0.00005, +0.00094] (worse); 2026 −0.00045 [−0.00086, −0.00004] (better); stars 2025 +0.00247 [+0.00113, +0.00385], 2026 −0.00089 [−0.00206, +0.00030]. The sign flips between seasons.

### Verdict
No engine-priced-points advantage over the existing arm (nba_player_points_v1 / EXP-040 baseline) once the post-game information is removed: pooled ALL is indistinguishable from zero; strike 10 is slightly better; strike 20 and the star subset at strike 20 are worse; the season sign flips. **EXP-044d is NOT frozen.** The block's trigger for it (engine beats existing arm held-out) is not met. Multiplicity: 4 strikes × 2 subsets × contrasts reported as-is; descriptive.

Caveats: two test seasons; engine 2–3 params fit in-sample on the calibration season; rows condition on the player having played (same as EXP-039); who-played-at-tip is unavailable, so a real pre-tip arm would need an expected-minutes input (the availability factors of Part B are the candidate, not wired here).

Market comparison: none possible. Kalshi KXNBAPTS is not archived before 2026, and the 2026-27 live rows are sealed-cell data (CHARTER rule 2), so there is no admissible market price to compare against; stated, not worked around.

ADR-0075 stage, player points from the engine: aggregated + interpreted (the split and the team-total link are built and tested); **not applied** (no leak-free held-out gain, no forward arm). When it would apply: pre-tip pricing of player-points over/under at strikes 10/15/20/25 for players expected to play, using the engine team total.

Lesson kept: any share normalised over a post-game roster is a leak; run the leak-free variant first.
