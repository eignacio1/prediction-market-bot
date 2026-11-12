# W113.3 — NBA same-game joint: shared latents (B-086)

Held-out: 2025-26 regular season, 1,075 scored games (same as W110.4). Fit: 2024-25 only (`fit_joint.py`, 200 games after the first 60, 70 random-search steps, 1,500 draws; `fit_joint_2024-25.json`; first version without a rebound loading kept as `_v1.json`). Same games, legs, lines (engine median), seeds and 4,000 draws for "before" (`props.py`, independent stats) and "after" (`nba_engine/joint.py`). Rows: `w113_{old,joint}_rows.csv.gz`; tables: `w113_*_analyze.txt`, `w113_*_RESULT.json`.

## Covariance gap = realised − engine covariance (against realised marginals), game-clustered 95% CI

| Pair class | n pairs | before | after |
|---|---|---|---|
| PTS x 3PM same player | 4,392 / 4,394 | +0.0861 [+0.0795,+0.0931] | **−0.0042 [−0.0109,+0.0025]** |
| PTS x REB same player | 4,631 | +0.0388 [+0.0317,+0.0452] | +0.0191 [+0.0122,+0.0255] |
| PTS x AST same player | 4,631 | +0.0111 [+0.0039,+0.0177] | +0.0063 [−0.0006,+0.0128] |
| PTS x PTS teammates | 3,532 | +0.0247 [+0.0167,+0.0328] | +0.0230 [+0.0157,+0.0311] (not closed) |
| PTS x AST teammates | 7,064 | +0.0038 [−0.0015,+0.0090] | +0.0108 [+0.0057,+0.0160] (worse) |
| WIN x REB | 4,631 | +0.0173 [+0.0107,+0.0240] | +0.0176 [+0.0110,+0.0243] (not closed) |
| REB x REB teammates | 3,532 | +0.0025 [−0.0053,+0.0106] | +0.0007 [−0.0069,+0.0085] |
| WIN x PTS / TT x PTS / TOT x PTS / TOT x 3PM / PTS x PTS opp. | 4.4k–5.1k | within CI of 0 before and after | within CI of 0 after |

## Log-loss gain of the joint over the independent product (positive = joint better), per pair

PTS x 3PM same: +0.0037 → **+0.0491**. PTS x REB same: −0.0010 → **+0.0110**. PTS x AST same: +0.0022 → +0.0062. Teammate PTS x PTS: −0.0082 → −0.0079 (joint still worse than the product). Teammate PTS x AST: +0.0016 → −0.0004. WIN x REB: −0.0006 → −0.0023. (CIs in the analyze files.)

## Game-level prices (last)
Team scores are the engine's own draws, untouched. Moneyline / spread / total Brier on the same 1,075 games, old vs new: 0.21544/0.21544, 0.24966/0.24966, 0.25012/0.25012; max |Δp| = 0.0. Not worse.

## 3-leg same-game combos (Part C), held-out, fair value, `w113_joint_combo3.csv.gz`
Lines are the engine's draw medians, so realised hit rates sit above predicted for every method (engine marginal bias known since W109.3); compare joint with the naive product.

| Combo | n | mean joint | mean naive product | realised | lift | Brier joint / naive |
|---|---|---|---|---|---|---|
| WIN + PTS + 3PM (same player) | 4,394 | 0.235 | 0.169 | 0.292 | 1.39 | 0.2030 / 0.2162 |
| TOT + PTS + 3PM (same player) | 4,394 | 0.248 | 0.171 | 0.266 | 1.45 | 0.1938 / 0.2024 |
| PTS + REB + AST (same player) | 4,631 | 0.208 | 0.185 | 0.319 | 1.12 | 0.2287 / 0.2343 |

The correlation a retail parlay ignores is worth ×1.1–1.5 on same-player legs. No Kalshi NBA same-game combo market was open; no fee schedule or market price applied.

## Stage per factor (ADR-0075)
Minutes / pace / blowout / usage form: aggregated and interpreted as shared latents in the simulation; applied in the engine joint (a usage tilt hook `JointRoster.usage` exists, tested, not yet fed). Not a tree split yet (113.1 owns trees).

## Caveats
Fixed engine constants (hca 2.0, sd 13/19); top-3 players per team; lines at draw median; rebounds/assists carry no team-total cap; 4 stats only; the loss fits covariance gaps, not marginals; teammate points sign and WIN x REB not fixed (the fitted latents do not reproduce the positive realised teammate covariance); DNP legs dropped (survivorship); 2026-27 games not used. Fit ≠ test seasons.
