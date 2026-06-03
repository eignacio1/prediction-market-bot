"""
C5 Sub-module: Paper Trader — Order Execution + Local Ledger (PIPE-03)
=======================================================================
Component:    C5 (Execution Engine) — paper trading sub-module
Phase active: Phase 6 (paper trading; ENV-02 only)
Status:       UPDATED — 2026-05-31 (ADR-0008: Kalshi demo order submission added)
Gate:         BOT_ENV=paper required

Responsibility:
  Submit C4-approved bets to Kalshi demo AND record them locally.
  Local paper_portfolio.json is the authoritative G6 evidence ledger.
  Kalshi demo orders are the live execution confirmation.

Order submission (ADR-0008):
  If KalshiMarketClient is provided with a loaded RSA private key, every
  open_position() call submits a real order to Kalshi demo. The Kalshi
  order_id and status are recorded in the position. If Kalshi submission
  fails, the position is still recorded locally (degraded mode) and a
  warning is logged. Local ledger is always authoritative for G6 P&L.

Portfolio state:
  Persisted to logs/paper_portfolio.json after every operation.
  Immutable history: closed_positions are never modified after resolution.

Outcome resolution:
  For any open position where game_date < today: fetch the player's
  actual points from nba_api and compare to the Kalshi bet threshold.
  YES wins if actual_pts >= threshold; NO wins if actual_pts < threshold.
  Bankroll updated accordingly.

Kill switch:
  All public methods return (bool, ...). False = C6 write failure → halt.
  Kalshi submission failure does NOT trigger kill switch — degraded mode only.
"""

from __future__ import annotations

import json
import threading
import time
import uuid
from datetime import datetime, date, timezone
from pathlib import Path
from typing import TYPE_CHECKING, Any, Optional

import pandas as pd

from prediction_market_bot.c6_audit_logger.audit_logger import AuditLogger

if TYPE_CHECKING:
    from prediction_market_bot.c5_execution.kalshi_client import KalshiMarketClient

COMPONENT = "C5-PAPER"

INITIAL_BANKROLL_USD: float = 1000.00


def _utc_now() -> str:
    return datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"

def _today() -> str:
    return date.today().isoformat()


class PaperTrader:
    """
    Paper trading execution engine — records and tracks simulated bets.

    Usage::

        trader = PaperTrader(
            portfolio_path=Path("logs/paper_portfolio.json"),
            logger=audit_logger,
        )

        # After C4 approves a forecast:
        ok, pos = trader.open_position(
            approval=c4_decision,
            player_name="SGA",
            player_id=1628983,
            kalshi_ticker="KXNBAPTS-...",
            kalshi_threshold=30,
            mid_price=0.280,
            vig=0.040,
            game_date="2026-05-29",
            session_id=session_id,
        )

        # Next day — resolve previous positions:
        ok, resolved = trader.resolve_pending(session_id=session_id)
    """

    def __init__(
        self,
        portfolio_path: Path,
        logger: AuditLogger,
        kalshi_client: Optional["KalshiMarketClient"] = None,
    ) -> None:
        self._path = portfolio_path
        self._logger = logger
        self._kalshi = kalshi_client  # None → local-only mode
        self._lock = threading.Lock()
        self._state = self._load_or_init()

    # ------------------------------------------------------------------
    # State management
    # ------------------------------------------------------------------

    def _load_or_init(self) -> dict[str, Any]:
        if self._path.exists():
            try:
                return json.loads(self._path.read_text())
            except Exception:
                pass
        return {
            "bankroll_usd": INITIAL_BANKROLL_USD,
            "initial_bankroll_usd": INITIAL_BANKROLL_USD,
            "total_realized_pnl": 0.0,
            "current_daily_loss": 0.0,
            "daily_loss_date": _today(),
            "open_positions": [],
            "closed_positions": [],
            "created_at": _utc_now(),
            "last_updated": _utc_now(),
        }

    def _save(self) -> bool:
        try:
            self._path.parent.mkdir(parents=True, exist_ok=True)
            self._state["last_updated"] = _utc_now()
            self._path.write_text(json.dumps(self._state, indent=2))
            return True
        except OSError:
            return False

    def _reset_daily_loss_if_new_day(self) -> None:
        today = _today()
        if self._state.get("daily_loss_date") != today:
            self._state["current_daily_loss"] = 0.0
            self._state["daily_loss_date"] = today

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_state(self) -> dict[str, Any]:
        """Return current portfolio state (copy — not live reference)."""
        with self._lock:
            return dict(self._state)

    def open_position(
        self,
        approval: dict[str, Any],
        player_name: str,
        player_id: int,
        kalshi_ticker: str,
        kalshi_threshold: int,
        mid_price: float,
        vig: float,
        game_date: str,
        session_id: str | None = None,
        pool_isolated: bool = False,
    ) -> tuple[bool, dict[str, Any]]:
        """
        Record a C4-approved paper bet.

        Deducts the approved size from the paper bankroll unless pool_isolated=True,
        in which case the position is recorded but the main bankroll is not touched.
        Used for T4 flat-sizing paper mode where T4 tracks its own pool independently
        (PAPER_T4_FLAT_SIZING=True) so T1 and T4 do not compete for the same bankroll.
        Logs to C6. Returns (ok, position_record).
        """
        with self._lock:
            self._reset_daily_loss_if_new_day()

            size    = float(approval.get("approved_size", 0.0))
            direction = str(approval.get("approved_direction", "PASS"))
            risk_id   = str(approval.get("risk_eval_id", ""))
            forecast_id = str(approval.get("forecast_id", ""))

            if size <= 0 or direction == "PASS":
                return True, {}

            entry_cost = size  # cost = size (we pay mid_price per $1 contract)

            model_p    = float(approval.get("model_p", 0.0))
            gross_edge = float(approval.get("edge", 0.0))
            fee_per_contract = round(0.07 * mid_price * (1.0 - mid_price), 6)
            fee_net_edge = round(gross_edge - fee_per_contract, 6)
            probable_injury_signal = bool(model_p > 0.0 and abs(model_p - mid_price) > 0.25)

            if pool_isolated:
                # T4 flat-sizing mode: position recorded; main bankroll unchanged.
                # T4 tracks its own pool via t4_deployed_usd in run_t4_live.py.
                pass
            else:
                # Deduct from bankroll
                if entry_cost > self._state["bankroll_usd"]:
                    ok = self._logger.warning(
                        COMPONENT, "insufficient_bankroll",
                        payload={"required": entry_cost, "available": self._state["bankroll_usd"]},
                        session_id=session_id,
                    )
                    return ok, {}
                self._state["bankroll_usd"] = round(self._state["bankroll_usd"] - entry_cost, 4)

            pos = {
                "position_id": f"POS-{uuid.uuid4().hex[:10].upper()}",
                "player_name": player_name,
                "player_id": player_id,
                "kalshi_ticker": kalshi_ticker,
                "kalshi_threshold": kalshi_threshold,
                "direction": direction,
                "mid_price_at_entry": round(mid_price, 4),
                "vig_at_entry": round(vig, 4),
                "size_usd": round(size, 4),
                "game_date": game_date,
                "entered_at": _utc_now(),
                "risk_eval_id": risk_id,
                "forecast_id": forecast_id,
                "status": "OPEN",
                "kalshi_order_id": None,
                "kalshi_order_status": "local_only",
                "kalshi_contracts": None,
                "model_p": round(model_p, 6),
                "gross_edge": round(gross_edge, 6),
                "fee_per_contract": fee_per_contract,
                "fee_net_edge": fee_net_edge,
                "fee_contaminated": bool(fee_net_edge < 0.0),
                "probable_injury_signal": probable_injury_signal,
            }

            # Submit to Kalshi demo if client is available (ADR-0008)
            if self._kalshi and self._kalshi.has_signing_key() and kalshi_ticker:
                side = direction.lower()  # "yes" or "no"
                order = self._kalshi.submit_order(
                    ticker=kalshi_ticker,
                    side=side,
                    size_usd=size,
                    mid_price=mid_price,
                    client_order_id=pos["position_id"],
                )
                if order.ok:
                    pos["kalshi_order_id"] = order.order_id
                    pos["kalshi_order_status"] = order.status
                    pos["kalshi_contracts"] = order.contracts
                else:
                    pos["kalshi_order_status"] = f"failed: {order.error}"
                    self._logger.warning(
                        COMPONENT, "kalshi_order_failed",
                        payload={
                            "position_id": pos["position_id"],
                            "ticker": kalshi_ticker,
                            "error": order.error,
                            "note": "local position recorded; Kalshi order not placed",
                        },
                        session_id=session_id,
                    )

            self._state["open_positions"].append(pos)

            ok_save = self._save()
            ok_log  = self._logger.info(
                COMPONENT, "paper_order_opened",
                payload={
                    "position_id": pos["position_id"],
                    "player_name": player_name,
                    "direction": direction,
                    "size_usd": size,
                    "mid_price": mid_price,
                    "kalshi_threshold": kalshi_threshold,
                    "bankroll_after": self._state["bankroll_usd"],
                    "game_date": game_date,
                    "kalshi_order_id": pos["kalshi_order_id"],
                    "kalshi_order_status": pos["kalshi_order_status"],
                    "kalshi_contracts": pos["kalshi_contracts"],
                },
                session_id=session_id,
            )
            return (ok_save and ok_log), pos

    def resolve_pending(
        self,
        session_id: str | None = None,
    ) -> tuple[bool, list[dict]]:
        """
        Resolve all open positions where game_date < today using nba_api.

        Returns (ok, list_of_resolved_positions).
        Logs each resolution to C6.

        Note: stats.nba.com blocks datacenter IPs (403). If running from a
        cloud server, this method will log a warning and return no resolved
        positions. Use run_resolve_local.py to resolve from a non-blocked IP.
        """
        today = _today()
        with self._lock:
            pending = [
                p for p in self._state["open_positions"]
                if p.get("game_date", today) < today
            ]

        if not pending:
            return True, []

        try:
            from nba_api.stats.endpoints import PlayerGameLog
        except ImportError:
            ok = self._logger.warning(
                COMPONENT, "nba_api_not_available",
                payload={"note": "Cannot resolve positions — nba_api not installed"},
                session_id=session_id,
            )
            return ok, []

        resolved = []
        all_ok = True

        for pos in pending:
            player_id   = pos["player_id"]
            game_date   = pos["game_date"]  # YYYY-MM-DD
            threshold   = pos["kalshi_threshold"]
            direction   = pos["direction"]
            size        = pos["size_usd"]
            mid         = pos["mid_price_at_entry"]

            # Determine season from game_date (nba_api format: "YYYY-YY")
            year = int(game_date[:4])
            month = int(game_date[5:7])
            season_start_year = year if month >= 10 else year - 1
            season = f"{season_start_year}-{str(season_start_year + 1)[-2:]}"

            actual_pts = None
            try:
                time.sleep(0.6)  # rate limit
                log = PlayerGameLog(player_id=player_id, season=season,
                                    season_type_all_star="Regular Season")
                df = log.get_data_frames()[0]
                df["GAME_DATE"] = pd.to_datetime(df["GAME_DATE"], format="mixed").dt.strftime("%Y-%m-%d")
                row = df[df["GAME_DATE"] == game_date]
                if not row.empty:
                    actual_pts = float(row.iloc[0]["PTS"])
            except Exception as e:
                self._logger.warning(
                    COMPONENT, "player_stats_fetch_failed",
                    payload={"player_id": player_id, "game_date": game_date,
                             "season": season, "season_type": "Regular Season",
                             "error": str(e)},
                    session_id=session_id,
                )

            # Always try Playoffs if Regular Season had no result (playoff games return
            # empty rows from Regular Season endpoint without throwing)
            if actual_pts is None:
                try:
                    time.sleep(0.6)
                    log = PlayerGameLog(player_id=player_id, season=season,
                                        season_type_all_star="Playoffs")
                    df = log.get_data_frames()[0]
                    df["GAME_DATE"] = pd.to_datetime(df["GAME_DATE"], format="mixed").dt.strftime("%Y-%m-%d")
                    row = df[df["GAME_DATE"] == game_date]
                    if not row.empty:
                        actual_pts = float(row.iloc[0]["PTS"])
                except Exception as e:
                    self._logger.warning(
                        COMPONENT, "player_stats_fetch_failed",
                        payload={"player_id": player_id, "game_date": game_date,
                                 "season": season, "season_type": "Playoffs",
                                 "error": str(e)},
                        session_id=session_id,
                    )

            if actual_pts is None:
                continue  # Game not found yet — try again tomorrow

            # Determine outcome
            yes_won = actual_pts >= threshold
            if direction == "YES":
                won = yes_won
                # Payout: win $1 - ask price; lose stake
                yes_ask = mid + pos["vig_at_entry"] / 2
                pnl = size * (1.0 - yes_ask) / yes_ask if won else -size
            else:  # direction == "NO"
                won = not yes_won
                no_ask = (1.0 - mid) + pos["vig_at_entry"] / 2
                pnl = size * (1.0 - no_ask) / no_ask if won else -size

            pnl = round(pnl, 4)
            outcome = "WIN" if won else "LOSS"

            with self._lock:
                # Remove from open, add to closed
                self._state["open_positions"] = [
                    p for p in self._state["open_positions"]
                    if p["position_id"] != pos["position_id"]
                ]
                closed_pos = {**pos, "actual_pts": actual_pts, "outcome": outcome,
                              "pnl": pnl, "resolved_at": _utc_now(), "status": "CLOSED"}
                self._state["closed_positions"].append(closed_pos)
                self._state["bankroll_usd"] = round(self._state["bankroll_usd"] + size + pnl, 4)
                self._state["total_realized_pnl"] = round(
                    self._state["total_realized_pnl"] + pnl, 4)
                if pnl < 0:
                    self._state["current_daily_loss"] = round(
                        self._state["current_daily_loss"] + abs(pnl), 4)
                self._save()

            ok = self._logger.info(
                COMPONENT, "paper_position_resolved",
                payload={
                    "position_id": pos["position_id"],
                    "player_name": pos["player_name"],
                    "direction": direction,
                    "threshold": threshold,
                    "actual_pts": actual_pts,
                    "outcome": outcome,
                    "pnl": pnl,
                    "bankroll_after": self._state["bankroll_usd"],
                },
                session_id=session_id,
            )
            if not ok:
                all_ok = False
            resolved.append(closed_pos)

        return all_ok, resolved

    def summary(self) -> dict[str, Any]:
        """Return a human-readable portfolio summary.

        Two distinct capital metrics:
          realized_drawdown_pct — closed losses as % of initial bankroll.
              This is what C4's kill switch monitors. Zero until a bet resolves.
          deployed_pct — open stakes as % of initial bankroll.
              Money in flight; returns to bankroll when positions resolve.
              NOT a drawdown — it is not permanently lost.
        """
        s = self._state
        n_open   = len(s.get("open_positions", []))
        n_closed = len(s.get("closed_positions", []))
        wins     = sum(1 for p in s.get("closed_positions", []) if p.get("outcome") == "WIN")
        win_rate = wins / n_closed if n_closed > 0 else None

        initial      = s["initial_bankroll_usd"]
        realized_pnl = s.get("total_realized_pnl", 0.0)
        realized_loss = max(0.0, -realized_pnl)
        realized_drawdown = realized_loss / initial

        # Stakes in open positions = initial - current_bankroll - realized_pnl
        # (realized gains would have already been added back to bankroll)
        open_stakes  = initial - s["bankroll_usd"] + realized_pnl
        deployed_pct = max(0.0, open_stakes) / initial

        return {
            "bankroll_usd": s["bankroll_usd"],
            "initial_bankroll_usd": initial,
            "total_realized_pnl": realized_pnl,
            "realized_drawdown_pct": round(realized_drawdown * 100, 2),
            "deployed_pct": round(deployed_pct * 100, 2),
            "open_positions": n_open,
            "closed_positions": n_closed,
            "win_rate": round(win_rate, 3) if win_rate is not None else None,
        }
