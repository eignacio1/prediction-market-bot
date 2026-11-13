# Session handoff - W113.3 (B-086) NBA joint for same-game legs

**Status:** PARTIAL | B-086: built and merged, teammate classes open | branch session/20261112T230443Z-w113-3-nba-joint, merged as a5cffd2 | PR #496, CI green (first run red on a stale registry test already red on main; rebased onto the fix, re-ran green) | Operator decisions: none.

**One line:** a shared-latent player joint (`nba_engine/joint.py`) closes the same-player points x threes covariance gap; teammate points, points x assists (teammates) and win x rebounds are not closed.

## MEASURE MOVED
D4 NBA (whole board from one engine, parlays included). Source: `12_EXPLORATORY/sgp_correlation/RESULT_W113_3.md`, held-out 2025-26, 1,075 games, game-clustered 95% CIs, parameters frozen on 2024-25.
Covariance gap (realised - engine), before -> after:
- PTS x 3PM same player +0.0861 -> -0.0042 [-0.0109, +0.0025] (closed)
- PTS x REB same player +0.0388 -> +0.0191 [+0.0122, +0.0255] (halved)
- PTS x AST same player +0.0111 -> +0.0063 [-0.0006, +0.0128]
- PTS x PTS teammates +0.0247 -> +0.0230 (NOT closed, sign still wrong)
- PTS x AST teammates +0.0038 -> +0.0108 (worse)
- WIN x REB +0.0173 -> +0.0176 (NOT closed)
Log-loss gain over the independent product: PTS x 3PM +0.0037 -> +0.0491; PTS x REB -0.0010 -> +0.0110.
Game-level Brier old/new identical (ML 0.21544, SPR 0.24966, TOT 0.25012; max |dp| = 0): not worse.
3-leg combos (n 4.4-4.6k): joint Brier beats the naive product in all three (0.2030 vs 0.2162; 0.1938 vs 0.2024; 0.2287 vs 0.2343). Lines sit at the engine median, so realised is above predicted for every method (known marginal bias).

Hypothesis closed (W110.4 teammate-points sign, WIN x REB; parked for R&D): a fixed-team-total split cannot lift teammate covariance; the positive realised value comes from the team total varying, which needs a pace/total latent shared across the two teams' players.

## Stage per factor (ADR-0075)
Minutes, pace, blowout, usage/form: aggregated and interpreted as shared latents, applied in the engine joint. Not yet a tree split. `JointRoster.usage` tilt is tested (usage shift lowers a teammate's points) but not fed by any lineup source.

## Interface for 113.1 (`decision_trees/longshot.py` pot-of-gold branch)
`nba_engine.sgp_price.price_combo(GameDraws, [LegSpec...])`, 2-3 legs. Returns legs, p_marginals, p_joint, p_naive, lift, excess, mc_se, resolved, frechet_lo/hi, n_draws. Leg kinds: ml / spread / total / team_total / player. Fair value only: no fee, no market price. Example input: `12_EXPLORATORY/sgp_correlation/w113_joint_combo3.csv.gz`. 113.1 owns the tree wiring.

## Caveats
Fixed engine constants; top-3 players per team; median lines; no team-total cap on rebounds/assists; DNP survivorship; 2026-27 data not used; no Kalshi combo market open and no fee schedule applied.

## Required fields
- vision_pillar: DEPTH (D4 NBA)
- gap_measure: same-game joint covariance gap by pair class
- gap_delta: see MEASURE MOVED
- pattern_sweep: n/a (no defect fixed)
- surface_delta: 0 (nothing imports the new modules from a service; no RUNTIME_REGISTRY entry)
- directive_conflicts: none
- `*_install` tasks needed: none
- Box deploy read after merge: requested via the deploy_truth_read box task; nothing in t4-mlb imports the new modules, so no decision to record.
