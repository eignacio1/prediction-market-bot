# EXP-030 results — T4M-PROJ structure enhancer (T-598, GG-320)

Pre-registration: `05_RESEARCH_EXPERIMENTS/EXP030_T4_STRUCTURE_PREREGISTRATION_2026-09-30.md` (pushed before any fit). Nothing in it was changed after seeing results.

## Verdict: NO DETECTABLE DIFFERENCE (harness verdict INCONCLUSIVE)

Sealed holdout, 2026-07-25..07-30, 40 games, 5,658 rows, `run_gate` from T-583 unmodified and called once:

| Metric (positive = candidate better) | Mean | 95% CI (game-clustered) |
|---|---|---|
| Brier gain over incumbent | -0.0063 | [-0.0203, +0.0091] |
| Log-loss gain over incumbent | -0.0185 | [-0.0512, +0.0173] |

The interval spans zero. The point estimate favours the incumbent, but the data cannot distinguish the two. Candidate differed from incumbent on 40 of 40 test games, so the power floor was met.

## Validation and permutation control (train 07-18..07-21, 47 games; validation 07-22..07-24, 20 games)
- Validation Brier gain by C: 0.01 = -0.0042, 0.1 = -0.0038, 1.0 = -0.0036. Chosen C = 1.0 (least negative). Every setting was worse than the incumbent.
- Permutation control (200 shuffles): real validation gain -0.0036 vs permuted 95th percentile +0.0125. Control NOT passed. 95.5% of shuffled fits scored at least as well as the real one, so the fitted structure did not transfer even relative to fitting noise. This is a statement about this shallow candidate on this window.

## What this does and does not say (GG-320 only)
- The three-scalar binomial was not beaten by a residual model over batting slot, inning, h_needed, ab_remaining, shrunk batting average and batter home/away.
- It does NOT say a deeper tree fails. Matchup, venue, weather and game-state inputs were absent from this candidate (game state is logged on 0.9% of rows, GG-323; park and weather are not in the cycle log).
- It does NOT support or oppose rebanding, deactivating or resizing T4M-PROJ. The population is 13 July days, ledgered-cohort tickers excluded, so it is not the traded population.
- No ADR proposed (bar not cleared).

## Refusals encountered
None from the harness on the run. Pre-flight facts that shaped the design are in GG-323: epoch-12 label refusal made the clean window end 2026-07-30; September cycle rows have no decoupled outcomes.

## Provenance
Cycle log copy sha256 `440df62ca9c5d95e2a7d76fbce22d63939d1a770cf347a38229ab831ae0b66a4`. Code: `src/prediction_market_bot/c3_forecasting/t4_structure_model.py`, `scripts/run_exp030_t4_structure.py`, tests `tests/test_t4_structure_model.py`. Incumbent `p_hits_gte_threshold` untouched.
