# Experiment Record — EXP-ARITH-MLB-01: T4M-ARITH Near-Certainty Boundary Calibration

**Status:** PLANNED  
**Experiment ID:** EXP-ARITH-MLB-01  
**Owner:** EL  
**Hypothesis tested:** T4M-ARITH alpha hypothesis (ADR-0039) — see Objective  
**Research question:** Does a dedicated near-certainty Binomial band, entered only in the last hit-and-AB window before a threshold resolves, produce calibrated probabilities that beat market price, independent of and in addition to the flat T4M-PROJ model?  
**Started:** (not started)  
**Completed:** (not started)

**Governance note — read before acting on this document:** T4M-ARITH is registered `status="BLOCKED"` in `T4_MLB_SUBBAND_REGISTRY` (`execution_bands.py`), gated on this exact experiment ID (`exp_gate=("EXP-ARITH-MLB-01",)`) per ADR-0039/T-219. **This document defines methodology only. It does not authorize running this experiment, registering data snapshots, or any Phase 8 activation.** T4M-ARITH cannot fire a paper or live bet until this experiment runs, is interpreted, and clears its own Phase 8 Activation Gate + APR, independent of T4M-PROJ's existing ADR-0023 approval.

---

## Objective

`T4MlbArithEvaluator` (`t4_mlb_execution_engine.py`) carves out a narrow band between the flat model's two hard boundaries — `h_so_far >= threshold` (p=1.0, trivial) and `h_needed > ab_remaining` (p=0.0, trivial) — where a batter is exactly `_ARITH_ENTRY_WINDOW` (currently 1) hit away from their market threshold and the resulting Binomial `p_arith` clears `_ARITH_CONFIDENCE_GATE` (currently 0.80). The hypothesis: in this near-certainty band, Binomial variance has contracted enough (few ABs remain, high per-AB hit probability) that the true probability is more sharply estimable than T4M-PROJ's general-purpose flat model treats it, and market makers under-react to how close a threshold is to resolving relative to remaining ABs — creating a distinct, additive edge source on top of (not a replacement for) T1/T4M-PROJ's pregame-calibrated baseline.

This experiment answers whether that additive edge is real, or whether `p_arith` in this band is already fully priced by market makers who correctly discount thin-AB variance themselves (in which case T4M-ARITH would fire on already-efficient prices and add no value beyond noise-buffer risk).

---

## Snapshot IDs Used

*Not yet registered — no experiment has run. To be filled per `DATA_SNAPSHOTS_INDEX.md` protocol at Phase 8 Activation, using resolved MLB T4M-PROJ paper-trading history plus retrospectively-reconstructed in-game AB sequences (h_so_far/ab_so_far/inning/batting_slot at each qualifying cycle) for games where a batter entered the `_ARITH_ENTRY_WINDOW` band at any point.*

| Snapshot ID | Dataset | Description | Ingested |
|-------------|---------|-------------|----------|
| (TBD) | `logs/t4_mlb_cycle_log.jsonl` (GG-067, SESSION 110) | Raw per-cycle context (`ts, cycle_id, session_id, game_date, ticker, player_name, player_id, threshold, p_t4, mip, vig, gross_edge, net_edge, ba_l10, h_so_far, ab_so_far, ab_remaining, inning, batting_slot`) written unconditionally by `run_t4_mlb_live.py::_run_cycle()` for every cycle reaching the p_t4/gross_edge computation, independent of dry_run/fired status. Did not exist before SESSION 110 — only rows from games since that deploy can appear. | (TBD) |
| (TBD) | Kalshi KXMLBHIT resolved market prices, via MLB Stats API outcome resolution | `mip`/`vig` are already embedded per-cycle in the row above; final resolved hit totals per player/game are fetched at backtest time via `run_resolve_mlb.fetch_actual_hits(player_id, game_date)`, not from a separate price-cache audit log | (TBD) |

---

## Code Reference

| Item | Detail |
|------|--------|
| Commit hash | (TBD — pin to the commit at experiment run time) |
| Script / notebook | `t4_mlb_execution_engine.py::T4MlbArithEvaluator` (evaluator under test); `scripts/run_exp_arith_mlb_01.py` (offline backtest runner, built SESSION 110) — reads `logs/t4_mlb_cycle_log.jsonl`, grid-sweeps `entry_window`/`confidence_gate`, resolves outcomes via `run_resolve_mlb.fetch_actual_hits`, computes EV/ADR-0024 tiering/edge monotonicity (Fisher). Requires `BOT_ENV=paper`. Tests: `tests/test_run_exp_arith_mlb_01.py` (36 tests, no live network calls). |
| Dependency lock | (TBD) |

---

## Experimental Design

**Train window:** (TBD — must postdate T4M-PROJ's live-paper-trading start so enough resolved games exist to retrospectively identify qualifying cycles)  
**Validation window:** (TBD)  
**Test window:** (TBD; held out per standard protocol)  
**Split method:** Chronological (no random shuffling) — consistent with project-wide temporal integrity policy

**Approach:** This is not a from-scratch model-fitting experiment — `T4MlbArithEvaluator` reuses the already-frozen `p_hits_gte_threshold`/`_compute_ab_remaining` Binomial math from `run_t4_mlb_live.py` (ADR-0023, ADR-0004 governs the model class generally). The object under test is narrower: (1) whether `_ARITH_ENTRY_WINDOW=1` and `_ARITH_CONFIDENCE_GATE=0.80` are the right thresholds to define "near-certainty" for this market's actual resolved outcomes, and (2) whether `p_arith - (mip + vig)` in this band is systematically positive (edge) or centers on zero/negative (already efficiently priced) against resolved Kalshi KXMLBHIT prices. A grid sweep over entry-window width (0, 1, 2 hits) and confidence-gate threshold (0.70–0.95) against realized outcomes is the natural first pass, reusing the reconstructed cycle log rather than re-running any live system.

**Features used:**

| Feature ID | Feature Name | Source | Temporal Safety |
|-----------|-------------|--------|----------------|
| F-ARITH-01 | h_so_far, ab_so_far, inning, batting_slot | ESPN live MLB boxscore poll (T4M-PROJ's existing C1 layer) | VERIFIED (already governs live T4M-PROJ; same source, no new pipeline) |
| F-ARITH-02 | ba_l10 | C2 feature store (existing MLB rolling-stat pipeline) | VERIFIED (already governs live T4M-PROJ) |
| F-ARITH-03 | mip, vig at evaluation cycle | Live `live_prices: dict` populated from `pm.mid_price`/`pm.vig` in `run_t4_mlb_live.py`'s main loop — **not** `t4_price_cache.py` (that module is Phase-8-BLOCKED NBA-oriented infra, never imported by the MLB live loop; corrected per GG-067) | VERIFIED (already governs live T4M-PROJ) |

**Corrected per GG-067 (SESSION 110):** a new data source WAS required — `logs/t4_mlb_cycle_log.jsonl` did not exist prior to SESSION 110 (only the `dry_run=True` branch persisted per-cycle context via `_append_dryrun_record`; production runs, the only ones that have ever executed, left no reconstructable record). `run_t4_mlb_live.py::_run_cycle()` now writes this log unconditionally (additive, observation-only change; betting logic unaffected — see `tests/test_run_t4_mlb_live.py::TestProductionCycleLog`). This experiment cannot run until enough resolved games accumulate rows in that log post-deploy — it is a prospective data collection, not a purely retrospective slice-and-recompute over data already captured.

**Model class:** Binomial threshold-probability (frozen, ADR-0004/ADR-0023) — same as T4M-PROJ; this experiment does not introduce a new model class, only a new entry condition and threshold sweep over an existing one.  
**Hyperparameters:** `_ARITH_ENTRY_WINDOW` (candidate values: 0, 1, 2), `_ARITH_CONFIDENCE_GATE` (candidate values: 0.70, 0.75, 0.80, 0.85, 0.90, 0.95) — both currently hardcoded provisional constants in `t4_mlb_execution_engine.py`, explicitly marked non-calibrated pending this experiment.  
**Null model:** market_implied_prob baseline (mip + vig at the qualifying cycle) — the standard project-wide null, per the T1/EXP-017 precedent and GG-004's standing requirement that edge be measured against real market prices, not a 0.50 coin flip.

---

## Temporal Integrity Check

- [ ] All feature temporal_cutoff values precede event_date (each qualifying cycle's h_so_far/ab_so_far/price must reflect only information available at that cycle's timestamp, not later at-bats in the same game)
- [ ] No outcome data appears in the feature set (final game h_total must not leak into p_arith computation or entry-window filtering)
- [ ] Train/validation/test splits are strictly chronological with no overlap
- [ ] Snapshot IDs are registered and immutable

*(Unchecked — experiment has not run. These are the checks that must pass before this document can move to RUNNING.)*

---

## Results

*(Not yet run.)*

| Metric | Train | Validation | Null Model (Val) | Notes |
|--------|-------|-----------|-----------------|-------|
| Brier Score | | | | Lower is better |
| Log Loss | | | | Lower is better |
| ECE (Calibration) | | | | Lower is better |
| AUC-ROC | | | | Higher is better |

**Calibration curve:** (TBD)  
**Edge distribution:** (TBD — distribution of `p_arith - (mip + vig)` across all qualifying cycles is the primary object of interest; a distribution centered meaningfully above zero, with the majority of mass exceeding `_MIN_EDGE=0.04`, would support activation)

---

## Look-Ahead Audit

- [ ] Automated temporal overlap check passed
- [ ] Manual review of temporal_cutoff for all features confirmed
- [ ] Lineage register entries confirmed for all features used

*(Unchecked — pending experiment run.)*

---

## Interpretation

*(Not yet run — no interpretation exists.)*

**Does this experiment confirm or falsify the hypothesis?**

*(TBD)*

**Key findings:**
- *(TBD)*

**Unexpected results:**
- *(TBD)*

---

## Confidence

**Confidence in this result:** N/A — not yet run  
**Reason:** This document exists to define methodology ahead of execution, per T-219's follow-up scope. No result exists to have confidence in.

---

## Follow-Up

| Action | Owner | Due | Status |
|--------|-------|-----|--------|
| Fix GG-067: add production per-cycle raw-context logging to `run_t4_mlb_live.py`, independent of `dry_run` | EL | Before backtest runner could have real data | DONE (SESSION 110) |
| Build an offline backtest runner (`scripts/run_exp_arith_mlb_01.py`) against `logs/t4_mlb_cycle_log.jsonl`, filtered to qualifying `h_needed <= entry_window` cycles | EL | Before Phase 8 Activation Gate request | DONE (SESSION 110) |
| Register data snapshots per `DATA_SNAPSHOTS_INDEX.md` protocol once the backtest runner and its inputs are finalized | EL | Same as above | OPEN — pending enough post-deploy cycle-log rows |
| Run the entry-window/confidence-gate grid sweep and populate the Results table | EL | Same as above | OPEN — `scripts/run_exp_arith_mlb_01.py` reports INSUFFICIENT_DATA/INCONCLUSIVE until enough resolved MLB games accumulate in the cycle log post-SESSION-110 deploy |
| If edge is confirmed: draft Phase 8 Activation Gate request + APR for T4M-ARITH, per ADR-0039's Governance Impact section | EL | After this experiment completes | OPEN |
| If edge is not confirmed: leave T4M-ARITH `status="BLOCKED"` indefinitely; document the null result here and in `GOVERNANCE_GAP_LOG.md` | EL | After this experiment completes | OPEN |

---

## Links

- Governing ADR: `03_DECISIONS/ADR-0039_mlb-native-t4-subband-architecture-scoping.md`
- Registry entry: `execution_bands.py::T4_MLB_SUBBAND_REGISTRY[ExecutionBand.T4M_ARITH]`
- Evaluator under test: `src/prediction_market_bot/t4_mlb_execution_engine.py::T4MlbArithEvaluator`
- Test coverage (construction/logic, not backtest): `tests/test_t4_mlb_engine.py`
- Backtest runner: `scripts/run_exp_arith_mlb_01.py` (SESSION 110); tests: `tests/test_run_exp_arith_mlb_01.py`
- Data source fix: `GOVERNANCE_GAP_LOG.md` — GG-067 (SESSION 110)
- Task registration: `04_EXECUTION/TODO_NEXT.md` — T-219
- NBA precedent (structurally analogous, not a substitute — MLB has no prior EXP-ARITH-01 result to borrow from): `t4_execution_engine.py`'s T4-ARITH sub-band, itself still Phase-8-blocked as of this writing
