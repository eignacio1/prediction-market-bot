# Run Instructions — Prediction Market Trading Bot

> **STATUS BANNER (2026-10-20, W80.4): NOT VERIFIED against the running system.** Written May 2026; commands (`run_exp001`, `run_backtest`, c8 dashboard) predate the current runtime; see `RUNTIME_MAP.md`, `deploy/DEPLOYMENT_GUIDE.md`, `scripts/`. Where this file disagrees with those sources, they win. Registered LIVING in `00_ADMIN/DOC_REGISTRY.toml` with no verification date.

**Purpose:** Step-by-step instructions to reproduce any experiment or pipeline run from a clean environment. If someone cannot reproduce a run from these instructions alone, the instructions are incomplete.  
**Owner (role):** Execution Lead (EL)  
**Status:** **CANONICAL — G3 Execution Gate 2026-05-22** — Changes require version bump and CHANGELOG entry  
**Last reviewed:** 2026-05-28 (T-049/T-050 Phase 5 — C7 kill switch drill command + C8 dashboard command added)  
**Next review:** On staleness trigger only  
**Staleness triggers:** Dependency version change; pipeline step change; environment change; new component added  
**Upstream links:** ENVIRONMENTS.md, DEPENDENCY_LOCKS/, ARCHITECTURE_OVERVIEW.md  
**Downstream links:** PIPELINES_JOBS.md, DATA_SNAPSHOTS_INDEX.md  
**Decision references:** ADR-0001, ADR-0002  
**Confidence:** 8/10 — Environment setup and Phase 3 pipeline commands confirmed; Phase 6+ live commands TBD

---

## Prerequisites

- [ ] **Python 3.11** installed (confirmed at G2; `python3.11 --version` must return 3.11.x)
- [ ] Virtual environment created and activated (`python3.11 -m venv .venv && source .venv/bin/activate`)
- [ ] Dependencies installed from pinned lock file: `pip install -r 06_CODE_EXECUTION_REPRODUCIBILITY/DEPENDENCY_LOCKS/requirements-dev.txt`
- [ ] Pre-commit hooks installed: `pre-commit install`
- [ ] Data snapshots registered in DATA_SNAPSHOTS_INDEX.md for the run being reproduced
- [ ] Environment variables set per SECRETS_HANDLING.md (BOT_ENV, LOG_DIR, SNAPSHOT_DIR at minimum)
- [ ] No live API credentials present in research environment (enforced by NFR-07)

---

## Step 0 — Verify Environment

```bash
# Verify Python version (must be 3.11.x)
python3.11 --version

# Verify virtual environment is active
which python | grep .venv

# Verify dependencies are installed and consistent
pip check

# Verify pre-commit hooks are installed
pre-commit run --all-files --show-diff-on-failure

# Verify BOT_ENV is set to 'research' for ENV-01
echo $BOT_ENV  # must output: research

# Verify no live credentials in environment (manual check until G5 tool)
# Inspect .env and shell environment — VENUE_API_KEY must NOT be set in ENV-01
```

---

## Step 1 — Install Dependencies

```bash
# Create virtual environment with pinned Python version
python3.11 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install from pinned dev lock file (research environment)
pip install -r 06_CODE_EXECUTION_REPRODUCIBILITY/DEPENDENCY_LOCKS/requirements-dev.txt

# After install, generate locked snapshot for this run
pip freeze > 06_CODE_EXECUTION_REPRODUCIBILITY/DEPENDENCY_LOCKS/requirements-locked.txt

# Verify installed packages are consistent (no conflicts)
pip check
```

**Never use `requirements.txt` with unpinned ranges in experiments. Always install from the DEPENDENCY_LOCKS/ file current at the time of the experiment, and record the lock file date in the experiment record.**

---

## Step 2 — Run Tests

Before any experiment, confirm the full test suite passes:

```bash
# From project root with .venv active
PYTHONPATH=src python -m pytest tests/ -q
```

Expected: all tests pass (194+ as of FEATURE_VERSION 1.1.0). A test failure before an experiment run is a hard stop — file a RID.

---

## Step 3 — Run EXP-001 (C1 → C2 → C3 → C4 Full Pipeline)

EXP-001 runs C1 ingestion (nba_api), C2 feature derivation (FEATURE_VERSION 1.1.0), C3 forecasting, and C4 risk gate.

```bash
# From project root with .venv active and package installed (pip install -e .)
python -m prediction_market_bot.run_exp001 --output-dir exp_output
```

**Optional flags:**
```bash
# Skip C1 API pull; provide existing raw CSV (avoids network dependency):
python -m prediction_market_bot.run_exp001 \
    --no-api \
    --output-dir exp_output

# Validate pipeline without writing to disk:
python -m prediction_market_bot.run_exp001 \
    --output-dir exp_output \
    --dry-run
```

**Expected output** (`exp_output/EXP-001/`):
- `SNAP-2026-05-27-001_raw_game_logs.csv` — raw C1 output (Snapshot ID registered in DATA_SNAPSHOTS_INDEX.md)
- `EXP-001_features.csv` — C2 feature matrix (FEATURE_VERSION 1.1.0; 38 columns)
- `EXP-001_forecasts.csv` — C3 forecast records (IF-C3-C4 schema)
- `EXP-001_metrics.json` — Brier score, ECE, AUC-ROC vs null model
- `EXP-001_audit.jsonl` — C6 audit log for this run

**C4 note:** C4 RiskEngine will REJECT all positions (phase gate closed). This is expected — `BOT_C4_ACTIVE` must NOT be set in ENV-01/ENV-02.

---

## Step 4 — Run EXP-002 / EXP-003 (Walk-Forward Backtest)

Run after EXP-001 completes. Reuses EXP-001's raw game log CSV to avoid a second API pull.

```bash
# Recommended: reuse EXP-001 raw CSV (no fresh API pull)
python -m prediction_market_bot.run_backtest \
    --raw-csv exp_output/EXP-001/SNAP-2026-05-27-001_raw_game_logs.csv \
    --output-dir exp_output/BACKTEST
```

**Optional flags:**
```bash
# Fresh C1 pull (registers SNAP-2026-05-27-002):
python -m prediction_market_bot.run_backtest \
    --output-dir exp_output/BACKTEST

# Run a single window only:
python -m prediction_market_bot.run_backtest \
    --raw-csv exp_output/EXP-001/SNAP-2026-05-27-001_raw_game_logs.csv \
    --window exp002

# Dry run (no disk writes):
python -m prediction_market_bot.run_backtest \
    --raw-csv exp_output/EXP-001/SNAP-2026-05-27-001_raw_game_logs.csv \
    --dry-run
```

**Expected output** (`exp_output/BACKTEST/`):
- `EXP-002_results.json` — HYP-001 window 2 (2021-22 second half)
- `EXP-003_results.json` — HYP-001 window 3 + HYP-004 (2021-22 early-mid; signal stability)
- Audit logs per window

---

## Step 5 — Verify Audit Log

```bash
# Check audit log for a completed run (inspect key events):
grep -c '"event_type"' exp_output/EXP-001/EXP-001_audit.jsonl   # count log entries
grep '"severity": "ERROR"' exp_output/EXP-001/EXP-001_audit.jsonl   # check for errors
grep '"severity": "CRITICAL"' exp_output/EXP-001/EXP-001_audit.jsonl   # check for kill-switch events
```

An audit log with CRITICAL entries requires investigation before interpreting experiment results. File a RID if unexpected CRITICAL events appear.

---

## Step 6 — Record Results

After each experiment:

1. Open the experiment record in `05_RESEARCH_EXPERIMENTS/EXPERIMENT_LOG/EXP-NNN_*.md`
2. Populate the Results section with metrics from `EXP-NNN_metrics.json`
3. Update `05_RESEARCH_EXPERIMENTS/RESULTS_SUMMARIES/RESULTS_INDEX.md` — change status from RUNNING → COMPLETE
4. Evaluate relevant hypotheses in `05_RESEARCH_EXPERIMENTS/HYPOTHESES.md`
5. Update `MEMORY_BANK.md` and `TODO_NEXT.md`

---

## Step 7 — Kill Switch Drill (T-051 / TC-007 — Required Before G5)

Run the pre-G5 kill switch drill using the `run_kill_switch_drill()` method in C7. This confirms NFR-03 (≤60s halt) in your environment before any live capital is deployed.

```python
# From a Python REPL or scratch script (project root with .venv active):
from prediction_market_bot.c6_audit_logger.audit_logger import AuditLogger
from prediction_market_bot.c7_monitoring.monitor import SystemMonitor

logger = AuditLogger.from_env()
monitor = SystemMonitor(
    logger=logger,
    snapshot_id="SNAP-DRILL-001",
    session_id="SES-DRILL-001",
)

result = monitor.run_kill_switch_drill(operator="Earl Ignacio")
print(f"Kill switch drill: passed={result.passed_sla}, halt_time_ms={result.halt_time_ms:.2f}")
print(f"Kill switch ID: {result.kill_switch_id}")
# Expected: passed=True, halt_time_ms well below 60000
```

**Pass criteria (TC-007, NFR-03):**
- `result.passed_sla is True`
- `result.halt_time_ms <= 60000`
- `kill_switch_triggered` + `kill_switch_drill_result` + `kill_switch_reset` entries in audit log
- Kill switch clears after drill (system operational)

After passing: record halt_time_ms and drill timestamp in `07_TEST_VALIDATION_EVIDENCE/VALIDATION_SIGNOFF.md` (TC-007 row). Get DS sign-off. This clears the G5 kill switch blocker.

---

## Step 8 — C8 Visual Dashboard

View the current system health and alert feed from the C6 audit log:

```bash
# From project root with .venv active
python -m prediction_market_bot.c8_dashboard.dashboard \
    --log-path logs/audit.jsonl \
    --n-alerts 20
```

The dashboard reads the audit log and renders three panels:
1. System Health — kill switch state + component last-seen timestamps
2. Drift Metrics — rolling Brier/ECE/mean edge vs. G4 baselines
3. Alert Feed — last 20 WARN/ERROR/CRITICAL audit events

---

## Reproducibility Checklist

Before running any experiment, confirm:

- [ ] Snapshot IDs registered in DATA_SNAPSHOTS_INDEX.md
- [ ] Dependency lock file matches DEPENDENCY_LOCKS/requirements-dev.txt (generate lock post-install: `pip freeze > DEPENDENCY_LOCKS/requirements-locked.txt`)
- [ ] `BOT_C4_ACTIVE` is NOT set in environment (Phase gate — must remain closed in ENV-01/ENV-02)
- [ ] No outcome data accessible in the feature store
- [ ] Train/validation/test splits are chronological (no random shuffle) — enforced by C2 `train_test_label` column
- [ ] Audit logger (C6) active and writing to designated log file
- [ ] No live API credentials in the research environment
- [ ] Full test suite passing before run: `PYTHONPATH=src python -m pytest tests/ -q`

---

## Reproducing a Specific Experiment

To reproduce experiment EXP-NNN from a clean state:

1. Check out the code commit cited in the experiment record
2. Create fresh venv: `python3.11 -m venv .venv && source .venv/bin/activate`
3. Install from pinned lock: `pip install -r 06_CODE_EXECUTION_REPRODUCIBILITY/DEPENDENCY_LOCKS/requirements-dev.txt`
4. Confirm the Snapshot IDs exist in DATA_SNAPSHOTS_INDEX.md
5. Run tests: `PYTHONPATH=src python -m pytest tests/ -q`
6. Run the experiment using the command in the experiment record (`EXP-001`: Step 3 above; `EXP-002/003`: Step 4 above)
7. Compare results to the recorded metrics in `05_RESEARCH_EXPERIMENTS/EXPERIMENT_LOG/EXP-NNN_*.md`

If results differ, open a RID in RID_LOG.md citing the differing metrics and the environment details.
