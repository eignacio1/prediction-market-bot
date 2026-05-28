# C2: Feature Store
# Phase active: Phase 3+
# Maintains temporally-safe feature sets for model training and inference.
# INVARIANT: temporal_cutoff field is REQUIRED on every feature record.
# INVARIANT: Outcome data (DS-03) NEVER enters this component (TI-03).
# See: DATA_FLOWS_LINEAGE.md TI-01 through TI-04, INTERFACES_CONTRACTS.md IF-C1-C2

from prediction_market_bot.c2_feature_store.features import FeatureStore

__all__ = ["FeatureStore"]
