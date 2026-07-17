"""
PIPE-05.5: MLB T2 Same-Day Batting Lineup Overlay
===================================================
Pipeline:     PIPE-05.5 (MLB T2 same-day overlay)
Band:         T2_SAME_DAY (ExecutionBand)
Phase:        Phase 6 (ENV-02 — paper trading)
Schedule:     Cron: 19:30 UTC (3:30pm ET) — after most evening-game lineups posted.
              Afternoon games (first pitch <19:30 UTC) are skipped by the per-game
              contamination guard.

What T2 adds over T1 (PIPE-05 at 11:00 UTC):
  1. Lineup confirmation — player NOT in today's confirmed batting lineup (scratch /
     benched) is SKIPPED. T1 has no confirmed lineup data at 11:00 UTC.
  2. Batting order adjustment — today's confirmed batting slot determines expected
     plate appearances. Top-of-order (slots 1-3) get more ABs; bottom-order (slots
     7-9) get fewer. T2 applies a Binomial adjustment to p_t1 using today's slot.

Data source (DS-04 MLB): MLB Stats API schedule endpoint with hydrate=lineups,team.
  Accessible from VPS for current season (2026); historical seasons 406 from DO/Fastly.
  See 03_DECISIONS/DS-04_mlb-t2-lineup-source.md.

Pool: paper_portfolio_mlb.json (shared with T1/PIPE-05 — both are pre-game bets).
  PaperTrader idempotency guard blocks re-entry on tickers where T1 already has an
  open position. T2 provides coverage on tickers where T1 PASSED (insufficient edge)
  but T2's lineup adjustment creates edge. Does NOT re-bet tickers already open.

Per-game contamination guard: skips players in games already Live at run time. This
  differs from T1's global guard — T2 checks per game_pk so afternoon game scratches
  don't block evening game bets.

Security: BOT_ENV=paper required. No real capital.
How to run:
  source /opt/prediction-market-bot/.env
  BOT_ENV=paper PYTHONPATH=src /opt/prediction-market-bot/venv/bin/python \\
      src/prediction_market_bot/run_t2_mlb_sameday.py
"""

from __future__ import annotations

import json
import os
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import requests

_SRC_ROOT = Path(__file__).parent.parent.parent
if str(_SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(_SRC_ROOT))

if os.environ.get("BOT_ENV", "").lower() != "paper":
    print(
        "FATAL: PIPE-05.5 requires BOT_ENV=paper. Set BOT_ENV=paper in your .env.",
        file=sys.stderr,
    )
    sys.exit(1)

os.environ["BOT_C4_ACTIVE"] = "true"

from prediction_market_bot.c1_signal_ingestion.mlb_ingestion import MLBIngestionClient
from prediction_market_bot.c3_forecasting.calibration import calibrate_probability
from prediction_market_bot.c4_risk_engine.risk import RiskEngine
from prediction_market_bot.c5_execution.kalshi_client import (
    KalshiMarketClient,
    SERIES_MLB_PLAYER_HITS,
)
from prediction_market_bot.c5_execution.market_mapper import normalize_player_name
from prediction_market_bot.c5_execution.paper_trader import PaperTrader
from prediction_market_bot.c6_audit_logger.audit_logger import AuditLogger
from prediction_market_bot.execution_bands import ExecutionBand, get_band_config

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

COMPONENT  = "PIPE-05.5-MLB"
BAND       = ExecutionBand.T2_SAME_DAY
BAND_CFG   = get_band_config(BAND)
SESSION_ID = f"T2-MLB-{uuid.uuid4().hex[:8].upper()}"
NOW_UTC    = datetime.now(tz=timezone.utc)
GAME_DATE  = NOW_UTC.strftime("%Y%m%d")
GAME_DATE_ISO = NOW_UTC.strftime("%Y-%m-%d")
RUN_TIME   = NOW_UTC.strftime("%H%M")

LOG_DIR        = Path(os.environ.get("LOG_DIR", str(_SRC_ROOT / "logs")))
PORTFOLIO_PATH = LOG_DIR / "paper_portfolio_mlb.json"
REPORT_PATH    = LOG_DIR / f"t2_mlb_{GAME_DATE}_{RUN_TIME}.json"
AUDIT_LOG_PATH = LOG_DIR / "audit_mlb.jsonl"

EDGE_YES  = float(os.environ.get("MLB_T2_EDGE_YES", "0.02"))
PAPER_YES_ONLY = os.environ.get("MLB_PAPER_YES_ONLY", "true").lower() == "true"
RESERVE_MANDATE_PCT = float(os.environ.get("RESERVE_MANDATE_PCT", "0.40"))
MIN_BET_PAPER = float(os.environ.get("MIN_BET_MLB_PAPER", "1.0"))

T2_KELLY = BAND_CFG.kelly_fraction

_MODEL_THRESHOLDS: frozenset[int] = frozenset({1, 2})

# Confirmed batting-slot → expected ABs per game (empirical MLB averages)
_AB_BY_SLOT: dict[int, float] = {
    1: 4.2, 2: 4.1, 3: 4.0, 4: 3.9, 5: 3.7,
    6: 3.6, 7: 3.4, 8: 3.2, 9: 3.1,
}
_AB_DEFAULT = 3.7   # population baseline used in T1 model (AB_PER_GAME_DEFAULT)

_MLB_SCHEDULE_URL = "https://statsapi.mlb.com/api/v1/schedule"
SNAPSHOT_ID = "SNAP-MLB-T2"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _utc_now() -> str:
    return datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


def _load_pregame_context() -> tuple[list[dict], Path | None]:
    """Load the most recent pregame_mlb_*.json produced by PIPE-06pre."""
    jsons = sorted(LOG_DIR.glob("pregame_mlb_*.json"), reverse=True)
    if not jsons:
        return [], None
    path = jsons[0]
    report = json.loads(path.read_text())
    return report.get("forecasts", []), path


def _slot_adjust(
    p_t1: float,
    ba_l10: float | None,
    batting_slot: int,
    threshold: int,
) -> float:
    """Apply Binomial batting-slot adjustment to T1 probability.

    Computes ratio of P(H >= threshold | ab_adj) / P(H >= threshold | ab_default)
    using the Binomial model with the player's L10 batting average.
    Caps adjustment at ±15% to prevent extreme movement.
    """
    if ba_l10 is None or ba_l10 <= 0.0 or ba_l10 >= 1.0:
        return p_t1

    ab_adj = _AB_BY_SLOT.get(batting_slot, _AB_DEFAULT)
    q = 1.0 - ba_l10

    if threshold == 1:
        p_adj  = 1.0 - q ** ab_adj
        p_base = 1.0 - q ** _AB_DEFAULT
    elif threshold == 2:
        # P(H >= 2) = 1 - P(H=0) - P(H=1) using Binomial approximation
        p_adj  = 1.0 - q**ab_adj - ab_adj * ba_l10 * q**(ab_adj - 1)
        p_base = 1.0 - q**_AB_DEFAULT - _AB_DEFAULT * ba_l10 * q**(_AB_DEFAULT - 1)
    else:
        return p_t1

    if p_base <= 0.0:
        return p_t1

    ratio = max(0.85, min(1.15, p_adj / p_base))
    return float(np.clip(p_t1 * ratio, 0.01, 0.99))


def _fetch_live_game_pks(
    game_date: str,
    logger: AuditLogger | None = None,
    session_id: str | None = None,
) -> set[int]:
    """Return set of game_pks that are currently Live for game_date.

    Returns empty set on API failure (permissive — treats all games as not-live
    but logs a WARNING via C6 if logger is provided so failures are visible).
    """
    try:
        resp = requests.get(
            _MLB_SCHEDULE_URL,
            params={"sportId": 1, "date": game_date},
            timeout=10,
        )
        resp.raise_for_status()
        live: set[int] = set()
        for date_block in resp.json().get("dates", []):
            for game in date_block.get("games", []):
                state = game.get("status", {}).get("abstractGameState", "")
                if state == "Live":
                    pk = game.get("gamePk")
                    if pk is not None:
                        live.add(int(pk))
        return live
    except Exception as exc:
        if logger is not None:
            logger.warning(
                COMPONENT, "mlb_schedule_api_failed",
                payload={"game_date": game_date, "error": str(exc)},
                session_id=session_id,
            )
        return set()


def _write_report(
    forecasts: list[dict],
    bets: list[dict],
    scratches: int,
    live_skips: int,
    players_not_in_lineup: int,
    session_id: str,
    t1_path: str = "",
    reason: str = "",
) -> None:
    report = {
        "session_id":       session_id,
        "band":             BAND.value,
        "game_date":        GAME_DATE,
        "sport":            "mlb",
        "run_at":           _utc_now(),
        "t1_path":          t1_path,
        "reason":           reason,
        "t2_evaluated":     len(forecasts),
        "scratches":        scratches,
        "live_game_skips":  live_skips,
        "lineup_misses":    players_not_in_lineup,
        "bets_placed":      len(bets),
        "forecasts":        forecasts,
        "bets":             bets,
    }
    REPORT_PATH.write_text(json.dumps(report, indent=2))


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    logger = AuditLogger(AUDIT_LOG_PATH, min_severity="INFO")
    # T-213/GG-060 edge-decision classification sink (T2 parity with T1/T4) —
    # see risk.summarize_edge_run(). Without this, a 0-bet T2 run is
    # indistinguishable between "no edge today" and "pipeline silently died."
    #
    # CAVEAT (found T-375, verified against real 2026-07-16 T2 production
    # output where 4/4 forecasts were PASS): T2 applies its own EDGE_YES
    # pre-filter (`direction = "YES" if net_edge > EDGE_YES else "PASS"`,
    # below) BEFORE calling engine.evaluate_forecast() — only non-PASS
    # forecasts reach C4 and get an edge_decision record. A legitimate day
    # where every forecast is PASS at T2's own pre-filter will show
    # total_evaluations=0 in summarize_edge_run(), which that function
    # classifies as PIPELINE_BROKEN — a false positive for T2 specifically.
    # T1 and T4 do not have this gap (they send every forecast to C4 and let
    # C4's own edge_signal determine accept/reject). Do not treat T2's
    # total_evaluations==0 as pipeline failure without first checking
    # t2_evaluated in the run's own report JSON. Flagged, not fixed here —
    # widening the sink to also cover T2's pre-filter PASS population is a
    # scope decision for Earl, not made unilaterally in this pass.
    edge_logger = AuditLogger(LOG_DIR / "audit_mlb_t2_edge_decisions.jsonl", min_severity="INFO")

    print(f"\n[PIPE-05.5-MLB T2] MLB same-day lineup overlay — {GAME_DATE} {RUN_TIME}Z")
    print(f"Session: {SESSION_ID}")
    print(f"Band:    {BAND.value} | Kelly: {T2_KELLY} | YES-only: {PAPER_YES_ONLY}")

    logger.info(COMPONENT, "t2_mlb_start",
                payload={"session_id": SESSION_ID, "game_date": GAME_DATE,
                         "band": BAND.value, "yes_only": PAPER_YES_ONLY},
                session_id=SESSION_ID)

    # ------------------------------------------------------------------
    # 1. Load T1 pregame context
    # ------------------------------------------------------------------
    all_forecasts, t1_path = _load_pregame_context()

    if t1_path is None:
        print(f"[T2-MLB] No pregame_mlb_*.json in {LOG_DIR} — PIPE-06pre not run. Exiting.")
        _write_report([], [], 0, 0, 0, SESSION_ID, reason="no_pregame_file")
        sys.exit(0)

    actionable = [f for f in all_forecasts if f.get("direction") != "PASS"]
    print(f"[T1-MLB] Loaded {len(all_forecasts)} forecasts from {t1_path.name} "
          f"| {len(actionable)} actionable")

    if not actionable:
        print("[T2-MLB] No actionable T1 forecasts. Exiting.")
        _write_report([], [], 0, 0, 0, SESSION_ID, t1_path=str(t1_path),
                      reason="no_actionable_t1")
        sys.exit(0)

    # ------------------------------------------------------------------
    # 2. Fetch confirmed batting lineups (DS-04 MLB)
    # ------------------------------------------------------------------
    print(f"[DS-04] Fetching MLB batting lineups for {GAME_DATE_ISO}...")
    mlb_client = MLBIngestionClient(
        logger=logger,
        snapshot_id=SNAPSHOT_ID,
    )
    ok_lineups, lineup_by_pid = mlb_client.fetch_lineups(GAME_DATE_ISO, SESSION_ID)
    if not ok_lineups:
        print("[T2-MLB] WARNING: Lineup fetch failed. Proceeding without lineup data "
              "(T1 edge only — no SCRATCH filter).")
        logger.warning(COMPONENT, "t2_mlb_lineup_fetch_failed",
                       payload={"game_date": GAME_DATE_ISO}, session_id=SESSION_ID)
        lineup_by_pid = {}
    else:
        print(f"  {len(lineup_by_pid)} players in confirmed lineups")

    # ------------------------------------------------------------------
    # 3. Fetch live game statuses (per-game contamination guard)
    # ------------------------------------------------------------------
    print("[DS-01] Checking live game statuses...")
    live_game_pks = _fetch_live_game_pks(GAME_DATE_ISO, logger=logger, session_id=SESSION_ID)
    if live_game_pks:
        print(f"  {len(live_game_pks)} game(s) already Live — players in those games skipped")
    else:
        print("  No games currently Live — T2 window is clean")

    # ------------------------------------------------------------------
    # 4. Fetch live KXMLBHIT prices
    # ------------------------------------------------------------------
    print("[DS-02] Fetching live KXMLBHIT prices from Kalshi...")
    try:
        kalshi = KalshiMarketClient.from_env()
        ok, status = kalshi.check_connectivity()
        if not ok:
            print(f"ERROR: DS-02 connectivity failed: {status}", file=sys.stderr)
            sys.exit(1)

        ok2, snapshot = kalshi.fetch_player_points_markets(series_ticker=SERIES_MLB_PLAYER_HITS)
        if not ok2 or not snapshot.markets:
            print("[T2-MLB] No KXMLBHIT markets available. Exiting.")
            _write_report([], [], 0, 0, 0, SESSION_ID, t1_path=str(t1_path),
                          reason="no_live_markets")
            sys.exit(0)

        live_by_ticker = {m.ticker: m for m in snapshot.markets if m.has_live_quotes}
        print(f"  {len(snapshot.markets)} markets | {len(live_by_ticker)} with live quotes")

    except EnvironmentError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)

    # ------------------------------------------------------------------
    # 5. Init PaperTrader (shared pool with T1)
    # ------------------------------------------------------------------
    trader = PaperTrader(portfolio_path=PORTFOLIO_PATH, logger=logger)
    trader.ensure_persisted()

    state = trader.get_state()
    bankroll = state["bankroll_usd"]
    _initial_bankroll = state.get("initial_bankroll_usd", 1000.0)
    _realized_loss = max(0.0, -state.get("total_realized_pnl", 0.0))
    current_drawdown_pct = _realized_loss / _initial_bankroll if _initial_bankroll > 0 else 0.0
    daily_loss = state.get("current_daily_loss", 0.0)

    print(f"[PORTFOLIO] Bankroll: ${bankroll:.2f} | "
          f"Drawdown: {current_drawdown_pct:.1%} | "
          f"Daily loss: ${daily_loss:.2f}")

    reserve_floor = RESERVE_MANDATE_PCT * _initial_bankroll
    engine = RiskEngine(
        logger=logger,
        snapshot_id=SNAPSHOT_ID,
        bankroll=bankroll,
        kelly_fraction=T2_KELLY,
        initial_bankroll=_initial_bankroll,
        min_bet_usd=MIN_BET_PAPER,
        edge_logger=edge_logger,
    )

    # Open tickers for idempotency guard
    open_tickers = {p["kalshi_ticker"] for p in state.get("open_positions", [])}

    # ------------------------------------------------------------------
    # 6. T2 evaluation loop
    # ------------------------------------------------------------------
    t2_results: list[dict] = []
    bets: list[dict] = []
    scratches = 0
    live_skips = 0
    lineup_misses = 0
    _reserve_halted = False

    for fc in actionable:
        if _reserve_halted:
            break

        ticker     = fc.get("kalshi_ticker", "")
        threshold  = int(fc.get("kalshi_threshold", 1))
        player     = fc.get("player_name", "")
        player_id  = fc.get("player_id")
        ba_l10     = fc.get("ba_l10")
        p_t1       = float(fc.get("p_estimate", 0.5))
        t1_dir     = fc.get("direction", "PASS")

        if threshold not in _MODEL_THRESHOLDS:
            continue

        # Idempotency guard: T1 already has an open position on this ticker
        if ticker in open_tickers:
            print(f"  [IDEMPOTENCY] SKIP {player:<26} H≥{threshold} — T1 already open")
            continue

        current_mkt = live_by_ticker.get(ticker)
        if current_mkt is None:
            continue

        # Per-game contamination guard
        lineup_entry = lineup_by_pid.get(int(player_id)) if player_id is not None else None
        if lineup_by_pid:  # only filter if lineup data was successfully fetched
            if lineup_entry is None:
                scratches += 1
                logger.info(COMPONENT, "t2_mlb_scratch",
                            payload={"player": player, "ticker": ticker},
                            session_id=SESSION_ID)
                print(f"  [SCRATCH] {player:<26} H≥{threshold} — not in confirmed lineup")
                continue

            game_pk = lineup_entry.get("game_pk")
            if game_pk is not None and int(game_pk) in live_game_pks:
                live_skips += 1
                logger.info(COMPONENT, "t2_mlb_live_game_skip",
                            payload={"player": player, "ticker": ticker, "game_pk": game_pk},
                            session_id=SESSION_ID)
                print(f"  [LIVE SKIP] {player:<26} H≥{threshold} — game {game_pk} in progress")
                continue

        # Batting-slot adjustment
        batting_slot = lineup_entry.get("batting_slot") if lineup_entry else None
        if batting_slot is not None:
            p_t2 = _slot_adjust(p_t1, ba_l10, int(batting_slot), threshold)
        else:
            p_t2 = p_t1

        # Re-compute edge with live Kalshi price
        mid = current_mkt.mid_price
        vig = current_mkt.vig
        half_spread = current_mkt.half_spread
        if mid <= 0.0 or mid >= 1.0:
            continue

        p_calibrated = calibrate_probability(p_t2, sport="mlb")
        # GG-122/APR-0028: cost term is the one-sided transaction cost
        # (half_spread = vig / 2.0), matching run_exp017.py's symmetric-cost
        # convention and T1's own formula (run_mlb_paper_trade.py). `vig`
        # itself is kept (unused in this computation) only because it is
        # still passed to open_position() below for recordkeeping.
        gross_edge = p_calibrated - mid - half_spread
        kalshi_fee = 0.07 * mid * (1.0 - mid)
        net_edge   = gross_edge - kalshi_fee

        direction = "YES" if net_edge > EDGE_YES else "PASS"

        if PAPER_YES_ONLY and direction != "YES":
            lineup_misses += 0  # not a lineup miss — edge insufficient
            result_rec = {
                "player_name":  player,
                "player_id":    player_id,
                "ticker":       ticker,
                "threshold":    threshold,
                "batting_slot": batting_slot,
                "p_t1":         round(p_t1, 4),
                "p_t2":         round(p_calibrated, 4),
                "mid_price":    round(mid, 4),
                "net_edge":     round(net_edge, 4),
                "direction":    "PASS",
                "outcome":      "PASS_NO_EDGE",
                "forecast_at":  _utc_now(),
            }
            t2_results.append(result_rec)
            print(f"  [PASS] {player:<26} H≥{threshold}  "
                  f"p_t2={p_calibrated:.3f}  mid={mid:.3f}  edge={net_edge:+.3f}")
            continue

        if direction == "PASS":
            result_rec = {
                "player_name":  player,
                "player_id":    player_id,
                "ticker":       ticker,
                "threshold":    threshold,
                "batting_slot": batting_slot,
                "p_t1":         round(p_t1, 4),
                "p_t2":         round(p_calibrated, 4),
                "mid_price":    round(mid, 4),
                "net_edge":     round(net_edge, 4),
                "direction":    "PASS",
                "outcome":      "PASS_NO_EDGE",
                "forecast_at":  _utc_now(),
            }
            t2_results.append(result_rec)
            continue

        # Run C4 RiskEngine
        forecast_rec = {
            "forecast_id":            f"T2-MLB-{uuid.uuid4().hex[:8].upper()}",
            "p_estimate":             p_calibrated,
            "market_implied_prob":    mid,
            "gross_edge":             round(gross_edge, 6),
            "kalshi_fee":             round(kalshi_fee, 6),
            "edge":                   round(net_edge, 6),
            "recommended_direction":  direction,
            "threshold":              threshold,
            "sport":                  "mlb",
        }

        _exp = trader.exposure_snapshot()
        ok_c4, approval = engine.evaluate_forecast(
            forecast_record=forecast_rec,
            current_daily_loss=daily_loss,
            current_drawdown_pct=current_drawdown_pct,
            session_id=SESSION_ID,
            current_open_exposure_usd=_exp["open_exposure_usd"],
            portfolio_equity_usd=_exp["equity_usd"],
        )

        c4_status = approval.get("approval_status", "UNKNOWN")

        if c4_status == "KILL_SWITCH":
            logger.critical(COMPONENT, "kill_switch_from_c4",
                            payload=approval, session_id=SESSION_ID)
            print("  KILL SWITCH triggered by C4 — halting PIPE-05.5.", file=sys.stderr)
            sys.exit(1)

        outcome = c4_status
        if c4_status == "APPROVED":
            approved_size = approval.get("approved_size", 0)

            if bankroll - approved_size < reserve_floor:
                print(f"  [RESERVE GATE] BATCH HALT — "
                      f"${bankroll:.2f} - ${approved_size:.2f} < ${reserve_floor:.2f} floor.")
                logger.warning(COMPONENT, "reserve_mandate_batch_halt",
                               payload={"bankroll": bankroll, "proposed_size": approved_size,
                                        "reserve_floor": reserve_floor, "ticker": ticker},
                               session_id=SESSION_ID)
                _reserve_halted = True
                outcome = "RESERVE_HALT"
            else:
                approval = {
                    **approval,
                    "model_p":    p_calibrated,
                    "edge":       net_edge,
                    "gross_edge": gross_edge,
                    "band":       "T2",  # T-253
                }
                ok_pos, pos = trader.open_position(
                    approval=approval,
                    player_name=player,
                    player_id=int(player_id) if player_id is not None else 0,
                    kalshi_ticker=ticker,
                    kalshi_threshold=threshold,
                    mid_price=mid,
                    vig=vig,
                    game_date=GAME_DATE_ISO,
                    session_id=SESSION_ID,
                )
                print(f"  BET  {player:<26} YES  ${approved_size:.2f}  "
                      f"p_t1={p_t1:.3f}→p_t2={p_calibrated:.3f}  "
                      f"edge={net_edge:+.3f}  H≥{threshold}  slot={batting_slot}")
                if pos:
                    bets.append(pos)
                    open_tickers.add(ticker)
                    _state = trader.get_state()
                    bankroll = _state["bankroll_usd"]
                    _initial_bankroll = _state.get("initial_bankroll_usd", 1000.0)
                    _realized_loss = max(0.0, -_state.get("total_realized_pnl", 0.0))
                    current_drawdown_pct = (
                        _realized_loss / _initial_bankroll if _initial_bankroll > 0 else 0.0
                    )
                    daily_loss = _state.get("current_daily_loss", 0.0)
                    engine = RiskEngine(
                        logger=logger,
                        snapshot_id=SNAPSHOT_ID,
                        bankroll=bankroll,
                        kelly_fraction=T2_KELLY,
                        initial_bankroll=_initial_bankroll,
                        min_bet_usd=MIN_BET_PAPER,
                        edge_logger=edge_logger,
                    )

        result_rec = {
            "player_name":  player,
            "player_id":    player_id,
            "ticker":       ticker,
            "threshold":    threshold,
            "batting_slot": batting_slot,
            "p_t1":         round(p_t1, 4),
            "p_t2":         round(p_calibrated, 4),
            "mid_price":    round(mid, 4),
            "net_edge":     round(net_edge, 4),
            "direction":    direction,
            "c4_status":    c4_status,
            "outcome":      outcome,
            "forecast_at":  _utc_now(),
        }
        t2_results.append(result_rec)

        logger.info(COMPONENT, "t2_mlb_forecast",
                    payload={k: v for k, v in result_rec.items() if k != "forecast_at"},
                    session_id=SESSION_ID)

    # ------------------------------------------------------------------
    # 7. Write report
    # ------------------------------------------------------------------
    _write_report(
        forecasts=t2_results,
        bets=bets,
        scratches=scratches,
        live_skips=live_skips,
        players_not_in_lineup=lineup_misses,
        session_id=SESSION_ID,
        t1_path=str(t1_path),
    )

    print(f"\n[DONE] T2-MLB: {len(bets)} bets | {scratches} scratches | "
          f"{live_skips} live-game skips | {len(t2_results)} evaluated | {REPORT_PATH}")

    logger.info(COMPONENT, "t2_mlb_complete",
                payload={"bets_placed": len(bets), "scratches": scratches,
                         "live_game_skips": live_skips,
                         "t2_evaluated": len(t2_results),
                         "output_path": str(REPORT_PATH)},
                session_id=SESSION_ID)


if __name__ == "__main__":
    main()
