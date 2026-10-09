# EXP-039 (W64.3) — NBA player-points pre-game shadow: pre-registration of 3 cells (2026-10-09)

**Status: written and pushed BEFORE any player-points model, forecast, shadow row or cron line exists.** Committed alone. The model artifact (Part B)
is trained once after this file is on `main`; its sha256 goes in an addendum, as in EXP-038. Structure mirrors `EXP038_NBA_PREGAME_SHADOW_PREREGISTRATION_2026-10-06.md`.

Directive in force (operator, 2026-10-08): start more evidence clocks, least-efficient families first. Authority: AUTHORIZATION - STANDING: NEW PRE-REGISTERED SHADOW
ARMS (ACTIVE_QUEUE.md). Shadow only: no order, position, stake or `kelly_fraction` (ADR-0048 sizing zero stands).

## 1. Cells (3) and what the survey found
`NBA_PLAYER_POINTS` × `T1` (12–48 h), `T2` (4–8 h), `T3` (15–60 min) before tip-off. Series `KXNBAPTS` (public read-only GETs, 2026-10-09). T4/T5 stay out of scope (registry T4 cell DARK).

Measured listing reality, fixed now (3 finalized events: 2026-10-05 NYK-PHI, 2026-10-08 BOS-CLE, 2026-10-08 PHI-BKN):
- **Two players per game**, four strikes each (10+, 15+, 20+, 25+) = 8 markets/game. Not a full-roster board.
- **Listed late:** markets opened ~6.3 h before tip (both 10-08 events) and ~14 h before tip (10-05 event). **T1 (≥12 h) will accrue few or no rows; T2 is the natural band.**
  T1 is judged on whatever n it reaches (§4); it is not padded.
- Settlement: points recorded in the game; a player who is inactive or never takes the court settles to a **fair price (scalar)** — excluded from scoring and counted separately (`dnp_scalar`).
  Postponed >48 h or cancelled → fair price, also excluded.
- Settlement source is the governing league / ESPN; the contract is `BASKETBALLENTITYSTAT`.
Expected volume at full season: ~1,230 games × 2 players ≈ 2,460 player-games, fewer in T1. A sparse board is a fact about the venue, not a defect to be fixed by inference.

## 2. Model decision (made with evidence): the legacy model cannot be used unchanged — retrain, new frozen artifact
Read from `models/prod_model_meta.json` and `train_and_save_model.py` (artifact sha256 `2d9a869b05473c97806d118521fc60b8be4ae21f6a9b6327cac81a490040b60a`, local-only, gitignored):
legacy = LR + Platt, 78 features (31 quantitative + 47 qualitative PRF), 12,748 training rows from 5 seasons through 2025-26, snapshot `SNAP-2026-05-28-002`.
Three reasons it is not fit to log unchanged:
1. **Wrong target.** Its label is `pts ≥ the player's own 10-game rolling mean`. It does not output P(points ≥ 10/15/20/25), so it cannot price a single Kalshi strike. (The live NBA player-points book bridged this by thresholding elsewhere; that path is not carried over.)
2. **Weak and stale.** Held-out 2025-26 AUC 0.577, Brier 0.2476 vs 0.25 null (`EXP-005_test_evaluation.json`). The 47 qualitative features are a 2026-05-28 snapshot that cannot be refreshed point-in-time for 2026-27 rosters (e.g. Paul George now on BOS).
3. **Prior evidence is negative.** The 114 closed legacy positions: model worse than the market mid by mean Δ-Brier −0.044 (SD 0.153) (GG-037). A model that was anti-predictive at the strike level is not the thing to extend.

**Chosen: a new frozen model, trained once before any 2026-27 row, never touched again (Hard Rule 4).**
- **Class:** one points distribution per player-game (negative binomial: ridge-linear mean from the features below, dispersion fixed on the calibration season); every strike (10/15/20/25) is read off that one
  distribution so strikes are coherent (monotone in the threshold); then a single Platt (a, b) on the logit, fit on the calibration season. Ridge λ fixed a priori at 100. ADR standing: same open question as EXP-038 §2
  (ADR-0070 covers the 12 EXP-037 NFL cells only) — **operator decision required before rows are read as anything but research.** This file does not edit ADR-0070.
- **Features (all point-in-time, from box scores):** player rolling points mean over 10 and 30 games (crossing seasons), rolling minutes mean over 10, rolling FGA mean over 10, season-to-date points mean, games played prior,
  home flag, days rest and back-to-back, opponent defensive rating over the last 10 games. **A player needs ≥ 10 prior games or no row is produced.**
- **D1 factor classes declared** (`scripts/distance_to_optimum_d1_manifest.json`, entry `nba_player_points_v1`): **personnel** (player's own rolling form/minutes/usage), **team** (opponent defense, rest), **venue** (home).
  **Not used (gaps, not silent drops):** qualitative PRF factors, injuries/availability/lineup, matchup-specific defender data, travel, any market price. Availability is the largest known weakness (§7).
- **Training data:** NBA box scores through the 2025-26 season, pulled off-box and frozen to a file before fitting. **Split fixed now:** train through 2023-24, calibrate on 2024-25, **held-out 2025-26 reported only, never used for any choice**;
  the shipped artifact is the train+calibrate fit (same convention as EXP-038 D1). Regular-season games only. The held-out report holds climatology-relative numbers only; the market comparison waits for live rows.
- **Population caveat stated in advance:** the training set is box-score rows for players who appear on Kalshi's two-per-game board, i.e. stars. If the available history is a narrower player set than that, it is reported, not hidden.

## 3. Definitions fixed now
Scoring unit = FIRST ledger row per (market_ticker, band); y = 1 if recorded points ≥ strike (settled result), scalar/fair-price settlements excluded.
`delta_brier_vs_X = Brier(X) − Brier(model)`, positive = model better; X = market mid at entry, or strike-specific climatology (training seasons).
**Cluster = the game** (both players, all four strikes, are one cluster). Game-cluster bootstrap, B = 2000, **seed 20261009**, two-sided 95% percentile CI.
E_net at entry under both fee candidates (k007 = 0.07·q(1−q), ADR-0016; kmult = 0.035·q(1−q), inferred, GG-332).
**Judged n = settled player-games with ≥1 scored row in the cell**; the number of distinct games is reported beside it.
Preseason (labelled `season_phase=preseason`, `excluded_from_judged_n=true`) goes to `exp_output/PREGAME_SHADOW_PRESEASON/` and is never in any judged ledger or any test below. Regular season begins 2026-10-20.

## 4. Expectations and power (stated, not tuned)
Per cell: **Δ-Brier vs climatology > 0; Δ-Brier vs market ≤ 0.** Props are less efficient than game markets, so the edge hypothesis is less implausible here than in EXP-038 — but the only direct evidence (legacy book, Δ −0.044) points the wrong way and the model has no availability data.
Expected Δ vs market, by band: **T1 −0.02 to +0.01, T2 −0.03 to 0.00, T3 −0.04 to −0.01** (the market absorbs inactive/load-managed news by tip-off; the feature row does not). Modal first-look outcome: SHADOW (CI spans zero) or negative. Δ non-increasing T1 → T2 → T3.
Cells sharing a game are not independent evidence and are never pooled.
- Per-row Brier-difference SD is **0.153**, taken from the legacy book (n = 114 closed positions, 3 game dates) — a thin, single-regime estimate, not a measured long-run value; the realised SD is reported with every result. MDE (80% power, α = 0.05) = 2.8·SD/√n.
- **First look: judged n = 300 player-games per cell, MDE ≈ 0.025.** (Roughly 150 games' worth, about 3 weeks into the season for T2/T3.) **Second look: judged n = 800 or 2027-01-31, whichever first, MDE ≈ 0.015.**
  The first-look MDE exceeds every effect the expectations allow, so the first look is mostly a check for a large negative result and for pipeline health. T1 will probably not reach 300 and is judged on what it reaches.
- No scoring before a cell reaches its judged n; between looks only row and settled-game counts are inspected. One second look; no third without a new pre-registration.

## 5. Decision rules (fixed now)
1. **RULED_OUT** — Δ-vs-market < 0 with the game-cluster 95% CI upper bound < 0 at the judged n → `RULED_OUT` with `reason` and `measured_date` via `promote_cell_status` (ADR-0056).
2. **SHADOW** — CI spans zero → stay SHADOW to the second look; still spans zero after it → UNRESOLVED, never decided by judgement.
3. **CANDIDATE-PENDING-CAPACITY** — Δ-vs-market > 0, CI lower bound > 0, AND mean E_net at entry > 0 under both fee candidates → a sizing question only; authorises no order or `kelly_fraction`.
Δ > 0 with E_net ≤ 0 under either fee candidate is SHADOW. Δ-vs-climatology ≤ 0 at the judged n is reported separately as a model failure.

## 6. Registry and wiring commitments
The three cells flip NOT_IMPLEMENTED → SHADOW **only after this file is on `main` and the frozen artifact exists**, and only when a first valid regular-season-or-preseason row path is proven on the VPS. New cron lines only (standing authorization), staggered off :00/:30 and the minutes already used, mirrored in `deploy/`. No existing cron line is edited.

## 7. Known weaknesses stated in advance
- No availability/injury/rest-management information; for two-star boards a single scratch moves a market by several points. Expect the model to lose most where that matters.
- Two players per game means a few high-usage stars dominate n; the result is about star points, not about player points in general.
- Negative-binomial dispersion is fixed per fit; late-game blowout minute cuts are not modelled.
- Early-season rolling windows are thin (≥ 10 prior games rule; the 2025-26 tail supplies history).
- Preseason distribution shift (starters play little) — the reason preseason is excluded.
- The ADR standing question in §2 is unresolved until the operator decides.

## 8. Nothing else
No order, position, paper fill or sizing change follows from any outcome of this file. SHADOW is evaluate-and-log.
