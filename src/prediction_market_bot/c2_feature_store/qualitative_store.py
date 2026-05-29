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

# DS-01 PAM raw columns loaded from CSV (used internally, not directly as model features)
_DS01_PRF_RAW: list[str] = [
    "prf_primary",       # integer 1–15 (used to compute one-hot; not a model feature)
    "prf_secondary",     # integer 0–15 (used to compute one-hot; not a model feature)
    "prf_hybrid_weight", # float 0–1   (used to compute one-hot; not a model feature)
]

# Weighted one-hot PRF features (F-103–F-117) — replace raw integer columns
# prf_w01 = weight assigned to PRF-1 archetype for this player (0.0–1.0)
# For pure players: prf_w{primary} = 1.0, all others = 0.0
# For hybrids:      prf_w{primary} = prf_hybrid_weight, prf_w{secondary} = 1-weight
PRF_ONEHOT_FEATURES: list[str] = [f"prf_w{i:02d}" for i in range(1, 16)]  # F-103–F-117

_DS01_MODIFIER_FEATURES: list[str] = [
    f"mod_{i:02d}" for i in range(1, 33)   # F-150–F-181: binary flags
]

# Full feature name list for model input (one-hot PRF + modifiers, no raw integers)
DS01_FEATURE_NAMES: list[str] = PRF_ONEHOT_FEATURES + _DS01_MODIFIER_FEATURES

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
            # No snapshot loaded — append all-NaN columns (one-hot PRF + modifiers) and warn
            result = feature_df.copy()
            for col in DS01_FEATURE_NAMES:  # PRF_ONEHOT_FEATURES + modifiers
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
            # Columns to pull from QS snapshot: raw PRF integers + modifiers + temporal guards.
            # prf_w01…prf_w15 are DERIVED (computed below) — they don't exist in the CSV.
            raw_join_cols = (
                ["player_id", "effective_from", "effective_until"]
                + _DS01_PRF_RAW          # prf_primary, prf_secondary, prf_hybrid_weight
                + _DS01_MODIFIER_FEATURES  # mod_01…mod_32
            )
            qs_df = self._ds01_df[[c for c in raw_join_cols if c in self._ds01_df.columns]].copy()

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

            # Convert raw PRF integers to weighted one-hot (prf_w01…prf_w15)
            # and drop the raw integer columns from the feature vector
            result = self.compute_prf_onehot(result)
            result = result.drop(columns=_DS01_PRF_RAW, errors="ignore")

            n_enriched = int((~outside_window).sum())
            n_outside = int(outside_window.sum())
            # prf_w01 is NaN for unclassified rows (outside window or no player match)
            n_prf_nan = int(result["prf_w01"].isna().sum()) if "prf_w01" in result.columns else 0
            n_no_player = max(0, n_prf_nan - n_outside)

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
    # PRF weighted one-hot encoding
    # ------------------------------------------------------------------

    @staticmethod
    def compute_prf_onehot(df: pd.DataFrame) -> pd.DataFrame:
        """
        Convert prf_primary / prf_secondary / prf_hybrid_weight columns into
        15 weighted continuous features prf_w01…prf_w15 (F-103–F-117).

        Encoding rules (PAM v4 weighted hybrid notation):
          - Pure player (prf_secondary == 0 or NaN): prf_w{primary} = 1.0
          - Hybrid player: prf_w{primary} = prf_hybrid_weight
                           prf_w{secondary} = 1 - prf_hybrid_weight
          - Unclassified (prf_primary NaN): all prf_wXX = NaN

        Values sum to 1.0 per row (for classified rows).
        Integer encoding (PRF-9 > PRF-1) is replaced — proper ordinality-free
        representation that lets LR learn separate coefficients per archetype.
        """
        result = df.copy()
        for col in PRF_ONEHOT_FEATURES:
            result[col] = 0.0

        primary  = pd.to_numeric(df.get("prf_primary",   pd.Series(dtype=float)), errors="coerce")
        secondary = pd.to_numeric(df.get("prf_secondary", pd.Series(dtype=float)), errors="coerce").fillna(0)
        weight    = pd.to_numeric(df.get("prf_hybrid_weight", pd.Series(dtype=float)), errors="coerce")

        has_primary = primary.notna() & primary.between(1, 15)
        is_pure     = has_primary & ((secondary == 0) | secondary.isna())
        is_hybrid   = has_primary & secondary.between(1, 15)

        # Primary weight: 1.0 for pure players; prf_hybrid_weight for hybrids
        primary_w = pd.Series(float("nan"), index=df.index)
        primary_w[is_pure]   = 1.0
        primary_w[is_hybrid] = weight[is_hybrid].fillna(1.0)

        # Distribute primary weight
        for prf_id in range(1, 16):
            col  = f"prf_w{prf_id:02d}"
            mask = has_primary & (primary == prf_id)
            result.loc[mask, col] = primary_w[mask]

        # Distribute secondary weight (1 - primary_w)
        secondary_w = (1.0 - primary_w).where(is_hybrid, other=0.0)
        for prf_id in range(1, 16):
            col  = f"prf_w{prf_id:02d}"
            mask = is_hybrid & (secondary == prf_id)
            result.loc[mask, col] += secondary_w[mask]

        # Unclassified rows → NaN (not 0 — model must distinguish "no data" from "PRF weight = 0")
        no_prf = ~has_primary
        for col in PRF_ONEHOT_FEATURES:
            result.loc[no_prf, col] = float("nan")

        return result

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
