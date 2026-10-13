# EXPLORATORY — W71.3 NBA game markets: personnel/availability challenger (PLAN, frozen before any fit)

**Status:** PLAN, committed before any fit. EXPLORATORY (CHARTER rule 6): nothing here is a verdict about any cell.
**Purpose (Hard Rule 12):** DEPTH **D1** (NBA games condition on team only → team + personnel) and **D3** (+1 only if a pre-registration is earned and the operator accepts it). Pillar: DEPTH.
**Scope:** `12_EXPLORATORY` only. No VPS, registry, runner, ledger, cron, stake or kelly change. No sealed-cell data read.

## 1. Question
Does adding point-in-time *minutes-weighted availability lost* per team to the frozen EXP-038 model (`nba_pregame_v1`, ridge λ=100 on 14 team-only features, probit-Platt margin calibration, bivariate Gaussian) improve out-of-sample Brier for the margin-derived families (moneyline, spread) and the total family?

## 2. Part A.1 — injury-report coverage across the GG-620 rename (measured)
PDFs were renamed 2025-12-22 (15-min grid, `_HH_30AM/PM`); the old URL 403s. `fetch_injury_v2.py` fetches the new URL from that date (114 date files, 2025-12-22 → 2026-04-14, 5 slots/day).
Share of regular-season games with a usable snapshot (`coverage.py`, `coverage.json`): **2026 season 33.9% → 96.4%**; by month before → after: Dec 61.6% → 96.5%, Jan 0% → 93.6%, Feb 0% → 95.2%, Mar 0% → 96.7%, Apr 0% → 97.9%. Earlier seasons (2023–2025) unchanged (≈95–99%). Injury reports and player box scores exist only from the 2022-23 season (`season=2023`); earlier seasons have no personnel data.

## 3. Feature (fixed)
Per team, per game: `out_min` = Σ over rotation teammates (played for that team within 21 days, ≥10 prior games) of their trailing-10-game minutes, for those listed **Out or Doubtful** in the snapshot. Snapshot = latest report on the game's ET date with slot ≤ tip − 4h (slots 11:30/13:30/15:30/17:30/19:30 ET); name match per `20261012_nba_points_minutes/features.py` (`snapshot`, `status_of`, `_recent`, `_team_candidates`, reused unchanged). No snapshot ⇒ `out_min = 0`, `inj_missing = 1` (per team-game, 2 flags).
Challenger columns (+5): `h_out_min`, `a_out_min`, `d_out_min = h − a`, `h_inj_missing`, `a_inj_missing`. Seasons < 2023 carry zeros and `inj_missing=1`, so the coefficients are identified by 2023+ rows only (stated limitation).

## 4. Arms / model class
- `ctrl_refit`: the 14 frozen features, same fit procedure as `scripts/train_nba_pregame.py` (ridge λ=100, margin & total means, Newton probit-Platt on the calibration season, residual sigma_margin/sigma_total/rho). **Integrity check:** fold A `ctrl_refit` must reproduce the frozen artifact's 2025 Brier to 4 dp, else the study is invalid and reported as such.
- `avail`: 14 + 5 columns, identical procedure, **λ=100 unchanged, no tuning**.

## 5. Splits (rolling origin, fixed)
- Fold A (= frozen split): train ≤2023, calibrate 2024, test **2025**.
- Fold B: train ≤2024, calibrate 2025, test **2026**.
Regular season only; games with fewer than MIN_GAMES prior games dropped exactly as the frozen builder does.

## 6. Families and strikes (fixed)
Outcomes scored are the same binary events the shadow cells use, derived from the model's Gaussian: moneyline (margin>0), spread and total families at strikes = control-arm mean rounded to the half-point plus offsets {−6,−3,0,+3,+6} (the strike grid is built from the **control** mean for both arms so both score identical events). Brier computed per event, per game, averaged per family.

## 7. Metric and statistics
ΔBrier = Brier(`avail`) − Brier(`ctrl_refit`) per family per fold (negative = better). Game-cluster bootstrap over games, seed 71303, B=20000, resampling the paired per-game difference. Multiplicity: m=3 families ⇒ **98.33% two-sided CI**. Also reported: pooled folds A+B; per-family point estimates.
**Market comparison:** NBA has no Kalshi price history (the store holds NFL 2025 only). Not available ⇒ not computed; ΔBrier vs the frozen model is the only judged quantity. Nothing is judged against a market (CHARTER).

## 8. Decision rule (fixed before fitting)
A family "beats frozen" iff **(a)** the pooled 98.33% CI for ΔBrier lies wholly below 0 **and (b)** the point estimate is favourable in **both** test seasons. Otherwise NO. No tuning, re-fit, feature or strike change after seeing results. A NO is recorded with the numbers and D1 stays.

## 9. No-look-ahead tests (`test_lookahead.py`, run before the fit is read)
(1) Snapshot slot ≤ tip − 4h for every row; (2) trailing minutes use only games before the cutoff; (3) shifting a game's own box score changes no feature of that game; (4) future-dated injury files do not alter a past game's row.

## 10. Expected modal outcome (written before the fit)
**NO / negligible.** Availability is largely priced into the market and into rest/form features; with one to two seasons identifying the coefficient, a CI excluding zero is not expected. If a family does earn it, a PROPOSED pre-registration will state "thinner edge vs market expected" (efficient, high-attention market; CLAUDE.md generality-vs-edge tension is not resolved here).

## 11. If earned
One line in the handoff: PROPOSED EXP-0xx (family/strike named, judged n, modal outcome) for the operator. Not accepted by being drafted (CHARTER rule 7).
