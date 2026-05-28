"""
C2 Sub-module: Qualitative Signal Store
========================================
Component:    C2 (Feature Store) — qualitative enrichment sub-module
Phase active: Phase 6+
Status:       IMPLEMENTED — 2026-05-28
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
            QS snapshot ID registered in QUALITATIVE_REGISTRY.md.
        session_id:
            Current run session ID.

        Returns
        -------
        bool — False on C6 write failure or schema validation error.
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

        try:
            df = pd.read_csv(csv_path, dtype={"player_id": int})

            # Validate required columns
            missing_cols = _REQUIRED_COLUMNS - set(df.columns)
            if missing_cols:
                ok = self._log(
                    "qs_load_error",
                    {"qs_id": qs_id, "missing_columns": sorted(missing_cols)},
                    severity="ERROR",
                    session_id=session_id,
                    run_id=run_id,
                )
                return False

            # Validate PRF range
            bad_prf = df[~df["prf_primary"].between(1, 15)]
            if not bad_prf.empty:
                ok = self._log(
                    "qs_load_error",
                    {
                        "qs_id": qs_id,
                        "error": f"{len(bad_prf)} rows have prf_primary outside 1–15",
                        "bad_player_ids": bad_prf["player_id"].tolist(),
                    },
                    severity="ERROR",
                    session_id=session_id,
                    run_id=run_id,
                )
                return False

            # Parse temporal columns
            df["effective_from"] = pd.to_datetime(df["effective_from"], errors="coerce")
            df["effective_until"] = pd.to_datetime(df["effective_until"], errors="coerce")

            if df["effective_from"].isna().any():
                ok = self._log(
                    "qs_load_error",
                    {"qs_id": qs_id, "error": "effective_from has null values — required on all rows"},
                    severity="ERROR",
                    session_id=session_id,
                    run_id=run_id,
                )
                return False

            # Coerce modifier columns to numeric
            mod_cols = [c for c in df.columns if c.startswith("mod_")]
            for col in mod_cols:
                df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(float)

            # Coerce PRF columns to numeric
            df["prf_primary"] = pd.to_numeric(df["prf_primary"], errors="coerce")
            df["prf_secondary"] = pd.to_numeric(df.get("prf_secondary", 0), errors="coerce").fillna(0)
            df["prf_hybrid_weight"] = pd.to_numeric(df.get("prf_hybrid_weight", float("nan")), errors="coerce")

            self._ds01_df = df
            self._ds01_qs_id = qs_id
            self._loaded_sources.append(qs_id)

            eff_from_min = df["effective_from"].min().strftime("%Y-%m-%d")
            eff_from_max = df["effective_from"].max().strftime("%Y-%m-%d")
            ok = self._log(
                "qs_load_complete",
                {
                    "qs_id": qs_id,
                    "player_count": len(df),
                    "effective_from_range": f"{eff_from_min} – {eff_from_max}",
                    "has_effective_until": int(df["effective_until"].notna().sum()),
                    "feature_columns": DS01_FEATURE_NAMES,
                },
                session_id=session_id,
                run_id=run_id,
            )
            return ok

        except Exception as exc:
            ok = self._log(
                "qs_load_error",
                {"qs_id": qs_id, "error": repr(exc)},
                severity="ERROR",
                session_id=session_id,
                run_id=run_id,
            )
            return False

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

        if self._ds01_df is None:
            # No snapshot loaded — append all-NaN columns and warn
            result = feature_df.copy()
            for col in DS01_FEATURE_NAMES:
                if col not in result.columns:
                    result[col] = float("nan")
            ok = self._log(
                "qs_enrich_no_snapshot",
                {
                    "output_rows": len(result),
                    "note": "No QS snapshot loaded; all qualitative features are NaN.",
                },
                severity="WARNING",
                session_id=session_id,
                run_id=run_id,
            )
            return ok, result

        try:
            # Columns to pull from QS snapshot (feature columns + temporal guard columns)
            qs_cols = ["player_id", "effective_from", "effective_until"] + DS01_FEATURE_NAMES
            qs_df = self._ds01_df[[c for c in qs_cols if c in self._ds01_df.columns]].copy()

            # Left-join on player_id — one QS row per player, so this is a 1:many join
            # (one classification row joins to many game rows for the same player)
            merged = feature_df.reset_index(drop=True).merge(
                qs_df,
                on="player_id",
                how="left",
                suffixes=("", "_qs"),
            )

            # Apply temporal guard (QTI-01):
            # Nullify qualitative columns for rows outside the effective window
            game_dates = pd.to_datetime(merged["game_date"], errors="coerce")
            eff_from = merged["effective_from"]
            eff_until = merged["effective_until"]

            before_window = game_dates < eff_from
            after_window = eff_until.notna() & (game_dates >= eff_until)
            outside_window = before_window | after_window

            for col in DS01_FEATURE_NAMES:
                if col in merged.columns:
                    merged.loc[outside_window, col] = float("nan")

            # Drop the temporal guard columns — they're metadata, not features
            result = merged.drop(
                columns=["effective_from", "effective_until"],
                errors="ignore",
            )

            n_enriched = int((~outside_window).sum())
            n_outside = int(outside_window.sum())
            n_no_player = int(result["prf_primary"].isna().sum()) - n_outside

            ok = self._log(
                "qs_enrich_complete",
                {
                    "qs_id": self._ds01_qs_id,
                    "input_rows": len(feature_df),
                    "output_rows": len(result),
                    "rows_within_window": n_enriched,
                    "rows_outside_window": n_outside,
                    "rows_no_player_match": max(0, n_no_player),
                    "qualitative_feature_count": len(DS01_FEATURE_NAMES),
                },
                session_id=session_id,
                run_id=run_id,
            )
            return ok, result

        except Exception as exc:
            ok = self._log(
                "qs_enrich_error",
                {"error": repr(exc), "qs_id": self._ds01_qs_id},
                severity="ERROR",
                session_id=session_id,
                run_id=run_id,
            )
            return False, feature_df

    # ------------------------------------------------------------------
    # Feature name registry
    # ------------------------------------------------------------------

    def get_qualitative_feature_names(self) -> list[str]:
        """
        Return qualitative feature column names for all loaded snapshots.
        Only includes DS-01 names when a snapshot is actually loaded.
        """
        names: list[str] = []
        if self._ds01_df is not None:
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
