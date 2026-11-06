# Blend-weight test — pre-registration (B-051, W105.1)

**Status:** FROZEN at the commit that adds this file (SHA in the W105.1 handoff). No look has been read. Authority: window-approved new pre-registration of a descriptive question (Wave 105 block 105.1). **Pillar / measure:** PROOF — P3 (blend-test looks scheduled per sport, with dates).
**Does not edit** EXP-041, EXP-044, EXP-044B, EXP-044C, EXP-045, their rows, cells, looks or verdict rules. A change to anything below after the first read is a new pre-registration.

## 1. Hypothesis
In `p = pm + w (pe − pm)` (pm = Kalshi mid at the logged quote, pe = engine probability, linear form), **w > 0** — blending the engine into the line lowers out-of-sample log loss versus the market alone. H0: w ≤ 0.

## 2. Cells
- **NBA, tested here (12):** engine {v1 `NBA_ENGINE_LIVE`, v2 `NBA_ENGINE_LIVE_V2`, v3 `NBA_ENGINE_LIVE_V3`} × family {moneyline, spread, game total, team total}. Rows are the existing shadow rows (no new logging), matched to ESPN finals (±1 day), outcome from `nba_engine.live_scoring.outcome`, cluster = game `(game_date, home, away)`. Eligible rows: pm in [0.02, 0.98].
- **NFL, NHL, MLB engine cells: named, not read.** Each is read only at its own existing judged n and look: NFL anchored price EXP-041 (scored look at 500 games with a logged price; descriptive count 2027-01-10) and NFL engine EXP-045 (Look 1, 2027-01-12); NHL EXP-036's own look; MLB cells at theirs. A blend-test read of those cells before those looks is forbidden; at those looks the same statistic (§3) is computed with a new alpha budget registered by then. Sealed cells are not opened.

## 3. Metric and statistic
- Estimand: change in log loss from moving w off 0. Test statistic is the **score test at w = 0** (the locally most powerful test of a log-loss gain at w = 0⁺; needs no refit, so it can be read at planned looks): per row `s = (y − pm)(pe − pm)/(pm(1 − pm))`; per-game mean S_g; `z = mean(S_g)/(sd(S_g)/√G)`, one-sided. Game is the independent unit (`quant/blend_power.py`).
- Reported alongside at every look (descriptive, no decision weight except where §6 says): w̃ = ΣS/ΣI, one-sided 95% bootstrap upper bound of w̃ (whole-game resample, B=1000, seed 20261106), and the 5-fold game-clustered CV log-loss gain (`quant.blend.cv_gain`, seed 20261106).

## 4. Looks and alpha spending
- **Per cell, four equally spaced looks at 25/50/75/100% of n_max games** (a game counts once it has ≥ 1 eligible settled row). **n_max = 400 for v1 and v2 cells (looks at 100/200/300/400 games); n_max = 100 for v3 cells (25/50/75/100).** A look is read only once its game count is reached; the final look is capped at **2027-04-20** (unreached looks are not read; the cell is INCONCLUSIVE).
- **Alpha: one-sided 0.05, Lan-DeMets O'Brien-Fleming spending** (`multiplicity.spend_obrien_fleming`). Chosen over Pocock because the early looks sit on ~100 games or fewer where the score statistic's normal approximation is weakest and one outlying game can move z a lot; O'Brien-Fleming spends almost nothing there and costs only 5.1% more final-look games than a single look (measured, `power_nba.json`), where Pocock would spend a flat ~0.02 at each look. Exact boundaries (4 looks, non-binding, efficacy only): z = 3.750 / 2.540 / 2.012 / 1.717. Null crossing probability verified = 0.0500 (known-answer test).
- No data read between looks (the Part C task prints only "n so far / look at" before a look).
- The first 66 settled NBA games (2026-10-28…11-05) were already read descriptively in W104.2 (w̃ ≈ 0, no decision made). They enter look 1 of every cell. The design used only their row variance, not their w; this is stated, not hidden.

## 5. Multiplicity
**Holm across the 12 NBA cells at every look, m = 12 fixed** (a cell that has not reached the look contributes p = 1). At look k the cumulative alpha spent is `a_k`; sort p-values; reject the j-th smallest if `p_(j) ≤ a_k/(12 − j + 1)`, stopping at the first failure. This is valid by the union argument: the scaled boundary is itself a spending function for each true null.

## 6. Decision words (per cell)
- **MOVE** — Holm-rejected at some look **and** the CV log-loss gain at that look is > 0. Means: the line leaves information the engine carries; keep building this engine as a market-anchored input and report w̃ as a descriptive weight. It is not a pass of EXP-044/B/C and authorises no order and no capital.
- **NO MOVE** — the final look was read, no rejection, **and** the one-sided 95% upper bound of w̃ is < 0.5 (the size the plan detects at ≥ 80% power in the powered cells). Means: this engine adds nothing the line does not already contain at that size; stop tuning the blend and move engine work to inputs the market cannot see.
- **INCONCLUSIVE** — anything else, including cells whose power at w = 0.5 is < 0.80 by construction (listed in §7). Means: no engine-direction change; keep logging; do not read it as "no skill".

## 7. Power of the plan (80%-power games from 104.2's per-row variance; comonotone simulation; `power_nba.json`, `plan_calendar.md`)
Plan power at n_max (O'Brien-Fleming, 4 looks) for w = 0.25 / 0.5: v1 ML .56/.95, spread .69/.98, total .31/.80, team total .31/.81; v2 ML .65/.98, spread .78/.99, total .48/.88, team total .44/.89; v3 ML .31/.69, spread .26/.65, total .08/.16, team total .10/.22. **v3 total and team total are underpowered by design** (cannot reach INCONCLUSIVE→NO MOVE at w = 0.5); w = 0.25 is detectable only in the spread/ML cells. Planned look dates at 9 games/night × observed coverage (7–12/night shifts them ± a third): v1/v2 final looks 2027-01-14 … 2027-02-15; v3 2026-12-29 … 2027-01-10. Dates are expectations; the game count is the trigger.

## 8. Modal outcome (stated before any look)
INCONCLUSIVE ≈ 55% of cells, NO MOVE ≈ 30%, MOVE ≈ 15% (104.2 saw w̃ ≈ 0 and no OOS gain on 12/12 cells; the market is the benchmark). A NO MOVE is a result.

## 9. Conflict check against frozen pre-registrations
- **EXP-044 / 044B / 044C (NBA engine v1/v2/v3):** their metric is paired Brier of engine vs market and a regression skill weight, PASS at ≥ 1,200 games, descriptive checkpoint 2027-01-31, verdict look 2027-04-20, claim "engine at least as good as the market". This test asks a different question (does a *blend* beat the market; log loss; score test), reads the same shadow rows but alters none, and its output is labelled non-verdict for those EXPs. Overlap: a blend look before 2027-01-31 shows an NBA-engine score earlier than their checkpoint. Their checkpoint is "no verdict" and their rows are not sealed, but I flag it: **if the operator reads that overlap as opening the EXP-044* verdict, the v1/v2/v3 looks here should be held until 2027-01-31.** No frozen value is changed.
- **EXP-041 (NFL anchored price, ΔBrier at T1/T2/T3, 500 games) and EXP-045 (NFL engine forward, Look 1 2027-01-12):** not read here; zero conflict. Their w_family and weights are untouched.
- Sealed cells and `kelly_fraction` untouched; no orders; no real capital.

## 10. Guardrails
Read-only. Any use of these results to size or place an order needs its own ADR and the G6 path.
