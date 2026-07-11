# T-333 — Scope: GG-105 Diagnostic (3) + Edge-Formula Audit Follow-On

**Date:** 2026-07-11
**Author:** Session (GG-105 follow-on to Workstream B / T-324, T-329, T-332)
**Status:** SCOPING ONLY. No diagnostic run in this task, no code changes to
the live edge formula. Not authorized for implementation beyond what §2.5
explicitly rules in/out. Feeds GG-105 / GG-004.
**Inputs:** `T324_T1_VS_T4_DIVERGENCE_MEMO.md`, GG-105's T-329 (size-weighted
re-run) and T-332 (game-state segmentation) resolution entries, and a direct
read of `src/prediction_market_bot/run_t4_mlb_live.py` (this session).

---

## 0. Why this task exists

GG-105 registered a statistically significant, tercile-monotonic
ANTI-PREDICTIVE relationship between T4M-PROJ's own computed edge and
realized win rate on clean data. Three diagnostics were originally proposed
in the T-324 memo: (1) size-weighted re-run, (2) game-state segmentation,
(3) re-run as clean_n grows past its immature-cadence window. (1) and (2)
are now done — T-329 ruled out sizing artifact as an explanation (found the
*opposite*: larger-edge terciles return more per dollar staked despite lower
win rate), and T-332 ruled out game-state concentration as an explanation
(the inversion reproduces independently in both game-state buckets large
enough to test). Diagnostic (3) was never executed — it was recommended,
not run.

Ruling out (a) game-state noise and (b) sizing artifact does more than leave
diagnostic (3) outstanding — it actively redirects suspicion toward the one
thing invariant across every game-state bucket T-332 tested: the `p_t4` /
edge computation itself. That is the new, higher-value component this task
scopes alongside the original diagnostic (3).

Per the user's directive — *"Scope diagnostic 3 and the edge-formula
follow-on as a new task - apply full institutional depth"* — this document
is the scope, not the execution. Consistent with this project's own
precedent (CLAUDE.md's ADR-0039 Tier B roster: *"Scoping-only. Not
authorized for implementation without a fresh, explicit DS sign-off"*),
scoping and implementation-authorization are kept as separate, explicit
steps here too.

---

## 1. Component A — Diagnostic (3): clean_n cadence re-run

The last of the three originally-proposed diagnostics. Simplest to
describe, cheapest to run — gated on time/data accrual, not on analysis
design.

- **What:** re-run T-324's tercile/Fisher edge-monotonicity methodology
  (identical machinery T-329/T-332 already reused: `run_band_monitor.py`'s
  `load_t4_ledger`/`filter_clean`/`to_mlb_positions`, and
  `run_exp017_mlb.edge_monotonicity()`) against the then-current `clean_n`
  cohort for T4M-PROJ.
- **Why insufficient now:** the clean epoch started 2026-07-06; as of T-332
  (2026-07-11) it is 5 calendar days / n=271 — short of T-324's own flagged
  14-day "immature cadence" floor, and short of T-323's n*=836 power target
  for `edge>0` detection (a related but distinct question).
- **Trigger condition, not a fixed date:** run when EITHER (i) the clean
  epoch crosses 14 calendar days of age (≈2026-07-20, assuming no
  epoch-resetting contamination event before then — recompute this live from
  `CURRENT_LOGIC_EPOCH`'s actual start, do not hardcode the date into any
  script), OR (ii) T4M-PROJ `clean_n` roughly doubles from its T-332 value
  (≈n=540), whichever comes first.
- **Exit criteria / possible outcomes:**
  1. Inversion persists at larger n/longer window → strengthens the case
     that Component B (edge-formula audit) found a real, structural cause,
     and elevates its priority from "investigate" to "fix."
  2. Inversion attenuates or disappears → suggests the original finding was
     a short-window artifact; downgrades Component B from urgent to
     routine follow-up.
  3. Inversion changes shape (e.g., stops being monotonic) → needs fresh
     interpretation; not covered by this scope.
- **Effort:** trivial. Reuse existing audited helpers verbatim — no new
  statistical methodology, per this project's standing discipline against
  reimplementing audited math (the same discipline T-329/T-332 followed).

---

## 2. Component B — Edge-formula audit (the new, higher-value follow-on)

### 2.1 What T-332's findings point to

T-332 tested whether the inversion concentrates in a specific game-state
slice (inning, ab_remaining) and found it does not — both buckets large
enough to test (`inning=early_1-3`, n=136; `ab_remaining=2+`, n=213)
independently reproduce ANTI-PREDICTIVE. A pattern that survives
segmentation by every live-state variable tested points toward the
computation applied uniformly across all of them: the `p_t4`/edge formula
and its inputs.

### 2.2 Concrete code entry points (read-only investigation this session, no changes made)

- `src/prediction_market_bot/run_t4_mlb_live.py:584-608` —
  `p_hits_gte_threshold()`, the actual live `p_t4` formula. A Binomial
  tail-probability computation: `P(total_hits >= threshold | h_so_far,
  ab_remaining, ba_l10)`, using `ba_l10` as a fixed per-AB Bernoulli
  parameter (clamped to `[0.001, 0.999]`) applied uniformly across every
  remaining at-bat.
- `src/prediction_market_bot/run_t4_mlb_live.py:945-954` — call site:
  `p_t4 = p_hits_gte_threshold(...)`; `gross_edge = p_t4 - mip - vig`;
  `kalshi_fee = 0.07 * mip * (1.0 - mip)`; `net_edge = gross_edge -
  kalshi_fee`.
- `src/prediction_market_bot/run_t4_mlb_live.py:334-346` — pregame context
  loader: `ba_l10` is sourced from `pregame_mlb` JSON forecast records,
  default-filled to a flat `0.25` when missing
  (`float(fc.get("ba_l10") or 0.25)`). `p_t1` — the calibrated T1
  LR+Platt-scaling estimate (ADR-0004) — is loaded into the same context
  dict (`ctx["p_t1"]`) but is **never passed into `p_hits_gte_threshold()`
  or used anywhere in the T4 edge computation.**
- `src/prediction_market_bot/run_t4_mlb_live.py:276-306` —
  `_compute_ab_remaining()`: a slot-aware AB estimator that falls back to a
  flat `AB_PER_GAME_DEFAULT` (3.7) when `batting_slot` is unknown (`0`).
  Per T-332's finding that `batting_slot` is hardcoded/near-constant at `0`
  in 19,202/19,275 (99.6%) of cycle-log rows system-wide, this estimator is
  almost always running the flat-default path rather than the slot-specific
  table in live production — a compounding data-quality gap layered on top
  of the `ba_l10` question, not yet assessed for its own contribution to
  the inversion.

### 2.3 Testable hypotheses (none yet verified — this is the proposed test list, not a finding)

1. **H1 — uncalibrated small-sample statistic used as a fixed Bernoulli
   parameter.** `ba_l10` is a batting average over a ~10-game / ~35-40-AB
   rolling window — high sampling variance, and a rolling BA over this
   window size is a well-known noisy, mean-reverting statistic. Using it
   directly and unregressed as the per-AB hit probability for the rest of
   the game may systematically overpredict `p_t4` for players currently on
   a hot streak (elevated `ba_l10` from variance, not true talent shift)
   and underpredict for cold-streak players. If so, the model's *largest*
   computed edges would concentrate on the most extreme, least reliable
   `ba_l10` readings — mechanically consistent with GG-105's
   tercile-monotonic inversion (largest computed edge → worst realized win
   rate).
2. **H2 — T1's calibration is loaded but discarded.** `p_t1` sits in the
   same context dict as `ba_l10` (line 343) but is never consumed by
   `p_hits_gte_threshold()`. If T1's calibrated estimate is better
   calibrated than raw `ba_l10` (plausible — per CLAUDE.md's Principal
   Vision, that calibration is the entire premise of T1's existence), T4
   is discarding its most calibrated available signal at exactly the step
   where GG-105 finds the inversion. Test: does blending or replacing
   `ba_l10` with a `p_t1`-informed prior change the tercile pattern in an
   offline ledger-replay backtest?
3. **H3 — default-fill masking.** Any cycle where `ba_l10` was missing from
   the pregame JSON silently defaults to `0.25` rather than surfacing as a
   data gap. Test: what fraction of the 271 clean_n resolved positions
   actually hit this default, and does the inversion differ between
   default-filled and real-`ba_l10` subsets? (Mirrors the
   `batting_slot`-is-99.6%-zero discipline T-332 already applied to a
   different field.)
4. **H4 — `ab_remaining` estimator drift under the near-universal
   `batting_slot=0` fallback.** Quantify how far the flat-default path
   deviates from a genuinely slot-aware estimate, and whether that
   deviation correlates with edge-magnitude tercile.
5. **H5 — vig/fee treatment.** `gross_edge = p_t4 - mip - vig` subtracts
   vig from `p_t4` before comparing to `mip`; a separate 7%-of-`mip*(1-mip)`
   Kalshi taker fee is subtracted again into `net_edge`. Confirm both terms
   carry the sign/direction the T-329/GG-087 direction-aware fixes intended
   — candidate (c) pre-epoch bug residue was ruled out *for the positions
   already in clean_n*, but this audit should re-derive the formula from
   first principles rather than only trusting that clean_n filtering caught
   everything relevant to a formula that is still live and still running.

### 2.4 Method (proposed, not yet executed)

- **Ledger-replay backtest, not a live-trading change.** Re-derive
  `p_t4`/`gross_edge`/`net_edge` for the same 271 clean_n resolved
  positions T-329/T-332 used, directly from `p_hits_gte_threshold()` and
  the stored cycle-log inputs (`h_so_far`, `ab_remaining`, `ba_l10`) —
  independently of the stored `edge`/`fee_net_edge` fields, continuing this
  project's standing discipline (GG-077/GG-100/GG-098) of never trusting a
  stored edge field.
- **H1/H2:** construct an alternative `p_t4'` using a shrunk/regressed
  `ba_l10` (e.g., toward league-average or toward `p_t1`) and re-run the
  identical tercile/Fisher test against realized outcomes. Diagnostic-only
  — two offline recomputations compared against history, not a change to
  the live formula.
- **H3:** a simple `ba_l10 == 0.25`-exact-match split, reusing the
  `forecast_id`→`cycle_id` join infrastructure T-332 built and validated
  (100% join rate, 0 collisions).
- **H4:** compare `_compute_ab_remaining()`'s slot-fallback output against
  a hypothetical slot-aware value, for the subset of cycles where real slot
  data happens to be available via `_load_t2_batting_slots()`.
- **H5:** static code/formula review plus a hand-worked numeric example,
  cross-checked against `run_exp017_mlb.compute_fee_net_edge()`'s
  independently-audited version of the same computation.

### 2.5 Explicitly out of scope for this task

- **No change to the live `p_t4`/edge formula in `run_t4_mlb_live.py`.**
  This task produces findings and a recommendation. Any actual formula
  change is a separate, future implementation task requiring its own DS
  sign-off — consistent with CLAUDE.md's ADR-0039 Tier B convention and
  Hard Rule 3 (ADRs are immutable; a superseding ADR is required for any
  model-class-level change touching C3 methodology).
- No change to `_compute_ab_remaining()`, `_load_t2_batting_slots()`, or
  any other live pipeline code.
- No new capital/exposure decision. T4M-PROJ's ACTIVE status is unaffected
  by this scoping task; if the audit produces a strong finding, it
  escalates through GG-105/GG-004 exactly as T-329/T-332 already have, not
  through a silent code fix.

### 2.6 Risks / assumptions

- **Data availability assumption:** `ba_l10` per-cycle is already captured
  in `t4_mlb_cycle_log.jsonl` (confirmed present in the schema per T-332),
  so H1/H3 do not depend on recovering historical `pregame_mlb` JSONs.
  H2's `p_t1`-blended alternative may need a direct check for whether
  `p_t1` itself is captured per-cycle anywhere in the resolved-position
  trail — not yet confirmed; if it isn't, H2 may require a fresh pregame
  JSON pull rather than a pure ledger-replay.
- **Small-n risk carries forward from T-332.** Any hypothesis-specific
  subgroup (e.g., default-filled vs. real `ba_l10`) must clear `MIN_N=30`
  (GG-098 discipline) before returning a statistical verdict; smaller
  subsets get descriptive-only treatment.
- **Multiple-hypothesis risk.** Five hypotheses tested against the same
  n=271 cohort raises a look-elsewhere-effect concern. No Bonferroni-style
  correction is proposed here because the intent is exploratory triage
  (which hypothesis deserves a targeted follow-up), not a final
  confirmatory claim. Any hypothesis that looks promising should be
  earmarked for independent re-verification (e.g., against Component A's
  larger future cohort) before being treated as resolved.

---

## 3. Sequencing

- **Component A** (diagnostic 3) is a passive trigger-condition re-check —
  no dedicated session needed until the §1 trigger fires. Track it in
  `TODO_NEXT.md` as a standing watch item, not an active work item.
- **Component B** (edge-formula audit) is ready to start now — code entry
  points are identified (§2.2), inputs exist (clean_n cohort, cycle-log
  data with `ba_l10` already captured), and it has no blocking dependency
  on Component A's cadence.
- Recommend Component B as the next active GG-105 work item. Component A
  converts from "scoped" to "active" automatically when its trigger
  condition fires — no separate task number needed at that point unless
  its findings warrant a dedicated memo.

---

## 4. Recommendation

1. Treat this as two independently-schedulable items under GG-105, not one
   monolithic task.
2. Prioritize Component B (edge-formula audit) — it is fully scoped, has
   concrete code targets, and directly follows from T-332's finding that
   the inversion is not game-state-concentrated.
3. Component A remains a standing watch item; revisit when clean_n crosses
   ~540 or the clean epoch crosses 14 days, whichever comes first.
4. Any hypothesis in §2.3 that survives the audit with a strong effect
   should be escalated to a fresh, explicit implementation task with its
   own DS sign-off before any live-formula change — per CLAUDE.md's
   ADR-0039 Tier B precedent and Hard Rule 3. This document authorizes
   investigation only, not remediation.
