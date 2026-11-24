# H-EXEC-4 pre-registration - do filled orders beat the close, net of the fee actually charged? (W124.3)

**Last reviewed:** 2026-11-23. **Frozen:** committed before any arm-order fill dated after 2026-11-20T20:00:00Z was read.
At commit time no such fill has been read by this block: the only fill-level data on the Mac is the evidence copy, which ends
2026-11-19T04:23Z. Rules: `04_EXECUTION/WAVE_BLOCKS/COMMON_RULES_W124.md` (first line quoted in the handoff); `HYPOTHESIS_DOCTRINE.md` Part I.
Code: `exec_fills.py` (same folder), tests `tests/test_exec_fills.py`. Local helpers are used because 124.1's quant tools are not on
main yet; swap for them when they merge (flagged in the handoff).

## 1. Population
- **Judged:** arm orders (post-epoch, all sides, `book = ARM_ORDERS`, `mode = on`) with `filled = True` and first fill time **after
  2026-11-20T20:00:00Z**. Nothing before it is judged.
- **Descriptive only:** every fill dated before that cut (W123 saw them). Labelled DESCRIPTIVE wherever shown.
- Unit of independence: the game (`event_ticker`). Void and unsettled orders are counted, never imputed.

## 2. Outcome
- **Primary:** settled net per contract = `won - fill_price - fee_per_contract`, where the fee is the fee the fill record carries
  (`fee_cost_dollars`), else the exact schedule fee for that fill's own maker / taker flag (`join.fee_of_fill`). Rows that fell back to
  the schedule are counted and reported; if more than 10% of judged fills did, the primary is also shown on reported-fee rows only.
- **Secondary:** CLV net of the same fee = `close_mid_on_held_side - fill_price - fee_per_contract` (markout `close`, 60 s before close).
- **Named lead (from W123.4, descriptive then):** hours-to-start 2-6 h, all arms pooled, 68 fills / 20 games, settle edge +10.1c
  gross. Judged forward only, as one pre-named test.

## 3. Method (all parameters fixed here)
1. **Control variate.** `c = p_cal(entry_mid) - fill_price`, where `p_cal` is a monotone (isotonic) map of entry mid to settle rate
   **fit on pre-cut fills only** and never refit. Adjusted outcome `y - b*(c - mean(c))`, `b` by game-clustered OLS. It removes the
   part of the outcome that the order's price already predicts. It cannot remove the coin-flip itself (sd about 0.5), so the
   reduction is reported as measured, not assumed.
2. **Pairing.** Arms are compared within a game: per game, mean net of arm A minus mean net of arm B, over games where both filled.
3. **Partial pooling.** Cells = arm x family x hours-to-start bucket (0-2, 2-6, 6-24, 24+ h). Normal-normal empirical Bayes: DerSimonian-
   Laird between-cell variance on game-clustered cell means, shrinking each cell toward the pooled mean. Cells under 10 fills or 5 games are
   pooled into their family, then into the arm; never judged alone.
4. **Intervals.** Game-clustered percentile bootstrap, 2,000 draws, seed 20261123, at the look's spent level (section 5).
5. **Round cost** is stated beside every net: mean spread at submit and mean fee actually charged, from the same rows.

## 4. Decision rule (per arm x cell, at a look)
- **SUPPORTED:** the pooled-posterior net interval is wholly above zero at the look's spent level **and** the cell passes BH q = 0.10
  across all judged cells at that look (the named lead is one pre-named test and skips BH).
- **NOT SUPPORTED:** the interval is wholly below zero.
- **COLLECTING:** otherwise, with the date its n is reached (section 6).
Consequence: SUPPORTED cells get placement and size priority in demo; NOT SUPPORTED is a routing result ("hypothesis closed (H-EXEC-4,
parked for R&D)" for that cell only). No capital follows (Doctrine I.4.10).

## 5. Looks and alpha spending
- Weekly, Tuesday 10:00 UTC. First eligible look needs at least 7 days of forward fills. A skipped look is reported, never filled in.
- **O'Brien-Fleming** (Lan-DeMets, `multiplicity.spend_obrien_fleming`), total one-sided alpha 0.05 (= the 90% two-sided default), named
  now. Reason: the early looks sit on tens of fills; OBF keeps them from firing on noise. Information fraction `t = fills / n_target`
  (section 6). The interval at look k uses the cumulative spent alpha at `t_k` (conservative for correlated looks).
- At `t` = 0.25, 0.5, 0.75, 1.0 the spent one-sided alpha is 0.00009, 0.0056, 0.0236, 0.05: a cell cannot be SUPPORTED before about half
  its target n unless the effect is large.

## 6. n needed (80% power, one-sided 0.05, sd 0.5 per contract) and dates
| Target | Effect | Independent fills | x2 for game clustering (n_target) |
|---|---|---|---|
| Named lead 2-6 h, all arms | +0.10 | 155 | 310 |
| Any arm x family pooled | +0.05 | 619 | 1,238 |
| All fills pooled | +0.03 | 1,718 | 3,436 |
Dates: from W123.4's rate (68 fills at 2-6 h and 157 fills overall in 8 days, 2026-11-12 to 11-20), 310 lead fills about 2026-12-26 and 3,436
pooled fills about 2027-05-14 if the rate holds. **ESTIMATES**, not measured forward; the 124.1 ledger is not on main, so these are computed
here and replaced at the first look. Design factor 2 is an assumption until the forward intra-game correlation is measured.

## 7. What would change this
Any change is a dated addendum written before the result it would alter. Not tested here: queue position, size impact, NHL (few fills),
real capital.
