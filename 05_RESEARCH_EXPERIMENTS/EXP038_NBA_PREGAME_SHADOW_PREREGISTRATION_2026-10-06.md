# EXP-038 (W58.2) — NBA pre-game shadow: pre-registration of 12 cells (2026-10-06)

**Status: written and pushed BEFORE any NBA model exists.** No NBA model file, forecast, shadow row or score exists at the time of writing;
this file is committed alone, ahead of Part D (training/freeze) and Part E (wiring). Structure and rules mirror
`EXP037_NFL_PREGAME_SHADOW_PREREGISTRATION_2026-10-02.md`; deviations from it are listed in §9.

Directive in force (operator, 2026-10-02): game-market expansion tests GENERALITY and accepts thinner edge. Expectations are stated before
scoring so a thin or negative result is informative. Shadow only: no order, position, stake or `kelly_fraction` (ADR-0048 sizing zero stands).

## 1. Cells (12)
`NBA_MONEYLINE`, `NBA_SPREAD`, `NBA_GAME_TOTAL`, `NBA_TEAM_TOTAL` × `T1` (12–48 h), `T2` (4–8 h), `T3` (15–60 min) before tip-off.
Series: KXNBAGAME, KXNBASPREAD, KXNBATOTAL, KXNBATEAMTOTAL (confirmed 2026-10-06; see `RESULTS_SUMMARIES/W58_2_nba_arm_results.md`). T4/T5 out of scope.
Registry status today: all 12 NOT_IMPLEMENTED (PR #174). A cell becomes SHADOW only once it has logged valid rows (Part E).
**Listing reality, measured 2026-10-06:** KXNBATEAMTOTAL has **zero** listings; spread and total list only ~1–2 days ahead (moneyline ~2 weeks).
Consequences, fixed now: the four team-total cells stay NOT_IMPLEMENTED until a first valid row exists and are un-evidenced until then; the spread and total
T1 cells may accrue far fewer games than T2/T3 and are judged on whatever n they reach (§4).

## 2. Model class, features, ADR standing
- **Class:** the EXP-037 distributional class: ridge-linear means for margin and total (λ fixed a priori), one bivariate Gaussian per game, probit-Platt (a, b) on
  the standardized margin; every strike (moneyline, spread, total, team total) is read off the one distribution so the four families are coherent.
- **Features (home perspective), scores-only because that is all that is reachable point-in-time:** recency-weighted rolling points for/against and net rating per team
  (window and decay fixed a priori at the NFL values scaled to NBA game counts; stated in the Part D addendum before fitting), rest days, back-to-back and 3-in-4 flags, home.
  **Not used (gaps, not silent drops):** injuries/availability, lineup and minutes, travel, market prices. NBA outcomes are dominated by availability; that is the largest known weakness (§7).
- **ADR standing — OPERATOR DECISION REQUIRED.** ADR-0070 (PROPOSED, not accepted) deviates from ADR-0004 for the **12 EXP-037 NFL cells only**
  (its §5 says so). Using the same class for NBA (and NHL) is outside that text. **ADR-0070 must be widened, or a superseding ADR written, to cover EXP-038** before NBA
  shadow rows are read as anything but research. This session does not edit ADR-0070 (another session's draft). Rows banked meanwhile are evaluate-and-log only.
- **Frozen model:** `models/nba_pregame_v1.json`, sha256 recorded in the Part D addendum and verified at load. No production retraining (Hard Rule 4).

## 3. Definitions fixed now
Identical to EXP-037 §2: scoring unit = FIRST ledger row per (market_ticker, band); y from the settled result (no ties in NBA; scalar settlements excluded);
`delta_brier_vs_X = Brier(X) − Brier(model)`, positive = model better; X = market mid at entry, or strike-specific climatology from the training seasons;
game-cluster bootstrap, B = 2000, seed 20261006, two-sided 95% percentile CI; E_net at entry under both fee candidates (k007 = 0.07·q(1−q), ADR-0016;
kmult = 0.035·q(1−q), inferred, GG-332) — with KXNBATEAMTOTAL's `quadratic` fee type (no maker fees, unlike the other three) noted when that family first lists;
judged n = settled games with ≥1 scored row in the cell.

## 4. Expectations and power (stated, not tuned)
Per cell: **Δ-Brier vs climatology > 0; Δ-Brier vs market ≤ 0.** Moneyline and spread (most-attended markets) expected −0.005 to −0.02; totals nearer zero.
Band ordering: the feature row is identical at T1/T2/T3 apart from `as_of` (no availability source) while the market absorbs injuries and lineups by tip-off, so
**Δ-vs-market is non-increasing T1 → T2 → T3**; T3 is the likeliest RULED_OUT, T1 the least. Cells sharing a game are not independent evidence and are never pooled.
- Per-game Brier-difference SD is an ASSUMPTION of 0.07 (not measured); the realised SD is reported with every result. MDE (80% power, α = 0.05) = 2.8·SD/√n.
- **First look: judged n = 150 settled games per cell, MDE ≈ 0.016. Second look: judged n = 400 or 2027-01-31, whichever first, MDE ≈ 0.010.** (NBA plays ~1,230 games a
  season, so n is set higher than NFL's 60/150.) The plausible effect vs market (≤ 0.02) is near or below the first-look MDE: the modal first-look outcome is SHADOW (CI spans zero).
- No scoring before a cell reaches its judged n; between looks only row and settled-game counts are inspected. One second look, no third without a new pre-registration.
- **Preseason (2026-10-06 → 2026-10-20) — OPERATOR DECISION, default stated:** preseason games are listed and will be banked, but starters play little and a scores-only model is
  most mis-specified there. Default: preseason rows are banked, labelled, and **excluded from judged n**; they get a separate descriptive report. If the operator prefers to count them, say so before the first look.

## 5. Decision rules (fixed now)
1. **RULED_OUT** — Δ-vs-market < 0 with the game-cluster 95% CI upper bound < 0 at the judged n → `RULED_OUT` with `reason` and `measured_date` via `promote_cell_status` (ADR-0056).
2. **SHADOW** — CI spans zero → stay SHADOW to the second look; still spans zero after it → UNRESOLVED, never decided by judgement.
3. **CANDIDATE-PENDING-CAPACITY** — Δ-vs-market > 0, CI lower bound > 0, AND mean E_net at entry > 0 under both fee candidates → a Wave 48 sizing question only; authorises no order or `kelly_fraction`.
Δ > 0 with E_net ≤ 0 under either fee candidate is SHADOW. Δ-vs-climatology ≤ 0 at the judged n is reported separately as a model failure.

## 6. Training data and window (to be confirmed in the Part D addendum, split fixed before fitting)
Source: ESPN public NBA scoreboard (HTTP 200 from Mac and VPS, 2026-10-06; stats.nba.com and cdn.nba.com return 403 from the VPS). Pulled **off-box** per game date (the endpoint rejects date ranges)
and frozen to a file. Split mirrors NFL: **train 2015-16 → 2022-23 seasons, calibrate 2023-24, held-out 2024-25 (reported only, never used for any choice).** Regular-season games only.
No NBA market history exists in the repo; the market comparison waits for live rows. The held-out report will hold climatology-relative numbers only.

## 7. Known weaknesses stated in advance
- No availability/injury, lineup, load-management or travel information; NBA star-absence swings lines by several points. Expect the model to lose to the market most where that matters.
- Gaussian margin and total are reasonable for NBA but ignore pace-specific variance and late-game foul-driven margin distortion.
- Preseason distribution shift (§4). Early-season rows have thin rolling windows.
- Spread/total listings arrive ≤ 2 days ahead, so T1 evidence for those families is thin.
- The deviation from the literal text of ADR-0004 (§2) is unresolved until the operator decides on ADR-0070.

## 8. Nothing else
No order, position, paper fill or sizing change follows from any outcome of this file. SHADOW is evaluate-and-log.

## 9. Differences from EXP-037 (NFL)
Judged n 150/400 vs 60/150; preseason carve-out; no tie outcomes; ESPN scores-only features vs nflverse EPA; team-total family unlisted at registration; bootstrap seed 20261006.
