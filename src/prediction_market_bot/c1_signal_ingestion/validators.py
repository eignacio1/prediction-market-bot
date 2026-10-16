"""
C1/C2: Data Quality Contract Enforcement
==========================================
Component:    C1 (Signal Ingestion) / C2 (Feature Store boundary)
Phase:        1 of 4 (T-212, GG-059)
Status:       ACTIVE (SESSION 107 2026-07-01)
Upstream:     data_contracts.py (manifest), C1/C2 pipeline outputs (DataFrames)
Downstream:   C6 Audit Logger (IF-ALL-C6), pipeline entrypoints (PIPE-05,
              PIPE-06pre, scripts/generate_mlb_features.py)
ADR refs:     ADR-0034 (Layer 3 Semantic Contracts — structural sibling)
Policy refs:  03_DECISIONS/GOVERNANCE_GAP_LOG.md (GG-059)
              CLAUDE.md NFR-03 (kill-switch on C6 write failure)

This module enforces the manifests declared in data_contracts.py. It checks
STRUCTURE only — schema (columns present/absent, nullability, physical
value floors), cardinality (row count floor and drift vs. last known-good
count), and freshness (staleness of a designated date column). It does not
check semantic plausibility of values — that is SemanticFloorGuard's job
(c7_monitoring/semantic_contracts.py).

Two usage patterns, mirroring the ContaminationGuard / SemanticFloorGuard
split in semantic_contracts.py:

  1. Non-raising, fine-grained: validate_schema() / validate_cardinality() /
     validate_staleness() / validate() return ContractFailure records (or a
     ValidationResult bundling them). Callers inspect and decide.

  2. Raising, pipeline-halting entrypoint: assert_contract() runs validate(),
     emits every failure to C6, and raises DataContractViolation if any
     HALT-severity failure is present. This is the call pipeline entrypoints
     should use — mirrors SemanticFloorGuard.assert_floor()'s catch-and-halt
     contract exactly (raise → caller catches → sys.exit()).

Severity policy
-----------------
HALT (raises via assert_contract):
  - required column missing (schema drift at the source)
  - non-nullable column contains nulls (data corruption)
  - value below a physical minimum, e.g. negative hit count (data corruption)
  - row count below contract floor (empty/near-empty — mirrors GG-049)
  - freshness column has no valid dates, or staleness exceeds halt threshold

WARN (recorded, emitted to C6, does not halt):
  - unexpected extra column present (schema evolution, non-fatal)
  - dtype not cleanly compatible with contract (CSV round-tripping routinely
    promotes int→float or bool→int; a hard failure here would be noisy)
  - row count changed by more than max_row_growth_ratio vs. last known-good
    count, in either direction (duplication or partial-loss signal, not
    proof of one — GG-059's "3x jump" example)
  - freshness exceeds warn threshold but not halt threshold

Cardinality drift requires a "last known-good" baseline. That baseline is
persisted on disk (data/data_contracts_state.json, JSON-on-disk — same
pattern as c5_execution/paper_trader.py's state file) and is only advanced
after a clean (no-HALT) validation, so a corrupted run can never poison the
baseline used to detect the next corruption.

Integration points
--------------------
  scripts/generate_mlb_features.py — assert_contract() for
    MLB_BATTER_CONTRACT / MLB_PITCHER_CONTRACT immediately after C1 fetch,
    before combined.to_csv().

  run_mlb_paper_trade.py (PIPE-05), run_mlb_pregame.py (PIPE-06pre) —
    assert_contract() for MLB_FEATURE_CSV_CONTRACT immediately after the
    feature CSV is loaded, replacing the T-193 ad hoc freshness block.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from prediction_market_bot.c1_signal_ingestion.data_contracts import SourceContract
from prediction_market_bot.atomic_io import atomic_write_json
from prediction_market_bot.c6_audit_logger.audit_logger import AuditLogger

_DEFAULT_STATE_PATH = Path("data/data_contracts_state.json")

_SEVERITY_HALT = "HALT"
_SEVERITY_WARN = "WARN"


def _utc_now_iso() -> str:
    return datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


# ---------------------------------------------------------------------------
# Result types
# ---------------------------------------------------------------------------


@dataclass
class ContractFailure:
    """One structural check failure against a SourceContract."""

    source_id: str
    check_type: str
    severity: str  # "HALT" | "WARN"
    reason: str
    payload: dict[str, Any] = field(default_factory=dict)


@dataclass
class ValidationResult:
    """Bundled outcome of validate() for one source against one contract."""

    source_id: str
    row_count: int
    failures: list[ContractFailure]
    ts: str = field(default_factory=_utc_now_iso)

    @property
    def ok(self) -> bool:
        """True iff no HALT-severity failure is present (WARNs may exist)."""
        return not self.halts()

    def halts(self) -> list[ContractFailure]:
        return [f for f in self.failures if f.severity == _SEVERITY_HALT]

    def warnings(self) -> list[ContractFailure]:
        return [f for f in self.failures if f.severity == _SEVERITY_WARN]


class DataContractViolation(Exception):
    """
    A SourceContract was violated with at least one HALT-severity failure.

    Raised only by assert_contract(). Callers must catch this exception and
    halt the pipeline (mirrors SemanticFloorViolation's contract exactly).

    Attributes
    ----------
    source_id:  the SourceContract.source_id that was violated
    pipeline_id: e.g. "PIPE-05", "generate_mlb_features"
    failures:   the HALT-severity ContractFailure records that triggered this
    """

    def __init__(
        self,
        source_id: str,
        pipeline_id: str,
        failures: list[ContractFailure],
    ) -> None:
        self.source_id = source_id
        self.pipeline_id = pipeline_id
        self.failures = failures
        reasons = "; ".join(f"{f.check_type}: {f.reason}" for f in failures)
        super().__init__(
            f"DataContractViolation: {pipeline_id} source={source_id} — "
            f"{len(failures)} HALT-severity failure(s): {reasons}"
        )


# ---------------------------------------------------------------------------
# Structural checks (non-raising)
# ---------------------------------------------------------------------------


def _dtype_compatible(series: "pd.Series[Any]", expected: str) -> bool:
    kind = series.dtype.kind
    if expected == "int":
        return kind in ("i", "u", "f")
    if expected == "float":
        return kind in ("f", "i", "u")
    if expected == "bool":
        return kind in ("b", "i", "u")
    if expected == "str":
        return kind in ("O", "U", "S")
    return True


def validate_schema(df: pd.DataFrame, contract: SourceContract) -> list[ContractFailure]:
    """Check column presence, nullability, physical minimums, and dtype."""
    failures: list[ContractFailure] = []
    actual_columns = set(df.columns)
    expected_columns = set(contract.field_names())

    missing = expected_columns - actual_columns
    for col in sorted(missing):
        failures.append(ContractFailure(
            source_id=contract.source_id,
            check_type="schema_missing_column",
            severity=_SEVERITY_HALT,
            reason=f"required column '{col}' is absent from source",
            payload={"column": col},
        ))

    extra = actual_columns - expected_columns
    for col in sorted(extra):
        failures.append(ContractFailure(
            source_id=contract.source_id,
            check_type="schema_unexpected_column",
            severity=_SEVERITY_WARN,
            reason=f"unexpected column '{col}' present in source (not in contract)",
            payload={"column": col},
        ))

    for f in contract.fields:
        if f.name not in actual_columns:
            continue  # already flagged as missing above

        series = df[f.name]

        if not f.nullable:
            n_null = int(series.isna().sum())
            if n_null > 0:
                failures.append(ContractFailure(
                    source_id=contract.source_id,
                    check_type="schema_nullability",
                    severity=_SEVERITY_HALT,
                    reason=(
                        f"column '{f.name}' has {n_null} null value(s) "
                        f"but is marked non-nullable"
                    ),
                    payload={"column": f.name, "n_null": n_null, "n_rows": len(series)},
                ))

        if f.min_value is not None:
            numeric = pd.to_numeric(series, errors="coerce")
            below = numeric < f.min_value
            n_below = int(below.sum())
            if n_below > 0:
                failures.append(ContractFailure(
                    source_id=contract.source_id,
                    check_type="schema_min_value",
                    severity=_SEVERITY_HALT,
                    reason=(
                        f"column '{f.name}' has {n_below} value(s) "
                        f"below physical minimum {f.min_value}"
                    ),
                    payload={"column": f.name, "n_below": n_below, "min_value": f.min_value},
                ))

        if not _dtype_compatible(series, f.dtype):
            failures.append(ContractFailure(
                source_id=contract.source_id,
                check_type="schema_dtype",
                severity=_SEVERITY_WARN,
                reason=(
                    f"column '{f.name}' dtype '{series.dtype}' is not cleanly "
                    f"compatible with contract dtype '{f.dtype}'"
                ),
                payload={
                    "column": f.name,
                    "actual_dtype": str(series.dtype),
                    "expected_dtype": f.dtype,
                },
            ))

    return failures


def validate_cardinality(
    df: pd.DataFrame,
    contract: SourceContract,
    previous_row_count: int | None = None,
) -> list[ContractFailure]:
    """Check row count floor and drift vs. the last known-good count."""
    failures: list[ContractFailure] = []
    n = len(df)

    if n < contract.min_rows:
        failures.append(ContractFailure(
            source_id=contract.source_id,
            check_type="cardinality_floor",
            severity=_SEVERITY_HALT,
            reason=f"row count {n} is below contract minimum {contract.min_rows}",
            payload={"row_count": n, "min_rows": contract.min_rows},
        ))

    if previous_row_count is not None and previous_row_count > 0 and n > 0:
        ratio = n / previous_row_count
        bound = contract.max_row_growth_ratio
        if ratio > bound or ratio < (1.0 / bound):
            failures.append(ContractFailure(
                source_id=contract.source_id,
                check_type="cardinality_drift",
                severity=_SEVERITY_WARN,
                reason=(
                    f"row count {n} is a {ratio:.2f}x change from last known-good "
                    f"count {previous_row_count} (bound: {bound}x)"
                ),
                payload={
                    "row_count": n,
                    "previous_row_count": previous_row_count,
                    "ratio": ratio,
                    "max_row_growth_ratio": bound,
                },
            ))

    return failures


def validate_staleness(
    df: pd.DataFrame,
    contract: SourceContract,
    now: datetime | None = None,
) -> list[ContractFailure]:
    """Check the contract's designated freshness column against thresholds."""
    failures: list[ContractFailure] = []
    if contract.freshness_column is None:
        return failures
    if contract.freshness_column not in df.columns:
        return failures  # already flagged by validate_schema as missing

    now = now if now is not None else datetime.now(timezone.utc)
    dates = pd.to_datetime(df[contract.freshness_column], errors="coerce")
    max_date = dates.max()

    if pd.isna(max_date):
        failures.append(ContractFailure(
            source_id=contract.source_id,
            check_type="staleness_no_valid_dates",
            severity=_SEVERITY_HALT,
            reason=f"freshness column '{contract.freshness_column}' has no valid dates",
            payload={"freshness_column": contract.freshness_column},
        ))
        return failures

    age_days = (now.date() - max_date.date()).days

    if contract.freshness_halt_days is not None and age_days > contract.freshness_halt_days:
        failures.append(ContractFailure(
            source_id=contract.source_id,
            check_type="staleness_halt",
            severity=_SEVERITY_HALT,
            reason=f"source is {age_days} days stale (halt threshold {contract.freshness_halt_days})",
            payload={
                "age_days": age_days,
                "halt_threshold_days": contract.freshness_halt_days,
                "max_date": str(max_date.date()),
            },
        ))
    elif contract.freshness_warn_days is not None and age_days > contract.freshness_warn_days:
        failures.append(ContractFailure(
            source_id=contract.source_id,
            check_type="staleness_warn",
            severity=_SEVERITY_WARN,
            reason=f"source is {age_days} days stale (warn threshold {contract.freshness_warn_days})",
            payload={
                "age_days": age_days,
                "warn_threshold_days": contract.freshness_warn_days,
                "max_date": str(max_date.date()),
            },
        ))

    return failures


def validate(
    df: pd.DataFrame,
    contract: SourceContract,
    previous_row_count: int | None = None,
    now: datetime | None = None,
) -> ValidationResult:
    """Run all structural checks and bundle the result. Never raises."""
    failures: list[ContractFailure] = []
    failures.extend(validate_schema(df, contract))
    failures.extend(validate_cardinality(df, contract, previous_row_count))
    failures.extend(validate_staleness(df, contract, now))
    return ValidationResult(source_id=contract.source_id, row_count=len(df), failures=failures)


# ---------------------------------------------------------------------------
# Cardinality state persistence (JSON-on-disk, mirrors paper_trader.py)
# ---------------------------------------------------------------------------


logger = logging.getLogger(__name__)

_STATE_RESET_COUNT: dict[str, int] = {}


def _load_state(state_path: Path) -> dict[str, Any]:
    if not state_path.exists():
        return {}
    try:
        loaded: dict[str, Any] = json.loads(state_path.read_text())
        return loaded
    except (json.JSONDecodeError, OSError) as exc:
        # W77.3/GG-764: a reset here silently disables the previous-row-count
        # cardinality check for every source (previous_row_count -> None) and
        # the next _save_row_count overwrites the damaged file. Never silent.
        _STATE_RESET_COUNT[str(state_path)] = _STATE_RESET_COUNT.get(str(state_path), 0) + 1
        logger.error(
            "CARDINALITY STATE RESET: %s unreadable (%s: %s) — previous-row-count "
            "check disabled for this run (GG-764)",
            state_path, type(exc).__name__, exc,
        )
        return {}


def _load_previous_row_count(source_id: str, state_path: Path = _DEFAULT_STATE_PATH) -> int | None:
    state = _load_state(state_path)
    entry = state.get(source_id)
    if not entry:
        return None
    row_count = entry.get("row_count")
    return int(row_count) if row_count is not None else None


def _save_row_count(source_id: str, row_count: int, state_path: Path = _DEFAULT_STATE_PATH) -> None:
    state = _load_state(state_path)
    state[source_id] = {"row_count": row_count, "updated_at": _utc_now_iso()}
    state_path.parent.mkdir(parents=True, exist_ok=True)
    atomic_write_json(state_path, state, indent=2)


# ---------------------------------------------------------------------------
# C6 emission
# ---------------------------------------------------------------------------


def emit_validation_result(
    result: ValidationResult,
    audit: AuditLogger,
    pipeline_id: str,
    session_id: str | None = None,
    snapshot_id: str | None = None,
) -> bool:
    """
    Emit every failure (and a clean-pass marker if none) to C6.

    Returns False if any C6 write fails — NFR-03: callers combine this with
    the validation outcome so an unaudited pass is never trusted silently.
    """
    all_ok = True

    for failure in result.failures:
        ok = audit.log(
            pipeline_id,
            "data_contract_violation",
            payload={
                "source_id": failure.source_id,
                "check_type": failure.check_type,
                "severity": failure.severity,
                "reason": failure.reason,
                "row_count": result.row_count,
                **failure.payload,
            },
            severity="CRITICAL" if failure.severity == _SEVERITY_HALT else "WARNING",
            session_id=session_id,
            snapshot_id=snapshot_id,
        )
        if not ok:
            all_ok = False

    if not result.failures:
        ok = audit.log(
            pipeline_id,
            "data_contract_ok",
            payload={"source_id": result.source_id, "row_count": result.row_count},
            severity="DEBUG",
            session_id=session_id,
            snapshot_id=snapshot_id,
        )
        if not ok:
            all_ok = False

    return all_ok


# ---------------------------------------------------------------------------
# assert_contract — raising, pipeline-halting entrypoint
# ---------------------------------------------------------------------------


def assert_contract(
    df: pd.DataFrame,
    contract: SourceContract,
    audit: AuditLogger,
    pipeline_id: str,
    session_id: str | None = None,
    snapshot_id: str | None = None,
    state_path: Path = _DEFAULT_STATE_PATH,
    update_state: bool = True,
    now: datetime | None = None,
) -> ValidationResult:
    """
    Validate df against contract, emit every finding to C6, and raise on
    any HALT-severity failure.

    Usage (pipeline entrypoint, after data load, before downstream use)::

        try:
            assert_contract(df, MLB_FEATURE_CSV_CONTRACT, audit=logger,
                             pipeline_id="PIPE-05", session_id=SESSION_ID,
                             snapshot_id=SNAPSHOT_ID)
        except DataContractViolation as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            sys.exit(1)

    The cardinality drift baseline (data/data_contracts_state.json) is only
    advanced after a clean (no-HALT) pass — a corrupted run never poisons
    the baseline used to detect the next corruption.

    Raises
    ------
    DataContractViolation
        If any HALT-severity structural failure is found, OR if the C6
        write for this validation result itself fails (NFR-03 — an
        unaudited pass cannot be trusted).
    """
    previous_row_count = _load_previous_row_count(contract.source_id, state_path)
    result = validate(df, contract, previous_row_count=previous_row_count, now=now)

    logged_ok = emit_validation_result(result, audit, pipeline_id, session_id, snapshot_id)

    failures = list(result.halts())
    if not logged_ok:
        failures.append(ContractFailure(
            source_id=contract.source_id,
            check_type="audit_write_failure",
            severity=_SEVERITY_HALT,
            reason="C6 audit write failed while emitting data contract validation result (NFR-03)",
        ))

    if failures:
        raise DataContractViolation(
            source_id=contract.source_id,
            pipeline_id=pipeline_id,
            failures=failures,
        )

    if update_state:
        _save_row_count(contract.source_id, result.row_count, state_path)

    return result
