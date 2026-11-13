# W114.4 — NBA joint, teammate legs: one usage pool per team (B-086)

Hypothesis closed (W114.4 team-pool latents, parked for R&D): a team-level rest-bucket shock (`s_pool`), a shared minutes shock (`s_tmin`), assists loaded on teammates' makes (`gamma_ast`) and rebounds loaded on the opponent's misses (`gamma_reb`) do NOT close the teammate covariance gap on held-out games.

Held-out 2025-26, 1,075 games, same games/lines/seeds/4,000 draws as 113.3. Fit: 2024-25 only (`fit_joint.py`, 60 random-search steps, 200 games; `fit_joint_2024-25_w114.json`; loss 5.27e-5 at zero latents -> 4.90e-5, fitted `s_pool` 0.010, `s_tmin` 0, `gamma_reb` 0, `gamma_ast` 0.176).

Why it cannot work here: points are already one multinomial over the team's points, so shares sum to the team total. What the realised data show is teammates' points moving together above that, and the named-player shares are only a small slice of what varies; the search put the pool shock at about 0, i.e. the loss does not reward it.

## Covariance gap (realised - engine, against realised marginals), game-clustered 95% CI (`gap_ci.py`)
| Pair class | n | 113.3 | 114.4 fitted |
|---|---|---|---|
| PTS x PTS teammates | 3,532 | +0.0230 [+0.0156,+0.0311] | +0.0224 [+0.0147,+0.0303] (not closed) |
| PTS x AST teammates | 7,064 | +0.0108 [+0.0054,+0.0161] | +0.0078 [+0.0026,+0.0129] (smaller, not closed) |
| REB x REB teammates | 3,532 | +0.0008 [-0.0060,+0.0084] | -0.0008 [-0.0078,+0.0062] (was already ~0) |
| WIN x REB | 4,631 | +0.0176 [+0.0107,+0.0249] | +0.0204 [+0.0134,+0.0275] (worse) |
| PTS x 3PM same | 4,392 | -0.0042 | -0.0039 |
| PTS x REB same | 4,631 | +0.0191 | +0.0220 (worse) |
| PTS x AST same | 4,631 | +0.0064 | +0.0083 (worse) |

## Game level (last): team scores are the engine's draws; Brier ML / spread / total 0.21544 / 0.24966 / 0.25012 before and after. Not worse.

## 3-leg combos re-priced (fair value, held-out), 113.3 -> fitted 114.4 Brier
PTS+REB+AST 0.2287 -> 0.2339; TOT+PTS+3PM 0.1938 -> 0.1947; WIN+PTS+3PM 0.2030 -> 0.2043. Slightly worse, so the fitted values are NOT shipped.

## Decision in code
The latents are in `nba_engine/joint.py`, tested on known answers (`tests/test_nba_joint.py`), default 0 = 113.3 behaviour. The pot-of-gold input is unchanged. Rows: `w114_joint_*`.

Applies: pre-game with team points draws. Does not: nothing here models who takes the shot beyond the fixed split; the sign of teammate covariance likely needs lineup-level (on/off) data, a registered next hypothesis.
Stage (ADR-0075): usage pool aggregated and interpreted; applied = NO (no held-out gain).
