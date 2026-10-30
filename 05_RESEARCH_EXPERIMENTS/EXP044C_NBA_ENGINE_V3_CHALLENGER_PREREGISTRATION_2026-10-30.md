# EXP-044c — NBA engine v3 challenger (availability + rotation lineups), frozen forward test (pre-registration)

**Status:** FROZEN at merge of the PR that adds this file, before the arm's first row. **Date:** 2026-10-30. **Block:** W97.1 Part A (backlog B-001).
**Pillar:** DEPTH + PROOF. **Challenger to:** EXP-044b (v2, params hash `d50932902832762d`) and EXP-044 (v1, `9019981832b8b15d`).
**Guardrails:** prices are logged only. No order, stake, `kelly_fraction`, gate, ledger row or live model is touched. No real capital. Free data only.

## What is frozen
- **Engine:** `src/prediction_market_bot/nba_engine/live_v3.py` (+ the merged `engine_v3.py`) and the artifact `12_EXPLORATORY/nba_engine_v3/frozen/v3_frozen_2027.json`,
  **sha256 `e7e2666ff0a6aa86…` (full: `e7e2666ff0a6aa8695e9c875ca2a20d6c33b41b1ede34a9b10b1b2856c80a081`)**; the runner refuses to start on a hash mismatch. The params hash written into every row is the first 16 hex of that sha (`e7e2666ff0a6aa86`).
- **Model:** v2_core (as-of team means, K = 10, estimated score correlation) plus two shifts and a per-family Platt step, fit on seasons 2024–2026 only (3,380 games), no refit during the arm:
  expected-missing availability (injury status → play rate, rates frozen from 2023–24) and rotation-weighted lineup net rating. Shifts: margin d_exp_missing −23.70, d_lineup_net +4.1137; total s_exp_missing −6.4855, s_lineup_net −0.65496. Platt (intercept, slope): ml (−0.0837, 1.4161), spread (−0.00079, 1.0423), team_total (−0.01626, 0.98181), total (−0.03302, 0.97994).
- **Pricing instant and quote:** identical to EXP-044 (tip − 60 min; Kalshi archive quote no older than 45 min; mid price). Rows → `exp_output/NBA_ENGINE_LIVE_V3/rows.jsonl`, same schema as v1/v2 plus `engine_version="v3"`, `claim`, `injury_slot_et`, `injury_report`, `rotation_known`, `factors`, `h_cover`, `a_cover`.

## What is claimed (and what is not)
- **Claimed:** spread and team total only — the two families where v3 beat v2_core held-out. **Not claimed:** moneyline (held-out CI includes zero) and total (v3 is worse, as expected). Moneyline and total rows are still logged (`claim=false`) so the null/worse results are checked forward, never read as a pass.
- **Held-out evidence (2025–26, n = 2,271 games, injury statuses cut at tip − 60 min, v3 minus v2_core Brier, game-clustered bootstrap 95%):** spread −0.00758 [−0.0104, −0.00484]; team total −0.00254 [−0.00353, −0.0015]; moneyline −0.00006 [−0.00394, +0.00402]; total +0.00023 [+0.00002, +0.00043]. (Lead 0, W96.1: spread −0.00793, team total −0.00264, moneyline −0.00072, total +0.00022 — conclusion unchanged at lead 60.)

## Disclosed gaps between the study and the live arm (store lag, stated up front)
1. **Injury snapshots.** The lineup-window capture (`scripts/nba_lineup_window_capture.py`) keeps only the latest report; no tip-60 snapshot exists anywhere. The live_v3 runner keeps its own append-only `injury_snapshots.jsonl` (names re-normalised) and prices from the latest slot ≤ tip − 60 on the tip's ET date. Games priced before any snapshot exists get the Unreported rate (flagged `injury_report=false`).
2. **Rotation and ratings are an end-of-2025-26 snapshot** (each team's last 10 completed games; ratings as of the start of 2027, season-gap decay applied). The event store has no 2026-27 player-level rows, so roster changes are ignored: injured players absent from the snapshot are skipped, and coverage is logged (`h_cover`, `a_cover`, `rotation_known`).
3. Early-season rotations differ from the study's in-season rotations; play rates are frozen from 2023–24.
These are scored, not hidden: each is a row-level flag, and the verdict is also reported on `injury_report=true & rotation_known=true` rows alone.

## Scoring (same as EXP-044)
Paired Brier, engine vs market, per claimed family, on the same tickers v1/v2 are scored on. d = Brier(engine) − Brier(market), negative favors the engine. Skill weight w from the regression of outcome on the engine/market logit blend. Game-clustered bootstrap (2,000 resamples). Additional paired contrast: v3 minus v2 Brier per family on rows both logged.

## Judged n and pass rule
Same as EXP-044: 300 games for full-effect detection, **1,200 games for a PASS call**. PASS (vs market) per claimed family requires the game-clustered upper bound of mean d < 0 and w ≥ 0.01 at n ≥ 1,200; a v3-over-v2 claim requires the upper bound of (v3 − v2) < 0 at the same n. Nothing is read as a verdict below judged n.

## Looks
Descriptive checkpoint 2027-01-31 (no verdict). Verdict look 2027-04-20.

## Modal outcome (stated before any row)
Undecided/FAIL against the market on both claimed families (spread is among the most-attended lines). v3 ≤ v2 in Brier on spread and team total but with a gap smaller than held-out (modal forward expectation roughly half, because of the stale rotation snapshot); moneyline v3 ≈ v2; **total v3 not better than v2** (expected, no claim).

## Not allowed to change
Parameters, artifact, claim set, quote window, scoring or judged n after the first row. A change is a new pre-registration.
