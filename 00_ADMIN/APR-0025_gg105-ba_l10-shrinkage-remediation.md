# APR-0025 — Empirical-Bayes Shrinkage of `ba_l10` in T4M-PROJ's Live Hit-Probability Model (GG-105 Remediation)

**Status:** PROPOSED — awaiting DS sign-off
**Touches:** `src/prediction_market_bot/run_t4_mlb_live.py::p_hits_gte_threshold()` (also consumed
identically by `t4_mlb_execution_engine.py:174`, currently registry-`BLOCKED`/dark). This is a **live
forecasting-model change** to code governed by ADR-0039 (which explicitly names the current
`run_t4_mlb_live.py` model "unchanged in substance" as its Tier B provisional baseline) and ADR-0029's
Tier B numerics. Per Hard Rule 3, if accepted this requires a superseding ADR before implementation —
this APR is the sign-off request that would authorize drafting that ADR, not the ADR itself.
**Drafted:** 2026-07-15, Window 2 (T-359/T-361), session continuation (shared `main` tree)
**Analysis source:** T-359 (`scripts/run_t359_gg105_interaction_model.py`) —
results: `exp_output/T359-GG105-INTERACTION-MODEL/interaction_model_results.json`
**Diagnostic lineage:** T-324→T-329→T-332→T-333→T-344 (GG-105 discovery and decomposition, all
diagnose-only per explicit scope) → T-359 (this session — the first test that actually manipulates the
suspected mechanism rather than just measuring around it) → this APR (the first remediation proposal)
**Approved by:** _pending — Earl Ignacio (DS)_
**Effective:** _pending sign-off_

---

## Why This Proposal Exists

GG-105 is OPEN: T4M-PROJ (MLB T4 live band) shows a robust, tercile-monotonic **anti-predictive**
relationship between computed edge and realized win rate — bets the model is *most* confident in win
*less* often than bets it is *least* confident in. This has been reconfirmed at growing sample size
across four prior sessions (T-329 n≈200s, T-332, T-333, T-344 n=412, this session's own re-derivation
n=666) and has never once flipped direction. It is not a measurement artifact: T-329 ruled out sizing,
T-332 ruled out game-state concentration, T-333 ruled out default-fill masking and offline-tool vig
omission, T-344 ruled out both a real sign-inversion (win rate stays >50% at every tercile — a decay
signature, not a flip) and the fee/edge-frame sign bug later registered as GG-113 (correcting GG-113
made the pattern *more* significant, not less — p: 0.046→0.0094 — which rules out fee-framing as the
driver even though the bug itself was real and independently worth fixing).

**Every prior GG-105 session was diagnose-only by explicit scope** ("investigation only... any live-formula
change requires a fresh DS sign-off," T-333's own stated boundary). T-333/T-344 converged on model
miscalibration/overconfidence as the leading remaining mechanism but never tested it directly — they
measured the pattern from the outside. T-359 (this session) is the first test that actually manipulates
the suspected mechanism and asks whether the pattern responds. It did. This APR turns that finding into
a concrete, boundable proposal.

---

## The Mechanism, In the Actual Code

`src/prediction_market_bot/c2_feature_store/mlb_features.py` computes `ba_l10` as a raw, unregularized
ratio over a trailing 10-game window (`DEFAULT_WINDOW=10`, `MIN_PERIODS=3`): `ba_l10 = sum(H)/sum(AB)`
over that window, no shrinkage, no floor on `ab_sum` beyond the 3-game minimum. A player who has gone
4-for-9 in his last 3 games gets `ba_l10 = 0.444` — a fixed point estimate built from as few as 9 at-bats,
carrying no signal about how unreliable that estimate is.

`run_t4_mlb_live.py::p_hits_gte_threshold()` (lines 584-608) then takes that number and uses it
**directly and unmodified** (only clamped to `[0.001, 0.999]`) as the fixed per-remaining-AB Bernoulli
success probability in an exact Binomial survival calculation:

```python
p = max(0.001, min(0.999, ba_l10))
p_gte = sum(_binomial_pmf(ab_remaining, k, p) for k in range(h_needed, ab_remaining + 1))
```

This is H1, as named in T-333: **a noisy small-sample ratio is being treated as a known, fixed Bernoulli
parameter**, with none of its estimation uncertainty propagated into `p_t4`. A player who ran hot for 9-15
AB gets a Binomial model built as if that hot streak were his true rate — producing an overconfident
`p_t4`, an inflated apparent edge over the market, and — per this session's finding — a bet that clears
threshold disproportionately on noise rather than signal. `p_t1` (T1's own calibrated pregame estimate,
already loaded into the same context dict at line 343) is never referenced anywhere in the `p_t4`/edge
path — H2's structural fact, also never remediated.

---

## What T-359 Found

Empirical-Bayes shrinkage of `ba_l10` toward the cohort's own observed mean (`0.2512`, an internal,
data-derived prior — not an external constant, consistent with this project's standing rule against
citing unsourced figures): `ba_l10' = (AB_WINDOW × ba_l10 + k × prior) / (AB_WINDOW + k)`, swept across
`k ∈ {0, 20, 40, 80, 160}` against the frozen, GG-113-unaffected epoch-3 cohort (n=666, 100% join rate,
k=0 exactly reproduces the stored `model_p` — sanity-checked).

| k | Fisher p (anti-predictive test) | winrate(edge>0) | winrate(edge≤0) | n(edge>0) | verdict |
|---|---|---|---|---|---|
| 0 (current, live) | **<0.0001** | 0.530 | 0.716 | 455 | ANTI-PREDICTIVE |
| 20 | 0.0000196 | 0.530 | 0.704 | 443 | ANTI-PREDICTIVE |
| 40 | **0.0045** | 0.546 | 0.659 | 414 | ANTI-PREDICTIVE |
| 80 | 0.0797 | 0.559 | 0.629 | 383 | ANTI-PREDICTIVE (weak) |
| 160 | 0.1552 | 0.563 | 0.619 | 359 | INCONCLUSIVE |

**Reading this honestly, not optimistically:** the dose-response is real and monotonic — every step up in
shrinkage strength narrows the winrate gap and raises the p-value. But **the gap does not close, even at
the largest k tested.** At k=160, positive-edge bets still win less often than negative-edge bets
(0.563 vs 0.619) — the anti-predictive *direction* persists throughout the entire sweep; only its
statistical significance and magnitude attenuate. This means H1 (unshrunk `ba_l10` noise) is a real,
demonstrated **contributing** mechanism, not necessarily the **sole** one. H2 (the discarded `p_t1`
blend) was not tested this session and remains a live, unremediated candidate for the residual.

H4 (`ab_remaining` estimator compounding the noise) could not be independently isolated: only 12/666
(1.8%) of the cohort has real known-`batting_slot` data, far below `MIN_N=20` (GG-098 gate). The
fallback-path segment (n=654, 98.2% of the cohort) reproduces the full-cohort H1 sweep almost exactly,
which rules out "H1's effect is a slot-known-subset artifact" but does not give H4 its own test.

---

## Proposed Fix

Apply empirical-Bayes shrinkage to `ba_l10` before it enters `p_hits_gte_threshold()`, using the same
form validated in T-359:

```python
ba_l10_shrunk = (AB_WINDOW * ba_l10 + K * PRIOR) / (AB_WINDOW + K)
```

**Three open parameters this APR does NOT pre-decide — flagged for DS at sign-off:**

1. **`K` (shrinkage strength).** T-359's sweep only establishes the shape of the dose-response, not an
   optimum — it was never designed as an optimization, and no k in {0,20,40,80,160} is being asserted as
   "correct." K=40 is the smallest value tested that reaches conventional significance (p=0.0045) in the
   *attenuated* direction, i.e. it's the lightest touch that already shows a real, measurable effect — a
   plausible starting point, not a recommendation. **This APR asks DS to either select a K value, direct
   a finer-grained sweep (e.g. every 10 between 20-160, or beyond 160) before selecting one, or reject
   shrinkage as insufficient given the persistent residual gap even at k=160.**
2. **`AB_WINDOW` (currently 37, an unverified heuristic).** Per the Explore-agent research this session
   ran: 37 is `10 games × 3.7 AB/game` (`run_t4_mlb_live.py:148`'s own `AB_PER_GAME_DEFAULT`), never
   independently verified against real per-player windowed AB counts, and no ADR or feature-store doc
   states an AB-count figure — only `mlb_features.py`'s `DEFAULT_WINDOW=10` (games) is canonical. **A
   correct implementation should shrink using the player's own actual summed AB over the trailing window
   (`ab_sum`, already computed in `mlb_features.py`'s `_compute_rolling_batter_features()`), not a fixed
   population-average assumption of 37 — this is a real, fixable input-quality gap this APR surfaces,
   not a decision DS needs to make.** Using real per-player `ab_sum` should be the implementation
   requirement, not the sweep constant.
3. **Interaction with H2 (blend `p_t1` into `p_t4`).** Not tested this session. Given the persistent
   residual anti-predictive gap at maximum tested shrinkage, DS should decide whether this APR proceeds
   as a standalone partial fix now, or whether H2 should be tested (a follow-on T-36X task) before any
   live-formula change ships, so a single remediation addresses both known mechanisms rather than
   shipping two separate live-formula changes in sequence.

**Where the fix lives:** `mlb_features.py`'s C2 feature-store output already computes both `ba_l10` and
the raw `ab_sum`/`h_sum` inputs — the natural implementation point is adding a shrunk field there (e.g.
`ba_l10_shrunk`) alongside the existing raw `ba_l10`, leaving the raw field untouched for any other
consumer, and pointing `p_hits_gte_threshold()`'s caller at the new field. This keeps the raw feature
available for audit/backtest comparison and makes the change a single, clearly-diffable substitution at
the T4 consumption site, not a change to the feature-store's existing contract.

---

## What This Does NOT Claim

- **This does not claim shrinkage resolves GG-105.** The persistent residual gap at k=160 is reported
  plainly above — this is a partial-mitigation proposal, not a fix claim. GG-105 should stay OPEN through
  implementation and be re-measured post-deployment against a fresh, post-fix cohort, exactly as GG-113's
  fix was independently re-verified this session rather than trusted on report.
- **This does not touch H2** (blending `p_t1`). That remains a separate, unremediated, un-tested
  candidate mechanism — explicitly flagged above as a DS decision point, not silently deferred.
- **This does not touch H4** (the `ab_remaining` estimator) beyond the `AB_WINDOW` input-quality fix
  named above, which is a data-correctness fix (use real AB, not an assumed constant) rather than a
  resolution of H4 as a hypothesis. H4 remains statistically untested (n=12 known-slot, underpowered).
- **This does not authorize implementation.** Per Hard Rule 3 and ADR-0039 Tier B precedent, DS sign-off
  here authorizes drafting a superseding ADR and building the change — it does not itself change any
  live code path. T4M-PROJ continues operating on the current unshrunk formula until that ADR ships.
- **This does not retract any prior GG-105 finding.** T-329/T-332/T-333/T-344's diagnostic conclusions
  stand unmodified; this APR builds on them, it does not revise them.

---

## Broken-System Test

| Failure mode | How this APR prevents it |
|---|---|
| Shipping a shrinkage fix that "resolves" GG-105 on paper while a real residual anti-predictive gap silently persists | The persistent gap at k=160 (0.563 vs 0.619 winrate) is reported in this document's own numbers, not hidden — GG-105 is explicitly kept OPEN through implementation, not closed by this APR |
| Picking a `K` value by eyeballing the sweep table rather than a DS decision | K selection is explicitly named as an open DS decision point (item 1), not pre-selected by this document |
| Silently reusing the unverified `AB_WINDOW=37` constant in the live implementation the same way the diagnostic script did | Explicitly flagged as a fixable input-quality gap requiring the real per-player `ab_sum` in implementation, not carried forward as a permanent assumption |
| A future session treating this APR's sign-off as authorization to also blend in `p_t1` (H2) since "it's the same GG-105 fix" | H2 is explicitly named as untouched and requiring its own decision/test (item 3) — scope creep from shrinkage into blending is called out by name |
| Re-measuring the fix against the wrong cohort (post-GG-113 `CURRENT_LOGIC_EPOCH` reset to `clean_n=0`) and concluding "no data yet" without recognizing why | This document's own analysis source used the frozen epoch-3 cohort by explicit design (documented in T-359) — the same trap is flagged here for whoever re-measures post-implementation |

---

## Review Checklist

- [ ] T-359's dose-response finding (Fisher p: <0.0001→0.1552, k=0→160; persistent residual gap at k=160)
      reviewed and accepted as sufficient evidence that H1 (unshrunk `ba_l10`) is a real contributing
      mechanism to GG-105
- [ ] `K` value selected, OR a finer sweep directed before selection, OR shrinkage rejected as
      insufficient given the persistent residual gap
- [ ] `AB_WINDOW=37` fixed-constant approach rejected in favor of real per-player `ab_sum` in the
      implementation (recommended above as a correctness fix, not a DS judgment call — confirm)
- [ ] Decision on H2 (blend `p_t1`): test first (new task) vs. ship shrinkage alone now vs. defer H2
      indefinitely
- [ ] Confirmed: this APR does NOT itself authorize implementation — a superseding ADR (referencing
      ADR-0039/ADR-0029 Tier B) is still required per Hard Rule 3 before `run_t4_mlb_live.py` changes
- [ ] Confirmed: GG-105 stays OPEN through implementation; re-measurement against a fresh post-fix
      cohort (not the frozen epoch-3 diagnostic cohort) is required before any closure claim

**Sign-off:** _pending_
**Date:** _pending_
**Role:** DS — Earl Ignacio
