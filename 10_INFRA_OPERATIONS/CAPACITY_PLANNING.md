# Capacity Planning — Prediction Market Trading Bot

> **STATUS BANNER (2026-10-20, W80.4): NOT VERIFIED against the running system.** Written May 2026; May-2026 estimates, not re-measured; box specs and loads are not recorded here. Where this file disagrees with those sources, they win. Registered LIVING in `00_ADMIN/DOC_REGISTRY.toml` with no verification date.

**Purpose:** Document system resource requirements, scaling constraints, and capacity limits for each phase of operation.  
**Owner (role):** Infrastructure Operator (IO)  
**Status:** STUB — Phase 5 minimum; expand before G6 live capital deployment  
**Last reviewed:** 2026-05-28 (T-055 Phase 5 stub created)  
**Next review:** G5 (before paper trading); G6 (before live capital); update when component load profile changes  
**Staleness triggers:** New component added; throughput model changes; data volume scales; venue API rate limits confirmed  
**Upstream links:** ARCHITECTURE_OVERVIEW.md, SLA_SLO_SLI.md, OBSERVABILITY.md  
**Downstream links:** ENVIRONMENTS.md, RUNBOOKS/  
**Decision references:** ADR-0001, ADR-0003  
**Confidence:** 4/10 — Stub only; actual load profile measured in Phase 5/6

---

## Phase 5 Capacity Baseline (Research / Paper)

### Compute

| Resource | Current demand | Notes |
|----------|---------------|-------|
| CPU | Minimal — single-process batch | No concurrency required in research phase |
| Memory | ~500 MB peak | pandas DataFrames for 50 players × 3 seasons |
| Disk (audit log) | ~10 MB/day research mode | JSON Lines; grows linearly with event volume |
| Disk (snapshots) | ~50 MB per snapshot | Raw game log CSVs; 1–2 snapshots per experiment |

### Network

| Dependency | Rate | Notes |
|-----------|------|-------|
| nba_api (DS-01 proxy) | ~100 requests/session | stats.nba.com unofficial API; rate-limit: ~1 req/s |
| Kalshi API (DS-02) | Not active — G5+ | Rate limits TBD at ACC-0002 approval |

### Venue API Rate Limits (DS-02 — Phase 6+)

To be confirmed at ADR-0003 venue integration phase. Known constraints (from public docs):
- Kalshi: TBD — document when ACC-0002 credentials obtained
- Reserve 50% of rate limit budget for monitoring / status checks

---

## Phase 6+ Paper Trading Capacity (Stub)

Requirements TBD when C5 Execution Engine is activated. At minimum:
- Persistent audit log storage (2-year retention per DATA_RETENTION_DELETION.md CAT-04)
- Kill switch response verified ≤60s on target hardware (NFR-03)
- C7 SystemMonitor running continuously (process management TBD)

---

## Phase 8+ Live Capital Capacity (Stub)

Requirements TBD at G6 gate. Minimum requirements before live:
- Remote log backup (OBSERVABILITY.md Phase 8 plan)
- 5-year log retention for execution records (DATA_RETENTION_DELETION.md CAT-05)
- Hardware kill switch test on live hardware (not just dev environment)
- All SLOs met on paper hardware before promoting to live (SLA_SLO_SLI.md)

---

## Kill Switch Hardware Requirement (NFR-03)

The kill switch must halt all components within ≤60 seconds on the target deployment hardware. This must be tested before G5 on the actual machine that will run Phase 6+ paper trading. A pass on dev hardware does not satisfy NFR-03 if the production hardware is different.

**Action:** Record target hardware spec in this document before G5 gate sign-off.

| Field | Value |
|-------|-------|
| Target hardware | TBD (Earl's dev machine / TBD cloud) |
| Kill switch drill result | TBD (pending T-051) |
| Halt time measured | TBD |
| NFR-03 pass | TBD |
