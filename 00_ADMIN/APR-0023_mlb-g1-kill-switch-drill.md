# APR-0023 — MLB Kill Switch Drill (MLB-G1 Gate, TC-007)

**Status:** COMPLETE — drill passed SLA  
**Gate:** MLB-G1  
**TC Reference:** TC-007  
**NFR Reference:** NFR-03 (kill switch ≤60,000ms)  
**Executed:** 2026-06-27  
**Session:** S90  
**Task:** T-197  
**Script:** `scripts/run_mlb_kill_switch_drill.py`  
**Operator:** Earl Ignacio  

---

## Drill Parameters

| Parameter | Value |
|---|---|
| Sport | MLB |
| Pipeline | PIPE-05 (MLB T1 paper trading) |
| Session ID | SES-MLB-DRILL-20260627-001 |
| Snapshot ID | SNAP-MLB-DRILL-T197 |
| Audit log | `logs/audit_mlb.jsonl` |
| Drill log | `logs/drill_audit.jsonl` |

---

## Result

| Metric | Value | Pass? |
|---|---|---|
| `kill_switch_id` | KS-02162B06AE53 | — |
| `halt_time_ms` | 0.116 ms | ✓ |
| `passed_sla` | True | ✓ |
| SLA threshold | 60,000 ms | — |

**PASS** — kill switch halted in 0.116ms, 99.9998% under NFR-03 SLA.

---

## Comparison to NBA Drill (APR baseline)

| Metric | NBA (2026-05-28) | MLB (2026-06-27) |
|---|---|---|
| halt_time_ms | 0.340 ms | 0.116 ms |
| passed_sla | True | True |
| Kill switch ID | KS-C8D7D90AF942 | KS-02162B06AE53 |

Both drills confirm the in-process `threading.Event` halt mechanism is sport-agnostic and well within NFR-03. The MLB drill uses the same `SystemMonitor.run_kill_switch_drill()` code path — no sport-specific kill switch logic exists at Phase 6.

---

## Scope Note

This drill tests the **in-process kill switch** (C7 `threading.Event` mechanism). It does not test:
- VPS cron halt (kill switch disables new cron invocations; existing runs complete)
- Band-level kill switch (T4 band budget exhaustion — T4 MLB not yet built)
- File-lock conflicts under concurrent cron runs

All three are out of scope at MLB-G1. Cron-level halt testing is deferred to MLB-G3 (T4 activation gate). The band-level kill switch will be tested when T4 MLB is built.

---

## C6 Audit Events

Three events written to `logs/audit_mlb.jsonl`:
1. `kill_switch_triggered` (CRITICAL) — drill invocation
2. `kill_switch_drill_result` (INFO) — halt_time_ms and passed_sla
3. `kill_switch_reset` (WARNING) — system reset to operational after drill

APR record written to `logs/drill_audit.jsonl` (machine-readable, mirrors NBA drill record format).
