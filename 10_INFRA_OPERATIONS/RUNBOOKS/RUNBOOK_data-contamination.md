# Runbook: Data Contamination / Look-Ahead Bias (FM-02, C1/C2) — CRITICAL

**Purpose:** Diagnose and respond to look-ahead bias / training-data contamination — future data leaking into features used to train or validate the model. Rated CRITICAL in `RESILIENCE_FAILURE_MODES.md`: "silently destroys validity of all downstream validation."
**Owner (role):** Model Owner (MO)
**Last reviewed:** 2026-07-12
**Next review:** Before any C3 model retrain; before any new feature is added to `c2_feature_store/mlb_features.py`
**Staleness triggers:** New feature added to the feature store; rolling-window computation changed; any backtesting framework change
**Upstream links:** `02_ARCHITECTURE_DESIGN/RESILIENCE_FAILURE_MODES.md` (FM-02), `03_DECISIONS/GOVERNANCE_GAP_LOG.md` (GG-092)
**Downstream links:** `10_INFRA_OPERATIONS/INCIDENTS_POSTMORTEMS/`
**Decision references:** ADR-0024 (commercial validation gate — a contamination finding would invalidate its inputs)
**Confidence:** 5/10 — the mitigation this runbook can actually offer is narrower than the failure mode it's named for; read the "What This Runbook Cannot Do" section before relying on it operationally

---

## Read this first: there is no production runtime detector for FM-02

**This is the single most important fact in this document.** FM-02 as defined in `RESILIENCE_FAILURE_MODES.md` is about *future data leaking into training features* — i.e., a corruption of the historical dataset used to fit and validate the model. Verified directly against source (2026-07-12):

- The only automated checks that exist are **offline pytest unit tests**, run manually/in CI, not at pipeline execution time:
  - `tests/test_t182_mlb_c2.py::test_temporal_cutoff_is_prior_game_date`
  - `tests/test_t182_mlb_c2.py::test_first_game_temporal_cutoff_is_nat`
  - `tests/test_t182_mlb_c2.py::test_nat_temporal_cutoff_excluded_from_all_splits`
  - `tests/test_c2_features.py::test_series_delta_temporal_integrity`
  - `tests/test_clean_dataset.py::test_contamination_column_labeled_not_dropped`
- These tests confirm the `.shift(1)` mechanism (below) behaves correctly **on the fixtures the tests ship with**. They do not run against live production data, do not run on a schedule, and produce no alert if they were to fail in CI — there is no "automated overlap check in backtesting framework" wired into any live pipeline, despite that phrase appearing as a stated Mitigation in `RESILIENCE_FAILURE_MODES.md` FM-02.
- **There is no runtime check anywhere in `run_mlb_pregame.py`, `run_mlb_paper_trade.py`, or the C3 training scripts that would catch a live contamination event as it happens.** If a future change to `mlb_features.py` broke the `.shift(1)` logic, the earliest this would surface is the next time someone runs the offline test suite by hand — not automatically, not in production.

**This gap is real, not a documentation staleness issue, and this runbook cannot close it — only a code change (wiring an equivalent check into the live pipeline, or a CI gate that blocks merge on test failure) can.** Treat this runbook as diagnostic and containment guidance for *if* contamination is suspected, not as evidence a detector will catch it for you.

---

## Do not confuse this with CONTAMINATION_HALT / ContaminationGuard

The T4 MLB live pipeline (`run_t4_mlb_live.py`) and `c7_monitoring/semantic_contracts.py`'s `ContaminationGuard` both use the word "contamination" and emit a `CONTAMINATION_HALT` audit event — **this is a different mechanism solving a different problem and is not evidence FM-02 is covered:**

| | FM-02 (this runbook) | `ContaminationGuard` / `CONTAMINATION_HALT` |
|---|---|---|
| What it protects | Historical training/backtest data integrity | A single live T4 evaluation cycle |
| Failure it catches | Future outcome data leaking into a feature computed for a past game | Stale/incoherent live state (closed market, player left game, game ended) feeding a *current* bet decision |
| When it runs | Never, automatically, in production (see above) | Every T4 evaluation cycle, in-process, O(1), no I/O |
| Code location | N/A — does not exist at runtime | `c7_monitoring/semantic_contracts.py:496` `ContaminationGuard.is_clean()` |
| Also watch for | — | `LiveDataFreshnessGuard`'s `game_state_fresh` check (`run_t4_mlb_live.py:718`) — same "contamination" vocabulary, third distinct mechanism: checks the live game-state poll isn't older than 2× the poll interval |

If you see `CONTAMINATION_HALT` in `logs/audit_mlb_t4.jsonl`, that is a **T4 live-staleness event**, not an FM-02 training-data contamination event. Do not close an FM-02 concern on the basis of `CONTAMINATION_HALT` activity, and do not use this runbook to diagnose a `CONTAMINATION_HALT` — see the T4 monitoring documentation and CLAUDE.md Step 4's `game_state_fresh` recency-window check instead.

---

## The mechanism that does exist: `.shift(1)` temporal cutoff

`c2_feature_store/mlb_features.py` and `c2_feature_store/features.py` compute every rolling statistic with `.shift(1)` applied **before** `.rolling()`, so that a row for game N's features are derived only from games 1..N-1, never game N itself:

```python
# mlb_features.py:187
df["temporal_cutoff"] = pd.to_datetime(df["game_date"]).shift(1)
# mlb_features.py:190-191
h_sum = df["h"].shift(1).rolling(window, min_periods=min_periods).sum()
ab_sum = df["ab"].shift(1).rolling(window, min_periods=min_periods).sum()
```

`temporal_cutoff` is carried as a column through the feature CSV (excluded from the model's actual feature set — see `_NON_FEATURE_MLB` frozensets in `run_mlb_paper_trade.py` / `run_mlb_pregame.py` / every `run_exp*.py`) and used at training time to filter to only rows with a valid, non-null cutoff (`train_test_label` filtering, `backtester.py:393`). A first-game row (no prior game to shift from) gets `temporal_cutoff=NaT` and is excluded from all splits.

This is a real, tested mechanism — but it is a *design pattern honored by convention in `mlb_features.py`*, not an enforced runtime contract. Nothing prevents a future feature added elsewhere in the codebase from being computed without `.shift(1)` and silently leaking same-game outcome data.

---

## Trigger Conditions

There is no automated trigger — by definition, since no runtime detector exists. This runbook is invoked when:

1. A human (model owner, reviewer) notices a backtest result that looks implausibly good (a classic contamination symptom).
2. A code review on a new feature raises the question of whether it respects the `.shift(1)` convention.
3. The offline pytest suite is run manually and a `test_temporal*` or `test_*contamination*` test fails.
4. Before any C3 model retrain — as a mandatory pre-check, not a reactive one.

---

## Diagnostics

```bash
# Run the offline temporal-integrity test suite manually — this is the ONLY
# automated check that exists; it is not run automatically on any cadence.
pytest tests/test_t182_mlb_c2.py -k temporal -v
pytest tests/test_c2_features.py -k temporal -v
pytest tests/test_clean_dataset.py -k contamination -v

# Spot-check a feature CSV directly: temporal_cutoff should always be strictly
# before game_date for every non-first-game row.
python3 -c "
import pandas as pd
df = pd.read_csv('<path-to-feature-csv>')
df['game_date'] = pd.to_datetime(df['game_date'])
df['temporal_cutoff'] = pd.to_datetime(df['temporal_cutoff'])
bad = df[df['temporal_cutoff'].notna() & (df['temporal_cutoff'] >= df['game_date'])]
print(f'{len(bad)} rows with temporal_cutoff >= game_date (should be 0)')
"

# Check any new/recently-changed feature computation for .shift(1) usage
git log --oneline -- src/prediction_market_bot/c2_feature_store/mlb_features.py | head -10
git diff <last-known-good-commit> HEAD -- src/prediction_market_bot/c2_feature_store/mlb_features.py
```

| What to check | Where | What to look for |
|---|---|---|
| Rolling stat computation order | `c2_feature_store/mlb_features.py`, `features.py` | `.shift(1)` appears BEFORE `.rolling()` for every stat column, not after |
| `temporal_cutoff` validity | Any feature CSV | Never ≥ `game_date` for non-null rows |
| New feature additions | `git diff` on `mlb_features.py` / `features.py` | Does the new feature use current-game data anywhere in its computation? |
| Backtest plausibility | EXP-0xx result summaries | Implausibly high win rate / Brier score vs. prior runs is a contamination symptom, not just "good luck" |

---

## Mitigations

### Mitigation A: Suspected contamination in a specific feature

1. Isolate the feature's computation in `mlb_features.py` / `features.py`.
2. Manually trace whether it uses `.shift(1)` correctly, or whether it derives from a column that itself was contaminated upstream.
3. Re-run the offline test suite (Diagnostics above) — if it doesn't already cover the suspect feature, **write a new test for it** before declaring it clean; absence of an existing test is not evidence of correctness.
4. If contamination is confirmed: any backtest or EXP-0xx result that used the affected feature is invalid and must be flagged in `DECISION_LOG.md` immediately (Hard Rule 7) — do not let a stale EXP result stand uncorrected.

### Mitigation B: Pre-retrain check (mandatory, manual — there is no automated gate)

```bash
pytest tests/test_t182_mlb_c2.py tests/test_c2_features.py tests/test_clean_dataset.py -v
```

All must pass before any C3 retrain proceeds. This is not currently enforced by CI or any pre-retrain script — it is a manual discipline step. **If retraining without running this manually, you are retraining without the only contamination check this system has.**

### Mitigation C: Close the actual gap (code-level fix, not a runbook action)

The durable fix is wiring an equivalent temporal-integrity check into either (a) a CI gate that blocks merge/deploy on test failure, or (b) `run_mlb_pregame.py`'s runtime path, similar to how `assert_contract` (T-212/GG-059) already runs schema/cardinality/staleness checks at runtime. This is out of scope for this runbook to perform, but should be tracked — recommend registering as a new governance gap if not already covered by an open GG/T-number (check `GOVERNANCE_GAP_LOG.md` before creating a duplicate).

---

## Rollback

If a contaminated feature is confirmed to have shipped into a live model:

1. Identify the last known-good feature-store commit (before the contaminating change).
2. Do not retrain on the contaminated dataset. Regenerate the feature CSV from the known-good code path.
3. Any bets placed under a model trained (even partially) on contaminated data should be flagged in `DECISION_LOG.md` and considered for exclusion from `clean_n` per the `logic_epoch.py` mechanism (CLAUDE.md's "commercial validation gap" section) — this may require a new epoch boundary, which is a DS-level decision, not one this runbook authorizes unilaterally.

**Verification:** offline test suite (Mitigation B command) passes; spot-check diagnostic script (above) reports 0 bad rows on a freshly regenerated feature CSV.

---

## Known Failure Modes

| Failure | Likelihood | Response |
|---|---|---|
| No production runtime detector exists (see top of this doc) | CERTAIN — this is documented current state, not a risk | No response available within this runbook's scope; requires a code-level fix (Mitigation C) |
| New feature added without `.shift(1)` convention, no test written | MEDIUM — nothing currently blocks this in code review or CI | Manual code review discipline; write a test before merge |
| Offline test suite exists but is never actually run before retrains | MEDIUM-HIGH — no evidence of an enforced cadence | Mitigation B must become a checklist item until a CI gate exists |
| A future refactor of `features.py`/`mlb_features.py` accidentally changes shift ordering | LOW-MEDIUM | Offline tests would catch this IF run — see above caveat |

---

## References

- `02_ARCHITECTURE_DESIGN/RESILIENCE_FAILURE_MODES.md` — FM-02
- `03_DECISIONS/GOVERNANCE_GAP_LOG.md` — GG-092 (this runbook)
- `src/prediction_market_bot/c2_feature_store/mlb_features.py` — lines 16-18 (design doc comment), 160-191 (`.shift(1)` implementation, `temporal_cutoff` computation)
- `src/prediction_market_bot/c2_feature_store/features.py` — lines 221-360 (NBA-side equivalent pattern)
- `src/prediction_market_bot/c7_monitoring/semantic_contracts.py` — `ContaminationGuard` (line 496) — DIFFERENT mechanism, see "Do not confuse" section above
- `src/prediction_market_bot/run_t4_mlb_live.py` — `LiveDataFreshnessGuard` / `game_state_fresh` (line ~718) — DIFFERENT mechanism, see "Do not confuse" section above
- `tests/test_t182_mlb_c2.py`, `tests/test_c2_features.py`, `tests/test_clean_dataset.py` — the only existing (offline, manual) checks
