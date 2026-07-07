# FR-06 Evidence — Backtesting Framework (pinned snapshots, look-ahead detection)

**Requirement:** (a) Backtest runs to completion on a pinned snapshot; (b) Reproducible on re-run; (c) Train/test windows non-overlapping; (d) No future data accessible in training window (look-ahead check).

**Populated:** 2026-07-06 (GG-075 remediation).

## Test evidence

- `tests/test_backtester.py`, `tests/test_run_backtest.py` — backtest completion + reproducibility.
- `tests/test_semantic_contracts.py` — temporal cutoff / look-ahead enforcement (`temporal_cutoff > event_date` rejection, TC-001 equivalent).
- Experiment runners exercised against pinned snapshots (grep-confirmed `SNAP-` references): `run_exp001.py` through the EXP-019C series, `run_exp_arith_mlb_01.py`, `run_exp_flow_mlb_01.py` — all logged in `DATA_SNAPSHOTS_INDEX.md`.

## Status

**OPERATIONALLY DEMONSTRATED** — the backtest runners listed above have run to completion against pinned, hashed snapshots repeatedly (most recently EXP-ARITH-MLB-01 / EXP-FLOW-MLB-01, 2026-07-05/06). Look-ahead and window-overlap checks are enforced by `test_semantic_contracts.py`, passing as of the 2026-07-06 full-suite run.
