"""
PIPE-05R: MLB Paper Position Resolution
=========================================
Pipeline:     PIPE-05R (Resolution-only; companion to PIPE-05)
Phase:        Phase 6 (ENV-02 — paper trading)
Schedule:     Cron: 06:30 UTC daily — after all MLB games finish
              (West Coast games end ~04:00–05:00 UTC; 90-min buffer)
Environment:  ENV-02 — BOT_ENV=paper required

Purpose:
  PIPE-05 places bets at 11:00 UTC. MLB games finish by ~04:00–05:00 UTC.
  This script runs at 06:30 UTC to resolve open MLB positions using the
  MLB Stats API (statsapi.mlb.com).

  Does NOT place new bets. Does NOT fetch live markets.
  Resolution-only: safe to run at any time without side effects.

Why separate from PIPE-05:
  Keeps resolution and bet-placement concerns clean. Each open position
  resolves exactly once (idempotent via settle_position() no-op guard).

VPS accessibility:
  CORRECTED 2026-07-05 (GG-084/T-239) — the prior claim here ("current season
  is reliably accessible from datacenter IP; only historical seasons 406") is
  FALSIFIED. Direct testing 2026-07-05 confirmed the datacenter IP (DigitalOcean
  157.230.91.33) received HTTP 406 on `gameLog` queries for the CURRENT (2026)
  season, on both gameType=R and gameType=P, for player/date combos that had
  resolved successfully from the same IP hours earlier — while the identical
  request from a residential IP returned HTTP 200 the entire time. This is an
  IP-based Fastly-CDN block/rate-limit that can escalate over the course of a
  run, not a historical-season-only restriction, and not request-parameter- or
  cadence-dependent. Treat datacenter-IP access to this endpoint as unreliable
  regardless of season. A circuit breaker (below) limits wasted retry time once
  the block is active; positions are never lost (48h grace + aged_open retry
  every subsequent run). See GG-084/GOVERNANCE_GAP_LOG.md.

  ESPN fallback (GG-084/T-241, added 2026-07-05): a live re-probe confirmed the
  block was still active hours after the circuit-breaker fix landed, meaning
  resolution could stall indefinitely rather than merely being delayed. When
  both MLB Stats API attempts (Regular + Postseason) return None,
  `fetch_actual_hits()` now falls back to ESPN's public site API
  (site.api.espn.com), which is unaffected by this block (different host/CDN)
  and is already used successfully in production by run_t4_mlb_live.py for
  live boxscores. Matches the batter by normalized display name against the
  position's stored `player_name`, and only trusts a game confirmed
  STATUS_FINAL/STATUS_POSTPONED. This closes the resolution gap without
  depending on the MLB Stats API IP block ever being lifted.

How to run:
  BOT_ENV=paper PYTHONPATH=src python3 src/prediction_market_bot/run_resolve_mlb.py

Season type handling:
  Regular season (gameType="R") is attempted first for all game dates.
  Postseason (gameType="P") is tried if Regular Season returns no result —
  mirrors NBA resolve_pending() Playoffs fallback pattern.
"""

from __future__ import annotations

import os
import sys
import time
import uuid
from datetime import date, datetime, timezone
from pathlib import Path

import requests

_SRC_ROOT = Path(__file__).parent.parent.parent
if str(_SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(_SRC_ROOT))

if os.environ.get("BOT_ENV", "").lower() != "paper":
    print("FATAL: PIPE-05R requires BOT_ENV=paper.", file=sys.stderr)
    sys.exit(1)

from prediction_market_bot.c5_execution.paper_trader import PaperTrader
from prediction_market_bot.c6_audit_logger.audit_logger import AuditLogger
from prediction_market_bot.c7_monitoring.monitor import (
    BRIER_BASELINE_MLB,
    ECE_BASELINE_MLB,
    SystemMonitor,
)
from typing import Any

SESSION_ID        = f"RESOLVE-MLB-{uuid.uuid4().hex[:8].upper()}"
GAME_DATE         = datetime.now(tz=timezone.utc).strftime("%Y%m%d")
LOG_DIR           = Path(os.environ.get("LOG_DIR", str(_SRC_ROOT / "logs")))
PORTFOLIO_PATH    = LOG_DIR / "paper_portfolio_mlb.json"
T4_PORTFOLIO_PATH = LOG_DIR / "paper_portfolio_mlb_t4.json"   # T-201: isolated T4 pool
SNAPSHOT_ID       = "SNAP-MLB-T187E"

_MLB_BASE_URL  = "https://statsapi.mlb.com"
_RATE_LIMIT_S  = 0.6   # matches mlb_ingestion.py; stays under API rate limit
_REQUEST_TIMEOUT_S = 15
_RETRY_DELAYS_S: tuple[int, ...] = (5, 10, 30)  # T-207: exponential backoff for 406 errors

# GG-084/T-241: ESPN fallback data source. When the MLB Stats API is IP-blocked
# (GG-084 — confirmed a sustained, not transient, condition), resolution would
# otherwise stall indefinitely (48h grace, then aged_open — no P&L visibility).
# ESPN's public site API is unaffected by the Fastly-CDN block (different host,
# different provider) and is already used successfully in production by
# run_t4_mlb_live.py for live boxscores. Constants/parsing convention mirrored
# from there (labels-based stat lookup, not a fixed index, since ESPN's finished-
# game boxscore label order — H-AB, AB, R, H, RBI, HR, BB, K — differs from the
# in-progress order documented in run_t4_mlb_live.py; label lookup is robust to
# either).
_ESPN_MLB_SCOREBOARD = "https://site.api.espn.com/apis/site/v2/sports/baseball/mlb/scoreboard"
_ESPN_MLB_SUMMARY    = "https://site.api.espn.com/apis/site/v2/sports/baseball/mlb/summary"
_ESPN_HEADERS        = {"User-Agent": "Mozilla/5.0"}
_ESPN_STATUS_FINAL     = "STATUS_FINAL"
_ESPN_STATUS_POSTPONED = "STATUS_POSTPONED"
_ESPN_TERMINAL_STATUSES = (_ESPN_STATUS_FINAL, _ESPN_STATUS_POSTPONED)

# GG-084/T-239: once the datacenter IP is hard-blocked (confirmed 2026-07-05 —
# a sustained condition, not per-request flakiness), every further retry-loop
# exhaustion burns up to 45s for nothing. After _CIRCUIT_BREAKER_THRESHOLD
# consecutive full exhaustions in this process, drop the retry/backoff
# schedule down to a single cheap attempt per call (half-open probe) instead
# of skipping the HTTP call outright — a full skip can never observe recovery
# since nothing would ever reach the reset line below.
#
# GG-089/T-242 (2026-07-06): the original design reset _consecutive_api_failures
# to 0 on ANY single call that got past raise_for_status(), which meant the
# breaker never actually tripped under a real sustained block — a block rarely
# fails 100% of individual calls, so one interleaved success (a different
# player_id/date happening to succeed) wiped out an accumulating failure streak
# before it reached _CIRCUIT_BREAKER_THRESHOLD. Fix: a single success no longer
# resets the failure count outright — it must be followed by
# _CONSECUTIVE_SUCCESSES_TO_RESET successes in a row (a sustained-recovery
# signal, not a lone lucky call) before the failure streak is cleared. Any
# failure immediately breaks a partial success streak, same as before.
_CIRCUIT_BREAKER_THRESHOLD = 5
_CONSECUTIVE_SUCCESSES_TO_RESET = 3
_consecutive_api_failures = 0
_consecutive_api_successes = 0


# ---------------------------------------------------------------------------
# MLB Stats API fetch
# ---------------------------------------------------------------------------

def _is_game_final(game_pk: int) -> bool:
    """GG-069 / T-221: confirm a game is actually over before trusting its box score.

    `gameLog` splits update live during a game, so a matching split can reflect
    a partial (mid-game) hit total. Queries the lightweight schedule-by-gamePk
    endpoint (not the full live-feed) and checks `status.abstractGameState`.
    Any failure (network error, missing field, unrecognized game_pk) returns
    False — the caller treats that identically to "no result yet," which is
    the safe default (position stays open, retried on the next cron run).
    """
    try:
        resp = requests.get(
            f"{_MLB_BASE_URL}/api/v1/schedule",
            params={"gamePk": game_pk},
            timeout=_REQUEST_TIMEOUT_S,
        )
        resp.raise_for_status()
        data = resp.json()
        game = data["dates"][0]["games"][0]
        return bool(game.get("status", {}).get("abstractGameState") == "Final")
    except Exception:
        return False


def _fetch_mlb_hits(
    player_id: int,
    game_date: str,
    game_type: str = "R",
) -> float | None:
    """Fetch actual hits for player_id on game_date from MLB Stats API.

    game_date: YYYY-MM-DD
    game_type: "R" (Regular) or "P" (Postseason)
    Returns hits as float, or None if game not found, not yet FINAL
    (GG-069/T-221), or API unreachable.

    GG-084/T-239: once the circuit breaker has tripped (see module-level
    constants above), the retry/backoff schedule collapses to a single
    cheap attempt per call — still probing every call for recovery, but
    without paying the up-to-45s full retry cost while the block is active.

    GG-089/T-242: the failure streak only clears after
    _CONSECUTIVE_SUCCESSES_TO_RESET calls in a row succeed, not on a single
    interleaved success — see module-level comment above the constants.
    """
    global _consecutive_api_failures, _consecutive_api_successes

    breaker_open = _consecutive_api_failures >= _CIRCUIT_BREAKER_THRESHOLD
    delays: tuple[int, ...] = () if breaker_open else _RETRY_DELAYS_S

    year = int(game_date[:4])
    url = f"{_MLB_BASE_URL}/api/v1/people/{player_id}/stats"
    params = {
        "stats":   "gameLog",
        "group":   "hitting",
        "season":  str(year),
        "gameType": game_type,
    }
    for attempt, delay in enumerate((*delays, None), start=1):
        try:
            time.sleep(_RATE_LIMIT_S)
            resp = requests.get(url, params=params, timeout=_REQUEST_TIMEOUT_S)
            resp.raise_for_status()
            _consecutive_api_successes += 1
            if _consecutive_api_successes >= _CONSECUTIVE_SUCCESSES_TO_RESET:
                _consecutive_api_failures = 0
                _consecutive_api_successes = 0
            data = resp.json()
            stats_arr = data.get("stats", [])
            if not stats_arr:
                return None
            splits = stats_arr[0].get("splits", [])
            for split in splits:
                if split.get("date", "") == game_date:
                    game_pk = split.get("game", {}).get("gamePk")
                    if game_pk is None or not _is_game_final(game_pk):
                        return None  # GG-069: not confirmed FINAL — do not resolve
                    return float(split.get("stat", {}).get("hits", 0))
            return None  # date not found in splits — not a transient error
        except Exception as exc:
            if delay is None:
                _consecutive_api_failures += 1
                _consecutive_api_successes = 0
                print(
                    f"  [MLB-API] player_id={player_id} game_date={game_date} "
                    f"game_type={game_type} attempt={attempt}/{len(delays)+1}: "
                    f"{type(exc).__name__}: {exc} — giving up "
                    f"(consecutive_failures={_consecutive_api_failures})"
                    + (" [circuit breaker open — single-probe attempt]" if breaker_open else ""),
                    file=sys.stderr,
                )
            else:
                print(
                    f"  [MLB-API] player_id={player_id} game_date={game_date} "
                    f"game_type={game_type} attempt={attempt}/{len(delays)+1}: "
                    f"{type(exc).__name__}: {exc} — retrying in {delay}s",
                    file=sys.stderr,
                )
                time.sleep(delay)
    return None


def _reset_circuit_breaker() -> None:
    """Test hook: reset the module-level consecutive-failure/success counters to 0."""
    global _consecutive_api_failures, _consecutive_api_successes
    _consecutive_api_failures = 0
    _consecutive_api_successes = 0


def _espn_game_ids_for_date(game_date: str) -> list[str]:
    """Return ESPN MLB event IDs for all games scheduled on game_date (YYYY-MM-DD).

    Unlike run_t4_mlb_live.py's `_espn_mlb_game_ids_today()` (always "today"),
    resolution needs an arbitrary past date, so this parameterizes `dates`.
    """
    try:
        date_str = datetime.strptime(game_date, "%Y-%m-%d").strftime("%Y%m%d")
        espn_params: dict[str, str | int] = {"dates": date_str, "limit": 30}
        resp = requests.get(
            _ESPN_MLB_SCOREBOARD,
            params=espn_params,
            headers=_ESPN_HEADERS,
            timeout=_REQUEST_TIMEOUT_S,
        )
        resp.raise_for_status()
        return [e["id"] for e in resp.json().get("events", [])]
    except Exception as exc:
        print(f"  [ESPN-FALLBACK] game_date={game_date}: scoreboard fetch failed: "
              f"{type(exc).__name__}: {exc}", file=sys.stderr)
        return []


def _espn_fetch_hits(player_name: str, game_date: str) -> float | None:
    """GG-084/T-241: fallback hit lookup via ESPN when MLB Stats API is blocked.

    Scans every ESPN game on game_date, matches the batter by normalized
    display name (same `lower().replace(" ", "")` convention as
    run_t4_mlb_live.py's pregame-context matching), and returns hits only from
    a game confirmed STATUS_FINAL/STATUS_POSTPONED — an in-progress or
    scheduled game's boxscore is not a resolvable result yet, so it is
    skipped rather than trusted.
    """
    norm_target = player_name.lower().replace(" ", "")
    if not norm_target:
        return None

    for game_id in _espn_game_ids_for_date(game_date):
        try:
            resp = requests.get(
                _ESPN_MLB_SUMMARY,
                params={"event": game_id},
                headers=_ESPN_HEADERS,
                timeout=_REQUEST_TIMEOUT_S,
            )
            resp.raise_for_status()
            data = resp.json()
        except Exception as exc:
            print(f"  [ESPN-FALLBACK] player={player_name} game_id={game_id}: "
                  f"summary fetch failed: {type(exc).__name__}: {exc}", file=sys.stderr)
            continue

        comps = data.get("header", {}).get("competitions", [{}])
        if not comps:
            continue
        status_name = comps[0].get("status", {}).get("type", {}).get("name", "")
        if status_name not in _ESPN_TERMINAL_STATUSES:
            continue  # not over yet — do not trust this game's boxscore

        for team_data in data.get("boxscore", {}).get("players", []):
            for stat_group in team_data.get("statistics", []):
                labels = stat_group.get("labels", [])
                if not labels or "AB" not in labels or "IP" in labels:
                    continue  # skip pitching stat group
                try:
                    h_idx = labels.index("H")
                except ValueError:
                    continue  # can't locate hits column — do not guess

                for athlete_entry in stat_group.get("athletes", []):
                    athlete = athlete_entry.get("athlete", {})
                    name = athlete.get("displayName", "")
                    if name.lower().replace(" ", "") != norm_target:
                        continue
                    stats = athlete_entry.get("stats", [])
                    try:
                        return float(stats[h_idx])
                    except (IndexError, ValueError, TypeError):
                        return None
    return None


def fetch_actual_hits(
    player_id: int,
    game_date: str,
    player_name: str | None = None,
) -> float | None:
    """Fetch actual hits with Postseason fallback, then ESPN fallback.

    Tries Regular Season first; if no result, tries Postseason (mirrors NBA
    resolve_pending() Playoffs fallback pattern). GG-084/T-241: if both MLB
    Stats API attempts return None and a player_name is supplied, falls back
    to ESPN's boxscore (unaffected by the MLB Stats API IP block) before
    giving up. player_name is optional and defaults to None so existing
    callers that only track player_id are unaffected — ESPN fallback is
    simply skipped in that case.
    """
    hits = _fetch_mlb_hits(player_id, game_date, game_type="R")
    if hits is None:
        hits = _fetch_mlb_hits(player_id, game_date, game_type="P")
    if hits is None and player_name:
        hits = _espn_fetch_hits(player_name, game_date)
    return hits


# ---------------------------------------------------------------------------
# Resolution helper — shared by T1/T2 pool and T4 pool (T-201)
# ---------------------------------------------------------------------------

def _run_pool_alarms(
    pool_label: str,
    trader: PaperTrader,
    monitor: SystemMonitor,
    session_id: str,
) -> None:
    """GG-125/T-379: drift check + the two ops alarms, run once per pool per
    resolve invocation regardless of how many positions were resolved this run
    (a pool with zero eligible resolutions this run can still be carrying a
    stale-open or failed-order-rate signal from prior runs). Warn-only.
    """
    monitor.check_and_alert(session_id=session_id)
    state = trader.get_state()
    monitor.check_stale_open_positions(
        open_positions=state.get("open_positions", []),
        pool_label=pool_label,
        session_id=session_id,
    )
    all_positions = (
        state.get("open_positions", [])
        + state.get("closed_positions", [])
        + state.get("rejected_positions", [])
    )
    monitor.check_failed_order_rate(
        all_positions=all_positions,
        pool_label=pool_label,
        session_id=session_id,
    )


def _resolve_pool(
    pool_label: str,
    trader: PaperTrader,
    logger: AuditLogger,
    session_id: str,
    monitor: SystemMonitor,
) -> tuple[int, int]:
    """Resolve all eligible positions in one portfolio pool.

    Returns (resolved_count, still_open_count).
    Eligible = open positions whose game_date is strictly before today.

    GG-125/T-379 (APR-0031): feeds `monitor`'s Brier/ECE drift window from
    each resolved bet's model_p/mid_price_at_entry, then runs check_and_alert()
    plus the two ops alarms (stale opens, failed-order rate) once at the end —
    one SystemMonitor instance per pool (T1/T2 and T4 kept separate; T1 pregame
    calibration and T4 live-latency edge are independent theses per CLAUDE.md's
    alpha taxonomy, so their drift windows should not be blended). Warn-only,
    log-to-C6-only — no auto-halt path is touched by this wiring (GG-098).
    """
    portfolio      = trader.get_state()
    open_positions = portfolio.get("open_positions", [])
    n_open         = len(open_positions)

    print(f"\n[{pool_label}] Open positions: {n_open}")

    if n_open == 0:
        print(f"[{pool_label}] No open positions — nothing to do.")
        _run_pool_alarms(pool_label, trader, monitor, session_id)
        return 0, 0

    today   = date.today().isoformat()
    pending = [p for p in open_positions if p.get("game_date", today) < today]

    if not pending:
        print(f"[{pool_label}] {n_open} open position(s) — all game dates today or future.")
        _run_pool_alarms(pool_label, trader, monitor, session_id)
        return 0, n_open

    print(f"[{pool_label}] {len(pending)} position(s) eligible (game_date < {today})...")
    resolved: list[dict[str, Any]] = []

    for pos in pending:
        player_id   = int(pos.get("player_id", 0))
        player_name = pos.get("player_name", "unknown")
        game_date   = pos.get("game_date", "")
        threshold   = int(pos.get("kalshi_threshold", 0))
        direction   = pos.get("direction", "YES")
        position_id = pos.get("position_id", "")

        actual_hits = fetch_actual_hits(player_id, game_date, player_name=player_name)

        if actual_hits is None:
            try:
                game_dt_utc = datetime.strptime(game_date, "%Y-%m-%d").replace(
                    tzinfo=timezone.utc
                )
                age_hours = (datetime.now(timezone.utc) - game_dt_utc).total_seconds() / 3600
            except ValueError:
                age_hours = 0.0

            if age_hours > 48:
                trader.mark_aged_open(
                    position_id=position_id,
                    reason="api_no_result_48h",
                    session_id=session_id,
                )
                print(
                    f"  [{pool_label}][AGED] {player_name:<24} — no MLB API result after "
                    f"{age_hours:.0f}h (>48h) — tagged aged_open",
                    file=sys.stderr,
                )
            else:
                logger.warning(
                    "PIPE-05R", "player_stats_fetch_failed",
                    payload={
                        "pool":         pool_label,
                        "player_id":    player_id,
                        "player_name":  player_name,
                        "game_date":    game_date,
                        "position_id":  position_id,
                        "age_hours":    round(age_hours, 1),
                        "note":         "MLB Stats API returned no result — position stays open",
                    },
                    session_id=session_id,
                )
                print(f"  [{pool_label}][SKIP] {player_name:<24} — no MLB API result for "
                      f"{game_date} ({age_hours:.0f}h old — within 48h grace period)")
            continue

        ok, closed_pos = trader.settle_position(
            position_id=position_id,
            actual_stat=actual_hits,
            stat_label="actual_hits",
            session_id=session_id,
        )

        if closed_pos:
            pnl     = closed_pos.get("pnl", 0.0)
            outcome = closed_pos.get("outcome", "?")
            sign    = "+" if pnl >= 0 else ""
            label   = "WIN " if outcome == "WIN" else "LOSS"
            print(f"  [{pool_label}] {player_name:<24} {label}  "
                  f"hits={actual_hits:.0f} vs H≥{threshold}  "
                  f"dir={direction}  P&L={sign}{pnl:.2f}")
            resolved.append(closed_pos)

            # GG-125/T-379 (APR-0031): feed the drift window from this resolved
            # bet's entry-time model_p / mid_price_at_entry — both already
            # captured by open_position(), previously unused after settlement.
            model_p = closed_pos.get("model_p")
            mip_at_entry = closed_pos.get("mid_price_at_entry")
            if model_p is not None and mip_at_entry is not None:
                monitor.record_forecast_outcome(
                    p_estimate=float(model_p),
                    outcome=1 if outcome == "WIN" else 0,
                    market_implied_prob=float(mip_at_entry),
                )

        if not ok:
            logger.warning(
                "PIPE-05R", "settle_position_partial_failure",
                payload={"pool": pool_label, "position_id": position_id,
                         "player_name": player_name},
                session_id=session_id,
            )

    still_open = len(trader.get_state().get("open_positions", []))

    # T-207 / GG-048: alert if eligible positions existed but none resolved.
    # Indicates possible systematic API failure (e.g. 406 from all endpoints).
    if pending and len(resolved) == 0:
        logger.warning(
            "PIPE-05R", "zero_resolved_with_eligible_positions",
            payload={
                "pool": pool_label,
                "eligible_count": len(pending),
                "resolved_count": 0,
                "note": "All fetch_actual_hits() calls returned None — possible 406 or API outage",
            },
            session_id=session_id,
        )
        print(
            f"  [{pool_label}][ALERT] {len(pending)} eligible position(s) but 0 resolved — "
            f"possible MLB Stats API 406 or outage (GG-048)",
            file=sys.stderr,
        )
    # GG-084/T-239: the zero-resolved alert above never fires on partial-but-
    # severe degradation (e.g. 2026-07-05's live run: 15/83 resolved, 68 skipped
    # — 82% failure — produced zero alert under the old all-or-nothing check).
    # Fire a distinct alert when resolution rate is below 50% on a batch large
    # enough (n>=5) that a few genuine "not final yet" skips can't explain it.
    elif pending and len(pending) >= 5 and (len(resolved) / len(pending)) < 0.5:
        resolved_fraction = len(resolved) / len(pending)
        logger.warning(
            "PIPE-05R", "degraded_resolution_rate",
            payload={
                "pool": pool_label,
                "eligible_count": len(pending),
                "resolved_count": len(resolved),
                "resolved_fraction": round(resolved_fraction, 3),
                "note": "Resolution rate below 50% — possible MLB Stats API degradation",
            },
            session_id=session_id,
        )
        print(
            f"  [{pool_label}][ALERT] Only {len(resolved)}/{len(pending)} eligible position(s) "
            f"resolved ({resolved_fraction:.0%}) — possible MLB Stats API degradation (GG-084/GG-048)",
            file=sys.stderr,
        )

    _run_pool_alarms(pool_label, trader, monitor, session_id)
    return len(resolved), still_open


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    logger = AuditLogger(LOG_DIR / "audit_mlb.jsonl", min_severity="INFO")

    print(f"\n[PIPE-05R] MLB resolution run — {GAME_DATE}")
    print(f"Session:  {SESSION_ID}")

    logger.info("PIPE-05R", "resolve_run_start",
                payload={"session_id": SESSION_ID, "game_date": GAME_DATE},
                session_id=SESSION_ID, snapshot_id=SNAPSHOT_ID)

    # GG-125/T-379 (APR-0031): one SystemMonitor per pool — T1/T2 pregame
    # calibration and T4 live-latency edge are independent theses (CLAUDE.md
    # alpha taxonomy), so their Brier/ECE drift windows are kept separate
    # rather than blended into one number (APR-0031 Open Question #2).
    # Persistence model: accept the per-run-reset window (APR-0031 design
    # option 3a) — simplest, strictly more coverage than today's zero, and
    # explicitly named as an acceptable starting point in the draft APR.
    # Earl authorized this implementation directly (2026-07-29 session,
    # T-379/GG-125), satisfying Hard Rule 3 for this monitoring-only,
    # warn-only wiring — see DECISION_LOG.md.

    # ---- T1/T2 pool ----
    trader_main = PaperTrader(PORTFOLIO_PATH, logger)
    monitor_main = SystemMonitor(
        logger=logger, snapshot_id=SNAPSHOT_ID, session_id=SESSION_ID,
        brier_baseline=BRIER_BASELINE_MLB, ece_baseline=ECE_BASELINE_MLB,
    )
    resolved_main, still_open_main = _resolve_pool(
        pool_label="T1/T2",
        trader=trader_main,
        logger=logger,
        session_id=SESSION_ID,
        monitor=monitor_main,
    )
    summary_main = trader_main.summary()

    # ---- T4 pool (T-201) ----
    resolved_t4 = still_open_t4 = 0
    summary_t4: dict[str, Any] = {}
    if T4_PORTFOLIO_PATH.exists():
        trader_t4 = PaperTrader(T4_PORTFOLIO_PATH, logger)
        monitor_t4 = SystemMonitor(
            logger=logger, snapshot_id=SNAPSHOT_ID, session_id=SESSION_ID,
            brier_baseline=BRIER_BASELINE_MLB, ece_baseline=ECE_BASELINE_MLB,
        )
        resolved_t4, still_open_t4 = _resolve_pool(
            pool_label="T4",
            trader=trader_t4,
            logger=logger,
            session_id=SESSION_ID,
            monitor=monitor_t4,
        )
        summary_t4 = trader_t4.summary()
    else:
        print(f"\n[T4] No T4 portfolio at {T4_PORTFOLIO_PATH} — skipping.")

    # ---- Summary ----
    total_resolved  = resolved_main + resolved_t4
    total_still_open = still_open_main + still_open_t4

    if total_resolved == 0:
        print("[RESOLVE] No positions settled yet — MLB API results not available.")
    else:
        print(f"\n[SUMMARY — T1/T2 pool]")
        print(f"  Resolved this run:  {resolved_main}")
        print(f"  Still open:         {still_open_main}")
        print(f"  Bankroll:           ${summary_main['bankroll_usd']:.2f}")
        print(f"  Total realized P&L: ${summary_main['total_realized_pnl']:+.2f}")
        if summary_main["win_rate"] is not None:
            print(f"  Win rate:           {summary_main['win_rate']:.1%}  "
                  f"({summary_main['closed_positions']} resolved bets)")
        print(f"  Realized drawdown:  {summary_main['realized_drawdown_pct']:.1f}%")

        if summary_t4:
            print(f"\n[SUMMARY — T4 pool]")
            print(f"  Resolved this run:  {resolved_t4}")
            print(f"  Still open:         {still_open_t4}")
            print(f"  Bankroll:           ${summary_t4['bankroll_usd']:.2f}")
            print(f"  Total realized P&L: ${summary_t4['total_realized_pnl']:+.2f}")
            if summary_t4["win_rate"] is not None:
                print(f"  Win rate:           {summary_t4['win_rate']:.1%}  "
                      f"({summary_t4['closed_positions']} resolved bets)")

    monitor_main.check_portfolio_pnl(
        total_realized_pnl=summary_main["total_realized_pnl"],
        initial_bankroll=summary_main["initial_bankroll_usd"],
        session_id=SESSION_ID,
    )

    logger.info("PIPE-05R", "resolve_run_complete",
                payload={
                    "resolved_main":       resolved_main,
                    "resolved_t4":         resolved_t4,
                    "still_open_main":     still_open_main,
                    "still_open_t4":       still_open_t4,
                    "bankroll_main":       summary_main["bankroll_usd"],
                    "total_realized_pnl":  summary_main["total_realized_pnl"],
                    "win_rate_main":       summary_main["win_rate"],
                },
                session_id=SESSION_ID, snapshot_id=SNAPSHOT_ID)


if __name__ == "__main__":
    main()
