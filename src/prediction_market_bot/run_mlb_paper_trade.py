"""
PIPE-05: MLB Paper Trading Pipeline
====================================
Pipeline:     PIPE-05 (MLB simulated decision cycle)
Phase:        Phase 6 (ENV-02 — paper trading)
Schedule:     Cron: 23:30 UTC daily (after T1 NBA window)
Environment:  ENV-02 — BOT_ENV=paper required; no real capital
Prerequisite: models/mlb_v1_model.joblib (run scripts/train_mlb_model.py)

Steps:
  1. Verify ENV-02 (BOT_ENV=paper); activate C4 in-process
  2. Log open MLB positions (resolution requires run_resolve_mlb.py — T-187E)
  3. Load mlb_v1_model.joblib artifact (pipeline, feature_names, col_medians)
  4. Load feature CSV; build latest-row-per-player lookup
  5. Fetch ALL live Kalshi KXMLBHIT markets via VenueRouter (sport="MLB")
  6. Abort if any MLB game is in progress (live market contamination guard)
  7. For each player/threshold with a live market:
     a. Look up player's latest feature row (name-normalised)
     b. Skip if player not in feature CSV (no fallback — MLB has no dynamic lookup)
     c. Inject threshold=float(k) into feature vector
     d. Predict_proba → calibrate_probability(sport="mlb")
     e. Calculate edge (gross edge - Kalshi fee)
     f. Route through C4 RiskEngine (Kelly sizing, hard limits, reserve gate)
     g. If APPROVED and reserve mandate satisfied: record paper order
  8. Log everything to C6; write paper_mlb_YYYYMMDD.json report
  9. Print portfolio summary

Model artifact schema (mlb_v1_model.joblib):
  pipeline, feature_names, col_medians, model_version, thresholds, sport="mlb"

  threshold is IN feature_names (alphabetically last). For each KXMLBHIT market
  with threshold k, inject threshold=float(k) before building the feature vector.

Calibration:
  CALIBRATION_TEMPERATURE["mlb"] = 1.0 → identity (no resolved calibration data
  yet). Probability is passed through unchanged. Revisit at T-187F.

Resolution note (T-187E):
  PaperTrader.resolve_pending() is NBA-specific (uses nba_api). MLB positions
  stay open until run_resolve_mlb.py (T-187E) is implemented and run separately.
  This runner logs pending MLB positions at startup but does not close them.

Security:
  BOT_C4_ACTIVE is set in-process only after BOT_ENV=paper is verified.
  If VENUE_PRIVATE_KEY_PATH is set, orders fire to Kalshi demo (ADR-0008).
  BOT_C4_ACTIVE must NOT be set externally in ENV-02's .env.

How to run:
  source /opt/prediction-market-bot/.env
  BOT_ENV=paper PYTHONPATH=src /opt/prediction-market-bot/venv/bin/python \\
      src/prediction_market_bot/run_mlb_paper_trade.py
"""

from __future__ import annotations

import json
import os
import re
import sys
import uuid
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import requests

_SRC_ROOT = Path(__file__).parent.parent.parent
if str(_SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(_SRC_ROOT))

# Verify ENV-02 before importing anything else
if os.environ.get("BOT_ENV", "").lower() != "paper":
    print(
        "FATAL: PIPE-05 requires BOT_ENV=paper. Set BOT_ENV=paper in your .env.",
        file=sys.stderr,
    )
    sys.exit(1)

# Activate C4 in-process (paper trading; verified ENV-02 above)
os.environ["BOT_C4_ACTIVE"] = "true"

from prediction_market_bot.c1_signal_ingestion.mlb_ingestion import MLBIngestionClient
from prediction_market_bot.c1_signal_ingestion.mlb_pitcher_stats_store import (
    MLBPitcherStatsStore,
)
from prediction_market_bot.c3_forecasting.calibration import calibrate_probability
from prediction_market_bot.c4_risk_engine.risk import RiskEngine
from prediction_market_bot.c5_execution.kalshi_client import KalshiMarketClient
from prediction_market_bot.c5_execution.market_mapper import normalize_player_name
from prediction_market_bot.c5_execution.paper_trader import PaperTrader
from prediction_market_bot.c5_execution.venue_router import VenueRouter
from prediction_market_bot.c6_audit_logger.audit_logger import AuditLogger
from prediction_market_bot.c7_monitoring.monitor import SystemMonitor
from prediction_market_bot.execution_bands import BAND_REGISTRY, ExecutionBand, get_band_config

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

SESSION_ID    = f"PT-MLB-{uuid.uuid4().hex[:8].upper()}"
# T1 night-before baseline: target tomorrow's games so that cron at 23:30 UTC
# (7:30pm ET) fires before any of tomorrow's games are live. The contamination
# guard (_is_mlb_game_in_progress) checks GAME_DATE_ISO — tomorrow's games are
# always "Preview" at 23:30 UTC so the guard correctly passes.
_now_utc      = datetime.now(tz=timezone.utc)
_target_date  = (_now_utc + timedelta(days=1)).date()
GAME_DATE     = _target_date.strftime("%Y%m%d")
GAME_DATE_ISO = _target_date.strftime("%Y-%m-%d")

MODEL_PATH    = Path("models/mlb_v1_model.joblib")
FEATURE_CSV   = Path("exp_output/MLB/mlb_feature_matrix.csv")
SNAPSHOT_ID   = "SNAP-MLB-T187D"
LOG_DIR       = Path(os.environ.get("LOG_DIR", str(_SRC_ROOT / "logs")))
PORTFOLIO_PATH = LOG_DIR / "paper_portfolio_mlb.json"
REPORT_PATH   = LOG_DIR / f"paper_mlb_{GAME_DATE}.json"

EDGE_YES = 0.02
EDGE_NO  = -0.02

# YES-only diagnostic gate: until MLB directional edge data exists, match NBA's
# pre-DS ruling default (all NO signals logged as counterfactuals, not placed).
# Override via MLB_PAPER_YES_ONLY=false in .env once DS rules.
PAPER_YES_ONLY = os.environ.get("MLB_PAPER_YES_ONLY", "true").lower() == "true"
RESERVE_MANDATE_PCT = float(os.environ.get("RESERVE_MANDATE_PCT", "0.40"))
MIN_BET_PAPER = float(os.environ.get("MIN_BET_MLB_PAPER", "1.0"))

# T1 Kelly fraction from band registry (ADR-0010: 0.10)
T1_KELLY = get_band_config(ExecutionBand.T1_MULTI_DAY).kelly_fraction

# MLB Kalshi hit market thresholds the model was trained on
_MODEL_THRESHOLDS: frozenset[int] = frozenset({1, 2})

# MLB Stats API
_MLB_SCHEDULE_URL = "https://statsapi.mlb.com/api/v1/schedule"


# ---------------------------------------------------------------------------
# Non-feature columns (mirror train_mlb_model.py _NON_FEATURE_MLB exactly)
# ---------------------------------------------------------------------------

_NON_FEATURE_MLB: frozenset[str] = frozenset({
    "player_id", "player_name", "team_abbreviation", "game_id", "game_date",
    "season", "season_type", "matchup", "opponent_team_abbr",
    "snapshot_id", "feature_run_id", "feature_version",
    "temporal_cutoff", "train_test_label", "ingestion_run_id", "ingested_at",
    "ab", "h", "doubles", "triples", "hr", "rbi", "bb", "k", "hbp", "sf",
    "y_target", "game_date_dt",
    "threshold",  # not in feature matrix — each pipeline is threshold-specific
})


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _utc_now() -> str:
    return datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


def _impute(X: np.ndarray, medians: np.ndarray) -> np.ndarray:
    X = X.copy().astype(float)
    mask = np.isnan(X)
    X[mask] = np.take(medians, np.where(mask)[1])
    return X


def _ticker_to_game_date(ticker: str) -> str:
    """Parse KXMLBHIT game date.

    Format: KXMLBHIT-{DD}{MON}{YY}{TIME}{AWAYTEAM}{HOMETEAM}-...
    Example: KXMLBHIT-26JUN241607BALLAA-... → 2024-06-26
    """
    m = re.search(r"-([0-9]{2})([A-Z]{3})([0-9]{2})[0-9]{4}", ticker)
    if m:
        try:
            return datetime.strptime(
                f"{m.group(1)}{m.group(2)}{m.group(3)}", "%d%b%y"
            ).strftime("%Y-%m-%d")
        except ValueError:
            pass
    return GAME_DATE_ISO


def _is_mlb_game_in_progress(game_date: str) -> bool:
    """Check whether any MLB game for game_date is currently live.

    Uses MLB Stats API /api/v1/schedule. Returns True if any game has
    abstractGameState == "Live". Returns False on API failure (permissive).
    """
    try:
        resp = requests.get(
            _MLB_SCHEDULE_URL,
            params={"sportId": 1, "date": game_date},
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        for date_block in data.get("dates", []):
            for game in date_block.get("games", []):
                state = game.get("status", {}).get("abstractGameState", "")
                if state == "Live":
                    return True
    except Exception:
        pass
    return False


def _safe_int(v: object) -> int | None:
    """Return int(v) or None if v is None/NaN/non-numeric."""
    if v is None:
        return None
    try:
        f = float(v)  # type: ignore[arg-type]
        if np.isnan(f):
            return None
        return int(f)
    except (TypeError, ValueError):
        return None


_SP_OVERRIDE_FIELDS = frozenset({
    "opp_sp_era_l5", "opp_sp_k9_l5", "opp_sp_bb9_l5", "opp_sp_is_known"
})


def _build_mlb_feature_vector(
    row: pd.Series,
    feature_names: list[str],
    col_medians: np.ndarray,
    sp_override: dict | None = None,
) -> np.ndarray:
    """Build a (1, n_features) feature matrix for one player row.

    If sp_override is provided, SP fields are taken from the override dict
    (tonight's live SP) rather than the stale historical row value.
    """
    vals: list[float] = []
    for col in feature_names:
        if sp_override is not None and col in _SP_OVERRIDE_FIELDS:
            v = sp_override.get(col)
            vals.append(float(v) if v is not None else np.nan)
        elif col in row.index:
            v = row[col]
            vals.append(float(v) if pd.notna(v) else np.nan)
        else:
            vals.append(np.nan)
    X = np.array([vals], dtype=float)
    return _impute(X, col_medians)


def _build_live_sp_override(
    today_iso: str,
    latest_df: pd.DataFrame,
    client: MLBIngestionClient,
    logger: AuditLogger,
    session_id: str,
) -> dict[int, dict]:
    """Fetch tonight's actual starting pitchers and return per-player SP override dicts.

    Returns a dict keyed by player_id (int). Each value has keys matching
    _SP_OVERRIDE_FIELDS. Returns {} on API failure so the caller can fall back
    to historical SP data without halting.
    """
    ok, starters = client.fetch_game_starters(today_iso, session_id)
    if not ok or not starters:
        return {}

    # Build team_id → (game_pk, is_home) mapping for tonight's games
    team_to_game: dict[int, tuple[int, bool]] = {}
    for game_pk, info in starters.items():
        htid = _safe_int(info.get("home_team_id"))
        atid = _safe_int(info.get("away_team_id"))
        if htid is not None:
            team_to_game[htid] = (game_pk, True)
        if atid is not None:
            team_to_game[atid] = (game_pk, False)

    # Build player_id → opp_sp_id mapping from the latest CSV row
    sp_ids_needed: set[int] = set()
    player_sp_map: dict[int, int | None] = {}
    player_sp_known: dict[int, bool] = {}

    for _, row in latest_df.iterrows():
        pid = _safe_int(row.get("player_id"))
        tid = _safe_int(row.get("team_id"))
        if pid is None or tid is None or tid not in team_to_game:
            continue
        game_pk, is_home = team_to_game[tid]
        sp_key = "away_sp_id" if is_home else "home_sp_id"
        sp_id_raw = starters[game_pk].get(sp_key)
        sp_id = _safe_int(sp_id_raw)
        known = sp_id is not None
        player_sp_map[pid] = sp_id
        player_sp_known[pid] = known
        if known:
            sp_ids_needed.add(sp_id)  # type: ignore[arg-type]

    if not player_sp_map:
        return {}

    # Fetch pitcher game logs for each unique SP playing tonight
    pitcher_store = MLBPitcherStatsStore()
    current_season = str(date.today().year)
    for sp_id in sp_ids_needed:
        ok_p, df_p = client.fetch_pitcher_game_log(
            sp_id, current_season, session_id=session_id
        )
        if ok_p and df_p is not None and not df_p.empty:
            pitcher_store.add_pitcher_log(sp_id, df_p)

    logger.info(
        "PIPE-05", "live_sp_overlay_fetched",
        payload={
            "n_games": len(starters),
            "n_players_mapped": len(player_sp_map),
            "n_sp_fetched": len(sp_ids_needed),
        },
        session_id=session_id,
    )

    # Build per-player override dict
    result: dict[int, dict] = {}
    for pid, sp_id in player_sp_map.items():
        is_known = player_sp_known.get(pid, False)
        era = pitcher_store.get_era_l5(sp_id, today_iso) if sp_id is not None else None
        k9  = pitcher_store.get_k_per_9_l5(sp_id, today_iso) if sp_id is not None else None
        bb9 = pitcher_store.get_bb_per_9_l5(sp_id, today_iso) if sp_id is not None else None
        result[pid] = {
            "opp_sp_era_l5":  era,
            "opp_sp_k9_l5":   k9,
            "opp_sp_bb9_l5":  bb9,
            "opp_sp_is_known": 1.0 if is_known else 0.0,
        }
    return result


def _write_report(orders: list, bankroll: float, trader: PaperTrader) -> None:
    summary = trader.summary()
    report = {
        "session_id": SESSION_ID,
        "game_date": GAME_DATE,
        "run_at": _utc_now(),
        "sport": "mlb",
        "bets_placed": len(orders),
        "portfolio": summary,
        "orders": orders,
    }
    REPORT_PATH.write_text(json.dumps(report, indent=2))
    print(f"\n[DONE] Report: {REPORT_PATH}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    logger = AuditLogger(LOG_DIR / "audit_mlb.jsonl", min_severity="INFO")

    # Kalshi client — loads RSA key if VENUE_PRIVATE_KEY_PATH is set (ADR-0008)
    try:
        kalshi_client = KalshiMarketClient.from_env()
        signing_ready = kalshi_client.has_signing_key()
    except Exception as e:
        kalshi_client = None
        signing_ready = False
        logger.warning(
            "PIPE-05", "kalshi_client_init_failed",
            payload={"error": str(e)}, session_id=SESSION_ID,
        )

    trader = PaperTrader(
        PORTFOLIO_PATH,
        logger,
        kalshi_client=kalshi_client,
    )
    # Ensure the portfolio file exists so dashboard and monitoring tools see it
    # even when no bets are placed (e.g., contamination guard fires before bets).
    trader.ensure_persisted()

    print(f"\n[PIPE-05] MLB Paper trading — {GAME_DATE}")
    print(f"Session:  {SESSION_ID}")
    print(f"BOT_ENV:  {os.environ.get('BOT_ENV')}  |  C4: ACTIVE  |  Sport: MLB")
    print(f"Kalshi:   {'LIVE ORDERS (demo)' if signing_ready else 'local-only (no RSA key)'}")
    print(f"Gate:     YES-ONLY {'ACTIVE' if PAPER_YES_ONLY else 'OFF'}")

    logger.info(
        "PIPE-05", "paper_run_start",
        payload={
            "session_id": SESSION_ID,
            "game_date": GAME_DATE,
            "sport": "mlb",
            "yes_only_gate": PAPER_YES_ONLY,
        },
        session_id=SESSION_ID, snapshot_id=SNAPSHOT_ID,
    )

    # ------------------------------------------------------------------
    # Band registry startup validation
    # ------------------------------------------------------------------
    band_violations = BAND_REGISTRY.validate()
    if band_violations:
        for v in band_violations:
            print(f"[BAND_REGISTRY] WARNING: {v}")
            logger.warning(
                "PIPE-05", "band_registry_violation",
                payload={"violation": v}, session_id=SESSION_ID,
            )
    else:
        print("[BAND_REGISTRY] OK — no violations")

    # ------------------------------------------------------------------
    # 1. Log open MLB positions (resolution is external — T-187E)
    # ------------------------------------------------------------------
    portfolio = trader.get_state()
    n_open = len(portfolio.get("open_positions", []))
    if n_open > 0:
        print(f"\n[RESOLVE] {n_open} open MLB position(s) pending.")
        print("  NOTE: MLB position resolution requires run_resolve_mlb.py (T-187E).")
        print("  Open positions will remain until that script is run.")
        logger.info(
            "PIPE-05", "mlb_positions_pending_resolution",
            payload={
                "n_open": n_open,
                "note": "MLB resolve requires run_resolve_mlb.py (T-187E)",
            },
            session_id=SESSION_ID,
        )
    else:
        print("\n[RESOLVE] No open MLB positions.")

    # ------------------------------------------------------------------
    # 2. Load model
    # ------------------------------------------------------------------
    if not MODEL_PATH.exists():
        print(
            f"ERROR: {MODEL_PATH} not found — run scripts/train_mlb_model.py first.",
            file=sys.stderr,
        )
        sys.exit(1)

    artifact      = joblib.load(MODEL_PATH)
    pipelines     = artifact["pipelines"]
    feature_names: list[str] = artifact["feature_names"]
    col_medians: np.ndarray  = artifact["col_medians"]
    model_version: str       = artifact["model_version"]
    model_thresholds: list[int] = artifact.get("thresholds", [1, 2])
    sport_label: str         = artifact.get("sport", "mlb")

    if sport_label.lower() != "mlb":
        print(
            f"ERROR: Model artifact sport='{sport_label}' — expected 'mlb'. "
            f"Wrong model file?",
            file=sys.stderr,
        )
        sys.exit(1)

    print(f"\n[MODEL] {model_version} | sport={sport_label} | "
          f"{len(feature_names)} features | thresholds={model_thresholds}")

    # ------------------------------------------------------------------
    # 3. Load feature CSV → latest-row-per-player lookup
    # ------------------------------------------------------------------
    if not FEATURE_CSV.exists():
        print(f"ERROR: {FEATURE_CSV} not found — run scripts/generate_mlb_features.py first.", file=sys.stderr)
        sys.exit(1)

    df = pd.read_csv(FEATURE_CSV, low_memory=False)
    df["game_date_dt"] = pd.to_datetime(df["game_date"], errors="coerce")
    latest = df.sort_values("game_date_dt").groupby("player_id").last().reset_index()

    # Name-normalised cohort lookup: normalize_player_name → latest row
    cohort_lookup: dict[str, pd.Series] = {}
    for _, row in latest.iterrows():
        norm = normalize_player_name(str(row.get("player_name", "")))
        cohort_lookup[norm] = row

    print(f"[FEATURE CSV] {len(df)} rows | {len(latest)} players in feature CSV")
    logger.info(
        "PIPE-05", "feature_csv_loaded",
        payload={"csv_rows": len(df), "players": len(latest)},
        session_id=SESSION_ID, snapshot_id=SNAPSHOT_ID,
    )

    # ------------------------------------------------------------------
    # 3b. Build live SP overlay (T-187G)
    # Fetches tonight's actual SPs via MLB Stats API and overwrites stale
    # opp_sp_* values from the historical feature CSV. Falls back to
    # historical values silently if the API call fails.
    # ------------------------------------------------------------------
    mlb_client = MLBIngestionClient(logger, SNAPSHOT_ID)
    sp_override_by_player: dict[int, dict] = {}
    try:
        sp_override_by_player = _build_live_sp_override(
            today_iso=GAME_DATE_ISO,
            latest_df=latest,
            client=mlb_client,
            logger=logger,
            session_id=SESSION_ID,
        )
        print(f"[SP OVERLAY] Live SP stats fetched for {len(sp_override_by_player)} players")
    except Exception as e:
        logger.warning(
            "PIPE-05", "live_sp_overlay_failed",
            payload={"error": str(e)}, session_id=SESSION_ID,
        )
        print(f"[SP OVERLAY] Failed — falling back to historical SP stats: {e}")

    # ------------------------------------------------------------------
    # 4. Initialize C4 Risk Engine
    # ------------------------------------------------------------------
    _state           = trader.get_state()
    bankroll         = _state["bankroll_usd"]
    _initial_bankroll = _state.get("initial_bankroll_usd", 1000.0)
    engine = RiskEngine(
        logger=logger,
        snapshot_id=SNAPSHOT_ID,
        bankroll=bankroll,
        kelly_fraction=T1_KELLY,
        initial_bankroll=_initial_bankroll,
        min_bet_usd=MIN_BET_PAPER,
    )
    daily_loss = _state.get("current_daily_loss", 0.0)
    if _state.get("daily_loss_date", "") != date.today().isoformat():
        daily_loss = 0.0
    _realized_loss = max(0.0, -_state.get("total_realized_pnl", 0.0))
    current_drawdown_pct = _realized_loss / _initial_bankroll if _initial_bankroll > 0 else 0.0

    print(f"[C4] Bankroll ${bankroll:.2f} | Daily loss ${daily_loss:.2f} | "
          f"Drawdown {current_drawdown_pct:.1%}")

    _pre_deployed_usd = max(0.0, _initial_bankroll - bankroll)
    _pre_deployed_pct = _pre_deployed_usd / _initial_bankroll if _initial_bankroll > 0 else 0.0
    _reserve_floor_usd = RESERVE_MANDATE_PCT * _initial_bankroll
    print(f"[C4] Reserve mandate: {RESERVE_MANDATE_PCT:.0%} floor (${_reserve_floor_usd:.2f}) | "
          f"Deployed: ${_pre_deployed_usd:.2f} ({_pre_deployed_pct:.1%}) | "
          f"Available: ${bankroll:.2f}")
    if _pre_deployed_pct > 0.80:
        print(
            f"  [WARN] RESERVE ALERT: {_pre_deployed_pct:.1%} of initial bankroll deployed.",
            file=sys.stderr,
        )
        logger.warning(
            "PIPE-05", "reserve_alert_high_deployment",
            payload={"deployed_pct": round(_pre_deployed_pct, 4), "bankroll": bankroll},
            session_id=SESSION_ID,
        )

    # ------------------------------------------------------------------
    # 5. Fetch live KXMLBHIT markets via VenueRouter
    # ------------------------------------------------------------------
    print("[DS-02] Fetching live KXMLBHIT markets via VenueRouter (sport=MLB)...")
    try:
        router = VenueRouter.from_env()
        connectivity = router.check_all_connectivity()
        kalshi_ok, kalshi_stat = connectivity.get("kalshi", (False, {}))
        if not kalshi_ok:
            logger.error(
                "PIPE-05", "ds02_failed",
                payload=kalshi_stat, session_id=SESSION_ID,
            )
            print(f"ERROR: DS-02 (Kalshi) unavailable: {kalshi_stat}", file=sys.stderr)
            sys.exit(1)

        ok2, snap = router.fetch_all_markets(sport="MLB")
        if not ok2 or not snap.markets:
            print("  No KXMLBHIT markets available. No games today or pre-market.")
            _write_report([], bankroll, trader)
            sys.exit(0)

        quoted = [m for m in snap.markets if m.has_live_quotes]
        if quoted:
            avg_vig = np.mean([m.vig for m in quoted])
            print(f"  {len(snap.markets)} markets | {len(quoted)} quoted | "
                  f"avg vig {avg_vig:.4f} | venues: {router.active_venues}")
        else:
            print(f"  {len(snap.markets)} markets — no live quotes yet. | "
                  f"venues: {router.active_venues}")

    except EnvironmentError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)

    # ------------------------------------------------------------------
    # 6. Abort if any MLB game is in progress
    # (mirrors NBA T-162/GG-024 guard but uses MLB Stats API)
    # ------------------------------------------------------------------
    if _is_mlb_game_in_progress(GAME_DATE_ISO):
        print(
            f"[PIPE-05] MLB game(s) in progress on {GAME_DATE_ISO} — "
            f"aborting bet placement (live market contamination guard)"
        )
        logger.info(
            "PIPE-05", "paper_run_skipped_game_in_progress",
            payload={"game_date": GAME_DATE_ISO, "session_id": SESSION_ID},
            session_id=SESSION_ID,
        )
        _write_report([], bankroll, trader)
        sys.exit(0)
    else:
        print(f"[PIPE-05] No MLB games in progress on {GAME_DATE_ISO} — proceeding")

    # ------------------------------------------------------------------
    # 7. Forecast + C4 evaluation + paper orders (market-first)
    # ------------------------------------------------------------------
    orders: list[dict] = []
    passes: list[dict] = []

    # Group active quoted markets by player name
    markets_by_player: dict[str, list] = defaultdict(list)
    for m in snap.markets:
        if m.status == "active" and m.has_live_quotes:
            # Only process markets whose ticker resolves to the target game date.
            # Prevents evaluating today's in-progress markets alongside tomorrow's.
            if _ticker_to_game_date(m.ticker) == GAME_DATE_ISO:
                markets_by_player[m.player_name].append(m)

    print(f"  {len(markets_by_player)} players in live MLB markets | "
          f"{sum(len(v) for v in markets_by_player.values())} market/threshold pairs")

    # Run-level game_date guard (mirrors NBA runner T-166 defense-in-depth)
    _game_date_deployed_count = sum(
        1 for p in trader.get_state().get("open_positions", [])
        if _ticker_to_game_date(p.get("kalshi_ticker", "")) == GAME_DATE_ISO
    )
    _game_date_guard_fired = _game_date_deployed_count > 0
    if _game_date_guard_fired:
        print(
            f"[GAME-DATE GUARD] {_game_date_deployed_count} open MLB position(s) already "
            f"deployed for {GAME_DATE_ISO}. C4 evaluation + placement blocked."
        )
        logger.info(
            "PIPE-05", "paper_run_game_date_guard_active",
            payload={"game_date": GAME_DATE_ISO,
                     "open_positions_for_date": _game_date_deployed_count},
            session_id=SESSION_ID,
        )

    _reserve_halted = False

    for kalshi_player_name, player_mkts in markets_by_player.items():
        if _reserve_halted:
            break

        norm = normalize_player_name(kalshi_player_name)
        row = cohort_lookup.get(norm)

        if row is None:
            logger.info(
                "PIPE-05", "player_not_in_feature_csv",
                payload={"player": kalshi_player_name, "norm": norm},
                session_id=SESSION_ID,
            )
            print(f"  [SKIP] {kalshi_player_name} — not in feature CSV (no MLB fallback lookup)")
            continue

        player_id = int(row.get("player_id", 0))

        for mkt in player_mkts:
            if _reserve_halted:
                break

            # Only evaluate thresholds the model was trained on
            if int(mkt.threshold) not in _MODEL_THRESHOLDS:
                logger.info(
                    "PIPE-05", "threshold_out_of_model_range",
                    payload={"ticker": mkt.ticker, "threshold": mkt.threshold,
                             "model_thresholds": list(_MODEL_THRESHOLDS)},
                    session_id=SESSION_ID,
                )
                print(f"  [SKIP] {kalshi_player_name} threshold={mkt.threshold} "
                      f"not in model thresholds {sorted(_MODEL_THRESHOLDS)}")
                continue

            # Idempotency guard
            _open_tickers = {
                p["kalshi_ticker"]
                for p in trader.get_state().get("open_positions", [])
            }
            if mkt.ticker in _open_tickers:
                print(f"  [IDEMPOTENCY] SKIP {kalshi_player_name} — {mkt.ticker} already open")
                continue

            # Build feature vector and dispatch to per-threshold pipeline
            sp_override = sp_override_by_player.get(player_id)
            X = _build_mlb_feature_vector(
                row=row,
                feature_names=feature_names,
                col_medians=col_medians,
                sp_override=sp_override,
            )

            p_raw = float(pipelines[int(mkt.threshold)].predict_proba(X)[0, 1])
            p_calibrated = calibrate_probability(p_raw, sport="mlb")

            mid   = mkt.mid_price
            half  = mkt.half_spread
            gross_edge = p_calibrated - mid - half
            kalshi_fee = 0.07 * mid * (1.0 - mid)
            edge       = gross_edge - kalshi_fee

            direction = ("YES" if edge > EDGE_YES else "NO" if edge < EDGE_NO else "PASS")

            # YES-only diagnostic gate
            if PAPER_YES_ONLY and direction == "NO":
                logger.info(
                    "PIPE-05", "yes_only_gate_filtered",
                    payload={
                        "ticker": mkt.ticker,
                        "player": kalshi_player_name,
                        "direction": "NO",
                        "edge": round(edge, 6),
                        "gross_edge": round(gross_edge, 6),
                        "p_calibrated": round(p_calibrated, 6),
                        "p_raw": round(p_raw, 6),
                        "market_implied_prob": mid,
                        "threshold": int(mkt.threshold),
                    },
                    session_id=SESSION_ID,
                )
                print(f"  [YES-ONLY] FILTER {kalshi_player_name:<22} NO    "
                      f"edge={edge:+.3f}  p={p_calibrated:.3f}  "
                      f"mkt=H≥{mkt.threshold}")
                continue

            # Run-level game_date guard
            if _game_date_guard_fired:
                logger.info(
                    "PIPE-05", "paper_run_skipped_already_deployed",
                    payload={"ticker": mkt.ticker, "player": kalshi_player_name,
                             "game_date": GAME_DATE_ISO},
                    session_id=SESSION_ID,
                )
                continue

            forecast_rec = {
                "forecast_id": f"FCST-MLB-{uuid.uuid4().hex[:8].upper()}",
                "p_estimate": p_calibrated,
                "p_estimate_raw": round(p_raw, 6),
                "market_implied_prob": mid,
                "gross_edge": round(gross_edge, 6),
                "kalshi_fee": round(kalshi_fee, 6),
                "edge": round(edge, 6),
                "recommended_direction": direction,
                "threshold": int(mkt.threshold),
                "sport": "mlb",
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

            status = approval.get("approval_status", "UNKNOWN")

            if status == "KILL_SWITCH":
                logger.critical(
                    "PIPE-05", "kill_switch_from_c4",
                    payload=approval, session_id=SESSION_ID,
                )
                print("  KILL SWITCH triggered by C4 — halting PIPE-05.", file=sys.stderr)
                sys.exit(1)

            if status == "APPROVED":
                approved_size = approval.get("approved_size", 0)

                # Batch reserve gate
                if bankroll - approved_size < RESERVE_MANDATE_PCT * _initial_bankroll:
                    reserve_floor = RESERVE_MANDATE_PCT * _initial_bankroll
                    print(
                        f"  [RESERVE GATE] BATCH HALT — "
                        f"${bankroll:.2f} - ${approved_size:.2f} = "
                        f"${bankroll - approved_size:.2f} < ${reserve_floor:.2f} floor. "
                        f"No further MLB bets."
                    )
                    logger.warning(
                        "PIPE-05", "reserve_mandate_batch_halt",
                        payload={
                            "bankroll": bankroll,
                            "proposed_size": approved_size,
                            "reserve_floor": reserve_floor,
                            "player": kalshi_player_name,
                            "ticker": mkt.ticker,
                        },
                        session_id=SESSION_ID,
                    )
                    _reserve_halted = True
                    break

                approval = {
                    **approval,
                    "model_p": float(forecast_rec["p_estimate"]),
                    "edge": float(forecast_rec["edge"]),
                    "gross_edge": float(forecast_rec["gross_edge"]),
                }
                ok_pos, pos = trader.open_position(
                    approval=approval,
                    player_name=kalshi_player_name,
                    player_id=player_id,
                    kalshi_ticker=mkt.ticker,
                    kalshi_threshold=int(mkt.threshold),
                    mid_price=mid,
                    vig=mkt.vig,
                    game_date=_ticker_to_game_date(mkt.ticker),
                    session_id=SESSION_ID,
                )
                print(
                    f"  BET  {kalshi_player_name:<22} {direction:<4}  ${approved_size:.2f}  "
                    f"edge={edge:+.3f}  p={p_calibrated:.3f}  H≥{mkt.threshold}"
                )
                if pos:
                    orders.append(pos)
                    _state = trader.get_state()
                    bankroll         = _state["bankroll_usd"]
                    _initial_bankroll = _state.get("initial_bankroll_usd", 1000.0)
                    _realized_loss   = max(0.0, -_state.get("total_realized_pnl", 0.0))
                    current_drawdown_pct = (
                        _realized_loss / _initial_bankroll if _initial_bankroll > 0 else 0.0
                    )
                    engine = RiskEngine(
                        logger=logger,
                        snapshot_id=SNAPSHOT_ID,
                        bankroll=bankroll,
                        kelly_fraction=T1_KELLY,
                        initial_bankroll=_initial_bankroll,
                        min_bet_usd=MIN_BET_PAPER,
                    )
            else:
                reason = approval.get("rejection_reason", "unknown")
                if direction != "PASS":
                    passes.append({
                        "player": kalshi_player_name,
                        "direction": direction,
                        "edge": round(edge, 3),
                        "reason": reason,
                    })

    # ------------------------------------------------------------------
    # 8. Summary
    # ------------------------------------------------------------------
    summary = trader.summary()
    print(f"\n[SUMMARY] — MLB PIPE-05")
    print(f"  Bets placed today:  {len(orders)}")
    print(f"  Rejected by C4:     {len(passes)}")
    print(f"  Bankroll:           ${summary['bankroll_usd']:.2f}")
    print(f"  Total realized P&L: ${summary['total_realized_pnl']:+.2f}")
    print(f"  Open positions:     {summary['open_positions']}")
    print(f"  Closed positions:   {summary['closed_positions']}")
    if summary["win_rate"] is not None:
        print(f"  Win rate:           {summary['win_rate']:.1%}")
    print(f"  Realized drawdown:  {summary['realized_drawdown_pct']:.1f}%")
    print(f"  Deployed (stakes):  {summary['deployed_pct']:.1f}%")

    _write_report(orders, summary["bankroll_usd"], trader)

    SystemMonitor(
        logger=logger, snapshot_id=SNAPSHOT_ID, session_id=SESSION_ID
    ).check_portfolio_pnl(
        total_realized_pnl=summary["total_realized_pnl"],
        initial_bankroll=summary["initial_bankroll_usd"],
        session_id=SESSION_ID,
    )

    logger.info(
        "PIPE-05", "paper_run_complete",
        payload={
            "bets_placed": len(orders),
            "rejected": len(passes),
            "bankroll": summary["bankroll_usd"],
            "total_pnl": summary["total_realized_pnl"],
            "sport": "mlb",
        },
        session_id=SESSION_ID, snapshot_id=SNAPSHOT_ID,
    )


if __name__ == "__main__":
    main()
