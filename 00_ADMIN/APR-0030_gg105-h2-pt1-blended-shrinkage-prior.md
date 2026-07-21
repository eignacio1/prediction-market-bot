# APR-0030 — Blend Pregame `p_t1` Into the `ba_l10` Empirical-Bayes Shrinkage Prior (GG-105 H2)

**Status:** DRAFT — not submitted for DS sign-off. This document proposes a hypothesis test and a
conditional remediation; it does not itself request implementation authorization. Per Hard Rule 3, if
DS accepts this proposal, a superseding ADR (analogous to ADR-0047) would still be required before any
`run_t4_mlb_live.py` change ships.
**Touches (if accepted):** `src/prediction_market_bot/run_t4_mlb_live.py::p_hits_gte_threshold()`'s
caller (line ~858, `ba_l10_shrunk` construction) and possibly `c2_feature_store/mlb_features.py` if the
blended prior is promoted to a feature-store field rather than computed inline at the T4 consumption
site. Also consumed identically by `t4_mlb_execution_engine.py:174` (currently registry-`BLOCKED`/dark).
**Drafted:** 2026-07-20, Window 1 (T-392)
**Prior remediation (for contrast):** APR-0025 / ADR-0047 (H1: empirical-Bayes shrinkage of `ba_l10`
toward its own cohort mean, K=40, real per-player `ab_sum` — ACCEPTED, DS sign-off 2026-07-17,
IMPLEMENTED and behaviorally live since 2026-07-18T18:07:19Z, epoch boundary per T-387)
**Diagnostic lineage:** T-359 (H1 dose-response sweep, APR-0025's evidence base) explicitly did not
test H2 and named it as the live, unremediated candidate for GG-105's residual anti-predictive gap —
"the gap does not close, even at the largest k tested" (APR-0025 §"What T-359 Found"). GG-105's own log
entry states H2 "remains deferred, not dropped — needs its own follow-on task/ID when picked up." This
document is that pickup.
**Approved by:** _not yet submitted_
**Effective:** _n/a — draft_

---

## Why This Proposal Exists

GG-105 is OPEN, now with a partial remediation (APR-0025/ADR-0047's H1 shrinkage) live in production
since 2026-07-18. That fix was explicit about its own limits: at every tested shrinkage strength up to
K=160, the anti-predictive tercile pattern narrowed in magnitude and significance but **never closed** —
positive-edge bets kept winning less often than negative-edge bets even at maximum tested shrinkage
(0.563 vs 0.619 winrate, K=160). APR-0025's own text named the mechanism this document now proposes to
test as the explanation for that residual: "H1 (unshrunk `ba_l10` noise) is a real, demonstrated
contributing mechanism, not necessarily the sole one. H2 (the discarded `p_t1` blend) was not tested
this session and remains a live, unremediated candidate for the residual."

Since APR-0025 shipped, GG-105's own post-fix re-measurement has not yet run (blocked on post-epoch-8
`clean_n` accumulating — see GG-124/GG-105 addenda, 2026-07-19). This document does not depend on that
re-measurement landing first; it proposes the H2 *test* as the next diagnostic step regardless of what
the H1-alone re-measurement shows, because APR-0025's own dose-response data already gives reason to
expect a residual gap. If the re-measurement shows the residual has in fact closed under H1 alone, H2
becomes moot and this proposal should be shelved without implementation — that determination is exactly
why this is a draft, not a request to build.

---

## The Mechanism, In the Actual Code

`ctx["p_t1"]` — T1's own calibrated pregame probability estimate — is loaded into T4's per-market
context dict at `run_t4_mlb_live.py:347` (`"p_t1": float(fc.get("p_estimate", 0.5))`) and is already
consumed elsewhere in the same function: it is passed to `store.stage_order(..., p_t1=ctx["p_t1"], ...)`
at line 1111 for audit/record-keeping. **It is never referenced in the `p_t4` computation path itself.**

The current (post-APR-0025) live calculation, at line 858 and 953-958:

```python
ba_l10_shrunk = market_ctxs[0].get("ba_l10_shrunk", ba_l10)   # line 858
...
p_t4 = p_hits_gte_threshold(
    h_so_far=...,
    threshold=...,
    ba_l10=ba_l10_shrunk,                                      # line 958
    ab_remaining=...,
)
```

`ba_l10_shrunk` itself (computed in `mlb_features.py` per ADR-0047) shrinks the raw per-player rolling
batting-average ratio toward the **cohort's own population mean** (`PRIOR=0.2512`, K=40): a single,
player-agnostic anchor. This is H1's fix — it addresses noise in the per-AB rate estimate, but the prior
it shrinks toward carries no player-specific information beyond what a handful of trailing at-bats
already encodes.

H2's structural claim: T1's pregame model (`p_t1`) is itself a calibrated, historically-validated
estimate of *this specific player's* outcome probability for *this specific game* — built from a richer
feature set (rolling stats, rest, home/away, PRF qualitative factors — CLAUDE.md § "T1 alpha") than the
10-game `ba_l10` window alone. `p_t1` and `ba_l10_shrunk` are estimating related but not identical
quantities (`p_t1` is a game-level hit-threshold probability; `ba_l10` is a per-AB rate), but they share
the same underlying player-quality signal. **A prior that blends toward `p_t1`-implied information,
rather than (or in addition to) a population-mean constant, could be a materially better-informed shrink
target than the current population mean** — closer to the player's true rate than an anonymous cohort
average, without reintroducing the small-sample noise H1 was built to suppress.

---

## Proposed Test (Diagnostic-Only, Analogous to T-359)

Before any live-formula change, run a T-359-style offline sweep — this is the necessary evidence step,
not yet performed, and this APR does not claim its outcome in advance:

1. **Derive a `ba_l10`-scale prior from `p_t1`.** `p_t1` is a threshold-hit probability, not a per-AB
   rate — it cannot be substituted directly as `ba_l10`'s prior without a conversion step. One candidate:
   invert `p_hits_gte_threshold()`'s own Binomial relationship to back out the implied per-AB rate
   consistent with `p_t1` at that player's pregame `ab_remaining`/threshold, then use *that* as the
   blend target instead of (or blended with) the population mean `PRIOR=0.2512`. This inversion step is
   itself a design decision requiring validation — the wrong conversion could inject T1's own miscalibration
   (if any) into T4's estimate, coupling two previously-independent alpha theses (CLAUDE.md's explicit
   T1/T4 independence framing) in a way that needs to be justified, not assumed harmless.
2. **Sweep a blend weight** analogous to T-359's `K` sweep — e.g. a second parameter `w ∈ [0, 1]`
   controlling how much of the shrinkage prior comes from the `p_t1`-derived rate vs. the existing
   population mean: `prior_blended = w * p_t1_implied_rate + (1-w) * PRIOR`, then apply the existing
   `ba_l10_shrunk = (ab_sum * ba_l10 + K * prior_blended) / (ab_sum + K)` formula with K held at its
   already-DS-approved value (40) unless the sweep gives reason to revisit it jointly.
3. **Re-run the same Fisher-exact tercile-monotonicity diagnostic** (T-359/T-373's methodology) across
   the `w` sweep, against a frozen, GG-105-safe cohort (the same discipline APR-0025 used: a fixed
   pre-epoch-8 cohort, not a live-mutating one), looking for whether any `w>0` narrows the residual gap
   further than K=40/w=0 (i.e., H1 alone) does, and whether the anti-predictive direction ever flips
   sign entirely (which would be a materially stronger result than H1's attenuation-only finding).
4. **Report honestly** whether the dose-response (if any) is monotonic in `w`, whether a residual gap
   persists at the tested maximum, and whether the T1/T4 coupling introduced by the inversion step (item
   1) shows any evidence of importing T1-side miscalibration into T4 rather than genuine signal.

**This document does not pre-select a blend weight, a conversion methodology, or claim the test will
show any effect at all.** Unlike APR-0025 (which had T-359's completed sweep as its evidence base before
drafting), this APR is proposing the test itself — the sweep has not been run. This is deliberate: the
user's instruction was to draft the APR for picking up H2, not to run new diagnostics in this session.

---

## Open Questions This APR Does NOT Pre-Decide

1. **The `p_t1` → per-AB-rate conversion methodology** (item 1 above) — this is a nontrivial modeling
   choice with more than one defensible approach (Binomial inversion vs. a simpler direct scaling vs.
   some other mapping) and should itself be reviewed before any sweep is trusted.
2. **Whether coupling T1 and T4 this way is architecturally sound at all.** CLAUDE.md is explicit that
   "T1 can prove edge while T4 has none... these are independent" and warns against conflating T1/T4
   verdicts. Blending `p_t1` into T4's own estimate is a deliberate, partial coupling of the two
   theses' information — not prohibited by that framing (which is about not conflating *verdicts*, not
   about forbidding shared inputs), but worth flagging explicitly as a design tension for DS review,
   since a T1 calibration problem could now leak into T4's edge computation in a way it structurally
   could not before.
3. **The blend weight `w`**, analogous to APR-0025's `K` — to be selected from sweep evidence, not
   asserted here.
4. **Whether this ships standalone or bundled with any further H1 K re-tuning** — APR-0025 fixed K=40
   as "a conservative default, not a data-fit optimum"; if this sweep is run, DS may want K and w
   considered jointly rather than treating K=40 as frozen.
5. **Sequencing against GG-105's own pending post-epoch-8 H1-alone re-measurement.** If that
   re-measurement (not yet run, blocked on `clean_n` accrual per GG-124) shows H1 alone has already
   closed the gap to a non-significant residual, this proposal's premise weakens and DS may reasonably
   choose to not prioritize H2 at all.

---

## What This Does NOT Claim

- **This does not claim H2 will improve anything.** No sweep has been run. The only evidence cited is
  APR-0025's own residual-gap finding, which motivates testing H2 — it does not predict H2's result.
- **This does not authorize any diagnostic script, sweep, or code change.** This is a draft proposal
  document only, per the explicit instruction governing this task ("draft, not implement").
- **This does not retract or supersede APR-0025/ADR-0047.** H1 shrinkage remains the live, DS-approved
  production behavior; this document proposes a possible second, additive remediation layered on top of
  it, not a replacement.
- **This does not change GG-105's OPEN status** or any of its pending re-measurement obligations.

---

## Broken-System Test

| Failure mode | How this draft prevents it |
|---|---|
| A future session reads this APR and starts implementing H2 directly, skipping the sweep | Explicitly scoped as "draft, not implement" in the Status line and reiterated in "What This Does NOT Claim"; the proposed test (sweep + Fisher re-check) is a prerequisite step, not optional |
| The `p_t1`→rate conversion is chosen ad hoc at implementation time without review | Named as an explicit open question (item 1) requiring its own validation before any sweep result is trusted |
| H2 is implemented as "the GG-105 fix" without acknowledging it structurally couples T1 and T4 for the first time | Named explicitly as open question 2, flagged for DS review rather than assumed harmless |
| This proposal is picked up before the H1-alone post-epoch-8 re-measurement has run, duplicating effort if H1 alone already resolved the gap | Open question 5 explicitly recommends checking that re-measurement's outcome first |
| A future K/w re-tune silently changes APR-0025's DS-approved K=40 without a fresh sign-off | Open question 4 flags joint K/w reconsideration as its own decision point, not a silent side effect |

---

## Review Checklist (for DS, when/if this is submitted)

- [ ] Reviewed APR-0025's residual-gap evidence (Fisher p 0.0045→0.1552, K=40→160; gap narrows but never
      closes) as the motivating premise for testing H2
- [ ] Decision: authorize the diagnostic sweep (item 1-4 above) as a follow-on task, or defer further
      pending the H1-alone post-epoch-8 re-measurement result
- [ ] If authorized: decide the `p_t1`→per-AB-rate conversion methodology, or delegate that choice to
      the task that runs the sweep with a requirement to present options rather than pre-select one
- [ ] Acknowledged: this draft does not authorize implementation; a sweep/diagnostic task ID and,
      separately, a superseding ADR (if a live-formula change is later proposed) both remain required
      per Hard Rule 3

**Sign-off:** _not yet submitted for DS review_
**Date:** _n/a_
**Role:** _n/a_
