# EXP-031 — Cross-family market-efficiency ranking: PRE-REGISTRATION

**Task:** T-599 · **Gap:** GG-324 · **Registered:** 2026-09-30, before any rank, bias, calibration or null statistic has been computed on any family.
**Status: FROZEN on push.** Any change after this commit is an *amendment*, appended below with a date and reason, and the original text is left intact. Nothing in this file may be edited to suit a result.

This experiment measures the **market**, not our model. No model is built, fit or tuned. No order is placed; no pool, ledger or sizing value is touched.

## What was known when this was written (D1, already pushed, bab0c6c)
Structure only: rows, tickers, days, snapshot cadence, fields, depth coverage, and Kalshi's own settled `result` per archived ticker (fetched read-only from the public markets endpoint into `exp_output/EXP-031-MKT-EFF-SURVEY/settlements/`). No outcome has been joined to a price, so no calibration quantity exists yet. Archive: 62 price files, 14 families (10 MLB, 4 NFL), 2026-08-01 → 2026-10-01 (NFL from 2026-09-05).

## Unit, population, snapshot
- **Unit:** family = Kalshi `series_ticker`. KXMLBHIT is the reference and is measured by the identical procedure. All 14 families are measured; none are dropped.
- **Contract population:** tickers whose Kalshi `result` is `yes` or `no`. `scalar` (void/tie) and tickers absent from the settled list (not yet played) are excluded and their counts reported.
- **Decision snapshot (one per ticker, no alternatives):** the *earliest* archived snapshot of that ticker with non-null `yes_bid`, `yes_ask` and `yes_mid`. Price `p = yes_mid`; cost `h = half_spread`. Tickers with no two-sided snapshot are excluded and the excluded share is reported per family (this matters for KXMLBHIT, ~30% one-sided).
- No other snapshot, window, or price definition is used for ranking.

## Proxies
**Ranked (unambiguous direction):**
1. **B — calibration gap.** Ten equal-width price buckets on `p` ([0,.1) … [.9,1]). `B = Σ_b (n_b/N)·|f_b − p̄_b|`, `f_b` = realised yes-frequency, `p̄_b` = mean `p`, in bucket b. Higher B = realised frequency departs further from price = less efficient. Signed longshot/favourite pattern (f−p̄ by bucket) is reported alongside, not ranked.
2. **H — cost to cross:** median `h` over the family's decision snapshots. Lower = cheaper to act on a gap.

**Combination:** `E = (B − median(B_null)) − H`. Excess calibration gap net of the cost of crossing the spread. Higher E ranks higher.

**Reported, NOT ranked** (direction ambiguous or not available for every family; justified-and-dropped from the ranking): implied vig (`yes_ask + no_ask − 1`; a cost and a competition signal at once), spread stability, price tick discreteness, convergence (how early/monotonically the price reaches the settled value; needs in-game snapshots whose coverage differs by family), depth (present for a sample only; KXMLBF7 has 7 rows over 2 tickers), volume, snapshots per ticker-day, one-sided-quote share.

## Null band (D4) — per family, at its own n
2000 draws, seed 20260930: redraw each included ticker's outcome as Bernoulli(`p`) independently, recompute B with the same buckets. `B_null_med` and `B_null_99.5` per family. **Gate: a family "clears its null" iff observed B > B_null_99.5.** The 99.5% level is Bonferroni-style for 14 families (0.05/14 ≈ 0.0036 → rounded to 0.005). *Known limitation, stated in advance:* independent draws understate within-game dependence (complementary tickers in one event), so the null band is somewhat narrow; this is offset only by the strict level and by the cluster CIs below, and is reported as a caveat on every family with >1 ticker per event.

## Uncertainty
95% CIs on B, H and E by two cluster bootstraps (2000 resamples each, seed 20260930): **by event_ticker (game)** and **by calendar day of the snapshot**. Both are reported. The decision rules below use the point estimate and the null gate only; CIs are for stating how loosely a ranking is held, and a day-cluster CI for E that includes 0 is flagged "day-fragile" without changing the label.

## Decision rules (evaluated in this order; every family gets exactly one label)
1. **INCONCLUSIVE** — fewer than 300 included settled tickers, or fewer than 20 distinct snapshot days. (Expected to hit NFL families; they are then reported with their n and not ranked.)
2. **CANDIDATE** — adequate n, **and** clears its own null, **and** E > 0, **and** E strictly greater than KXMLBHIT's E.
3. **NO BETTER THAN KXMLBHIT** — adequate n and not CANDIDATE (fails the null gate, or E ≤ 0, or E ≤ KXMLBHIT's E).
KXMLBHIT itself is labelled REFERENCE and also reported against its own null.

## Ranking
One ordering. Families labelled CANDIDATE first, by E descending; then NO BETTER, by E descending; then INCONCLUSIVE, listed unranked. **Tie-break:** if two E values differ by less than 0.0005, the family with more included settled tickers ranks higher. A family that does not clear its null is never described as exploitable, whatever its E.

## D5 join (after the ranking is fixed)
For each CANDIDATE, in rank order, state from `01_SPEC/PREGAME_FEATURE_ARCHITECTURE.md` whether the factor classes for that market's outcome exist, from `T586_absent_attribute_pricing.md` the recorded cost of missing inputs, and from the market-type registry whether a `(MarketType, ExecutionBand)` cell exists and its `CellStatus`. If the top family has no feature substrate at acceptable cost, that is stated and the decision moves to data acquisition. With zero CANDIDATES, the shortlist is empty and says so.

## Interpretation limits (binding on the write-up)
- A family's label is a statement about *calibration bias in the archived window at the first-seen snapshot*, not about the family forever, and not about any model. EXP-029's HARMFUL verdict is about one frozen model against one family; this experiment neither confirms nor overturns it, and no family — KXMLBHIT included — is recommended for or against on one finding.
- Calibration gap is necessary, not sufficient, for an edge: it says nothing about whether we can predict the side. Exploitability requires D5 plus a separate pre-registered model test.
- The window is ~2 months, one regular-season tail; NFL is ~4 weeks of games. Results are not extrapolated.
- Kalshi's `result` is the venue's own settlement, not an independent source; settlement disputes/voids are excluded as `scalar`.

## Frozen, not to be changed after results
Proxies, bucket edges, snapshot rule, combination, 99.5% null level, seed, draw counts, n thresholds, tie-break, labels. Re-cutting a family (window, bucket, snapshot) to improve its rank is prohibited; if an error in this document is found, record an amendment below and, if the rule changes, report results under both the original and amended rule.

## Amendments
(none)
