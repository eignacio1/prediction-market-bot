"""
C1/C2: Data Quality Contracts — Schema, Cardinality, and Freshness Manifest
============================================================================
Component:    C1 (Signal Ingestion) / C2 (Feature Store boundary)
Phase:        1 of 4 (T-212, GG-059)
Status:       ACTIVE (SESSION 107 2026-07-01)
Upstream:     MLB Stats API (via mlb_ingestion.py), scripts/generate_mlb_features.py
Downstream:   validators.py (structural checks), PIPE-05/PIPE-06pre (runtime gates)
ADR refs:     ADR-0034 (Layer 3 Semantic Contracts — sibling framework)
Policy refs:  03_DECISIONS/GOVERNANCE_GAP_LOG.md (GG-059)

Root cause this framework addresses
------------------------------------
GG-059: no declarative, checkable manifest exists for the shape MLB data is
expected to take at the C1 output boundary or the C2 feature CSV boundary.
Schema drift (a column silently renamed, dropped, or retyped upstream) and
cardinality drift (a row-count collapse or explosion) currently have no
structural detector — only the *semantic* floor (SemanticFloorGuard in
c7_monitoring/semantic_contracts.py) catches out-of-range values, and only
after the pipeline has already ingested malformed data.

This module owns the *manifest* — what a valid payload looks like, expressed
as typed Python data, not enforcement logic. validators.py owns enforcement.

Why Python, not YAML (GG-059 said "data_contracts.yaml")
-----------------------------------------------------------
See DECISION_LOG.md, SESSION 107 / T-212 entry, for the full rationale.
Summary: no YAML dependency exists in this project; mypy runs in strict mode
project-wide; the codebase already expresses constraint manifests as typed
Python (_HARD_LIMITS in risk.py, _MLB_BATTER_COLUMNS in mlb_ingestion.py).
A YAML manifest would be the only untyped, unchecked data-shape surface in
an otherwise fully-typed codebase. The declarative/auditable intent of
GG-059 is preserved; only the file format changed.

Contract taxonomy
------------------
FieldContract   — one column: name, dtype, nullable, min_value (numeric floor).
SourceContract  — one data source: field list, cardinality bounds, freshness
                   column + thresholds.

Structural vs. semantic — division of responsibility
--------------------------------------------------------
This module (and validators.py) checks STRUCTURE:
  - Are the expected columns present? Are unexpected columns absent?
  - Are values the right dtype and non-null where required?
  - Is row count within a sane multiple of the last known-good count?
  - Is the data fresh enough (freshness column within threshold)?

It does NOT check semantics (is a batting average plausible, is a computed
probability in [0,1]) — that is SemanticFloorGuard's job
(c7_monitoring/semantic_contracts.py). The two frameworks are deliberately
separate and compose: a payload can be structurally valid but semantically
implausible, or vice versa is not possible (semantic checks assume valid
structure).

Scope (Phase 1)
----------------
In scope:  C1 MLB Stats API batter/pitcher output (mlb_ingestion.py column
           lists), C2 feature CSV (scripts/generate_mlb_features.py output,
           consumed by PIPE-05/PIPE-06pre).
Out of scope (Phase 1): Kalshi (C5) market data, ESPN (T4-only) live state.
Deferred to Phases 2-4: contract versioning, automatic drift alerting to
C8, contracts for additional sports.
"""

from __future__ import annotations

from dataclasses import dataclass

from prediction_market_bot.c1_signal_ingestion.mlb_ingestion import (
    _MLB_BATTER_COLUMNS,
    _MLB_PITCHER_COLUMNS,
)


@dataclass(frozen=True)
class FieldContract:
    """Structural contract for a single column.

    dtype is one of {"int", "float", "str", "bool"} — a coarse type family,
    not a pandas/numpy dtype string, since CSV round-tripping and JSON
    normalization make exact dtype matching brittle across the pipeline.
    """

    name: str
    dtype: str
    nullable: bool = False
    min_value: float | None = None


@dataclass(frozen=True)
class SourceContract:
    """Structural contract for one data source (a DataFrame or CSV)."""

    source_id: str
    fields: tuple[FieldContract, ...]
    min_rows: int = 1
    max_row_growth_ratio: float = 3.0
    freshness_column: str | None = None
    freshness_warn_days: int | None = None
    freshness_halt_days: int | None = None

    def field_names(self) -> tuple[str, ...]:
        return tuple(f.name for f in self.fields)


def _counting_stat_fields(names: list[str]) -> list[FieldContract]:
    """Non-negative integer counting stats (ab, h, hr, k, ip, etc.)."""
    return [FieldContract(name=n, dtype="int", nullable=False, min_value=0.0) for n in names]


_MLB_BATTER_COUNTING_COLUMNS = {
    "ab", "h", "doubles", "triples", "hr", "rbi", "bb", "k", "hbp", "sf",
}
_MLB_PITCHER_COUNTING_COLUMNS = {
    "h_allowed", "er", "bb", "k", "hr_allowed",
}
_MLB_ID_COLUMNS = {"player_id", "team_id", "game_id"}


def _field_for_batter_column(col: str) -> FieldContract:
    if col in _MLB_BATTER_COUNTING_COLUMNS:
        return FieldContract(name=col, dtype="int", nullable=False, min_value=0.0)
    if col in _MLB_ID_COLUMNS:
        return FieldContract(name=col, dtype="int", nullable=False, min_value=0.0)
    if col == "is_home_game":
        return FieldContract(name=col, dtype="bool", nullable=False)
    return FieldContract(name=col, dtype="str", nullable=False)


def _field_for_pitcher_column(col: str) -> FieldContract:
    if col in _MLB_PITCHER_COUNTING_COLUMNS:
        return FieldContract(name=col, dtype="int", nullable=False, min_value=0.0)
    if col == "ip":
        return FieldContract(name=col, dtype="float", nullable=False, min_value=0.0)
    if col in _MLB_ID_COLUMNS:
        return FieldContract(name=col, dtype="int", nullable=False, min_value=0.0)
    if col == "is_home_game" or col == "is_start":
        return FieldContract(name=col, dtype="bool", nullable=False)
    return FieldContract(name=col, dtype="str", nullable=False)


# IF-C1-C2 MLB batter game log contract — mirrors _MLB_BATTER_COLUMNS exactly.
# Imported (not hand-duplicated) so schema drift at the C1 source is caught
# by this contract automatically rather than relying on two lists staying
# in sync by convention.
MLB_BATTER_CONTRACT = SourceContract(
    source_id="mlb_batter_gamelog",
    fields=tuple(_field_for_batter_column(c) for c in _MLB_BATTER_COLUMNS),
    min_rows=1,
    max_row_growth_ratio=3.0,
)

# IF-C1-C2 MLB pitcher game log contract — mirrors _MLB_PITCHER_COLUMNS exactly.
MLB_PITCHER_CONTRACT = SourceContract(
    source_id="mlb_pitcher_gamelog",
    fields=tuple(_field_for_pitcher_column(c) for c in _MLB_PITCHER_COLUMNS),
    min_rows=1,
    max_row_growth_ratio=3.0,
)

# C2 feature CSV contract — the 44-column output of scripts/generate_mlb_features.py,
# consumed at runtime by PIPE-05 (run_mlb_paper_trade.py) and PIPE-06pre
# (run_mlb_pregame.py). Freshness thresholds mirror the values already used
# ad hoc (T-193) in both consumers before this contract replaced them.
_MLB_FEATURE_CSV_COLUMNS: list[str] = [
    "player_id", "player_name", "team_id", "team_abbreviation", "game_id",
    "game_date", "season", "season_type", "matchup", "is_home_game",
    "opponent_team_abbr", "ab", "h", "doubles", "triples", "hr", "rbi", "bb",
    "k", "hbp", "sf", "snapshot_id", "ingestion_run_id", "ingested_at",
    "temporal_cutoff", "ba_l10", "slg_l10", "obp_l10", "ops_l10",
    "h_l10_mean", "k_rate_l10", "bb_rate_l10", "hr_rate_l10", "days_rest",
    "b2b_flag", "opp_runs_allowed_l10", "opp_sp_era_l5", "opp_sp_k9_l5",
    "opp_sp_bb9_l5", "opp_sp_is_known", "park_factor_hits", "feature_run_id",
    "feature_version", "train_test_label",
]

_MLB_FEATURE_CSV_RATE_FIELDS = {
    "ba_l10", "slg_l10", "obp_l10", "ops_l10", "h_l10_mean", "k_rate_l10",
    "bb_rate_l10", "hr_rate_l10", "opp_runs_allowed_l10", "opp_sp_era_l5",
    "opp_sp_k9_l5", "opp_sp_bb9_l5", "park_factor_hits",
}
_MLB_FEATURE_CSV_INT_FIELDS = {
    "player_id", "team_id", "game_id", "ab", "h", "doubles", "triples",
    "hr", "rbi", "bb", "k", "hbp", "sf", "days_rest",
}
_MLB_FEATURE_CSV_BOOL_FIELDS = {"is_home_game", "b2b_flag", "opp_sp_is_known"}
# Feature engineering columns are permitted to be null for players with an
# incomplete rolling window (e.g. early-season, few prior games) — this is
# expected data sparsity, not a structural defect.
#
# days_rest and train_test_label are also expected-null by design, not sparsity:
# mlb_features.py:225-228 sets days_rest=NaN for a player's first game in the
# dataset (no prior game to diff against); mlb_features.py:315/features.py:802
# set train_test_label=None for "retained" rows with no temporal_cutoff (TI-02
# excluded from train/val/test splits). Both were omitted here at T-212
# (SESSION 107) build time and went undetected because unit-test fixtures
# always populated every row — production data hit the real edge case first
# on 2026-07-02, HALTing PIPE-06pre and blocking that day's pregame context
# generation (see DECISION_LOG SESSION 111 entry).
_MLB_FEATURE_CSV_NULLABLE = _MLB_FEATURE_CSV_RATE_FIELDS | {
    "opp_sp_era_l5", "opp_sp_k9_l5", "opp_sp_bb9_l5",
    "days_rest", "train_test_label",
}


def _field_for_feature_csv_column(col: str) -> FieldContract:
    nullable = col in _MLB_FEATURE_CSV_NULLABLE
    if col in _MLB_FEATURE_CSV_RATE_FIELDS:
        return FieldContract(name=col, dtype="float", nullable=nullable, min_value=0.0)
    if col in _MLB_FEATURE_CSV_INT_FIELDS:
        return FieldContract(name=col, dtype="int", nullable=nullable, min_value=0.0)
    if col in _MLB_FEATURE_CSV_BOOL_FIELDS:
        return FieldContract(name=col, dtype="bool", nullable=nullable)
    return FieldContract(name=col, dtype="str", nullable=nullable)


MLB_FEATURE_CSV_CONTRACT = SourceContract(
    source_id="mlb_feature_csv",
    fields=tuple(_field_for_feature_csv_column(c) for c in _MLB_FEATURE_CSV_COLUMNS),
    min_rows=1,
    max_row_growth_ratio=3.0,
    freshness_column="game_date",
    freshness_warn_days=3,
    freshness_halt_days=7,
)
