# EXPLORATORY - W103.1 (B-044): tails and kill-switch breach odds. Not evidence about any cell.

Common rules first line (quoted): `# Wave 103 common rules`. Pillar: PROOF/EXECUTION measurement quality. No limit is set, no Kelly proposed; blanks stay blank (ADR-0076 s4).

Code: `src/prediction_market_bot/quant/tails.py` (PR #432, 13 known-answer tests, CI green). Run: `run_tails_w103.py` here. Data: `daily_series.csv` (per book/day), `result.json` (everything below). Money math from `quant/money.py`. Read-only copies of box files, taken 2026-11-05.

## Quant Bar
- **Known answer:** GPD(0.3) and |t4| shape/quantile recovered; light tail told from heavy; ES exact for exponential; exact drawdown; breach = 0 for a riskless book, 1 for a ruinous one, and matches an independent random-walk reference.
- **Applies:** cluster (game / day) losses, roughly independent across clusters, >= 15 exceedances. **Does not apply:** one binary contract's own loss (bounded at its stake, so EVT is undefined there); more than ~1 day outside the observed worst; any horizon beyond the data (the breach simulator is a resample, not a forecast).
- **Measured result:** below, with n and 95% intervals.

## How to read it
- Per-game loss is measured **per $ staked** and can never exceed 1.0 (the stake). So every fitted tail is *bounded* (shape xi < 0, "light"). That says a single game cannot lose more than its stake. It says **nothing** about how often a whole day is lost. The kill switch is driven by **drift and day-to-day variance**, not by a heavy tail.
- Breach odds resample the book's own observed days (day-clustered) at a flat cadence as measured. Stake per bet = Kelly x f-bar, f-bar = mean of (p - c)/(1 - c) over that book's ledger. Shadow books have no ledger Kelly; they use the T4M-PROJ YES f-bar (0.205) as a **proxy**. Aggregate deployment is capped at 60% of equity (ADR-0026), applied per day.
- Intervals are wide because n is days (15 to 56), not bets. Where n is too small the cell says **too few**; no fit is forced.

## Per book (YES-only is the headline, GG-1771)
Tail = game-level GPD (n games, exceedances, shape xi, 95% interval). VaR99 / ES99 are per $ staked in a game; the last column rescales to the $500 per-event cap.

| Book | n bets | days | games | tail fit | xi [95%] | VaR99 / ES99 per $ | at $500 cap |
|---|---|---|---|---|---|---|---|
| T4M-PROJ MLB **YES** | 1,733 | 56 | 295 | OK (q .70, 89 exc, unstable) | -1.69 [-7.8, -1.2] | 1.00 / 1.00 | ~$500 |
| T4M-PROJ MLB NO (GG-1770/1771 caveat) | 2,583 | 50 | 334 | OK (q .80, 67 exc, unstable) | -2.45 [-5.0, -1.3] | 1.00 / 1.00 | ~$500 |
| T1 MLB **YES** | 34 | 14 | 19 | **too few** | - | - | - |
| T1 MLB NO (mirror-priced, caveat) | 435 | 23 | 162 | OK (q .60, 65 exc, unstable) | -2.40 [-3.4, -1.4] | 1.00 / 1.00 | ~$500 |
| shadow NBA YES | 24,429 | 19 | 121 | OK (q .50, 60 exc, stable) | -0.62 [-1.29, -0.48] | 0.93 / 0.97 | $467 / $484 |
| shadow NHL YES | 4,309 | 23 | 147 | OK (q .50, 29 exc, stable) | -1.38 [-2.6, +0.47] undetermined | 0.98 / 0.99 | $492 / $497 |
| shadow NFL YES | 9,775 | 21 | 47 | **too few** games (47 < 60) | - | - | - |
| shadow MLB YES | 85 | 4 | 5 | **too few** | - | - | - |

Reading: in every OK row the tail is bounded at the stake. In the live-order books a "worst game" is a full-stake loss (VaR99 = 1.00 per $): a game's whole stake going is a 1-in-100 event or more common. The $500 per-event cap therefore binds as the **expected worst game**, not as a remote tail.

## Breach odds: drawdown kill (20%) within 1 / 6 / 12 months, flat cadence as measured
Point estimate with 95% interval across day-resamples. Daily breaker (15%) in the last column group, 12 months.

| Book | Kelly | stake/bet | cap binds (share of days) | 1 mo | 6 mo | 12 mo | breaker 12 mo |
|---|---|---|---|---|---|---|---|
| T4M-PROJ **YES** (56 d, 15.9 active d/mo) | 0.01 | 0.205% | 0% | 0.20 [0.00,0.47] | 0.91 [0.52,1.00] | 0.98 [0.78,1.00] | 0.00 |
| | 0.025 | 0.514% | 2% | 0.76 [0.43,0.95] | 1.00 | 1.00 | 0.92 |
| | 0.05 | 1.03% | 18% | 0.93 [0.76,1.00] | 1.00 | 1.00 | 1.00 |
| T4M-PROJ NO (caveat) | 0.01 | 0.31% | 0% | 0.12 [0.00,0.37] | 0.84 [0.19,1.00] | 0.95 [0.67,1.00] | 0.00 |
| | 0.025 | 0.76% | 24% | 0.53 | 0.98 | 0.99 | 0.86 |
| | 0.05 | 1.53% | 46% | 0.74 | 1.00 | 1.00 | 0.98 |
| T1 MLB YES | any | - | - | **too few** (14 days) | | | |
| T1 MLB NO (caveat; 23 d, 24 active d/mo) | 0.01 | 0.19% | 0% | 0.00 [0.00,0.00] | 0.21 [0.00,0.99] | 0.34 [0.00,1.00] | 0.00 |
| | 0.025 | 0.47% | 0% | 0.08 [0.00,0.41] | 0.57 | 0.61 | 0.00 |
| | 0.05 | 0.95% | 0% | 0.43 [0.02,0.87] | 0.87 | 0.92 | 0.00 |
| shadow NBA YES (19 d) | 0.01 / .025 / .05 | | 89 / 95 / 95% | 0.68 / 0.74 / 0.75 | 0.86 / 0.91 / 0.91 | 0.89 / 0.94 / 0.94 | 0.63 |
| shadow NHL YES (23 d) | 0.01 | 0.205% | 17% | 0.00 | 0.00 | 0.00 [0.00,0.00] | 0.00 |
| | 0.025 | 0.514% | 74% | 0.00 | 0.01 | 0.02 [0.00,0.17] | 0.00 |
| | 0.05 | 1.03% | 83% | 0.01 | 0.05 | 0.10 [0.00,0.57] | 0.00 |
| shadow NFL YES (21 d) | 0.01 | 0.205% | 38% | 0.00 | 0.01 | 0.02 [0.00,0.17] | 0.00 |
| | 0.025 | 0.514% | 67% | 0.12 | 0.35 | 0.51 [0.00,1.00] | 0.00 |
| | 0.05 | 1.03% | 86% | 0.57 | 0.65 | 0.70 [0.00,1.00] | 0.69 |
| shadow MLB YES | any | - | - | **too few** (4 days) | | | |

## What this says (and does not)
1. **The live-order MLB books breach the kill switch at every Kelly tested, including 0.01 (T4M-PROJ YES 0.98 in 12 months).** Measured mean daily return per $ staked: T4M-PROJ YES -6.8% (sd 50%), T4M-PROJ NO +0.5% (sd 28%), T1 NO -3.1% (sd 25%). So YES is drift plus variance; NO is variance alone (day-level swings of 28% of the day's stake, at 15-18 active days a month, are enough to walk 20% off the peak). It restates ADR-0048 (ruin geometry at any positive Kelly) in numbers. No verdict on any cell is drawn.
2. **For the shadow books the 60% deployment cap, not Kelly, sets the risk.** At 1,300 orders per NBA day the cap binds on 89-95% of days even at Kelly 0.01, so the three Kelly rows are nearly the same (0.89 / 0.94 / 0.94). A per-bet Kelly limit does not govern those books; the aggregate cap does.
3. **The NBA shadow worst day is -43% of stake (-26% of equity at the 60% cap).** That alone exceeds the 15% daily breaker, hence breaker odds of 0.63. The NHL worst day is -13% per $ (-8% of equity). NFL's is -79% per $.
4. **Epoch mix:** the T4M-PROJ ledger spans logic epochs (it is the whole ledger, not a clean epoch); the NO side carries the GG-1770 sign-inversion/mirror-pricing caveat and is shown for completeness only. T1 NO is the only T1 side with enough data and is a pre-GG-1771 mirror-priced book.
5. **Shadow fills are not execution evidence (GG-527)**; their stake is the fill-priced stake and f-bar is a borrowed proxy. They show tail *shape* and the cap's behavior, not what a live book would earn.
6. **Not tested:** correlation between books/sports on the same day (each is a separate book per ADR-0035/0037); fee changes; a bankroll other than the $1,000 normalisation (results are in fractions of equity).

## Data-quality flag (GG-1775, registered, not investigated here)
Shadow fill rows imply implausible returns: NHL YES wins 71.7% of 4,309 fills at a 48.1% mean price (mean daily return +101% of stake); NFL 45.7% at 34.2% (+94%); NBA 43.0% at 40.8% (+11%). Fill selection (only some orders fill, settled rows only; 121 fill rows unsettled and skipped) or a settlement mapping defect could do this. **The shadow NHL/NFL breach odds above are therefore optimistic by construction and must not be read as safe**; they are shown because the tail and cap-binding shapes are still informative. Out of scope to fix (Hard Rule 11).

## Method notes
- Threshold chosen by shape stability (`choose_threshold`); "unstable" means no q in {.5,.6,.7,.8,.9} had three agreeing shape values - read those VaRs as the bounded-at-stake ceiling, not a precise level.
- CHARTER rule 2 tension: this block reads shadow fills and ledgers read-only, as the block brief authorises; no order/position/registry imports, outputs only via `_fence.safe_out`.
- Cadence: active days per calendar month as measured in each window (14-30).
