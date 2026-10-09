# NFL deep challenger: QB-shrunk performance + early-season EB shrinkage (W64.1, T-772)

**EXPLORATORY. Never a verdict. Pillar: DEPTH. Measures: D1 (nfl_pregame team -> team+personnel), D3 (0 -> 1 if and only if Part B beats the frozen model).**
**Frozen BEFORE any fitting (Part A, 2026-10-09).** Anything not written here is not allowed to influence the verdict; deviations go in a dated
"Deviations" section at the bottom, never as edits above.

## 1. Challenger = frozen EXP-037 NFL recipe + two mechanisms (from `NFL_TRANSLATION_MAP.md` ranks 1 and 2)
Base (identical in both arms): the 11 frozen features (`nfl_pregame_features.FEATURE_NAMES`), ridge lambda=100 on home margin, probit-Platt on
margin/sigma, sigma = std of cal-season residuals (ddof=1), exactly the recipe in `20261009_nfl_rolling_origin/study.py`. Frozen arm = that recipe, nothing else.

**Mechanism 1 - starting-QB shrunk performance (analogue of the MLB game model's starting-pitcher shrunk runs-allowed).** Two added features per game:
`qb_epa_h`, `qb_epa_a`. For team T at game g with as-of date d (the game date; every source row must have gameday < d):
- projected starter q = actual starter of T's most recent completed prior game (strictly earlier gameday). This is point-in-time legal. The
  actual starter of g itself is **never** used in the primary arm (nflverse QB ids are the post-hoc starter; a late scratch would leak).
- x_i = off_epa of the team in each game q started (any team, any season) with gameday < d; take q's last N=16 starts.
- `qb_epa = (sum x_i + k*mu) / (n + k)`, n = number of those starts (0..16), **k = 6**, mu = league mean team-game off_epa over all team-games
  with gameday < d. Why k=6: single-game team EPA noise (SD ~0.2) is several times the between-QB talent spread (SD ~0.08), a noise/talent
  variance ratio of roughly 4-8; 6 is the middle, chosen a priori, **not tuned**. N=16 ~ one season of starts.
- No projected starter (first-ever game / missing id) -> n=0 -> qb_epa = mu.
A new QB (rookie, backup, transfer) arrives with n small and is pulled to mu: the personnel change the team-only features cannot see.

**Mechanism 2 - early-season empirical-Bayes shrinkage of team rates.** The 8 team-rate features (off_epa, def_epa, pf, pa; h/a) are replaced by
`(sum w_i x_i + K*mu) / (sum w_i + K)` over the **same** window the frozen builder uses (last 8 prior games, decay 0.85 weights w_i), **K = 2**
weight-units, mu = league mean of that quantity over all team-games with gameday < d. Why K=2: sum(w) is 4.7 at a full window and 2.6 at the
3-game minimum, so K=2 shrinks the thin early-season windows hard and a full window ~30%; below the noise-ratio-implied value deliberately
(the weights are already decayed). **Not tuned.** Same sample of games as the frozen builder (rows where it returns None are dropped from every arm).

Mechanism 3 (injury report, QB-only) is **not** included: its point-in-time filter is not proven on this data (`injuries_YYYY.csv date_modified`
is not in the local cache, and nflverse injury rows are rolling snapshots). It stays a named next mechanism, not part of this challenger.

## 2. Arms (all fitted by the same code path)
- `frozen`: 11 features.  - `full` (**the challenger**): 11 team features EB-shrunk (M2) + qb_epa_h, qb_epa_a (M1) = 13 features.
- Decompositions (descriptive, counted in multiplicity): `qb_only` (11 frozen + 2 QB), `eb_only` (11 EB-shrunk).
- Sensitivity, **flagged upper bound, not decision-bearing, counted in multiplicity**: `full_oracle` = `full` but QB = the actual starter of g
  (the QB-change information a perfect pre-kickoff projection would have).

## 3. Evaluation (frozen)
Rolling origin: test season T in 2019..2025 (7 seasons, REG season only); ridge on 2015..T-2, Platt+sigma on T-1, score T. For T=2025 this is
exactly the frozen artifact's recipe (train 2015-23, cal 2024); a check that the `frozen` arm reproduces W61.3's 2025 Brier 0.2185 is run first.
No season is untouched: 2019-2023 were used by W61.3's rolling origin, 2024 is the frozen model's calibration season, 2025 its held-out. Reuse is
disclosed; it does not leak because **neither mechanism was chosen by looking at any of those seasons' outcomes** (both were chosen by the
translation map, before this code existed). 2026 outcomes, rows and ledgers are never read.
Metric: Brier of home-win probability (ties 0.5). Primary statistic: `full` minus `frozen`, pooled over 2019-2025, game-level bootstrap
(B=2000, seed 20261009). Also per-season deltas and the count of seasons where `full` is better.

**Multiplicity.** Challengers already tested against the frozen model on these seasons (counted from `12_EXPLORATORY`): recal (2025), lambda 30,
lambda 300, dome flag (2019-23) = **4**. This study adds `full`, `qb_only`, `eb_only`, `full_oracle` = 4. **m = 8**, Bonferroni
alpha = 0.05/8 = 0.00625 two-sided, so the decision interval is the **99.375% bootstrap CI** (percentiles 0.3125 / 99.6875).
**Verdict rule:** `full` "beats the frozen model" iff the upper limit of that CI for (full - frozen) is < 0 **and** `full` is better in >= 5 of 7 seasons.
Otherwise: no improvement, said plainly, scoped to this feature set and these seasons.
Market comparison (Part B step 3): 2025-season KXNFLGAME moneyline mid at kickoff-30min, same construction as W61.3 (ask/bid close, <=1h
stale), model vs mid Brier with the same bootstrap; descriptive only (n~180, MDE ~0.04 Brier per W62.2).

## 4. Rules
Charter rules 1-8 bind. Writes only via `_fence.safe_out`. Feature code lives in `qb_features.py` in this directory; tests in `test_qb_features.py`
fail on look-ahead (future-dated rows, current-game starter use, and k=0/K=0 must reproduce the frozen builder).
