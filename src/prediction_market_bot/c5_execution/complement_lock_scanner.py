"""
C5: Complement Lock Scanner
============================
Module:   c5_execution.complement_lock_scanner
Phase:    Phase 7 (Strategy C — cross-venue complement lock arbitrage)
Purpose:  Detect cross-venue complement lock conditions in a merged
          multi-venue market snapshot.

Complement lock condition:
  ask_YES (best venue A) + ask_NO (best venue B) < $1.00 - 2 × fee

This scanner DETECTS opportunities and logs them. It does NOT place orders.
Execution requires:
  - APR-0010 signed by DS (arb/ module governance gate)
  - C5 upgraded to write-capable mode (new API key)
  - Two-leg simultaneous order infrastructure in C5

Governance invariant (ANTI-CONTEXT-EROSION #1):
  arb/ folder = REFERENCE ONLY until APR-0010 is signed.
  All detected opportunities are logged to C6 only.
  See STRATEGY_OVERVIEW.md Strategy C and REJECTED_OPTIONS.md RO-001.

Same-venue locks:
  Kalshi alone can exhibit ask_YES + ask_NO < $1.00 transiently after
  large orders move one side. These are detected when require_cross_venue=False.
  Default: True — focus on cross-venue opportunities where vig differentials
  create more durable windows.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

from prediction_market_bot.c5_execution.kalshi_client import PlayerMarket
from prediction_market_bot.c5_execution.market_mapper import (
    PlayerMarketKey,
    group_by_key,
    normalize_player_name,
)


# ---------------------------------------------------------------------------
# Data class
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class LockOpportunity:
    """
    A detected complement lock opportunity across two venues.

    The lock condition holds when:
      ask_yes + ask_no < 1.00 - 2 * fee_per_contract

    Buying YES on yes_venue and NO on no_venue guarantees $1.00 at settlement
    regardless of outcome, at a total cost of ask_yes + ask_no + fees < $1.00.
    """
    player_name: str          # Normalized canonical name
    threshold: int
    yes_venue: str            # Venue with the lowest ask_YES
    no_venue: str             # Venue with the lowest ask_NO
    ask_yes: float
    ask_no: float
    gross_profit: float       # 1.00 - ask_yes - ask_no (before fees)
    estimated_fee: float      # 2 × fee_per_contract (both legs)
    net_profit: float         # gross_profit - estimated_fee
    detected_at: str          # UTC ISO timestamp

    @property
    def is_cross_venue(self) -> bool:
        """True when the two legs are on different venues."""
        return self.yes_venue != self.no_venue


# ---------------------------------------------------------------------------
# Scanner
# ---------------------------------------------------------------------------

# EXP-010 confirmed Kalshi vig = 0.030 per contract.
# Used as the default fee estimate for all venues until venue-specific data.
DEFAULT_FEE_PER_CONTRACT: float = 0.030

# Minimum net profit after fees to include in output.
# 0.001 excludes marginal opportunities that noise could eliminate at fill time.
MIN_NET_PROFIT: float = 0.001


class ComplementLockScanner:
    """
    Scans a merged multi-venue market snapshot for complement lock conditions.

    Usage::

        scanner = ComplementLockScanner()
        all_markets = router.fetch_all_markets()[1].markets  # all venues merged
        opportunities = scanner.scan_snapshot(all_markets)

        for opp in opportunities:
            logger.info("PIPE-02", "lock_detected", payload={
                "player": opp.player_name,
                "threshold": opp.threshold,
                "yes_venue": opp.yes_venue,
                "no_venue": opp.no_venue,
                "net_profit": opp.net_profit,
                "governance": "detection_only_APR-0010_required",
            })

    Governance:
        Output is DETECTION ONLY. APR-0010 required before any execution.
        Log all detected opportunities to C6 for retrospective analysis.
    """

    def __init__(
        self,
        fee_per_contract: float = DEFAULT_FEE_PER_CONTRACT,
        min_net_profit: float = MIN_NET_PROFIT,
        require_cross_venue: bool = True,
    ) -> None:
        """
        Parameters
        ----------
        fee_per_contract:
            Estimated cost per contract per venue. Total two-leg cost = 2×.
            Defaults to Kalshi's confirmed vig of 0.030 (EXP-010).
        min_net_profit:
            Minimum net profit (after fees) to include in results.
        require_cross_venue:
            If True (default), only report opportunities where YES and NO
            are on different venues. Set to False to also detect same-venue
            transient lock windows (rare; usually stale quotes).
        """
        self._fee = fee_per_contract
        self._min_net = min_net_profit
        self._require_cross_venue = require_cross_venue

    def scan_snapshot(
        self, markets: list[PlayerMarket]
    ) -> list[LockOpportunity]:
        """
        Scan a merged multi-venue snapshot for lock conditions.

        Groups markets by (normalized_player_name, threshold) using
        market_mapper.group_by_key(). For each group, finds the best
        YES ask and best NO ask across all venues and evaluates the
        lock condition.

        Returns
        -------
        list[LockOpportunity]
            Detected opportunities sorted by net_profit descending.
            Empty list when no profitable lock exists.
        """
        opportunities: list[LockOpportunity] = []
        groups = group_by_key(markets)

        for key, group_markets in groups.items():
            opp = self._evaluate_group(key, group_markets)
            if opp is not None:
                opportunities.append(opp)

        return sorted(opportunities, key=lambda o: o.net_profit, reverse=True)

    def scan_single(
        self,
        player_name_fragment: str,
        threshold: int,
        markets: list[PlayerMarket],
    ) -> Optional[LockOpportunity]:
        """
        Scan for a lock on a specific player/threshold combination.

        Useful for targeted checks during PIPE-06 T3 momentum scan:
        after identifying a player with an interesting T1 forecast,
        check if a lock exists before deciding which direction to trade.

        Parameters
        ----------
        player_name_fragment:
            Case-insensitive substring matched against player_name.
        threshold:
            Exact integer threshold to match.
        markets:
            Flat list of PlayerMarket from all venues.
        """
        frag = player_name_fragment.upper()
        relevant = [
            m for m in markets
            if frag in m.player_name.upper() and m.threshold == threshold
        ]
        if not relevant:
            return None
        key = PlayerMarketKey(
            normalized_name=normalize_player_name(relevant[0].player_name),
            threshold=threshold,
        )
        return self._evaluate_group(key, relevant)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _evaluate_group(
        self,
        key: PlayerMarketKey,
        group: list[PlayerMarket],
    ) -> Optional[LockOpportunity]:
        """
        Evaluate a single (player, threshold) group for lock condition.

        Returns LockOpportunity if the net profit meets the threshold,
        None otherwise.
        """
        if not group:
            return None

        best_yes_market = min(group, key=lambda m: m.yes_ask)
        best_no_market  = min(group, key=lambda m: m.no_ask)

        if self._require_cross_venue and (
            best_yes_market.venue == best_no_market.venue
        ):
            return None

        ask_yes     = best_yes_market.yes_ask
        ask_no      = best_no_market.no_ask
        gross       = round(1.00 - ask_yes - ask_no, 6)
        fee         = round(2 * self._fee, 6)
        net         = round(gross - fee, 6)

        if net < self._min_net:
            return None

        return LockOpportunity(
            player_name=key.normalized_name,
            threshold=key.threshold,
            yes_venue=best_yes_market.venue,
            no_venue=best_no_market.venue,
            ask_yes=round(ask_yes, 4),
            ask_no=round(ask_no, 4),
            gross_profit=gross,
            estimated_fee=fee,
            net_profit=net,
            detected_at=_utc_now(),
        )


def _utc_now() -> str:
    return datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
