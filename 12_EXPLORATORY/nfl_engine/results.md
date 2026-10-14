# NFL engine scaffold — results (W73.3 Part B)

**EXPLORATORY. Not a verdict.** Plan frozen in `PLAN.md` before any fit; no deviations. Data: nflverse pre-2026 only; rolling origin T=2019..2025, n=1852 games, 40,000 sims/game, engine arms vs same-mean Gaussian comparators. Raw: `results.json`; code: `engine.py`, `study.py`, `test_engine.py` (7 pass).

**Sanity:** frozen Gaussian ML Brier on 2025 = 0.21854 — reproduces W64.1 exactly. Consistency: 0 sum-identity violations, 0 monotone-ladder violations in 3,704 game-arm sims; P(ML) = P(cover −0.5) − ½P(tie) to 1e-16. Sim OT rate 3.6% (real NFL ≈ 3–4%), tie rate 0.2%.

## ΔBrier = engine − Gaussian (95% game-cluster bootstrap; negative = engine better)
| Arm | Family | Δ | 95% CI | Rule (hi<+0.0010 matches; hi<0 beats) |
|---|---|---:|---|---|
| A (11 frozen feats) | ML | +0.00014 | [−0.00017, +0.00046] | MATCHES |
| A | spread | +0.00016 | [−0.00012, +0.00044] | MATCHES |
| A | total | −0.00045 | [−0.00102, +0.00012] | MATCHES |
| A | team total | +0.00009 | [−0.00042, +0.00059] | MATCHES |
| B (13 `full` feats) | ML | +0.00006 | [−0.00025, +0.00037] | MATCHES |
| B | spread | +0.00033 | [+0.00007, +0.00061] | MATCHES |
| B | total | −0.00048 | [−0.00106, +0.00010] | MATCHES |
| B | team total | −0.00010 | [−0.00064, +0.00043] | MATCHES |

**Reading:** one possession-level simulation prices ML, spread, total and team totals from the same draws and is statistically indistinguishable from four separately-modelled Gaussians (all 8 within the +0.0010 non-inferiority margin; none beats). 8 comparisons, descriptive, no superiority claim.

## What did NOT work (said plainly)
- **Key-number shape claim: NOT supported.** On spread strikes at ±2.5/3.5/6.5/7.5 the engine is slightly *worse* than the Gaussian (A +0.00031 [+0.00005, +0.00056]; B +0.00033 [+0.00007, +0.00058]), and equally worse elsewhere (+0.0003). The discreteness the engine produces is real (tests show 3/7 mass) but at this shape-fit it does not pay in Brier on game-level ladders.
- **Joint (margin>c AND total>c) check:** engine vs bivariate-normal Δ +0.00011 (A, CI spans 0) and +0.00040 [−0.00021, +0.00105] (B). No advantage shown; descriptive only. (Reliability slope on a single-strike joint is not meaningful.)
- Shape fit is unstable across seasons (r 0.7–1.0, s_N 0–1.0): the 2 shape parameters are poorly identified by one calibration season's two residual SDs.
- Engine totals calibration intercept is better than Gaussian (−0.035 vs −0.099 A) — suggestive, not tested.

## Market comparison (reported, never judged)
2025 KXNFLGAME ML mid at kickoff−30min, n=254 (MDE ≈ 0.04 Brier): Brier gaussA 0.2223 / engA 0.2221 / gaussB 0.2269 / engB 0.2266 / mid 0.2132. Model−mid: engA +0.0089 [−0.0044, +0.0222]; engB +0.0134 [+0.0002, +0.0263]. Same picture as W64.1: the mid is at least as good. Spread/total/team-total mids: none exist in the archive.

## D4 line — NFL
**D4 (NFL, scaffold stage): 0 → 1.** A single simulation engine now prices ML/spread/total/team totals/parlay joints from one joint distribution with the pricing API in `02_ARCHITECTURE_DESIGN/NFL_ENGINE/INTERFACE.md`, at parity (non-inferior, not better) with the frozen per-family models on equal inputs. This is scaffold evidence: **no edge claim, no accuracy gain**; the value is extensibility (event layer for props/live, Wave 73.2/74 inputs). Source: this file / `results.json`, 2026-10-14.

## Limits
Equal-input design means only shape can differ; ladder centres are model means, not market lines; the frozen model was already internally coherent, so "consistency" is a property gained for new markets (props/parlays), not a fix. 2026 outcomes not read.
