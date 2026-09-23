# T-569 — T4 Latency Thesis: Pre-Registration

**Status: PRE-REGISTERED, IMMUTABLE ONCE PUSHED.** This document is written and pushed
*before* any thesis-relevant statistic (D2 movement, D3 slopes) has been computed. Do not
edit the event definitions, test statistics, horizons, or verdict criteria below after this
commit lands — if a design flaw is found during execution, stop and file a superseding
document with its own timestamp; do not silently relabel this one.

**What this tests.** CLAUDE.md states T4's thesis as: *"prediction markets are slow to
incorporate live in-game state... the market price lags behind the true updated
probability... the market hasn't updated yet, the bot has."* This is the single most
load-bearing untested claim behind T4M-PROJ's ACTIVE status and the 11-sub-band
decomposition. It has never been measured. This block measures it using only
`t4_mlb_cycle_log.jsonl` — no bets, no fills, no settlements, no ledger. Its result is
therefore independent of whatever the concurrent ledger-integrity audit (33.2, this wave)
finds.

---

## 0. Instrument characteristics (measured before any thesis statistic — this is calibration,
not hypothesis-testing, and is reported here for transparency)

Fresh pull from the VPS (`/opt/prediction-market-bot/logs/t4_mlb_cycle_log.jsonl`, pulled
2026-09-23 ~23:47 UTC — NOT the stale local mirror `logs/.vps_t4_mlb_cycle_log_cache.jsonl`,
which stops at 2026-08-07 and is explicitly excluded from this analysis):

- **Row count:** 398,865
- **Date span:** 2026-07-02T19:09:34Z → 2026-09-23T23:46:35Z (77 distinct `game_date` values)
- **Distinct tickers:** 8,325
- **Null fields:** `p_t4` / `gross_edge` / `net_edge` / `ba_l10` are null together on 28,638
  rows (7.2%) — these are rows where the model could not price (insufficient `ba_l10`
  history). `mip`, `h_so_far`, `ab_so_far`, `ab_remaining`, `inning`, `batting_slot`,
  `threshold`, `game_date` are never null in this pull.
- **Re-derived cadence** (consecutive same-ticker row pairs, n=390,540): **p10 = 65.8s,
  median = 103.9s, p90 = 176.1s, mean = 138.3s.** Histogram: 13.4% of gaps fall in 30-70s,
  58.7% in 70-130s, 25.0% in 130-300s, 2.9% above 300s.
  **This materially disagrees with the ~60s cadence (p10 56s / median 60s / p90 65s) quoted
  in the task brief, which was measured on the stale mirror.** The re-derived figure is
  used throughout this document; the brief's figure is superseded. Plausible mechanism
  (consistent with GG-080's finding that `cycle_id` is a single counter shared across all
  concurrently-live games, not per-ticker): with multiple games live simultaneously, the
  wall-clock revisit interval for any one ticker lengthens beyond the base ~60s poll,
  because the process works through every live ticker once per sweep. **This is reported as
  fact, not investigated further — root-causing the sweep architecture is out of scope for
  T-569 and belongs to whoever owns `t4_mlb_execution_engine.py`.**
- **Re-derived state-change rate** (consecutive same-ticker pairs, n=390,540): `h_so_far`
  changes 1.32% of pairs (5,138), `ab_so_far` changes 4.63% (18,064), `inning` changes
  10.21% (39,875), **any of the three** changes 13.70% (53,523). The task brief's "9.8%"
  figure (measured on the stale mirror, 400k-row sample) is in the same order of magnitude
  as this pull's 13.70% "any" rate but is not identical — expected, given the brief's
  figure appears to have used a different/unspecified combination rule. This document's
  13.70% (and the three disaggregated rates above) supersede it.

**Consequence for horizon definition:** because cadence is not a fixed ~60s step, "T+1
cycle" through "T+4 cycles" below means **the next 1, 2, 3, 4 rows in that ticker's
time-ordered sequence**, not a fixed +60s/+120s/+180s/+240s. The actual elapsed wall-clock
time to reach each horizon is itself measured and reported (median/p10/p90) alongside every
horizon-k statistic in D2 and D3, because at median ~104s per step, "T+4 cycles" is a
~400-450s window in practice, not the ~240s a naive reading of "4 cycles of a 60s bot" would
imply. This is the resolution-limit correction and it is treated as part of the instrument,
not as a result.

---

## 1. Data preparation (fixed before computation)

- Source: fresh pull only (`exp_output/t4_latency_thesis/t4_mlb_cycle_log_fresh.jsonl`, not
  committed to git — 183MB, gitignored by the existing `*.jsonl` rule).
- Group rows by `ticker`, sort ascending by `ts` within each ticker. A ticker's sequence is
  assumed to belong to one game (consistent with the ticker-encodes-game-and-player
  convention used elsewhere in this codebase); this is not independently re-verified here.
- Non-monotonic or duplicate-timestamp adjacent pairs (`dt <= 0`) are dropped from
  cadence/event construction (9 such pairs found out of 390,549 in the profiling pass above
  — negligible, not investigated further).
- D2 (event-based) uses all rows regardless of `p_t4`/`gross_edge` nullity, since it only
  needs `mip` and the state fields.
- D3 (`gross_edge`-based) uses only rows where `gross_edge` is non-null (excludes the 7.2%
  unpriced rows).

## 2. Event definitions (D2)

For each ticker sequence, at row index i (i ≥ 1), comparing row i-1 ("T") to row i:

- **H_EVENT**: `h_so_far` strictly increases.
- **AB_EVENT**: `ab_so_far` strictly increases. (Not mutually exclusive with H_EVENT — a hit
  is also a completed at-bat. Both are reported. An `AB_ONLY` residual category, `ab_so_far`
  increases and `h_so_far` does not, is also reported for disambiguation, though it was not
  explicitly requested.)
- **INNING_EVENT**: `inning` changes (either direction; MLB innings are monotonic within a
  game in this data absent an ingestion error, so this is expected to mean "advances").

These three are reported **separately**, per the task brief — they are not collapsed into
one "any state change" event for D2's headline numbers (that combined rate is reported only
in §0 as an instrument characteristic).

## 3. D2 — the direct test: does `mip` move after a state change?

For each event type × horizon k ∈ {1,2,3,4} (the next k rows in the ticker's sequence after
the event row T):

- `delta_mip(T, T+k) = mip(T+k) - mip(T)`, computed only when row T+k exists in that
  ticker's sequence (right-censored events near a ticker's last row are dropped for that k
  — n shrinks with k, and n at each k is reported).
- **Primary statistic:** mean and cluster-robust SE of `delta_mip(T,T+k)`, reported (a)
  pooled, and (b) split by `sign(gross_edge(T))` ("direction of the model's implied
  update" — positive: model above market, negative: model below market; rows with
  `gross_edge(T)` null at the event are excluded from the split but retained in the pooled
  figure).
- **Signed-direction statistic:** mean of `delta_mip(T,T+k) * sign(gross_edge(T))` — this is
  the number that is actually informative about "the market moved toward the model," since
  raw pooled `delta_mip` mixes both directions and can average near zero even if the market
  moves toward the model both ways.
- **Clustering:** cluster-robust SE via block bootstrap, 1,000 resamples, resampling
  **tickers** with replacement (primary — tickers are the natural non-independence unit
  since one ticker contributes many events). `game_date` cluster-bootstrap SE reported as a
  secondary robustness check.
- **Resolution-limit reporting (mandatory, stated prominently in results, not folded into a
  null):** alongside every horizon-k statistic, report the actual elapsed wall-clock
  median/p10/p90 seconds to reach T+k for the events in that stratum, and separately report
  what fraction of events already show `mip == p_t4(T)` (rounded to the instrument's stored
  precision) or `|gross_edge(T)| ` below some small band (e.g. <0.005) at T itself — i.e.,
  cases where the market had already closed the gap by the time this row was logged, which
  this instrument cannot distinguish from "the market never lagged at all" at its own ~104s
  median cadence. This is reported as a stated limit, not scored as evidence against the
  thesis.

## 4. D3 — the sharp test: does `gross_edge(T)` predict `mip`'s forward move?

For every row T with non-null `gross_edge`, `mip`, and a horizon-k row T+k in the same
ticker sequence (k = 1..4):

- **Forward regression:** OLS of `delta_mip(T, T+k)` on `gross_edge(T)` (plus intercept).
  Report slope, cluster-robust SE (block bootstrap, 1,000 reps, resampled by ticker —
  primary; resampled by `game_date` — secondary), and n.
- **Confound (a) — mean reversion.** Define `own_dislocation(T) = mip(T) -
  trailing_mean_mip(T)`, where `trailing_mean_mip(T)` is the expanding mean of `mip` over
  that ticker's prior rows up to and including T (minimum 3 prior rows required; rows
  without enough history are excluded from this specific comparison only). Run: (i) OLS of
  `delta_mip(T,T+k)` on `own_dislocation(T)` alone — this is the "reverts to its own
  history" statistic; (ii) a multiple regression of `delta_mip(T,T+k)` on both
  `gross_edge(T)` and `own_dislocation(T)` — report both coefficients. If `gross_edge(T)`'s
  coefficient survives (same sign, still excludes 0 at 95% cluster-robust CI) after adding
  `own_dislocation(T)`, that is evidence beyond simple reversion-to-own-mean. If it does not
  survive, reversion explains the pooled result and this is reported plainly as such.
- **Confound (b) — shared information / mechanical artifact, tested via a reverse-time
  placebo.** `gross_edge(T) = p_t4(T) - mip(T)` and `delta_mip(T,T+k) = mip(T+k) - mip(T)`
  both algebraically contain `mip(T)` with sign structure that can induce a correlation
  independent of any genuine forward-predictive content (shared-noisy-regressor /
  Yule-type artifact). This is addressed with a **falsification regression**: OLS of the
  **backward** change `delta_mip(T-k, T) = mip(T) - mip(T-k)` on `gross_edge(T)` (same k,
  same rows where T-k exists in the ticker sequence). A `gross_edge` computed at T cannot
  have causally produced a market move that **already happened before T** except through
  the shared-`mip(T)` mechanical channel. If the backward slope is comparable in
  sign/magnitude to the forward slope, the forward result is presumptively a mechanical
  artifact of the shared term, not evidence of the thesis. If the backward slope is
  materially smaller (pre-registered threshold: backward |slope| < 50% of forward |slope|,
  or the backward 95% cluster-robust CI includes 0 while the forward CI does not), the
  forward result survives this confound check.
- Both confound results are reported in full (not "mentioned and dropped") for every
  horizon k, alongside the raw forward slope.

## 5. D4 — segmentation

D3's forward slope (with both confound checks) is re-run within each stratum of:

- **Inning bucket:** early (1-3), mid (4-6), late (7+).
- **`ab_remaining` bucket:** 0, 1, 2, 3+.
- **Price stratum (`mip` at T):** <0.10, 0.10-0.30, 0.30-0.50, 0.50-0.70, 0.70-0.90, >0.90.
- **`threshold`:** as its observed categorical values.

A cell is reported as `INSUFFICIENT_N` rather than given a point estimate if it has fewer
than 30 qualifying (T, T+k) pairs at that k. No cell's result is used to override or average
away another cell's — D4 is reported as a table, not collapsed to one number.

## 6. Verdict criteria (fixed in advance — apply mechanically, do not adjust post hoc)

**THESIS SUPPORTED** requires **all** of:

1. D3's pooled forward slope is positive (mip moves toward the model, i.e., same sign as
   `gross_edge`) with a cluster-robust (by-ticker) 95% CI excluding 0, for a majority of
   k ∈ {1,2,3,4}.
2. The reverse-time placebo (confound b) does *not* explain it away: for the horizons where
   (1) holds, the backward slope is either <50% the forward slope's magnitude or has a CI
   including 0 while the forward CI does not.
3. The gross_edge coefficient survives confound (a)'s multiple regression (same sign, CI
   still excludes 0) for the horizons where (1) holds.
4. D2's signed-direction statistic (`delta_mip * sign(gross_edge)`) is positive with a
   cluster-robust CI excluding 0 for a majority of k ∈ {1,2,3,4}, consistent with D3.

**THESIS NOT SUPPORTED** if D3's pooled forward slope is ~zero, not significant, or
wrong-signed across all k, **or** if it is significant but confound (a) or (b) fully
explains it away per the thresholds above (i.e., criteria 2 or 3 fail for every k where
criterion 1 held).

**INCONCLUSIVE** if results are mixed with no consistent direction across k (e.g.,
significant positive at k=1 but significant negative at k=4 with no monotonic story),
or if D4 shows the effect exists in some strata and not others with no coherent pattern
(this is a valid, useful outcome — reported as such, not forced into SUPPORTED/NOT), or if
n is below the 30-event `INSUFFICIENT_N` floor in the strata that would be needed to
adjudicate criteria 1-4 at the pooled level itself (this last case is not expected given
n≈390k rows, but is stated as a floor regardless).

**What a SUPPORTED verdict does NOT establish:** that the lag is large enough to clear
trading costs. 32.1 (a concurrent/prior audit referenced in the task brief) found 71.5% of
765 approvals flip to rejected at median spread. A measured, statistically real lag can
still be smaller than the spread it would need to clear. This tension is named in the
results write-up (Deliverable 5) and explicitly not resolved by this analysis.

---

**Pre-registered by:** T-569, 2026-09-23 23:5x UTC, prior to computing any of §3/§4/§5's
statistics. Only §0 (instrument calibration: row counts, cadence, raw state-change rates) was
computed before this document was written, per the task brief's own framing of that
re-derivation as an instrument characteristic, not a thesis-relevant result.
