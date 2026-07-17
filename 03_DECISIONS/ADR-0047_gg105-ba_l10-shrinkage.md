# ADR-0047 — GG-105: Empirical-Bayes Shrinkage of ba_l10 for T4M-PROJ (ACCEPTED)

**Status:** ACCEPTED — DS sign-off received (operator, Earl Ignacio, 2026-07-17; see DECISION_LOG.md 2026-07-17 entry).
**Date:** 2026-07-17
**Session:** T-382, isolated worktree `20260717T201405Z-apr0025-gg105-ba-l10-shrinkage`.
**Operator:** Earl Ignacio
**Scope:** MLB feature store (`c2_feature_store/mlb_features.py`), T1 pregame audit surfacing (`run_mlb_pregame.py`), and T4M-PROJ's live Binomial gating calc (`run_t4_mlb_live.py`). No change to `risk.py` `_HARD_LIMITS`, no change to C3's frozen model class (ADR-0004), no NBA impact, no change to T1's live gating formula (audit-only surfacing there — see D3), no change to the dark/BLOCKED `t4_mlb_execution_engine.py` (T4M-ARITH/T4M-FLOW, ADR-0039 Tier B) or any of its sub-bands.
**Supersedes / relates:** Implements APR-0025 (ACCEPTED, 2026-07-17) — the DS-approved remediation for GG-105 (statistically significant, tercile-monotonic anti-predictive relationship in T4M-PROJ: higher stated model confidence correlates with *lower* observed win rate). Relates to GG-124 (separate, self-resolving clean_n/UNDERPOWERED gap across all active MLB bands — no code change, wait-and-monitor sign-off, logged separately in the same DECISION_LOG entry as this ADR). Does not supersede ADR-0039 (T4M-ARITH/T4M-FLOW governance) or ADR-0024/APR-0024 (commercial validation gate). Temperature scaling was tested and ruled out as an alternative fix prior to this ADR (see APR-0025 Context) — not re-litigated here.

---

## Context

GG-105 found a statistically significant, monotonic-across-terciles anti-predictive pattern in T4M-PROJ's resolved book: bets where the live model reported *higher* confidence resolved at a *lower* win rate than bets reported with lower confidence. Temperature scaling (a global recalibration of reported probabilities) was tested against the same data and did not reproduce or explain the pattern — ruled out as the fix. The surviving diagnosis (APR-0025): `ba_l10`, the batting-average-over-last-10-games input feeding T4M-PROJ's live Binomial hit-probability calc (`p_hits_gte_threshold()`), is a raw sample ratio computed over a small and variable at-bat count. Small-sample ratios are noisy estimators — a player who has gone 3-for-5 in limited recent at-bats produces a `ba_l10` of 0.600, an extreme value driven by sampling noise rather than true talent, and the live calc trusted that raw ratio as if it were a stable rate. This is the textbook condition empirical-Bayes shrinkage exists to correct: shrink noisy small-sample estimates toward a stable prior, weighted by how much real data actually supports the raw estimate.

APR-0025 (DS-approved, 2026-07-17) authorized a shrinkage fix with three open parameters, each resolved by the operator's sign-off this session:

- **D1 — Shrinkage strength `K=40`** (of the two candidates presented, K=40 vs. a lighter alternative; K=40 selected as Recommended).
- **D2 — Use real per-player `ab_sum`** (already computed by the existing rolling-window feature calc) as the observed-sample-size term, rather than continuing to use the flat `AB_WINDOW=37` constant the pre-fix code implicitly assumed.
- **D3 — Ship the shrinkage fix alone now; defer H2** (a second hypothesis — blending in the pregame T1 model's calibrated probability, `p_t1`, as an additional signal) **to a later, separately-scoped task.** H2 is not tested or implemented under this ADR.

**Why K=40 and not a data-fit optimum:** the operator selected the Recommended option presented, which was chosen for being a conservative, defensible shrinkage strength rather than a value fit to minimize backtest error on the same data the anti-predictive pattern was found in — fitting K to that data would risk re-introducing a form of the same overfitting problem this fix exists to correct. This is a judgment call, not a derived optimum, and is logged as such.

**PRIOR=0.2512 provenance:** this is not an external or unsourced figure. It is the epoch-3 cohort's own observed mean `ba_l10` (T-359, n=666) — an internal, data-derived constant already computed and logged elsewhere in this project's history, reused here as the shrinkage target.

## Decision

**D1 — Empirical-Bayes shrinkage formula, K=40, PRIOR=0.2512.** Implemented in `c2_feature_store/mlb_features.py` as a new column, `ba_l10_shrunk`, computed alongside (not replacing) the existing `ba_l10`:

```python
GG105_SHRINKAGE_K = 40
GG105_SHRINKAGE_PRIOR = 0.2512

ba_l10_shrunk = (h_sum + GG105_SHRINKAGE_K * GG105_SHRINKAGE_PRIOR) / (
    ab_sum + GG105_SHRINKAGE_K
)
df["ba_l10_shrunk"] = ba_l10_shrunk.where(ab_sum.notna())
```

This is algebraically `(ab_sum * ba_l10 + K * PRIOR) / (ab_sum + K)`, computed directly from `h_sum`/`ab_sum` rather than from the already-computed `ba_l10` ratio, so its NaN behavior is exact rather than a NaN-propagation side effect: `ba_l10_shrunk` is NaN only when `ab_sum` itself is NaN (fewer than `MIN_PERIODS=3` prior games — no window to shrink from at all), and is a well-defined, fully-shrunk-to-`PRIOR` value when `ab_sum == 0` (a populated window with zero recorded at-bats — itself informative under empirical Bayes, not a missing-data condition). This intentionally differs from `ba_l10`'s own `_safe_div()`-based NaN-on-zero-denominator rule; the two columns are not expected to share identical NaN masks by design.

`MLB_FEATURE_VERSION` bumped `1.0.0` → `1.1.0` (additive column, no existing feature's values changed).

**D2 — Real per-player `ab_sum` as the observed-sample-size term**, already available from the existing rolling-window computation (`.shift(1).rolling(window, min_periods=min_periods).sum()`) — no new computation, no continued use of the flat `AB_WINDOW=37` constant.

**D3 — Scope: T4M-PROJ only, T1 is audit-only, H2/H4/T4M-ARITH-FLOW are out of scope.**

- `run_t4_mlb_live.py`: `ba_l10_shrunk` is read from the pregame context (with fallback to raw `ba_l10` for any pregame JSON predating this fix) and is the value passed into the live Binomial calc: `p_hits_gte_threshold(..., ba_l10=ba_l10_shrunk, ...)`. This is the actual behavioral fix — T4M-PROJ's live gating now evaluates against the shrunk estimate instead of the raw small-sample ratio. Both `ba_l10` (raw) and `ba_l10_shrunk` are written to both audit-log record types (the unconditional per-cycle record and the `dry_run` record) for post-hoc comparison.
- `run_mlb_pregame.py` (T1): `ba_l10_shrunk` is surfaced into the pregame JSON's `fc` dict for audit/backtest comparison only. T1's forecasting model is the frozen C3 LR+Platt model (ADR-0004) and does not consume this field — T1's live gating formula is unchanged by this ADR.
- H2 (blending `p_t1` into the T4 estimate) is explicitly deferred per the DS sign-off, not tested, not implemented. A follow-on task should be registered separately when picked up.
- `t4_mlb_execution_engine.py` (T4M-ARITH/T4M-FLOW, ADR-0039 Tier B, registry status BLOCKED) is untouched — those bands require their own EXP-ARITH-MLB-01/EXP-FLOW-MLB-01 clearance before activation regardless of this fix, per existing governance.

**Hard Rule 4 (frozen model policy) — explicitly addressed, not silently assumed:** `mlb_features.py`'s existing docstring states a version bump requires "Model retrain required." This refers to C3's frozen LR+Platt pregame model. `ba_l10_shrunk` is a new, additive column that C3's frozen model does not consume — T4M-PROJ's live Binomial calc (`p_hits_gte_threshold()`) is not a trained/frozen artifact subject to ADR-0004's retraining freeze; it is a deterministic formula whose input is being corrected. This version bump does not trigger, and is not exempted from, Hard Rule 4 — it simply does not implicate it, because no frozen trained model is being retrained or having its input distribution silently changed underneath it. This reasoning is stated here explicitly per this ADR's own drafting requirement, not left as an implicit assumption.

## Consequences

- **Positive:** T4M-PROJ's live gating now evaluates against a shrinkage-corrected hit-rate estimate instead of a raw, small-sample-noisy ratio — directly targets the mechanism APR-0025 diagnosed as the source of GG-105's anti-predictive pattern. Both raw and shrunk values remain visible in every audit record, preserving full backtest comparability between the two.
- **Negative / cost (accepted):** This changes T4M-PROJ's live gating math, which is a version/logic change to an active band. Per this project's own precedent (ADR-0043 D2), a logic change of this kind typically triggers a `CURRENT_LOGIC_EPOCH` advance and an associated `clean_n` reset for T4M-PROJ. This ADR flags that consequence but does not itself execute the epoch bump — that is an operational step to confirm at deploy time, tracked under Open items below.
- **Explicitly deferred, not resolved by this ADR:**
  - **GG-105 stays OPEN.** This ADR implements the DS-approved remediation; it does not itself constitute proof the anti-predictive pattern is resolved. A fresh re-measurement of the tercile-monotonicity check against a clean, post-fix epoch cohort is required before GG-105 can be marked RESOLVED. Do not treat this ADR's merge as closing GG-105.
  - **GG-124** (clean_n/UNDERPOWERED across all active MLB bands, self-resolving) is unaffected by this ADR and is logged separately with its own wait-and-monitor sign-off in the same DECISION_LOG entry as this ADR's decisions.
  - **H2** (blending `p_t1` into the T4 estimate) — deferred, not implemented, not tested. Requires its own follow-on task/ID when picked up.
  - K=40 is a DS-selected conservative default, not a data-fit optimum — re-derivation against a larger post-fix sample is legitimate future work, not a defect in this ADR.

## Evidence / reproducibility

- Code: `c2_feature_store/mlb_features.py` (`GG105_SHRINKAGE_K`, `GG105_SHRINKAGE_PRIOR`, `ba_l10_shrunk` column, `MLB_FEATURE_VERSION` 1.0.0→1.1.0), `run_mlb_pregame.py` (`ba_l10_shrunk` surfaced in `fc` dict, audit-only), `run_t4_mlb_live.py` (`ba_l10_shrunk` read from pregame context with raw-value fallback; passed into `p_hits_gte_threshold()`; written to both audit-log record types).
- APR-0025 (`00_ADMIN/APR-0025_gg105-ba_l10-shrinkage-remediation.md`, ACCEPTED 2026-07-17) — the governing DS sign-off document; all Review Checklist items closed.
- DECISION_LOG.md 2026-07-17 entry (T-382) — D1/D2/D3 decisions and GG-124's separate sign-off logged immediately per Hard Rule 7.
- Regression tests: see Open items — full suite run pending as of this ADR's drafting; results to be appended once run.

## Open items

- Confirm whether this fix requires a `CURRENT_LOGIC_EPOCH` advance for T4M-PROJ (per ADR-0043 D2 precedent for logic changes to an active band's live formula) — not yet executed as part of this ADR; a deploy-time decision to confirm.
- Full test suite run and any new/updated regression tests targeting `ba_l10_shrunk` — tracked as this session's Task #7, not yet complete as of this ADR's drafting.
- Fresh post-fix re-measurement of GG-105's tercile-monotonicity check against a clean epoch cohort, once sufficient post-fix `clean_n` accumulates — required before GG-105 can be marked RESOLVED.
- H2 (pregame `p_t1` blending) — register a follow-on task/ID when picked up; explicitly not part of this ADR's scope.
- GOVERNANCE_GAP_LOG.md update for GG-105 (remediation-in-progress, stays OPEN) and GG-124 (wait-and-monitor sign-off logged) — tracked as this session's Task #8, not yet complete as of this ADR's drafting.
