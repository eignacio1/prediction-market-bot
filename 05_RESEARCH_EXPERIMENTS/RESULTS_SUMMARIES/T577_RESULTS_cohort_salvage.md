# T-577 Results — Cohort Salvage or Declare

Pre-registration: `T577_PREREGISTRATION_cohort_salvage.md` (pushed `eb4f06c`, immutable, unedited). Script: `scripts/t577_cohort_salvage.py`. Raw output: `exp_output/T577_cohort_salvage/t577_results.json`. Data: the same `paper_portfolio_mlb_t4.LIVE.20260922.json` + `t571_kalshi_verification_results.json` snapshot T-571/T-573 used, cross-verified 905/905 match against `t573_duplicate_ticker_full_join_results.json` before any new statistic was computed.

## Deliverable 2 — four-tier partition

| Tier | n | date span | n dates | max single-date share |
|---|---|---|---|---|
| CONFIRMED-REAL | 35 | 2026-07-31 .. 2026-09-22 | 10 | 2026-08-10: 42.9% |
| CONFIRMED-CANCELED | 139 | 2026-09-22 only | 1 | 100.0% |
| DUPLICATE-SUSPECT | 395 | 2026-07-31 .. 2026-08-13 | 9 | 2026-08-10: 25.3% |
| UNCONFIRMED-CLEAN | 336 | 2026-07-31 .. 2026-08-13 | 9 | 2026-08-07: 29.5% |

All four tiers reconcile exactly to the pre-registered expected n (35/139/395/336); partition is exhaustive and non-overlapping over the 905-row cohort (asserted in-script).

**CONFIRMED-CANCELED note (candidate for 35.1, not investigated further per scope):** all 139 CANCELED rows fall on a single date, 2026-09-22. That is either a single mass-cancellation event or the cron's most recent run being entirely canceled — worth a governance-gap registration and a look at that day's cron log, outside this task's scope.

Observable means per tier (5 pre-registered continuous fields): see script stdout / JSON for full table; the material comparison is the bias screen below.

## Bias screen — UNCONFIRMED-CLEAN vs CONFIRMED-REAL (pre-registered test, Bonferroni α=0.01)

| observable | mean REAL (n=35) | mean CLEAN-NR (n=336) | p | survives Bonferroni? |
|---|---|---|---|---|
| mid_price_at_entry | 0.6527 | 0.4337 | 0.00014 | **YES** |
| gross_edge | -0.1913 | -0.0647 | 0.02618 | no |
| h_so_far_at_entry | 0.2857 | 0.1548 | 0.04844 | no |
| ab_remaining_at_entry | 2.4286 | 2.6042 | 0.02744 | no |
| size_usd | 0.6271 | 0.8808 | 0.00075 | **YES** |

**Result: 2 of 5 continuous observables survive Bonferroni.** The pre-registered criterion required zero. UNCONFIRMED-CLEAN fails the bias screen against CONFIRMED-REAL. (Date-spread screen would have passed on its own — 9 distinct dates, max share 29.5% < 30% — but the bias screen is the disqualifying one and either failing alone is sufficient per the pre-registration.)

DUPLICATE-SUSPECT was not tested — it is excluded from any combination by the pre-registration regardless of test outcome (fabricated-order-id defect, not a power problem).

## Deliverable 3 — scenario-bounds calibration estimate

| scenario | n | n dates | model_brier | market_brier | skill_vs_market | win_rate | total_pnl |
|---|---|---|---|---|---|---|---|
| S1: CONFIRMED-REAL only | 35 | 10 | 0.2618 | 0.5215 | **+0.498** | 0.171 | -7.78 |
| S2: CONFIRMED-REAL + UNCONFIRMED-CLEAN | 371 | 12 | 0.2979 | 0.3609 | **+0.175** | 0.423 | +10.57 |
| S3: UNCONFIRMED-CLEAN only | 336 | 9 | 0.3017 | 0.3442 | **+0.123** | 0.449 | +18.35 |

All three scenarios show positive skill_vs_market (model beats market on Brier score) — the sign does not flip. This is a genuinely interesting observation, but it does **not** rescue the verdict below: S2/S3 include the UNCONFIRMED-CLEAN tier, which just failed its own pre-registered bias screen on exactly two variables — `mid_price_at_entry` and `size_usd` — that plausibly correlate with market efficiency regime and bet sizing. A composition effect (more bets at cheaper, less-efficient price points in the unconfirmed-clean tier) could produce an inflated or deflated skill number that has nothing to do with the model's actual edge. Same-signed results across a biased and unbiased tier are suggestive, not confirmatory — precisely the situation the pre-registration was written to prevent being oversold.

## Deliverable 4 — verdict

**UNRECOVERABLE**, triggered by pre-registered condition (a): *"no tier combination other than CONFIRMED-REAL alone passes both the bias screen and the n≥30/date-spread screen."*

UNCONFIRMED-CLEAN — the only tier that could have expanded the n=35 cohort — fails the bias screen (2/5 covariates survive Bonferroni, vs. the required 0/5). DUPLICATE-SUSPECT is categorically excluded regardless of any test. No other tier or combination was available under the pre-registered rules. Condition (a) alone is sufficient per the pre-registration; condition (b) does not additionally trigger (the S1-S2 bracket does not span positive/negative — both are positive), so this is the single-condition form of UNRECOVERABLE, not the compound form.

This means: the only population that can honestly answer "does the model beat the market" on this ledger remains the same 35 CONFIRMED-REAL rows GG-301 already characterized — non-random on 3 of 5 covariates versus the full cohort, clustered 42.9% on one game-date, and too small and too skewed to generalize past its own sample. The full-765 and full-905 headline figures answer a different, contaminated question. UNCONFIRMED-CLEAN's own numbers (n=336, positive skill_vs_market) are real data points that cannot currently be defended as an unbiased read on the model, given the demonstrated selection difference from the one population whose fills are independently confirmed.

### What would be needed to build a clean cohort from scratch (costed)

1. **GG-303 fix first (owned by session "35.1").** The fabricated/duplicate `kalshi_order_id` defect must be closed before any *new* accrual can be trusted — otherwise every future paper-trade row inherits the same identity-verification gap this whole exercise exists to route around. This is a hard precondition, not parallelizable with step 2.
2. **Fresh accrual, real fills only, verified at write time (not reconstructed after the fact).** Given the 2026-09-22 confirmed-FILLED count (35) accrued over roughly seven weeks of live paper trading (2026-07-31 to 2026-09-22) at a low per-day fill rate, reaching even a bare n=30 minimum of *newly and independently verified* fills — with the ≥5-distinct-dates, ≤30%-single-date-share spread this pre-registration requires — likely needs several more weeks of continuous cron operation once GG-303 is fixed, not days.
3. **Season timing constraint.** MLB's regular season has ended (today is 2026-09-24); T4M-PROJ is an MLB player-hits band, so its own accrual clock stops here for this year regardless of GG-303's fix timeline. NFL runs into January but is a different sport, different C1/C2/C3 stack, and does not extend this specific band's cohort — it would be new-band accrual, not a continuation of the same calibration question.
4. **Net implication for APR-0035:** this ledger, as it stands today, cannot supply a bias-corrected answer larger than the existing n=35. Any further progress on APR-0035 (open five weeks) needs either (a) GG-303 fixed plus a new MLB season's worth of verified fills, or (b) an explicit decision to evaluate on the n=35 CONFIRMED-REAL population alone with its known, disclosed non-representativeness, or (c) a different band/sport with an intact fill-verification chain from day one.

## Candidate governance-gap items for "35.1" (not registered here, per scope fence)

- CONFIRMED-CANCELED tier is 100% concentrated on 2026-09-22 (139/139) — looks like a single-day mass-cancellation event, undiagnosed.
- UNCONFIRMED-CLEAN failing the bias screen on `mid_price_at_entry` and `size_usd` specifically (not `gross_edge`, `h_so_far_at_entry`, `ab_remaining_at_entry`) suggests the *retrievability* of a Kalshi order may itself correlate with price/size — i.e., NOT_RETRIEVABLE may not be missing-at-random with respect to entry price and bet size. Worth its own investigation before GG-303's fix is called complete, since a fix that only addresses fabricated order IDs but not this price/size correlation would still leave a biased confirmation channel.

— T-577, 2026-09-25.
