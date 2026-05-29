"""
C2: Feature Store — PRF-Aligned Feature Derivation
====================================================

Component:    C2 (Feature Store)
Phase active: Phase 3+ (Research Build)
Status:       CANONICAL (Phase 3 2026-05-26)
Upstream:     C1 Signal Ingestion (IF-C1-C2 player-game DataFrame)
Downstream:   C3 Forecasting Engine (IF-C2-C3 feature DataFrame)
Interfaces:   IF-C1-C2 (input); IF-C2-C3 (output)
ADR refs:     ADR-0001 (Compass OS), ADR-0002 (forecast-only)
Policy refs:  DATA_FLOWS_LINEAGE.md, INTERFACES_CONTRACTS.md,
              07_TEST_VALIDATION_EVIDENCE/TEST_STRATEGY.md

Temporal integrity (TI-01 through TI-04):
  - All features are computed using ONLY data from games strictly BEFORE
    or AT the target game_date.
  - Rolling windows are computed over the N most recent PRIOR games.
    The current game's box score is EXCLUDED from its own feature vector
    (look-ahead prevention).
  - temporal_cutoff per row = game_date of the LAST game in the rolling
    window used to produce those features (= the prior game's date).
  - Outcome data (DS-03) NEVER enters this component (TI-03).
  - Train/test split is chronological only (TI-02). No random shuffle.

Feature version policy:
  - FEATURE_VERSION is incremented when any feature definition changes.
  - All experiment records must cite the feature_version used.
  - Model retrain is required after any feature change in ENV-03.

v1.3.0 additions (2026-05-29 — T-075):
  - F-039: is_home_game — binary (1=home, 0=away) from C1 MATCHUP parsing.
    Passed through from C1 output; requires matchup column in game log data.
  - F-040: opp_def_rating_l10_mean — opponent team's rolling mean pts_allowed
    over prior 10 games (= pts_scored - plus_minus from TeamGameLog).
    Requires TeamStatsStore built from TeamGameLog data.
    NaN when TeamStatsStore not provided or opponent data insufficient.
  Total features: 33 (was 31 in v1.2.0; +2 new opponent/context features)

v1.2.0 changes (2026-05-28 — T-046):
  - PRUNED: F-032–F-038 (schedule/load and ERI v0 features)
    HYP-005 falsified — Δ Brier = +0.0002 (threshold 0.005); no meaningful
    incremental signal. Features removed: season_type_is_playoffs,
    days_since_last_game, b2b_flag, load_games_l7d, eri_prev_hot,
    eri_prev_cold, eri_consec_cold_games.
  Total features: 31 (was 38 in v1.1.0)

v1.1.0 additions (2026-05-27 — T-037): [PRUNED in v1.2.0]
  - Schedule/load context: season_type_is_playoffs, days_since_last_game,
    b2b_flag, load_games_l7d
  - ERI v0 (Emotional Relay Index): eri_prev_hot, eri_prev_cold,
    eri_consec_cold_games

Rolling window:
  - Default: 10 games (L10)
  - Minimum periods: 3 (rows with fewer prior games return NaN features)
  - Window is computed per-player, sorted by game_date ascending.

Feature naming convention:
  - {stat}_{window}_{agg}  e.g.  pts_l10_mean, pts_l10_std
  - Efficiency metrics use descriptive names: ts_pct, usage_proxy, ast_tov
  - Regime/streak flags: {stat}_hot_flag, {stat}_cold_flag
  - Threshold for hot/cold: mean ± 1.0 * std over the window

Kill switch constraint (NFR-03):
  - All public methods return (bool, DataFrame).
  - False indicates a C6 write failure; callers must trigger kill switch.

Audit events emitted:
  - feature_derivation_start   (INFO)
  - feature_derivation_complete (INFO) — includes row count, feature count
  - feature_derivation_error    (ERROR) — unhandled exception in derivation
  - temporal_integrity_warning  (WARNING) — if any temporal_cutoff is null
  - train_test_split_applied    (INFO) — split date boundaries
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, TYPE_CHECKING

import numpy as np
import pandas as pd

if TYPE_CHECKING:
    from prediction_market_bot.c1_signal_ingestion.team_stats_store import TeamStatsStore

from prediction_market_bot.c6_audit_logger.audit_logger import AuditLogger

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

COMPONENT = "C2"

# Feature set version — increment on any feature definition change
FEATURE_VERSION = "1.3.0"

# Rolling window size (games)
DEFAULT_WINDOW = 10

# Minimum prior games required to produce non-NaN rolling features
MIN_PERIODS = 3

# Train/test split labels (TI-02)
LABEL_TRAIN = "TRAIN"
LABEL_VALIDATION = "VALIDATION"
LABEL_TEST = "TEST"

# IF-C2-C3 output columns (required by INTERFACES_CONTRACTS.md IF-C2-C3)
_ID_COLUMNS = [
    "player_id",
    "player_name",
    "game_id",
    "game_date",
    "season",
    "season_type",
    "snapshot_id",
    "feature_run_id",
    "feature_version",
    "temporal_cutoff",
    "train_test_label",
]

# Rolling mean features
_ROLLING_MEAN_STATS = [
    "pts",
    "reb",
    "ast",
    "stl",
    "blk",
    "tov",
    "min",
    "fg_pct",
    "fg3_pct",
    "ft_pct",
    "plus_minus",
    "fgm",
    "fga",
    "fg3m",
    "fg3a",
    "ftm",
    "fta",
    "pf",
]

# Rolling std features (subset — model variance, not all stats)
_ROLLING_STD_STATS = ["pts", "reb", "ast", "min", "plus_minus"]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _utc_now_iso() -> str:
    """UTC ISO 8601 timestamp with milliseconds."""
    return datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


def _run_id() -> str:
    """Generate a feature derivation run ID."""
    return f"C2-RUN-{uuid.uuid4().hex[:10].upper()}"


def _safe_div(numerator: pd.Series, denominator: pd.Series) -> pd.Series:
    """Element-wise division returning NaN where denominator is 0 or NaN."""
    with np.errstate(divide="ignore", invalid="ignore"):
        result = numerator / denominator.replace(0, np.nan)
    return result


# ---------------------------------------------------------------------------
# Core feature computation
# ---------------------------------------------------------------------------


def _compute_rolling_features(
    player_df: pd.DataFrame,
    window: int,
    min_periods: int,
) -> pd.DataFrame:
    """
    Compute all rolling features for a single player's game log.

    IMPORTANT: The rolling window for game N uses games [0 … N-1] only.
    We achieve this with .shift(1) before applying .rolling(), so game N's
    features are computed from the prior N games — never from itself.
    This is the core temporal integrity guarantee (TI-01).

    Parameters
    ----------
    player_df:
        DataFrame of one player's games, sorted by game_date ascending.
        Must contain all IF-C1-C2 columns.
    window:
        Number of prior games to include in rolling window.
    min_periods:
        Minimum prior games required to produce non-NaN features.

    Returns
    -------
    DataFrame with one row per game, feature columns added.
    The original IF-C1-C2 columns are retained alongside features.
    """
    df = player_df.copy()

    # Ensure chronological sort (temporal integrity prerequisite)
    df = df.sort_values("game_date", ascending=True).reset_index(drop=True)

    # Numeric coercion — nba_api can return mixed types
    numeric_cols = [
        "pts", "reb", "ast", "stl", "blk", "tov", "min",
        "fgm", "fga", "fg_pct", "fg3m", "fg3a", "fg3_pct",
        "ftm", "fta", "ft_pct", "plus_minus", "pf",
    ]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # ---------------------------------------------------------------------------
    # Rolling mean features
    # We shift(1) so each row uses prior games only.
    # ---------------------------------------------------------------------------
    for stat in _ROLLING_MEAN_STATS:
        if stat in df.columns:
            col_name = f"{stat}_l{window}_mean"
            df[col_name] = (
                df[stat]
                .shift(1)
                .rolling(window=window, min_periods=min_periods)
                .mean()
            )

    # ---------------------------------------------------------------------------
    # Rolling std features (volatility)
    # ---------------------------------------------------------------------------
    for stat in _ROLLING_STD_STATS:
        if stat in df.columns:
            col_name = f"{stat}_l{window}_std"
            df[col_name] = (
                df[stat]
                .shift(1)
                .rolling(window=window, min_periods=min_periods)
                .std(ddof=1)
            )

    # ---------------------------------------------------------------------------
    # Efficiency features (computed from current game's cumulative season stats)
    # These are NOT look-ahead: they use per-game box score columns, which are
    # the inputs to the prediction target, not the target itself.
    # ---------------------------------------------------------------------------

    # True Shooting %: TS% = PTS / (2 * (FGA + 0.44 * FTA))
    # Uses rolling L10 means to produce a stable efficiency estimate
    ts_numerator = df.get("pts_l{}_mean".format(window), pd.Series(dtype=float))
    fga_mean = df.get("fga_l{}_mean".format(window), pd.Series(dtype=float))
    fta_mean = df.get("fta_l{}_mean".format(window), pd.Series(dtype=float))
    if not ts_numerator.empty and not fga_mean.empty and not fta_mean.empty:
        ts_denom = 2.0 * (fga_mean + 0.44 * fta_mean)
        df["ts_pct_l{}_mean".format(window)] = _safe_div(ts_numerator, ts_denom)

    # Usage proxy: approximation of possession-usage rate
    # Usage ≈ (FGM + 0.44*FTM + TOV) / MAX(MIN, 1)
    # Uses rolling L10 means
    fgm_mean = df.get("fgm_l{}_mean".format(window), pd.Series(dtype=float))
    ftm_mean = df.get("ftm_l{}_mean".format(window), pd.Series(dtype=float))
    tov_mean = df.get("tov_l{}_mean".format(window), pd.Series(dtype=float))
    min_mean = df.get("min_l{}_mean".format(window), pd.Series(dtype=float))
    if not fgm_mean.empty and not ftm_mean.empty and not tov_mean.empty and not min_mean.empty:
        usage_num = fgm_mean + 0.44 * ftm_mean + tov_mean
        df["usage_proxy_l{}_mean".format(window)] = _safe_div(
            usage_num, min_mean.clip(lower=1.0)
        )

    # Assist-to-Turnover ratio (rolling)
    ast_mean = df.get("ast_l{}_mean".format(window), pd.Series(dtype=float))
    if not ast_mean.empty and not tov_mean.empty:
        df["ast_tov_l{}_mean".format(window)] = _safe_div(
            ast_mean, tov_mean.replace(0, np.nan)
        )

    # ---------------------------------------------------------------------------
    # Regime / streak flags
    # hot_flag: rolling L10 mean pts > 75th percentile of player's season pts
    # cold_flag: rolling L10 mean pts < 25th percentile of player's season pts
    # Computed as mean ± 1 std of the rolling pts mean (cross-game)
    # ---------------------------------------------------------------------------
    pts_mean_col = f"pts_l{window}_mean"
    pts_std_col = f"pts_l{window}_std"
    if pts_mean_col in df.columns and pts_std_col in df.columns:
        # Use the player-level rolling statistics to define thresholds
        player_pts_baseline = df[pts_mean_col].expanding(min_periods=3).mean()
        player_pts_vol = df[pts_mean_col].expanding(min_periods=3).std(ddof=1).fillna(0)
        df["pts_hot_flag"] = (
            (df[pts_mean_col] > (player_pts_baseline + player_pts_vol)).astype("Int8")
        )
        df["pts_cold_flag"] = (
            (df[pts_mean_col] < (player_pts_baseline - player_pts_vol)).astype("Int8")
        )
    else:
        df["pts_hot_flag"] = pd.array([pd.NA] * len(df), dtype="Int8")
        df["pts_cold_flag"] = pd.array([pd.NA] * len(df), dtype="Int8")

    # ---------------------------------------------------------------------------
    # Season context features
    # ---------------------------------------------------------------------------
    # Games played in this season before this game (0-indexed game number)
    df["games_played_prior"] = df.groupby(
        ["player_id", "season", "season_type"], sort=False
    ).cumcount()

    # Season-to-date mean points (using prior games only via shift + expanding)
    df["pts_season_mean"] = (
        df["pts"].shift(1).expanding(min_periods=1).mean()
    )
    df["min_season_mean"] = (
        df["min"].shift(1).expanding(min_periods=1).mean()
    )

    # ---------------------------------------------------------------------------
    # Temporal cutoff: date of the most recent prior game used in this row's window.
    # For row i, the prior game is row i-1 (after sort). If no prior game,
    # temporal_cutoff = NaT (feature row is not usable for training).
    # ---------------------------------------------------------------------------
    df["temporal_cutoff"] = df["game_date"].shift(1)

    # ---------------------------------------------------------------------------
    # F-039: is_home_game — passed through from C1 MATCHUP parsing (v1.3.0+)
    # Already present as Int8 column from C1 if matchup data was pulled.
    # No computation needed here — C1 derives it. We just ensure it's present.
    # ---------------------------------------------------------------------------
    if "is_home_game" not in df.columns:
        df["is_home_game"] = pd.array([pd.NA] * len(df), dtype="Int8")

    return df


def _compute_opponent_features(
    df: pd.DataFrame,
    team_stats_store: "TeamStatsStore",
    window: int = DEFAULT_WINDOW,
) -> pd.DataFrame:
    """
    Compute opponent-context features for each row using TeamStatsStore.

    Called once per player-group after _compute_rolling_features().
    Temporal integrity: TeamStatsStore.get_opp_def_rating() uses games
    strictly before the player's game_date (TI-01 preserved).

    Features computed:
      F-040: opp_def_rating_l10_mean — opponent team's rolling mean pts_allowed
    """
    opp_def: list[float] = []

    for _, row in df.iterrows():
        opp_abbr = row.get("opponent_team_abbr")
        game_date = row.get("game_date")
        if pd.isna(opp_abbr) or opp_abbr is None or pd.isna(game_date):
            opp_def.append(np.nan)
        else:
            rating = team_stats_store.get_opp_def_rating(
                str(opp_abbr), str(game_date), window=window
            )
            opp_def.append(rating if rating is not None else np.nan)

    return pd.DataFrame({"opp_def_rating_l10_mean": opp_def}, index=df.index)


# ---------------------------------------------------------------------------
# FeatureStore
# ---------------------------------------------------------------------------


class FeatureStore:
    """
    C2 Feature Store — computes PRF-aligned feature vectors from C1 game-log data.

    Usage::

        store = FeatureStore(logger=audit_logger, snapshot_id="SNAP-2024-10-01-001")
        ok, feature_df = store.compute_features_bulk(
            game_log_df=c1_output_df,
            session_id=session_id,
        )
        if not ok:
            trigger_kill_switch()

    All public methods return (bool, pd.DataFrame).
    False indicates an audit log write failure; callers must trigger the kill switch.

    The feature DataFrame (IF-C2-C3 schema) contains:
      - ID columns: player_id, game_id, game_date, season, snapshot_id, ...
      - Rolling features: pts_l10_mean, reb_l10_mean, ... (ROLLING_MEAN_STATS)
      - Std features: pts_l10_std, reb_l10_std, ...    (ROLLING_STD_STATS)
      - Efficiency: ts_pct_l10_mean, usage_proxy_l10_mean, ast_tov_l10_mean
      - Regime flags: pts_hot_flag, pts_cold_flag
      - Context: games_played_prior, pts_season_mean, min_season_mean
      - Metadata: feature_run_id, feature_version, temporal_cutoff, train_test_label

    train_test_label is set to None until assign_train_test_labels() is called.
    """

    def __init__(
        self,
        logger: AuditLogger,
        snapshot_id: str,
        window: int = DEFAULT_WINDOW,
    ) -> None:
        """
        Parameters
        ----------
        logger:
            Shared AuditLogger instance (C6). Must be pre-initialised.
        snapshot_id:
            DS-01 snapshot anchor (e.g. 'SNAP-2024-10-01-001').
            Flows through to all output rows for traceability.
        window:
            Rolling window size in games. Default 10.
        """
        self._logger = logger
        self._snapshot_id = snapshot_id
        self._window = window

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _log(self, event_type: str, payload: dict[str, Any], severity: str = "INFO",
             session_id: str | None = None, feature_run_id: str | None = None) -> bool:
        return self._logger.log(
            component=COMPONENT,
            event_type=event_type,
            payload=payload,
            severity=severity,
            session_id=session_id,
            snapshot_id=self._snapshot_id,
            feature_run_id=feature_run_id,
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def compute_features_bulk(
        self,
        game_log_df: pd.DataFrame,
        session_id: str | None = None,
        team_stats_store: "TeamStatsStore | None" = None,
    ) -> tuple[bool, pd.DataFrame]:
        """
        Compute PRF-aligned features for all players in a game-log DataFrame.

        Processes each player independently (rolling windows are per-player).
        Players with fewer than MIN_PERIODS prior games will have NaN feature
        rows — these rows are retained but marked with temporal_cutoff=NaT and
        should be excluded from training splits (train_test_label=None).

        Parameters
        ----------
        game_log_df:
            IF-C1-C2 DataFrame from C1 NBAIngestionClient. Must contain at
            minimum: player_id, game_id, game_date, season, season_type,
            snapshot_id, pts, reb, ast, stl, blk, tov, min, fgm, fga, fg_pct,
            fg3m, fg3a, fg3_pct, ftm, fta, ft_pct, plus_minus, pf.
        session_id:
            Current bot run session ID for audit trail.
        team_stats_store:
            Optional TeamStatsStore built from TeamGameLog data (T-075).
            When provided, computes F-040 opp_def_rating_l10_mean for each row.
            When None, opp_def_rating_l10_mean is left as NaN (backward compatible).

        Returns
        -------
        (all_ok, feature_df):
            all_ok — False if any C6 write failed; caller must trigger kill switch.
            feature_df — IF-C2-C3 DataFrame with all feature columns. Empty on
                         unhandled exception.
        """
        run_id = _run_id()
        all_ok = True

        ok = self._log(
            "feature_derivation_start",
            {
                "input_rows": len(game_log_df),
                "player_count": game_log_df["player_id"].nunique() if "player_id" in game_log_df.columns else None,
                "window": self._window,
                "feature_version": FEATURE_VERSION,
            },
            session_id=session_id,
            feature_run_id=run_id,
        )
        if not ok:
            all_ok = False

        try:
            if game_log_df.empty:
                ok = self._log(
                    "feature_derivation_complete",
                    {"output_rows": 0, "note": "empty input — returning empty DataFrame"},
                    session_id=session_id,
                    feature_run_id=run_id,
                )
                if not ok:
                    all_ok = False
                empty_df = pd.DataFrame(columns=_ID_COLUMNS)
                return all_ok, empty_df

            # Process each player independently
            player_chunks: list[pd.DataFrame] = []
            for player_id, player_group in game_log_df.groupby("player_id", sort=False):
                player_features = _compute_rolling_features(
                    player_group,
                    window=self._window,
                    min_periods=MIN_PERIODS,
                )
                # F-040: opponent defensive rating (v1.3.0+) — requires TeamStatsStore
                if team_stats_store is not None:
                    opp_df = _compute_opponent_features(
                        player_features, team_stats_store, window=self._window
                    )
                    player_features = player_features.join(opp_df, how="left")
                else:
                    player_features["opp_def_rating_l10_mean"] = np.nan
                player_chunks.append(player_features)

            if not player_chunks:
                feature_df = pd.DataFrame(columns=_ID_COLUMNS)
            else:
                feature_df = pd.concat(player_chunks, ignore_index=True)

            # Attach metadata required by IF-C2-C3
            feature_df["feature_run_id"] = run_id
            feature_df["feature_version"] = FEATURE_VERSION
            feature_df["train_test_label"] = None  # Assigned by assign_train_test_labels()

            # Warn if any temporal_cutoff is null (row has no prior game — first appearance)
            null_cutoff_count = feature_df["temporal_cutoff"].isna().sum() if "temporal_cutoff" in feature_df.columns else 0
            if null_cutoff_count > 0:
                ok = self._log(
                    "temporal_integrity_warning",
                    {
                        "null_temporal_cutoff_rows": int(null_cutoff_count),
                        "note": (
                            "Rows with null temporal_cutoff have no prior games in window. "
                            "These rows MUST NOT be included in TRAIN/VALIDATION/TEST splits."
                        ),
                    },
                    severity="WARNING",
                    session_id=session_id,
                    feature_run_id=run_id,
                )
                if not ok:
                    all_ok = False

            # Determine feature column count (all non-ID, non-metadata columns)
            feature_cols = [
                c for c in feature_df.columns
                if c not in _ID_COLUMNS
                and c not in game_log_df.columns
            ]

            ok = self._log(
                "feature_derivation_complete",
                {
                    "output_rows": len(feature_df),
                    "player_count": feature_df["player_id"].nunique() if "player_id" in feature_df.columns else None,
                    "feature_count": len(feature_cols),
                    "feature_version": FEATURE_VERSION,
                    "null_temporal_cutoff_rows": int(null_cutoff_count),
                    "window": self._window,
                },
                session_id=session_id,
                feature_run_id=run_id,
            )
            if not ok:
                all_ok = False

            return all_ok, feature_df

        except Exception as exc:
            ok = self._log(
                "feature_derivation_error",
                {"error": repr(exc), "feature_version": FEATURE_VERSION},
                severity="ERROR",
                session_id=session_id,
                feature_run_id=run_id,
            )
            if not ok:
                all_ok = False
            return False, pd.DataFrame(columns=_ID_COLUMNS)

    def assign_train_test_labels(
        self,
        feature_df: pd.DataFrame,
        train_end_date: str,
        val_end_date: str,
        session_id: str | None = None,
    ) -> tuple[bool, pd.DataFrame]:
        """
        Assign chronological train/validation/test split labels to a feature DataFrame.

        Split logic (TI-02 — chronological only, no random shuffle):
          game_date <= train_end_date                    → TRAIN
          train_end_date < game_date <= val_end_date     → VALIDATION
          game_date > val_end_date                       → TEST

        Rows with temporal_cutoff=NaT are set to label=None (excluded from all splits).

        Parameters
        ----------
        feature_df:
            Output of compute_features_bulk().
        train_end_date:
            Last date (inclusive) for training set. Format: "YYYY-MM-DD".
        val_end_date:
            Last date (inclusive) for validation set. Format: "YYYY-MM-DD".
        session_id:
            Current run session ID for audit trail.

        Returns
        -------
        (ok, labeled_df):
            ok — False if C6 write failed.
            labeled_df — feature_df with train_test_label column updated.
        """
        run_id = feature_df["feature_run_id"].iloc[0] if "feature_run_id" in feature_df.columns and len(feature_df) > 0 else _run_id()

        df = feature_df.copy()

        game_dates = pd.to_datetime(df["game_date"], errors="coerce")
        train_end = pd.Timestamp(train_end_date)
        val_end = pd.Timestamp(val_end_date)

        # Rows with null temporal_cutoff → None (unusable for any split)
        has_cutoff = df["temporal_cutoff"].notna() if "temporal_cutoff" in df.columns else pd.Series([True] * len(df))

        df["train_test_label"] = None
        df.loc[has_cutoff & (game_dates <= train_end), "train_test_label"] = LABEL_TRAIN
        df.loc[has_cutoff & (game_dates > train_end) & (game_dates <= val_end), "train_test_label"] = LABEL_VALIDATION
        df.loc[has_cutoff & (game_dates > val_end), "train_test_label"] = LABEL_TEST

        label_counts = df["train_test_label"].value_counts(dropna=False).to_dict()

        ok = self._log(
            "train_test_split_applied",
            {
                "train_end_date": train_end_date,
                "val_end_date": val_end_date,
                "label_counts": {str(k): int(v) for k, v in label_counts.items()},
                "total_rows": len(df),
            },
            session_id=session_id,
            feature_run_id=run_id,
        )

        return ok, df

    def get_feature_names(self) -> list[str]:
        """
        Return a list of all feature column names that this FeatureStore produces.

        Used for DATA_FLOWS_LINEAGE.md feature registration and model input validation.
        """
        w = self._window
        names: list[str] = []

        # Rolling mean
        for stat in _ROLLING_MEAN_STATS:
            names.append(f"{stat}_l{w}_mean")

        # Rolling std
        for stat in _ROLLING_STD_STATS:
            names.append(f"{stat}_l{w}_std")

        # Efficiency composites
        names += [
            f"ts_pct_l{w}_mean",
            f"usage_proxy_l{w}_mean",
            f"ast_tov_l{w}_mean",
        ]

        # Regime flags
        names += ["pts_hot_flag", "pts_cold_flag"]

        # Season context
        names += ["games_played_prior", "pts_season_mean", "min_season_mean"]

        # v1.3.0: opponent and venue context (F-039, F-040)
        names += ["is_home_game", "opp_def_rating_l10_mean"]

        return names
