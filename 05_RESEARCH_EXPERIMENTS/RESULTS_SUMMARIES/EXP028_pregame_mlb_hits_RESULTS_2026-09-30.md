# EXP-028 — Pre-game MLB hit-prop model — RESULTS (T-594)

Pre-registration: `EXP028_pregame_mlb_hits_PREREGISTRATION_2026-09-30.md`, pushed alone as commit `90e96c2` before any fit. Nothing in it was changed afterward. Raw output: `exp_output/EXP-028/{validation,holdout}_results.json`. Holdout scored once (`HOLDOUT_TOUCHED.lock` blocks a second run).

## Headline
**Skill over climatology is detected. Edge over the market is NOT TESTABLE on this substrate and is not established.** Nothing here supports sizing, activation or a band assignment.

## D0 — predecessors / substrate
* Matrix: shared-tree copy (not regenerated), sha256 `b2a845a6…9114a4` verified against the pre-registration, 132,184 × 45.
* `bfd4c4d` (40.3) is on no branch of `origin`; it lives only in the provenance-allowlist worktree. Not landed, not duplicated — 41.1's job. This experiment does not depend on it.

## D1 — what the matrix is
One row = one batter-game, 861 players / 6,318 games. Serves **only the player-hits (KXMLBHIT ≥1) family**; no team scores or lineup slots, so no moneyline / spread / total / team-total. **It has no market prices, and the priced archive (2026-08-01→09-30) starts after the matrix ends (2026-07-17): overlap = 0 rows.** Details in the pre-registration §1.

## D3/D4 — pre-registered claims, line by line (holdout 2026-01-01→07-17, 27,732 rows, 1,414 games; C=10 from validation)

| # | predicted | measured | verdict |
|---|---|---|---|
| P1 | DEFENSIBLE_IMPROVEMENT vs climatology | ΔBrier +0.00520 [0.00438, 0.00601]; Δlog-loss +0.01065 [0.00898, 0.01243] | **HIT** |
| P2 | ΔBrier in (+0.002, +0.012) | +0.00520 | **HIT** |
| P3 | vs B1 (shrunk-BA binomial): no difference, or gain <25 % of P2 | ΔBrier +0.00364 [0.00293, 0.00435] (70 % of P2); DEFENSIBLE_IMPROVEMENT | **MISS** — the multi-feature tree adds detectably over the one-line rule |
| P4 | backward placebo retains ≥50 % of forward gain | +0.00846 [0.00766, 0.00927] (163 % of forward) | **HIT** (per §8.1 ⇒ gain is time-symmetric persistent skill, not evidence of forward-specific information) |
| P5 | permutation-null CI contains 0 | ΔBrier −0.00030 [−0.00040, −0.00020] | **FAIL (literal criterion)** — see below |
| P6 | market comparison NOT TESTABLE | overlap 0 rows | **HIT** |

Validation (train 2024 → 2025): model Brier 0.23838 vs climatology 0.24322 (Δ ≈ +0.0048); C grid differs by ~1e-6, so the C choice is immaterial. Absolute holdout Brier: model 0.23920, climatology 0.24440 (descriptive only — population is selected on `ab ≥ 1`, §3).

## Things that qualify the headline
1. **P5 failed its literal criterion.** §8.2 says a CI excluding 0 voids all results. The delta is small and *negative*: a model fit on shuffled labels does slightly worse than a constant, the ordinary cost of fitting noise. A leak would push it positive, so the sign argues against leakage — but the pre-registered wording was two-sided and I did not relax it. Read every number above as **void-flagged under the literal rule, with a stated diagnosis that it is a mis-specified control rather than a leak.** Implementation note, fixed before seeing results: the control was run train→validation (never on the holdout) because a permuted-label holdout score would have been a second touch.
2. **The placebo exceeded the forward gain.** Likely partly mechanical: `y_backward` is taken from the player's sequence before the `ab ≥ 1` filter (games with `ab = 0` count as 0), and `ab_l10_mean` (the largest coefficient, +0.20) predicts playing time. So the placebo is contaminated by the playing-time selection and I do not claim a magnitude from it. Per §8.1 the *interpretation* stands: what the model learned is largely persistent, time-symmetric skill/role — precisely what a market prices.
3. **`ab_l10_mean` is doing the most work** (role proxy), with the `ab ≥ 1` look-ahead in the population (§3). Part of the "skill" is predicting who bats a lot, which a KXMLBHIT market conditions on by construction (the market exists only for lineup members).
4. **Holdout is not virgin data** (prior sessions saw 2026 aggregates; same window as T-183's TEST label). No choice here was made on it.
5. Factor classes not populated: qualitative (all), matchup platoon/lineup/bullpen, external weather/travel/umpire/park, own-team strength.

## Is there a deep pre-game tree that beats the market, and at what n?
Not answerable from this data, and this experiment does not answer it: the matrix that carries the features has no prices, and the priced window has no features, so the decisive comparison (B2) was never run. What is shown is that a 16-feature logistic tree beats climatology by ~0.005 Brier and beats a one-line shrunk-BA rule by ~0.004, on ~28k rows / 1,414 games — but most of that is probably persistent skill and role that a market already prices, and the failed permutation control keeps even that at "detected, with a caveat". The cheapest next step is to extend the matrix over 2026-08-01→09-30 with `scripts/generate_mlb_features.py`, join to the price archive by real ticker, and run T-583 `run_gate` unmodified against the market's `p_incumbent` with this frozen model (also the first genuinely unseen holdout). Required n for a market edge is unknown until a market-relative delta and variance exist; do not quote a figure. A clean answer on edge is still pending; the answer on skill is yes-with-caveats.

## Deviations (all disclosed above)
`run_gate` not invoked (input contract needs tickers/market prices that do not exist for matrix rows; a test asserts it refuses them); harness primitives imported instead. Permutation control run on train→validation. No second specification was run.
