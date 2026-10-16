# NFL engine scaffold — PLAN (frozen before any fit)

**EXPLORATORY. Never a verdict.** Written 2026-10-14 (W73.3, T-950) BEFORE any engine fit or score. Pillar DEPTH, measure **D4** (NFL, scaffold stage). Charter rules 1-8 bind; writes only via `_fence.safe_out`. Deviations go in a dated section at the bottom, never as edits above.

## 1. Model class — chosen and why
**Possession-level Monte Carlo** (not a bivariate score model, not yet drive/play-level).
- Why not a bivariate discrete-score model (e.g. bivariate Poisson): football scoring is under-dispersed vs Poisson (11 bounded possessions each; margin SD 13.2 vs ~16 for compound-Poisson with the same means), and it carries no event structure — nothing for props/parlays/live to read. It would price three markets and stop.
- Why not drive-by-drive with field position: needs play-by-play features this block does not have (73.2 builds them); building it now would invent parameters the data cannot identify.
- Possession model: per team, N possessions (`N = max(6, round(N0 + s_N·z_pace + 1.0·z_team))`, z_pace shared, N0 = 11.0 fixed a priori), each ends TD (prob p_td) / FG (p_fg = r·p_td) / nothing; TD worth 7 (0.93) / 6 (0.04) / 8 (0.03) — fixed a priori; regulation tie → OT module (each team one possession, then up to 2 alternating sudden-death possessions, FG counts, else tie).
- Mean mapping: team regulation mean μ → `p_td = (μ/N0)/(6.99 + 3r)`, `p_fg = r·p_td` (cap p_td ≤ 0.55). Mean points are NOT re-fit by the engine: they come from the same ridge-on-margin/total as the frozen arm (below), so the comparison is on **equal inputs**.
- OT mean correction δ: one deterministic simulation at league-average μ with vs without OT gives the OT total-points add-on; regulation μ is reduced by δ/2 per team so sim mean total = ridge mean total.

## 2. Inputs (equal to the frozen arms)
- **Arm A** inputs: the 11 frozen features (`nfl_pregame_features.FEATURE_NAMES`). Comparator: `frozen` Gaussian (ridge λ=100 on margin and on total, probit-Platt on margin/σ_margin from cal season, σ_total and ρ from cal-season residuals).
- **Arm B** inputs: the 13 W64.1 `full` features (EB-shrunk team rates + projected-starter QB EPA). Comparator: `full` Gaussian, same recipe.
- Engine arms `engA`, `engB` use the SAME means (μ_margin Platt-calibrated, μ_total) as their comparator. Only the distribution shape/discreteness differs. Anything better must come from shape, which is what the scaffold claims.

## 3. Shape parameters (2) — fitted on training/cal data only, never on test seasons
`r` (FG:TD ratio) and `s_N` (shared-pace SD), by deterministic grid (r ∈ {0.30,0.40,…,1.00}, s_N ∈ {0,0.5,…,3.0}) minimizing squared error of (sim SD of margin, sim SD of total) vs the cal-season (T-1) out-of-sample residual SDs of the ridge means. Common random numbers (fixed seed) across the grid. This mirrors how the frozen model sets σ from cal residuals — same information, no test leakage.

## 4. Evaluation — rolling origin identical to W64.1
Test seasons T ∈ 2019..2025 (REG, scores final), ridge on ≤T−2, calibration/shape on T−1, score T. n ≈ 1852 games. 2026 outcomes, ledgers, shadow rows never read. `frozen` arm for T=2025 must reproduce W64.1's 0.21854 (sanity check, run first).
- **Simulation size** 40,000 draws/game, seed = hash(game_id) (MC Brier inflation ≈ p(1−p)/n_sim ≈ 5e-6, negligible vs deltas; reported).
- **Ladders (paired, identical strikes for both models):** center c = floor(μ_frozen)+0.5 for margin, total, home pts, away pts (μ_frozen = the comparator's mean; a stand-in for a market line, which the pre-2026 history does not hold for these families); strikes c+{−7,−3,0,+3,+7}.
- **Metrics per family (ML, spread, total, team total):** Brier on every ladder strike pooled; ΔBrier engine − Gaussian by game-cluster bootstrap (B=2000, seed 20261014; 95% CI); per-season Δ; calibration (10-bin reliability + slope/intercept of logit(outcome) on logit(p)); log-loss secondary. ML = home win, ties 0.5.
- **Key-number check (the shape claim):** on spread strikes at ±2.5/3.5 and ±6.5/7.5 residual calibration, i.e. Brier on strikes adjacent to 3 and 7 vs elsewhere, per model.
- **Joint check (what a single-model-per-family stack cannot do):** parlay legs "home covers c_m AND total over c_t" — engine from the same draws; Gaussian from the bivariate normal with the frozen ρ. Brier of the joint event, descriptive.
- **Internal-consistency assertions** (tests, all draws): total = home+away exactly; ladders monotone; P(ML) = P(cover −0.5) + ½P(tie); engine and Gaussian implied P(win) vs P(cover 0) difference reported (zero for both by construction — stated, not claimed as a win).
- **Market comparison (reported, never judged):** 2025-season KXNFLGAME moneyline mid at kickoff−30min where the archive has it, same construction as W64.1; model-vs-mid Brier, n≈180, MDE ≈0.04 Brier per W62.2. Spread/total/team-total mids are not in the archive for 2025 → "none exists".

## 5. Decision rule (frozen)
The scaffold "matches or beats" a comparator on a family iff the upper 95% limit of ΔBrier (engine − Gaussian) over that family's pooled strikes is < +0.0010 (non-inferiority margin, ~⅓ of the QB challenger's effect size) — and "beats" iff the upper limit < 0. Otherwise NO, said plainly. Multiplicity: 4 families × 2 arms = 8 comparisons, reported with 95% CIs and flagged descriptive; no Bonferroni claim of superiority is made. A NO is a result.

## 6. Non-goals
No registry, runner, ledger, cron, order, sizing or model-artifact change. No drive/play data. No weather/officials/coverage (73.2 / Wave 74). Nothing here graduates to evidence except via a new accepted pre-registration (Charter rule 7).

## Addendum 2026-10-15 (W75.2, T-990) — Stage 2: first factor class taken to APPLIED. Frozen BEFORE any stage-2 fit.

**Scope.** One factor class (F5/F6: coverage shell × offensive personnel; motion is carried by the builder but is not in the term — 2022+ only and direction is unavailable, GG-800). The deliverable is the chain aggregation → interpretation → application run once and reusable; the next class (e.g. pressure vs protection) plugs into `factors.FactorSpec` + `rate_layer.Factor`.

**Factor term (points for an offense O vs defense D, as of t).** `term = 62 · Σ_pers w_O(pers) · Σ_shell [ c_D(shell|pers) − l(shell|pers) ] · L(shell,pers)`, where `w_O(pers)` = O's shrunk personnel usage, `c_D(shell|pers)` = D's shrunk shell share given personnel (normalised), `l` = league shell share given personnel, `L` = league mean opponent-adjusted EPA/play in the cell. Rationale (Part A): shell share is a stable trait (split-half r 0.59–0.80), team-specific cell EPA is noise (YoY r ≈ 0.0–0.1), so the stable tendency is priced at stable league-wide cell payoffs. 62 = league plays per team-game (fixed a priori).

**Rate layer.** `mu_home += β·(term_H − term_A)`-equivalent: each team's mean points gets `β·term` (home: `β·term(H vs A)`, away: `β·term(A vs H)`); the engine, shape parameters (r, s_n, δ) and arm-B base means are otherwise identical to engine v0 arm B. β is ONE scalar, pooled OLS through the origin of team-points residual (actual − arm-B ridge prediction, split from margin/total predictions) on the term, over seasons 2019..T−1 (seasons ≤T−2 are in-sample for the ridge — stated; no test-season row enters). Never fitted on season T.

**Rolling origin.** Test seasons T ∈ 2020..2025 (term needs a prior participation season; 2018 is the first). Ridge/calibration/shape exactly as W73.3. 

**Arms.** C (PRIMARY, application-ready): tendencies from seasons ≤T−1 only (no in-season rows) — exactly the information state of 2026 under GAP-1. D (secondary, descriptive): seasons ≤T−1 plus current-season games with kickoff+4h ≤ as_of=gameday 00:00 UTC, recomputed weekly. Baseline for both: engine arm B.

**Metric and decision.** ΔBrier (C − B) pooled over each family's ladder strikes (ML, spread, total, team total; strikes centred on arm-B means, ±{0,3,7}, identical to W73.3), game-cluster bootstrap B=2000, seed 20261014, 95% CI. Decision per family: BEATS if upper < 0; MATCHES if upper < +0.0010; else NO. 4 families, descriptive, no superiority claim. Calibration (10-bin reliability, logit slope/intercept) reported for B and C. Market comparison: 2025 KXNFLGAME ML mids at kickoff−30min, reported, never judged.

**GAP-1 stated.** No 2026 participation file exists, so 2026 in-season tendencies cannot be computed. This alone does NOT block application this season: arm C uses prior-season tendencies only, which is what 2026 offers. It blocks only arm D's in-season refresh, and any 2026-season application of the term would also need the 2025 participation file to remain the store of record. Whether a 2026 file appears is outside this wave.

**Modal expectation (pre-fit).** The term moves means by a few tenths of a point; ΔBrier near 0; modal decision MATCHES on ML/spread, NO-or-MATCHES elsewhere. A NO is a result.

## Addendum 2026-10-15 (W76.2) — Stage 3: second factor class (F8 unit availability) to APPLIED. Frozen BEFORE any stage-3 fit.

**Factor and why it was chosen (Part A, `results_stage3.md`).** F8 = expected snap-weighted usual non-QB starters lost, by unit (OL, skill, DL, CB, back seven), from the final weekly injury report; Sunday/Monday games only (Thu/Fri/Sat → None = league average). Orthogonality measured pre-fit: R² of the term on all rating-layer inputs 1.3%, max |r| 0.10. QB is excluded (already in arm B).

**Term.** `points(offense O vs defense D) = Σ_u coef_u · (lost_u − center_u)` over O's own OL, SK and D's DL, CB, BK. `lost_u = Σ_players share · P(absent | status)`; `share` = mean snap pct of the player's last ≤6 appearances (≥3, ≤400 days, ≥0.40, kickoff+4h rule); `P(absent|status)` from seasons ≤ T−1 flagged starters with snap data. Coefficients and centers: centered ridge (λ=50, five unit columns) of team-points residual (actual − uncalibrated arm-B ridge team mean) on the unit-loss columns, over sides in seasons 2019..T−1 with a usable report (seasons ≤T−2 are in-sample for the ridge — stated; no season-T row enters). Because the coefficients are in points, β = 1 (no second scalar).

**Rate layer.** Each team's mean points gets `+ term` (None → 0); engine, shape (r, s_n, δ), Platt means identical to v0 arm B.

**Rolling origin.** T ∈ 2020..2025 (1,612 games), ridge ≤T−2, Platt/shape on T−1, score T. Identical to W75.2.

**Arms.** B = engine v0 arm B. C = B + F5/F6 (stage-2 primary, prior-season tendencies, β refit exactly as stage 2). E = B + F8. F = C + F8 (same F8 term as E).

**Metric and decision.** ΔBrier per family (ML, spread, total, team total; ladders centred on arm-B means, ±{0,3,7}) for **E − B** and **F − C** (i.e. vs v0 and vs v0 + F5/F6), game-cluster bootstrap B=2000, seed 20261014, 95% CI; BEATS if upper < 0, MATCHES if upper < +0.0010, else NO. Team totals are one of the four families and are reported on their own line and never pooled into another family. All one simulation per game per arm (all families priced from the same draws). Per-season Δ and calibration (logit slope/intercept) reported. 8 comparisons, descriptive, no superiority claim. Stage reported per ADR-0075: aggregated / interpreted / applied (applied = the term was run through the rate layer and measured here; "applied" is not "adds value").

**Market comparison (reported, never judged).** 2025 KXNFLGAME ML mids at kickoff−30min where archived, arms B/C/E/F vs mid.

**Modal expectation (pre-fit).** Term SD ≈ 0.56 points; defense-unit coefficients unstable by season; ΔBrier ≈ 0; modal MATCHES on ML/spread/total, possible NO on team totals if the coefficient noise inflates. A NO is a result.

**Non-goals.** No registry, runner, ledger, cron, order, sizing or model-artifact change; no running component.
