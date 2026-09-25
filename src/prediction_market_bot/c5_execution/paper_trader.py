"""
C5 Sub-module: Paper Trader — Order Execution + Local Ledger (PIPE-03)
=======================================================================
Component:    C5 (Execution Engine) — paper trading sub-module
Phase active: Phase 6 (paper trading; ENV-02 only)
Status:       UPDATED — 2026-05-31 (ADR-0008: Kalshi demo order submission added)
Gate:         BOT_ENV=paper required

Responsibility:
  Submit C4-approved bets to Kalshi demo AND record them locally.
  Local paper_portfolio.json is the authoritative G6 evidence ledger.
  Kalshi demo orders are the live execution confirmation.

Order submission (ADR-0008):
  If KalshiMarketClient is provided with a loaded RSA private key, every
  open_position() call submits a real order to Kalshi demo. The Kalshi
  order_id and status are recorded in the position. If Kalshi submission
  fails (non-2xx — no capital ever reached the venue), the position is
  still recorded locally for audit purposes but routed to
  rejected_positions rather than open_positions (GG-079/T-234), a warning
  is logged, and open_position() returns an empty position dict so callers'
  `if pos:` fired/deployed-capital accounting does not count it. Local
  ledger is always authoritative for G6 P&L.

Portfolio state:
  Persisted to logs/paper_portfolio.json after every operation.
  Immutable history: closed_positions are never modified after resolution.

Outcome resolution:
  For any open position where game_date < today: fetch the player's
  actual stat from the sport's data source and compare to the Kalshi
  bet threshold. YES wins if actual_stat >= threshold; NO wins otherwise.
  Bankroll updated accordingly.
  Sport-agnostic: settle_position() handles P&L + ledger; the caller
  fetches the stat. resolve_pending() is the NBA-specific wrapper that
  uses nba_api. run_resolve_mlb.py is the MLB-specific resolver.

Kill switch:
  All public methods return (bool, ...). False = C6 write failure → halt.
  Kalshi submission failure does NOT trigger kill switch — degraded mode only.
"""

from __future__ import annotations

import json
import threading
import time
import uuid
from contextlib import contextmanager
from datetime import datetime, date, timezone
from pathlib import Path
from typing import TYPE_CHECKING, Any, Iterator, Optional

try:
    import fcntl  # POSIX only (Linux VPS + macOS dev); absent on Windows.
    _HAS_FCNTL = True
except ImportError:  # pragma: no cover - non-POSIX fallback
    _HAS_FCNTL = False

import pandas as pd

from prediction_market_bot.c6_audit_logger.audit_logger import AuditLogger
from prediction_market_bot.c5_execution.market_type_registry import MarketType
from prediction_market_bot.logic_epoch import (
    CURRENT_APPROVAL_COMMIT,
    CURRENT_LOGIC_EPOCH,
)

if TYPE_CHECKING:
    from prediction_market_bot.c5_execution.kalshi_client import KalshiMarketClient

COMPONENT = "C5-PAPER"

INITIAL_BANKROLL_USD: float = 1000.00

# GG-271: rejected_positions is a live ring buffer, not an event log — every
# Kalshi order rejection is already durably captured in the C6 audit log at
# write time (open_position()'s "kalshi_order_failed" warning, logged before
# the append below), so bounding here does not lose the only copy. The bound
# is sized against this field's one live functional reader,
# monitor.py::check_failed_order_rate (invoked once per pool per day via
# run_resolve_mlb.py's 06:30 UTC cron) — 2,000 comfortably spans that daily
# cadence with multi-day margin even at the accelerated ~1,000-1,200/day
# rejection rate observed 2026-09-11, while keeping this field's steady-state
# footprint in the low single-digit MB range regardless of process uptime.
MAX_REJECTED_POSITIONS: int = 2000

# Box 1.5 (T-442): NO-direction vig coefficient per (market_type, band) cell,
# extracted from the inline if/elif/band cascade that used to live directly
# in open_position(). YES-direction bets never consult this table — they use
# gross_edge directly regardless of band (see _directional_edge() below).
# A (market_type, band) pair with no entry here falls through to coefficient
# 0.0, which reproduces the pre-extraction "else: -gross_edge" branch exactly.
#
# Coefficients are pinned by prior DS sign-off, per band, and must not change
# without a new sign-off (ADR-0043 §D3 scopes sign-off per-band, not
# globally):
#   T4M-PROJ = 2.0 — ADR-0043 (GG-113's vig-sign derivation).
#   T1       = 1.0 — GG-119/ADR-0045 (T1's gross_edge already embeds
#              half_spread, so 1.0*vig == 2.0*half_spread exactly).
# All cells below are MLB_PLAYER_PROP_HITS because that is the only
# market_type with live band traffic today — this table is what lets a
# future market type (e.g. MLB_MONEYLINE) register its own per-band
# coefficients without touching open_position()'s logic again.
_NO_DIRECTION_VIG_COEFFICIENT: dict[tuple[MarketType, str], float] = {
    (MarketType.MLB_PLAYER_PROP_HITS, "T4M-PROJ"): 2.0,
    (MarketType.MLB_PLAYER_PROP_HITS, "T1"): 1.0,
}


def _directional_edge(
    direction: str,
    band: str | None,
    market_type: MarketType,
    gross_edge: float,
    vig: float,
) -> float:
    """
    Pure extraction of the vig cascade formerly inlined in open_position()
    (box 1.5, T-442). See _NO_DIRECTION_VIG_COEFFICIENT above for the
    per-cell coefficients and their DS-sign-off provenance.
    """
    if direction == "YES":
        return gross_edge
    coeff = _NO_DIRECTION_VIG_COEFFICIENT.get((market_type, band), 0.0)
    return -gross_edge - coeff * vig

# GG-034: a closed position carries `pnl` (resolved/CLOSED) XOR `exit_pnl`
# (early-exit/EXITED). The two keys are mutually exclusive per position, so
# summing both is the single authoritative realized-P&L source. Any derivation
# that reads only `pnl` silently under-counts every EXITED position.
RECONCILE_TOLERANCE_USD: float = 0.01


def _position_pnl(p: dict[str, Any]) -> float:
    """Realized P&L of one closed position, covering both resolve and exit paths."""
    return float(p.get("pnl", 0.0)) + float(p.get("exit_pnl", 0.0))


class PortfolioReconciliationError(RuntimeError):
    """Raised when the stored realized-P&L scalar diverges from the ledger
    beyond RECONCILE_TOLERANCE_USD under strict reconciliation (GG-034)."""


def _utc_now() -> str:
    return datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"

def _today() -> str:
    return date.today().isoformat()


class PaperTrader:
    """
    Paper trading execution engine — records and tracks simulated bets.

    Usage::

        trader = PaperTrader(
            portfolio_path=Path("logs/paper_portfolio.json"),
            logger=audit_logger,
        )

        # After C4 approves a forecast:
        ok, pos = trader.open_position(
            approval=c4_decision,
            player_name="SGA",
            player_id=1628983,
            kalshi_ticker="KXNBAPTS-...",
            kalshi_threshold=30,
            mid_price=0.280,
            vig=0.040,
            game_date="2026-05-29",
            session_id=session_id,
        )

        # Next day — resolve previous positions:
        ok, resolved = trader.resolve_pending(session_id=session_id)
    """

    def __init__(
        self,
        portfolio_path: Path,
        logger: AuditLogger,
        kalshi_client: Optional["KalshiMarketClient"] = None,
    ) -> None:
        self._path = portfolio_path
        self._logger = logger
        self._kalshi = kalshi_client  # None → local-only mode
        self._lock = threading.Lock()
        self._state = self._load_or_init()
        # GG-034: detect a desynced realized-P&L scalar at load time and adopt the
        # ledger value before any health surface reads it. In-memory only — does not
        # write the file (correction persists on the next real mutation's _save()).
        self.reconcile()

    # ------------------------------------------------------------------
    # State management
    # ------------------------------------------------------------------

    def _load_or_init(self) -> dict[str, Any]:
        if self._path.exists():
            try:
                state = json.loads(self._path.read_text())
                # GG-079/T-234: files written before this bucket existed lack the key.
                state.setdefault("rejected_positions", [])
                return state
            except Exception:
                pass
        return {
            "bankroll_usd": INITIAL_BANKROLL_USD,
            "initial_bankroll_usd": INITIAL_BANKROLL_USD,
            "total_realized_pnl": 0.0,
            "current_daily_loss": 0.0,
            "daily_loss_date": _today(),
            "open_positions": [],
            "closed_positions": [],
            "rejected_positions": [],  # GG-079/T-234: orders Kalshi never accepted
            "created_at": _utc_now(),
            "last_updated": _utc_now(),
        }

    def _ledger_realized_pnl(self) -> float:
        """Authoritative realized P&L = Σ over the immutable closed-position ledger.

        GG-034: this replaces the old `total_realized_pnl` accumulator, which was
        incremented in-memory under an in-process lock only and drifted when
        concurrent runner processes clobbered each other's load→mutate→save.
        The closed_positions list and the C6 audit log are append-only ground
        truth; this value is now derived from them and can no longer desync.
        """
        return round(
            sum(_position_pnl(p) for p in self._state.get("closed_positions", [])),
            4,
        )

    def _ledger_bankroll(self) -> float:
        """Authoritative free cash, derived from the position ledger (GG-034).

        Cash identity (non-isolated positions only):
            bankroll = initial
                       + Σ realized pnl on closed positions   (stake returned + pnl)
                       − Σ entry cost of still-open positions  (stake out in flight)

        pool_isolated (T4) positions never touch the main bankroll on entry or
        close, so they are excluded from both sums. Deriving this also fixes the
        latent resolve_pending bug where the resolve path credited the bankroll
        unconditionally, ignoring pool_isolated.
        """
        initial = float(self._state.get("initial_bankroll_usd", INITIAL_BANKROLL_USD))
        closed_pnl = sum(
            _position_pnl(p)
            for p in self._state.get("closed_positions", [])
            if not p.get("pool_isolated", False)
        )
        open_cost = sum(
            float(p.get("size_usd", 0.0))
            for p in self._state.get("open_positions", [])
            if not p.get("pool_isolated", False)
        )
        return round(initial + closed_pnl - open_cost, 4)

    def exposure_snapshot(self) -> dict[str, float]:
        """Portfolio-state snapshot for C4's ADR-0026 deployment invariant (GG-035).

        Returns the two figures the free-cash invariant needs, derived from the
        same ledger identity as _ledger_bankroll (non-isolated positions only):

            open_exposure_usd — Σ entry cost of still-open NON-isolated positions
                                (capital currently in flight).
            equity_usd        — initial + Σ closed non-isolated pnl
                                (= bankroll + open_exposure; the deployable base).

        T4 (pool_isolated) positions are excluded — they run their own budget
        (ADR-0013/0022/0023). free_cash_usd == _ledger_bankroll() by construction.
        """
        initial = float(self._state.get("initial_bankroll_usd", INITIAL_BANKROLL_USD))
        closed_pnl = sum(
            _position_pnl(p)
            for p in self._state.get("closed_positions", [])
            if not p.get("pool_isolated", False)
        )
        open_exposure = sum(
            float(p.get("size_usd", 0.0))
            for p in self._state.get("open_positions", [])
            if not p.get("pool_isolated", False)
        )
        return {
            "open_exposure_usd": round(open_exposure, 4),
            "equity_usd": round(initial + closed_pnl, 4),
            "free_cash_usd": round(initial + closed_pnl - open_exposure, 4),
        }

    # ------------------------------------------------------------------
    # Cross-process safety (GG-034)
    # ------------------------------------------------------------------
    # The portfolio JSON is written by four separate runner processes
    # (run_paper_trade, run_resolve, run_t4_live, run_t4_resolve_local). A
    # threading.Lock only serialises threads within ONE process; across
    # processes, load→mutate→save races clobber appended positions. Every
    # mutating section therefore runs under an exclusive file lock and re-reads
    # the latest committed state from disk before applying its single change.

    @contextmanager
    def _file_lock(self) -> Iterator[None]:
        if not _HAS_FCNTL:  # pragma: no cover - non-POSIX fallback
            yield
            return
        lock_path = self._path.with_suffix(self._path.suffix + ".lock")
        lock_path.parent.mkdir(parents=True, exist_ok=True)
        fd = open(lock_path, "w")
        try:
            fcntl.flock(fd, fcntl.LOCK_EX)
            yield
        finally:
            fcntl.flock(fd, fcntl.LOCK_UN)
            fd.close()

    def _reload_locked(self) -> None:
        """Re-read the latest committed state from disk. Call only while holding
        _file_lock so a concurrent writer's appends are not lost on save."""
        if self._path.exists():
            try:
                self._state = json.loads(self._path.read_text())
                self._state.setdefault("rejected_positions", [])
            except Exception:
                pass

    def _save(self) -> bool:
        try:
            self._path.parent.mkdir(parents=True, exist_ok=True)
            # GG-034: realized P&L and bankroll are derived from the ledger on every
            # save, never incremented. Any in-memory drift is corrected here before
            # persistence, so no scalar can desync from the position lists.
            self._state["total_realized_pnl"] = self._ledger_realized_pnl()
            self._state["bankroll_usd"] = self._ledger_bankroll()
            self._state["last_updated"] = _utc_now()
            # GG-271: enforce the rejected_positions ring buffer on every save,
            # regardless of which caller appended — this is the single choke
            # point every mutation already passes through, so bounding here
            # (rather than at each append site) cannot be bypassed by a future
            # writer. Drop-oldest: keeps the most recent MAX_REJECTED_POSITIONS.
            rejected = self._state.get("rejected_positions")
            if isinstance(rejected, list) and len(rejected) > MAX_REJECTED_POSITIONS:
                self._state["rejected_positions"] = rejected[-MAX_REJECTED_POSITIONS:]
            self._path.write_text(json.dumps(self._state, indent=2))
            return True
        except OSError:
            return False

    def ensure_persisted(self) -> None:
        """Write the portfolio file if it does not yet exist.

        Called at pipeline start so monitoring tools and the MLB dashboard
        see the file even when no bets are placed (e.g., contamination guard
        fires before the first bet). Safe to call multiple times — no-op if
        the file is already on disk.
        """
        if not self._path.exists():
            self._save()

    def reconcile(
        self,
        *,
        strict: bool = False,
        session_id: str | None = None,
    ) -> tuple[bool, dict[str, Any]]:
        """Check the stored realized-P&L scalar against the ledger (GG-034).

        The drawdown kill switch (risk.py), C7 monitor, C8 dashboard, and the G6
        gate all read `total_realized_pnl`. If that scalar has drifted from the
        closed-position ledger, every one of those health surfaces is reporting a
        false number — the exact failure mode that left the −25% drawdown blind to
        the 20% kill switch. This logs the drift loudly and adopts the ledger value
        as authoritative (or raises under strict=True for invariant tests/asserts).

        Pure check: does not write the file. The corrected value is persisted only
        when the next real mutation calls _save().
        """
        stored = float(self._state.get("total_realized_pnl", 0.0))
        derived = self._ledger_realized_pnl()
        drift = round(stored - derived, 4)
        report = {
            "stored_total_realized_pnl": stored,
            "ledger_total_realized_pnl": derived,
            "drift_usd": drift,
            "n_closed": len(self._state.get("closed_positions", [])),
        }
        ok = True
        if abs(drift) > RECONCILE_TOLERANCE_USD:
            ok = self._logger.warning(
                COMPONENT, "portfolio_pnl_desync",
                payload={
                    **report,
                    "note": (
                        "GG-034: stored total_realized_pnl diverged from the "
                        "closed-position ledger; ledger is authoritative. All "
                        "health surfaces (kill switch/monitor/dashboard/G6) were "
                        "reading the corrupted scalar."
                    ),
                },
                session_id=session_id,
            )
            if strict:
                raise PortfolioReconciliationError(
                    f"realized-P&L desync: stored={stored} ledger={derived} "
                    f"drift={drift} (tolerance ${RECONCILE_TOLERANCE_USD})"
                )
            self._state["total_realized_pnl"] = derived
        return ok, report

    def _reset_daily_loss_if_new_day(self) -> None:
        today = _today()
        if self._state.get("daily_loss_date") != today:
            self._state["current_daily_loss"] = 0.0
            self._state["daily_net_pnl"] = 0.0
            self._state["daily_loss_date"] = today

    def _accumulate_daily_loss(self, pnl: float) -> None:
        """Net daily-loss semantics: wins offset losses within the same day.

        current_daily_loss = max(0, -daily_net_pnl), so MAX_DAILY_LOSS_PCT
        (ADR-0012) gates on true net daily loss. Gross-only accumulation made
        a profitable high-churn night able to halt betting (G3: gross $317.76
        vs net -$198.84). ADR-0012 amendment registered as T-156.
        """
        self._reset_daily_loss_if_new_day()
        self._state["daily_net_pnl"] = round(
            self._state.get("daily_net_pnl", 0.0) + pnl, 4)
        self._state["current_daily_loss"] = round(
            max(0.0, -self._state["daily_net_pnl"]), 4)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_state(self) -> dict[str, Any]:
        """Return current portfolio state (copy — not live reference)."""
        with self._lock:
            return dict(self._state)

    def open_position(
        self,
        approval: dict[str, Any],
        kalshi_ticker: str,
        mid_price: float,
        vig: float,
        game_date: str,
        player_name: str | None = None,
        player_id: int | None = None,
        kalshi_threshold: float | None = None,
        market_type: MarketType | None = None,
        session_id: str | None = None,
        pool_isolated: bool = False,
        h_so_far_at_entry: int | None = None,
        ab_remaining_at_entry: int | None = None,
    ) -> tuple[bool, dict[str, Any]]:
        """
        Record a C4-approved paper bet.

        Deducts the approved size from the paper bankroll unless pool_isolated=True,
        in which case the position is recorded but the main bankroll is not touched.
        Used for T4 paper mode, where T4 tracks its own isolated pool (ADR-0023:
        pool_isolated=True hardcoded) so T1 and T4 do not compete for the same
        bankroll. Logs to C6. Returns (ok, position_record).

        player_name/player_id (box 1.4, T-442) are optional — meaningful only
        for player-prop markets (e.g. KXMLBHIT); a game-market bet (moneyline,
        spread/run_line, totals, team_totals) leaves them None.
        kalshi_threshold is float | None but should be None only for a
        player-prop market whose C1/C2 layer has no threshold concept at
        all — every game-market caller must pass a real float (0.0 for
        moneyline/partial_game, the real floor_strike otherwise; see
        kalshi_client.py::derive_kalshi_threshold(), GG-291). This method
        does not itself enforce that -- the refuse/raise guard lives at each
        call site, since only the caller knows whether a None here is
        expected for its market type. kalshi_ticker/mid_price/vig/game_date
        are universal to every market type and remain required.

        market_type (box 1.5, T-442) selects the vig-cascade cell in
        _NO_DIRECTION_VIG_COEFFICIENT. Every existing caller omits it, so it
        defaults to MLB_PLAYER_PROP_HITS — the only market_type with live
        band traffic today — reproducing pre-extraction behavior exactly.
        """
        with self._lock, self._file_lock():
            # GG-034: re-read the latest committed state so a concurrent runner's
            # appended positions are not clobbered by this load→mutate→save.
            self._reload_locked()
            self._reset_daily_loss_if_new_day()

            size    = float(approval.get("approved_size", 0.0))
            direction = str(approval.get("approved_direction", "PASS"))
            risk_id   = str(approval.get("risk_eval_id", ""))
            forecast_id = str(approval.get("forecast_id", ""))
            band = approval.get("band")  # T-253: T1/T2/T3/T4/T4M-PROJ/... — caller-supplied, no derivation

            if size <= 0 or direction == "PASS":
                return True, {}

            entry_cost = size  # cost = size (we pay mid_price per $1 contract)

            model_p    = float(approval.get("model_p", 0.0))
            # ADR-0016: approval["gross_edge"] is pre-fee; "edge" is net-of-fee.
            # Prefer explicit gross_edge key; fall back to edge for backward compat.
            gross_edge = float(approval.get("gross_edge", approval.get("edge", 0.0)))
            fee_per_contract = round(0.07 * mid_price * (1.0 - mid_price), 6)
            # gross_edge is stored signed YES-direction (ADR-0016); NO bets have
            # negative gross_edge, so it must be flipped before applying the fee
            # to get the bet's true, direction-effective edge. GG-077: this flip
            # was previously applied only to fee_contaminated, never to
            # fee_net_edge itself, so the stored field silently represented the
            # YES-side edge of the opposite bet for every NO position.
            #
            # GG-113: a plain sign flip (-gross_edge) also flips vig's sign,
            # turning it from a cost into a credit for NO bets, since
            # gross_edge = (p - mip) - vig already has vig baked in with a
            # fixed sign. -gross_edge = -(p - mip) + vig. Correcting for NO
            # requires -(p - mip) - vig, i.e. -gross_edge - 2*vig, so vig stays
            # a symmetric cost regardless of direction (matches
            # run_exp017.py's compute_pnl_unit() convention).
            #
            # ADR-0043's DS sign-off is scoped to T4M-PROJ only (D3): T1/T2/T3
            # share this function but each has its own gating formula. T2/T3
            # are left deliberately unfixed pending their own sign-off.
            # Applying a corrected formula unconditionally here would
            # silently change T2/T3's stored ledger values without
            # authorization, so the fix is band-gated per band.
            #
            # GG-119/ADR-0045: T1's gross_edge (run_mlb_paper_trade.py) is
            # computed as p - mid - half_spread, i.e. it already embeds only
            # half_spread (vig/2.0), unlike T4M-PROJ's gross_edge
            # (run_t4_mlb_live.py) which embeds the FULL vig. The `vig` param
            # passed into this function is always the full spread regardless
            # of band, so the two bands' corrections need different
            # coefficients on the same `vig` value to both land on
            # "-gross_edge - 2*half_spread": T4M-PROJ needs -2.0*vig (its
            # gross_edge already has 1*vig baked in, so 2 more full vigs
            # cancel/correct it per ADR-0043's derivation), while T1 needs
            # only -1.0*vig, since 1.0*vig == 2.0*half_spread exactly. Mirrors
            # run_mlb_paper_trade.py::_directional_edge()'s NO branch.
            _resolved_market_type = market_type or MarketType.MLB_PLAYER_PROP_HITS
            if market_type is None:
                # GG-184: every current call site relies on this default rather
                # than passing market_type explicitly. Non-fatal — just make the
                # defaulting visible in the audit trail so it isn't silent the
                # day a second market type goes live and a call site is missed.
                self._logger.warning(
                    COMPONENT, "market_type_defaulted",
                    payload={
                        "resolved_market_type": _resolved_market_type.value,
                        "kalshi_ticker": kalshi_ticker,
                        "band": band,
                    },
                    session_id=session_id,
                )
            _directional_gross = _directional_edge(
                direction, band, _resolved_market_type, gross_edge, vig
            )
            fee_net_edge = round(_directional_gross - fee_per_contract, 6)
            probable_injury_signal = bool(model_p > 0.0 and abs(model_p - mid_price) > 0.25)

            if pool_isolated:
                # T4 flat-sizing mode: position recorded; main bankroll unchanged.
                # T4 tracks its own pool via t4_deployed_usd in run_t4_live.py.
                pass
            else:
                # Reject if free cash cannot cover the stake. Bankroll itself is
                # DERIVED from the ledger in _save() (GG-034) — appending this open
                # position is what reduces it; do not decrement the scalar here.
                if entry_cost > self._state["bankroll_usd"]:
                    ok = self._logger.warning(
                        COMPONENT, "insufficient_bankroll",
                        payload={"required": entry_cost, "available": self._state["bankroll_usd"]},
                        session_id=session_id,
                    )
                    return ok, {}

            pos = {
                "position_id": f"POS-{uuid.uuid4().hex[:10].upper()}",
                "player_name": player_name,
                "player_id": player_id,
                "kalshi_ticker": kalshi_ticker,
                "kalshi_threshold": kalshi_threshold,
                "direction": direction,
                "mid_price_at_entry": round(mid_price, 4),
                "vig_at_entry": round(vig, 4),
                "size_usd": round(size, 4),
                "game_date": game_date,
                "entered_at": _utc_now(),
                "risk_eval_id": risk_id,
                "forecast_id": forecast_id,
                "band": band,
                "logic_epoch": CURRENT_LOGIC_EPOCH,  # T-320: write-path provenance
                "approval_commit": CURRENT_APPROVAL_COMMIT,  # T-320: resolving commit SHA for logic_epoch
                "status": "OPEN",
                "pool_isolated": pool_isolated,  # ADR-0019: exit_position uses this to skip bankroll update
                "kalshi_order_id": None,
                "kalshi_order_status": "local_only",
                "kalshi_contracts": None,
                "model_p": round(model_p, 6),
                "gross_edge": round(gross_edge, 6),
                "fee_per_contract": fee_per_contract,
                "fee_net_edge": fee_net_edge,
                "fee_contaminated": bool(fee_net_edge < 0.0),
                "probable_injury_signal": probable_injury_signal,
                "t3_signal": str(approval.get("t3_signal", "NEUTRAL")),   # EXP-018: T3 overlay signal at entry
                "t1_edge": round(float(approval.get("t1_edge", gross_edge)), 6),  # EXP-018: raw T1 edge pre-T3
                # T-225: live-state snapshot at entry, used by T4 MLB's per-ticker
                # re-entry dedup guard to detect whether p_t4's inputs have moved
                # since this ticker's last fire. None for non-T4 callers.
                "h_so_far_at_entry": h_so_far_at_entry,
                "ab_remaining_at_entry": ab_remaining_at_entry,
                # ADR-0050 addendum §C (2026-07-30): pre-registered price-stratum
                # stamp, written at entry time — not derivable post hoc from
                # mid_price_at_entry alone, since that field is YES-frame regardless
                # of direction while entry_price_paid is direction-adjusted (NO pays
                # 1-mid_price_at_entry). None for non-T4M-PROJ callers (field is
                # opt-in via approval dict; absence is not an error).
                "entry_price_paid": approval.get("entry_price_paid"),
                "price_stratum": approval.get("price_stratum"),
                "contracts": approval.get("contracts"),
                # ADR-0053 §6.3 item 2: persist the cell key's market_type axis
                # on the position record itself, not just derivable via band.
                "market_type": _resolved_market_type.value,
                # GG-267: per-row model-identity provenance. Opt-in via the
                # approval dict (only run_t1_nfl_game_market.py populates it
                # today) — never absent/empty/None: any caller that doesn't
                # supply it (every MLB/NBA path) gets the explicit literal
                # "UNKNOWN" written, never a default that could be mistaken
                # for a real model label. A legacy row predating this field
                # entirely (no key at all) reads the same "UNKNOWN" on load
                # via .get() at render time — see web_dashboard.py.
                "model_identity": approval.get("model_identity") or "UNKNOWN",
            }

            # Submit to Kalshi demo if client is available (ADR-0008)
            if self._kalshi and self._kalshi.has_signing_key() and kalshi_ticker:
                side = direction.lower()  # "yes" or "no"
                order = self._kalshi.submit_order(
                    ticker=kalshi_ticker,
                    side=side,
                    size_usd=size,
                    mid_price=mid_price,
                    client_order_id=pos["position_id"],
                )
                # GG-303/T-576 defense-in-depth: never trust order.order_id as a
                # confirmed exchange acknowledgement if it's empty, even when
                # order.ok is True. kalshi_client.py's submit_order() now refuses
                # this case itself, but the write boundary here must not depend
                # solely on that upstream guarantee holding forever.
                if order.ok and order.order_id:
                    pos["kalshi_order_id"] = order.order_id
                    pos["kalshi_order_status"] = order.status
                    pos["kalshi_contracts"] = order.contracts
                else:
                    if order.ok and not order.order_id:
                        order.error = order.error or (
                            "order.ok=True but order_id was empty -- refusing to "
                            "persist as a confirmed position (GG-303)"
                        )
                    # GG-079/T-234: a non-2xx response means Kalshi never accepted
                    # this order — no capital is at risk with the venue. Route to
                    # rejected_positions at write time rather than open_positions,
                    # so exposure math (_reconstruct_t4_ledger, exposure_snapshot,
                    # kill-switch proximity) never counts a non-executed order as
                    # deployed capital, and the caller's `if pos:` truthiness check
                    # (uniform across every T1/T2/T4 caller) does not count it as
                    # a placed bet either.
                    pos["kalshi_order_status"] = f"failed: {order.error}"
                    pos["status"] = "REJECTED"
                    self._logger.warning(
                        COMPONENT, "kalshi_order_failed",
                        payload={
                            "position_id": pos["position_id"],
                            "ticker": kalshi_ticker,
                            "error": order.error,
                            "note": "rejected: Kalshi order not placed, no capital deployed",
                        },
                        session_id=session_id,
                    )
                    time.sleep(2.0)  # T-164/GG-014: raised 0.5→2.0s; 29-order burst hit rate-limit at 0.5s
                    self._state.setdefault("rejected_positions", []).append(pos)
                    ok_save = self._save()
                    return ok_save, {}
                time.sleep(2.0)  # T-164/GG-014: raised 0.5→2.0s; 29-order burst hit rate-limit at 0.5s

            self._state["open_positions"].append(pos)

            ok_save = self._save()
            ok_log  = self._logger.info(
                COMPONENT, "paper_order_opened",
                payload={
                    "position_id": pos["position_id"],
                    "player_name": player_name,
                    "direction": direction,
                    "size_usd": size,
                    "mid_price": mid_price,
                    "kalshi_threshold": kalshi_threshold,
                    "bankroll_after": self._state["bankroll_usd"],
                    "game_date": game_date,
                    "kalshi_order_id": pos["kalshi_order_id"],
                    "kalshi_order_status": pos["kalshi_order_status"],
                    "kalshi_contracts": pos["kalshi_contracts"],
                },
                session_id=session_id,
            )
            return (ok_save and ok_log), pos

    def exit_position(
        self,
        position_id: str,
        exit_mip: float,
        p_current: float,
        exit_reason: str,
        session_id: str | None = None,
    ) -> tuple[bool, dict[str, Any]]:
        """
        Early exit from an open position (ADR-0018/0019 — band exit mechanics).

        Sells the position at the current market mid price before expiry.
        EXP-019B analytic: Kelly fraction → 0 at exit boundary, so full exit
        is always the correct action. Partial exit is never implemented.

        PnL formula (pre-fee):
          YES: pnl = size × (exit_mip / entry_mip  − 1)
          NO:  pnl = size × ((1−exit_mip) / (1−entry_mip) − 1)

        Kalshi charges a taker fee on exit in the same form as entry
        (ADR-0016): fee = 0.07 × exit_mip × (1−exit_mip).
        We record this but do NOT deduct from paper P&L — paper fees are
        notional until G6 live capital (T-151).

        pool_isolated positions (T4 flat-sizing): bankroll is NOT adjusted
        (never was deducted on entry); only total_realized_pnl updated.
        Returns (ok, closed_position_record). Empty dict if position not found.
        """
        with self._lock, self._file_lock():
            # GG-034: re-read latest committed state under the file lock. The lookup
            # below then doubles as a guard — if a concurrent runner already closed
            # this position it will be absent and we no-op rather than double-close.
            self._reload_locked()
            pos = next(
                (p for p in self._state["open_positions"] if p["position_id"] == position_id),
                None,
            )
            if pos is None:
                return True, {}

            size        = pos["size_usd"]
            entry_mip   = pos["mid_price_at_entry"]
            direction   = pos["direction"]
            pool_isolated = pos.get("pool_isolated", False)

            if direction == "YES":
                exit_proceeds = size * (exit_mip / entry_mip) if entry_mip > 0 else 0.0
            else:
                entry_no = 1.0 - entry_mip
                exit_no  = 1.0 - exit_mip
                exit_proceeds = size * (exit_no / entry_no) if entry_no > 0 else 0.0

            pnl = round(exit_proceeds - size, 4)

            # Exit taker fee (notional in paper mode — not deducted from P&L per T-151)
            exit_fee_per_contract = round(0.07 * exit_mip * (1.0 - exit_mip), 6)

            # Remove from open positions
            self._state["open_positions"] = [
                p for p in self._state["open_positions"]
                if p["position_id"] != position_id
            ]

            closed_pos = {
                **pos,
                "status": "EXITED",
                "exit_mip": round(exit_mip, 6),
                "p_current_at_exit": round(p_current, 6),
                "exit_reason": exit_reason,
                "exit_pnl": pnl,
                "exit_fee_per_contract": exit_fee_per_contract,
                "exited_at": _utc_now(),
            }
            self._state["closed_positions"].append(closed_pos)
            # GG-034: both total_realized_pnl and bankroll_usd are derived from the
            # ledger in _save() — moving this position from open→closed is what
            # returns its stake+pnl to the derived bankroll (pool_isolated excluded
            # by _ledger_bankroll). No imperative scalar updates here.
            self._accumulate_daily_loss(pnl)

            ok_save = self._save()
            ok_log  = self._logger.info(
                COMPONENT, "paper_position_exited",
                payload={
                    "position_id": position_id,
                    "player_name": pos["player_name"],
                    "direction": direction,
                    "threshold": pos["kalshi_threshold"],
                    "size_usd": size,
                    "entry_mip": entry_mip,
                    "exit_mip": exit_mip,
                    "p_current": p_current,
                    "pnl": pnl,
                    "exit_reason": exit_reason,
                    "bankroll_after": self._state["bankroll_usd"],
                    "pool_isolated": pool_isolated,
                },
                session_id=session_id,
            )
            return (ok_save and ok_log), closed_pos

    def resolve_pending(
        self,
        session_id: str | None = None,
    ) -> tuple[bool, list[dict]]:
        """
        Resolve all open positions where game_date < today using nba_api.

        Returns (ok, list_of_resolved_positions).
        Logs each resolution to C6.

        Note: stats.nba.com blocks datacenter IPs (403). If running from a
        cloud server, this method will log a warning and return no resolved
        positions. Use run_resolve_local.py to resolve from a non-blocked IP.
        """
        today = _today()
        with self._lock:
            pending = [
                p for p in self._state["open_positions"]
                if p.get("game_date", today) <= today
            ]

        if not pending:
            return True, []

        try:
            from nba_api.stats.endpoints import PlayerGameLog
        except ImportError:
            ok = self._logger.warning(
                COMPONENT, "nba_api_not_available",
                payload={"note": "Cannot resolve positions — nba_api not installed"},
                session_id=session_id,
            )
            return ok, []

        resolved = []
        all_ok = True

        for pos in pending:
            player_id   = pos["player_id"]
            game_date   = pos["game_date"]  # YYYY-MM-DD
            threshold   = pos["kalshi_threshold"]
            direction   = pos["direction"]
            size        = pos["size_usd"]
            mid         = pos["mid_price_at_entry"]

            # Determine season from game_date (nba_api format: "YYYY-YY")
            year = int(game_date[:4])
            month = int(game_date[5:7])
            season_start_year = year if month >= 10 else year - 1
            season = f"{season_start_year}-{str(season_start_year + 1)[-2:]}"

            actual_pts = None
            try:
                time.sleep(0.6)  # rate limit
                log = PlayerGameLog(player_id=player_id, season=season,
                                    season_type_all_star="Regular Season")
                df = log.get_data_frames()[0]
                df["GAME_DATE"] = pd.to_datetime(df["GAME_DATE"], format="mixed").dt.strftime("%Y-%m-%d")
                row = df[df["GAME_DATE"] == game_date]
                if not row.empty:
                    actual_pts = float(row.iloc[0]["PTS"])
            except Exception as e:
                self._logger.warning(
                    COMPONENT, "player_stats_fetch_failed",
                    payload={"player_id": player_id, "game_date": game_date,
                             "season": season, "season_type": "Regular Season",
                             "error": str(e)},
                    session_id=session_id,
                )

            # Always try Playoffs if Regular Season had no result (playoff games return
            # empty rows from Regular Season endpoint without throwing)
            if actual_pts is None:
                try:
                    time.sleep(0.6)
                    log = PlayerGameLog(player_id=player_id, season=season,
                                        season_type_all_star="Playoffs")
                    df = log.get_data_frames()[0]
                    df["GAME_DATE"] = pd.to_datetime(df["GAME_DATE"], format="mixed").dt.strftime("%Y-%m-%d")
                    row = df[df["GAME_DATE"] == game_date]
                    if not row.empty:
                        actual_pts = float(row.iloc[0]["PTS"])
                except Exception as e:
                    self._logger.warning(
                        COMPONENT, "player_stats_fetch_failed",
                        payload={"player_id": player_id, "game_date": game_date,
                                 "season": season, "season_type": "Playoffs",
                                 "error": str(e)},
                        session_id=session_id,
                    )

            if actual_pts is None:
                continue  # Game not found yet — try again tomorrow

            # Determine outcome
            yes_won = actual_pts >= threshold
            if direction == "YES":
                won = yes_won
                # Payout: win $1 - ask price; lose stake
                yes_ask = mid + pos["vig_at_entry"] / 2
                pnl = size * (1.0 - yes_ask) / yes_ask if won else -size
            else:  # direction == "NO"
                won = not yes_won
                no_ask = (1.0 - mid) + pos["vig_at_entry"] / 2
                pnl = size * (1.0 - no_ask) / no_ask if won else -size

            pnl = round(pnl, 4)
            outcome = "WIN" if won else "LOSS"

            with self._lock, self._file_lock():
                # GG-034: re-read latest committed state under the file lock, then
                # guard against double-resolution — if a concurrent runner already
                # resolved this position, skip it rather than append a second
                # closed record (which would corrupt the realized-P&L ledger).
                self._reload_locked()
                if not any(p["position_id"] == pos["position_id"]
                           for p in self._state["open_positions"]):
                    continue
                # Remove from open, add to closed
                self._state["open_positions"] = [
                    p for p in self._state["open_positions"]
                    if p["position_id"] != pos["position_id"]
                ]
                closed_pos = {**pos, "actual_pts": actual_pts, "outcome": outcome,
                              "pnl": pnl, "resolved_at": _utc_now(), "status": "CLOSED"}
                self._state["closed_positions"].append(closed_pos)
                # GG-034: bankroll_usd + total_realized_pnl are derived from the
                # ledger in _save(). The old imperative credit here added stake+pnl
                # unconditionally, ignoring pool_isolated — the derived bankroll now
                # excludes isolated positions, fixing that latent bug.
                self._accumulate_daily_loss(pnl)
                self._save()

            ok = self._logger.info(
                COMPONENT, "paper_position_resolved",
                payload={
                    "position_id": pos["position_id"],
                    "player_name": pos["player_name"],
                    "direction": direction,
                    "threshold": threshold,
                    "actual_pts": actual_pts,
                    "outcome": outcome,
                    "pnl": pnl,
                    "bankroll_after": self._state["bankroll_usd"],
                },
                session_id=session_id,
            )
            if not ok:
                all_ok = False
            resolved.append(closed_pos)

        return all_ok, resolved

    def settle_position(
        self,
        position_id: str,
        actual_stat: float,
        *,
        stat_label: str = "actual_pts",
        session_id: str | None = None,
    ) -> tuple[bool, dict[str, Any]]:
        """Sport-agnostic position settlement.

        The caller fetches the actual stat from the sport's data source
        (nba_api pts for NBA; MLB Stats API hits for MLB). This method
        handles outcome determination, P&L computation, and ledger mutation
        under the file lock — the same GG-034 invariant as resolve_pending().

        actual_stat: raw outcome value (points, hits, etc.)
        stat_label:  field name stored in the closed record.
                     Default "actual_pts" preserves NBA backward compat.
                     Pass "actual_hits" for MLB.

        Returns (ok, closed_position_record). Empty dict if position_id is
        not found in open_positions (idempotent — already settled is a no-op).
        """
        with self._lock, self._file_lock():
            self._reload_locked()
            pos = next(
                (p for p in self._state["open_positions"]
                 if p["position_id"] == position_id),
                None,
            )
            if pos is None:
                return True, {}

            threshold = pos["kalshi_threshold"]
            direction = pos["direction"]
            size      = float(pos["size_usd"])
            mid       = float(pos["mid_price_at_entry"])
            vig       = float(pos["vig_at_entry"])

            yes_won = actual_stat >= threshold
            if direction == "YES":
                won     = yes_won
                yes_ask = mid + vig / 2
                pnl     = size * (1.0 - yes_ask) / yes_ask if won else -size
            else:  # NO
                won    = not yes_won
                no_ask = (1.0 - mid) + vig / 2
                pnl    = size * (1.0 - no_ask) / no_ask if won else -size

            pnl     = round(pnl, 4)
            outcome = "WIN" if won else "LOSS"

            self._state["open_positions"] = [
                p for p in self._state["open_positions"]
                if p["position_id"] != position_id
            ]
            closed_pos = {
                **pos,
                stat_label: actual_stat,
                "outcome": outcome,
                "pnl": pnl,
                "resolved_at": _utc_now(),
                "status": "CLOSED",
            }
            self._state["closed_positions"].append(closed_pos)
            # GG-034: bankroll derived from ledger in _save(); no imperative scalar.
            self._accumulate_daily_loss(pnl)
            self._save()

        ok = self._logger.info(
            COMPONENT, "paper_position_resolved",
            payload={
                "position_id": position_id,
                "player_name": pos["player_name"],
                "direction": direction,
                "threshold": threshold,
                stat_label: actual_stat,
                "outcome": outcome,
                "pnl": pnl,
                "bankroll_after": self._state["bankroll_usd"],
            },
            session_id=session_id,
        )
        return ok, closed_pos

    def mark_aged_open(
        self,
        position_id: str,
        reason: str = "api_no_result_48h",
        session_id: str | None = None,
    ) -> tuple[bool, dict[str, Any]]:
        """Tag an open position as aged-open in-place (capital remains deployed).

        Called by run_resolve_mlb.py when a position's game_date is >48h old and
        the MLB Stats API still returns None hits.  The position stays in
        open_positions so _ledger_bankroll() continues to count its open_cost —
        capital is NOT credited back.  The tags make the position visible in
        monitoring and audits without distorting the bankroll calculation.

        Idempotent: if aged_open is already True, returns (True, existing_pos)
        without writing again.

        Returns (ok, position_record).  Empty dict if position_id not found.
        """
        with self._lock, self._file_lock():
            self._reload_locked()
            pos = next(
                (p for p in self._state["open_positions"]
                 if p["position_id"] == position_id),
                None,
            )
            if pos is None:
                return True, {}
            if pos.get("aged_open") is True:
                return True, pos

            pos["aged_open"]        = True
            pos["aged_open_reason"] = reason
            pos["aged_open_at"]     = _utc_now()
            self._save()

        ok = self._logger.warning(
            COMPONENT, "paper_position_aged_open",
            payload={
                "position_id": position_id,
                "player_name": pos.get("player_name", ""),
                "game_date":   pos.get("game_date", ""),
                "reason":      reason,
            },
            session_id=session_id,
        )
        return ok, pos

    def summary(self) -> dict[str, Any]:
        """Return a human-readable portfolio summary.

        Two distinct capital metrics:
          realized_drawdown_pct — closed losses as % of initial bankroll.
              This is what C4's kill switch monitors. Zero until a bet resolves.
          deployed_pct — open stakes as % of initial bankroll.
              Money in flight; returns to bankroll when positions resolve.
              NOT a drawdown — it is not permanently lost.
        """
        s = self._state
        n_open     = len(s.get("open_positions", []))
        n_closed   = len(s.get("closed_positions", []))
        n_rejected = len(s.get("rejected_positions", []))  # GG-079/T-234
        wins     = sum(1 for p in s.get("closed_positions", []) if p.get("outcome") == "WIN")
        win_rate = wins / n_closed if n_closed > 0 else None

        initial      = s["initial_bankroll_usd"]
        # GG-034: derive from the ledger, never trust the stored scalar here — the
        # drawdown figure below is what the kill switch acts on.
        realized_pnl = self._ledger_realized_pnl()
        realized_loss = max(0.0, -realized_pnl)
        realized_drawdown = realized_loss / initial

        # Stakes in open positions = initial - current_bankroll - realized_pnl
        # (realized gains would have already been added back to bankroll)
        open_stakes  = initial - s["bankroll_usd"] + realized_pnl
        deployed_pct = max(0.0, open_stakes) / initial

        return {
            "bankroll_usd": s["bankroll_usd"],
            "initial_bankroll_usd": initial,
            "total_realized_pnl": realized_pnl,
            "realized_drawdown_pct": round(realized_drawdown * 100, 2),
            "deployed_pct": round(deployed_pct * 100, 2),
            "open_positions": n_open,
            "closed_positions": n_closed,
            "rejected_positions": n_rejected,
            "win_rate": round(win_rate, 3) if win_rate is not None else None,
        }
