"""
Tests: T-174 — Realized-P&L Reconciliation + Blind-Drawdown Fix (GG-034)
========================================================================
Root cause being fixed:
  `total_realized_pnl` was an in-memory scalar incremented under an in-process
  lock only, while four runner processes did load→mutate→save on the same JSON.
  Concurrent writers clobbered each other's increments, so the scalar drifted
  from the append-only closed-position ledger. The drawdown kill switch, C7
  monitor, C8 dashboard, and G6 gate all read the corrupted scalar — leaving a
  true −25% drawdown invisible to a 20% kill switch.

Invariants asserted here:
  - Realized P&L is DERIVED from the ledger (Σ pnl + Σ exit_pnl), never an
    independent accumulator.
  - Mixed resolve + exit positions are both counted (resolve→`pnl`, exit→`exit_pnl`).
  - A corrupted scalar on disk is detected and corrected on load (reconcile()).
  - reconcile(strict=True) raises on drift (for invariant guards/asserts).
  - The GG-034 production scenario (stored ≈ breakeven, ledger ≈ −25%) is caught
    and the drawdown surfaced to summary() reflects the ledger, not the scalar.
  - A clean book produces zero drift and no desync log.
"""

import json
from pathlib import Path

import pytest

from prediction_market_bot.c5_execution.paper_trader import (
    PaperTrader,
    PortfolioReconciliationError,
    _position_pnl,
    RECONCILE_TOLERANCE_USD,
)
from prediction_market_bot.c6_audit_logger.audit_logger import AuditLogger


# ---------------------------------------------------------------------------
# Fixtures / helpers
# ---------------------------------------------------------------------------

@pytest.fixture
def tmp_portfolio(tmp_path):
    return tmp_path / "paper_portfolio_test.json"


@pytest.fixture
def logger(tmp_path):
    return AuditLogger(log_path=tmp_path / "audit_test.jsonl")


def _make_trader(tmp_portfolio, logger):
    return PaperTrader(portfolio_path=tmp_portfolio, logger=logger)


def _resolved(position_id: str, pnl: float) -> dict:
    return {"position_id": position_id, "status": "CLOSED", "outcome": "WIN" if pnl >= 0 else "LOSS", "pnl": pnl}


def _exited(position_id: str, exit_pnl: float) -> dict:
    return {"position_id": position_id, "status": "EXITED", "exit_pnl": exit_pnl}


def _write_book(path: Path, *, stored_pnl: float, closed: list[dict], initial: float = 1000.0, bankroll: float = 1000.0):
    """Write a portfolio JSON with an arbitrary (possibly corrupt) stored scalar."""
    state = {
        "bankroll_usd": bankroll,
        "initial_bankroll_usd": initial,
        "total_realized_pnl": stored_pnl,
        "current_daily_loss": 0.0,
        "daily_loss_date": "2026-06-14",
        "open_positions": [],
        "closed_positions": closed,
        "created_at": "2026-06-14T00:00:00.000Z",
        "last_updated": "2026-06-14T00:00:00.000Z",
    }
    path.write_text(json.dumps(state, indent=2))


def _read_desync_events(logger_path: Path) -> list[dict]:
    if not logger_path.exists():
        return []
    out = []
    for line in logger_path.read_text().splitlines():
        if not line.strip():
            continue
        rec = json.loads(line)
        if rec.get("event_type") == "portfolio_pnl_desync":
            out.append(rec)
    return out


# ---------------------------------------------------------------------------
# _position_pnl — both keys
# ---------------------------------------------------------------------------

def test_position_pnl_covers_resolve_and_exit_keys():
    assert _position_pnl(_resolved("A", -12.5)) == pytest.approx(-12.5)
    assert _position_pnl(_exited("B", 3.25)) == pytest.approx(3.25)
    assert _position_pnl({"position_id": "C"}) == 0.0


# ---------------------------------------------------------------------------
# Derived realized P&L on a clean book
# ---------------------------------------------------------------------------

def test_clean_book_has_zero_drift_and_no_log(tmp_portfolio, logger, tmp_path):
    closed = [_resolved("A", -10.0), _resolved("B", 4.0), _exited("C", -2.0)]
    _write_book(tmp_portfolio, stored_pnl=-8.0, closed=closed)  # stored == ledger
    trader = _make_trader(tmp_portfolio, logger)
    ok, report = trader.reconcile()
    assert ok
    assert report["drift_usd"] == pytest.approx(0.0, abs=RECONCILE_TOLERANCE_USD)
    assert _read_desync_events(tmp_path / "audit_test.jsonl") == []


def test_derived_pnl_counts_both_resolve_and_exit(tmp_portfolio, logger):
    closed = [_resolved("A", -10.0), _resolved("B", 4.0), _exited("C", -2.0), _exited("D", 1.5)]
    _write_book(tmp_portfolio, stored_pnl=-6.5, closed=closed)
    trader = _make_trader(tmp_portfolio, logger)
    assert trader._ledger_realized_pnl() == pytest.approx(-6.5)


# ---------------------------------------------------------------------------
# Drift detection + correction on load
# ---------------------------------------------------------------------------

def test_corrupt_scalar_detected_and_corrected_on_load(tmp_portfolio, logger, tmp_path):
    closed = [_resolved("A", -100.0), _resolved("B", -100.0), _resolved("C", -51.21)]
    # Ledger truth = -251.21; corrupted stored scalar = -8.46 (the live VPS book).
    _write_book(tmp_portfolio, stored_pnl=-8.46, closed=closed)
    trader = _make_trader(tmp_portfolio, logger)  # __init__ calls reconcile()
    # In-memory scalar adopted the ledger value...
    assert trader._state["total_realized_pnl"] == pytest.approx(-251.21)
    # ...and the desync was logged loudly.
    events = _read_desync_events(tmp_path / "audit_test.jsonl")
    assert len(events) == 1
    payload = events[0]["payload"]
    assert payload["stored_total_realized_pnl"] == pytest.approx(-8.46)
    assert payload["ledger_total_realized_pnl"] == pytest.approx(-251.21)


def test_reconcile_does_not_write_file_on_load(tmp_portfolio, logger):
    closed = [_resolved("A", -251.21)]
    _write_book(tmp_portfolio, stored_pnl=-8.46, closed=closed)
    before = tmp_portfolio.read_text()
    _make_trader(tmp_portfolio, logger)  # reconcile() in __init__ must not persist
    assert tmp_portfolio.read_text() == before


def test_strict_reconcile_raises_on_drift(tmp_portfolio, logger):
    closed = [_resolved("A", -251.21)]
    _write_book(tmp_portfolio, stored_pnl=-8.46, closed=closed)
    trader = _make_trader(tmp_portfolio, logger)
    # Re-corrupt in memory to exercise strict mode independent of load correction.
    trader._state["total_realized_pnl"] = -8.46
    with pytest.raises(PortfolioReconciliationError):
        trader.reconcile(strict=True)


# ---------------------------------------------------------------------------
# Blind-drawdown scenario (the actual GG-034 impact)
# ---------------------------------------------------------------------------

def test_summary_drawdown_reflects_ledger_not_scalar(tmp_portfolio, logger):
    # Stored scalar says ~breakeven; ledger says −$251.21 on $1000 = 25.1% drawdown.
    closed = [_resolved("A", -125.60), _resolved("B", -125.61)]
    _write_book(tmp_portfolio, stored_pnl=-8.46, closed=closed, bankroll=130.62)
    trader = _make_trader(tmp_portfolio, logger)
    summ = trader.summary()
    assert summ["total_realized_pnl"] == pytest.approx(-251.21)
    # 251.21 / 1000 = 25.12% — past the 20% kill-switch threshold the scalar hid.
    assert summ["realized_drawdown_pct"] == pytest.approx(25.12, abs=0.01)
    assert summ["realized_drawdown_pct"] >= 20.0


# ---------------------------------------------------------------------------
# Correction persists only on next real mutation's _save()
# ---------------------------------------------------------------------------

def test_save_persists_derived_value(tmp_portfolio, logger):
    closed = [_resolved("A", -251.21)]
    _write_book(tmp_portfolio, stored_pnl=-8.46, closed=closed)
    trader = _make_trader(tmp_portfolio, logger)
    assert trader._save()
    on_disk = json.loads(tmp_portfolio.read_text())
    assert on_disk["total_realized_pnl"] == pytest.approx(-251.21)


# ---------------------------------------------------------------------------
# Bankroll is derived from the ledger too (GG-034 — second scalar)
# ---------------------------------------------------------------------------

def _approval(size: float, direction: str = "YES") -> dict:
    return {
        "approval_status": "APPROVED",
        "approved_size": size,
        "approved_direction": direction,
        "risk_eval_id": "RISK-T174",
        "forecast_id": "FCST-T174",
    }


def _open(trader, size, *, pool_isolated=False, direction="YES", game_date="2099-01-01"):
    return trader.open_position(
        approval=_approval(size, direction),
        player_name="Test", player_id=999,
        kalshi_ticker="KXNBAPTS-T174", kalshi_threshold=20,
        mid_price=0.45, vig=0.02, game_date=game_date,
        pool_isolated=pool_isolated,
    )


def test_bankroll_derived_from_ledger_on_open(tmp_portfolio, logger):
    trader = _make_trader(tmp_portfolio, logger)
    _open(trader, 50.0)
    _open(trader, 30.0)
    on_disk = json.loads(tmp_portfolio.read_text())
    # 1000 initial − 80 in open non-isolated stakes.
    assert on_disk["bankroll_usd"] == pytest.approx(920.0)
    assert trader._ledger_bankroll() == pytest.approx(920.0)


def test_pool_isolated_open_does_not_touch_bankroll(tmp_portfolio, logger):
    trader = _make_trader(tmp_portfolio, logger)
    _open(trader, 50.0, pool_isolated=True)
    on_disk = json.loads(tmp_portfolio.read_text())
    assert on_disk["bankroll_usd"] == pytest.approx(1000.0)


def test_derived_bankroll_excludes_isolated_closed_positions(tmp_portfolio, logger):
    # The latent resolve_pending bug: the old imperative credit added stake+pnl
    # to bankroll for EVERY resolved position, ignoring pool_isolated. The derived
    # bankroll must exclude isolated closed positions entirely.
    closed = [
        {"position_id": "ISO", "status": "CLOSED", "outcome": "WIN",
         "pnl": 40.0, "size_usd": 100.0, "pool_isolated": True},
        _resolved("MAIN", -25.0),
    ]
    _write_book(tmp_portfolio, stored_pnl=15.0, closed=closed)
    trader = _make_trader(tmp_portfolio, logger)
    # Bankroll reflects only the −25 non-isolated realized loss; the isolated +40
    # never flows into the main bankroll.
    assert trader._ledger_bankroll() == pytest.approx(975.0)
    # Realized P&L scalar still counts BOTH (it is total realized, not main-cash).
    assert trader._ledger_realized_pnl() == pytest.approx(15.0)


# ---------------------------------------------------------------------------
# Cross-process safety: reload-under-lock prevents clobbering (GG-034)
# ---------------------------------------------------------------------------

def test_concurrent_traders_do_not_clobber_appends(tmp_portfolio, logger):
    # Two PaperTrader instances on the SAME file model two runner processes.
    # Before the fix, B's load→mutate→save would overwrite A's appended position
    # (last-write-wins). With _file_lock + _reload_locked, B re-reads A's commit
    # before appending, so both positions survive.
    a = _make_trader(tmp_portfolio, logger)
    b = _make_trader(tmp_portfolio, logger)
    _open(a, 50.0)
    _open(b, 30.0)  # b's in-memory state predates a's append; reload must recover it
    on_disk = json.loads(tmp_portfolio.read_text())
    assert len(on_disk["open_positions"]) == 2
    assert on_disk["bankroll_usd"] == pytest.approx(920.0)


def test_reload_recovers_external_closed_positions(tmp_portfolio, logger):
    # A long-lived trader's in-memory ledger is stale; another process appended a
    # closed loss. The next mutation must reload it, not erase it.
    trader = _make_trader(tmp_portfolio, logger)
    _open(trader, 40.0)  # disk now has 1 open
    # Simulate an external process resolving a *different* position into the book.
    external = json.loads(tmp_portfolio.read_text())
    external["closed_positions"].append(_resolved("EXT", -60.0))
    tmp_portfolio.write_text(json.dumps(external, indent=2))
    # Trader (unaware) opens another bet; reload-under-lock must preserve EXT.
    _open(trader, 20.0)
    on_disk = json.loads(tmp_portfolio.read_text())
    assert any(p["position_id"] == "EXT" for p in on_disk["closed_positions"])
    assert len(on_disk["open_positions"]) == 2
    # Bankroll: 1000 − 60 realized loss − 60 open stakes = 880.
    assert on_disk["bankroll_usd"] == pytest.approx(880.0)
