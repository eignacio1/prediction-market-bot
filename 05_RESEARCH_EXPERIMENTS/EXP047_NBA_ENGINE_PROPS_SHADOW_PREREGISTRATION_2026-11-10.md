# EXP-047 (W109.3, B-070) — NBA player props priced from the NBA engine: pre-registration of 9 shadow cells (2026-11-10)

**Status: written and committed BEFORE any EXP-047 shadow row exists.** No runner is installed; the registry cells are SHADOW (evaluate-and-log) and the runner is paused until the operator approves the named install task. Shadow only: no order, position, fill, stake or `kelly_fraction` (ADR-0048 sizing zero stands). Guardrails unchanged.

Purpose (ADR-0073): one engine prices the whole board. NBA player props are priced from the same game draws as the NBA engine's moneyline/spread/total (engine_v2), via `nba_engine/props.py` — player points sum to the team's points in the same draw; rebounds/assists/threes are drawn as a team total coupled to the draw's points, then split. This is the prerequisite for engine-priced parlays. Pillar: BREADTH (B4 props families logging).

## 1. Cells (9)
`NBA_PLAYER_REBOUNDS` (KXNBAREB), `NBA_PLAYER_ASSISTS` (KXNBAAST), `NBA_PLAYER_THREES` (KXNBA3PT) × `T1` (12–48 h), `T2` (4–8 h), `T3` (15–60 min) before tip. Points (KXNBAPTS) is already covered by EXP-039/EXP-040 (different model: LR/NB features) and is **not re-registered**; the engine's points price is logged as a field-only comparator inside the same rows' family only if the runner is extended by a later pre-registration. T4/T5 out of scope.

## 2. Model (frozen by this file)
`engine_v2` with fixed league constants (hca 2.0, tbias 0, sd_margin 13, sd_total 19), walk-forward shrunk team ratings (prior weight 8 games at league mean 114), 4,000 draws per game, `props.py` defaults (beta/r/rest/conc as in `DEFAULT_*`). Player expected stats = mean of the player's prior games (≥4 games, ≥10 mpg, top 10 by minutes). A player not in the prior rotation yields no row. No availability/injury information (largest known weakness). **No parameter is fitted or changed on W109.3 backtest data or on shadow data (Hard Rule 4); any change is a new challenger with its own pre-registration.** The constants block is hashed (sha256 in the row as `model_sha256`).

## 3. Prior evidence (W109.3 Part B, `12_EXPLORATORY/quant_w109_props/RESULT.md`)
Backtest on settled Kalshi props 2026-10-20..11-10, n=15,364, 96 games; Brier(engine) − Brier(market mid, last two-sided quote ≥5 h before close), game-clustered bootstrap 95% CI: rebounds +0.0103 [+0.0069,+0.0141]; assists +0.0072 [+0.0029,+0.0114]; threes +0.0068 [+0.0030,+0.0108] (points +0.0156 [+0.0106,+0.0210], not a cell here). The engine was worse than the market in every family.

## 4. Scoring rule and judged n
- Score: per cell, Brier(engine p_yes) − Brier(market mid at the logged row), one row per (market, band) at the first in-band evaluation; settlement from Kalshi result. Scalar-settled (DNP / postponed) markets are excluded and counted separately.
- Interval: game-clustered bootstrap, 95%, 5,000 resamples (rows from one game are not independent).
- **Judged n per cell: 300 settled markets spanning ≥ 40 distinct games.** No score is read below judged n; a cell that does not reach it is reported "not judged", not extrapolated. A look is taken once per cell at judged n; later looks are descriptive.
- Verdict: engine BETTER if the whole interval is < 0; WORSE if > 0; otherwise NO DIFFERENCE. Edge net of fee/spread is a separate, later question (e_net columns are logged but not scored here).

## 5. Modal outcome, stated in advance
Engine WORSE than the market in all three families at judged n (from §3: probability ~0.8 per family that the interval excludes 0 on the worse side; ~0.15 no difference; ≤0.05 better). A NO is a result, not a failure; it will not be explained afterward as a data problem unless §6 pre-lists it.

## 6. Known confounds pre-listed
No availability data (starters rested/out inflate engine mass on absent players); selection toward prior-rotation players; short early-season history (≥4 games); market quotes at logged time may be thin. The Part B backtest shows engine mean p below yes-rate in points (0.336 vs 0.380) — an under-dispersed/biased mean is the leading suspected mechanism; recorded here so it cannot be invoked post hoc as a surprise.

## 7. Operations
Ledgers: `exp_output/PREGAME_SHADOW_EXP047/NBAENG_<MARKET_TYPE>_<band>.jsonl`. Runner `scripts/run_nba_engine_props_shadow.py` (public read-only Kalshi GETs, ESPN public JSON; no orders). RUNTIME_REGISTRY entry status `paused`; install is one allowlisted task, named in the W109.3 handoff, run only after the operator approves it by name. Factor stage reached: aggregated/interpreted — **not applied** (no tested path to a stake).
