"""T1 MLB game-market run script (GG-255/T-536, MLB half — mirrors T-530's
NFL precedent, run_t1_nfl_game_market.py, exactly). PAPER ONLY.

Exercises the five MLB cells of ADR-0058's nine T1 game-market cells
(`measurement_stake.py`) for the first time — before this script, those
cells existed unimported by any run path except an audit tool, with no cron
entry. This script does not change that dark status; it is a
manually-invoked, paper-only pipeline for verifying the wiring shape end to
end. MLB is the only band currently trading live (T1 player-prop hits,
`run_mlb_paper_trade.py`) — this script is a separate, pool-isolated cell
family, not an extension of that live pipeline.

Pipeline: kalshi_client.fetch_game_markets() [C1/C5 fetch] -> INJECTABLE
model interface (see MLBForecastModel/StubMLBForecastModel below) -> C4 risk
(RiskEngine.evaluate_forecast, fixed_stake_usd bypass per ADR-0050) -> T1
measurement stake (measurement_stake.py, ADR-0059) -> paper trade only
(PaperTrader constructed with kalshi_client=None, unconditionally — no live
order path is reachable from this script under any config).

Model status: MLB already has a live C1/C2/C3 layer (`mlb_ingestion.py`,
`mlb_features.py`), but it is built for player-prop hits forecasting
(ba_l10, rest, home/away) — not for team-level game-outcome probabilities
(moneyline win prob, run-line cover prob, totals over/under). No calibrated
model exists for the five ADR-0058 MLB game-market cells this script
targets; they are NOT_IMPLEMENTED. The default model wired into main() is
StubMLBForecastModel, an explicitly labeled placeholder returning a fixed
probability — NOT a calibrated forecast. Any run of this script's main() is
exercising pipeline shape against a stub, not against a real model, until a
real game-outcome model is injected.

Cell-tier kill switch: `market_type_registry.resolve_kill_switch_state()` is
consulted (read-only) before evaluating each market. This script never calls
`halt_cell()` — that write path remains unwired to any live caller, as
before this session. No halt threshold, cron entry, or live-order path is
added or modified by this script.

Security: BOT_C4_ACTIVE is set in-process only after BOT_ENV=paper is
verified below, mirroring run_mlb_paper_trade.py's pattern exactly.
BOT_C4_ACTIVE must NOT be set externally in ENV-02's .env.

Ledger isolation (GG-255 Deliverable 1 constraint): this script writes only
to logs/paper_portfolio_t1_mlb_game_market.json and
logs/audit_t1_mlb_game_market.jsonl — it never opens, writes, or locks
paper_portfolio_mlb.json or paper_portfolio_mlb_t4.json (the live T1
player-prop and T4 ledgers). See test_run_t1_mlb_game_market.py's
no-shared-ledger test.

How to run:
  source /opt/prediction-market-bot/.env
  BOT_ENV=paper PYTHONPATH=src python \\
      src/prediction_market_bot/run_t1_mlb_game_market.py
"""

from __future__ import annotations

import os
import sys
import uuid
from pathlib import Path
from typing import Any, Protocol

_SRC_ROOT = Path(__file__).parent.parent.parent
if str(_SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(_SRC_ROOT))

# Verify ENV-02 before importing anything else (same pattern as
# run_mlb_paper_trade.py lines 76-85).
if os.environ.get("BOT_ENV", "").lower() != "paper":
    print(
        "FATAL: run_t1_mlb_game_market.py requires BOT_ENV=paper. "
        "Set BOT_ENV=paper in your .env.",
        file=sys.stderr,
    )
    sys.exit(1)

# Activate C4 in-process (paper trading; verified ENV-02 above).
os.environ["BOT_C4_ACTIVE"] = "true"

from prediction_market_bot.c4_risk_engine.risk import RiskEngine  # noqa: E402
from prediction_market_bot.c5_execution.kalshi_client import (  # noqa: E402
    GameMarket,
    GameMarketSnapshot,
    KalshiMarketClient,
)
from prediction_market_bot.c5_execution.market_type_registry import (  # noqa: E402
    CellKillSwitchStatus,
    MarketType,
    resolve_kill_switch_state,
)
from prediction_market_bot.c5_execution.measurement_stake import (  # noqa: E402
    MeasurementStakeRefused,
    is_t1_game_market,
    t1_measurement_stake_and_stratum,
)
from prediction_market_bot.c5_execution.paper_trader import PaperTrader  # noqa: E402
from prediction_market_bot.c6_audit_logger.audit_logger import AuditLogger  # noqa: E402
from prediction_market_bot.execution_bands import ExecutionBand  # noqa: E402

COMPONENT = "run_t1_mlb_game_market"

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

SESSION_ID = f"PT-T1-MLBGM-{uuid.uuid4().hex[:8].upper()}"
LOG_DIR = Path(os.environ.get("LOG_DIR", str(_SRC_ROOT / "logs")))
AUDIT_LOG_PATH = LOG_DIR / "audit_t1_mlb_game_market.jsonl"

# Pool-isolated (ADR-0023 precedent, applied here for the same reason: these
# five cells are unproven/NOT_IMPLEMENTED — they must not compete for or
# distort the live MLB T1-prop / T4 bankroll pools). Separate portfolio
# file, separate bankroll, exactly mirroring T4M-PROJ's isolation rationale
# and run_t1_nfl_game_market.py's identical isolation for its four cells.
# GG-255 Deliverable 1 constraint: never paper_portfolio_mlb.json or
# paper_portfolio_mlb_t4.json.
PORTFOLIO_PATH = LOG_DIR / "paper_portfolio_t1_mlb_game_market.json"
INITIAL_BANKROLL_USD = float(
    os.environ.get("T1_MLB_GAME_MARKET_INITIAL_BANKROLL_USD", "1000.0")
)

EDGE_THRESHOLD = float(os.environ.get("T1_MLB_GAME_MARKET_EDGE_THRESHOLD", "0.02"))

BAND = ExecutionBand.T1_MULTI_DAY

# GameMarket.market_type (bare string, as emitted by
# kalshi_client._parse_mlb_game_market — GG-255 Deliverable 2) -> MarketType
# enum. Conveniently, MarketType.MLB_*.value already matches
# measurement_stake.py's T1_GAME_MARKET_TYPES strings exactly, so no second
# mapping is needed for is_t1_game_market(). KXMLBF3/F5/F7 all collapse into
# the single "partial_game" market_type string at parse time (see
# kalshi_client.py's _parse_mlb_game_market docstring) — no ticker-level
# special-casing is needed here.
_GAME_MARKET_TYPE_MAP: dict[str, MarketType] = {
    "moneyline": MarketType.MLB_MONEYLINE,
    "run_line": MarketType.MLB_RUN_LINE,
    "total": MarketType.MLB_GAME_TOTAL,
    "team_total": MarketType.MLB_TEAM_TOTAL,
    "partial_game": MarketType.MLB_PARTIAL_GAME,
}

_MLB_GAME_SERIES = (
    "KXMLBGAME", "KXMLBSPREAD", "KXMLBTOTAL", "KXMLBTEAMTOTAL",
    "KXMLBF3", "KXMLBF5", "KXMLBF7",
)


# ---------------------------------------------------------------------------
# Injectable model interface (GG-255 Deliverable 2)
# ---------------------------------------------------------------------------


class MLBForecastModel(Protocol):
    """Swappable forecasting interface. No MLB game-outcome C3 model exists
    yet (MLB's existing C3 model forecasts player-prop hits, not team
    moneyline/run-line/totals win probability) — this Protocol is the seam a
    future trained model slots into without changing this script's pipeline
    code."""

    def predict_proba(
        self, market: GameMarket, features: dict[str, Any]
    ) -> float | None:
        """Return calibrated P(YES) in [0, 1], or None if no prediction is
        available for this market (e.g. missing upstream data) — None is a
        refusal signal, not an error, and callers must treat it as such."""
        ...


class StubMLBForecastModel:
    """EXPLICIT STUB — NOT a trained model (GG-255). No MLB game-outcome C3
    model artifact exists (see module docstring). Returns a fixed
    placeholder probability (or None, to exercise the no-model refusal
    path) for pipeline-shape testing only. Any report of this script's
    output MUST state it ran against this stub, not a real model, whenever
    this class is in use."""

    def __init__(self, fixed_p: float | None = 0.55) -> None:
        self._fixed_p = fixed_p

    def predict_proba(
        self, market: GameMarket, features: dict[str, Any]
    ) -> float | None:
        return self._fixed_p


# ---------------------------------------------------------------------------
# Core per-market decision logic (isolated for direct testing — GG-255
# Deliverable 3)
# ---------------------------------------------------------------------------


def evaluate_and_maybe_trade(
    mkt: GameMarket,
    *,
    snapshot_unparsed_count: int,
    model: MLBForecastModel,
    engine: RiskEngine,
    trader: PaperTrader,
    audit: AuditLogger,
    session_id: str = SESSION_ID,
) -> str:
    """Evaluate one GameMarket and, if approved, open a paper position.

    Returns a short outcome tag for testing/logging:
      REFUSED_UNPARSED | REFUSED_KILL_SWITCH | REFUSED_NO_MODEL |
      REFUSED_NO_EDGE | REFUSED_STAKE | REJECTED | KILL_SWITCH_HALT |
      C6_WRITE_FAILURE | OPENED
    """
    # GG-252 precedent (NFL): refuse to trade out of a batch known to have
    # dropped markets — a snapshot with unparsed_count > 0 signals
    # parser/data-quality uncertainty for the whole fetch, not just the
    # dropped tickers. Applies identically to the MLB game-market fetch.
    if snapshot_unparsed_count > 0:
        audit.warning(
            COMPONENT, "gg252_unparsed_markets_present",
            payload={"ticker": mkt.ticker, "unparsed_count": snapshot_unparsed_count},
            session_id=session_id,
        )
        return "REFUSED_UNPARSED"

    market_type = _GAME_MARKET_TYPE_MAP.get(mkt.market_type)
    if market_type is None or not is_t1_game_market(market_type.value):
        audit.warning(
            COMPONENT, "unmapped_market_type",
            payload={"ticker": mkt.ticker, "market_type": mkt.market_type},
            session_id=session_id,
        )
        return "REFUSED_UNPARSED"

    # Cell-tier kill switch (Deliverable 3) — READ-side only. This script
    # never calls halt_cell(); the write path stays unwired, as before.
    kss = resolve_kill_switch_state(market_type, BAND)
    if kss.status is CellKillSwitchStatus.HALTED:
        audit.warning(
            COMPONENT, "cell_kill_switch_halted",
            payload={
                "ticker": mkt.ticker,
                "market_type": market_type.value,
                "band": BAND.value,
                "reason": kss.reason,
            },
            session_id=session_id,
        )
        return "REFUSED_KILL_SWITCH"

    if not mkt.has_live_quotes:
        audit.warning(
            COMPONENT, "no_live_quotes",
            payload={"ticker": mkt.ticker}, session_id=session_id,
        )
        return "REFUSED_NO_MODEL"  # no tradable price -> cannot evaluate

    features: dict[str, Any] = {
        "mid_price": mkt.mid_price, "vig": mkt.vig, "volume": mkt.volume,
    }
    p_estimate = model.predict_proba(mkt, features)
    if p_estimate is None:
        audit.warning(
            COMPONENT, "no_model_prediction",
            payload={"ticker": mkt.ticker}, session_id=session_id,
        )
        return "REFUSED_NO_MODEL"

    market_implied_prob = mkt.mid_price
    edge_yes = p_estimate - market_implied_prob
    edge_no = (1.0 - p_estimate) - (1.0 - market_implied_prob)
    if edge_yes >= EDGE_THRESHOLD:
        direction = "YES"
        edge = edge_yes
    elif edge_no >= EDGE_THRESHOLD:
        direction = "NO"
        edge = edge_no
    else:
        audit.info(
            COMPONENT, "no_edge",
            payload={
                "ticker": mkt.ticker, "p_estimate": p_estimate,
                "market_implied_prob": market_implied_prob,
            },
            session_id=session_id,
        )
        return "REFUSED_NO_EDGE"

    entry_price = market_implied_prob if direction == "YES" else (1.0 - market_implied_prob)

    try:
        stake, contracts, price_stratum = t1_measurement_stake_and_stratum(
            entry_price, mkt.half_spread,
        )
    except MeasurementStakeRefused as exc:
        audit.warning(
            COMPONENT, "measurement_stake_refused",
            payload={"ticker": mkt.ticker, "reason": str(exc)},
            session_id=session_id,
        )
        return "REFUSED_STAKE"

    forecast_record = {
        "forecast_id": f"T1-MLBGM-{session_id}-{mkt.ticker[-12:]}",
        "p_estimate": p_estimate,
        "market_implied_prob": market_implied_prob,
        "edge": edge,
        "recommended_direction": direction,
        "entry_price_paid": round(entry_price, 4),  # ADR-0050 addendum §C
        "price_stratum": price_stratum,              # ADR-0050 addendum §C
        "contracts": contracts,                       # ADR-0050 addendum §B
    }

    ok, approval = engine.evaluate_forecast(
        forecast_record=forecast_record,
        session_id=session_id,
        pool_isolated=True,
        fixed_stake_usd=stake,  # ADR-0050 bypass — kelly_fraction untouched
    )
    if not ok:
        audit.error(
            COMPONENT, "c6_write_failure",
            payload={"ticker": mkt.ticker}, session_id=session_id,
        )
        return "C6_WRITE_FAILURE"

    approval_status = approval.get("approval_status")

    # GG-255 Deliverable 1 fix: run_t4_mlb_live.py:1364 treats KILL_SWITCH
    # identically to REJECTED (`if approval.get("approval_status") !=
    # "APPROVED": continue`) — it never distinguishes a bankroll kill-switch
    # trip from an ordinary per-bet rejection, and keeps evaluating
    # subsequent markets after a kill switch has fired. This script branches
    # on KILL_SWITCH distinctly and self-halts (mirrors run_mlb_paper_trade.py's
    # existing three-way branch, not run_t4_mlb_live.py's two-way collapse).
    if approval_status == "KILL_SWITCH":
        audit.error(
            COMPONENT, "kill_switch_halt",
            payload={"ticker": mkt.ticker, "approval": approval},
            session_id=session_id,
        )
        return "KILL_SWITCH_HALT"

    if approval_status != "APPROVED":
        audit.info(
            COMPONENT, "rejected",
            payload={
                "ticker": mkt.ticker,
                "approval_status": approval_status,
                "rejection_reason": approval.get("rejection_reason"),
            },
            session_id=session_id,
        )
        return "REJECTED"

    approval = {
        **approval,
        "entry_price_paid": round(entry_price, 4),  # ADR-0050 addendum §C
        "price_stratum": price_stratum,              # ADR-0050 addendum §C
        "contracts": contracts,                       # ADR-0050 addendum §B
    }

    trader.open_position(
        approval=approval,
        kalshi_ticker=mkt.ticker,
        mid_price=mkt.mid_price,
        vig=mkt.vig,
        game_date=mkt.game_date,
        market_type=market_type,
        session_id=session_id,
        pool_isolated=True,
    )
    return "OPENED"


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------


def main(model: MLBForecastModel | None = None) -> dict[str, int]:
    if model is None:
        model = StubMLBForecastModel()
        print(
            "WARNING: running against StubMLBForecastModel — NOT a trained "
            "model. No MLB game-outcome C3 model exists yet (GG-255).",
            file=sys.stderr,
        )

    audit = AuditLogger(AUDIT_LOG_PATH)
    kalshi = KalshiMarketClient.from_env()
    engine = RiskEngine(
        logger=audit, snapshot_id="SNAP-T1-MLBGM-001", bankroll=INITIAL_BANKROLL_USD,
    )
    # kalshi_client=None, unconditionally — this is the sole mechanical
    # guard against a live order path (GG-255 DO NOT constraint).
    trader = PaperTrader(portfolio_path=PORTFOLIO_PATH, logger=audit, kalshi_client=None)

    outcome_counts: dict[str, int] = {}
    for series in _MLB_GAME_SERIES:
        ok, snapshot = kalshi.fetch_game_markets(series)
        if not ok:
            audit.error(
                COMPONENT, "fetch_game_markets_failed",
                payload={"series": series}, session_id=SESSION_ID,
            )
            outcome_counts["FETCH_FAILED"] = outcome_counts.get("FETCH_FAILED", 0) + 1
            continue

        halted = False
        for mkt in snapshot.markets:
            if halted:
                break
            outcome = evaluate_and_maybe_trade(
                mkt,
                snapshot_unparsed_count=snapshot.unparsed_count,
                model=model, engine=engine, trader=trader, audit=audit,
            )
            outcome_counts[outcome] = outcome_counts.get(outcome, 0) + 1
            if outcome == "KILL_SWITCH_HALT":
                halted = True

    print(f"T1 MLB game-market run complete: {outcome_counts}")
    return outcome_counts


if __name__ == "__main__":
    main()
