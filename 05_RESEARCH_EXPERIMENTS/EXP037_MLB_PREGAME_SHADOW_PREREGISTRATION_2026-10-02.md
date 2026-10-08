# EXP-037 (T-608) — MLB pre-game shadow: pre-registration of 12 cells (2026-10-02)

**Status: written and committed ALONE, before any MLB shadow row is scored.** Rows may be banked (evaluate-and-log); no
delta-Brier, log-loss or E_net *outcome* statistic is computed for any cell until this file is on the remote. The only numbers
used below are the frozen model's 2025 held-out report (climatology only) and structural counts.

Directive (operator, 2026-10-02): game-market expansion tests GENERALITY and accepts thinner edge. Every expectation below is
stated before scoring so that a thin or negative result is *informative*, not explained afterward.

## 0. What this experiment can and cannot judge in 2026 — stated plainly
**The 2026 MLB postseason holds too few games to reach a judged n.** The live board on 2026-10-02 lists four Division Series
(12 events across KXMLBGAME/SPREAD/TOTAL/TEAMTOTAL); the whole remaining postseason is a few dozen games at most, split across
bands and four market families, so no cell can reach the first-look n of 60 settled games. **Therefore every row banked from
2026-10-02 through the end of the 2026 postseason is a head start for the 2027 regular season, not evidence.** Those rows are tagged by
their `start_time_utc` (before 2027-03-01), are NEVER scored at any look, and may only be counted. Judged looks (§4) use 2027
regular-season games only. No cell receives a verdict from 2026 data.

## 1. Cells (12)
`MLB_MONEYLINE`, `MLB_RUN_LINE`, `MLB_GAME_TOTAL`, `MLB_TEAM_TOTAL` × `T1` (12–48 h), `T2` (4–8 h), `T3` (15–60 min).
Series: KXMLBGAME, KXMLBSPREAD, KXMLBTOTAL, KXMLBTEAMTOTAL. Partial-game series (KXMLBF3/F5/F7) are out of scope. T4/T5 out of scope.
Model: `models/mlb_game_pregame_v1.json` (frozen, sha-verified at load; sha256 `a57990a1…1f861`). One bivariate-Gaussian over
(run margin, total runs) per game; every strike is read off it. Runner: `scripts/run_mlb_pregame_shadow.py`. No registry status is changed by this file.

## 2. Definitions fixed now
- **Scoring unit:** the FIRST ledger row per (market_ticker, band). Later re-evaluations in the same band are never scored.
- **Outcome y:** 1 / 0 from the settled result. MLB has no ties. Scalar settlements and postponed / suspended / shortened games are excluded.
- **Sign convention:** `delta_brier_vs_X = Brier(X) − Brier(model)`. **Positive = the model is better than X.**
- **X = market:** Brier of the mid at entry. **X = climatology:** Brier of the strike-specific climatological probability from the training
  seasons 2015–2023 (home win rate for the moneyline; Normal(mean, sd) of margin / total / team total for the ladders; the team-total reference takes ρ = 0).
- **Inference:** game-cluster bootstrap (all strikes and sides of one game form one cluster), B = 2000, seed 20261002, two-sided 95% percentile CI.
- **E_net at entry:** mean over scored first rows of the model-expected net edge on the preferred side, under BOTH fee candidates: k007 = 0.07·q(1−q) (ADR-0016) and
  kmult = 0.035·q(1−q) (series fee_multiplier 0.5, coefficient inferred, GG-332). Realised best-side E_net and log loss are reported beside it and gate nothing.
- **Judged n:** settled 2027-regular-season games with ≥1 scored row in the cell (not rows, not strikes).
- **Starter status:** each row records whether both probable starters were shown at `as_of_utc`. It is reported per band and never used to drop rows.

## 3. Model standard (fixed before fitting)
Regular season (`gameType=R`) only. Train 2015–2023 (ridge means for margin and total, λ = 100 chosen a priori), calibrate 2024 (probit-Platt on the margin;
σ and ρ from 2024 residuals), held-out 2025 (reported only, never used for any choice). Information cutoff: features use only games with `game_date`
strictly before the as-of date, same season; short history returns no forecast. Nine features: decayed team runs scored / allowed / win rate (last 20),
a schedule-derived starter run-prevention proxy for each team (shrunk mean of team runs allowed in the starter's last ≤ 8 starts, prior weight 4), and league runs per game.
**The confirmed starting pitcher is the T1-versus-T3 difference:** a starter not shown in the schedule snapshot at `as_of_utc` falls back to the team's own runs allowed.

## 4. Judged n and power (stated, not tuned)
- Per-game Brier-difference SD is assumed **0.05** (|p_model − p_mkt| is small on MLB, whose prices are tight around 0.5). This is an ASSUMPTION; the realised SD is reported with every result.
- MDE at 80% power, two-sided α = 0.05: MDE = 2.8·SD/√n. **First look, n = 150 settled games per cell:** MDE ≈ **0.011**. **Second look, n = 600 per cell** (or the end of the 2027
  regular season, whichever comes first): MDE ≈ **0.006**.
- Consequence stated plainly: the plausible true effect vs market (≤ 0.01 in magnitude) is at or below the first-look MDE. The modal first-look outcome is SHADOW (CI spans zero), not a verdict.
  Cells at T1 will reach n sooner than T3 only if the board lists games that early; per-band counts differ and are reported.
- No scoring before a cell reaches its judged n. Between looks only row and settled-game counts are inspected. There is no third look without a new pre-registration.

## 5. Expectations, per cell (stated before scoring)
| Cell family | Δ-Brier vs climatology | Δ-Brier vs market |
|---|---|---|
| MLB_MONEYLINE T1/T2/T3 | **> 0**, small | **≤ 0** |
| MLB_RUN_LINE T1/T2/T3 | **> 0**, small | **≤ 0** |
| MLB_GAME_TOTAL T1/T2/T3 | **> 0**, small | **≤ 0** |
| MLB_TEAM_TOTAL T1/T2/T3 | **> 0**, small | **≤ 0** |

Band ordering (all four families): **Δ-vs-market is non-increasing from T1 → T2 → T3.** The market absorbs lineup, bullpen, weather and late starter news as first pitch nears; the
model adds only the probable-starter proxy. Magnitude priors (not rule inputs): moneyline and run line ≈ −0.003 to −0.015; totals nearer zero. Team-total, run-line and moneyline cells share one game's
information, so they are **not independent** evidence of generality and are never pooled into a verdict.

## 6. Decision rules (fixed now, none to be changed after seeing a score)
1. **RULED_OUT** — `delta_brier_vs_market < 0` with the game-cluster 95% CI excluding zero (upper bound < 0) at the judged n → registry cell → `RULED_OUT` with `reason` and `measured_date` (via `promote_cell_status`, ADR-0056).
2. **SHADOW (keep accruing)** — CI spans zero at the judged n → stays SHADOW to the second look; if still spanning zero it stays SHADOW and is reported UNRESOLVED, not promoted or ruled out by judgement.
3. **CANDIDATE-PENDING-CAPACITY** — `delta_brier_vs_market > 0` with CI excluding zero (lower bound > 0) AND mean E_net at entry > 0 under **both** fee candidates → raised only as a sizing question. It authorises no order, position or `kelly_fraction` change (ADR-0048 sizing zero stands).
- Δ-vs-market > 0, CI excluding zero, but E_net ≤ 0 under either fee candidate → SHADOW.
- Δ-vs-climatology ≤ 0 at the judged n is reported as a model failure, separately; it is not a decision rule.

## 7. Backtest — climatology only, and why not more
No historical market prices are available (EXP-034 D1(b) FAILED), so no historical market Brier is computed. Held-out season 2025 (2,245 regular-season games), from `models/mlb_game_pregame_v1_heldout_2025.json`:
- Moneyline Brier: model **0.2456** vs climatology **0.2486** → Δ-vs-climatology = **+0.0030**. This is thin: the model barely beats a constant. No CI is claimed on one season.
- RMSE margin: model 4.567 vs climatology 4.594. RMSE total: model 4.558 vs climatology 4.586.
- 5-bin reliability (pred / obs, n = 449 each): 0.446/0.488, 0.497/0.497, 0.528/0.519, 0.559/0.570, 0.612/0.615. Calibration is acceptable in the middle; the lowest bin is over-pessimistic by ≈ 0.04.
- No historical run-line / total / team-total Brier is claimed.

## 8. Known weaknesses that bias the expectations above (stated in advance)
- **Train/live starter mismatch:** the historical schedule lists the pitcher who actually started, so training saw a "confirmed" starter on every game; live T1 rows will often show none and fall back to team runs allowed.
- The starter feature is a team-runs-allowed proxy, not pitcher-level run prevention, and ignores park, lineup, bullpen, weather and travel (no point-in-time source for any of them). T1 = T2 apart from starter status.
- A continuous Gaussian over integer run margins and totals; run-line and total strikes inherit that shape.
- Regular-season-trained model applied to the postseason (different pitching usage, opponents); irrelevant to any verdict because 2026 postseason rows are never scored (§0).
- ADR-0004 text deviation (probit-Platt on a distribution) is recorded by the same PROPOSED ADR as NFL. kmult coefficient is inferred (GG-332); both fee candidates are carried.

## 9. Nothing else
No order, position, paper fill or sizing change follows from any outcome of this file. SHADOW is evaluate-and-log.


## Addendum 2026-10-08 — ordering key for "earliest 60 settled games" (closes GG-510)
Authorization: operator, 2026-10-07 19:03 PT ("Yes proceed with both recommendations"), recorded in 04_EXECUTION/ACTIVE_QUEUE.md "AUTHORIZATION - PRE-REGISTRATION ADDENDA". Appended 2026-10-08 (W60.2 Part B) before any judged data exists. The text above is unchanged.

The first look scores the earliest 60 settled games per cell. "Earliest" is defined as ascending `(start_time_utc, game_key)`: the game's scheduled start time (the game's first ledger `ts_utc` only if a game has no start time), ties broken by `game_key`, never by arrival order. The released set is frozen in a write-once manifest.

## Addendum 2026-10-08 — MLB climatology comparison is unavailable (closes GG-512)
Authorization: operator, 2026-10-07 19:03 PT ("Yes proceed with both recommendations"), recorded in 04_EXECUTION/ACTIVE_QUEUE.md "AUTHORIZATION - PRE-REGISTRATION ADDENDA". Appended 2026-10-08 (W60.2 Part B) before any judged data exists. The text above is unchanged.

This file defines no climatology comparator for MLB, and MLB settled rows carry no `p_clim` (the MLB settle step writes `y` and `game_key` only). The engine therefore reports no delta-vs-climatology for MLB and does not invent one. The NFL/NHL RULED_OUT-vs-climatology check cannot be applied to MLB; MLB's falsification gate is the delta-vs-market test in this file only. No MLB `p_clim` is added by this addendum; any later baseline needs its own superseding document and applies to new rows only.
