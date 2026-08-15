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

Fire condition (bidirectional — GG-087, 2026-07-05):
  gross_edge = p_t4 - mip - vig
  gross_edge > 0  → YES edge candidate; gross_edge < 0 → NO edge candidate
    (direction is whichever side the market currently misprices; a prior
    version of this file only ever considered YES, silently discarding all
    NO-side signal — measured at 41.6x the volume it acted on, GG-087).
  directional_net_edge = abs(gross_edge) - kalshi_fee (ADR-0016 taker fee)
  C4 gates on directional_net_edge (MIN_EDGE via RiskEngine).

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

Reclassified under ADR-0039 as sub-band T4M-PROJ — SESSION 109/T-219. No logic in this
file changed; this is a labeling/traceability update only. See
execution_bands.py::T4_MLB_SUBBAND_REGISTRY[ExecutionBand.T4M_PROJ].
"""

from __future__ import annotations

import errno
import fcntl
import json
import logging
import math
import os
import re
import sys
import time
import uuid
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable, Optional, Union

import requests

_SRC_ROOT = Path(__file__).resolve().parents[2]
if str(_SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(_SRC_ROOT))

from prediction_market_bot.c4_risk_engine.risk import RiskEngine
from prediction_market_bot.c4_risk_engine.staged_order_store import StagedOrderStore
from prediction_market_bot.c5_execution.kalshi_client import (
    KalshiMarketClient,
    PlayerMarket,
    SERIES_MLB_PLAYER_HITS,
)
from prediction_market_bot.c5_execution.paper_trader import PaperTrader
from prediction_market_bot.c6_audit_logger.audit_logger import AuditLogger
from prediction_market_bot.c7_monitoring.semantic_contracts import (
    ContaminationGuard as SemanticContaminationGuard,
    T4CorrDownwardViolation,
)

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
# GG-090 (2026-07-06): this used to run unconditionally at module import time,
# so any script or test that merely *imported* this module (for its shared
# helper functions, e.g. run_t4_mlb_execution_engine.py, run_exp_flow_mlb_01.py)
# would crash unless it had already set BOT_ENV/BOT_C4_ACTIVE in the process
# environment before the import — a fragile, easy-to-forget precondition
# (EXP-FLOW-MLB-01 hit exactly this crash). The guard is only meaningful for
# actually *running* this file as the live T4 MLB process, so it now runs
# under the __main__ block below, not as an import side effect. No behavior
# change for the systemd-managed live service, which always runs this file
# directly.


def _enforce_paper_mode_guard() -> None:
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
KELLY_T4            = 0.0           # ADR-0048 (2026-07-29, supersedes ADR-0023's 0.10): this module-level
                                     # constant, not execution_bands.py's BAND_CONFIGS[T4M_PROJ].kelly_fraction,
                                     # is what this live pipeline actually stakes with (no import of
                                     # execution_bands.py exists in this file) — zeroed here directly so T4M-PROJ
                                     # sizing is genuinely halted, not just relabeled. GG-142 abs()-gate fix
                                     # landed (R2, ADR-0049, epoch=10). ADR-0050 (2026-07-30) reactivates T4M-PROJ
                                     # at a FLAT measurement stake (T4_MEASUREMENT_STAKE_USD, below) while
                                     # deliberately leaving KELLY_T4 at 0.0 — the proportional Kelly path stays
                                     # off pending GG-105 anti-predictive-edge remediation; a flat stake and a
                                     # Kelly fraction are mutually exclusive by design. DS sign-off: operator
                                     # 2026-07-30.
T4_MEASUREMENT_STAKE_USD = 1.00     # ADR-0050 (2026-07-30): flat per-bet stake for the T4M-PROJ measurement
                                     # cohort, used in place of Kelly sizing (KELLY_T4 stays 0.0 above) on every
                                     # gate-valid (signed edge >= MIN_EDGE_TO_APPROVE, direction-consistent)
                                     # evaluation. Far inside GG-045 orderbook depth ($500-$2k est., later
                                     # refined to median $66-$195 per T-393). Passed to RiskEngine.evaluate_forecast
                                     # as fixed_stake_usd= (after the contract-cap adjustment below) — see risk.py
                                     # for the bypass mechanics. EXIT: once volume accrues, sizing is
                                     # regression-analyzed and moved to the B2 survivable-edge frontier (operator
                                     # directive, 2026-07-30); reverts to 0 if edge fails to validate by the
                                     # power-calc n* for this cohort. That regression must NOT treat the prior
                                     # in-sample GG-142 gate-valid ROI readings (+10.99%/+27.58%) as a validated
                                     # prior — this cohort is the first out-of-sample test of that filter
                                     # (ADR-0050 addendum item g, 2026-07-30).
T4_MEASUREMENT_MAX_CONTRACTS = 10   # ADR-0050 addendum (2026-07-30, operator): flat DOLLARS != flat exposure —
                                     # at an uncapped $1.00 stake, a sub-$0.10 entry price becomes a 100+:1
                                     # payout position. Measured on the epoch-8 gate-valid cohort (n=234):
                                     # 23% of bets (54/234) price below $0.10; uncapped flat-$1 has ~15x the
                                     # per-bet variance of a 10-contract-capped form on the same bets/signs,
                                     # and n* scales with variance, so uncapped defeats the point of accruing a
                                     # measurement cohort efficiently. stake = min(flat_stake, this * entry_price)
                                     # — every bet at entry_price >= $0.10 (77% of the cohort) still stakes
                                     # exactly $1.00 (the min() saturates at flat_stake); only the sub-10c tail
                                     # is capped, bounded at a uniform $10 max payout instead of unbounded.
                                     # Operator-overridable — do not change unilaterally.
T4_PRICE_STRATUM_LOW_MAX  = 0.10    # ADR-0050 addendum §C pre-registration (2026-07-30): LOW < 0.10
T4_PRICE_STRATUM_MID_MAX  = 0.70    # MID in [0.10, 0.70]; HIGH > 0.70. Fixed BEFORE this cohort accrues data —
                                     # see ADR-0050 §8 for the committed analysis rule (headline verdict on
                                     # MID+HIGH, LOW reported separately as a named secondary stratum, neither
                                     # pooled nor discarded). Do not change post hoc.
# T-228: skip the Binomial/C4 evaluation cost on markets priced too wide to plausibly
# clear MIN_EDGE_TO_APPROVE. Ceiling set from real 2026-07-02 production data, not a
# guess: of 4,971 evaluated cycles that day, the widest vig on any net_edge>=0.04
# qualifying signal was 0.24 (KXMLBHIT PHIBHARPER3-2, p_t4=0.45, mip=0.15); 0.30 keeps
# clear margin above every observed real signal while still cutting the fat right tail
# (477/4,971 rows, ~9.6%, had vig>0.30 and none of them ever qualified).
VIG_CEILING         = 0.30

# Slot-specific expected ABs per game — mirrors T2 empirical averages (T-200)
_AB_BY_SLOT: dict[int, float] = {
    1: 4.2, 2: 4.1, 3: 4.0, 4: 3.9, 5: 3.7,
    6: 3.6, 7: 3.4, 8: 3.2, 9: 3.1,
}


def measurement_stake_and_stratum(entry_price: float) -> tuple[float, float, str]:
    """ADR-0050 addendum §B/§C (2026-07-30): contract-capped flat measurement
    stake + pre-registered price stratum for a single T4M-PROJ bet.

    Extracted from the main evaluation loop (rather than left inline) so the
    addendum's Part D.3 requirement — "assert the contract cap binds" — can be
    tested directly against this function instead of the whole live-polling
    loop. See T4_MEASUREMENT_MAX_CONTRACTS's definition above for why this
    uses min(flat_stake, max_contracts * entry_price) rather than a
    floor()-based integer-contract count.

    Returns (measurement_stake_usd, contracts, price_stratum). Caller must
    guard entry_price > 0.0 — this function does not.
    """
    stake = round(
        min(T4_MEASUREMENT_STAKE_USD, T4_MEASUREMENT_MAX_CONTRACTS * entry_price), 4
    )
    contracts = round(stake / entry_price, 4)
    if entry_price < T4_PRICE_STRATUM_LOW_MAX:
        stratum = "LOW"
    elif entry_price <= T4_PRICE_STRATUM_MID_MAX:
        stratum = "MID"
    else:
        stratum = "HIGH"
    return stake, contracts, stratum

_LOGS_DIR        = Path(__file__).resolve().parents[2] / "logs"
_PORTFOLIO_PATH  = _LOGS_DIR / "paper_portfolio_mlb_t4.json"
_STAGED_DB_PATH  = str(_LOGS_DIR / "staged_orders_mlb_t4.db")
_AUDIT_LOG_PATH  = _LOGS_DIR / "audit_mlb_t4.jsonl"
KILL_SWITCH_PATH = _LOGS_DIR / "t4_mlb_kill_switch.flag"
SINGLETON_LOCK_PATH = _LOGS_DIR / "t4_mlb_live.lock"

# GG-149: T1 MLB's portfolio file, read-only, for the cross-book (T1 vs T4)
# alarm-only conflict check. ADR-0023 pool isolation means T1 and T4 are
# separate processes with separate portfolio files and no shared coordination
# mechanism — this is a best-effort file read, never a live handle into T1's
# process, and must tolerate the file being absent or stale.
_T1_PORTFOLIO_PATH = _LOGS_DIR / "paper_portfolio_mlb.json"

# GG-067 (SESSION 110): raw per-cycle context, independent of T4_MLB_DRY_RUN.
# Written for every cycle that reaches the p_t4/gross_edge computation (fired
# or not) so EXP-ARITH-MLB-01 / EXP-FLOW-MLB-01 have a real data source —
# previously only the dry-run branch persisted this context, so production
# runs (the only ones that have ever executed) left no reconstructable record.
CYCLE_LOG_PATH = _LOGS_DIR / "t4_mlb_cycle_log.jsonl"

# ---------------------------------------------------------------------------
# ESPN MLB live feed
# ---------------------------------------------------------------------------

_ESPN_MLB_SCOREBOARD = "https://site.api.espn.com/apis/site/v2/sports/baseball/mlb/scoreboard"
_ESPN_MLB_SUMMARY    = "https://site.api.espn.com/apis/site/v2/sports/baseball/mlb/summary"
# GG-163: ESPN blocks on the literal "Mozilla/5.0" browser-spoofed UA (403,
# verified 723/723 since 2026-08-04T23:41Z), not on source IP. Sending no
# User-Agent at all lets `requests` use its own default UA, which is not
# blocked (verified 200 live). Do not reintroduce a browser-style UA here.
_ESPN_HEADERS: dict[str, str] = {}

_ESPN_STATUS_IN_PROGRESS = "STATUS_IN_PROGRESS"
_ESPN_STATUS_SCHEDULED   = "STATUS_SCHEDULED"
_ESPN_STATUS_FINAL       = "STATUS_FINAL"
_ESPN_STATUS_POSTPONED   = "STATUS_POSTPONED"
_ESPN_TERMINAL_STATUSES  = (_ESPN_STATUS_FINAL, _ESPN_STATUS_POSTPONED)

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
# Singleton lock (T-216 — GG-062 fix)
#
# ExecStartPre='pkill -f run_t4_mlb_live.py' is a best-effort cleanup of the
# *previous* instance: it depends on timing between that process's death and
# its deregistration, not on an atomic check. GG-062 proved this race can
# leave an orphan alive for hours, running a second, independently-clocked
# evaluation loop against the same portfolio/audit files. An flock is race-free
# by construction — the kernel serializes acquisition, and it self-releases if
# the holding process dies or is killed, so it can't leak a stale lock across a
# crash the way a manual PID-file could.
# ---------------------------------------------------------------------------

_singleton_lock_fh: Optional[object] = None  # keeps the fd alive for process lifetime


def acquire_singleton_lock(path: Path = SINGLETON_LOCK_PATH) -> bool:
    """
    Acquire an exclusive, non-blocking flock on `path`. Returns True if this
    process now holds the lock (safe to proceed), False if another live
    process already holds it (caller must not start a second evaluation loop).

    The lock is held for the lifetime of this process's file descriptor and is
    released automatically on process exit (normal or crash) — no cleanup step
    required, and nothing to leak across a restart.
    """
    global _singleton_lock_fh
    path.parent.mkdir(parents=True, exist_ok=True)
    fh = open(path, "w")
    try:
        fcntl.flock(fh.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError as exc:
        fh.close()
        if exc.errno in (errno.EACCES, errno.EAGAIN):
            return False
        raise
    fh.write(f"{os.getpid()}\n")
    fh.flush()
    _singleton_lock_fh = fh  # noqa: F841 — retained only to hold the fd open
    return True


# ---------------------------------------------------------------------------
# Dry-run record writer (T-202)
# ---------------------------------------------------------------------------


def _append_dryrun_record(path: Path, record: dict[str, Any]) -> None:
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

    Extra innings (inning > 9, T-220): unlike innings 1-9, there is no fixed
    endpoint to derive an inning-based cap from — the game continues until
    resolved. Rather than clamping ab_from_inning to 0 (which silently
    stopped T4 from evaluating any batter once a game went past inning 9),
    floor it at 1 AB — the batter's next likely plate appearance. ab_from_total
    still acts as the ceiling, so a batter who has already exceeded their
    expected ABs for the game correctly returns 0.
    """
    expected_total = _AB_BY_SLOT.get(batting_slot, AB_PER_GAME_DEFAULT)
    if inning <= 9:
        innings_remaining = max(0.0, 9.0 - inning + 0.5)
        ab_from_inning = expected_total * (innings_remaining / 9.0)
    else:
        ab_from_inning = 1.0
    ab_from_total = max(0.0, expected_total - ab_so_far)
    return max(0, round(min(ab_from_inning, ab_from_total)))


# ---------------------------------------------------------------------------
# Pregame context loader
# ---------------------------------------------------------------------------


def _load_pregame_context() -> tuple[dict[int, list[dict[str, Any]]], dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
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

    by_player_id: dict[int, list[dict[str, Any]]] = {}
    by_ticker: dict[str, dict[str, Any]] = {}
    name_to_pregame: dict[str, dict[str, Any]] = {}

    for fc in forecasts:
        pid   = int(fc.get("player_id", 0))
        name  = fc.get("player_name", "")
        ticker = fc.get("kalshi_ticker", "")
        raw_ba_l10 = float(fc.get("ba_l10") or 0.25)
        # GG-105/APR-0025/ADR-0047: prefer the shrunk field; fall back to raw ba_l10 for
        # pregame JSON produced before this fix landed (field absent → fc.get returns None).
        _shrunk = fc.get("ba_l10_shrunk")
        ctx = {
            "player_id":   pid,
            "player_name": name,
            "ticker":      ticker,
            "threshold":   int(fc.get("kalshi_threshold", 1)),
            "p_t1":        float(fc.get("p_estimate", 0.5)),
            "ba_l10":      raw_ba_l10,
            "ba_l10_shrunk": float(_shrunk) if _shrunk is not None else raw_ba_l10,
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


def _latest_pregame_file() -> Optional[Path]:
    """Cheap (glob+sort, no parse) lookup of the file _load_pregame_context() would load."""
    jsons = sorted(_LOGS_DIR.glob("pregame_mlb_*.json"), reverse=True)
    return jsons[0] if jsons else None


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


def _espn_mlb_game_ids_today(for_date: date | None = None) -> list[str]:
    """Return ESPN game IDs for the given UTC date's MLB games (in-progress first).

    Defaults to today (UTC) when `for_date` is omitted. GG-143: cold start also
    calls this with yesterday's date to discover still-live games missed by the
    empty in-memory tracked set on a fresh process.
    """
    try:
        query_date = for_date or date.today()
        today_str = query_date.strftime("%Y%m%d")
        espn_params: dict[str, str | int] = {"dates": today_str, "limit": 30}
        r = requests.get(
            _ESPN_MLB_SCOREBOARD,
            params=espn_params,
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


def _espn_game_status(espn_game_id: str) -> str:
    """Fetch just the status name for one game (GG-058 rollover pruning).

    Used only at UTC-midnight rollover to decide whether a game carried over
    from the previous day is done (STATUS_FINAL/STATUS_POSTPONED) or still
    needs tracking. Returns "" on fetch failure — callers must treat "" as
    non-terminal (keep tracking) rather than assume the game ended, since an
    ESPN blip must never cause a live game to silently drop off the poll list.
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
        logger.warning("ESPN MLB status fetch failed game=%s: %s", espn_game_id, exc)
        return ""
    comps = d.get("header", {}).get("competitions", [{}])
    if not comps:
        return ""
    return str(comps[0].get("status", {}).get("type", {}).get("name", ""))


def _rollover_game_ids(
    tracked_game_ids: list[str],
    newly_discovered: list[str],
    status_fn: Callable[[str], str] = _espn_game_status,
) -> list[str]:
    """GG-058: merge-in rollover, never a destructive replace.

    A hard UTC-midnight `game_ids[:] = _espn_mlb_game_ids_today()` dropped
    every still-in-progress West-coast game every night (first pitch commonly
    straddles 22:30-01:45 UTC, so the boundary lands mid-game). Carries
    forward any previously-tracked game that has not reached a terminal ESPN
    status (STATUS_FINAL/STATUS_POSTPONED); only new-day discovery is
    additive on top of that.
    """
    carried_over = [
        gid for gid in tracked_game_ids
        if gid not in newly_discovered
        and status_fn(gid) not in _ESPN_TERMINAL_STATUSES
    ]
    return carried_over + [gid for gid in newly_discovered if gid not in carried_over]


def _espn_poll_once_mlb(
    espn_game_id: str,
    name_to_pregame: dict[str, dict[str, Any]],
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
        for stat_group in team_data.get("statistics", []):
            # ESPN MLB API does not include a 'name' field on stat groups.
            # Identify batting vs pitching by labels: batting has "AB", pitching has "IP".
            labels = stat_group.get("labels", [])
            if not labels or "AB" not in labels or "IP" in labels:
                continue  # skip pitching stat group

            try:
                h_idx  = labels.index("H")
            except ValueError:
                h_idx = 3   # fallback position in H-AB, AB, R, H, RBI layout
            try:
                ab_idx = labels.index("AB")
            except ValueError:
                ab_idx = 1

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


def _compute_t4_band_budget(portfolio: dict[str, Any]) -> float:
    return float(max(portfolio["bankroll_usd"] * T4_BAND_WEIGHT, 0.0))


def _exit_budget_credit(size_usd: float, exit_pnl: float) -> float:
    return size_usd + min(0.0, exit_pnl)


# GG-166/T-429 (2026-08-07): ticker-derived game date, reusing the anchored-regex
# format from scripts/build_t4_outcome_store.py::ticker_game_date (validated 100%
# reliable parse across 2,021 tickers under T-421). The wall-clock `game_date`
# session variable (assigned at startup and again on UTC-midnight rollover) is
# what GG-166 found silently mis-stamping ~44% of positions when a game is still
# live after UTC midnight — this function derives the true per-position date from
# the ticker itself instead, at the exact write sites that persist it.
_TICKER_DATE_RE = re.compile(r"^KXMLBHIT-(\d{2})([A-Z]{3})(\d{2})(\d{4})")
_TICKER_DATE_MONTHS = {
    "JAN": "01", "FEB": "02", "MAR": "03", "APR": "04", "MAY": "05", "JUN": "06",
    "JUL": "07", "AUG": "08", "SEP": "09", "OCT": "10", "NOV": "11", "DEC": "12",
}


def _ticker_to_game_date(ticker: str, fallback: str) -> str:
    """Derive the true game date from a ticker's embedded date token.

    Returns `fallback` (the wall-clock session `game_date`) only if the ticker
    doesn't match the expected KXMLBHIT format — logged loudly since that should
    not happen for any real Kalshi MLB ticker and would mean this is silently
    reverting to the exact bug this function exists to fix.
    """
    m = _TICKER_DATE_RE.match(ticker)
    if not m:
        logger.warning(
            "GG-166: ticker %s did not match expected date format — "
            "falling back to session game_date=%s", ticker, fallback,
        )
        return fallback
    yy, mon, dd, _hhmm = m.groups()
    month = _TICKER_DATE_MONTHS.get(mon)
    if month is None:
        logger.warning(
            "GG-166: ticker %s has unrecognized month token %r — "
            "falling back to session game_date=%s", ticker, mon, fallback,
        )
        return fallback
    return f"20{yy}-{month}-{dd}"


def _game_date_window(game_date: str) -> set[Any]:
    """GG-081/GG-082 (2026-07-04): expand a single game_date into {game_date, prior_day}.

    UTC date rollover reassigns `game_date` to the new calendar day while a game that
    started the evening before (e.g. a 19:40 local first pitch = ~23:40-00:40 UTC) is
    still live. Reconstructing ledger/dedup state filtered on the new day alone silently
    drops every position tied to that still-live game's original game_date, both at
    scheduled midnight rollover and at a cold process restart that happens to land after
    midnight mid-game. Kalshi tickers embed the actual game date
    (KXMLBHIT-26JUL021940TBKC-...), so including one extra day carries no collision risk
    — it only ever adds positions from a genuinely distinct game/date pairing.
    """
    d = date.fromisoformat(game_date)
    return {game_date, (d - timedelta(days=1)).isoformat()}


def _reconstruct_t4_ledger(portfolio: dict[str, Any], game_dates: Union[str, set[Any]]) -> float:
    """GG-086/T-240 (2026-07-05): open exposure is never date-filtered.

    Confirmed in production the day this was found: 33 pool_isolated positions
    (22 dated 2026-07-02, 11 dated 2026-07-03 — $12.78 combined) were still
    open against the live T4 ledger, three and two days respectively past
    their game_date, almost certainly stuck by GG-084's MLB Stats API block
    preventing `run_resolve_mlb.py` from resolving them. `_game_date_window`
    only ever widens by one day (today + prior_day), so once a second
    midnight rollover passes without a position resolving, it permanently
    drops out of every future reconstruction — the budget check then believes
    there is more headroom than truly exists, allowing new fires to stack on
    top of invisible real exposure and silently breach the intended T4 band
    cap. An open position is real deployed capital until it resolves, no
    matter how many days that takes — so the open-exposure sum must never be
    scoped by date. `game_dates` still scopes `realized_losses`, which
    attributes a closed loss to a specific day's budget by design (a
    genuinely dated concept, unlike open exposure) — that half is unaffected.
    """
    if isinstance(game_dates, str):
        game_dates = {game_dates}
    open_exposure = sum(
        p.get("size_usd", 0.0)
        for p in portfolio.get("open_positions", [])
        if p.get("pool_isolated")
    )
    realized_losses = sum(
        max(0.0, -p.get("exit_pnl", 0.0))
        for p in portfolio.get("closed_positions", [])
        if p.get("pool_isolated") and p.get("game_date") in game_dates
    )
    return float(open_exposure + realized_losses)


def _reconstruct_fired_ticker_states(portfolio: dict[str, Any], game_dates: Union[str, set[Any]]) -> dict[str, tuple[int, int]]:
    """T-209/T-225: rebuild the game-day re-entry dedup guard from the persisted portfolio.

    `already_fired_game` is otherwise a process-local in-memory dict that is
    silently wiped on every restart (crash, RestartSec cooldown, or a deploy-
    triggered `systemctl restart`). Without this reconstruction, a restart
    mid-game forgets each ticker's last-fired live state, and
    `PaperTrader.open_position()` has no ticker-level duplicate guard of its
    own — so a restart could cause a redundant same-state re-fire on a market
    this process (or a prior instance of it) already bet at that exact state.

    T-225: the guard now maps ticker -> (h_so_far, ab_remaining) at last entry
    rather than a permanent one-shot set, so a ticker may re-fire once the
    live state that feeds p_t4 has actually moved. Positions are scanned in
    `entered_at` order (ascending) so the most recent entry per ticker wins,
    regardless of whether it currently sits in open_positions or has since
    closed.
    """
    if isinstance(game_dates, str):
        game_dates = {game_dates}
    states: dict[str, tuple[int, int]] = {}
    positions = portfolio.get("open_positions", []) + portfolio.get("closed_positions", [])
    positions.sort(key=lambda p: p.get("entered_at", ""))
    for p in positions:
        if p.get("pool_isolated") and p.get("game_date") in game_dates:
            ticker = p.get("kalshi_ticker")
            h_so_far = p.get("h_so_far_at_entry")
            ab_remaining = p.get("ab_remaining_at_entry")
            if ticker and h_so_far is not None and ab_remaining is not None:
                states[ticker] = (h_so_far, ab_remaining)
    return states


def _find_open_position_opposite_direction(
    open_positions: list[dict[str, Any]], ticker: str, direction: str
) -> Optional[dict[str, Any]]:
    """GG-149: return the OPEN position on `ticker` whose direction is the
    opposite of `direction`, if one exists in `open_positions`.

    This is a genuinely new control, not a repair of the existing
    `already_fired_game` state-dedup guard (T-225, above): that guard is
    keyed on ticker but its blocking condition is exact (h_so_far,
    ab_remaining) state-equality, has no direction field anywhere in its key
    or value, and its source (`_reconstruct_fired_ticker_states`) merges
    OPEN and CLOSED positions together — it cannot represent "is there
    currently an open opposite-direction position" without a redesign of
    its data model, which would be a rewrite, not a fix.
    """
    for p in open_positions:
        if (
            p.get("kalshi_ticker") == ticker
            and p.get("status") == "OPEN"
            and p.get("direction") in ("YES", "NO")
            and p.get("direction") != direction
        ):
            return p
    return None


def _t1_open_position_opposite_direction(
    ticker: str, t4_direction: str
) -> Optional[dict[str, Any]]:
    """GG-149: read-only, best-effort check of the T1 MLB portfolio file for
    an OPEN position on `ticker` with a direction opposite to `t4_direction`.

    Cross-book (T1 vs T4) is alarm-only, never blocking — ADR-0023 pool
    isolation means T1 and T4 are separate processes with separate portfolio
    files and no shared coordination mechanism; blocking would require
    cross-process locking that doesn't exist and shouldn't be improvised
    here. Must tolerate the file being absent, stale, or malformed and must
    never raise into a live T4 cycle.
    """
    try:
        if not _T1_PORTFOLIO_PATH.exists():
            return None
        with open(_T1_PORTFOLIO_PATH) as f:
            t1_state = json.load(f)
        for p in t1_state.get("open_positions", []):
            if (
                p.get("kalshi_ticker") == ticker
                and p.get("status") == "OPEN"
                and p.get("direction") in ("YES", "NO")
                and p.get("direction") != t4_direction
            ):
                return p
    except Exception as exc:
        logger.debug("T1 cross-book check skipped for %s: %s", ticker, exc)
    return None


# ---------------------------------------------------------------------------
# Contamination guard
# ---------------------------------------------------------------------------


class LiveDataFreshnessGuard:
    """
    Runtime gate: validates each T4 bet evaluation operates on coherent,
    fresh, and active data before passing to evaluate_forecast().

    Four checks per evaluation:
      game_state_fresh   — cycle started within 2× POLL_INTERVAL_S of now
      market_active      — Kalshi market status=active with live quotes
      player_in_game     — player_id in live batter state matches pregame record
      snapshot_not_stale — Kalshi price snapshot fetched within 2× POLL_INTERVAL_S

    market_active halts are normal at game end (market settles mid-cycle).
    Staleness halts (game_state_fresh / snapshot_not_stale) are unexpected —
    they surface as logger.warning in cron output and as CONTAMINATION_HALT
    events in the C6 JSONL audit. Zero staleness_halts per session = healthy.

    Distinct from SemanticContaminationGuard (ADR-0034): this guard checks
    timestamp freshness and market liveness; SemanticContaminationGuard checks
    business-logic coherence (mip range, mathematical impossibility, T4-CORR).
    """

    _FRESHNESS_WINDOW_S: float = 2.0 * POLL_INTERVAL_S  # 90s

    def __init__(self, audit: AuditLogger, session_id: str) -> None:
        self._audit = audit
        self._session_id = session_id
        self.total_halts: int = 0
        self.staleness_halts: int = 0

    def check(
        self,
        *,
        ticker: str,
        player_id: int,
        ls: MLBLiveBatterState,
        pm: object,
        cycle_start_at: datetime,
        snapshot_fetched_at: datetime,
    ) -> bool:
        """Return True if all checks pass; False (+ log) on any failure."""
        now = datetime.now(timezone.utc)
        checks: dict[str, bool] = {
            "game_state_fresh": (
                (now - cycle_start_at).total_seconds() < self._FRESHNESS_WINDOW_S
            ),
            "market_active": (
                getattr(pm, "status", "") == "active"
                and bool(getattr(pm, "has_live_quotes", False))
            ),
            "player_in_game": ls is not None and ls.player_id == player_id,
            "snapshot_not_stale": (
                (now - snapshot_fetched_at).total_seconds() < self._FRESHNESS_WINDOW_S
            ),
        }
        failed = [k for k, v in checks.items() if not v]
        if not failed:
            return True

        self.total_halts += 1
        _staleness = {"game_state_fresh", "snapshot_not_stale"}
        if any(f in _staleness for f in failed):
            self.staleness_halts += 1
            logger.warning(
                "T4-MLB CONTAMINATION_HALT %s — unexpected staleness: %s",
                ticker, failed,
            )
        self._audit.warning(
            COMPONENT, "CONTAMINATION_HALT",
            payload={
                "ticker": ticker,
                "player_id": player_id,
                "failed_checks": failed,
                "total_halts": self.total_halts,
                "staleness_halts": self.staleness_halts,
            },
            session_id=self._session_id,
        )
        return False


# ---------------------------------------------------------------------------
# Evaluation cycle
# ---------------------------------------------------------------------------


def _run_cycle(
    cycle_id: str,
    session_id: str,
    live_states: list[MLBLiveBatterState],
    live_prices: dict[str, PlayerMarket],
    pregame_by_player_id: dict[int, list[dict[str, Any]]],
    engine: RiskEngine,
    trader: PaperTrader,
    store: StagedOrderStore,
    audit: AuditLogger,
    game_date: str,
    t4_band_budget: float,
    t4_deployed_usd: float,
    already_fired_game: Optional[dict[str, tuple[int, int]]] = None,
    batting_slots: Optional[dict[int, int]] = None,
    dry_run: bool = False,
    dryrun_log_path: Optional[Path] = None,
    contamination_guard: Optional[LiveDataFreshnessGuard] = None,
    cycle_start_at: Optional[datetime] = None,
    snapshot_fetched_at: Optional[datetime] = None,
    cycle_log_path: Optional[Path] = None,
) -> tuple[int, int, float]:
    """
    Run one T4 MLB evaluation cycle.

    Returns (evaluated, fired, updated_t4_deployed_usd).
    contamination_guard: if provided, gates each evaluation via LiveDataFreshnessGuard.check().
    cycle_start_at / snapshot_fetched_at: timestamps for freshness checks in the guard.
    Omitting either timestamp disables that specific freshness check (guard uses now()).
    cycle_log_path: if provided, appends the raw per-cycle context (GG-067) for every
    ctx that reaches the p_t4/gross_edge computation, independent of dry_run/fired status.
    """
    if already_fired_game is None:
        already_fired_game = {}
    evaluated = 0
    fired = 0
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
        # GG-105/APR-0025/ADR-0047: shrunk value drives the live Binomial calc below;
        # raw ba_l10 is retained only for audit-log comparison (fallback to raw if absent).
        ba_l10_shrunk = market_ctxs[0].get("ba_l10_shrunk", ba_l10)
        batting_slot = _slots.get(player_id, 0)
        ab_remaining = _compute_ab_remaining(ls.ab_so_far, ls.inning, batting_slot)

        for ctx in market_ctxs:
            ticker    = ctx["ticker"]
            threshold = int(ctx["threshold"])

            # T-225: allow re-entry once the live state feeding p_t4 has moved
            # since this ticker's last fire (new hit, new out, or ab_remaining
            # decay). A same-state re-check is a no-op re-fire and is blocked.
            last_state = already_fired_game.get(ticker)
            if last_state is not None and last_state == (ls.h_so_far, ab_remaining):
                continue

            pm = live_prices.get(ticker)
            if pm is None:
                continue

            if contamination_guard is not None:
                _cg_start = cycle_start_at or datetime.now(timezone.utc)
                _cg_snap  = snapshot_fetched_at or datetime.now(timezone.utc)
                if not contamination_guard.check(
                    ticker=ticker,
                    player_id=player_id,
                    ls=ls,
                    pm=pm,
                    cycle_start_at=_cg_start,
                    snapshot_fetched_at=_cg_snap,
                ):
                    continue
            elif not getattr(pm, "has_live_quotes", False):
                continue  # no guard: fallback to original inline check

            mip = pm.mid_price
            vig = pm.vig
            if mip <= 0.0 or mip >= 1.0:
                continue

            # T-228: markets priced this wide have never produced a qualifying signal
            # in production (see VIG_CEILING derivation above) — skip before paying the
            # Binomial p_t4 / semantic-guard / C4 evaluation cost. Still log a lightweight
            # record (no p_t4/edge fields) so EXP-ARITH-MLB-01/EXP-FLOW-MLB-01 retain
            # visibility into how much volume this filter removes (GG-067).
            if vig > VIG_CEILING:
                if cycle_log_path is not None:
                    _append_dryrun_record(cycle_log_path, {
                        "ts":           datetime.now(timezone.utc).isoformat(),
                        "cycle_id":     cycle_id,
                        "session_id":   session_id,
                        "game_date":    _ticker_to_game_date(ticker, game_date),  # GG-166
                        "ticker":       ticker,
                        "player_name":  ctx["player_name"],
                        "player_id":    player_id,
                        "threshold":    threshold,
                        "mip":          round(mip, 6),
                        "vig":          round(vig, 6),
                        "vig_skip":     True,
                        "h_so_far":     ls.h_so_far,
                        "ab_so_far":    ls.ab_so_far,
                        "ab_remaining": ab_remaining,
                        "inning":       ls.inning,
                        "batting_slot": batting_slot,
                    })
                continue

            # Layer 3 semantic contract check (ADR-0034): business-logic coherence
            try:
                _sem = SemanticContaminationGuard(
                    ticker=ticker,
                    player_id=player_id,
                    has_live_quotes=getattr(pm, "has_live_quotes", False),
                    mip=mip,
                    player_in_live_game=True,   # ls not None: checked in outer loop
                    game_in_progress=bool(live_states),
                    cycle_id=cycle_id,
                    audit=audit,
                    session_id=session_id,
                    snapshot_id=SNAPSHOT_ID,
                    h_needed=max(0, threshold - ls.h_so_far),
                    ab_remaining=ab_remaining,
                )
                if not _sem.is_clean():
                    continue
            except T4CorrDownwardViolation:
                audit.log(
                    component=COMPONENT,
                    event_type="t4_corr_downward_violation",
                    payload={"ticker": ticker, "player_id": player_id},
                    severity="CRITICAL",
                    session_id=session_id,
                    snapshot_id=SNAPSHOT_ID,
                )
                raise  # propagate to main loop kill switch

            p_t4 = p_hits_gte_threshold(
                h_so_far=ls.h_so_far,
                threshold=threshold,
                # GG-105/APR-0025/ADR-0047: shrunk estimate feeds the live Binomial calc
                # instead of the raw noisy ba_l10 ratio — this is the remediation itself.
                ba_l10=ba_l10_shrunk,
                ab_remaining=ab_remaining,
            )

            gross_edge = p_t4 - mip - vig
            kalshi_fee = 0.07 * mip * (1.0 - mip)
            net_edge   = gross_edge - kalshi_fee

            # GG-067 (SESSION 110): raw per-cycle context, independent of dry_run/fired
            # status, so EXP-ARITH-MLB-01 / EXP-FLOW-MLB-01 have real data to backtest
            # against — previously only the dry_run branch below persisted this context.
            if cycle_log_path is not None:
                _append_dryrun_record(cycle_log_path, {
                    "ts":           datetime.now(timezone.utc).isoformat(),
                    "cycle_id":     cycle_id,
                    "session_id":   session_id,
                    "game_date":    _ticker_to_game_date(ticker, game_date),  # GG-166
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
                    "ba_l10_shrunk": round(ba_l10_shrunk, 6),
                    "h_so_far":     ls.h_so_far,
                    "ab_so_far":    ls.ab_so_far,
                    "ab_remaining": ab_remaining,
                    "inning":       ls.inning,
                    "batting_slot": batting_slot,
                })

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
                        "ba_l10_shrunk": round(ba_l10_shrunk, 6),
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
                    already_fired_game[ticker] = (ls.h_so_far, ab_remaining)
                    logger.info(
                        "T4-MLB DRY_RUN WOULD_FIRE  %-45s  p=%.3f  mip=%.3f  edge=%+.3f",
                        ticker, p_t4, mip, net_edge,
                    )
                continue

            # Normal execution path
            # GG-087: both directions are actionable. gross_edge is the YES-frame
            # edge (p_t4 - mip - vig); a sufficiently negative gross_edge is a
            # legitimate NO-direction edge, not noise to discard — the prior
            # hardcoded YES-only path here silently dropped every NO-side signal,
            # measured at 41.6x the volume of the YES-side signal it acted on.
            # `net_edge` above stays YES-frame for the diagnostic cycle log; the
            # direction-effective edge actually gated/traded on is recomputed
            # here for NO by flipping only the *signal* term (p_t4 - mip) and
            # re-subtracting vig as a cost — do not reuse an unflipped edge
            # value for a NO-direction gate/position (see GG-077, the sign-
            # convention bug this pattern is designed to avoid reintroducing).
            #
            # GG-113: naively negating the whole gross_edge expression here
            # (`-gross_edge`, i.e. `-(p_t4 - mip - vig)` = `(mip - p_t4) + vig`)
            # turns vig from a subtracted cost into an added credit for every
            # NO bet — vig is a bid-ask spread cost and must never flip sign
            # with direction, matching run_exp017.py's compute_pnl_unit()
            # convention (half_vig applied as a cost to price_paid on both
            # YES and NO sides identically). Recompute the NO-direction edge
            # from the signal term directly so vig stays a cost in both
            # branches, instead of algebraically re-deriving it from the
            # already vig-inclusive gross_edge.
            if gross_edge > 0.0:
                direction = "YES"
                directional_gross_edge = gross_edge
            elif gross_edge < 0.0:
                direction = "NO"
                directional_gross_edge = (mip - p_t4) - vig
            else:
                evaluated += 1
                continue

            directional_net_edge = directional_gross_edge - kalshi_fee

            # GG-149: intra-book (T4 vs T4) offsetting-position suppression.
            # Simultaneous YES+NO on one contract from one account is
            # economically a wash trade — Kalshi (CFTC-regulated DCM)
            # prohibits wash trades/self-matching regardless of intent. Skip
            # (never close-and-reverse — that's a separate strategy decision
            # requiring its own ADR under ADR-0018, out of scope here).
            _opposing_t4 = _find_open_position_opposite_direction(
                trader.get_state().get("open_positions", []), ticker, direction
            )
            if _opposing_t4 is not None:
                audit.warning(
                    COMPONENT, "t4_offsetting_suppressed",
                    payload={
                        "ticker": ticker,
                        "existing_direction": _opposing_t4.get("direction"),
                        "blocked_direction": direction,
                        "existing_edge": _opposing_t4.get("fee_net_edge"),
                        "blocked_edge": round(directional_net_edge, 6),
                    },
                    session_id=session_id,
                )
                evaluated += 1
                continue

            # GG-149: cross-book (T1 vs T4) alarm-only. T1/T4 are pool-isolated
            # (ADR-0023) with separate processes/portfolio files — no blocking
            # coordination mechanism exists or should be improvised here.
            _opposing_t1 = _t1_open_position_opposite_direction(ticker, direction)
            if _opposing_t1 is not None:
                audit.warning(
                    COMPONENT, "t4_t1_cross_book_direction_conflict",
                    payload={
                        "ticker": ticker,
                        "t1_direction": _opposing_t1.get("direction"),
                        "t4_direction": direction,
                        "t1_edge": _opposing_t1.get("fee_net_edge"),
                        "t4_edge": round(directional_net_edge, 6),
                    },
                    session_id=session_id,
                )
                # Alarm-only — do not suppress or continue.

            # ADR-0050 addendum §B (2026-07-30): flat DOLLARS != flat exposure. entry_price
            # is the true price paid for THIS bet's direction (YES pays mip, NO pays
            # 1-mip) — distinct from the p_entry=mip convention used elsewhere in this
            # pipeline as a YES-frame diagnostic/ledger field. T4M-PROJ trades are paper
            # positions (store.stage_order()/paper_trader.py), not literal Kalshi orders
            # pre-G6, so "contracts" is a notional cap on payout, not an integer-order
            # constraint: stake = min(flat_stake, max_contracts * entry_price). This
            # lands every bet at entry_price >= flat_stake/max_contracts ($0.10 here) at
            # exactly the flat $1.00 stake (min() saturates at flat_stake), while a
            # sub-10c entry is capped at a uniform $10 max payout (max_contracts * $1/
            # contract) instead of an unbounded one. A floor()-based integer-contract
            # count would under-stake most non-$0.10-aligned prices even above the cap
            # threshold (e.g. $0.395 -> 2 contracts -> $0.79, not $1.00) — rejected for
            # exactly that reason; verified against the addendum's own worked example
            # ($0.005 entry -> $0.05 stake / effectively 10 contracts).
            entry_price = mip if direction == "YES" else (1.0 - mip)
            if entry_price <= 0.0:
                evaluated += 1
                continue
            measurement_stake_usd, contracts, price_stratum = measurement_stake_and_stratum(
                entry_price
            )

            fc_record = {
                "forecast_id":         f"T4-MLB-{cycle_id}-{ticker[-12:]}",
                "p_estimate":          p_t4,
                "market_implied_prob": mip,
                "edge":                directional_net_edge,
                "gross_edge":          gross_edge,
                "recommended_direction": direction,
                "entry_price_paid":    round(entry_price, 4),  # ADR-0050 addendum §C
                "price_stratum":       price_stratum,          # ADR-0050 addendum §C
                "contracts":           contracts,              # ADR-0050 addendum §B
            }

            ok, approval = engine.evaluate_forecast(
                forecast_record=fc_record,
                current_daily_loss=current_daily_loss,
                current_drawdown_pct=drawdown,
                session_id=session_id,
                current_open_exposure_usd=t4_deployed_usd,
                portfolio_equity_usd=t4_band_budget,
                pool_isolated=True,
                fixed_stake_usd=measurement_stake_usd,  # ADR-0050 + addendum §B cap
            )
            evaluated += 1

            if not ok:
                logger.error("C4/C6 write failure at %s — halting cycle", ticker)
                return evaluated, fired, t4_deployed_usd

            if approval.get("approval_status") != "APPROVED":
                continue

            # ADR-0050 (2026-07-30): flat $1.00 measurement stake (contract-capped per
            # addendum §B) — replaces the prior "1 contract at market price" policy.
            # RiskEngine already set approved_size to measurement_stake_usd via
            # fixed_stake_usd= above (KELLY_T4 stays 0.0; sizing_mode="fixed_measurement"
            # on the approval record confirms the bypass took the intended path).
            approved_size = approval["approved_size"]
            approval = {**approval, "model_p": p_t4, "edge": directional_net_edge,
                        "gross_edge": gross_edge, "band": "T4M-PROJ",  # T-253
                        "entry_price_paid": round(entry_price, 4),  # ADR-0050 addendum §C
                        "price_stratum": price_stratum,             # ADR-0050 addendum §C
                        "contracts": contracts}                     # ADR-0050 addendum §B

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
                game_date=_ticker_to_game_date(ticker, game_date),  # GG-166: per-position, not session wall-clock
                session_id=session_id,
                pool_isolated=True,
                h_so_far_at_entry=ls.h_so_far,
                ab_remaining_at_entry=ab_remaining,
            )
            if not ok_pos:
                logger.error("PaperTrader write failure at %s — halting cycle", ticker)
                return evaluated, fired, t4_deployed_usd

            if pos:
                store.mark_fired(order_id)
                already_fired_game[ticker] = (ls.h_so_far, ab_remaining)
                fired += 1
                t4_deployed_usd += approved_size
                logger.info(
                    "T4-MLB FIRED  %-45s  %-3s  $%5.2f  p=%.3f  mip=%.3f  edge=%+.3f"
                    "  budget_used=$%.2f/%.2f  h=%d ab_rem=%d  cycle=%s",
                    ticker, direction, approved_size, p_t4, mip, directional_net_edge,
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
        schedule_params: dict[str, str | int] = {
            "sportId": _MLB_SPORT_ID, "date": date_str, "hydrate": "team",
        }
        r = requests.get(
            _MLB_SCHEDULE_API,
            params=schedule_params,
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

    # T-216 (GG-062): refuse to start a second concurrent evaluation loop.
    # Must run before any other setup — a lost race here means this process
    # exits before touching the shared portfolio/audit/staged-order files.
    if not acquire_singleton_lock():
        logger.error(
            "T4-MLB singleton lock held by another live process (%s) — "
            "refusing to start a second concurrent evaluation loop (GG-062/T-216). "
            "Exiting.", SINGLETON_LOCK_PATH,
        )
        sys.exit(1)

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
    _loaded_pregame_file = _latest_pregame_file()
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
    # T-213/GG-060 edge-decision classification sink (Phase 2 — T4 parity with T1).
    edge_logger = AuditLogger(log_path=_LOGS_DIR / "audit_mlb_t4_edge_decisions.jsonl", min_severity="INFO")
    store  = StagedOrderStore(_STAGED_DB_PATH)
    try:
        kalshi = KalshiMarketClient.from_env()
        _signing_ready = kalshi.has_signing_key()
    except Exception as _e:
        logger.warning("Kalshi client init failed — orders will be local_only: %s", _e)
        kalshi = None
        _signing_ready = False
    trader = PaperTrader(
        portfolio_path=_PORTFOLIO_PATH,
        logger=audit,
        kalshi_client=kalshi if _signing_ready else None,
    )

    # ---- T4 band budget ----
    t4_state = trader.get_state()
    t4_band_budget = _compute_t4_band_budget(t4_state)
    t4_deployed_game = _reconstruct_t4_ledger(t4_state, _game_date_window(game_date))
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
            edge_logger=edge_logger,
        )

    # ---- Game ID discovery ----
    _eval_date = date.today()   # tracks which UTC date game_ids/pregame are loaded for
    # GG-143: a cold start (fresh process, empty in-memory tracked set) that lands
    # after 00:00 UTC otherwise only ever discovers the new day's STATUS_SCHEDULED
    # games — every game still in progress from the prior evening goes unpolled for
    # the rest of the night. Mirror the in-loop rollover (_rollover_game_ids, GG-058)
    # by seeding the merge with a prior-day query instead of trusting only "today".
    prior_day_game_ids = _espn_mlb_game_ids_today(for_date=_eval_date - timedelta(days=1))
    today_game_ids = _espn_mlb_game_ids_today()
    game_ids: list[str] = _rollover_game_ids(prior_day_game_ids, today_game_ids)
    _carried_over_coldstart = [gid for gid in game_ids if gid not in today_game_ids]
    if _carried_over_coldstart:
        logger.info(
            "T4-MLB cold-start carried over %d still-live game(s) from %s: %s",
            len(_carried_over_coldstart), _eval_date - timedelta(days=1), _carried_over_coldstart,
        )
    logger.info("Initial MLB game IDs: %s", game_ids or "(none yet)")

    # GG-143 restart alarm: an overnight cold start that ends up tracking zero games
    # is only safe if ESPN genuinely shows no live game. Re-verify independently of
    # the merge above so a future regression there still gets caught rather than
    # failing silently (systemctl is-active stays green, no HALT fires).
    _restart_utc = datetime.now(timezone.utc)
    if not game_ids and 0 <= _restart_utc.hour < 6:
        _still_live = [
            gid for gid in (prior_day_game_ids + today_game_ids)
            if _espn_game_status(gid) == _ESPN_STATUS_IN_PROGRESS
        ]
        if _still_live:
            logger.error(
                "T4-MLB COLD_START_BLIND: restart at %s UTC tracked 0 games but ESPN "
                "shows %d in-progress game(s): %s (GG-143)",
                _restart_utc.isoformat(), len(_still_live), _still_live,
            )
            audit.log(
                component=COMPONENT,
                event_type="t4_cold_start_blind",
                payload={
                    "restart_utc": _restart_utc.isoformat(),
                    "espn_in_progress_game_ids": _still_live,
                },
                severity="CRITICAL",
                session_id=session_id,
                snapshot_id=SNAPSHOT_ID,
            )

    # ---- Contamination guard (session-scoped) ----
    contamination_guard = LiveDataFreshnessGuard(audit=audit, session_id=session_id)

    # ---- Main polling loop ----
    cycle_n = 0
    total_evaluated = 0
    total_fired = 0
    # Game-day dedup guard: ticker -> (h_so_far, ab_remaining) at that ticker's last
    # entry this game day. Reset at UTC midnight (date rollover). Prevents re-betting
    # the same market every 90-second cycle while the live state hasn't moved
    # (GG-050 fix — moved out of _run_cycle where it was per-cycle only).
    # T-209: reconstructed from the persisted portfolio (not started empty) so a process
    # restart mid-game does not forget each ticker's last-fired state.
    # T-225: re-keyed from a permanent one-shot set to a per-ticker last-state dict —
    # a ticker may re-fire once (h_so_far, ab_remaining) has actually changed, per the
    # operator's 2026-07-03 design ruling (DECISION_LOG.md).
    already_fired_game: dict[str, tuple[int, int]] = _reconstruct_fired_ticker_states(t4_state, _game_date_window(game_date))
    if already_fired_game:
        logger.info(
            "T4-MLB dedup guard reconstructed: %d ticker(s) already fired for %s",
            len(already_fired_game), game_date,
        )

    while True:
        if kill_switch_armed(KILL_SWITCH_PATH):
            logger.warning(
                "T4-MLB kill switch armed — sleeping 10s. rm %s to resume.",
                KILL_SWITCH_PATH,
            )
            time.sleep(10)
            continue

        try:
            # ---- Date-rollover refresh (24/7 systemd service support) ----
            # When running as a persistent service, UTC date rolls over at midnight.
            # Refresh game_ids, pregame context, batting slots, and band budget so
            # tomorrow's games are evaluated with correct state (not yesterday's).
            today = date.today()
            if today != _eval_date:
                _prior_eval_date = _eval_date
                logger.info(
                    "T4-MLB date rollover %s → %s — refreshing game IDs, pregame, band budget",
                    _eval_date, today,
                )
                _eval_date = today
                game_date = today.isoformat()
                newly_discovered = _espn_mlb_game_ids_today()
                merged = _rollover_game_ids(game_ids, newly_discovered)
                carried_over = [gid for gid in merged if gid not in newly_discovered]
                if carried_over:
                    logger.info(
                        "T4-MLB rollover: carrying over %d not-yet-final game(s) "
                        "from %s: %s",
                        len(carried_over), _prior_eval_date, carried_over,
                    )
                game_ids[:] = merged
                # Refresh pregame context and batting slots for the new day.
                # GG-058: merge, don't clear-then-replace — if a carried-over
                # game's players aren't in the new day's pregame file (most
                # recent file only, per _load_pregame_context()), clearing
                # first would silently drop their matching context even
                # though we're still polling their game.
                by_player_id_r, _, name_to_pregame_r = _load_pregame_context()
                by_player_id.update(by_player_id_r)
                name_to_pregame.update(name_to_pregame_r)
                _loaded_pregame_file = _latest_pregame_file()
                batting_slots = _load_t2_batting_slots()
                # Reconstruct band budget for the new date
                t4_state = trader.get_state()
                t4_band_budget = _compute_t4_band_budget(t4_state)
                # GG-081/GG-082 (2026-07-04): reconstruct against {new_day, prior_day}, not
                # new_day alone. A game still live across UTC midnight keeps its positions'
                # game_date pinned to the day it started — filtering on the new day only
                # silently dropped that game's ledger exposure and dedup state the moment
                # the clock crossed midnight (confirmed root cause of the TBJCAMINERO13
                # double-fire, 2026-07-02 23:43/2026-07-03 00:01 UTC, same session_id).
                t4_deployed_game = _reconstruct_t4_ledger(t4_state, _game_date_window(game_date))
                # T-209: reconstruct (not just clear) — new day is normally empty,
                # but this keeps the guard correct if the date rollover races a restart.
                already_fired_game.clear()
                already_fired_game.update(_reconstruct_fired_ticker_states(t4_state, _game_date_window(game_date)))
                logger.info(
                    "T4-MLB rollover complete: %d games, %d players, budget=$%.2f",
                    len(game_ids), len(by_player_id), t4_band_budget,
                )

            # Re-discover games if we have none yet
            if not game_ids:
                game_ids[:] = _espn_mlb_game_ids_today()
                if game_ids:
                    logger.info("MLB game(s) discovered: %s", game_ids)
                else:
                    logger.debug("No active MLB games found — sleeping 60s")
                    time.sleep(60)
                    continue

            # Reload pregame context if empty, or if a newer pregame_mlb_*.json has
            # been written since our last load (GG-181: PIPE-06pre commonly runs
            # mid-day UTC, well after this process's own UTC-midnight date rollover
            # already merged in whatever file was "most recent" at that moment —
            # often the prior day's, if today's hadn't been written yet. The old
            # `if not by_player_id` guard only ever fired on a cold/empty start, so
            # once any file had been merged in, a same-day-later PIPE-06pre write
            # was never picked up for the rest of the day.)
            _latest_file = _latest_pregame_file()
            if not by_player_id or _latest_file != _loaded_pregame_file:
                by_player_id_new, _bt, name_to_pregame_new = _load_pregame_context()
                if by_player_id_new:
                    by_player_id.update(by_player_id_new)
                    name_to_pregame.update(name_to_pregame_new)
                    logger.info(
                        "Pregame context reloaded: %d players (file=%s)",
                        len(by_player_id), _latest_file.name if _latest_file else None,
                    )
                _loaded_pregame_file = _latest_file

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
            if kalshi is None:
                logger.warning(
                    "Kalshi client unavailable (init failed at startup) — sleeping %ds", POLL_INTERVAL_S
                )
                time.sleep(POLL_INTERVAL_S)
                continue
            ok, snapshot = kalshi.fetch_player_points_markets(series_ticker=SERIES_MLB_PLAYER_HITS)
            snapshot_fetched_at = datetime.now(timezone.utc)
            # cycle_start_at captured AFTER both fetches — Kalshi pagination with rate-limit
            # backoff (4+8+16+32s) burns 60–130s before this line; capturing before the fetches
            # caused game_state_fresh to expire before _run_cycle() ran (GG-052 root cause).
            cycle_start_at = snapshot_fetched_at
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
                already_fired_game=already_fired_game,
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
                contamination_guard=contamination_guard,
                cycle_start_at=cycle_start_at,
                snapshot_fetched_at=snapshot_fetched_at,
                cycle_log_path=CYCLE_LOG_PATH,
            )

            cycle_n += 1
            total_evaluated += ev
            total_fired += fi

            budget_pct = (
                t4_deployed_game / t4_band_budget * 100.0
            ) if t4_band_budget > 0 else 0.0
            logger.info(
                "─ cycle=%s  eval=%d fired=%d │ session: eval=%d fired=%d"
                " │ T4_budget: $%.2f/$%.2f (%.0f%%)  │ bankroll=$%.2f"
                " │ cg_halts=%d(stale=%d)",
                cycle_id, ev, fi,
                total_evaluated, total_fired,
                t4_deployed_game, t4_band_budget, budget_pct,
                trader.get_state()["bankroll_usd"],
                contamination_guard.total_halts,
                contamination_guard.staleness_halts,
            )

            time.sleep(POLL_INTERVAL_S)

        except Exception as exc:
            logger.error(
                "Unhandled exception in T4-MLB main loop — sleeping %ds: %s",
                POLL_INTERVAL_S, exc, exc_info=True,
            )
            time.sleep(POLL_INTERVAL_S)


if __name__ == "__main__":
    _enforce_paper_mode_guard()
    main()
