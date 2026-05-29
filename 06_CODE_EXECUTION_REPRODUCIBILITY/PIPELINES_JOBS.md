# Pipelines and Jobs — Prediction Market Trading Bot

**Purpose:** Enumerate all automated pipelines and jobs, their trigger conditions, owners, and failure modes. Every automated process must be documented here.  
**Owner (role):** Execution Lead (EL)  
**Last reviewed:** 2026-05-22  
**Next review:** G2 Architecture Gate; update when any pipeline is created or modified  
**Staleness triggers:** New pipeline created; pipeline schedule changed; component architecture change  
**Upstream links:** ARCHITECTURE_OVERVIEW.md, INTERFACES_CONTRACTS.md, RUN_INSTRUCTIONS.md  
**Downstream links:** 10_INFRA_OPERATIONS/RUNBOOKS/  
**Decision references:** ADR-0001, ADR-0002  
**Confidence:** 3/10 — Pipeline designs are preliminary; instantiated at Phase 3 build

---

## Pipeline Inventory

### PIPE-01 — Research Backtest Pipeline (Phase 3+)

| Attribute | Detail |
|-----------|--------|
| Purpose | Run full C1→C2→C3 pipeline on historical snapshots; produce forecast records with calibration metrics |
| Trigger | Manual (operator-initiated per experiment) |
| Steps | (1) Ingest snapshot (C1) → (2) Derive features (C2) → (3) Train model → (4) Evaluate backtest (C3) → (5) Log to C6 |
| Inputs | Pinned Snapshot IDs from DATA_SNAPSHOTS_INDEX.md; pinned dependency lock file |
| Outputs | Forecast records; Brier score vs null model; calibration curve; C6 audit log entries |
| Pre-checks | Snapshot integrity; dependency version match; no live credentials in environment |
| Failure handling | On any step failure: log error to C6; halt pipeline; do NOT write partial results |
| Reproducibility | 100% reproducible given same Snapshot IDs + dependency lock + code commit hash |
| Gate required | Phase 3 entry |

### PIPE-02 — Live Inference Pipeline (Phase 6, ENV-02 VPS)

| Attribute | Detail |
|-----------|--------|
| Purpose | Pre-game edge calculations from live Kalshi prices; no orders; paper trading decision feed |
| Trigger | **Cron: 21:30 UTC + 01:30 UTC daily** (VPS cron.conf) |
| Runner | `src/prediction_market_bot/run_pregame.py` |
| Steps | (1) Load serialized model (models/prod_model.joblib) → (2) Load static L10 features (EXP-005 matrix) → (3) Apply qualitative enrichment (QS-002) → (4) Fetch live Kalshi KXNBAPTS markets → (5) Compute edges per player → (6) Log to C6 → (7) Write `logs/pregame_YYYYMMDD.json` |
| Inputs | `models/prod_model.joblib`; `exp_output/EXP-005/EXP-005_feature_matrix.csv`; `VENUE_API_KEY` (DS-02 read-only) |
| Outputs | Forecast records in C6 audit log; `logs/pregame_YYYYMMDD.json` edge report |
| Pre-checks | healthcheck.sh (21:00 UTC): model present, VENUE_API_KEY set, DS-02 reachable, BOT_C4_ACTIVE absent |
| Graceful exit | If no active KXNBAPTS markets (off-season, pre-market): exit 0, empty JSON report |
| Failure handling | DS-02 connectivity failure → exit 1, log error; C6 write failure → exit 1 |
| Gate required | G5 ✅ (Phase 6 active); VPS provisioned (T-059) |

### PIPE-03 — Paper Trading Pipeline (Phase 6+)

| Attribute | Detail |
|-----------|--------|
| Purpose | Full simulated decision cycle from live data to simulated orders |
| Trigger | Scheduled or event-driven (TBD at ADR-0004) |
| Steps | PIPE-02 steps → (5) Risk evaluation (C5 sim) → (6) Simulated order (C4 sim) → (7) Update paper portfolio |
| Inputs | Live DS-02; paper portfolio state |
| Outputs | Simulated order records; paper P&L; C6 audit log |
| Pre-checks | C7 active; kill switch active; paper portfolio initialized; no live order credentials |
| Failure handling | On risk check failure: REJECTED (log reason). On kill switch: halt. On any pipeline failure: halt + alert. |
| Gate required | ADR-0004 accepted |

### PIPE-04 — Live Capital Pipeline (Phase 8+)

| Attribute | Detail |
|-----------|--------|
| Purpose | Full live decision cycle from data to real order submission |
| Trigger | Scheduled or event-driven |
| Steps | PIPE-02 steps → (5) Risk evaluation (C5 live) → (6) Live order via venue API (C4 live) → (7) Confirm fill |
| Inputs | Live DS-02; live portfolio state; venue API credentials (vault) |
| Outputs | Real orders; real fills; live P&L; C6 audit log |
| Pre-checks | G5 kill switch drill passed; G6 gate cleared; ADR-0005 accepted; APR-0009 signed; all limits enforced |
| Failure handling | On any step failure: halt pipeline; kill switch auto-triggers on limit breach; all events logged to C6 |
| Gate required | ADR-0005 + G6 Release Gate + ACC-0002 + APR-0009 |

---

## Scheduled Jobs

| Job | Pipeline | Schedule | Phase | Status |
|-----|----------|----------|-------|--------|
| Snapshot integrity check | PIPE-01 | Before each experiment | Phase 3+ | 🔴 Pending |
| Dependency version verification | All | Before each run | Phase 3+ | 🔴 Pending |
| Brier score monitoring | PIPE-03/04 | After each event resolves | Phase 6+ | 🔴 Pending |
| Audit log integrity check | All | Daily | Phase 5+ | 🔴 Pending |
| Kill switch heartbeat | PIPE-02/03/04 | Continuous | Phase 5+ | 🔴 Pending |

---

## Pipeline Failure Escalation

| Failure Type | Severity | Auto-Response | Manual Response |
|-------------|----------|---------------|----------------|
| Step failure in PIPE-01 | WARN | Log + halt | Review C6 log; fix + re-run |
| Live data feed interruption (PIPE-02/03) | HIGH | Log + halt pipeline | Alert; check DS-02 availability |
| Risk limit breach (PIPE-03/04) | CRITICAL | Kill switch trigger | Review C6; resolve before restart |
| Fill confirmation failure (PIPE-04) | CRITICAL | Halt; do NOT retry without confirmation | Manual venue reconciliation |
| Kill switch failure (PIPE-03/04) | CRITICAL | N/A (kill switch failed) | Manual halt of all processes; P1 incident |
