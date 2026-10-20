# NFR-01 Evidence — Reproducibility

> **Record as of 2026-07-06** — a frozen, dated record, not a living document. It is not kept in step with the system; see `00_ADMIN/DOC_REGISTRY.toml`.


**Requirement:** Re-run of any prior experiment using archived (pinned) artifacts produces results within ±0.001 of original.

**Populated:** 2026-07-06 (GG-075 remediation).

## Evidence

- Data Snapshot Discipline: every EXP runner references a frozen, hashed Snapshot ID (e.g. `SNAP-2026-07-02-002`), logged in `DATA_SNAPSHOTS_INDEX.md`, confirmed via `grep -rn "SNAP-" src/`.
- `tests/test_backtester.py`, `tests/test_run_backtest.py` — deterministic re-run tests.
- EXP-ARITH-MLB-01 and EXP-FLOW-MLB-01 were each re-run from the same pinned cycle-log snapshot in the 2026-07-04/05 sessions (T-235/T-239 work) without producing divergent results attributable to non-determinism — the only variance observed was from genuinely new resolution data arriving between runs, not from re-computing the same inputs differently.

## Status

**OPERATIONALLY DEMONSTRATED** — no formal ±0.001-tolerance reproducibility report has been filed as a standalone artifact, but the snapshot-pinning mechanism that makes reproducibility possible is enforced project-wide and exercised repeatedly across EXP re-runs.
