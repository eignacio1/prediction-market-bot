# EXP-044 — NBA engine v1 prices the live board: forward pre-registration

**Status:** FROZEN at the commit that adds this file (hash is that commit's SHA, recorded in its commit message and in `12_EXPLORATORY/nba_engine_live/results_W94_1.md`). Written before any 2026-27 engine row was scored; the first logged rows are a dry run on archive day 2026-10-28 and carry no outcome. Not edited after the freeze; a change is a superseding EXP.
**Pillar / measure:** DEPTH + PROOF — D4 NBA (engine pricing live boards), D3 challengers 3 -> 4, P3 (one dated engine look).
**Scope guard:** logging and scoring only. No order, stake, gate, live model, registry cell or ledger row. Reads the price archive. No edit of engine logic (`live.py` is a thin entry point).
**Block:** W94.1 Part B. Engine: 93.3, PR #363, pinned commit `cfdc423`.

## What is logged
For every NBA game on the archive, at the first runner pass with tip−60 min <= now < tip: every contract of four Kalshi families — NBA_MONEYLINE (KXNBAGAME), NBA_SPREAD (KXNBASPREAD), NBA_GAME_TOTAL (KXNBATOTAL), NBA_TEAM_TOTAL (KXNBATEAMTOTAL) — gets `p_engine` and `p_market` (the archive's latest quote at or before T−60, not older than 45 min; no quote → no row). Strike rule: ticker suffix N -> floor_strike N−0.5 -> P(X >= N).
**Frozen parameters:** shrinkage K = 10; ratings from regular seasons <= 2026 with as-of-cut point-in-time updating (a game informs a rating only once it has ended, plus a completion buffer); calibration season 2026 (hca, tbias, s_p, s_e fit there once); 4,000 simulations per game; seed derived by sha256 of the event ticker. The parameter hash is written on every row.
**Known weaknesses, stated now (from 93.3):** moneyline slope 1.83 (over-confident); simulated score correlation 0.30–0.44 vs empirical 0.24–0.35; simulated total SD 20.2–20.8 vs 18.7–19.4; a ~3.5-point home lean vs the market on 33 pre-season games; early-season ratings are mostly the prior-season mean. Descriptive 2026-10-27 comparison (n=32, no outcomes): engine ML minus market +0.035 on the home side, margin SD 15.2 vs 13.2, total SD 20.1 vs 18.8.

## Hypothesis
The engine's probabilities, before any recalibration, are no worse than the market's in Brier score for at least one family and carry skill weight w > 0 under the accepted gate (`position_gate.skill_weight`, w = clip(1 − Brier_engine / Brier_market, 0, 1); market-anchored pricing, 10-21).

## Scoring
Paired per-row difference d = (p_engine − y)² − (p_market − y)², per family and pooled, **game-clustered** (cluster = event ticker; `quant.inference.cluster_bootstrap`, 2,000 resamples, 95% percentile interval). `nba_engine/live_scoring.py`. Outcome y from the final score of the nba_stats/ESPN result. Reported beside it: w per family, reliability curves.

## Judged n
n = ((z_a + z_b) · sigma_c / delta)², one-sided alpha 0.05 (1.645), power 0.80 (0.842). sigma_c = 0.0139 per game (93.3: SE of the engine-vs-Gaussian-twin Brier difference × sqrt(7,230 games)); this is the nearest measured paired-Brier spread we have, **approximate** — there are no settled engine-vs-market games yet. delta = 0.002 Brier (the smallest advantage that gives w >= 0.01 at a market Brier near 0.20). **Judged n = 300 games** (full effect). A PASS call uses the **half-effect n: delta = 0.001 -> 1,200 games** (a winner's-curse haircut; the engine was tuned on the same seasons it is described on).
Reachable: ~1,230 games/season, 82% archive coverage assumed -> 300 games about 2027-01-15; 1,200 games not before the 2026-27 regular-season end (~2027-04-15), and then only if coverage holds (unverified).

## Pass rule
Per family, at the look: game-clustered 95% upper bound of mean d < 0 (engine better than market) **and** w >= 0.01, at n >= 1,200 games. Otherwise FAIL (n reached, interval includes or exceeds zero) or UNDECIDED (n not reached). No PASS on a point estimate. A family whose interval lies wholly above zero (engine worse) is FAIL-WORSE and the engine is not given weight there.
**Look dates:** descriptive checkpoint **2027-01-31** (sign and interval, no verdict, no status change); verdict look **2027-04-20** (or the first date >= 1,200 settled games).

## Modal outcome, stated before the data
Most likely **UNDECIDED at the checkpoint and FAIL or UNDECIDED at the verdict look** for moneyline and spread: the market is the benchmark, the engine has a documented moneyline over-confidence, a home lean and early-season ratings that are mostly the prior mean. Total and team-total are where a positive result is most plausible (slopes 0.99–1.06 in 93.3). Expected d: ML and spread positive (engine worse), total and team total near zero. A w of exactly 0 for the moneyline is the expected result and is informative, not a failure.

## Not in scope
v2 (the availability / altitude / officials / lineup factors, estimated score correlation, a train-only calibration step) is **EXP-044b**, frozen separately before its first row. Any change to v1 after the freeze is a new EXP. Registered runner install waits for a GREEN `budget_read`.
