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
