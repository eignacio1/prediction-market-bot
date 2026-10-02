# EXP-037 (T-608) — NFL pre-game shadow: pre-registration of 12 cells (2026-10-02)

**Status: written and pushed ALONE, before any shadow row is scored.** Rows may be banked (evaluate-and-log) but no
delta-Brier, log-loss or E_net *outcome* statistic is computed for any cell until this file is on the remote. The only
numbers used below are the frozen model's 2025 held-out report (climatology only) and structural counts.

Directive (operator, 2026-10-02): game-market expansion tests GENERALITY and accepts thinner edge. Every expectation
below is stated before scoring so that a thin or negative result is *informative*, not explained afterward.

## 1. Cells (12)
`NFL_MONEYLINE`, `NFL_SPREAD`, `NFL_GAME_TOTAL`, `NFL_TEAM_TOTAL` × `T1` (12–48 h), `T2` (4–8 h), `T3` (15–60 min).
Series: KXNFLGAME, KXNFLSPREAD, KXNFLTOTAL, KXNFLTEAMTOTAL. T4/T5 out of scope. Model: `models/nfl_pregame_v1.json`
(frozen, sha-verified at load). One bivariate-Gaussian distribution per game; every strike is read off it.

## 2. Definitions fixed now
- **Scoring unit:** the FIRST ledger row per (market_ticker, band). Later re-evaluations of the same market in the same band are never scored.
- **Outcome y:** 1 / 0 from the settled result; a moneyline tie = 0.5 (Kalshi pays $0.50 each side). Scalar settlements are excluded.
- **Sign convention:** `delta_brier_vs_X = Brier(X) − Brier(model)`. **Positive = the model is better than X.**
- **X = market:** Brier of the mid at entry. **X = climatology:** Brier of the strike-specific climatological probability from the training seasons 2015–2023 (home win rate ex-ties for the moneyline; Normal(mean, sd) of margin / total / team total for the ladders; the team-total reference takes margin-total correlation ρ = 0).
- **Inference:** game-cluster bootstrap (all strikes and sides of one game form one cluster), B = 2000, seed 20261002, two-sided 95% percentile CI.
- **E_net at entry:** mean over scored first rows of the model-expected net edge on the preferred side (`expected_e_net_entry`), under BOTH fee candidates: k007 = 0.07·q(1−q) (ADR-0016) and kmult = 0.035·q(1−q) (series fee_multiplier 0.5, coefficient inferred, GG-332). Realised best-side E_net and log loss are reported beside it and do **not** gate any rule.
- **Judged n:** settled games with ≥1 scored row in the cell (not rows, not strikes).

## 3. Expectations, per cell (stated before scoring)
| Cell family | Δ-Brier vs climatology | Δ-Brier vs market |
|---|---|---|
| NFL_MONEYLINE T1/T2/T3 | **> 0** | **≤ 0** |
| NFL_SPREAD T1/T2/T3 | **> 0** | **≤ 0** |
| NFL_GAME_TOTAL T1/T2/T3 | **> 0** | **≤ 0** |
| NFL_TEAM_TOTAL T1/T2/T3 | **> 0** | **≤ 0** |

Band ordering (all four families): the model's feature row is identical at T1, T2 and T3 apart from `as_of` (no point-in-time
injury, QB, weather or travel source exists — a known gap). The market, by contrast, absorbs that information as kickoff nears.
Pre-registered: **Δ-vs-market is non-increasing from T1 → T2 → T3**, so T3 is the cell most likely to be RULED_OUT and T1 the least.
Expected magnitude vs market: moneyline and spread ≈ −0.005 to −0.02 (most-attended, most efficient markets on the board);
game and team totals nearer zero. These magnitudes are priors, not rule inputs.
Team-total and spread cells share one game's information with the moneyline cell, so their results are **not independent** evidence
of generality; they are reported per cell and never pooled to claim a verdict.

## 4. Judged n and power (stated, not tuned)
- Per-game Brier-difference SD is assumed **0.07** (|p_model − p_mkt| ≈ 0.07 on a typical row, times a factor ≈ 1). This is an ASSUMPTION,
  not a measurement; the realised SD is reported with every result.
- Minimum detectable |Δ| at 80% power, two-sided α = 0.05: MDE = 2.8·SD/√n.
  - **First look, judged n = 60 settled games** per cell (≈ 4 NFL weeks of banked games): MDE ≈ **0.025**.
  - **Second look, judged n = 150 settled games** per cell, or the end of the 2026 regular season (week 18), whichever comes first: MDE ≈ **0.016**.
- Consequence stated plainly: the plausible true effect vs market (≤ 0.02 in magnitude) is **below the first-look MDE**. The expected modal outcome at the
  first look is SHADOW (CI spans zero), not a verdict. A full regular season holds ≈ 272 games; a cell cannot reach a judged n of several thousand.
  The regular season therefore *cannot* settle a 0.005 difference; this experiment can only detect gross failure or gross success.
- No scoring before a cell reaches its judged n. Between looks only row and settled-game counts are inspected. A cell reaching 150 judged games gets exactly
  one second look; there is no third look without a new pre-registration.

## 5. Decision rules (fixed now, none to be changed after seeing a score)
1. **RULED_OUT** — `delta_brier_vs_market < 0` with the game-cluster 95% CI excluding zero (upper bound < 0) at the judged n →
   registry cell → `RULED_OUT` with a `reason` and a `measured_date` (via `promote_cell_status`, per ADR-0056).
2. **SHADOW (keep accruing)** — the CI spans zero at the judged n → the cell stays SHADOW and accrues to the pre-stated second look
   (n = 150 or week 18). If it still spans zero after the second look it stays SHADOW and is reported as UNRESOLVED; it is not promoted or ruled out by judgement.
3. **CANDIDATE-PENDING-CAPACITY** — `delta_brier_vs_market > 0` with the CI excluding zero (lower bound > 0) AND mean E_net at entry > 0 under **both** fee
   candidates → raised only as a Wave 48 sizing question. It authorises no order, no position and no `kelly_fraction` change. (ADR-0048 sizing zero stands.)
- A cell with Δ-vs-market > 0, CI excluding zero, but E_net ≤ 0 under either fee candidate is SHADOW (the model beats the market's probability but not
  the fee-and-spread cost).
- Δ-vs-climatology is a sanity check on the model, not a decision rule: a cell with Δ-vs-climatology ≤ 0 at its judged n is reported as a model failure, separately.

## 6. Backtest — climatology only, and why not more
The market comparison for history is **not available**: 47.1 has not published validated NFL market history (EXP-034 D1(b) FAILED). No
historical market Brier is computed here. The market comparison waits for live rows.

Held-out season 2025 (never used for any choice; 272 games; train 2015–2023, calibrate 2024), from `models/nfl_pregame_v1_heldout_2025.json`:
- Moneyline Brier: model **0.2185** vs climatology **0.2476** → Δ-vs-climatology = **+0.029** (positive, as expected in §3).
- RMSE margin: model 13.09 vs climatology 14.16. RMSE total: model 13.37 vs climatology 13.80. (Direction-consistent with spread / total cells beating climatology.)
- 5-bin reliability (pred / obs): 0.297/0.318, 0.435/0.519, 0.518/0.444, 0.620/0.537, 0.761/0.873. n per bin ≈ 54: individual bins are noisy; the
  middle bins are on the wrong side of the diagonal and the top bin is under-confident. **Read cautiously.** One season, one held-out year; no CI on this
  Brier gap is claimed.
- No historical spread / total / team-total Brier is claimed: the held-out report holds the moneyline Brier and the two RMSEs only.

## 7. Known weaknesses that bias the expectations above (stated in advance)
- The Gaussian places ≈ 2.8% of its mass on |margin| < 0.5 against a real NFL tie rate ≈ 0.4%: the moneyline carries a slight pull toward 0.5.
- T1 = T2 = T3 features (no point-in-time injury / QB / weather / travel), hence the band ordering in §3.
- The model deviates from the literal text of ADR-0004 (probit-Platt on a distribution rather than logit-Platt on a binary); a PROPOSED ADR records it.
- kmult coefficient is inferred, not documented (GG-332); both fee candidates are carried precisely because of this.

## 8. Nothing else
No order, position, paper fill or sizing change follows from any outcome of this file. SHADOW is evaluate-and-log.
