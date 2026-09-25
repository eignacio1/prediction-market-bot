# T-569 — T4 Latency Thesis: Results

**Pre-registration (immutable, pushed before any statistic in this document was computed):**
`T569_t4_latency_thesis_PREREGISTRATION.md` (same directory). Every statistic below follows
that document's fixed event definitions, horizons, test statistics, confound tests, and
verdict criteria mechanically. Nothing in this file relabels or adjusts those criteria.

**Data:** fresh pull of `logs/t4_mlb_cycle_log.jsonl` from the VPS (NOT the stale local mirror
`logs/.vps_t4_mlb_cycle_log_cache.jsonl`, which stops 2026-08-07). No bets, fills,
settlements, or ledger data of any kind were used — this analysis is fully independent of any
concurrent ledger-integrity work.

- Rows: 398,865. Distinct tickers: 8,325.
- Cadence (re-derived, supersedes the task brief's ~60s assumption): p10=65.8s,
  p50=103.9s, p90=176.1s, mean=138.3s.
- State-change rate (re-derived, supersedes the task brief's ~9.8% assumption):
  h_so_far=1.32%, ab_so_far=4.63%, inning=10.21%, any=13.70%.
- 9 non-monotonic/duplicate-timestamp row pairs dropped in data prep (per §1 of the
  pre-registration).

---

## D2 — Direct test: does `mip` move after a state change?

Per event type, per horizon k (next k rows in the ticker's own sequence). `pooled` = mean
`delta_mip(T,T+k)` regardless of direction. `signed` = mean `delta_mip(T,T+k) * sign(gross_edge(T))`
— the number that actually speaks to "market moved toward the model." All SEs are cluster-robust
block-bootstrap (1,000 reps, resampled by ticker).

**H_EVENT** (n=5,107 events, 0.96% already within 0.005 of closed at T):

| k | pooled mean [95% CI] | signed mean [95% CI] | n (signed) | elapsed median (p10–p90) |
|---|---|---|---|---|
| 1 | 0.00467 [0.00314, 0.00624] | −0.00097 [−0.00222, 0.00038] | 4,369 | 116.6s (73.1–187.3) |
| 2 | 0.00622 [0.00437, 0.00806] | −0.00113 [−0.00269, 0.00052] | 4,334 | 236.6s (148.3–375.2) |
| 3 | 0.00676 [0.00494, 0.00869] | −0.00103 [−0.00273, 0.00075] | 4,304 | 355.7s (222.6–569.5) |
| 4 | 0.00863 [0.00660, 0.01073] | **−0.00185 [−0.00369, −0.00005]** | 4,276 | 474.5s (297.4–763.7) |

**AB_EVENT** (n=18,017 events, 2.48% already-closed):

| k | pooled mean [95% CI] | signed mean [95% CI] | n (signed) | elapsed median (p10–p90) |
|---|---|---|---|---|
| 1 | 0.00269 [0.00170, 0.00364] | **−0.00237 [−0.00336, −0.00143]** | 14,546 | 119.1s (74.4–200.7) |
| 2 | 0.00385 [0.00263, 0.00523] | **−0.00280 [−0.00399, −0.00164]** | 14,351 | 243.3s (151.0–463.5) |
| 3 | 0.00428 [0.00306, 0.00563] | **−0.00294 [−0.00428, −0.00164]** | 14,180 | 366.7s (228.0–709.1) |
| 4 | 0.00459 [0.00320, 0.00604] | **−0.00278 [−0.00410, −0.00154]** | 14,009 | 490.5s (304.8–946.3) |

**INNING_EVENT** (n=39,875 events, 3.03% already-closed):

| k | pooled mean [95% CI] | signed mean [95% CI] | n (signed) | elapsed median (p10–p90) |
|---|---|---|---|---|
| 1 | 0.00219 [0.00146, 0.00298] | **−0.00302 [−0.00368, −0.00235]** | 34,938 | 117.8s (74.0–194.0) |
| 2 | 0.00327 [0.00223, 0.00423] | **−0.00427 [−0.00516, −0.00333]** | 34,367 | 239.7s (149.6–408.8) |
| 3 | 0.00363 [0.00241, 0.00473] | **−0.00465 [−0.00569, −0.00353]** | 33,826 | 361.6s (225.6–627.4) |
| 4 | 0.00428 [0.00296, 0.00565] | **−0.00427 [−0.00547, −0.00310]** | 33,250 | 480.7s (302.2–846.2) |

**Resolution-limit caveat (stated prominently per pre-registration, not a null result):** at
the instrument's own ~104s median cadence, only 1.0–3.0% of events show the market having
already closed the gap (`|gross_edge|<0.005`) by the time of the triggering row. This
instrument cannot distinguish "the market lags but closes faster than ~65–176s" from "the
market never lagged." The result below is a statement about lag observable at this cadence,
not a statement that no faster lag exists.

**D2 reading:** pooled `delta_mip` is positive and grows with k for all three event types —
`mip` does move after state changes, monotonically more so at longer horizons. But the
**signed** statistic — the one that actually tests "toward the model" — is **negative** for
AB_EVENT and INNING_EVENT at every k (CI excludes 0 in all 8 cases), and negative-but-mostly-
insignificant for H_EVENT (significant only at k=4). This is the opposite of what the thesis
predicts: when the model implies the market should move up (`gross_edge>0`), the market's
subsequent move is, on average, down, not up. Criterion 4 of the pre-registered verdict
(signed-direction stat positive for a majority of k) **fails outright** for the two event
types with the largest n.

---

## D3 — Sharp test: does `gross_edge(T)` predict `mip`'s forward move?

**Forward regression** — OLS of `delta_mip(T,T+k)` on `gross_edge(T)`, cluster-robust
(by-ticker) block-bootstrap SE, pooled across all rows/events (not just the three D2 event
types):

| k | slope | 95% CI | n |
|---|---|---|---|
| 1 | **−0.02061** | [−0.02515, −0.01564] | 364,080 |
| 2 | **−0.02579** | [−0.03347, −0.01803] | 357,840 |
| 3 | **−0.02731** | [−0.03648, −0.01768] | 351,289 |
| 4 | **−0.03034** | [−0.04211, −0.01895] | 344,633 |

The pooled forward slope is **negative and statistically distinguishable from 0 at every
horizon k=1..4**. This is the wrong sign for the thesis: it says that as `gross_edge` (model
above market) increases, the market's subsequent move tends to be *downward* — away from the
model, not toward it. Magnitude also grows with k (−0.021 → −0.030), i.e., the wrong-signed
relationship gets stronger, not weaker, at longer horizons.

**Confound (a) — mean reversion.** `own_dislocation(T) = mip(T) − trailing_mean_mip(T)`:

| k | own_dislocation univariate slope [95% CI] | multi-reg gross_edge coef [95% CI] | multi-reg own_dislocation coef |
|---|---|---|---|
| 1 | −0.01727 [−0.01805, −0.01654] | −0.02056 [−0.02593, −0.01546] | −0.01700 |
| 2 | −0.02430 [−0.02549, −0.02311] | −0.02399 [−0.03157, −0.01642] | −0.02398 |
| 3 | −0.02831 [−0.03006, −0.02663] | −0.02382 [−0.03387, −0.01314] | −0.02800 |
| 4 | −0.03132 [−0.03352, −0.02921] | −0.02577 [−0.03824, −0.01290] | −0.03100 |

`gross_edge`'s coefficient survives this specific confound in the mechanical sense the
pre-registration defines (same sign, CI still excludes 0 after controlling for
`own_dislocation`) — but the sign it survives with is the wrong sign for the thesis. `mip`
mean-reverting toward its own trailing history and `mip` moving opposite to `gross_edge` are
two closely related, comparably-sized effects (own_dislocation's coefficient is essentially
unchanged between univariate and multiple regression, ~−0.017 to −0.031 across k) — they are
not distinguishable as separate mechanisms here, both point the same direction.

**Confound (b) — shared-information / mechanical-artifact placebo.** Backward regression of
`delta_mip(T-k,T)` (a move that already happened *before* T) on `gross_edge(T)`:

| k | forward slope | backward (placebo) slope | \|backward\|/\|forward\| | survives pre-registered threshold (<50% or CI∋0)? |
|---|---|---|---|---|
| 1 | −0.02061 | −0.13121 [−0.13991,−0.12308] | 6.37x | **NO** |
| 2 | −0.02579 | −0.14594 [−0.15534,−0.13720] | 5.66x | **NO** |
| 3 | −0.02731 | −0.15268 [−0.16243,−0.14313] | 5.59x | **NO** |
| 4 | −0.03034 | −0.15586 [−0.16571,−0.14508] | 5.14x | **NO** |

At every horizon, the backward placebo slope is **larger in magnitude than the forward
slope** (5–6x), with a CI that excludes 0 just as cleanly as the forward CI does. The
pre-registered survival threshold (backward <50% of forward, or backward CI includes 0) is
not met at any k. Per the pre-registration's own framing: "If the backward slope is
comparable in sign/magnitude to the forward slope, the forward result is presumptively a
mechanical artifact of the shared term, not evidence of the thesis." That is what these
numbers show — the backward relationship is not merely comparable, it dominates. The forward
result does not survive confound (b).

---

## D4 — Segmentation

Forward slope and backward-placebo slope, re-run per stratum. Cells below `n<30` are marked
`INSUFFICIENT_N` (none occurred — all cells had ample n). No cell overrides the pooled result;
this is reported as a table, per the pre-registration.

**By inning bucket:**

| bucket | k1 fwd [CI] | k2 fwd | k3 fwd | k4 fwd | bwd (k1) |
|---|---|---|---|---|---|
| early (1-3) | −0.0139 [−0.0192,−0.0081] | −0.0233 | −0.0303 | −0.0371 | −0.0695 |
| mid (4-6) | −0.0229 [−0.0293,−0.0162] | −0.0178 | −0.0115 (CI∋0) | −0.0088 (CI∋0) | −0.1198 |
| late (7+) | −0.0345 [−0.0462,−0.0219] | −0.0572 | −0.0668 | −0.0771 | −0.2665 |

Negative and growing more negative at longer horizons, in every inning bucket except mid-game
where the effect weakens and loses significance at k3/k4. No bucket shows a positive,
thesis-consistent forward slope. Backward placebo is 3–8x forward magnitude in every bucket.

**By `ab_remaining` bucket:** same pattern — negative at essentially every (bucket, k), most
pronounced at `ab_remaining=1` (k1=−0.0293 to k4=−0.0443), weakest and losing significance at
k3/k4 for `ab_remaining=2`. Backward placebo dominates forward by 4–27x depending on bucket/k.

**By price stratum (`mip` at T)** — this is where the pooled picture breaks down into
genuinely mixed sub-results, the one place in D4 with a coherent departure from the pooled
sign:

| price stratum | k1 fwd [CI] | k4 fwd [CI] | k1 bwd | note |
|---|---|---|---|---|
| <0.10 | −0.0111 (CI∋0) | −0.0089 (CI∋0) | −0.1107 | not significant either direction |
| 0.10–0.30 | **−0.0869** [−0.0936,−0.0801] | **−0.1440** [−0.1611,−0.1280] | +0.0478 | strongly negative, largest magnitude in the table |
| 0.30–0.50 | −0.0050 (CI∋0) | +0.0219 (CI∋0) | −0.0166 | drifts positive at k3/k4 but never significant |
| 0.50–0.70 | +0.0100 [0.0011,0.0191] (weak) | −0.0110 (CI∋0) | −0.0105 | marginally positive only at k1, gone by k2 |
| 0.70–0.90 | **+0.1391** [0.0856,0.2062] | **+0.1875** [0.0995,0.2836] | −0.2619 | only segment positive AND growing AND significant at all k — but n≈1,600–1,650 (smallest cell in the table by 30x), and backward placebo is still 1.1–1.9x forward magnitude at every k, so confound (b) is **not** ruled out even here |
| >0.90 | ~0.0000 (CI∋0) | −0.0072 (weak) | **−0.866** | forward ≈0; backward placebo is enormous (~5-6x larger than any other bucket's), consistent with a boundary/bounded-support mechanical effect near mip≈1, not signal |

**By `threshold`:** both observed threshold values (1, 2) show the same pattern as the pooled
result — negative forward slope, significant at k1/k2, weakening toward CI∋0 at k3/k4 for
threshold=2, backward placebo 5–7x forward magnitude throughout.

**D4 reading:** the negative, confound-dominated pooled result is not an artifact of pooling
across a genuinely mixed population — it holds in nearly every inning, `ab_remaining`, and
threshold cell. The one partial exception is the 0.70–0.90 price stratum, which is positive,
growing, and significant at all four k — but it is the smallest cell by an order of magnitude,
and even there the backward placebo slope exceeds the forward slope in magnitude at every k,
so it does not clear the pre-registered confound (b) survival bar either. No cell in the table
achieves a positive forward slope that also clears confound (b).

---

## Verdict (mechanical application of §6 of the pre-registration)

**THESIS: NOT SUPPORTED (current feature set).**

**Scope correction (added by T-575, 2026-09-25, per operator directive — no statistic above was
re-run or altered):** the model under test, `p_hits_gte_threshold(h_so_far, ab_remaining,
ba_l10, threshold)` (`run_t4_mlb_live.py:687`), is a closed-form binomial survival function over
four inputs only — it carries no score/leverage, opponent-pitcher, park, or qualitative signal
(see T-575's `05_RESEARCH_EXPERIMENTS/RESULTS_SUMMARIES/T575_feature_space_audit_RESULTS.md` for
the full inventory). This verdict is therefore a finding about that specific four-input model
failing to beat the market, not a general finding that the T4 live-latency market is efficient
to any better-informed model.

- Criterion 1 for SUPPORTED (pooled forward slope positive, CI excluding 0, majority of k)
  **fails** — the pooled forward slope is negative at all four k, each with a CI excluding 0.
  This alone satisfies the pre-registered NOT SUPPORTED condition: "D3's pooled forward slope
  is ... wrong-signed across all k."
- Independently, even setting the sign aside, confound (b) is not ruled out at any k — the
  backward placebo slope is 5.1–6.4x the forward slope in magnitude at every pooled horizon,
  and in every D4 stratum where a significant forward slope exists at all (the sole exception,
  0.70–0.90 price, still fails confound (b) on its own terms).
- D2's signed-direction statistic (criterion 4) is negative, not positive, for AB_EVENT and
  INNING_EVENT at every k (CI excludes 0 in all 8 cases) — directly contradicting the
  direction the thesis requires, and consistent with (not contradicting) the D3 finding.

None of the three legs of evidence (D2 signed stat, D3 forward slope, D3 confound-survival)
point toward the thesis. This is a clean NOT SUPPORTED under the pre-registered criteria, not
an INCONCLUSIVE call — the direction is consistent (wrong-signed) across event types, across
horizons, and across nearly every D4 stratum, which is the opposite of the "mixed with no
consistent direction" condition that would trigger INCONCLUSIVE.

**What this does NOT establish:**
- It does not establish *why* the relationship is wrong-signed / confound-dominated. Candidate
  explanations not investigated here: `p_t4`'s own construction may itself lag or over-react to
  the same state changes that move `mip`, `mip` bid/ask microstructure effects, or a genuine
  overreaction-then-correction pattern in `p_t4` that this analysis cannot distinguish from a
  pure mechanical artifact.
- Because the thesis is NOT SUPPORTED, the pre-registered "what a SUPPORTED verdict does not
  establish" caveat about trading-cost clearance is moot for the headline verdict — but it is
  worth naming per the pre-registration's own instruction: a concurrent/prior line of work
  ("32.1") found 71.5% of 765 approvals flip to rejected at median spread. That finding is
  about a different question (does a *measured* edge clear costs) and is **not** resolved,
  contradicted, or otherwise addressed by this analysis either way.

---

## What was NOT checked

- **No ledger, bet, fill, settlement, or outcome data of any kind was used.** This analysis is
  purely about `mip` vs. `p_t4` dynamics in the cycle log; it says nothing about realized P&L.
- **Per-D4-cell confound (a) (mean-reversion multiple regression) was not replicated at the
  segmented level** — only run once, pooled, at the D3 level. D4 reports forward and backward-
  placebo slopes per cell but not a per-cell own-dislocation multiple regression. Given the
  pooled result already fails on sign and on confound (b), this was judged unnecessary to
  reach the mechanical verdict above, but it means D4's cells have not been individually
  checked for confound (a) survival.
  - **Gap candidate for 33.2 to register (not registered here per task scope):** worth a GGL
    entry noting that the T4 alpha thesis, when directly measured for the first time, shows a
    wrong-signed and confound-dominated relationship between `gross_edge` and subsequent `mip`
    movement — structurally analogous to GG-037's NBA "anti-predictive" finding, but now
    measured for MLB T4 specifically, where the thesis had never previously been tested. This
    is a first-time direct measurement of a foundational thesis underlying every T4 sub-band
    and T4M-PROJ's ACTIVE status; it does not by itself require any action (no kelly_fraction,
    band, or cell-status change was made or is recommended by this analysis), but the finding
    should be visible in governance tracking.
  - **Also carried forward from the prior session segment as a gap candidate for 33.2:** a
    single historical `SemanticFloorViolation` VPS log hit was noted but not investigated
    further (out of scope, Hard Rule 11).
- **No causal mechanism was tested** for why the backward placebo dominates the forward
  slope — only that it does, per the pre-registered falsification test.
- **No robustness check against `game_date`-clustered SEs was run for D4** (only the primary
  by-ticker clustering) — the pre-registration marks game_date clustering as a secondary
  check for D2/D3 pooled results; it was not extended to every D4 cell.
- **No adjustment for multiple comparisons** across the ~4 dimensions × buckets × 4 horizons in
  D4 — cells are reported individually per the pre-registration's "table, not one number"
  instruction, not as a joint test.

---

**Analysis code:** `scripts/t4_latency_thesis_analysis.py`. **Raw results:**
`exp_output/t4_latency_thesis/t569_results.json`. **Fresh data pull:** excluded from git via
the repo's blanket `*.jsonl` rule (reproducible from the VPS; not committed).
