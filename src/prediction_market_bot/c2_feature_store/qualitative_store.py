"""
C2 Sub-module: Qualitative Signal Store
========================================
Component:    C2 (Feature Store) — qualitative enrichment sub-module
Phase active: Phase 6+ (first qualitative experiment — pending DS-01 operationalization)
Status:       SKELETON — structure defined; activation pending QS snapshot population
Upstream:     Qualitative classification CSVs (qualitative_data/<source>/<QS-ID>_classifications.csv)
Downstream:   C2 FeatureStore.compute_features_bulk() (enrichment step)
Interfaces:   IF-DS-Q-C2 (see INTERFACES_CONTRACTS.md)

Governance:
  See 08_MODEL_RISK_GOVERNANCE/QUALITATIVE_SIGNALS.md for the full framework.
  See 05_RESEARCH_EXPERIMENTS/DATA_SOURCES/QUALITATIVE_REGISTRY.md for all
  registered sources and their operationalization status.

Temporal integrity (QTI-01):
  Qualitative features are joined to the feature DataFrame by player_id AND
  game_date. The join enforces:
      game_date >= classification.effective_from
      AND game_date < classification.effective_until (or NULL = currently active)
  Rows with no matching classification for a game_date produce NaN for all
  qualitative features. NaN is the correct output — it means "not classified
  for this period." C3 handles NaN imputation.

Feature ID range:
  DS-01 PAM:          F-100–F-149 (PRF archetype), F-150–F-181 (modifiers)
  DS-04 (reserved):   F-200–F-249
  DS-05 (reserved):   F-250–F-299
  Composite/derived:  F-300–F-399

Kill switch constraint (NFR-03):
  All public methods return (bool, DataFrame).
  False on any C6 write failure. Callers must trigger kill switch.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from prediction_market_bot.c6_audit_logger.audit_logger import AuditLogger

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

COMPONENT = "C2-QS"

# DS-01 PAM feature columns — names that appear in the merged DataFrame
# Populated when DS-01 operationalization is complete
_DS01_PRF_FEATURES: list[str] = [
    "prf_primary",         # F-100: primary archetype (integer 1–15)
    "prf_secondary",       # F-101: secondary archetype (integer 0–15; 0=none)
    "prf_hybrid_weight",   # F-102: primary weight in hybrid notation (float 0–1; NaN if pure)
]

_DS01_MODIFIER_FEATURES: list[str] = [
    f"mod_{i:02d}" for i in range(1, 33)   # F-150–F-181: binary flags
]

DS01_FEATURE_NAMES: list[str] = _DS01_PRF_FEATURES + _DS01_MODIFIER_FEATURES

# Required columns in any qualitative classification CSV
_REQUIRED_COLUMNS = {
    "player_id",
    "effective_from",
    "prf_primary",
}

# Temporal guard columns
_EFFECTIVE_FROM_COL = "effective_from"
_EFFECTIVE_UNTIL_COL = "effective_until"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _utc_now_iso() -> str:
    return datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


def _qs_run_id() -> str:
    return f"QS-RUN-{uuid.uuid4().hex[:10].upper()}"


# ---------------------------------------------------------------------------
# QualitativeSignalStore
# ---------------------------------------------------------------------------


class QualitativeSignalStore:
    """
    C2 sub-module: loads qualitative classification snapshots and enriches
    a feature DataFrame with qualitative features (F-100+).

    Usage (once DS-01 is operationalized)::

        qs = QualitativeSignalStore(
            logger=audit_logger,
            snapshot_id="SNAP-2026-05-28-002",   # game-log snapshot anchor
        )

        ok = qs.load_ds01_snapshot(
            csv_path=Path("qualitative_data/pam_v4/QS-2026-05-28-001_classifications.csv"),
            qs_id="QS-2026-05-28-001",
        )
        if not ok:
            trigger_kill_switch()

        ok, enriched_df = qs.enrich_features(
            feature_df=feature_df,
            session_id=session_id,
        )
        if not ok:
            trigger_kill_switch()

    The returned DataFrame has all original columns plus F-100+ qualitative
    features appended. Rows with no matching classification for their game_date
    (because game_date < effective_from) will have NaN for all F-100+ columns.
    This is intentional and correct — C3 imputes NaN at training/inference time.

    Status: SKELETON — load_ds01_snapshot() and enrich_features() are stubbed.
    Implement when the first QS snapshot CSV is populated and registered.
    """

    def __init__(
        self,
        logger: AuditLogger,
        snapshot_id: str,
    ) -> None:
        """
        Parameters
        ----------
        logger:
            Shared AuditLogger (C6) instance.
        snapshot_id:
            Game-log snapshot ID (flows through audit trail for traceability).
        """
        self._logger = logger
        self._snapshot_id = snapshot_id
        self._ds01_df: pd.DataFrame | None = None
        self._ds01_qs_id: str | None = None
        self._loaded_sources: list[str] = []

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _log(
        self,
        event_type: str,
        payload: dict[str, Any],
        severity: str = "INFO",
        session_id: str | None = None,
        run_id: str | None = None,
    ) -> bool:
        return self._logger.log(
            component=COMPONENT,
            event_type=event_type,
            payload=payload,
            severity=severity,
            session_id=session_id,
            snapshot_id=self._snapshot_id,
            feature_run_id=run_id,
        )

    # ------------------------------------------------------------------
    # DS-01 PAM loader
    # ------------------------------------------------------------------

    def load_ds01_snapshot(
        self,
        csv_path: Path,
        qs_id: str,
        session_id: str | None = None,
    ) -> bool:
        """
        Load a DS-01 PAM classification CSV into memory.

        Parameters
        ----------
        csv_path:
            Path to the populated QS snapshot CSV. Must conform to
            qualitative_data/pam_v4/SCHEMA.md.
        qs_id:
            QS snapshot ID (e.g., "QS-2026-05-28-001"). Must be registered
            in QUALITATIVE_REGISTRY.md before calling this method.
        session_id:
            Current run session ID.

        Returns
        -------
        bool — False on C6 write failure or schema validation error.

        Status: STUB — implement when QS snapshot is populated.
        """
        run_id = _qs_run_id()

        ok = self._log(
            "qs_load_start",
            {"qs_id": qs_id, "csv_path": str(csv_path), "source": "DS-01"},
            session_id=session_id,
            run_id=run_id,
        )
        if not ok:
            return False

        # --- STUB: implement below when QS snapshot is populated ---
        # Steps to implement:
        #   1. Read CSV: df = pd.read_csv(csv_path)
        #   2. Validate required columns (_REQUIRED_COLUMNS) are present
        #   3. Validate prf_primary in range 1–15; mod_XX in {0, 1}
        #   4. Parse effective_from / effective_until as dates
        #   5. Assign to self._ds01_df
        #   6. Set self._ds01_qs_id = qs_id
        #   7. Log success with row count, player count, effective date range
        # --- END STUB ---

        ok = self._log(
            "qs_load_stub",
            {
                "qs_id": qs_id,
                "note": (
                    "QualitativeSignalStore.load_ds01_snapshot() is not yet implemented. "
                    "Populate qualitative_data/pam_v4/PAM_CLASSIFICATION_TEMPLATE.csv "
                    "and register a QS snapshot before activating this code path."
                ),
            },
            severity="WARNING",
            session_id=session_id,
            run_id=run_id,
        )
        return ok

    # ------------------------------------------------------------------
    # Feature enrichment
    # ------------------------------------------------------------------

    def enrich_features(
        self,
        feature_df: pd.DataFrame,
        session_id: str | None = None,
    ) -> tuple[bool, pd.DataFrame]:
        """
        Left-join qualitative features onto a feature DataFrame.

        Join key: player_id
        Temporal guard (QTI-01): only join rows where
            game_date >= classification.effective_from
            AND game_date < classification.effective_until (or NULL)

        All qualitative feature columns (F-100+) are appended. Rows with
        no matching classification return NaN for those columns.

        Parameters
        ----------
        feature_df:
            Output of FeatureStore.compute_features_bulk(). Must contain
            player_id and game_date columns.
        session_id:
            Current run session ID.

        Returns
        -------
        (ok, enriched_df):
            ok — False if C6 write failed.
            enriched_df — feature_df with qualitative columns appended.
                          On stub/no-op: returns feature_df unchanged with
                          NaN qualitative columns added.

        Status: STUB — temporal join not yet implemented.
        """
        run_id = _qs_run_id()

        ok = self._log(
            "qs_enrich_start",
            {
                "input_rows": len(feature_df),
                "ds01_loaded": self._ds01_df is not None,
                "ds01_qs_id": self._ds01_qs_id,
            },
            session_id=session_id,
            run_id=run_id,
        )
        if not ok:
            return False, feature_df

        # --- STUB: implement temporal join below when QS snapshot is loaded ---
        # Steps to implement:
        #   1. If self._ds01_df is None: append NaN columns and return (warn logged)
        #   2. Parse feature_df["game_date"] as datetime
        #   3. Expand self._ds01_df to per-game rows via effective_from/until guard:
        #        join_df = self._ds01_df[
        #            (feature_df["game_date"] >= row["effective_from"])
        #            & ((row["effective_until"].isna()) | (feature_df["game_date"] < row["effective_until"]))
        #        ]
        #   4. Left-merge feature_df with join_df on player_id
        #   5. Select only DS01_FEATURE_NAMES from the merged result
        #   6. Append to feature_df; rows with no match → NaN
        #   7. Log enrichment stats: rows_enriched, rows_missing_classification
        # --- END STUB ---

        # Stub: append NaN qualitative columns so the DataFrame schema is stable
        for col in DS01_FEATURE_NAMES:
            if col not in feature_df.columns:
                feature_df = feature_df.copy()
                feature_df[col] = float("nan")

        ok = self._log(
            "qs_enrich_stub",
            {
                "output_rows": len(feature_df),
                "qualitative_cols_appended": DS01_FEATURE_NAMES,
                "note": (
                    "QualitativeSignalStore.enrich_features() is running in stub mode. "
                    "All qualitative features are NaN. Implement temporal join when "
                    "DS-01 QS snapshot is loaded."
                ),
            },
            severity="WARNING",
            session_id=session_id,
            run_id=run_id,
        )
        return ok, feature_df

    # ------------------------------------------------------------------
    # Feature name registry
    # ------------------------------------------------------------------

    def get_qualitative_feature_names(self) -> list[str]:
        """
        Return the list of qualitative feature column names for all loaded sources.
        Used by ModelForecaster to register qualitative features alongside
        quantitative features (get_feature_names() in FeatureStore).

        Call this AFTER loading all desired QS snapshots.
        Until DS-01 is loaded: returns DS01_FEATURE_NAMES (all will be NaN).
        """
        names: list[str] = []
        if self._ds01_df is not None or True:  # include when stub is active too
            names.extend(DS01_FEATURE_NAMES)
        return names

    # ------------------------------------------------------------------
    # Status
    # ------------------------------------------------------------------

    @property
    def is_ready(self) -> bool:
        """True if at least one QS snapshot is loaded and the store can enrich."""
        return self._ds01_df is not None

    @property
    def loaded_sources(self) -> list[str]:
        """List of QS-IDs currently loaded."""
        return list(self._loaded_sources)
