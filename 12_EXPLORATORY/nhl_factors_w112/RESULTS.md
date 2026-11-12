# W112.4 NHL factor classes: results (Parts A + C; Part B not done)

Source: `leaf_scores.json` (score_leaves.py). 44,979 settled shadow rows, 271 games, 8 filters known for all. 70/30 game split, arm picked on fit, game-clustered bootstrap 90% interval, BH q=0.10.

- 72 leaves; 44 routed; 38 reportable; 1 BH survivor.
- Survivor: `deployment@side` NHL_MONEYLINE `away_edge` -> MOMENTUM, held-out +0.133 [+0.085, +0.179], 35 rows / 15 games. Few games: a lead needing replication, not a verdict.
- Nominal (not BH) leads: deployment@total low MODEL_FADE +0.272 [0.081, 0.419] (12 games); shot_quality@side home_edge RIDE +0.219 [0.063, 0.323] (12 games); shot_quality@total mid MODEL_FADE +0.105 [0.002, 0.203] (57 games).
- Puck line: no leaf with a positive interval here; routed to ride / no bet in these leaves (hypothesis parked for R&D, not closed as an arm).

Stages (SEATS/nhl.toml): applied 3 -> 8 of 12 (H1, H3, H6, H7, H8 added). Caveats: router does not yet call `nhl_filters` (112.1); H2 goalie quality is previous-game starter only (GG-1010).
Interface for 112.1: `nhl_filters(home, away)` in `nhl_engine/filters.py`; per-team dict keys rest_days, back_to_back, games_last_7d, travel_km, tz_shift_h, neutral_site, hd_for, hd_against, top_share (last three as league percentiles).
Part B (goalie confirmation timing, Muse snapshot grading, officials/injuries gaps) not started.
