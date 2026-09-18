"""T1 MLB game-market run script (GG-255/T-538). PAPER ONLY.

Exercises the MLB half of the nine ADR-0058 T1 game-market cells
(`measurement_stake.py`) — the NFL half was built first (GG-255/T-530,
`run_t1_nfl_game_market.py`); this script is its direct MLB counterpart,
ported deliberately rather than invented from scratch so the two scripts'
pipeline shape, refusal semantics, and safety guarantees match exactly.
Before this script, all five MLB game-market cells existed unimported by
any run path except an audit tool, with no cron entry. This script does not
change that dark status; it is a manually-invoked, paper-only pipeline for
verifying the wiring shape end to end. MLB is notable here as the ONLY band
currently trading live (KXMLBHIT, T4M-PROJ) — this script is fully isolated
from that live pipeline (see PORTFOLIO_PATH below).

Pipeline: kalshi_client.fetch_game_markets() [C1/C5 fetch] -> INJECTABLE
model interface (see MLBGameMarketForecastModel/StubMLBGameMarketForecastModel
below; no C2/C3 layer exists for these five cells yet) -> C4 risk
(RiskEngine.evaluate_forecast, fixed_stake_usd bypass per ADR-0050) -> T1
measurement stake (measurement_stake.py, ADR-0059) -> paper trade only
(PaperTrader constructed with kalshi_client=None, unconditionally — no live
order path is reachable from this script under any config).

Model status: NO trained model exists yet for these five MLB game-market
cells (they are distinct from the live KXMLBHIT player-prop model). The
default model wired into main() is StubMLBGameMarketForecastModel, an
explicitly labeled placeholder returning a fixed probability — NOT a
calibrated forecast. Any run of this script's main() is exercising pipeline
shape against a stub, not against a real model, until a real model is
injected.

Cell-tier kill switch: `market_type_registry.resolve_kill_switch_state()` is
consulted (read-only) before evaluating each market. This script never calls
`halt_cell()` — that write path remains unwired to any live caller, as
before this session. No halt threshold, cron entry, or live-order path is
added or modified by this script.

Ledger isolation (GG-255 DO NOT constraint, non-negotiable): this script
writes ONLY to paper_portfolio_t1_mlb_game_market.json and
audit_t1_mlb_game_market.jsonl. It MUST NEVER open, write, or lock
paper_portfolio_mlb.json or paper_portfolio_mlb_t4.json — those are the two
live MLB paper-trading ledgers (T1 sameday and T4M-PROJ respectively) and
are in active use. See tests/test_run_t1_mlb_game_market.py for a test that
asserts this by construction, not just by inspection.

Security: BOT_C4_ACTIVE is set in-process only after BOT_ENV=paper is
verified below, mirroring run_mlb_paper_trade.py's and
run_t1_nfl_game_market.py's pattern exactly.
BOT_C4_ACTIVE must NOT be set externally in ENV-02's .env.

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
# run_mlb_paper_trade.py lines 76-85 / run_t1_nfl_game_market.py).
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

# Pool-isolated (ADR-0023 precedent, applied here for the same reason as
# run_t1_nfl_game_market.py: these five cells are unproven/NOT_IMPLEMENTED —
# they must not compete for or distort the live MLB bankroll pools
# (paper_portfolio_mlb.json / paper_portfolio_mlb_t4.json). Separate
# portfolio file, separate bankroll — GG-255 DO NOT constraint.
PORTFOLIO_PATH = LOG_DIR / "paper_portfolio_t1_mlb_game_market.json"
INITIAL_BANKROLL_USD = float(
    os.environ.get("T1_MLB_GAME_MARKET_INITIAL_BANKROLL_USD", "1000.0")
)

EDGE_THRESHOLD = float(os.environ.get("T1_MLB_GAME_MARKET_EDGE_THRESHOLD", "0.02"))

BAND = ExecutionBand.T1_MULTI_DAY

# GameMarket.market_type (bare string) -> MarketType enum. Conveniently,
# MarketType.MLB_*.value already matches measurement_stake.py's
# T1_GAME_MARKET_TYPES strings exactly, so no second mapping is needed for
# is_t1_game_market(). "run_line" and "partial_game" have no NFL analogue —
# see kalshi_client.py's _MLB_GAME_SERIES comment for why.
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
# Injectable model interface (GG-255 Deliverable 1, mirrors NFL exactly)
# ---------------------------------------------------------------------------


class MLBGameMarketForecastModel(Protocol):
    """Swappable forecasting interface. No C2/C3 layer exists yet for these
    five cells — this Protocol is the seam a future trained model slots into
    without changing this script's pipeline code."""

    def predict_proba(
        self, market: GameMarket, features: dict[str, Any]
    ) -> float | None:
        """Return calibrated P(YES) in [0, 1], or None if no prediction is
        available for this market (e.g. missing upstream data) — None is a
        refusal signal, not an error, and callers must treat it as such.
        Never substitute a default probability for a missing one."""
        ...


class StubMLBGameMarketForecastModel:
    """EXPLICIT STUB — NOT a trained model (GG-255). No C2 feature store or
    C3 model artifact exists for these five cells (they are distinct from
    the live KXMLBHIT player-prop model). Returns a fixed placeholder
    probability (or None, to exercise the no-model refusal path) for
    pipeline-shape testing only. Any report of this script's output MUST
    state it ran against this stub, not a real model, whenever this class
    is in use."""

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
    model: MLBGameMarketForecastModel,
    engine: RiskEngine,
    trader: PaperTrader,
    audit: AuditLogger,
    session_id: str = SESSION_ID,
) -> str:
    """Evaluate one GameMarket and, if approved, open a paper position.

    Returns a short outcome tag for testing/logging:
      REFUSED_UNPARSED | REFUSED_NO_THRESHOLD | REFUSED_NO_SETTLEMENT_PATH |
      REFUSED_KILL_SWITCH | REFUSED_NO_MODEL | REFUSED_NO_EDGE |
      REFUSED_STAKE | REJECTED | KILL_SWITCH_HALT | C6_WRITE_FAILURE | OPENED
    """
    # GG-252: refuse to trade out of a batch known to have dropped markets —
    # a snapshot with unparsed_count > 0 signals parser/data-quality
    # uncertainty for the whole fetch, not just the dropped tickers.
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

    # GG-291/T-562: MLB_PARTIAL_GAME (KXMLBF3/F5/F7) has no numeric
    # threshold at all -- it's a three-way win/loss/tie market, structurally
    # unlike the other five MLB game-market types -- and no settlement
    # module supports it yet (game_market_settlement.py is NFL-only; GG-294,
    # OPEN, registered and explicitly deferred this session). Refuse to open
    # rather than write a position this codebase cannot yet settle.
    if market_type is MarketType.MLB_PARTIAL_GAME:
        audit.warning(
            COMPONENT, "gg294_no_settlement_path",
            payload={"ticker": mkt.ticker, "market_type": market_type.value},
            session_id=session_id,
        )
        return "REFUSED_NO_SETTLEMENT_PATH"

    # GG-291/T-562: derive the settlement threshold once, up front, and
    # refuse before doing any further evaluation work if it can't be
    # determined. A moneyline is a spread at zero (game_market_settlement.py
    # module docstring) — 0.0, not None. run_line/total/team_total carry the
    # real line on GameMarket.threshold; refuse rather than open a position
    # paper_trader.py's UndeterminedThresholdError guard would reject anyway,
    # since that guard fires mid-open_position() after model/risk work has
    # already run.
    if market_type is MarketType.MLB_MONEYLINE:
        kalshi_threshold = 0.0
    else:
        kalshi_threshold = mkt.threshold
        if kalshi_threshold is None:
            audit.warning(
                COMPONENT, "gg291_no_threshold",
                payload={"ticker": mkt.ticker, "market_type": market_type.value},
                session_id=session_id,
            )
            return "REFUSED_NO_THRESHOLD"

    # Cell-tier kill switch (Deliverable 1) — READ-side only. This script
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

    # GG-255 Deliverable 1 fix (ported verbatim from run_t1_nfl_game_market.py):
    # run_t4_mlb_live.py:1364 treats KILL_SWITCH identically to REJECTED
    # (`if approval.get("approval_status") != "APPROVED": continue`) — it
    # never distinguishes a bankroll kill-switch trip from an ordinary
    # per-bet rejection, and keeps evaluating subsequent markets after a
    # kill switch has fired. This script branches on KILL_SWITCH distinctly
    # and self-halts (mirrors run_mlb_paper_trade.py's existing three-way
    # branch, not run_t4_mlb_live.py's two-way collapse).
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
        kalshi_threshold=kalshi_threshold,  # GG-291/T-562
        session_id=session_id,
        pool_isolated=True,
    )
    return "OPENED"


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------


def main(model: MLBGameMarketForecastModel | None = None) -> dict[str, int]:
    if model is None:
        model = StubMLBGameMarketForecastModel()
        print(
            "WARNING: running against StubMLBGameMarketForecastModel — NOT a "
            "trained model. No C2/C3 layer exists yet for these five MLB "
            "game-market cells (GG-255).",
            file=sys.stderr,
        )

    audit = AuditLogger(AUDIT_LOG_PATH)
    kalshi = KalshiMarketClient.from_env()
    engine = RiskEngine(
        logger=audit, snapshot_id="SNAP-T1-MLBGM-001", bankroll=INITIAL_BANKROLL_USD,
        # min_bet_usd=1.0: aligns to existing precedent (run_mlb_paper_trade.py's
        # MIN_BET_PAPER, run_t2_mlb_sameday.py's MIN_BET_PAPER, run_t4_mlb_live.py's
        # 0.01), not a new value. Without this override, RiskEngine defaults to the
        # live MIN_BET_USD=10.0 floor (risk.py) against this script's $1.00 ADR-0050
        # measurement stake (T1_MEASUREMENT_STAKE_USD) — an unintended mismatch
        # (GG-282/T-551): ADR-0059 explicitly cites the sibling paper-mode override
        # as the precedent that makes the flat-stake bypass "already work for T1
        # with zero code change," but that override was never actually applied when
        # this script was written (T-538/DECISION_LOG does not mention min_bet_usd).
        min_bet_usd=1.0,
    )
    # kalshi_client=None, unconditionally — this is the sole mechanical
    # guard against a live order path (GG-255 DO NOT constraint). Quote
    # your line: this is the structural guarantee no live order is
    # possible, not an assumption.
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
