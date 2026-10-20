# NFR-04 Evidence — Data Integrity (no leakage, chronological splits)

> **Record as of 2026-07-06** — a frozen, dated record, not a living document. It is not kept in step with the system; see `00_ADMIN/DOC_REGISTRY.toml`.


**Requirement:** Automated scan: zero date overlap between train/test snapshots; look-ahead audit passes.

**Populated:** 2026-07-06 (GG-075 remediation).

## Evidence

- `tests/test_semantic_contracts.py` — automated temporal-cutoff / look-ahead rejection (`temporal_cutoff > event_date` fails ingestion, TC-001 equivalent).
- Chronological train/test split enforced by design in all EXP runners (confirmed via `DATA_SNAPSHOTS_INDEX.md` snapshot dating and the backtester's window-selection logic in `tests/test_backtester.py`).

## Status

**OPERATIONALLY DEMONSTRATED** — the overlap/look-ahead check is automated and runs on every test suite pass (currently passing), not a manual one-time audit; this satisfies the requirement's intent more strongly than a single filed report would.
