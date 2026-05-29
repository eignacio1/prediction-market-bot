"""
C2 Sub-module: Qualitative Amplifier — Layer 3 Context-Conditional Features
=============================================================================
Component:    C2 (Feature Store) — Layer 3 amplification sub-module
Phase active: Phase 6+ (pending first amplification experiment)
Status:       SKELETON — architecture defined; implementation pending OQ-021 study design
Feature IDs:  F-300–F-399
Interfaces:   Consumes Layer 1 (F-001–F-031) + Layer 2 (F-100+) features
              Produces F-300+ interaction/amplification features

Core principle (QUALITATIVE_SIGNALS.md §7):
  Qualitative signals (Layer 2) are auxiliary enhancements to quantitative
  computation (Layer 1). Their effect on outcome probability is NOT uniform
  across game contexts — it is AMPLIFIED in high-leverage, high-variance,
  or emotionally-loaded situations.

  The Emotional Relay Index (ERI v0, F-036–F-038) was pruned in v1.2.0 because
  it applied momentum signals uniformly. The signal existed but was diluted by
  contexts where it carries no information (blowouts, low-stakes regular season
  stretches). This module re-introduces context-conditional qualitative effects
  as explicit interaction features rather than globally-applied signals.

Why qualitative factors are amplified in high-leverage contexts:
  In close games, overtime, long scoring droughts, or playoff situations:
    - A heliocentric PRF-1 player's M-16 (clutch process) dominates possession outcomes
    - A PRF-2 player's M-17 (high variance) on a long cold streak has outsized
      downside risk vs the same player mid-season
    - A PRF-9 rim protector's M-10 (rim deterrence) during an opponent scoring run
      is the primary swing factor for the next 2-4 possessions
    - M-31 (late-career athletic decline) matters far more in 4th-quarter defensive
      assignments than in mid-game bench stints

Amplification contexts (initial set — expand via OQ-021):
  CTX-1: Game closeness proxy — plus_minus trend (rolling variance close to 0)
  CTX-2: Cold streak amplifier — pts_cold_flag + games_played_prior
  CTX-3: Hot streak amplifier — pts_hot_flag × high_usage context
  CTX-4: Season stakes — games_played_prior as proxy for season stage
  CTX-5: Load stress — min_season_mean vs current min (above-load flag)

F-300+ feature range:
  F-300–F-314: PRF archetype × cold streak (15 features, one per PRF)
  F-315–F-329: PRF archetype × hot streak (15 features)
  F-330–F-344: Modifier × season stakes (high-leverage modifiers × season stage)
  F-345–F-399: Reserved for future amplification contexts

Kill switch constraint (NFR-03):
  All public methods return (bool, DataFrame).
  False on any C6 write failure. Callers must trigger kill switch.

Open question: OQ-021 — amplification study design
  Before implementing, resolve OQ-021:
    - Which amplification contexts produce the largest per-context Brier Δ?
    - Do PRF-1 (heliocentric) × clutch interactions outperform PRF-9 × defensive
      run interactions?
    - At what season-stage does load stress (CTX-5) become measurable?
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

import numpy as np
import pandas as pd

from prediction_market_bot.c6_audit_logger.audit_logger import AuditLogger
from prediction_market_bot.c2_feature_store.qualitative_store import PRF_ONEHOT_FEATURES

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

COMPONENT = "C2-AMP"

# F-300+ feature ranges
_PRF_COLD_FEATURES: list[str] = [f"amp_prf_cold_{i:02d}" for i in range(1, 16)]   # F-300–F-314
_PRF_HOT_FEATURES:  list[str] = [f"amp_prf_hot_{i:02d}"  for i in range(1, 16)]   # F-315–F-329
_MOD_STAKES_FEATURES: list[str] = [                                                 # F-330–F-334
    "amp_m16_clutch_stakes",     # M-16 × season_stage (late-season games matter more)
    "amp_m17_variance_cold",     # M-17 × pts_cold_flag (high-variance player in cold streak)
    "amp_m17_variance_hot",      # M-17 × pts_hot_flag  (high-variance player in hot streak)
    "amp_m19_load_stress",       # M-19 × above-avg-minutes flag (injury-prone + load spike)
    "amp_m31_late_season",       # M-31 × late-season stage (age-decline amplified at season end)
]

AMP_FEATURE_NAMES: list[str] = (
    _PRF_COLD_FEATURES + _PRF_HOT_FEATURES + _MOD_STAKES_FEATURES
)

# Season stage breakpoints (games_played_prior)
_EARLY_SEASON_THRESHOLD = 20    # games 0-20: early season
_MID_SEASON_THRESHOLD   = 55    # games 20-55: mid season
# late season: > 55 games prior


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _utc_now_iso() -> str:
    return datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


def _amp_run_id() -> str:
    return f"AMP-RUN-{uuid.uuid4().hex[:10].upper()}"


def _season_stage(games_played_prior: pd.Series) -> pd.Series:
    """Continuous season stage [0.0, 1.0] from games played prior."""
    gpp = pd.to_numeric(games_played_prior, errors="coerce").fillna(0)
    return (gpp / 82.0).clip(0.0, 1.0)


# ---------------------------------------------------------------------------
# QualitativeAmplifier
# ---------------------------------------------------------------------------


class QualitativeAmplifier:
    """
    Layer 3: context-conditional qualitative amplification features (F-300+).

    Computes interaction terms between Layer 2 qualitative features and
    Layer 1 game-context signals. Produces per-game amplification scores
    that reflect WHEN a player's qualitative profile matters most.

    Status: SKELETON — compute_amplification() is stubbed.
    Implement after OQ-021 study design is resolved.

    Usage (once implemented)::

        amp = QualitativeAmplifier(logger=audit_logger, snapshot_id=snap_id)
        ok, enriched_df = amp.compute_amplification(
            feature_df=qualitatively_enriched_df,
            session_id=session_id,
        )
        if not ok:
            trigger_kill_switch()

    The returned DataFrame has all original columns plus F-300+ appended.
    Rows with NaN Layer 2 features produce NaN F-300+ features (no amplification
    signal possible without archetype classification).
    """

    def __init__(self, logger: AuditLogger, snapshot_id: str) -> None:
        self._logger = logger
        self._snapshot_id = snapshot_id

    def _log(self, event_type: str, payload: dict[str, Any],
             severity: str = "INFO", session_id: str | None = None,
             run_id: str | None = None) -> bool:
        return self._logger.log(
            component=COMPONENT, event_type=event_type, payload=payload,
            severity=severity, session_id=session_id,
            snapshot_id=self._snapshot_id, feature_run_id=run_id,
        )

    def compute_amplification(
        self,
        feature_df: pd.DataFrame,
        session_id: str | None = None,
    ) -> tuple[bool, pd.DataFrame]:
        """
        Compute F-300+ amplification features from Layer 1 + Layer 2 inputs.

        Requires both quantitative features (pts_cold_flag, pts_hot_flag,
        games_played_prior, min_season_mean) and qualitative features
        (prf_w01…prf_w15, mod_16, mod_17, mod_19, mod_31) to be present.

        Returns (ok, enriched_df) with F-300+ columns appended.
        NaN for rows where Layer 2 features are absent.

        Status: STUB — implement after OQ-021 study design.
        """
        run_id = _amp_run_id()
        ok = self._log(
            "amp_compute_start",
            {"input_rows": len(feature_df), "amp_features": len(AMP_FEATURE_NAMES)},
            session_id=session_id, run_id=run_id,
        )
        if not ok:
            return False, feature_df

        result = feature_df.copy()

        # --- STUB: implement each amplification context ---
        # CTX-2/3: PRF archetype × streak (cold/hot flag)
        # cold_flag = feature_df.get("pts_cold_flag", pd.Series(0, index=feature_df.index))
        # hot_flag  = feature_df.get("pts_hot_flag",  pd.Series(0, index=feature_df.index))
        # for i, prf_col in enumerate(PRF_ONEHOT_FEATURES):
        #     prf_w = feature_df.get(prf_col, pd.Series(float("nan"), index=feature_df.index))
        #     result[_PRF_COLD_FEATURES[i]] = prf_w * cold_flag
        #     result[_PRF_HOT_FEATURES[i]]  = prf_w * hot_flag
        #
        # CTX-4: Modifier × season stakes
        # stage = _season_stage(feature_df.get("games_played_prior", pd.Series(0)))
        # m16 = pd.to_numeric(feature_df.get("mod_16", 0), errors="coerce").fillna(0)
        # m17 = pd.to_numeric(feature_df.get("mod_17", 0), errors="coerce").fillna(0)
        # m19 = pd.to_numeric(feature_df.get("mod_19", 0), errors="coerce").fillna(0)
        # m31 = pd.to_numeric(feature_df.get("mod_31", 0), errors="coerce").fillna(0)
        # result["amp_m16_clutch_stakes"]  = m16 * stage
        # result["amp_m17_variance_cold"]  = m17 * cold_flag
        # result["amp_m17_variance_hot"]   = m17 * hot_flag
        # result["amp_m19_load_stress"]    = m19 * (stage > 0.7).astype(float)
        # result["amp_m31_late_season"]    = m31 * stage
        # --- END STUB ---

        # Stub: append NaN columns so schema is stable for experiment runners
        for col in AMP_FEATURE_NAMES:
            if col not in result.columns:
                result[col] = float("nan")

        ok = self._log(
            "amp_compute_stub",
            {
                "output_rows": len(result),
                "amp_cols_appended": AMP_FEATURE_NAMES,
                "note": (
                    "QualitativeAmplifier.compute_amplification() is running in stub mode. "
                    "All F-300+ features are NaN. Resolve OQ-021 before implementing."
                ),
            },
            severity="WARNING",
            session_id=session_id, run_id=run_id,
        )
        return ok, result

    def get_amplification_feature_names(self) -> list[str]:
        """Return F-300+ feature names. Empty until stub is implemented."""
        return []  # Return empty until implemented — avoids NaN-all columns in model
