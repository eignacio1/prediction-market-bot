"""
PIPE-07 Live: T4/T5 Continuous In-Play Execution
=================================================
Pipeline:  PIPE-07
Band:      T4 (in-play Bayesian) + T5 (late-game arithmetic)
Requires:  BOT_ENV=paper, BOT_C4_ACTIVE=true
           Active NBA game in progress or scheduled today
           Pregame JSON in logs/ from today's PIPE-02 run

Activation:
    PYTHONPATH=src BOT_ENV=paper BOT_C4_ACTIVE=true \\
        python src/prediction_market_bot/run_t4_live.py

Kill switch (halts within one 45s cycle):
    touch logs/t4_kill_switch.flag
    rm    logs/t4_kill_switch.flag

Re-entry policy:
    T4 places multiple bets on the same ticker throughout the game as
    Kalshi prices move. One bet per ticker per 45s cycle (per-cycle
    deduplication). No cross-cycle idempotency — this is intentional.

Ghost protection:
    Every approved bet is staged in SQLite (WAL / ACID) BEFORE the
    portfolio JSON write. C6 JSONL is the canonical record.
    paper_portfolio.json is derived state.

MIN_BET override:
    paper mode passes min_bet_usd=1.0 to RiskEngine, bypassing the
    live $10 floor. Evidence accumulation at paper scale requires
    volume, not dollar threshold. Change requires ADR at G6.
"""

from __future__ import annotations

import json
import logging
import os
import time
import uuid
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

import requests

from prediction_market_bot.c1_signal_ingestion.ds02_nba_live import (
    LivePlayerState,
    kill_switch_armed,
    KILL_SWITCH_PATH,
)
from prediction_market_bot.c3_forecasting.game_state_model import (
    GameStateModel,
    LateGameArithmetic,
    KELLY_T4,
    KELLY_T5,
)
from prediction_market_bot.run_t4_inplay import T4EventLoop, GameStateEvent
from prediction_market_bot.c4_risk_engine.staged_order_store import StagedOrderStore
from prediction_market_bot.c4_risk_engine.risk import RiskEngine
from prediction_market_bot.c5_execution.paper_trader import PaperTrader
from prediction_market_bot.c5_execution.kalshi_client import KalshiMarketClient
from prediction_market_bot.c6_audit_logger.audit_logger import AuditLogger

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# ESPN live feed (primary data source — NBA CDN blocked on cloud IPs)
# ---------------------------------------------------------------------------

_ESPN_SCOREBOARD = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard"
_ESPN_SUMMARY    = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/summary"
_ESPN_HEADERS    = {"User-Agent": "Mozilla/5.0"}

_ESPN_STATUS_SCHEDULED = "STATUS_SCHEDULED"
_ESPN_STATUS_IN_PROGRESS = "STATUS_IN_PROGRESS"
_ESPN_STATUS_FINAL = "STATUS_FINAL"

# Stat label positions in ESPN boxscore statistics array
_ESPN_STAT_LABELS = ["MIN", "PTS", "FG", "3PT", "FT", "REB", "AST", "TO", "STL", "BLK", "OREB", "DREB", "PF", "+/-"]


def _espn_game_ids_today() -> list[str]:
    """Return ESPN game IDs for today's NBA games (in-progress first)."""
    try:
        today_str = date.today().strftime("%Y%m%d")
        r = requests.get(
            _ESPN_SCOREBOARD,
            params={"dates": today_str, "limit": 20},
            headers=_ESPN_HEADERS,
            timeout=10,
        )
        r.raise_for_status()
        events = r.json().get("events", [])
        in_progress = [
            e["id"] for e in events
            if e.get("status", {}).get("type", {}).get("name") == _ESPN_STATUS_IN_PROGRESS
        ]
        scheduled = [
            e["id"] for e in events
            if e.get("status", {}).get("type", {}).get("name") == _ESPN_STATUS_SCHEDULED
        ]
        return in_progress + scheduled
    except Exception as exc:
        logger.warning("ESPN game ID discovery failed: %s", exc)
        return []


def _parse_espn_clock(display_clock: str, period: int) -> float:
    """
    Convert ESPN displayClock + period to full-game minutes remaining.

    displayClock format: "5:32" (min:sec) or "0.0" (scheduled/final).
    period: 1-4 (regulation), 5+ (OT).
    Returns total game minutes remaining.
    """
    try:
        if ":" in (display_clock or ""):
            parts = display_clock.split(":")
            clock_min = float(parts[0]) + float(parts[1]) / 60.0
        else:
            clock_min = float(display_clock or "0") / 60.0
    except (ValueError, IndexError):
        clock_min = 0.0

    if period <= 0:
        return 48.0
    if period <= 4:
        quarters_remaining = max(0, 4 - period)
        return quarters_remaining * 12.0 + clock_min
    return clock_min   # OT: just current period clock


def _espn_poll_once(
    espn_game_id: str,
    name_to_pregame: dict[str, dict],  # {normalized_name: {player_id, ...}}
) -> list[LivePlayerState]:
    """
    Fetch live boxscore from ESPN for one game.
    Returns [] if game not in progress or request fails.
    Maps player names to NBA player IDs via pregame context.
    """
    try:
        r = requests.get(
            _ESPN_SUMMARY,
            params={"event": espn_game_id},
            headers=_ESPN_HEADERS,
            timeout=10,
        )
        r.raise_for_status()
        d = r.json()
    except Exception as exc:
        logger.error("ESPN boxscore fetch failed game=%s: %s", espn_game_id, exc)
        return []

    # Game state from header
    h = d.get("header", {})
    comps = h.get("competitions", [{}])
    if not comps:
        return []
    comp = comps[0]
    status = comp.get("status", {})
    status_name = status.get("type", {}).get("name", "")

    if status_name != _ESPN_STATUS_IN_PROGRESS:
        logger.info("ESPN game %s status=%s — not polling", espn_game_id, status_name)
        return []

    period = int(status.get("period") or 0)
    display_clock = str(status.get("displayClock") or "0:00")
    time_remaining = _parse_espn_clock(display_clock, period)

    # Player stats from boxscore
    bx = d.get("boxscore", {})
    players_teams = bx.get("players", [])
    states: list[LivePlayerState] = []

    for team_data in players_teams:
        stats_groups = team_data.get("statistics", [])
        if not stats_groups:
            continue
        sg = stats_groups[0]
        labels = sg.get("labels", _ESPN_STAT_LABELS)

        try:
            pts_idx = labels.index("PTS")
            min_idx = labels.index("MIN")
        except ValueError:
            pts_idx, min_idx = 1, 0   # fallback to expected positions

        for athlete_entry in sg.get("athletes", []):
            athlete = athlete_entry.get("athlete", {})
            name = athlete.get("displayName", "")
            stats = athlete_entry.get("stats", [])

            if not stats:
                continue

            norm = name.lower().replace(" ", "")
            ctx = name_to_pregame.get(norm)
            if ctx is None:
                continue   # player not in pregame context

            try:
                pts = int(float(stats[pts_idx] or 0))
            except (IndexError, ValueError, TypeError):
                pts = 0

            try:
                min_str = str(stats[min_idx] or "0")
                mins_played = float(min_str) if ":" not in min_str else (
                    float(min_str.split(":")[0]) + float(min_str.split(":")[1]) / 60.0
                )
            except (IndexError, ValueError, TypeError):
                mins_played = 0.0

            states.append(LivePlayerState(
                player_id=int(ctx["player_id"]),
                player_name=name,
                team_id=0,
                pts_so_far=pts,
                rebounds=0,
                assists=0,
                minutes_played=mins_played,
                quarter=period,
                time_remaining_min=time_remaining,
                game_id=espn_game_id,
                game_status=2,
            ))

    if states:
        logger.info(
            "ESPN poll: game=%s  Q%d  clock=%s  time_rem=%.1f min  %d players",
            espn_game_id, period, display_clock, time_remaining, len(states),
        )
    return states

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

POLL_INTERVAL_S = 45
PACE_MINUTES_PER_GAME = 36.0   # approx starter minutes used for pace_pts_per_min calc
MIN_BET_T4_PAPER = 1.0         # paper T4: $1 floor (live uses $10 global MIN_BET_USD)
SNAPSHOT_ID = "T4-LIVE"
SESSION_ID_PREFIX = "T4"

_LOGS_DIR = Path(__file__).resolve().parents[2] / "logs"
_PORTFOLIO_PATH = _LOGS_DIR / "paper_portfolio.json"
_STAGED_DB_PATH = str(_LOGS_DIR / "staged_orders.db")
_AUDIT_LOG_PATH = _LOGS_DIR / "audit_t4.jsonl"


# ---------------------------------------------------------------------------
# Pregame context loader
# ---------------------------------------------------------------------------

def _load_pregame_context() -> tuple[dict[int, list[dict]], dict[str, dict], dict[str, dict]]:
    """
    Load the latest pregame JSON from logs/pregame_*.json.

    Returns:
        by_player_id   {player_id (int): [market_ctx, ...]}
        by_ticker      {ticker (str): market_ctx}
        name_to_pregame  {normalized_name (str): first market_ctx for player}

    Each market_ctx dict contains:
        ticker, threshold, p_t1, pts_l10_mean, player_name, player_id
    """
    jsons = sorted(_LOGS_DIR.glob("pregame_*.json"), reverse=True)
    if not jsons:
        raise FileNotFoundError(
            "No pregame JSON found in logs/. Run PIPE-02 (run_pregame.py) first."
        )

    path = jsons[0]
    logger.info("Pregame context: %s", path.name)
    raw = json.loads(path.read_text())
    forecasts = raw.get("forecasts", raw) if isinstance(raw, dict) else raw

    by_player_id: dict[int, list[dict]] = {}
    by_ticker: dict[str, dict] = {}
    name_to_pregame: dict[str, dict] = {}

    for fc in forecasts:
        pid = fc.get("player_id")
        ticker = fc.get("kalshi_ticker", "")
        player_name = fc.get("player_name", "")
        if not pid or not ticker:
            continue
        pid = int(pid)
        ctx = {
            "ticker": ticker,
            "threshold": int(fc.get("kalshi_threshold", 0)),
            "p_t1": float(fc.get("p_estimate") or 0.5),
            "pts_l10_mean": float(fc.get("pts_l10_mean") or 20.0),
            "player_name": player_name,
            "player_id": pid,
        }
        by_player_id.setdefault(pid, []).append(ctx)
        by_ticker[ticker] = ctx
        norm = player_name.lower().replace(" ", "")
        if norm not in name_to_pregame:
            name_to_pregame[norm] = ctx   # first market seen for this player

    logger.info(
        "Loaded %d player(s), %d market(s) from %s",
        len(by_player_id), len(by_ticker), path.name,
    )
    return by_player_id, by_ticker, name_to_pregame


# ---------------------------------------------------------------------------
# Game ID discovery (ESPN primary — NBA CDN blocked on cloud IPs)
# ---------------------------------------------------------------------------

def _discover_game_ids() -> list[str]:
    """
    Return today's ESPN game IDs (in-progress first, then scheduled).
    Uses ESPN API — NBA CDN/stats API are blocked on cloud provider IPs.
    """
    return _espn_game_ids_today()


# ---------------------------------------------------------------------------
# Single evaluation cycle
# ---------------------------------------------------------------------------

def _run_cycle(
    *,
    cycle_id: str,
    session_id: str,
    live_states: list[LivePlayerState],
    live_prices: dict,              # {ticker: PlayerMarket}
    pregame_by_player_id: dict,     # {player_id: [market_ctx, ...]}
    loop: T4EventLoop,
    engine_t4: RiskEngine,
    engine_t5: RiskEngine,
    trader: PaperTrader,
    store: StagedOrderStore,
    game_date: str,
) -> tuple[int, int]:
    """
    Evaluate all live player × market pairs and fire approved bets.

    Returns (evaluated, fired) counts.
    """
    evaluated = 0
    fired = 0
    fired_tickers: set[str] = set()   # one bet per ticker per cycle

    portfolio = trader.get_state()
    current_bankroll   = portfolio["bankroll_usd"]
    initial_bankroll   = portfolio.get("initial_bankroll_usd", current_bankroll)
    current_daily_loss = portfolio.get("current_daily_loss", 0.0)
    drawdown = max(0.0, (initial_bankroll - current_bankroll) / initial_bankroll)

    state_by_id = {ls.player_id: ls for ls in live_states}

    for player_id, markets in pregame_by_player_id.items():
        ls = state_by_id.get(player_id)
        if ls is None:
            continue   # player not in live boxscore

        pts_mean = markets[0]["pts_l10_mean"]
        pace = pts_mean / PACE_MINUTES_PER_GAME

        for mkt_ctx in markets:
            ticker = mkt_ctx["ticker"]
            if ticker in fired_tickers:
                continue

            pm = live_prices.get(ticker)
            if pm is None or not pm.has_live_quotes:
                continue   # market not active / no quotes

            mip = pm.mid_price
            vig = pm.vig
            if mip <= 0.0 or mip >= 1.0:
                continue

            event = GameStateEvent(
                market_id=ticker,
                player_id=str(player_id),
                threshold=float(mkt_ctx["threshold"]),
                pts_so_far=float(ls.pts_so_far),
                time_remaining_min=ls.time_remaining_min,
                quarter=ls.quarter,
                pace_pts_per_min=pace,
                p_t1=mkt_ctx["p_t1"],
                mip=mip,
                vig=vig,
            )

            result = loop.on_game_state_event(event)
            evaluated += 1

            if result.action not in ("FIRE_BAYESIAN", "FIRE_T5"):
                continue

            # ---- Determine direction + C4 inputs ----
            signal = result.signal

            if result.action == "FIRE_T5":
                p_hit = float(signal.p_hit)
                verdict = signal.verdict
                if verdict == "NEAR_CERTAIN_YES":
                    direction = "YES"
                    p_est = p_hit
                    edge = p_hit - mip
                elif verdict == "NEAR_CERTAIN_NO":
                    direction = "NO"
                    p_est = p_hit          # P(YES) per model; C4 flips for NO
                    edge = mip - p_hit
                else:
                    continue               # UNCERTAIN — T4EventLoop should not emit this
                engine = engine_t5
            else:
                # FIRE_BAYESIAN: fire condition guarantees p_t4 > mip + vig → always YES
                p_est = float(signal.p_t4)
                direction = "YES"
                edge = p_est - mip
                engine = engine_t4

            fc_record = {
                "forecast_id": f"T4-{cycle_id}-{ticker[-12:]}",
                "p_estimate": p_est,
                "market_implied_prob": mip,
                "edge": edge,
                "recommended_direction": direction,
            }

            # ---- C4 risk evaluation ----
            ok, approval = engine.evaluate_forecast(
                forecast_record=fc_record,
                current_daily_loss=current_daily_loss,
                current_drawdown_pct=drawdown,
                session_id=session_id,
            )
            if not ok:
                logger.error("C4/C6 write failure at %s — halting cycle", ticker)
                return evaluated, fired

            if approval.get("approval_status") != "APPROVED":
                continue

            approved_size = float(approval["approved_size"])

            # ---- Ghost protection: stage before portfolio write ----
            valid_until = (
                datetime.now(timezone.utc) + timedelta(hours=4)
            ).isoformat()

            try:
                order_id = store.stage_order(
                    market_id=ticker,
                    player_id=str(player_id),
                    threshold=float(mkt_ctx["threshold"]),
                    direction=direction,
                    strategy="A",
                    p_t1=mkt_ctx["p_t1"],
                    p_entry=mip,
                    kelly_fraction=result.kelly_fraction,
                    sized_amount_usd=approved_size,
                    valid_until_iso=valid_until,
                    notes=f"T4-LIVE cycle={cycle_id}",
                )
            except Exception as exc:
                logger.warning("stage_order failed for %s: %s — skipping", ticker, exc)
                continue

            # ---- Execute: portfolio write ----
            ok, pos = trader.open_position(
                approval=approval,
                player_name=mkt_ctx["player_name"],
                player_id=int(player_id),
                kalshi_ticker=ticker,
                kalshi_threshold=int(mkt_ctx["threshold"]),
                mid_price=mip,
                vig=vig,
                game_date=game_date,
                session_id=session_id,
            )
            if not ok:
                logger.error("PaperTrader C6 write failure at %s — halting cycle", ticker)
                return evaluated, fired

            if pos:
                store.mark_fired(order_id)
                fired_tickers.add(ticker)
                fired += 1
                logger.info(
                    "T4 FIRED  %-45s  %-3s  $%5.2f  p=%.3f  mip=%.3f  edge=%+.3f  cycle=%s",
                    ticker, direction, approved_size, p_est, mip, edge, cycle_id,
                )

    return evaluated, fired


# ---------------------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------------------

def main() -> None:
    import sys

    bot_env = os.environ.get("BOT_ENV", "paper").lower()
    if bot_env != "paper":
        print("ERROR: run_t4_live.py is paper-mode only. Set BOT_ENV=paper.")
        sys.exit(1)

    if os.environ.get("BOT_C4_ACTIVE", "").lower() not in ("true", "1", "yes"):
        print("ERROR: BOT_C4_ACTIVE not set. T4 requires C4 active.")
        print("  Set BOT_C4_ACTIVE=true in your environment before running.")
        sys.exit(1)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)-8s %(message)s",
    )

    session_id = f"{SESSION_ID_PREFIX}-{uuid.uuid4().hex[:8].upper()}"
    logger.info("=" * 60)
    logger.info("PIPE-07 T4 Live  session=%s", session_id)
    logger.info("Kill switch: touch logs/t4_kill_switch.flag")
    logger.info("=" * 60)

    # ---- Load pregame context ----
    by_player_id, _by_ticker, name_to_pregame = _load_pregame_context()
    game_date = date.today().isoformat()

    # ---- Initialize components (once per session) ----
    audit  = AuditLogger(log_path=_AUDIT_LOG_PATH)
    store  = StagedOrderStore(_STAGED_DB_PATH)
    model  = GameStateModel()
    arith  = LateGameArithmetic()
    loop   = T4EventLoop(store, model, arith)
    trader = PaperTrader(portfolio_path=_PORTFOLIO_PATH, logger=audit)
    kalshi = KalshiMarketClient.from_env()

    # ---- Game ID discovery ----
    game_ids = _discover_game_ids()
    logger.info("Initial game IDs: %s", game_ids or "(none yet)")

    def _make_engines() -> tuple[RiskEngine, RiskEngine]:
        """Create fresh RiskEngine instances with current bankroll."""
        state = trader.get_state()
        br  = state["bankroll_usd"]
        ibr = state.get("initial_bankroll_usd", br)
        e4 = RiskEngine(
            logger=audit,
            snapshot_id=SNAPSHOT_ID,
            bankroll=br,
            kelly_fraction=KELLY_T4,
            initial_bankroll=ibr,
            min_bet_usd=MIN_BET_T4_PAPER,
        )
        e5 = RiskEngine(
            logger=audit,
            snapshot_id=SNAPSHOT_ID,
            bankroll=br,
            kelly_fraction=KELLY_T5,
            initial_bankroll=ibr,
            min_bet_usd=MIN_BET_T4_PAPER,
        )
        return e4, e5

    # ---- Main polling loop ----
    cycle_n = 0
    total_evaluated = 0
    total_fired = 0

    while True:
        if kill_switch_armed(KILL_SWITCH_PATH):
            logger.warning(
                "Kill switch armed — sleeping 10s. rm logs/t4_kill_switch.flag to resume."
            )
            time.sleep(10)
            continue

        # Re-discover games if we have none yet
        if not game_ids:
            game_ids[:] = _discover_game_ids()
            if game_ids:
                logger.info("Game(s) discovered: %s", game_ids)
            else:
                logger.debug("No active games found — sleeping 60s")
                time.sleep(60)
                continue

        # Poll all tracked games via ESPN
        all_states: list[LivePlayerState] = []
        for gid in game_ids:
            all_states.extend(_espn_poll_once(gid, name_to_pregame))

        if not all_states:
            logger.info("No live states — game not in progress. Sleeping 60s.")
            time.sleep(60)
            continue

        # Fetch live Kalshi prices
        ok, snapshot = kalshi.fetch_player_points_markets()
        if not ok or not snapshot.markets:
            logger.warning("Kalshi price fetch failed — skipping cycle, sleeping %ds", POLL_INTERVAL_S)
            time.sleep(POLL_INTERVAL_S)
            continue

        live_prices = {m.ticker: m for m in snapshot.markets}

        # Build fresh engines (tracks current bankroll)
        engine_t4, engine_t5 = _make_engines()
        cycle_id = f"C{cycle_n:04d}-{uuid.uuid4().hex[:6]}"

        ev, fi = _run_cycle(
            cycle_id=cycle_id,
            session_id=session_id,
            live_states=all_states,
            live_prices=live_prices,
            pregame_by_player_id=by_player_id,
            loop=loop,
            engine_t4=engine_t4,
            engine_t5=engine_t5,
            trader=trader,
            store=store,
            game_date=game_date,
        )

        cycle_n += 1
        total_evaluated += ev
        total_fired += fi

        logger.info(
            "─ cycle=%s  eval=%d fired=%d │ session: eval=%d fired=%d bankroll=$%.2f",
            cycle_id, ev, fi, total_evaluated, total_fired,
            trader.get_state()["bankroll_usd"],
        )

        time.sleep(POLL_INTERVAL_S)


if __name__ == "__main__":
    main()
