# Acceptance Criteria — Prediction Market Trading Bot

**Purpose:** Map each requirement to its acceptance criteria, test method, and evidence location. This is the contractual definition of "done."  
**Owner (role):** Evidence Owner (EO) / Product Owner (PO)  
**Status:** **FROZEN — G1 Spec Gate 2026-05-22** — Changes require REQUIREMENTS.md to be unfrozen; follows same change control as REQUIREMENTS.md  
**Last reviewed:** 2026-05-22 (FROZEN at G1)  
**Next review:** On staleness trigger only; unfreezes with REQUIREMENTS.md  
**Staleness triggers:** Requirement added/changed; test method revised; evidence location moved; metric threshold finalized at G4 (threshold values populated, not criteria unfrozen)  
**Upstream links:** REQUIREMENTS.md  
**Downstream links:** 07_TEST_VALIDATION_EVIDENCE/TEST_STRATEGY.md, 07_TEST_VALIDATION_EVIDENCE/TEST_CASES/  
**Decision references:** ADR-0001, ADR-0002  
**Confidence:** 9/10 — FROZEN at G1; specific metric thresholds (Brier score target, Kelly fraction) are marked PENDING and will be populated in-place at G4 without unfreezing  

---

## Functional Requirements

| Req ID | Acceptance Criteria | Test Method | Evidence Location | Status |
|--------|--------------------|-----------|--------------------|--------|
| FR-01 | (a) Ingestion runs without error on a valid input snapshot; (b) Output schema matches DATA_REQUIREMENTS.md contract; (c) Snapshot ID assigned and written to DATA_SNAPSHOTS_INDEX.md; (d) Invalid input rejected with structured error log | Unit test (schema validation); integration test (end-to-end ingestion run) | 07_TEST_VALIDATION_EVIDENCE/EVIDENCE/FR-01/ | PENDING |
| FR-02 | (a) Forecast output includes: event_id, timestamp, p_estimate, confidence_interval, snapshot_id, model_version; (b) p_estimate ∈ [0,1]; (c) Every output traceable to a Snapshot ID | Unit test (output schema); integration test (pipeline run) | 07_TEST_VALIDATION_EVIDENCE/EVIDENCE/FR-02/ | PENDING |
| FR-03 | (a) Brier score computed correctly against held-out outcomes (verified on synthetic ground truth); (b) Log loss computed correctly; (c) Both metrics compared to null model (market-implied probability); (d) Results written to timestamped file with Snapshot ID | Unit test (metric math on synthetic data); backtesting integration test | 07_TEST_VALIDATION_EVIDENCE/BENCHMARKS/ | PENDING |
| FR-04 | (a) Decision log entry created for every forecast; (b) Log is append-only (no modification after write); (c) All required fields present; (d) Log survives process restart | Unit test (field presence); integration test (restart persistence); audit test (immutability check) | 07_TEST_VALIDATION_EVIDENCE/EVIDENCE/FR-04/ | PENDING |
| FR-05 | (a) Manual kill-switch trigger halts all processes within ≤60 seconds (timed); (b) Auto-trigger fires on daily loss limit breach (simulated in test); (c) Log entry created on every kill-switch activation; (d) System does not resume without explicit operator restart | Timed kill-switch drill (at G5); unit test (auto-trigger logic); integration test (full halt) | 07_TEST_VALIDATION_EVIDENCE/EVIDENCE/FR-05/ | PENDING |
| FR-06 | (a) Backtest runs to completion on a pinned snapshot; (b) Results match when re-run on same snapshot (reproducibility); (c) Train/test windows confirmed non-overlapping; (d) No future data accessible in training window (look-ahead check) | Integration test (reproducibility run); unit test (window overlap check); automated look-ahead audit | 07_TEST_VALIDATION_EVIDENCE/EVIDENCE/FR-06/ | PENDING |
| FR-07 | (a) Paper trading mode records hypothetical orders with all fields (event, direction, size, price, timestamp); (b) No real orders submitted (API call log shows zero submissions); (c) Simulated PnL calculated correctly on resolution | Integration test (mock venue API); paper trading run with verification | 07_TEST_VALIDATION_EVIDENCE/EVIDENCE/FR-07/ | PENDING (Phase 6) |
| FR-08 | (a) Real order placed and confirmed on venue (sandbox/test environment first); (b) All orders logged per FR-04; (c) Order fails and logs error if risk check (FR-09) fails | End-to-end test on venue sandbox; risk check bypass test | 07_TEST_VALIDATION_EVIDENCE/EVIDENCE/FR-08/ | PENDING (Phase 8) |
| FR-09 | (a) Order rejected when position would exceed max single-event limit; (b) Kill switch triggered automatically when daily loss limit breached (simulated); (c) Risk check runs before every order attempt; (d) Override path requires ADR evidence | Unit test (each limit type); integration test (auto-trigger); audit test (no bypass path) | 07_TEST_VALIDATION_EVIDENCE/EVIDENCE/FR-09/ | PENDING |

---

## Non-Functional Requirements

| NFR ID | Acceptance Criteria | Test Method | Evidence Location | Status |
|--------|--------------------|-----------|--------------------|--------|
| NFR-01 | Re-run of any prior experiment using archived (pinned) artifacts produces results within ±0.001 of original (numerical tolerance for float math) | Reproducibility regression test | 07_TEST_VALIDATION_EVIDENCE/EVIDENCE/NFR-01/ | PENDING |
| NFR-02 | Log audit: sample 10 forecast events; confirm all required fields present in every entry | Log schema audit | 07_TEST_VALIDATION_EVIDENCE/EVIDENCE/NFR-02/ | PENDING |
| NFR-03 | Kill-switch drill completed and time recorded ≤60s; all process IDs confirmed halted | Timed drill at G5 | 07_TEST_VALIDATION_EVIDENCE/EVIDENCE/FR-05/ | PENDING |
| NFR-04 | Automated scan: zero date overlap between train/test snapshots; look-ahead audit passes | Automated overlap check + manual spot audit | 07_TEST_VALIDATION_EVIDENCE/EVIDENCE/NFR-04/ | PENDING |
| NFR-05 | Secrets scan returns zero findings; no credentials in logs | Automated scan (pre-commit hook + gate review) | 07_TEST_VALIDATION_EVIDENCE/EVIDENCE/NFR-05/ | PENDING |
| NFR-06 | Sample 50 log lines from research pipeline run; confirm structured format; confirm metric emission endpoint reachable | Log format audit; metric endpoint probe | 07_TEST_VALIDATION_EVIDENCE/EVIDENCE/NFR-06/ | PENDING |
| NFR-07 | Full research pipeline runs end-to-end with all external calls mocked; zero live API dependencies in dev mode | Dev-mode integration test | 07_TEST_VALIDATION_EVIDENCE/EVIDENCE/NFR-07/ | PENDING |
| NFR-08 | DIR check: zero major changes in last 4 weeks without ADR reference | Weekly DIR artifact | 07_TEST_VALIDATION_EVIDENCE/EVIDENCE/NFR-08/ | ONGOING |
