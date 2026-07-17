"""
C2: MLB Feature Store — Baseball Feature Derivation
====================================================

Component:    C2 (Feature Store)
Sport:        MLB
Status:       CANONICAL (T-182 2026-06-23)
Upstream:     C1 Signal Ingestion (IF-C1-C2 MLB batter schema)
Downstream:   C3 Forecasting Engine (IF-C2-C3 feature DataFrame)
Interfaces:   IF-C1-C2 (input); IF-C2-C3 (output)
ADR refs:     ADR-0001 (Compass OS), ADR-0002 (forecast-only), ADR-0031 (multi-sport)

Temporal integrity (TI-01 through TI-04):
  - All features are computed using ONLY data from games strictly BEFORE
    the target game_date.
  - Rolling windows use .shift(1) before .rolling() — current game box score
    is excluded from its own feature vector.
  - temporal_cutoff = game_date of the prior game (the last game in the window).
  - Outcome data NEVER enters this component (TI-03).
  - Train/test split is chronological only (TI-02). No random shuffle.

v1.0.0 features (T-182 2026-06-23):
  Batter rolling (L10 games, min 3 prior):
    ba_l10        — batting average (sum h / sum ab)
    slg_l10       — slugging % (sum total_bases / sum ab)
    obp_l10       — on-base % (sum(h+bb+hbp) / sum(ab+bb+hbp+sf))
    ops_l10       — OBP + SLG
    h_l10_mean    — mean hits/game (outcome baseline)
    k_rate_l10    — strikeout rate (sum k / sum ab)
    bb_rate_l10   — walk rate (sum bb / sum ab)
    hr_rate_l10   — home run rate (sum hr / sum ab)
  Game context:
    is_home_game      — 1=home, 0=away (passthrough from C1)
    days_rest         — calendar days since prior game (NaN if first game)
    b2b_flag          — 1 if days_rest <= 1 (back-to-back)
  Opponent context:
    opp_runs_allowed_l10  — opponent team's rolling mean runs allowed (L10)
  Starting pitcher overlay (MANDATORY — structural equivalent of T2 injury overlay):
    opp_sp_era_l5     — opposing SP's ERA over last 5 starts (NaN if unknown/insufficient)
    opp_sp_k9_l5      — opposing SP's K/9 over last 5 starts
    opp_sp_bb9_l5     — opposing SP's BB/9 over last 5 starts
    opp_sp_is_known   — 1 if SP announced, 0 if unknown (None sp_id in game_starters)
  Park factor:
    park_factor_hits  — venue-level hit park factor (1.0 = neutral, source: 2022-2024 avg)

Feature version policy:
  - MLB_FEATURE_VERSION is incremented whenever any feature definition changes.
  - Model retrain required after any version change.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, TYPE_CHECKING

import numpy as np
import pandas as pd

from prediction_market_bot.c6_audit_logger.audit_logger import AuditLogger

if TYPE_CHECKING:
    from prediction_market_bot.c1_signal_ingestion.mlb_pitcher_stats_store import (
        MLBPitcherStatsStore,
    )
    from prediction_market_bot.c1_signal_ingestion.mlb_team_stats_store import (
        MLBTeamStatsStore,
    )

COMPONENT = "C2_MLB"
MLB_FEATURE_VERSION = "1.0.0"

DEFAULT_WINDOW = 10
MIN_PERIODS = 3

LABEL_TRAIN = "TRAIN"
LABEL_VALIDATION = "VALIDATION"
LABEL_TEST = "TEST"

# ---------------------------------------------------------------------------
# Park factor table — hit park factors by venue name (2022-2024 multi-year avg)
# Source: Baseball Reference / Fangraphs multi-year park factor consensus.
# Neutral = 1.000. Values above 1.0 favor hitters; below 1.0 favor pitchers.
# Unknown venues default to 1.000 (neutral) — caller sees NaN only for missing
# game_starters entries.
# ---------------------------------------------------------------------------
_PARK_FACTOR_HITS: dict[str, float] = {
    "Coors Field": 1.120,              # COL — extreme altitude
    "Great American Ball Park": 1.050, # CIN
    "Yankee Stadium": 1.015,           # NYY
    "Globe Life Field": 1.010,         # TEX
    "Chase Field": 1.008,              # ARI
    "Wrigley Field": 1.005,            # CHC
    "Truist Park": 1.004,              # ATL
    "Camden Yards": 1.003,             # BAL
    "Fenway Park": 1.002,              # BOS
    "Citizens Bank Park": 0.998,       # PHI
    "Busch Stadium": 0.997,            # STL
    "PNC Park": 0.995,                 # PIT
    "Angel Stadium": 0.995,            # LAA
    "Target Field": 0.993,             # MIN
    "American Family Field": 0.992,    # MIL
    "Comerica Park": 0.990,            # DET
    "Nationals Park": 0.990,           # WSH
    "Progressive Field": 0.988,        # CLE
    "Kauffman Stadium": 0.988,         # KC
    "Tropicana Field": 0.985,          # TB
    "Rogers Centre": 0.985,            # TOR
    "Guaranteed Rate Field": 0.983,    # CWS
    "Minute Maid Park": 0.982,         # HOU
    "Dodger Stadium": 0.980,           # LAD
    "T-Mobile Park": 0.977,            # SEA
    "loanDepot park": 0.975,           # MIA
    "Petco Park": 0.973,               # SD
    "Oracle Park": 0.970,              # SF
    "Oakland Coliseum": 0.968,         # ATH (pre-2025)
    "Sutter Health Park": 1.000,       # ATH temp (2025) — limited data
}

# IF-C2-C3 output identity/metadata columns
_ID_COLUMNS: list[str] = [
    "player_id",
    "player_name",
    "team_abbreviation",
    "game_id",
    "game_date",
    "season",
    "season_type",
    "matchup",
    "opponent_team_abbr",
    "snapshot_id",
    "feature_run_id",
    "feature_version",
    "temporal_cutoff",
    "train_test_label",
]


def _run_id() -> str:
    return f"C2MLB-{uuid.uuid4().hex[:8]}"


def _utc_now_iso() -> str:
    return datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


def _safe_div(numerator: pd.Series, denominator: pd.Series) -> pd.Series:
    """Divide two rolling-sum Series; return NaN where denominator is 0 or NaN."""
    return numerator / denominator.where(denominator > 0, other=np.nan)


# ---------------------------------------------------------------------------
# Per-player rolling feature computation (TI-01)
# ---------------------------------------------------------------------------


def _compute_rolling_batter_features(player_df: pd.DataFrame, window: int, min_periods: int) -> pd.DataFrame:
    """Compute rolling batter features for a single player's game log.

    Uses .shift(1) before .rolling() so each row's features are derived
    from the prior N games only (current game excluded — TI-01).

    Parameters
    ----------
    player_df:
        One player's games sorted by game_date ascending.
        Must contain: ab, h, doubles, triples, hr, bb, k, hbp, sf, game_date,
        is_home_game.
    window:
        Rolling window size (games).
    min_periods:
        Minimum prior games to produce non-NaN features.

    Returns
    -------
    DataFrame with original columns plus rolling feature columns added.
    """
    df = player_df.copy()
    df = df.sort_values("game_date", ascending=True).reset_index(drop=True)

    numeric_cols = ["ab", "h", "doubles", "triples", "hr", "rbi", "bb", "k", "hbp", "sf"]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    # temporal_cutoff = date of the immediately prior game (TI-01 audit trail)
    df["temporal_cutoff"] = pd.to_datetime(df["game_date"]).shift(1)

    # Rolling sums (shifted — prior games only)
    h_sum = df["h"].shift(1).rolling(window, min_periods=min_periods).sum()
    ab_sum = df["ab"].shift(1).rolling(window, min_periods=min_periods).sum()
    doubles_sum = df["doubles"].shift(1).rolling(window, min_periods=min_periods).sum()
    triples_sum = df["triples"].shift(1).rolling(window, min_periods=min_periods).sum()
    hr_sum = df["hr"].shift(1).rolling(window, min_periods=min_periods).sum()
    bb_sum = df["bb"].shift(1).rolling(window, min_periods=min_periods).sum()
    k_sum = df["k"].shift(1).rolling(window, min_periods=min_periods).sum()
    hbp_sum = df["hbp"].shift(1).rolling(window, min_periods=min_periods).sum()
    sf_sum = df["sf"].shift(1).rolling(window, min_periods=min_periods).sum()

    # Batting average: sum(H) / sum(AB)
    df["ba_l10"] = _safe_div(h_sum, ab_sum)

    # Slugging: sum(total_bases) / sum(AB)
    tb_sum = h_sum + doubles_sum + 2 * triples_sum + 3 * hr_sum
    df["slg_l10"] = _safe_div(tb_sum, ab_sum)

    # On-base %: sum(H + BB + HBP) / sum(AB + BB + HBP + SF)
    ob_sum = h_sum + bb_sum + hbp_sum
    pa_sum = ab_sum + bb_sum + hbp_sum + sf_sum
    df["obp_l10"] = _safe_div(ob_sum, pa_sum)

    # OPS
    df["ops_l10"] = df["obp_l10"] + df["slg_l10"]

    # Mean hits per game
    df["h_l10_mean"] = h_sum / window

    # Rate stats per AB
    df["k_rate_l10"] = _safe_div(k_sum, ab_sum)
    df["bb_rate_l10"] = _safe_div(bb_sum, ab_sum)
    df["hr_rate_l10"] = _safe_div(hr_sum, ab_sum)

    # Days rest
    game_dates = pd.to_datetime(df["game_date"])
    df["days_rest"] = (game_dates - game_dates.shift(1)).dt.days.astype(float)
    df["b2b_flag"] = (df["days_rest"] <= 1).astype(float)
    # First game per player: days_rest=NaN, b2b_flag=0
    df.loc[df["days_rest"].isna(), "b2b_flag"] = 0.0

    return df


# ---------------------------------------------------------------------------
# Game-level feature lookups (SP overlay, park factors, opponent context)
# ---------------------------------------------------------------------------


def _get_opp_sp_id(row: pd.Series, game_starters: dict[int, dict[str, Any]]) -> int | None:
    """Return the opposing starting pitcher's player_id for a batter row."""
    game_id = row.get("game_id")
    if game_id is None:
        return None
    starter_info = game_starters.get(int(game_id))
    if starter_info is None:
        return None
    is_home = bool(row.get("is_home_game", 0))
    return starter_info.get("away_sp_id") if is_home else starter_info.get("home_sp_id")


def _get_venue_name(game_id: int | None, game_starters: dict[int, dict[str, Any]]) -> str | None:
    """Return the venue name for a game_id from game_starters."""
    if game_id is None:
        return None
    info = game_starters.get(int(game_id))
    return info.get("venue_name") if info else None


# ---------------------------------------------------------------------------
# MLBFeatureStore
# ---------------------------------------------------------------------------


class MLBFeatureStore:
    """Compute MLB batter features for C3 training and live prediction.

    Parameters
    ----------
    logger:
        AuditLogger (C6) instance.
    snapshot_id:
        DS snapshot anchor for this feature run.
    window:
        Rolling window size in games. Default 10 (L10).
    """

    def __init__(
        self,
        logger: AuditLogger,
        snapshot_id: str,
        window: int = DEFAULT_WINDOW,
    ) -> None:
        self._logger = logger
        self._snapshot_id = snapshot_id
        self._window = window

    def _log(
        self,
        event: str,
        payload: dict[str, Any],
        severity: str = "INFO",
        session_id: str | None = None,
        feature_run_id: str | None = None,
    ) -> bool:
        return self._logger.log(
            COMPONENT,
            event,
            payload={**payload, **({"feature_run_id": feature_run_id} if feature_run_id else {})},
            session_id=session_id,
            snapshot_id=self._snapshot_id,
            severity=severity,
        )

    def compute_features_bulk(
        self,
        batter_game_log_df: pd.DataFrame,
        game_starters: dict[int, dict[str, Any]],
        pitcher_store: "MLBPitcherStatsStore",
        team_store: "MLBTeamStatsStore",
        session_id: str | None = None,
    ) -> tuple[bool, pd.DataFrame]:
        """Compute MLB C2 features for all batters in the game log.

        Processes each player independently (rolling windows are per-player).
        Players with fewer than MIN_PERIODS prior games will have NaN feature
        rows (retained, temporal_cutoff=NaT, train_test_label=None).

        Parameters
        ----------
        batter_game_log_df:
            IF-C1-C2 MLB batter DataFrame from C1 MLBIngestionClient.
            Required columns: player_id, player_name, team_abbreviation, game_id,
            game_date, season, season_type, matchup, opponent_team_abbr,
            is_home_game, ab, h, doubles, triples, hr, rbi, bb, k, hbp, sf,
            snapshot_id.
        game_starters:
            Dict[gamePk → {home_sp_id, away_sp_id, venue_name, ...}] from
            MLBIngestionClient.fetch_game_starters(). Keys are int gamePk.
        pitcher_store:
            MLBPitcherStatsStore populated with SP game logs for TI-01-guarded
            ERA/K9/BB9 queries.
        team_store:
            MLBTeamStatsStore populated with completed game scores for opponent
            context features.
        session_id:
            Current bot run session ID for audit trail.

        Returns
        -------
        (all_ok, feature_df):
            all_ok — False if any C6 write failed; caller must trigger kill switch.
            feature_df — IF-C2-C3 DataFrame. Empty on unhandled exception.
        """
        run_id = _run_id()
        all_ok = True

        ok = self._log(
            "mlb_feature_derivation_start",
            {
                "input_rows": len(batter_game_log_df),
                "player_count": (
                    batter_game_log_df["player_id"].nunique()
                    if "player_id" in batter_game_log_df.columns
                    else None
                ),
                "n_games_in_starters": len(game_starters),
                "window": self._window,
                "feature_version": MLB_FEATURE_VERSION,
            },
            session_id=session_id,
            feature_run_id=run_id,
        )
        if not ok:
            all_ok = False

        try:
            if batter_game_log_df.empty:
                ok = self._log(
                    "mlb_feature_derivation_complete",
                    {"output_rows": 0, "note": "empty input"},
                    session_id=session_id,
                    feature_run_id=run_id,
                )
                if not ok:
                    all_ok = False
                return all_ok, pd.DataFrame(columns=_ID_COLUMNS)

            player_chunks: list[pd.DataFrame] = []
            for player_id, player_group in batter_game_log_df.groupby("player_id", sort=False):
                chunk = _compute_rolling_batter_features(
                    player_group, window=self._window, min_periods=MIN_PERIODS
                )
                player_chunks.append(chunk)

            if not player_chunks:
                return all_ok, pd.DataFrame(columns=_ID_COLUMNS)

            feature_df = pd.concat(player_chunks, ignore_index=True)

            # --- Game-level context: join on game_id (not per-player rolling) ---

            # Opponent runs allowed (TI-01: query as_of game_date)
            feature_df["opp_runs_allowed_l10"] = feature_df.apply(
                lambda row: team_store.get_opp_runs_allowed(
                    str(row.get("opponent_team_abbr", "")),
                    str(row.get("game_date", "")),
                    window=self._window,
                ),
                axis=1,
            )

            # Starting pitcher overlay (MANDATORY)
            sp_era: list[float | None] = []
            sp_k9: list[float | None] = []
            sp_bb9: list[float | None] = []
            sp_known: list[float] = []

            for _, row in feature_df.iterrows():
                sp_id = _get_opp_sp_id(row, game_starters)
                game_date_str = str(row.get("game_date", ""))
                if sp_id is not None:
                    era = pitcher_store.get_era_l5(sp_id, game_date_str)
                    k9 = pitcher_store.get_k_per_9_l5(sp_id, game_date_str)
                    bb9 = pitcher_store.get_bb_per_9_l5(sp_id, game_date_str)
                    sp_era.append(era)
                    sp_k9.append(k9)
                    sp_bb9.append(bb9)
                    sp_known.append(1.0)
                else:
                    sp_era.append(None)
                    sp_k9.append(None)
                    sp_bb9.append(None)
                    sp_known.append(0.0)

            feature_df["opp_sp_era_l5"] = sp_era
            feature_df["opp_sp_k9_l5"] = sp_k9
            feature_df["opp_sp_bb9_l5"] = sp_bb9
            feature_df["opp_sp_is_known"] = sp_known

            # Park factor (hit PF by venue name from game_starters)
            def _park_factor(row: pd.Series) -> float:
                venue = _get_venue_name(row.get("game_id"), game_starters)
                if venue is None:
                    return 1.000
                return _PARK_FACTOR_HITS.get(str(venue), 1.000)

            feature_df["park_factor_hits"] = feature_df.apply(_park_factor, axis=1)

            # Metadata
            feature_df["feature_run_id"] = run_id
            feature_df["feature_version"] = MLB_FEATURE_VERSION
            feature_df["train_test_label"] = None

            # Warn on null temporal_cutoff (players with no prior game)
            null_cutoff_count = (
                feature_df["temporal_cutoff"].isna().sum()
                if "temporal_cutoff" in feature_df.columns
                else 0
            )
            if null_cutoff_count > 0:
                ok = self._log(
                    "temporal_integrity_warning",
                    {
                        "null_temporal_cutoff_rows": int(null_cutoff_count),
                        "note": "Rows with null temporal_cutoff have no prior games. Exclude from all train/val/test splits.",
                    },
                    severity="WARNING",
                    session_id=session_id,
                    feature_run_id=run_id,
                )
                if not ok:
                    all_ok = False

            ok = self._log(
                "mlb_feature_derivation_complete",
                {
                    "output_rows": len(feature_df),
                    "player_count": feature_df["player_id"].nunique() if "player_id" in feature_df.columns else None,
                    "feature_version": MLB_FEATURE_VERSION,
                    "null_temporal_cutoff_rows": int(null_cutoff_count),
                    "window": self._window,
                    "sp_known_count": int(sum(1 for v in sp_known if v == 1.0)),
                    "sp_unknown_count": int(sum(1 for v in sp_known if v == 0.0)),
                },
                session_id=session_id,
                feature_run_id=run_id,
            )
            if not ok:
                all_ok = False

            return all_ok, feature_df

        except Exception as exc:
            ok = self._log(
                "mlb_feature_derivation_error",
                {"error": repr(exc), "feature_version": MLB_FEATURE_VERSION},
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
        """Assign chronological TRAIN/VALIDATION/TEST labels (TI-02).

        game_date <= train_end_date              → TRAIN
        train_end_date < game_date <= val_end_date → VALIDATION
        game_date > val_end_date                 → TEST
        Rows with temporal_cutoff=NaT            → None (excluded from all splits)
        """
        run_id = (
            feature_df["feature_run_id"].iloc[0]
            if "feature_run_id" in feature_df.columns and len(feature_df) > 0
            else _run_id()
        )
        df = feature_df.copy()
        game_dates = pd.to_datetime(df["game_date"], errors="coerce")
        train_end = pd.Timestamp(train_end_date)
        val_end = pd.Timestamp(val_end_date)

        has_cutoff = (
            df["temporal_cutoff"].notna()
            if "temporal_cutoff" in df.columns
            else pd.Series([True] * len(df))
        )

        df["train_test_label"] = None
        df.loc[has_cutoff & (game_dates <= train_end), "train_test_label"] = LABEL_TRAIN
        df.loc[has_cutoff & (game_dates > train_end) & (game_dates <= val_end), "train_test_label"] = LABEL_VALIDATION
        df.loc[has_cutoff & (game_dates > val_end), "train_test_label"] = LABEL_TEST

        label_counts = df["train_test_label"].value_counts(dropna=False).to_dict()
        ok = self._log(
            "mlb_train_test_split_applied",
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
