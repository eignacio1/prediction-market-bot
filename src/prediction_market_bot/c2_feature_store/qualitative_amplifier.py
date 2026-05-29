"""
C2 Sub-module: Qualitative Amplifier — Layer 3 Context-Conditional Features
=============================================================================
Component:    C2 (Feature Store) — Layer 3 amplification sub-module
Phase active: Phase 6+
Status:       IMPLEMENTED — 2026-05-28 (EXP-009)
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

    Usage::

        amp = QualitativeAmplifier(logger=audit_logger, snapshot_id=snap_id)
        ok, enriched_df = amp.compute_amplification(
            feature_df=qualitatively_enriched_df,   # must have L1 + L2 features
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
        idx = feature_df.index

        def _col(name: str, default: float = 0.0) -> pd.Series:
            """Safe column fetch: returns default-filled numeric Series."""
            if name in feature_df.columns:
                return pd.to_numeric(feature_df[name], errors="coerce").fillna(default)
            return pd.Series(default, index=idx, dtype=float)

        # ------------------------------------------------------------------
        # CTX-2: PRF archetype × cold streak (F-300–F-314)
        # Captures which archetype players in cold form deviate most from mean.
        # PRF-1 (heliocentric) cold: team-wide possession disruption.
        # PRF-9 (rim protector) cold: mostly noise (scoring not their role).
        # ------------------------------------------------------------------
        cold_flag = _col("pts_cold_flag")
        for i, prf_col in enumerate(PRF_ONEHOT_FEATURES):
            prf_w = feature_df[prf_col] if prf_col in feature_df.columns else pd.Series(float("nan"), index=idx)
            result[_PRF_COLD_FEATURES[i]] = prf_w * cold_flag

        # ------------------------------------------------------------------
        # CTX-3: PRF archetype × hot streak (F-315–F-329)
        # Captures hot-hand amplification by archetype.
        # PRF-1 (heliocentric) hot: elevated usage + confidence compounds scoring.
        # PRF-17 (high-variance, via M-17) hot: regression-to-mean risk.
        # ------------------------------------------------------------------
        hot_flag = _col("pts_hot_flag")
        for i, prf_col in enumerate(PRF_ONEHOT_FEATURES):
            prf_w = feature_df[prf_col] if prf_col in feature_df.columns else pd.Series(float("nan"), index=idx)
            result[_PRF_HOT_FEATURES[i]] = prf_w * hot_flag

        # ------------------------------------------------------------------
        # CTX-4/5: Modifier × situational context (F-330–F-334)
        # ------------------------------------------------------------------
        stage = _season_stage(_col("games_played_prior"))

        m16 = _col("mod_16")   # Elite Clutch Process
        m17 = _col("mod_17")   # High Variance / Streak Profile
        m19 = _col("mod_19")   # Injury-Managed / Load-Sensitive
        m31 = _col("mod_31")   # Late-Career Athletic Decline

        # amp_m16_clutch_stakes: clutch identity amplified as season progresses.
        # Late-season games concentrate high-leverage possessions (playoff races,
        # seeding games) — M-16 players matter more per possession than at mid-season.
        result["amp_m16_clutch_stakes"] = m16 * stage

        # amp_m17_variance_cold: high-variance player in a cold streak.
        # M-17 players have wider σ(per-game pts). In cold streaks, their
        # variance works against consistency — amplified downside signal.
        result["amp_m17_variance_cold"] = m17 * cold_flag

        # amp_m17_variance_hot: high-variance player in a hot streak.
        # Opposite direction — hot M-17 players are above their true mean,
        # elevating the probability of exceeding their rolling threshold.
        result["amp_m17_variance_hot"] = m17 * hot_flag

        # amp_m19_load_stress: injury-managed player late in season.
        # M-19 players' injury risk and performance degradation are most
        # acute in the final quarter of the season (stage > 0.75).
        # Binary amplification at late-season threshold.
        late_season = (stage >= 0.75).astype(float)
        result["amp_m19_load_stress"] = m19 * late_season

        # amp_m31_late_season: late-career athletic decline amplified by season stage.
        # M-31 players show most visible decline in minutes-intensive late-season
        # stretches where fatigue accumulates. Continuous stage multiplier.
        result["amp_m31_late_season"] = m31 * stage

        # ------------------------------------------------------------------
        # Summary stats for audit log
        # ------------------------------------------------------------------
        n_amp_rows = int(result[_PRF_COLD_FEATURES[0]].notna().sum())  # PRF-1 cold as probe
        n_cold_active = int((cold_flag > 0).sum())
        n_hot_active  = int((hot_flag > 0).sum())

        ok = self._log(
            "amp_compute_complete",
            {
                "output_rows": len(result),
                "amp_feature_count": len(AMP_FEATURE_NAMES),
                "rows_with_amp_values": n_amp_rows,
                "cold_flag_active_rows": n_cold_active,
                "hot_flag_active_rows": n_hot_active,
                "contexts": ["CTX-2 PRF×cold", "CTX-3 PRF×hot",
                             "CTX-4 M16×stage", "CTX-4b M17×streak", "CTX-5 M19/M31×stage"],
            },
            session_id=session_id, run_id=run_id,
        )
        return ok, result

    def get_amplification_feature_names(self) -> list[str]:
        """Return F-300+ feature names (35 total: 15 PRF×cold + 15 PRF×hot + 5 mod×context)."""
        return list(AMP_FEATURE_NAMES)
