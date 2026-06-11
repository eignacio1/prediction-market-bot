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
    paper_portfolio_t4.json is derived state.

MIN_BET override:
    paper mode passes min_bet_usd=1.0 to RiskEngine, bypassing the
    live $10 floor. Evidence accumulation at paper scale requires
    volume, not dollar threshold. Change requires ADR at G6.

PAPER_T4_VIRTUAL mode (default: disabled — non-virtual paper positions):
    When PAPER_T4_VIRTUAL=true, C4 evaluates + stages every approved
    bet, but does NOT deduct from bankroll. This proves the architecture
    fires at scale (~1000s of bets per game) without depleting T1 capital.
    Default is false: positions are recorded in paper_portfolio_t4.json
    with pool_isolated=True (T1 bankroll untouched; T4 pool is separate).
    Virtual bets appear in logs/audit_t4.jsonl and staged_orders_t4.db.
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
    p_exceeds_threshold,
)
from prediction_market_bot.execution_bands import (
    NOISE_BUFFER_BAND_T4,
    EXIT_MIN_TIME_REMAINING_MIN,
    EXIT_MECHANICS_ACTIVE,
)
from prediction_market_bot.run_t4_inplay import T4EventLoop, GameStateEvent
from prediction_market_bot.c4_risk_engine.staged_order_store import StagedOrderStore
from prediction_market_bot.c4_risk_engine.risk import RiskEngine, RESERVE_MANDATE_PCT
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
MIN_BET_T4_PAPER = 0.01        # paper T4: Kalshi actual minimum (1 contract at lowest price)
PAPER_T4_VIRTUAL = os.environ.get("PAPER_T4_VIRTUAL", "false").lower() in ("true", "1", "yes")
PAPER_T4_FLAT_SIZING = os.environ.get("PAPER_T4_FLAT_SIZING", "true").lower() in ("true", "1", "yes")
PAPER_T4_POOL_USD = float(os.environ.get("PAPER_T4_POOL_USD", "500.0"))
SNAPSHOT_ID = "T4-LIVE"
SESSION_ID_PREFIX = "T4"

# ---------------------------------------------------------------------------
# T4 Band Budget — ADR-0013
# ---------------------------------------------------------------------------
# T4 operates on a per-game capital allocation, not the full portfolio bankroll.
# Without this, the high-throughput T4 band (~1000 evaluations/game) exhausts
# capital after ~60 bets, leaving 940+ opportunities unfunded.
#
# Architecture: T4 RiskEngine receives t4_band_budget as its 'bankroll'.
#   t4_band_budget = deployable_capital × T4_BAND_WEIGHT
#   deployable_capital = bankroll × (1 - RESERVE_MANDATE_PCT)
#   bet_size = edge × KELLY_T4 × t4_band_budget
#
# This scales correctly with capital ceiling:
#   $618 bankroll, weight=0.10 → $37 budget → ~$0.37/bet at edge=0.05
#   $10k bankroll, weight=0.10 → $600 budget → ~$6.00/bet at edge=0.05
#   $1M bankroll, weight=0.10 → $60k budget → ~$600/bet at edge=0.05
#
# PAPER_T4_VIRTUAL=true (calibration mode): track deployment, do NOT enforce ceiling.
#   G1/G2 PAPER_T4_VIRTUAL data calibrates T4_BAND_WEIGHT and T4_EXPECTED_TOTAL_EDGE.
# PAPER_T4_VIRTUAL=false (active mode): enforce band budget ceiling — stop firing when
#   t4_deployed_game >= t4_band_budget. Evaluation continues for log data.
#
# T4_BAND_WEIGHT: Phase 8 placeholder only — NOT used in PAPER_T4_FLAT_SIZING=true mode.
# ADR-0017 (2026-06-05): the fractional-allocation formula is architecturally incompatible
# with high-throughput T4 (~1,447 approved bets/game, G1 data). Budget exhausts in ~16 bets
# at 0.10 weight; 99% of evaluations go unfunded. PAPER_T4_FLAT_SIZING=true (default)
# bypasses this via PAPER_T4_POOL_USD — value is inactive in all current execution paths.
# Phase 8 per-bet sizing formula defined in ADR-0018 (required before T4 ACTIVE designation).
#
# T4_EXPECTED_TOTAL_EDGE: calibrated from Finals G1 2026-06-03 (PAPER_T4_FLAT_SIZING=true,
# 1459 evaluations, 1447 approved, KELLY_T4=0.20). Sum of edge = 442.52.
# Monitoring/planning constant only — not used in bet sizing computation.
T4_BAND_WEIGHT: float = 0.10           # Phase 8 placeholder — ADR-0017; inactive in PAPER_T4_FLAT_SIZING=true mode
T4_EXPECTED_TOTAL_EDGE: float = 441.38 # G1 calibrated 2026-06-04: sum(edge) across 1446 evals, KELLY_T4=0.20
                                       # NOTE: this was calibrated on GROSS edge (pre-T-149 fee fix);
                                       # net-of-fee total ≈ 416 at G1 throughput. Recalibrate post-G4.

_LOGS_DIR = Path(__file__).resolve().parents[2] / "logs"
_PORTFOLIO_PATH = _LOGS_DIR / "paper_portfolio_t4.json"
_STAGED_DB_PATH = str(_LOGS_DIR / "staged_orders_t4.db")
_AUDIT_LOG_PATH = _LOGS_DIR / "audit_t4.jsonl"
_SPREAD_LOG_PATH = _LOGS_DIR / "spread_observations.jsonl"    # EXP-019C
_TRAJ_LOG_PATH   = _LOGS_DIR / "t4_position_trajectories.jsonl"  # EXP-019B empirical


# ---------------------------------------------------------------------------
# T4 band budget helpers
# ---------------------------------------------------------------------------


def _compute_t4_band_budget(portfolio: dict) -> float:
    """
    T4 band budget = deployable_capital × T4_BAND_WEIGHT.
    Computed once at game start from live portfolio state.
    T4 RiskEngine uses this as 'bankroll' so Kelly operates within band allocation.
    """
    bankroll = portfolio["bankroll_usd"]
    deployable = bankroll * (1.0 - RESERVE_MANDATE_PCT)
    return max(deployable * T4_BAND_WEIGHT, 0.0)


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
    t4_band_budget: float,
    t4_deployed_usd: float,
) -> tuple[int, int, int, float]:   # (evaluated, fired, exited, updated_t4_deployed_usd)
    """
    Evaluate all live player × market pairs and fire approved bets.

    Returns (evaluated, fired, updated_t4_deployed_usd).
    t4_deployed_usd accumulates across cycles for the full game.
    PAPER_T4_VIRTUAL=true: tracks deployment for calibration, does NOT enforce budget.
    PAPER_T4_VIRTUAL=false: enforces band budget; stops firing when budget exhausted.
    """
    evaluated = 0
    fired = 0
    exited = 0
    fired_tickers: set[str] = set()   # one bet per ticker per cycle

    _spread_buf: list[str] = []
    _traj_buf: list[str] = []
    _cycle_ts = datetime.now(timezone.utc).isoformat()

    portfolio = trader.get_state()
    current_bankroll   = portfolio["bankroll_usd"]
    initial_bankroll   = portfolio.get("initial_bankroll_usd", current_bankroll)
    current_daily_loss = portfolio.get("current_daily_loss", 0.0)
    if portfolio.get("daily_loss_date", "") != date.today().isoformat():
        current_daily_loss = 0.0
    # Bug H fix: drawdown = realized losses only (deployed T1 capital is not a loss).
    # Without this fix, T1 deploying $382 shows 38.2% drawdown — above the 20% kill
    # switch — and C4 rejects every T4 bet before the game starts.
    _realized_loss = max(0.0, -portfolio.get("total_realized_pnl", 0.0))
    drawdown = _realized_loss / initial_bankroll if initial_bankroll > 0 else 0.0

    state_by_id = {ls.player_id: ls for ls in live_states}

    # ------------------------------------------------------------------
    # Exit evaluation pass (ADR-0018/0019 — symmetric filter-out)
    # Check all open positions before evaluating new entries.
    # Exit signal: mip_current > p_current + NOISE_BUFFER_BAND_T4  (YES)
    #              p_current > mip_current + NOISE_BUFFER_BAND_T4   (NO)
    # EXP-019B analytic: full exit always (Kelly fraction → 0 at boundary).
    # Time guard: no exits in final EXIT_MIN_TIME_REMAINING_MIN (T5 takes over).
    # Gate: EXIT_MECHANICS_ACTIVE must be True (ADR-0019 Tier 2). Default: False.
    # ------------------------------------------------------------------
    for open_pos in (list(portfolio.get("open_positions", [])) if EXIT_MECHANICS_ACTIVE else []):
        ticker    = open_pos.get("kalshi_ticker", "")
        player_id = int(open_pos.get("player_id", 0))
        threshold = float(open_pos.get("kalshi_threshold", 0))
        direction = open_pos.get("direction", "YES")

        pm = live_prices.get(ticker)
        if pm is None or not pm.has_live_quotes:
            continue

        ls = state_by_id.get(player_id)
        if ls is None:
            continue

        # Time guard: T5 handles final 3 minutes, exit mechanics stop here
        if ls.time_remaining_min <= EXIT_MIN_TIME_REMAINING_MIN:
            continue

        # Recompute p_current using same Poisson CDF as T4 entry (ADR-0018 §1)
        pts_mean = pregame_by_player_id.get(player_id, [{}])[0].get("pts_l10_mean", 20.0)
        pace = pts_mean / PACE_MINUTES_PER_GAME
        lam_remaining = pace * ls.time_remaining_min
        p_current = p_exceeds_threshold(ls.pts_so_far, threshold, lam_remaining)

        mip_current = pm.mid_price
        if direction == "YES":
            should_exit = mip_current > p_current + NOISE_BUFFER_BAND_T4
        else:  # NO
            should_exit = p_current > mip_current + NOISE_BUFFER_BAND_T4

        if not should_exit:
            continue

        position_id = open_pos["position_id"]
        exit_reason = (
            f"BAYESIAN_REVERSAL  p_current={p_current:.4f}"
            f"  mip={mip_current:.4f}  buffer={NOISE_BUFFER_BAND_T4}"
        )
        ok, closed = trader.exit_position(
            position_id=position_id,
            exit_mip=mip_current,
            p_current=p_current,
            exit_reason=exit_reason,
            session_id=session_id,
        )
        if not ok:
            logger.error("PaperTrader C6 write failure on exit for %s — halting cycle", ticker)
            return evaluated, fired, exited, t4_deployed_usd
        if closed:
            exited += 1
            logger.info(
                "T4 EXIT  %-45s  %-3s  p_cur=%.3f  mip=%.3f  pnl=%+.4f  reason=%s",
                ticker, direction, p_current, mip_current,
                closed.get("exit_pnl", 0.0), "BAYESIAN_REVERSAL",
            )

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

            # EXP-019C: log spread for every live quote seen this cycle
            _spread_buf.append(json.dumps({
                "ticker": ticker,
                "timestamp_utc": _cycle_ts,
                "bid": pm.yes_bid,
                "ask": pm.yes_ask,
                "mid": mip,
                "time_remaining_min": ls.time_remaining_min,
                "pts_so_far": float(ls.pts_so_far),
                "threshold": int(mkt_ctx["threshold"]),
            }))

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

            # EXP-019B empirical: log p_t4 per cycle for all evaluated tickers
            if result.action in ("FIRE_BAYESIAN", "NO_ACTION") and result.signal is not None:
                _traj_buf.append(json.dumps({
                    "ticker": ticker,
                    "cycle_id": cycle_id,
                    "timestamp_utc": _cycle_ts,
                    "p_t4": float(result.signal.p_t4),
                    "p_t4_baseline": float(result.signal.p_t4_baseline),
                    "delta_p_incr": float(result.signal.delta_p_incr),
                    "sigma_null": float(result.signal.sigma_null),
                    "mip": mip,
                    "pts_so_far": float(ls.pts_so_far),
                    "time_remaining_min": ls.time_remaining_min,
                    "action": result.action,
                }))

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

            gross_edge = edge
            kalshi_fee = 0.07 * mip * (1.0 - mip)  # ADR-0016 taker fee
            net_edge = gross_edge - kalshi_fee

            fc_record = {
                "forecast_id": f"T4-{cycle_id}-{ticker[-12:]}",
                "p_estimate": p_est,
                "market_implied_prob": mip,
                "edge": net_edge,          # net-of-fee — C4 gates on this (GG-019 fix)
                "gross_edge": gross_edge,  # pre-fee — for paper_trader annotation (ADR-0016)
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
                return evaluated, fired, exited, t4_deployed_usd

            if approval.get("approval_status") != "APPROVED":
                continue

            approved_size = float(approval["approved_size"])

            # Flat sizing: 1 contract at market price (paper throughput validation).
            # Overrides Kelly so every approved bet fires at the same unit cost,
            # decoupling actual bet COUNT from the Kelly-sized amount.
            if PAPER_T4_FLAT_SIZING:
                approved_size = mip
                approval = {**approval, "approved_size": approved_size}

            approval = {**approval, "model_p": float(p_est), "edge": float(net_edge), "gross_edge": float(gross_edge)}

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

            # ---- Execute: virtual log OR portfolio write ----
            if PAPER_T4_VIRTUAL:
                # Virtual mode (calibration): C4 approved — stage + log, no bankroll deduction.
                # Budget is tracked but NOT enforced here — we want to see unconstrained
                # would-be deployment so G1 data can calibrate T4_BAND_WEIGHT (ADR-0013).
                store.mark_fired(order_id)
                fired_tickers.add(ticker)
                fired += 1
                t4_deployed_usd += approved_size
                logger.info(
                    "T4 VIRTUAL %-45s  %-3s  $%5.2f  p=%.3f  mip=%.3f  edge=%+.3f"
                    "  budget_track=$%.2f/%.2f  cycle=%s",
                    ticker, direction, approved_size, p_est, mip, net_edge,
                    t4_deployed_usd, t4_band_budget, cycle_id,
                )
            else:
                # Active mode: enforce band budget ceiling (ADR-0013).
                # Stop firing when band is exhausted; continue evaluating for log data.
                if t4_deployed_usd + approved_size > t4_band_budget:
                    logger.info(
                        "T4 BAND_BUDGET_EXHAUSTED %-45s  remaining=$%.2f",
                        ticker, max(0.0, t4_band_budget - t4_deployed_usd),
                    )
                    continue

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
                    pool_isolated=PAPER_T4_FLAT_SIZING,
                )
                if not ok:
                    logger.error("PaperTrader C6 write failure at %s — halting cycle", ticker)
                    return evaluated, fired, exited, t4_deployed_usd

                if pos:
                    store.mark_fired(order_id)
                    fired_tickers.add(ticker)
                    fired += 1
                    t4_deployed_usd += approved_size
                    logger.info(
                        "T4 FIRED  %-45s  %-3s  $%5.2f  p=%.3f  mip=%.3f  edge=%+.3f"
                        "  budget_used=$%.2f/%.2f  cycle=%s",
                        ticker, direction, approved_size, p_est, mip, net_edge,
                        t4_deployed_usd, t4_band_budget, cycle_id,
                    )

    if _spread_buf:
        with open(_SPREAD_LOG_PATH, "a") as _f:
            _f.write("\n".join(_spread_buf) + "\n")
    if _traj_buf:
        with open(_TRAJ_LOG_PATH, "a") as _f:
            _f.write("\n".join(_traj_buf) + "\n")

    if exited > 0:
        logger.info("T4 EXIT PASS  exited=%d this cycle", exited)

    return evaluated, fired, exited, t4_deployed_usd


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

    def _make_engines(t4_band_budget: float) -> tuple[RiskEngine, RiskEngine]:
        """
        Create fresh RiskEngine instances for T4/T5.

        'bankroll' = t4_band_budget so Kelly sizes within the band allocation (ADR-0013).
        'initial_bankroll' = real session-start bankroll to anchor kill-switch thresholds —
        the system-level kill switch (drawdown/daily-loss) remains anchored to the full
        portfolio, not the band budget.
        """
        state = trader.get_state()
        ibr = state.get("initial_bankroll_usd", state["bankroll_usd"])
        e4 = RiskEngine(
            logger=audit,
            snapshot_id=SNAPSHOT_ID,
            bankroll=t4_band_budget,
            kelly_fraction=KELLY_T4,
            initial_bankroll=ibr,
            min_bet_usd=MIN_BET_T4_PAPER,
        )
        e5 = RiskEngine(
            logger=audit,
            snapshot_id=SNAPSHOT_ID,
            bankroll=t4_band_budget,
            kelly_fraction=KELLY_T5,
            initial_bankroll=ibr,
            min_bet_usd=MIN_BET_T4_PAPER,
        )
        return e4, e5

    # ---- T4 band budget (ADR-0013) ----
    # Computed once at session start from current portfolio state.
    # Held fixed for the game; Kelly operates on this allocation, not full bankroll.
    # PAPER_T4_FLAT_SIZING=true: use PAPER_T4_POOL_USD directly — flat 1-contract sizing
    # decouples bet count from Kelly amount; pool must accommodate ~1,050 × avg market price.
    if PAPER_T4_FLAT_SIZING:
        t4_band_budget = PAPER_T4_POOL_USD
    else:
        t4_band_budget = _compute_t4_band_budget(trader.get_state())
    t4_deployed_game = 0.0
    if PAPER_T4_FLAT_SIZING:
        logger.info(
            "T4 band budget: $%.2f  (PAPER_T4_POOL_USD — flat sizing mode, bypasses ADR-0013 Kelly budget)",
            t4_band_budget,
        )
        logger.info(
            "PAPER_T4_FLAT_SIZING=true: 1-contract flat sizing active. "
            "~1,050 bets × avg $0.50/contract ≈ $525 total stake. Pool=$%.2f", PAPER_T4_POOL_USD,
        )
    else:
        logger.info(
            "T4 band budget: $%.2f  (T4_BAND_WEIGHT=%.2f × deployable)  [ADR-0013 — STUB values until G1 calibration]",
            t4_band_budget, T4_BAND_WEIGHT,
        )
    if PAPER_T4_VIRTUAL:
        logger.info(
            "PAPER_T4_VIRTUAL=true: budget tracked for calibration, ceiling NOT enforced. "
            "G1 data → calibrate T4_BAND_WEIGHT and T4_EXPECTED_TOTAL_EDGE before T4 ACTIVE."
        )
    else:
        logger.info(
            "PAPER_T4_VIRTUAL=false: band budget ceiling ENFORCED. Bets fire as actual paper positions."
        )

    # ---- Main polling loop ----
    cycle_n = 0
    total_evaluated = 0
    total_fired = 0
    total_exited = 0

    while True:
        if kill_switch_armed(KILL_SWITCH_PATH):
            logger.warning(
                "Kill switch armed — sleeping 10s. rm logs/t4_kill_switch.flag to resume."
            )
            time.sleep(10)
            continue

        try:
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

            # Build fresh engines each cycle — bankroll = t4_band_budget (ADR-0013).
            # t4_band_budget is fixed for the game; engine refresh tracks kill-switch state.
            engine_t4, engine_t5 = _make_engines(t4_band_budget)
            cycle_id = f"C{cycle_n:04d}-{uuid.uuid4().hex[:6]}"

            ev, fi, ex, t4_deployed_game = _run_cycle(
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
                t4_band_budget=t4_band_budget,
                t4_deployed_usd=t4_deployed_game,
            )

            cycle_n += 1
            total_evaluated += ev
            total_fired += fi
            total_exited += ex

            budget_pct = (t4_deployed_game / t4_band_budget * 100.0) if t4_band_budget > 0 else 0.0
            logger.info(
                "─ cycle=%s  eval=%d fired=%d exited=%d │ session: eval=%d fired=%d exited=%d"
                " │ T4_budget: $%.2f/$%.2f (%.0f%%)  │ bankroll=$%.2f",
                cycle_id, ev, fi, ex,
                total_evaluated, total_fired, total_exited,
                t4_deployed_game, t4_band_budget, budget_pct,
                trader.get_state()["bankroll_usd"],
            )

            time.sleep(POLL_INTERVAL_S)

        except Exception as exc:
            logger.error(
                "Unhandled exception in main loop — sleeping %ds before retry: %s",
                POLL_INTERVAL_S, exc, exc_info=True,
            )
            time.sleep(POLL_INTERVAL_S)


if __name__ == "__main__":
    main()
