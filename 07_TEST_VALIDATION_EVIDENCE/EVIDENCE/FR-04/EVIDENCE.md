# FR-04 Evidence — Decision Recording (append-only audit log)

> **Record as of 2026-07-06** — a frozen, dated record, not a living document. It is not kept in step with the system; see `00_ADMIN/DOC_REGISTRY.toml`.


**Requirement:** (a) Decision log entry created for every forecast; (b) Log is append-only (no modification after write); (c) All required fields present; (d) Log survives process restart.

**Populated:** 2026-07-06 (GG-075 remediation).

## Test evidence

- `tests/test_c6_audit_logger.py` — field presence, append-only guarantee, restart persistence.
- `edge_logger` (extended for T1/T4M parity, T-213) — confirmed via `grep -rn "edge_logger" src/`.
- Live artifact: `logs/audit_mlb_t4.jsonl` on the VPS is a running, multi-week append-only JSONL log actively consumed by the session-start operational health check (CLAUDE.md Step 4) — its own continued growth across restarts is itself a restart-survival demonstration, distinct from the unit test.

## Status

**OPERATIONALLY DEMONSTRATED** — C6 audit logger active continuously since Phase 3, exercised on every T1/T2/T3/T4M-PROJ decision across 5+ weeks of MLB paper trading plus the NBA T1/T4 history. Tests above pass as of the 2026-07-06 full-suite run.
