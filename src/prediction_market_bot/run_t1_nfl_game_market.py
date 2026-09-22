"""T1 NFL game-market run script (GG-255/T-530). PAPER ONLY.

Exercises the nine ADR-0058 T1 game-market cells (`measurement_stake.py`)
for the first time — before this script, those cells existed unimported by
any run path except an audit tool, with no cron entry. This script does not
change that dark status; it is a manually-invoked, paper-only pipeline for
verifying the wiring shape end to end.

Pipeline: kalshi_client.fetch_game_markets() [C1/C5 fetch] -> NFL C1 features
(module import only — nfl_ingestion.py currently stops at data-fetch; no C2
feature-transform or C3 model layer exists for NFL yet) -> INJECTABLE model
interface (see NFLForecastModel/StubNFLForecastModel below) -> C4 risk
(RiskEngine.evaluate_forecast, fixed_stake_usd bypass per ADR-0050) -> T1
measurement stake (measurement_stake.py, ADR-0059) -> paper trade only
(PaperTrader constructed with kalshi_client=None, unconditionally — no live
order path is reachable from this script under any config).

Model status: NO trained NFL forecasting model exists yet (no C2/C3 layer).
The default model wired into main() is StubNFLForecastModel, an explicitly
labeled placeholder returning a fixed probability — NOT a calibrated
forecast. Any run of this script's main() is exercising pipeline shape
against a stub, not against a real model, until a real model is injected.

Cell-tier kill switch: `market_type_registry.resolve_kill_switch_state()` is
consulted (read-only) before evaluating each market. This script never calls
`halt_cell()` — that write path remains unwired to any live caller, as
before this session. No halt threshold, cron entry, or live-order path is
added or modified by this script.

Security: BOT_C4_ACTIVE is set in-process only after BOT_ENV=paper is
verified below, mirroring run_mlb_paper_trade.py's pattern exactly.
BOT_C4_ACTIVE must NOT be set externally in ENV-02's .env.

How to run:
  source /opt/prediction-market-bot/.env
  BOT_ENV=paper PYTHONPATH=src python \\
      src/prediction_market_bot/run_t1_nfl_game_market.py
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
        "FATAL: run_t1_nfl_game_market.py requires BOT_ENV=paper. "
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

COMPONENT = "run_t1_nfl_game_market"

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

SESSION_ID = f"PT-T1-NFLGM-{uuid.uuid4().hex[:8].upper()}"
LOG_DIR = Path(os.environ.get("LOG_DIR", str(_SRC_ROOT / "logs")))
AUDIT_LOG_PATH = LOG_DIR / "audit_t1_nfl_game_market.jsonl"

# Pool-isolated (ADR-0023 precedent, applied here for the same reason: these
# nine cells are unproven/NOT_IMPLEMENTED — they must not compete for or
# distort the MLB/NBA bankroll pools). Separate portfolio file, separate
# bankroll, exactly mirroring T4M-PROJ's isolation rationale.
PORTFOLIO_PATH = LOG_DIR / "paper_portfolio_t1_nfl_game_market.json"
INITIAL_BANKROLL_USD = float(
    os.environ.get("T1_NFL_GAME_MARKET_INITIAL_BANKROLL_USD", "1000.0")
)

EDGE_THRESHOLD = float(os.environ.get("T1_NFL_GAME_MARKET_EDGE_THRESHOLD", "0.02"))

BAND = ExecutionBand.T1_MULTI_DAY

# GameMarket.market_type (bare string) -> MarketType enum. Conveniently,
# MarketType.NFL_*.value already matches measurement_stake.py's
# T1_GAME_MARKET_TYPES strings exactly, so no second mapping is needed for
# is_t1_game_market().
_GAME_MARKET_TYPE_MAP: dict[str, MarketType] = {
    "moneyline": MarketType.NFL_MONEYLINE,
    "spread": MarketType.NFL_SPREAD,
    "total": MarketType.NFL_GAME_TOTAL,
    "team_total": MarketType.NFL_TEAM_TOTAL,
}

_NFL_GAME_SERIES = ("KXNFLGAME", "KXNFLSPREAD", "KXNFLTOTAL", "KXNFLTEAMTOTAL")


# ---------------------------------------------------------------------------
# Injectable model interface (GG-255 Deliverable 2)
# ---------------------------------------------------------------------------


class NFLForecastModel(Protocol):
    """Swappable forecasting interface. No NFL C2/C3 layer exists yet — this
    Protocol is the seam a future trained model slots into without changing
    this script's pipeline code.

    PROVENANCE (GG-267): every implementation MUST declare this class
    attribute — a short human-readable model-identity string written to
    every position row and audit event this model produces. It must be
    readable off the class or an already-constructed instance WITHOUT
    triggering any re-fit/re-instantiation side effect (see
    nfl_exp027_adapter.py's docstring for why that distinction matters for
    EXP-027 specifically). There is no valid model with no PROVENANCE —
    _model_identity() below falls back to the literal string "UNKNOWN" for
    any object missing it, never to silence or another model's label."""

    PROVENANCE: str

    def predict_proba(
        self, market: GameMarket, features: dict[str, Any]
    ) -> float | None:
        """Return calibrated P(YES) in [0, 1], or None if no prediction is
        available for this market (e.g. missing upstream data) — None is a
        refusal signal, not an error, and callers must treat it as such."""
        ...


class StubNFLForecastModel:
    """EXPLICIT STUB — NOT a trained model (GG-255). No NFL C2 feature store
    or C3 model artifact exists. Returns a fixed placeholder probability (or
    None, to exercise the no-model refusal path) for pipeline-shape testing
    only. Any report of this script's output MUST state it ran against this
    stub, not a real model, whenever this class is in use.

    PROVENANCE (GG-267): explicit stub marker written to every row/audit
    event this instance produces, so a stub-produced row is distinguishable
    on disk from a trained-model-produced row without cross-referencing
    which script/session ran it."""

    PROVENANCE = "STUB (StubNFLForecastModel — NOT a trained model, GG-255)"

    def __init__(self, fixed_p: float | None = 0.55) -> None:
        self._fixed_p = fixed_p

    def predict_proba(
        self, market: GameMarket, features: dict[str, Any]
    ) -> float | None:
        return self._fixed_p


def _model_identity(model: NFLForecastModel) -> str:
    """Resolve a model's provenance label for row/audit-event labeling
    (GG-267). Reads the PROVENANCE class/instance attribute off the model
    object the caller already constructed — never instantiates or
    re-instantiates a model to obtain this (see nfl_exp027_adapter.py
    docstring: constructing EXP027NFLForecastModel re-fits it in-memory,
    forbidden as a side effect of a label lookup).

    Falls back to the explicit string "UNKNOWN" for any model missing a
    non-empty PROVENANCE — never blank, never another model's label, never
    silently absent — so a row can never be mislabeled by omission."""
    provenance = getattr(model, "PROVENANCE", None)
    if isinstance(provenance, str) and provenance:
        return provenance
    return "UNKNOWN"


# ---------------------------------------------------------------------------
# Core per-market decision logic (isolated for direct testing — GG-255
# Deliverable 4)
# ---------------------------------------------------------------------------


def evaluate_and_maybe_trade(
    mkt: GameMarket,
    *,
    snapshot_unparsed_count: int,
    model: NFLForecastModel,
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
    # GG-267: resolved once per market evaluation, off the model object the
    # caller already constructed (never re-instantiated) — see
    # _model_identity()'s docstring. Stamped into every audit payload below
    # and into the approval dict before open_position(), so every row this
    # run produces is labeled, not just the section-wide dashboard badge.
    model_identity = _model_identity(model)

    # GG-252: refuse to trade out of a batch known to have dropped markets —
    # a snapshot with unparsed_count > 0 signals parser/data-quality
    # uncertainty for the whole fetch, not just the dropped tickers.
    if snapshot_unparsed_count > 0:
        audit.warning(
            COMPONENT, "gg252_unparsed_markets_present",
            payload={
                "ticker": mkt.ticker, "unparsed_count": snapshot_unparsed_count,
                "model_identity": model_identity,
            },
            session_id=session_id,
        )
        return "REFUSED_UNPARSED"

    market_type = _GAME_MARKET_TYPE_MAP.get(mkt.market_type)
    if market_type is None or not is_t1_game_market(market_type.value):
        audit.warning(
            COMPONENT, "unmapped_market_type",
            payload={
                "ticker": mkt.ticker, "market_type": mkt.market_type,
                "model_identity": model_identity,
            },
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
                "model_identity": model_identity,
            },
            session_id=session_id,
        )
        return "REFUSED_KILL_SWITCH"

    if not mkt.has_live_quotes:
        audit.warning(
            COMPONENT, "no_live_quotes",
            payload={"ticker": mkt.ticker, "model_identity": model_identity},
            session_id=session_id,
        )
        return "REFUSED_NO_MODEL"  # no tradable price -> cannot evaluate

    features: dict[str, Any] = {
        "mid_price": mkt.mid_price, "vig": mkt.vig, "volume": mkt.volume,
    }
    p_estimate = model.predict_proba(mkt, features)
    if p_estimate is None:
        audit.warning(
            COMPONENT, "no_model_prediction",
            payload={"ticker": mkt.ticker, "model_identity": model_identity},
            session_id=session_id,
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
                "model_identity": model_identity,
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
            payload={
                "ticker": mkt.ticker, "reason": str(exc),
                "model_identity": model_identity,
            },
            session_id=session_id,
        )
        return "REFUSED_STAKE"

    forecast_record = {
        "forecast_id": f"T1-NFLGM-{session_id}-{mkt.ticker[-12:]}",
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
            payload={"ticker": mkt.ticker, "model_identity": model_identity},
            session_id=session_id,
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
            payload={
                "ticker": mkt.ticker, "approval": approval,
                "model_identity": model_identity,
            },
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
                "model_identity": model_identity,
            },
            session_id=session_id,
        )
        return "REJECTED"

    approval = {
        **approval,
        "entry_price_paid": round(entry_price, 4),  # ADR-0050 addendum §C
        "price_stratum": price_stratum,              # ADR-0050 addendum §C
        "contracts": contracts,                       # ADR-0050 addendum §B
        "model_identity": model_identity,             # GG-267
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


def main(model: NFLForecastModel | None = None) -> dict[str, int]:
    if model is None:
        model = StubNFLForecastModel()
        print(
            "WARNING: running against StubNFLForecastModel — NOT a trained "
            "model. No NFL C2/C3 layer exists yet (GG-255).",
            file=sys.stderr,
        )

    audit = AuditLogger(AUDIT_LOG_PATH)
    kalshi = KalshiMarketClient.from_env()
    engine = RiskEngine(
        logger=audit, snapshot_id="SNAP-T1-NFLGM-001", bankroll=INITIAL_BANKROLL_USD,
        # min_bet_usd=1.0: aligns to existing precedent (run_mlb_paper_trade.py's
        # MIN_BET_PAPER, run_t2_mlb_sameday.py's MIN_BET_PAPER, run_t4_mlb_live.py's
        # 0.01), not a new value. Without this override, RiskEngine defaults to the
        # live MIN_BET_USD=10.0 floor (risk.py) against this script's $1.00 ADR-0050
        # measurement stake (T1_MEASUREMENT_STAKE_USD) — an unintended mismatch
        # (GG-282/T-551): ADR-0059 explicitly cites the sibling paper-mode override
        # as the precedent that makes the flat-stake bypass "already work for T1
        # with zero code change," but that override was never actually applied when
        # this script was written (T-530/DECISION_LOG does not mention min_bet_usd).
        min_bet_usd=1.0,
    )
    # kalshi_client=None, unconditionally — this is the sole mechanical
    # guard against a live order path (GG-255 DO NOT constraint).
    trader = PaperTrader(portfolio_path=PORTFOLIO_PATH, logger=audit, kalshi_client=None)

    outcome_counts: dict[str, int] = {}
    for series in _NFL_GAME_SERIES:
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

    print(f"T1 NFL game-market run complete: {outcome_counts}")
    return outcome_counts


if __name__ == "__main__":
    main()
