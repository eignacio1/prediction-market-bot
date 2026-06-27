"""
PIPE-07 MLB: T4 MLB Live In-Play Paper Trading
================================================
Pipeline:     PIPE-07 MLB (T4 — In-Play, baseball)
Band:         T4 (Bayesian in-play)
Requires:     BOT_ENV=paper, BOT_C4_ACTIVE=true
              Active MLB game in progress or scheduled today
              pregame_mlb_YYYYMMDD.json in logs/ from today's PIPE-06pre run

Schedule:     0 13 * * * timeout 43200 (9am ET default; self-heal waits until first_pitch−30min)
              PIPE-08 adjusts live crontab daily to optimal fire time.
              Self-heal makes crontab timing irrelevant — process always waits correctly.
Environment:  ENV-02 (VPS paper trading)

Kill switch:
    touch logs/t4_mlb_kill_switch.flag    # halts within one 45s cycle
    rm    logs/t4_mlb_kill_switch.flag    # resume

Bayesian model (MLB — Binomial):
  Prior:   p_t1 from pregame context (T1 model calibrated probability)
  Update:  P(total_hits >= threshold | h_so_far, ba_l10, ab_remaining)
           Uses Binomial distribution. Exact for discrete hit events.
  ba_l10:  Batting average from last 10 games (from pregame_mlb JSON)
           = P(hit | at-bat). Used as Binomial success probability.
  ab_remaining: expected_total_ab - ab_so_far
           (AB_PER_GAME_DEFAULT=3.7 minus completed ABs from ESPN boxscore)
  Special cases:
    h_so_far >= threshold → p_t4 = 1.0 (already achieved)
    h_needed > ab_remaining → p_t4 = 0.0 (mathematically impossible)

Fire condition:
  p_t4 > mip + vig (edge positive after vig, before Kalshi fee)
  Then: net_edge = p_t4 - mip - kalshi_fee (ADR-0016 taker fee)
  C4 gates on net_edge (MIN_EDGE via RiskEngine).

Portfolio isolation (ADR-0013/ADR-0023):
  Isolated to paper_portfolio_mlb_t4.json. T1 bankroll untouched.
  Budget: pool × T4_BAND_WEIGHT=0.27 (ADR-0023).

~1,000 evaluations per game expected (CLAUDE.md Hard Rule 9).

Security (NFR-05):
  BOT_ENV=paper + BOT_C4_ACTIVE=true checked at startup.
  VENUE_API_KEY from environment only.
  Never touches live capital.

How to run:
  source /opt/prediction-market-bot/.env
  BOT_ENV=paper BOT_C4_ACTIVE=true PYTHONPATH=src \\
      /opt/prediction-market-bot/venv/bin/python \\
      src/prediction_market_bot/run_t4_mlb_live.py
"""

from __future__ import annotations

import json
import logging
import math
import os
import sys
import time
import uuid
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

import requests

_SRC_ROOT = Path(__file__).resolve().parents[2]
if str(_SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(_SRC_ROOT))

from prediction_market_bot.c4_risk_engine.risk import RiskEngine
from prediction_market_bot.c4_risk_engine.staged_order_store import StagedOrderStore
from prediction_market_bot.c5_execution.kalshi_client import KalshiMarketClient, SERIES_MLB_PLAYER_HITS
from prediction_market_bot.c5_execution.paper_trader import PaperTrader
from prediction_market_bot.c6_audit_logger.audit_logger import AuditLogger

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# MLB schedule API (self-heal startup)
# ---------------------------------------------------------------------------

_MLB_SCHEDULE_API     = "https://statsapi.mlb.com/api/v1/schedule"
_MLB_SPORT_ID         = 1
_NO_PLAY_STATES       = frozenset({"Postponed", "Cancelled", "Postponed - Rain"})
T4_STARTUP_BUFFER_MIN = 30  # start this many minutes before first pitch

# ---------------------------------------------------------------------------
# Guard: paper mode + C4 active
# ---------------------------------------------------------------------------

if os.environ.get("BOT_ENV", "").lower() != "paper":
    print("ERROR: run_t4_mlb_live.py is paper-mode only. Set BOT_ENV=paper.")
    sys.exit(1)

if os.environ.get("BOT_C4_ACTIVE", "").lower() not in ("true", "1", "yes"):
    print("ERROR: BOT_C4_ACTIVE not set. T4 requires C4 active.")
    print("  Set BOT_C4_ACTIVE=true in your environment before running.")
    sys.exit(1)

# ---------------------------------------------------------------------------
# Dry-run mode (T-202)
# When T4_MLB_DRY_RUN=true: compute all evaluations, log to JSONL, skip execution.
# No positions are opened, no staged orders written, no portfolio mutated.
# Used to collect evaluation distribution for edge calibration (T-203/GG-007).
# ---------------------------------------------------------------------------
T4_MLB_DRY_RUN = os.environ.get("T4_MLB_DRY_RUN", "").lower() in ("true", "1", "yes")

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

COMPONENT           = "PIPE-07-MLB"
POLL_INTERVAL_S     = 45
T4_BAND_WEIGHT      = 0.27          # ADR-0023 (same as NBA T4)
MIN_BET_T4_PAPER    = 0.01          # paper min: 1 contract at lowest price
SNAPSHOT_ID         = "T4-MLB-LIVE"
SESSION_ID_PREFIX   = "T4-MLB"
AB_PER_GAME_DEFAULT = 3.7           # typical MLB batter ABs per game (slot-5 / population baseline)
KELLY_T4            = 0.10          # conservative Kelly for T4 paper (ADR-0023)

# Slot-specific expected ABs per game — mirrors T2 empirical averages (T-200)
_AB_BY_SLOT: dict[int, float] = {
    1: 4.2, 2: 4.1, 3: 4.0, 4: 3.9, 5: 3.7,
    6: 3.6, 7: 3.4, 8: 3.2, 9: 3.1,
}

_LOGS_DIR        = Path(__file__).resolve().parents[2] / "logs"
_PORTFOLIO_PATH  = _LOGS_DIR / "paper_portfolio_mlb_t4.json"
_STAGED_DB_PATH  = str(_LOGS_DIR / "staged_orders_mlb_t4.db")
_AUDIT_LOG_PATH  = _LOGS_DIR / "audit_mlb_t4.jsonl"
KILL_SWITCH_PATH = _LOGS_DIR / "t4_mlb_kill_switch.flag"

# ---------------------------------------------------------------------------
# ESPN MLB live feed
# ---------------------------------------------------------------------------

_ESPN_MLB_SCOREBOARD = "https://site.api.espn.com/apis/site/v2/sports/baseball/mlb/scoreboard"
_ESPN_MLB_SUMMARY    = "https://site.api.espn.com/apis/site/v2/sports/baseball/mlb/summary"
_ESPN_HEADERS        = {"User-Agent": "Mozilla/5.0"}

_ESPN_STATUS_IN_PROGRESS = "STATUS_IN_PROGRESS"
_ESPN_STATUS_SCHEDULED   = "STATUS_SCHEDULED"

# ESPN MLB batter stat label order — H is typically index 2 in (AB, R, H, HR, RBI, BB, SO)
_MLB_STAT_LABELS = ["AB", "R", "H", "HR", "RBI", "BB", "SO", "AVG", "OBP", "SLG"]


@dataclass
class MLBLiveBatterState:
    player_id: int
    player_name: str
    h_so_far: int
    ab_so_far: int
    inning: int
    game_id: str


# ---------------------------------------------------------------------------
# Kill switch
# ---------------------------------------------------------------------------


def kill_switch_armed(path: Path) -> bool:
    return path.exists()


# ---------------------------------------------------------------------------
# Dry-run record writer (T-202)
# ---------------------------------------------------------------------------


def _append_dryrun_record(path: Path, record: dict) -> None:
    """Append one evaluation record to the dry-run JSONL log (append-only)."""
    try:
        with path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(record) + "\n")
    except Exception as exc:
        logger.warning("Dry-run record write failed: %s", exc)


# ---------------------------------------------------------------------------
# AB remaining — inning-aware (T-200)
# ---------------------------------------------------------------------------


def _compute_ab_remaining(
    ab_so_far: int,
    inning: int,
    batting_slot: int = 0,
) -> int:
    """Inning-aware AB remaining estimate (T-200).

    Combines two signals and takes the conservative minimum:
      ab_from_inning  — expected_total × (innings_remaining / 9.0)
      ab_from_total   — expected_total − ab_so_far

    Eliminates the ±14–25% Binomial probability error from the old flat-3.7
    heuristic. Uses _AB_BY_SLOT when batting_slot is known; falls back to
    AB_PER_GAME_DEFAULT (3.7) for unknown slots (0).

    Extra innings (inning > 9): innings_remaining clamps to 0 →
    ab_remaining = 0 → T4 stops evaluating. Known conservative behaviour;
    acceptable for paper trading.
    """
    expected_total = _AB_BY_SLOT.get(batting_slot, AB_PER_GAME_DEFAULT)
    innings_remaining = max(0.0, 9.0 - inning + 0.5)
    ab_from_inning = expected_total * (innings_remaining / 9.0)
    ab_from_total  = max(0.0, expected_total - ab_so_far)
    return max(0, round(min(ab_from_inning, ab_from_total)))


# ---------------------------------------------------------------------------
# Pregame context loader
# ---------------------------------------------------------------------------


def _load_pregame_context() -> tuple[dict[int, list[dict]], dict[str, dict], dict[str, dict]]:
    """
    Load the most recent pregame_mlb_*.json from _LOGS_DIR.

    Returns:
      by_player_id:   {player_id: [{"ticker", "threshold", "p_t1", "ba_l10", "h_l10_mean", ...}]}
      by_ticker:      {ticker: ctx_dict}
      name_to_pregame: {normalized_name: first_ctx}
    """
    jsons = sorted(_LOGS_DIR.glob("pregame_mlb_*.json"), reverse=True)
    if not jsons:
        return {}, {}, {}

    report = json.loads(jsons[0].read_text())
    forecasts = report.get("forecasts", [])

    by_player_id: dict[int, list[dict]] = {}
    by_ticker: dict[str, dict] = {}
    name_to_pregame: dict[str, dict] = {}

    for fc in forecasts:
        pid   = int(fc.get("player_id", 0))
        name  = fc.get("player_name", "")
        ticker = fc.get("kalshi_ticker", "")
        ctx = {
            "player_id":   pid,
            "player_name": name,
            "ticker":      ticker,
            "threshold":   int(fc.get("kalshi_threshold", 1)),
            "p_t1":        float(fc.get("p_estimate", 0.5)),
            "ba_l10":      float(fc.get("ba_l10") or 0.25),
            "h_l10_mean":  float(fc.get("h_l10_mean") or 1.0),
        }
        by_player_id.setdefault(pid, []).append(ctx)
        by_ticker[ticker] = ctx
        norm = name.lower().replace(" ", "")
        name_to_pregame.setdefault(norm, ctx)

    logger.info(
        "Pregame context loaded: %d players, %d market/threshold pairs, from %s",
        len(by_player_id), len(by_ticker), jsons[0].name,
    )
    return by_player_id, by_ticker, name_to_pregame


def _load_t2_batting_slots() -> dict[int, int]:
    """Load batting slots from today's T2 MLB output, if available (T-200).

    Returns {player_id: batting_slot}. Empty dict if no T2 file found for today.
    T4 falls back to AB_PER_GAME_DEFAULT (3.7) for unknown slots.
    Date-filtered to today to prevent stale lineup from prior day.
    """
    today = date.today().strftime("%Y%m%d")
    files = sorted(
        (f for f in _LOGS_DIR.glob("t2_mlb_*.json") if today in f.name),
        reverse=True,
    )
    if not files:
        logger.info("No T2 MLB output for today — batting slots default to 3.7 ABs")
        return {}
    try:
        data   = json.loads(files[0].read_text())
        slots: dict[int, int] = {}
        for fc in data.get("forecasts", []):
            pid  = fc.get("player_id")
            slot = fc.get("batting_slot")
            if pid and slot:
                slots[int(pid)] = int(slot)
        if slots:
            logger.info(
                "T2 batting slots loaded: %d players from %s", len(slots), files[0].name
            )
        return slots
    except Exception as exc:
        logger.warning("T2 batting slots load failed (%s) — slots default to 3.7", exc)
        return {}


# ---------------------------------------------------------------------------
# ESPN MLB polling
# ---------------------------------------------------------------------------


def _espn_mlb_game_ids_today() -> list[str]:
    """Return ESPN game IDs for today's MLB games (in-progress first)."""
    try:
        today_str = date.today().strftime("%Y%m%d")
        r = requests.get(
            _ESPN_MLB_SCOREBOARD,
            params={"dates": today_str, "limit": 30},
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
        logger.warning("ESPN MLB game ID discovery failed: %s", exc)
        return []


def _espn_poll_once_mlb(
    espn_game_id: str,
    name_to_pregame: dict[str, dict],
) -> list[MLBLiveBatterState]:
    """
    Fetch live MLB boxscore from ESPN for one game.
    Returns [] if game not in progress or request fails.
    Maps player names to MLB player IDs via pregame context.
    """
    try:
        r = requests.get(
            _ESPN_MLB_SUMMARY,
            params={"event": espn_game_id},
            headers=_ESPN_HEADERS,
            timeout=10,
        )
        r.raise_for_status()
        d = r.json()
    except Exception as exc:
        logger.error("ESPN MLB boxscore fetch failed game=%s: %s", espn_game_id, exc)
        return []

    h = d.get("header", {})
    comps = h.get("competitions", [{}])
    if not comps:
        return []
    comp = comps[0]
    status_name = comp.get("status", {}).get("type", {}).get("name", "")
    if status_name != _ESPN_STATUS_IN_PROGRESS:
        logger.info("ESPN MLB game %s status=%s — not polling", espn_game_id, status_name)
        return []

    inning = int(comp.get("status", {}).get("period") or 1)

    bx = d.get("boxscore", {})
    players_teams = bx.get("players", [])
    states: list[MLBLiveBatterState] = []

    for team_data in players_teams:
        # MLB ESPN boxscore: statistics list, first entry = batting stats
        for stat_group in team_data.get("statistics", []):
            if stat_group.get("name", "").lower() != "batting":
                continue

            labels = stat_group.get("labels", _MLB_STAT_LABELS)
            try:
                h_idx  = labels.index("H")
            except ValueError:
                h_idx = 2   # fallback: AB=0, R=1, H=2
            try:
                ab_idx = labels.index("AB")
            except ValueError:
                ab_idx = 0

            for athlete_entry in stat_group.get("athletes", []):
                athlete = athlete_entry.get("athlete", {})
                name    = athlete.get("displayName", "")
                stats   = athlete_entry.get("stats", [])
                if not stats:
                    continue

                norm = name.lower().replace(" ", "")
                ctx  = name_to_pregame.get(norm)
                if ctx is None:
                    continue

                try:
                    h_so_far = int(float(stats[h_idx] or 0))
                except (IndexError, ValueError, TypeError):
                    h_so_far = 0

                try:
                    ab_so_far = int(float(stats[ab_idx] or 0))
                except (IndexError, ValueError, TypeError):
                    ab_so_far = 0

                states.append(MLBLiveBatterState(
                    player_id=int(ctx["player_id"]),
                    player_name=name,
                    h_so_far=h_so_far,
                    ab_so_far=ab_so_far,
                    inning=inning,
                    game_id=espn_game_id,
                ))
            break   # only read batting stats, not pitching

    if states:
        logger.info(
            "ESPN MLB poll: game=%s  inning=%d  %d batters",
            espn_game_id, inning, len(states),
        )
    return states


# ---------------------------------------------------------------------------
# Binomial probability model (MLB Bayesian update)
# ---------------------------------------------------------------------------


def _binomial_pmf(n: int, k: int, p: float) -> float:
    """P(X = k) for X ~ Binomial(n, p)."""
    if k < 0 or k > n:
        return 0.0
    if p <= 0.0:
        return 1.0 if k == 0 else 0.0
    if p >= 1.0:
        return 1.0 if k == n else 0.0
    log_c = math.lgamma(n + 1) - math.lgamma(k + 1) - math.lgamma(n - k + 1)
    return math.exp(log_c + k * math.log(p) + (n - k) * math.log(1.0 - p))


def p_hits_gte_threshold(
    h_so_far: int,
    threshold: int,
    ba_l10: float,
    ab_remaining: int,
) -> float:
    """
    P(total_hits >= threshold | h_so_far hits already, ab_remaining ABs left, ba_l10 hit rate).

    Bayesian update for MLB hit totals using Binomial distribution.
    """
    h_needed = max(0, threshold - h_so_far)

    if h_needed <= 0:
        return 1.0   # already achieved

    if h_needed > ab_remaining or ab_remaining <= 0:
        return 0.0   # mathematically impossible

    p = max(0.001, min(0.999, ba_l10))
    p_gte = sum(
        _binomial_pmf(ab_remaining, k, p)
        for k in range(h_needed, ab_remaining + 1)
    )
    return float(min(1.0, max(0.0, p_gte)))


# ---------------------------------------------------------------------------
# T4 band budget helpers (mirrors run_t4_live.py)
# ---------------------------------------------------------------------------


def _compute_t4_band_budget(portfolio: dict) -> float:
    return max(portfolio["bankroll_usd"] * T4_BAND_WEIGHT, 0.0)


def _exit_budget_credit(size_usd: float, exit_pnl: float) -> float:
    return size_usd + min(0.0, exit_pnl)


def _reconstruct_t4_ledger(portfolio: dict, game_date: str) -> float:
    open_exposure = sum(
        p.get("size_usd", 0.0)
        for p in portfolio.get("open_positions", [])
        if p.get("pool_isolated") and p.get("game_date") == game_date
    )
    realized_losses = sum(
        max(0.0, -p.get("exit_pnl", 0.0))
        for p in portfolio.get("closed_positions", [])
        if p.get("pool_isolated") and p.get("game_date") == game_date
    )
    return open_exposure + realized_losses


# ---------------------------------------------------------------------------
# Evaluation cycle
# ---------------------------------------------------------------------------


def _run_cycle(
    cycle_id: str,
    session_id: str,
    live_states: list[MLBLiveBatterState],
    live_prices: dict[str, object],
    pregame_by_player_id: dict[int, list[dict]],
    engine: RiskEngine,
    trader: PaperTrader,
    store: StagedOrderStore,
    audit: AuditLogger,
    game_date: str,
    t4_band_budget: float,
    t4_deployed_usd: float,
    batting_slots: Optional[dict[int, int]] = None,
    dry_run: bool = False,
    dryrun_log_path: Optional[Path] = None,
) -> tuple[int, int, float]:
    """
    Run one T4 MLB evaluation cycle.

    Returns (evaluated, fired, updated_t4_deployed_usd).
    """
    evaluated = 0
    fired = 0
    fired_tickers: set[str] = set()
    _slots = batting_slots or {}

    state_by_id = {ls.player_id: ls for ls in live_states}

    portfolio = trader.get_state()
    current_daily_loss = portfolio.get("current_daily_loss", 0.0)
    if portfolio.get("daily_loss_date", "") != date.today().isoformat():
        current_daily_loss = 0.0
    initial_bankroll = portfolio.get("initial_bankroll_usd", portfolio["bankroll_usd"])
    realized_loss = max(0.0, -portfolio.get("total_realized_pnl", 0.0))
    drawdown = realized_loss / initial_bankroll if initial_bankroll > 0 else 0.0

    for player_id, market_ctxs in pregame_by_player_id.items():
        ls = state_by_id.get(player_id)
        if ls is None:
            continue   # player not in live boxscore this game

        ba_l10       = market_ctxs[0].get("ba_l10", 0.25)
        batting_slot = _slots.get(player_id, 0)
        ab_remaining = _compute_ab_remaining(ls.ab_so_far, ls.inning, batting_slot)

        for ctx in market_ctxs:
            ticker    = ctx["ticker"]
            threshold = int(ctx["threshold"])

            if ticker in fired_tickers:
                continue

            pm = live_prices.get(ticker)
            if pm is None or not getattr(pm, "has_live_quotes", False):
                continue

            mip = pm.mid_price
            vig = pm.vig
            if mip <= 0.0 or mip >= 1.0:
                continue

            p_t4 = p_hits_gte_threshold(
                h_so_far=ls.h_so_far,
                threshold=threshold,
                ba_l10=ba_l10,
                ab_remaining=ab_remaining,
            )

            gross_edge = p_t4 - mip - vig
            kalshi_fee = 0.07 * mip * (1.0 - mip)
            net_edge   = gross_edge - kalshi_fee

            if dry_run:
                if dryrun_log_path is not None:
                    _append_dryrun_record(dryrun_log_path, {
                        "ts":           datetime.now(timezone.utc).isoformat(),
                        "cycle_id":     cycle_id,
                        "session_id":   session_id,
                        "ticker":       ticker,
                        "player_name":  ctx["player_name"],
                        "player_id":    player_id,
                        "threshold":    threshold,
                        "p_t4":         round(p_t4, 6),
                        "mip":          round(mip, 6),
                        "vig":          round(vig, 6),
                        "gross_edge":   round(gross_edge, 6),
                        "net_edge":     round(net_edge, 6),
                        "ba_l10":       round(ba_l10, 6),
                        "h_so_far":     ls.h_so_far,
                        "ab_so_far":    ls.ab_so_far,
                        "ab_remaining": ab_remaining,
                        "inning":       ls.inning,
                        "batting_slot": batting_slot,
                        "would_fire":   net_edge > 0,
                    })
                evaluated += 1
                if net_edge > 0:
                    fired += 1
                    fired_tickers.add(ticker)
                    logger.info(
                        "T4-MLB DRY_RUN WOULD_FIRE  %-45s  p=%.3f  mip=%.3f  edge=%+.3f",
                        ticker, p_t4, mip, net_edge,
                    )
                continue

            # Normal execution path
            if gross_edge <= 0.0:
                evaluated += 1
                continue

            direction = "YES"

            fc_record = {
                "forecast_id":         f"T4-MLB-{cycle_id}-{ticker[-12:]}",
                "p_estimate":          p_t4,
                "market_implied_prob": mip,
                "edge":                net_edge,
                "gross_edge":          gross_edge,
                "recommended_direction": direction,
            }

            ok, approval = engine.evaluate_forecast(
                forecast_record=fc_record,
                current_daily_loss=current_daily_loss,
                current_drawdown_pct=drawdown,
                session_id=session_id,
                current_open_exposure_usd=t4_deployed_usd,
                portfolio_equity_usd=t4_band_budget,
                pool_isolated=True,
            )
            evaluated += 1

            if not ok:
                logger.error("C4/C6 write failure at %s — halting cycle", ticker)
                return evaluated, fired, t4_deployed_usd

            if approval.get("approval_status") != "APPROVED":
                continue

            # T4 paper policy: 1 contract at market price (mirrors NBA T4 ADR-0023)
            approved_size = mip
            approval = {**approval, "approved_size": approved_size,
                        "model_p": p_t4, "edge": net_edge, "gross_edge": gross_edge}

            if t4_deployed_usd + approved_size > t4_band_budget:
                logger.info(
                    "T4-MLB BAND_BUDGET_EXHAUSTED %-45s  remaining=$%.2f",
                    ticker, max(0.0, t4_band_budget - t4_deployed_usd),
                )
                continue

            valid_until = (datetime.now(timezone.utc) + timedelta(hours=4)).isoformat()
            try:
                order_id = store.stage_order(
                    market_id=ticker,
                    player_id=str(player_id),
                    threshold=float(threshold),
                    direction=direction,
                    strategy="A",
                    p_t1=ctx["p_t1"],
                    p_entry=mip,
                    kelly_fraction=KELLY_T4,
                    sized_amount_usd=approved_size,
                    valid_until_iso=valid_until,
                    notes=f"T4-MLB cycle={cycle_id}",
                )
            except Exception as exc:
                logger.warning("stage_order failed for %s: %s — skipping", ticker, exc)
                continue

            ok_pos, pos = trader.open_position(
                approval=approval,
                player_name=ctx["player_name"],
                player_id=int(player_id),
                kalshi_ticker=ticker,
                kalshi_threshold=int(threshold),
                mid_price=mip,
                vig=vig,
                game_date=game_date,
                session_id=session_id,
                pool_isolated=True,
            )
            if not ok_pos:
                logger.error("PaperTrader write failure at %s — halting cycle", ticker)
                return evaluated, fired, t4_deployed_usd

            if pos:
                store.mark_fired(order_id)
                fired_tickers.add(ticker)
                fired += 1
                t4_deployed_usd += approved_size
                logger.info(
                    "T4-MLB FIRED  %-45s  %-3s  $%5.2f  p=%.3f  mip=%.3f  edge=%+.3f"
                    "  budget_used=$%.2f/%.2f  h=%d ab_rem=%d  cycle=%s",
                    ticker, direction, approved_size, p_t4, mip, net_edge,
                    t4_deployed_usd, t4_band_budget,
                    ls.h_so_far, ab_remaining, cycle_id,
                )

    return evaluated, fired, t4_deployed_usd


# ---------------------------------------------------------------------------
# Startup self-heal — crontab-timing-agnostic first-pitch wait
# ---------------------------------------------------------------------------


def _earliest_first_pitch_utc(today: date) -> "Optional[datetime]":
    """
    Fetch today's MLB schedule and return the earliest active game start (UTC).
    Returns None if all games are postponed/cancelled or if the API fails.
    """
    date_str = today.strftime("%m/%d/%Y")
    try:
        r = requests.get(
            _MLB_SCHEDULE_API,
            params={"sportId": _MLB_SPORT_ID, "date": date_str, "hydrate": "team"},
            timeout=10,
        )
        r.raise_for_status()
        dates = r.json().get("dates", [])
        if not dates:
            return None
        games = dates[0].get("games", [])
        starts: list[datetime] = []
        for g in games:
            state = g.get("status", {}).get("detailedState", "")
            if state in _NO_PLAY_STATES:
                continue
            gd = g.get("gameDate", "")
            if not gd:
                continue
            try:
                dt = datetime.fromisoformat(gd.replace("Z", "+00:00"))
                starts.append(dt)
            except ValueError:
                continue
        return min(starts) if starts else None
    except Exception as exc:
        logger.warning("MLB schedule API self-heal query failed: %s", exc)
        return None


def _startup_self_heal() -> None:
    """
    Make crontab firing time irrelevant: compute the correct T4 start from the
    live MLB schedule and sleep until first_pitch - 30min if cron fired us early.

    Cases handled:
      - PIPE-08 adjusted cron correctly: target already passed → start immediately.
      - Cron default fired early (e.g. 13:00 UTC, first pitch at 23:05 UTC): sleep ~9.5h.
      - VPS restart wiped PIPE-08 timing: cron default fires early, self-heal corrects.
      - All games postponed: start immediately (loop will idle gracefully).
      - MLB API unavailable: start immediately (failsafe).

    Kill switch is checked every 60 seconds during any wait.
    """
    now = datetime.now(timezone.utc)
    earliest = _earliest_first_pitch_utc(now.date())
    if earliest is None:
        logger.info("T4-MLB self-heal: no active games found — starting immediately")
        return

    target = earliest - timedelta(minutes=T4_STARTUP_BUFFER_MIN)
    if now >= target:
        logger.info(
            "T4-MLB self-heal: first pitch %s, target %s (now %s) — starting immediately",
            earliest.strftime("%H:%M UTC"), target.strftime("%H:%M UTC"),
            now.strftime("%H:%M UTC"),
        )
        return

    wait_s = (target - now).total_seconds()
    logger.info(
        "T4-MLB self-heal: first pitch %s → waiting until %s (%.0f min). Cron fired %s UTC.",
        earliest.strftime("%H:%M UTC"), target.strftime("%H:%M UTC"),
        wait_s / 60, now.strftime("%H:%M UTC"),
    )

    while True:
        now = datetime.now(timezone.utc)
        remaining = (target - now).total_seconds()
        if remaining <= 0:
            logger.info("T4-MLB self-heal: wait complete — entering eval loop")
            return
        if kill_switch_armed(KILL_SWITCH_PATH):
            logger.warning("T4-MLB kill switch armed during self-heal wait — exiting")
            sys.exit(0)
        time.sleep(min(60.0, remaining))


# ---------------------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------------------


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)-8s %(message)s",
    )

    session_id = f"{SESSION_ID_PREFIX}-{uuid.uuid4().hex[:8].upper()}"
    logger.info("=" * 60)
    logger.info("PIPE-07-MLB T4 Live  session=%s", session_id)
    logger.info("Kill switch: touch %s", KILL_SWITCH_PATH)
    logger.info("=" * 60)

    # Self-heal: compute correct start time from live MLB schedule regardless of
    # what time cron fired us. Crontab timing becomes irrelevant.
    _startup_self_heal()

    # Dry-run mode: compute all evaluations, log to JSONL, skip execution (T-202).
    if T4_MLB_DRY_RUN:
        dryrun_log_path: Optional[Path] = (
            _LOGS_DIR / f"t4_mlb_dryrun_{date.today().strftime('%Y%m%d')}.jsonl"
        )
        logger.info("=" * 60)
        logger.info("T4-MLB DRY-RUN MODE — no positions will be opened")
        logger.info("Dry-run log: %s", dryrun_log_path)
        logger.info("=" * 60)
    else:
        dryrun_log_path = None

    # ---- Load pregame context ----
    by_player_id, _by_ticker, name_to_pregame = _load_pregame_context()
    if not by_player_id:
        logger.warning(
            "No MLB pregame context found in %s — run PIPE-06pre first. "
            "Will retry discovery in loop.", _LOGS_DIR,
        )

    # ---- Load T2 batting slots (optional; improves ab_remaining accuracy) ----
    batting_slots = _load_t2_batting_slots()

    game_date = date.today().isoformat()

    # ---- Initialize components (once per session) ----
    audit  = AuditLogger(log_path=_AUDIT_LOG_PATH)
    store  = StagedOrderStore(_STAGED_DB_PATH)
    trader = PaperTrader(portfolio_path=_PORTFOLIO_PATH, logger=audit)
    kalshi = KalshiMarketClient.from_env()

    # ---- T4 band budget ----
    t4_state = trader.get_state()
    t4_band_budget = _compute_t4_band_budget(t4_state)
    t4_deployed_game = _reconstruct_t4_ledger(t4_state, game_date)
    if t4_deployed_game > 0.0:
        logger.info(
            "T4-MLB ledger reconstructed: $%.2f already deployed for %s",
            t4_deployed_game, game_date,
        )
    logger.info(
        "T4-MLB band budget: $%.2f  (pool=$%.2f × T4_BAND_WEIGHT=%.2f  ADR-0023)",
        t4_band_budget, t4_state["bankroll_usd"], T4_BAND_WEIGHT,
    )

    def _make_engine(t4_band_budget: float) -> RiskEngine:
        state = trader.get_state()
        ibr = state.get("initial_bankroll_usd", state["bankroll_usd"])
        return RiskEngine(
            logger=audit,
            snapshot_id=SNAPSHOT_ID,
            bankroll=t4_band_budget,
            kelly_fraction=KELLY_T4,
            initial_bankroll=ibr,
            min_bet_usd=MIN_BET_T4_PAPER,
        )

    # ---- Game ID discovery ----
    game_ids: list[str] = _espn_mlb_game_ids_today()
    logger.info("Initial MLB game IDs: %s", game_ids or "(none yet)")

    # ---- Main polling loop ----
    cycle_n = 0
    total_evaluated = 0
    total_fired = 0

    while True:
        if kill_switch_armed(KILL_SWITCH_PATH):
            logger.warning(
                "T4-MLB kill switch armed — sleeping 10s. rm %s to resume.",
                KILL_SWITCH_PATH,
            )
            time.sleep(10)
            continue

        try:
            # Re-discover games if we have none yet
            if not game_ids:
                game_ids[:] = _espn_mlb_game_ids_today()
                if game_ids:
                    logger.info("MLB game(s) discovered: %s", game_ids)
                else:
                    logger.debug("No active MLB games found — sleeping 60s")
                    time.sleep(60)
                    continue

            # Reload pregame context if empty (in case PIPE-06pre ran after T4 started)
            if not by_player_id:
                by_player_id_new, _bt, name_to_pregame_new = _load_pregame_context()
                if by_player_id_new:
                    by_player_id.update(by_player_id_new)
                    name_to_pregame.update(name_to_pregame_new)
                    logger.info("Pregame context loaded on retry: %d players", len(by_player_id))

            # Poll all tracked games via ESPN — kill switch checked per game (NFR-03 ≤60s halt)
            all_states: list[MLBLiveBatterState] = []
            _ks_fired = False
            for gid in game_ids:
                if kill_switch_armed(KILL_SWITCH_PATH):
                    _ks_fired = True
                    break
                all_states.extend(_espn_poll_once_mlb(gid, name_to_pregame))
            if _ks_fired:
                continue  # outer loop re-checks kill switch immediately

            if not all_states:
                logger.info("No live MLB batter states — sleeping 60s.")
                time.sleep(60)
                continue

            # Fetch live KXMLBHIT prices from Kalshi
            ok, snapshot = kalshi.fetch_player_points_markets(series_ticker=SERIES_MLB_PLAYER_HITS)
            if not ok or not snapshot.markets:
                logger.warning(
                    "Kalshi MLB price fetch failed — sleeping %ds", POLL_INTERVAL_S
                )
                time.sleep(POLL_INTERVAL_S)
                continue

            live_prices = {m.ticker: m for m in snapshot.markets}

            engine_t4 = _make_engine(t4_band_budget)
            cycle_id = f"C{cycle_n:04d}-{uuid.uuid4().hex[:6]}"

            ev, fi, t4_deployed_game = _run_cycle(
                cycle_id=cycle_id,
                session_id=session_id,
                live_states=all_states,
                live_prices=live_prices,
                pregame_by_player_id=by_player_id,
                engine=engine_t4,
                trader=trader,
                store=store,
                audit=audit,
                game_date=game_date,
                t4_band_budget=t4_band_budget,
                t4_deployed_usd=t4_deployed_game,
                batting_slots=batting_slots,
                dry_run=T4_MLB_DRY_RUN,
                dryrun_log_path=dryrun_log_path,
            )

            cycle_n += 1
            total_evaluated += ev
            total_fired += fi

            budget_pct = (
                t4_deployed_game / t4_band_budget * 100.0
            ) if t4_band_budget > 0 else 0.0
            logger.info(
                "─ cycle=%s  eval=%d fired=%d │ session: eval=%d fired=%d"
                " │ T4_budget: $%.2f/$%.2f (%.0f%%)  │ bankroll=$%.2f",
                cycle_id, ev, fi,
                total_evaluated, total_fired,
                t4_deployed_game, t4_band_budget, budget_pct,
                trader.get_state()["bankroll_usd"],
            )

            time.sleep(POLL_INTERVAL_S)

        except Exception as exc:
            logger.error(
                "Unhandled exception in T4-MLB main loop — sleeping %ds: %s",
                POLL_INTERVAL_S, exc, exc_info=True,
            )
            time.sleep(POLL_INTERVAL_S)


if __name__ == "__main__":
    main()
