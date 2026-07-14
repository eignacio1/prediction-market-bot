# Runbook: Data Contamination / Look-Ahead Bias (FM-02, CRITICAL)

**Purpose:** Detect and remediate look-ahead bias or temporal contamination in C1/C2 data — the failure mode that "silently destroys validity of all downstream validation" (`RESILIENCE_FAILURE_MODES.md`, FM-02).
**Owner (role):** Architecture Owner (AO) + Data Science Owner (DS)
**Last reviewed:** 2026-07-13
**Next review:** On any change to C1 ingestion, C2 feature store, or the TI-01–TI-04 rules; or on any EXP-0xx result that looks anomalously strong
**Staleness triggers:** New feature added to `feature_engineering.py`; new C1 data source; model retrain; any EXP result with suspiciously high accuracy
**Upstream links:** `RESILIENCE_FAILURE_MODES.md` (FM-02 definition), `02_ARCHITECTURE_DESIGN/DATA_FLOWS_LINEAGE.md` (TI-01–TI-04 rules)
**Downstream links:** `03_DECISIONS/GOVERNANCE_GAP_LOG.md` (GG-092), `08_MODEL_RISK_GOVERNANCE/`
**Decision references:** APR-0004 (TI-01–TI-04 captured at G2 gate), ADR-0004 (model governance)
**Confidence:** 7/10 — detection steps are grounded in real code paths; there is no single automated "run this and get a clean/dirty verdict" script for training-time contamination (see Known Gaps below), so this runbook is partly a manual audit checklist.

---

## Overview

FM-02 is training-pipeline data contamination — a model trained or validated on data that includes information it could not have known at forecast time (`T_forecast`). This is **not** the same thing as the live `CONTAMINATION_HALT` event emitted by `ContaminationGuard` in `c7_monitoring/semantic_contracts.py` during T4 live evaluation cycles. That guard checks *live data-window coherence at bet-evaluation time* (stale quotes, player no longer in the game, cycle desync) — a real-time integrity check, not a training-data leakage check. **The two concepts share the word "contamination" but are different failure modes with different code paths.** This runbook is scoped to FM-02 (training/feature-store leakage). If you are chasing a live `CONTAMINATION_HALT` count in `audit_mlb_t4.jsonl`, see CLAUDE.md Step 4's semantic-oracle checks instead — that is expected/routine at game-end (`market_active=False`) and is not this failure mode.

The four governing rules (`DATA_FLOWS_LINEAGE.md` TI-01–TI-04, captured at G2 via APR-0004):

| Rule | Requirement |
|------|-------------|
| TI-01 | All quantitative features computable using only data available at or before `T_forecast` |
| TI-02 | Training window ends before validation/test window begins — chronological split only, no random shuffling |
| TI-03 | Outcome data (`T_resolution`) must never appear in training data |
| TI-04 | Market prices used as features must be from a defined look-back window (e.g. ≥1 min pre-event), not post-event |

FM-02 is CRITICAL because a violation does not crash anything — it produces a model that backtests well and loses money live, and nothing in the pipeline raises an exception when it happens.

---

## Trigger Conditions

### Automatic

There is no single automated gate that blocks a contaminated model from being trained or deployed. Partial, real automated coverage exists:

| Signal | Where | What it catches |
|--------|-------|------------------|
| `shift(1)` applied before all rolling-window features | `c2_feature_store/feature_engineering.py` (rolling mean/std, efficiency composite, regime/streak flags — all tagged TI-01 ✅ in `DATA_FLOWS_LINEAGE.md`) | TI-01 violations in the *existing* rolling-stat feature set. Does not protect a newly added feature that forgets the shift. |
| `effective_from` date guard | `c2_feature_store/qualitative_store.py`, `QualitativeSignalStore.enrich_features()` | QTI-01 — qualitative (PRF) features joined only to game rows on/after their classification's effective date |
| `test_c2_features.py` | `tests/` | Confirms F-001–F-031 are TI-01 compliant (per `DATA_FLOWS_LINEAGE.md` line 174) — regression coverage on the *existing* feature set only |

### Manual (the real trigger, most of the time)

- A new feature is added to C2 and its temporal safety was not independently verified.
- A model's backtest/validation accuracy is implausibly high relative to the sport's known base rates — this is the single strongest empirical signal of leakage and should always prompt this runbook.
- An EXP-0xx result (`05_RESEARCH_EXPERIMENTS/`) shows a result that contradicts T1/T4 alpha-taxonomy expectations (see CLAUDE.md's alpha taxonomy section) without an obvious mechanism.
- Any new C1 data source is added — verify whether the source itself embeds future information (e.g. a stat that is only finalized post-game but back-dated to the game date).

---

## FM-02 Contamination Audit Procedure

Run this whenever a trigger above fires. This is a manual audit, not a single script — treat each step as a checklist item.

**Step 1 — Confirm TI-01 (no future data in features).** ≤15 minutes.
```bash
grep -n "shift(1)\|shift(-1)" src/prediction_market_bot/c2_feature_store/feature_engineering.py
```
Any rolling/aggregate feature computation that does NOT precede its `.rolling()`/`.expanding()` call with a `shift(1)` is a TI-01 candidate violation — a rolling mean computed without shifting first includes the current (unknown-at-forecast-time) row. Cross-check the feature against the F-0xx table in `DATA_FLOWS_LINEAGE.md` (lines ~148–174) — every active feature should carry a `✅ TI-01` annotation. A feature missing that annotation, or added since the table was last reviewed, needs manual derivation-window verification.

**Step 2 — Confirm TI-02 (chronological split).** ≤10 minutes.
Locate the train/validation split logic for the model in question (see `models/` training scripts, e.g. `scripts/train_*.py`). Confirm the split is by date (`df[df.game_date < cutoff]` style), never `train_test_split(..., shuffle=True)` or any random sampling. A shuffled split with time-series data is the single most common way TI-02 is silently violated.

**Step 3 — Confirm TI-03 (outcome data excluded from training features).** ≤10 minutes.
```bash
grep -n "outcome\|resolution\|result" src/prediction_market_bot/c2_feature_store/feature_engineering.py
```
Any hit here needs a manual check: is this field populated from data known strictly before `T_forecast`, or does it require the game to have already resolved? Outcome fields must be ingested by a separate path (post-resolution) and must never be joined into the pre-game feature matrix used for the forecast.

**Step 4 — Confirm TI-04 (market price look-back window).** ≤10 minutes.
For any feature that consumes a Kalshi/market price, confirm the fetch timestamp is strictly pre-event by the documented look-back window (e.g. `run_pregame.py`'s live Kalshi price snapshot, taken minutes before `run_paper_trade.py` fires — see `deploy/cron.conf`'s PIPE-02 comment on the 5-minute gap). A market price feature that could include post-event price movement is a TI-04 violation.

**Step 5 — Spot-check via holdout sanity.** ≤20 minutes.
If Steps 1–4 pass but the suspicion remains (e.g. implausibly strong backtest), pull 5–10 resolved bets from `paper_portfolio_mlb.json` at random and manually reconstruct: what data would genuinely have been available at the recorded `T_forecast` timestamp? Compare against what the feature matrix row actually contains for that game/player/date. A mismatch is direct evidence of leakage.

**Step 6 — Escalate if confirmed.** Any confirmed TI-01–TI-04 violation is a P1-equivalent finding:
1. Register in `03_DECISIONS/GOVERNANCE_GAP_LOG.md` immediately (do not wait for session-end — Hard Rule 7).
2. Identify every model version trained on the contaminated feature/window and flag its EXP-0xx results as suspect in `05_RESEARCH_EXPERIMENTS/RESULTS_SUMMARIES/`.
3. If the contaminated feature is currently live in production (`c2_feature_store`), this is a live-system integrity issue — treat with the same urgency as a kill-switch-adjacent event even though FM-02 itself has no automated kill-switch trigger. Consider whether affected paper-trading results should be excluded from G6 sample-adequacy counts (`clean_n`) pending DS review.
4. Fix (add the missing `shift(1)`, correct the split, exclude the field, or correct the look-back window) and re-run the model's validation from scratch — a contaminated model must be retrained, not patched.

---

## Known Failure Modes

| Failure mode | Cause | Detection signal | Mitigation |
|---|---|---|---|
| New rolling feature ships without `shift(1)` | Feature added without following the TI-01 pattern used by existing features | Backtest accuracy anomalously high; Step 1 grep shows the feature's rolling call unshifted | Code review checklist item for any C2 PR: does every new rolling/aggregate feature have TI-01 annotation + shift? |
| Random train/test split reintroduced | A generic ML tutorial pattern (`train_test_split(shuffle=True)`) copy-pasted into a new training script | Step 2 audit finds `shuffle=True` or no explicit date cutoff | Training script template should hardcode chronological split; new scripts should copy from an existing TI-02-compliant script |
| Outcome field leaks via a joined-in "context" table | A convenience join (e.g. team season summary) that itself was computed using full-season data including future games | Step 3 grep may not catch this if the outcome leakage is indirect (aggregated stat, not a raw `outcome` column) | When adding any joined external table, ask explicitly: "was this table computed using only data through T_forecast?" |
| Qualitative (PRF) classification backdated without evidence | QTI-03 violation — an operator backdates a QS snapshot's `effective_from` without justification | `backdated`/`backdating_rationale` fields empty or missing in QS snapshot | QTI-03/QTI-04 (`DATA_FLOWS_LINEAGE.md`) — backdating requires explicit evidence + second review; QS snapshots immutable once registered |

---

## Known Gaps (surfaced during this runbook's authoring, 2026-07-13)

- **No single automated "run this, get PASS/FAIL" contamination check exists** for TI-01–TI-04 as a whole — coverage is distributed across `test_c2_features.py` (existing features only), the `shift(1)` pattern (convention, not enforced by a linter), and the `effective_from` guard (QTI-01 only). `RESILIENCE_FAILURE_MODES.md`'s FM-02 detection cell ("automated overlap check fails") describes an aspiration; no file matching `*overlap_check*`/`*temporal_overlap*` exists in `src/`, `scripts/`, or `tests/` as of this writing. This gap itself may warrant a future T-NNN (build a real automated TI-01–TI-04 checker) — noted here rather than silently worked around, per this runbook's own audit standard.
- This runbook does not cover MLB-specific temporal quirks (e.g. suspended/resumed games, doubleheaders) in depth — if a contamination incident involves either, treat Step 5's holdout sanity check as mandatory rather than optional.

---

## References

- `RESILIENCE_FAILURE_MODES.md` — FM-02 canonical definition (CRITICAL severity)
- `02_ARCHITECTURE_DESIGN/DATA_FLOWS_LINEAGE.md` — TI-01–TI-04, QTI-01–QTI-04 full rule table
- `src/prediction_market_bot/c2_feature_store/feature_engineering.py` — feature computation, `shift(1)` pattern
- `src/prediction_market_bot/c7_monitoring/semantic_contracts.py` — `ContaminationGuard` (live/T4 — a different failure mode, see Overview)
- `03_DECISIONS/GOVERNANCE_GAP_LOG.md` — GG-092
- `10_INFRA_OPERATIONS/RUNBOOKS/RUNBOOK_kill-switch.md` — format template this runbook follows
