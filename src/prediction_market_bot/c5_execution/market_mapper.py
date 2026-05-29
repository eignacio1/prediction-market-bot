"""
C5: Cross-Venue Player Market Normalizer
=========================================
Module:   c5_execution.market_mapper
Phase:    Phase 7 (cross-venue routing active)
Purpose:  Normalize player names and market identifiers across prediction
          market venues. Enables reliable deduplication and lock detection
          when the same contract (player + threshold) appears on multiple
          venues with different display name formats.

Cross-venue mapping rules:
  1. Canonical name: NFKD-normalized, lowercase, strip apostrophes/periods
  2. PlayerMarketKey = (canonical_name, threshold) — stable across venues
  3. group_by_key() buckets a flat multi-venue list for lock scanning and
     best-price deduplication by the VenueRouter

Example normalizations:
  "Shai Gilgeous-Alexander"  → "shai gilgeous-alexander"
  "LeBron James"              → "lebron james"
  "A.J. Green"                → "aj green"
  "De'Aaron Fox"              → "deaaron fox"
  "Luka Doncic"               → "luka doncic"
  "Luka Dončić"               → "luka doncic"
"""

from __future__ import annotations

import re
import unicodedata
from typing import NamedTuple

from prediction_market_bot.c5_execution.kalshi_client import PlayerMarket


class PlayerMarketKey(NamedTuple):
    """
    Venue-independent identity for a player/threshold market.

    Two PlayerMarket objects from different venues with the same
    PlayerMarketKey represent the same underlying contract and can be
    compared for best-price selection or lock condition detection.
    """
    normalized_name: str
    threshold: int


def normalize_player_name(name: str) -> str:
    """
    Return the canonical player name for cross-venue deduplication.

    Rules applied in order:
      1. NFKD normalize → strip accent combining characters (Dončić → Doncic)
      2. Lowercase
      3. Remove apostrophes, periods, and parentheses
      4. Collapse consecutive whitespace to a single space
      5. Strip leading/trailing whitespace
    """
    nfkd = unicodedata.normalize("NFKD", name)
    ascii_name = "".join(c for c in nfkd if not unicodedata.combining(c))
    lower = ascii_name.lower()
    cleaned = re.sub(r"['.()]", "", lower)
    collapsed = re.sub(r"\s+", " ", cleaned)
    return collapsed.strip()


def market_key(market: PlayerMarket) -> PlayerMarketKey:
    """Return the venue-independent identity key for a PlayerMarket."""
    return PlayerMarketKey(
        normalized_name=normalize_player_name(market.player_name),
        threshold=market.threshold,
    )


def group_by_key(
    markets: list[PlayerMarket],
) -> dict[PlayerMarketKey, list[PlayerMarket]]:
    """
    Group a flat list of PlayerMarket objects by (normalized_name, threshold).

    Returns {PlayerMarketKey: [market_venue_A, market_venue_B, ...]}.
    Any key with len > 1 represents a cross-venue overlap for the same contract.

    Used by:
      - VenueRouter._deduplicate_best_price() for best-price selection
      - ComplementLockScanner.scan_snapshot() for lock detection
    """
    groups: dict[PlayerMarketKey, list[PlayerMarket]] = {}
    for m in markets:
        key = market_key(m)
        if key not in groups:
            groups[key] = []
        groups[key].append(m)
    return groups
