# C1: Signal Ingestion
# Phase active: Phase 3+
# Ingests DS-01 snapshots (Phase 3) and DS-02 live feed (Phase 6+)
# See: ARCHITECTURE_OVERVIEW.md, INTERFACES_CONTRACTS.md IF-C1-C2
# CRITICAL: All data entering C1 must have temporal_cutoff set.
# CRITICAL: Outcome data (DS-03) must NEVER enter this component — separate path only.

from prediction_market_bot.c1_signal_ingestion.ingestion import NBAIngestionClient
from prediction_market_bot.c1_signal_ingestion.mlb_ingestion import MLBIngestionClient
from prediction_market_bot.c1_signal_ingestion.mlb_team_stats_store import MLBTeamStatsStore
from prediction_market_bot.c1_signal_ingestion.mlb_pitcher_stats_store import MLBPitcherStatsStore

__all__ = [
    "NBAIngestionClient",
    "MLBIngestionClient",
    "MLBTeamStatsStore",
    "MLBPitcherStatsStore",
]
