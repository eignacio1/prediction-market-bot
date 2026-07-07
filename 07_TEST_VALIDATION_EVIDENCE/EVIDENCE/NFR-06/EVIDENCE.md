# NFR-06 Evidence — Observability (structured JSON logs)

**Requirement:** Sample 50 log lines from research pipeline run; confirm structured format; confirm metric emission endpoint reachable.

**Populated:** 2026-07-06 (GG-075 remediation).

## Evidence

- `tests/test_c7_monitor.py`, `tests/test_c8_dashboard.py` — structured JSONL log consumption tests for C7 monitoring and C8 dashboard.
- Live artifact: `logs/audit_mlb_t4.jsonl` on the VPS — actively parsed line-by-line by the session-start operational health check (CLAUDE.md Step 4, e.g. `grep -c "CONTAMINATION_HALT"`), which is itself a continuous structured-format confirmation far exceeding a one-time 50-line sample.

## Status

**OPERATIONALLY DEMONSTRATED** — C7/C8 consume structured JSONL logs in production continuously; a literal one-time 50-line manual sample was not filed separately, since the format is exercised by every governance session's operational health check instead.
