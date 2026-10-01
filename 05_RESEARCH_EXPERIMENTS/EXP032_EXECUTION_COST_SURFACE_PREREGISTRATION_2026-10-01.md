# EXP-032 — Execution cost surface: is the toll structural, or an artefact of when we looked?

**Status:** PRE-REGISTERED — FROZEN ON PUSH. Nothing below is changed after any result is seen; deviations go in the results file under "Deviations", never here.
**Task:** T-603 · **Gap:** GG-325 · **Predecessor:** EXP-031 (T-599, GG-324)
**Date:** 2026-10-01 (UTC) · **Decisions logged:** false (one DECISION_LOG entry is written at close)

## 0. What was inspected before this was written

Structure only, no cost or outcome statistic: (i) archive quote complementarity (`no_ask = 1 − yes_bid` and `yes_ask = 1 − no_bid` hold to zero residual on all 2,125,077 rows); (ii) row counts per family; (iii) snapshot counts per family by time-to-close bucket; (iv) share of rows with a settlement-cache record. No half-spread, vig, price-drift, fill or outcome figure was computed or viewed. The counts did show a **capture hole between 6h and 12h before close** (a few dozen to a few hundred snapshots per family, against tens of thousands in neighbouring buckets). That is a capture defect, not a venue property, and it is why the surface will show UNMEASURED cells there (§2).

## 1. Question and scope

EXP-031's H is one number per family: the median half-spread at the first-seen two-sided snapshot. This experiment measures H as a **function** and asks whether any family's E = B − null_median − H crosses zero under a cost policy the archive can evidence.

**This is not T-569.** T-569 tested a ~60-second in-play T4 latency thesis and returned NOT SUPPORTED. This experiment's drift test (§7) is a pre-game, hours-to-days horizon claim about whether the price moves systematically between the first quote and the start of the game. Any coincidental resemblance (both regress a price change on a price level, both use a backward placebo) is reported in the results, not buried.

**Cost side only.** B, the 10-bucket tables, the null bands (`null_B_median`, `null_B_99.5`), `clears_null`, `day_fragile`, and the B confidence intervals are read from `exp_output/EXP-031-MKT-EFF-SURVEY/d3_d4_results.json` as given inputs. B is not re-derived, re-bucketed or re-windowed. No settlement is re-fetched (cache: `EXP-031-MKT-EFF-SURVEY/settlements/`). No model is fit, no position opened, no sizing touched. Archive is read-only.

Population: the 14 archived families (10 MLB, 4 NFL). KXMLBHIT is the reference and is reported in every table.

## 2. Deliverable 1 — the cost surface

**Unit.** One archive price row = one snapshot. Usable snapshot: `yes_bid > 0`, `yes_ask > 0`, non-null `yes_mid` (EXP-031's two-sided rule). One-sided books are counted separately as availability, not dropped silently.

**Clock.** Archive `close_time == expiration_time` (verified: zero rows differ) and is days after the game, so it is not used. Two clocks:
- `tau_close` = settlement-cache `close_time` − `run_ts` (ex-post, available for all families with a cache record; NFL coverage is 76–86%, others ≥99.7%).
- `tau_start` = scheduled start − `run_ts`, for MLB families only, parsed from the ticker (`YYMONDDHHMM`, Eastern time, converted with `America/New_York`). NFL tickers carry no time, so NFL has **no pregame split**: NFL pregame cells are UNMEASURED and NFL is reported on `tau_close` only.
- **Clock sanity gate:** for MLB, median(`close_time` − ticker start) must lie in [2.0, 4.5]h and ≥95% of tickers in (0, 8]h. If not, `tau_start` is abandoned for that family, flagged, and every pregame-restricted result for it is UNMEASURED.

**Dimensions (each reported as a marginal per family, plus the two 2-D cross-tabs named below):**
1. `tau_start` buckets (hours before start; MLB): `<0` (in-play), `[0,1)`, `[1,3)`, `[3,6)`, `[6,12)`, `[12,24)`, `[24,48)`, `≥48`. NFL and any gate-failed family: the same edges on `tau_close`, labelled as such.
2. Session phase: Eastern hour of the snapshot — overnight 00–06, morning 06–12, afternoon 12–18, evening 18–24.
3. Side: cost of buying YES (`yes_ask − yes_mid`) and of buying NO (`no_ask − (1 − yes_mid)`) reported separately, plus availability per side (share of snapshots in which that side can be bought below 0.99 with a positive opposite bid). Because the books are complementary, the two-sided costs are expected to be identical; the result is reported whichever way it falls, and asymmetry is attributed to one-sided books only if that is what the data show.
4. Price level: the same 10 equal-width buckets on `yes_mid` as EXP-031.
5. 2-D cross-tabs: `tau_start × price bucket` (the surface used by §3 policy (b) coverage test) and `tau_start × session phase`.

**Metrics per cell:** n snapshots, n tickers, n event-days, median and 25th/75th percentile of half-spread (price units) and of vig (`yes_ask + no_ask − 1`), and tick discreteness (share of half-spreads on whole-cent multiples; smallest nonzero half-spread).

**Measured vs UNMEASURED.** A cell is MEASURED iff n snapshots ≥ 200 **and** n tickers ≥ 30 **and** n event-days ≥ 5. Otherwise it is UNMEASURED and is **never interpolated, smoothed or pooled into a neighbour**. Per family, report: measured cells / total cells in the `tau_start × price` grid (8 × 10 = 80), and the share of the family's usable snapshots that fall in MEASURED cells. Snapshots are serially correlated within a ticker; cell medians are descriptive and carry no CI. Cost-side uncertainty enters only through the cluster bootstraps in §4.

## 3. Deliverable 2 — cost policies

All policies score the same fixed B. They differ only in the cost charged to realise it. Fees are excluded in every policy, as in EXP-031.

**(a) Cross at first-seen — baseline.** H_a is EXP-031's per-family H. **Correctness gate:** the script must recompute H_a from the archive with EXP-031's `decision_snapshots` and match the file's H and E to 1e-5; if it does not, stop and register a gap before anything else is reported.

**(b) Cross at the cheapest measured point.**
- Entry snapshot at bucket τ: for each ticker, the earliest usable snapshot inside that `tau_start` bucket. (Same construction as EXP-031's first-seen, restricted to a bucket.)
- Eligible τ: pregame buckets only (`tau_start ≥ 0`). B is a **pregame** calibration gap; in-play prices incorporate game state B never saw, so in-play cheap points are reported in the surface as context and are **not** eligible for (b).
- **Split-sample selection (guards the winner's curse):** order event-days ascending; even-ordinal days are the *selection set*, odd-ordinal days the *evaluation set*. τ* = the eligible bucket with the lowest median entry half-spread on the selection set, subject to ≥ 200 tickers and ≥ 5 event-days in **both** sets. H_b = the median entry half-spread at τ* on the **evaluation set** only. Same estimator as H_a (median over tickers, unweighted).
- If no pregame bucket meets coverage for a family, (b) is UNMEASURED for that family and the family keeps its (a) verdict.
- Secondary diagnostic, not part of the rule: price-bucket-weighted H_b using EXP-031's bucket weights, fully-measured buckets only (≥ 0.90 of weight measured, renormalised, flagged).

**(c) Rest at mid, no fill unless the archive evidences one.**
- Order: at each ticker's EXP-031 first-seen snapshot, rest a buy at the first-seen mid `m`, on the side EXP-031's bucket table favours: YES if `f_minus_p > 0` for the ticker's bucket, NO if `< 0` (bucket table taken as given).
- **What evidences a fill:** a *later pregame* snapshot (`tau_start ≥ 0`; for NFL, before `tau_close` of 0) whose opposite quote is **strictly through** the resting price: for a resting YES buy at `m`, `yes_ask < m`; for a resting NO buy at `1 − m`, `yes_bid > m` (i.e. `no_ask < 1 − m`). The fill price is the resting price `m` (no price improvement credited).
- **What does NOT evidence a fill:** `last_price` equal to `m`; any rise in `volume` or `volume_24h`; the mid or the same-side bid touching `m`; the ask merely *equalling* `m` (queue position is unknowable from this archive); a snapshot after game start; the order still resting at settlement. All of these are priced as **unfilled, earning nothing**. The archive has no order-level or queue data, so this is a lower bound on fills and the fill rate is reported next to the result.
- Realised edge: `R_c = (1/N) Σ_i fill_i · s_i · (y_i − m_i)` where `y_i` is the settled outcome, `s_i = ±1` the side sign, `N` the number of first-seen tickers (unfilled tickers contribute 0 and stay in the denominator). **Correctness gate:** with `fill_i` forced to 1, `R_c` must equal EXP-031's B to 1e-5. H_c = 0 (no toll is paid on a filled resting order); E_c = R_c − `null_B_median` (EXP-031's, as given). CI: game- and day-cluster bootstrap of R_c with the EXP-031 resample count and seed 20260930.
- **Adverse-selection diagnostic (reported, not in the rule):** mean `s_i · (y_i − m_i)` among filled versus unfilled tickers. A fill that only occurs when the price has moved against the order will show filled < unfilled.

**B-entry consistency diagnostic (policy b).** EXP-031's B is a calibration gap at the *first-seen* mid. Entering at a different snapshot does not earn that B unless the gap exists there too. For each family with a (b) result, compute `B_entry` on the evaluation-set entry snapshots at τ* with EXP-031's `calib_gap`, and its null by EXP-031's `_null_B` (2000 draws, seed 20260930) on that population. This is a *labelled additional diagnostic*; it does not replace B in any E.

## 4. B held fixed — arithmetic

For (a) and (b): `E_p = B − null_B_median − H_p`, with B and `null_B_median` from the EXP-031 file.
- Confidence interval for E_p (game-cluster and day-cluster separately): `[B_lo − null − H_p_hi, B_hi − null − H_p_lo]`, where `[B_lo, B_hi]` is EXP-031's stored CI for B and `[H_p_lo, H_p_hi]` is a cluster bootstrap of H_p on the cost side only (resample games or days, recompute the median; EXP-031's `_cluster_ci` machinery, same resample count, seed 20260930). This interval-sum is wider than a quadrature sum and is chosen deliberately to be conservative.
- For (c) the CI is the §3 bootstrap of R_c, minus the fixed `null_B_median`.
- `day_fragile` is carried from EXP-031 unchanged.

## 5. Decision rule (frozen)

Under policy p ∈ {a, b, c}, a family is a **CANDIDATE** iff **all** hold:
1. `clears_null` is true in EXP-031 (B > `null_B_99.5`);
2. E_p > 0 as a point estimate;
3. the **lower bound** of E_p's CI is > 0 under **both** the game-cluster and the day-cluster interval;
4. for (b): `B_entry` exceeds its own null's 99.5th percentile *and* `B_entry − null_median_entry − H_b > 0` — otherwise the label is **CANDIDATE-B-NOT-EARNED-AT-ENTRY**;
5. for (c): fill rate ≥ 0.10 and R_c's CI lower bound > `null_B_median` (a policy that fills almost nothing is reported with its numbers but is not a candidate).

Labels: **CANDIDATE** (1–5 hold, `day_fragile` false); **CANDIDATE-FRAGILE** (1–5 hold, `day_fragile` true); **NEAR** (point E_p > 0 but a CI lower bound ≤ 0); **NO** (E_p ≤ 0). Nothing is called a candidate on a point estimate. KXMLBHIT is shown as the reference under the same rule; it is not special-cased.

The headline question, stated before any result: *does any family's E cross zero under any evidenced policy, and by how many CI half-widths?* Report the distance of every family's E_p from zero in units of its own CI half-width. If none crosses, that is the answer.

## 6. Deliverable 4 — capacity check (for any CANDIDATE or CANDIDATE-FRAGILE)

Depth data is a **sample**, not a time series (`exp_output/PRICE_ARCHIVE/depth_*.jsonl`, ~1.4k–2.8k rows per family; KXMLBF7 has 7 rows over 2 tickers), and depth is volatile by 10–100× intraday (GG-155 / T-411). Tested stakes: $5, $25, $100, $500 (the last is the C4 per-event hard cap read from `risk.py`; no sizing is touched). A stake S is **supported** only if, using depth rows for the family that fall in the candidate policy's entry window (for (b), the τ* bucket; for (a)/(c), all rows), all hold: ≥ 30 rows spanning ≥ 10 tickers; the 25th percentile of `within_5c_usd_min_side` ≥ 5 × S (the order is ≤ 20% of visible depth in the thinner direction). Otherwise **CANDIDATE-PENDING-CAPACITY**: the family is not a candidate. The report states, for each stake, what the sample supports and what it cannot say (it cannot say what depth is at the moment an order would be placed).

## 7. Deliverable 5 — pregame drift, with backward placebo

Population: MLB tickers with first-seen `tau_start ≥ 6h` and a later pregame two-sided snapshot ≥ 1h after the first and before start; `p_first` = first-seen mid, `p_last` = mid of the latest such snapshot. NFL: UNMEASURED (no start time). Cells by family × first-seen price bucket; a cell is MEASURED iff ≥ 200 tickers across ≥ 5 event-days.

- **Forward drift** `D = p_last − p_first`: mean per cell with day-cluster 95% CI; and the slope of `D` on `(p_first − 0.5)` per family (negative = pull toward 0.5, positive = polarisation).
- **Tradeable component (CLV-style):** `s_b · D`, with `s_b` the sign of EXP-031's bucket `f_minus_p` for the ticker's first-seen bucket. Compared against H_a as context only.
- **Backward placebo (T-569 / EXP-029 convention):** repeat the identical estimator with time reversed — change `D' = p_first − p_last`, grouped and regressed on the **later** quote's level `(p_last − 0.5)`, side sign taken from the bucket of `p_last`. Placebo ratio = |backward slope| / |forward slope|. Per T-569, a forward effect **survives** only if the ratio < 0.5 or the backward slope's day-cluster CI contains 0. A ratio near 1 (EXP-029 reported 1.02) means the apparent drift is the mechanical regression-to-the-mean of conditioning on an endpoint, not information. The ratio is reported per family regardless of outcome; no drift result is reported without it.
- No claim is made about price movement after game start.

## 8. What cannot be measured, named in advance

- Anything in the 6–12h-to-close band: the archive was not capturing densely there (§0). UNMEASURED where it falls under the §2 floor.
- Pregame split for NFL (no start time in tickers) and for any family failing the clock gate.
- Queue position, order-level fills, and fees (no data).
- Depth at the moment of a hypothetical order (sample only).
- The archive has no snapshots before first-seen for most tickers; `p_first` is "first captured", not "first listed". 44.3 owns the capture fix; defects found are registered, not worked around.
- Settlement coverage: NFL cache coverage is 76–86%; unsettled tickers are excluded exactly as EXP-031 excluded them and the count is reported.

## 9. Mechanics

Script: `scripts/execution_cost_surface.py` (new; imports `scripts/market_efficiency_survey.py` read-only). Tests: `tests/test_execution_cost_surface.py`, including the two correctness gates on synthetic data and a no-lookahead test (fill logic uses only strictly later snapshots). Outputs: `exp_output/EXP-032-EXECUTION-COST-SURFACE/`. Results: `05_RESEARCH_EXPERIMENTS/RESULTS_SUMMARIES/EXP032_RESULTS_execution_cost_surface_2026-10-01.md`, line-by-line against this document. Seed 20260930 throughout. One DECISION_LOG entry, appended at close. No order, pool write, schedule, or sizing change.

## 10. Not decided here

Whether to recommend for or against any sport or market family. A result on the families measurable here says nothing about the rest of the board.
