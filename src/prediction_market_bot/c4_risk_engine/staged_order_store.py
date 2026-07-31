"""
C4: Staged Order Store — T1→T4 Pre-Staging Handoff Layer
=========================================================
Component:    C4 (Risk Engine) — pre-staging sub-module
Phase active: SKELETON — Phase 7+ dark-period infrastructure.
              Usable now (paper trading). Not wired to T4 event loop until
              DS-02 is active (Phase 8+).
Upstream:     C3 forecast + C4 Kelly sizing (T1/T2 cron)
Downstream:   run_t4_inplay.py (PIPE-07); run_t3_pretip.py (T3 verification)
ADR refs:     ADR-0006 (pipeline + Kelly + kill switch risk framework);
              Phase 8 infrastructure ADR (required before T4 live activation).

What this does:
    The expensive work (inference, sizing) happens at T1/T2. At T4 execution
    time, the system needs to make a decision in <5s with no API calls.

    StagedOrderStore bridges the gap. At T1/T2, C4-approved orders are
    written here with an expiry time. At T4, the event loop reads the staged
    order by market_id in <1ms. T3 verification scans for expired or
    invalidated orders before the game starts and marks them CANCELLED.

    This is the pre-staging principle: detection band ≠ execution band.
    T1/T2 computes. T3 verifies. T4 fires (zero API calls at execution).

Schema:
    staged_orders table — one row per staged order:
        order_id        TEXT PRIMARY KEY (uuid4)
        market_id       TEXT NOT NULL    (kalshi_ticker)
        player_id       TEXT NOT NULL
        threshold       REAL NOT NULL
        direction       TEXT NOT NULL    ("YES" | "NO")
        strategy        TEXT NOT NULL    ("A" | "C" | "E")
        p_t1            REAL NOT NULL    (T1 model probability)
        p_entry         REAL             (Kalshi price at staging time; nullable)
        kelly_fraction  REAL NOT NULL
        sized_amount_usd REAL NOT NULL   (C4-approved bet size in USD)
        staged_at       TEXT NOT NULL    (ISO 8601 UTC)
        valid_until     TEXT NOT NULL    (ISO 8601 UTC; T4 rejects after this)
        status          TEXT NOT NULL    ("STAGED" | "FIRED" | "EXPIRED" | "CANCELLED")
        fired_at        TEXT             (ISO 8601 UTC; NULL until fired)
        notes           TEXT             (free text; audit trail)

Thread safety:
    SQLite WAL mode. Multiple readers; single writer per table.
    The T4 event loop reads; the T1/T2 cron writes. No concurrent writes.

Governance:
    All staged orders are append-only from a C6 audit perspective.
    Marking FIRED/EXPIRED/CANCELLED is a status update, not a delete.
    Do not DELETE rows. The store is a permanent audit log.
"""

from __future__ import annotations

import sqlite3
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Generator, Optional


# ---------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------

_DDL = """
CREATE TABLE IF NOT EXISTS staged_orders (
    order_id         TEXT PRIMARY KEY,
    market_id        TEXT NOT NULL,
    player_id        TEXT NOT NULL,
    threshold        REAL NOT NULL,
    direction        TEXT NOT NULL CHECK(direction IN ('YES','NO')),
    strategy         TEXT NOT NULL CHECK(strategy IN ('A','C','E')),
    p_t1             REAL NOT NULL,
    p_entry          REAL,
    kelly_fraction   REAL NOT NULL,
    sized_amount_usd REAL NOT NULL,
    staged_at        TEXT NOT NULL,
    valid_until      TEXT NOT NULL,
    status           TEXT NOT NULL DEFAULT 'STAGED'
                     CHECK(status IN ('STAGED','FIRED','EXPIRED','CANCELLED')),
    fired_at         TEXT,
    notes            TEXT
);
CREATE INDEX IF NOT EXISTS idx_staged_orders_market_status
    ON staged_orders(market_id, status);
CREATE INDEX IF NOT EXISTS idx_staged_orders_status
    ON staged_orders(status);
"""

_VALID_STATUSES = {"STAGED", "FIRED", "EXPIRED", "CANCELLED"}
_VALID_DIRECTIONS = {"YES", "NO"}
_VALID_STRATEGIES = {"A", "C", "E"}


# ---------------------------------------------------------------------------
# Store
# ---------------------------------------------------------------------------

class StagedOrderStore:
    """
    SQLite-backed store for C4-approved orders awaiting T4/T5 execution.

    Usage:
        store = StagedOrderStore()         # uses default path logs/staged_orders.db
        store = StagedOrderStore("/tmp/test.db")  # override for testing

        order_id = store.stage_order(
            market_id="KXNBAPTS-25-LBJ-22",
            player_id="LeBronJames",
            threshold=22.5,
            direction="YES",
            strategy="A",
            p_t1=0.61,
            p_entry=0.54,
            kelly_fraction=0.05,
            sized_amount_usd=10.0,
            valid_until_iso="2026-06-03T23:59:00Z",
        )

        order = store.get_staged("KXNBAPTS-25-LBJ-22")  # None if not STAGED
        store.mark_fired(order_id)
        store.expire_stale()  # call at T3 verification time
    """

    def __init__(self, db_path: Optional[str] = None) -> None:
        if db_path is None:
            default = Path(__file__).resolve().parents[4] / "logs" / "staged_orders.db"
            db_path = str(default)
        self._db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.executescript(_DDL)

    @contextmanager
    def _connect(self) -> Generator[sqlite3.Connection, None, None]:
        conn = sqlite3.connect(self._db_path, timeout=5.0)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    @staticmethod
    def _now_iso() -> str:
        return datetime.now(timezone.utc).isoformat()

    # ------------------------------------------------------------------
    # Write operations
    # ------------------------------------------------------------------

    def stage_order(
        self,
        *,
        market_id: str,
        player_id: str,
        threshold: float,
        direction: str,
        strategy: str,
        p_t1: float,
        kelly_fraction: float,
        sized_amount_usd: float,
        valid_until_iso: str,
        p_entry: Optional[float] = None,
        notes: Optional[str] = None,
    ) -> str:
        """
        Write a C4-approved order to the store with STAGED status.

        Returns order_id (uuid4 string).
        Raises ValueError on invalid direction/strategy.
        """
        if direction not in _VALID_DIRECTIONS:
            raise ValueError(f"direction must be one of {_VALID_DIRECTIONS}")
        if strategy not in _VALID_STRATEGIES:
            raise ValueError(f"strategy must be one of {_VALID_STRATEGIES}")
        if sized_amount_usd <= 0:
            raise ValueError("sized_amount_usd must be positive")
        if not (0.0 <= kelly_fraction <= 1.0):
            raise ValueError("kelly_fraction must be in [0, 1]")

        order_id = str(uuid.uuid4())
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO staged_orders
                    (order_id, market_id, player_id, threshold, direction,
                     strategy, p_t1, p_entry, kelly_fraction, sized_amount_usd,
                     staged_at, valid_until, status, notes)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,'STAGED',?)
                """,
                (
                    order_id, market_id, player_id, threshold, direction,
                    strategy, p_t1, p_entry, kelly_fraction, sized_amount_usd,
                    self._now_iso(), valid_until_iso, notes,
                ),
            )
        return order_id

    def mark_fired(self, order_id: str, fired_at_iso: Optional[str] = None) -> None:
        """Mark a STAGED order as FIRED (executed). Idempotent if already FIRED."""
        fired_at = fired_at_iso or self._now_iso()
        with self._connect() as conn:
            conn.execute(
                "UPDATE staged_orders SET status='FIRED', fired_at=? WHERE order_id=? AND status='STAGED'",
                (fired_at, order_id),
            )

    def mark_cancelled(self, order_id: str, reason: Optional[str] = None) -> None:
        """Mark a STAGED order as CANCELLED (T3 invalidation or kill switch)."""
        with self._connect() as conn:
            conn.execute(
                "UPDATE staged_orders SET status='CANCELLED', notes=? WHERE order_id=? AND status='STAGED'",
                (reason, order_id),
            )

    def expire_stale(self, cutoff_iso: Optional[str] = None) -> int:
        """
        Mark all STAGED orders whose valid_until has passed as EXPIRED.
        Returns count of orders expired.
        Call at T3 verification time (pre-game) and at start of each T4 loop.
        """
        cutoff = cutoff_iso or self._now_iso()
        with self._connect() as conn:
            cur = conn.execute(
                "UPDATE staged_orders SET status='EXPIRED' WHERE status='STAGED' AND valid_until < ?",
                (cutoff,),
            )
            return cur.rowcount

    # ------------------------------------------------------------------
    # Read operations
    # ------------------------------------------------------------------

    def get_staged(self, market_id: str) -> Optional[dict]:
        """
        Return the most recently staged STAGED order for market_id, or None.

        T4 event loop calls this on every game-state event for fast lookup.
        Returns a plain dict (not sqlite3.Row) for downstream convenience.
        """
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT * FROM staged_orders
                WHERE market_id=? AND status='STAGED'
                ORDER BY staged_at DESC
                LIMIT 1
                """,
                (market_id,),
            ).fetchone()
        return dict(row) if row else None

    def get_all_staged(self) -> list[dict]:
        """Return all STAGED orders. Used by T3 verification scan."""
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM staged_orders WHERE status='STAGED' ORDER BY staged_at"
            ).fetchall()
        return [dict(r) for r in rows]

    def get_by_order_id(self, order_id: str) -> Optional[dict]:
        """Return a single order by order_id regardless of status."""
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM staged_orders WHERE order_id=?", (order_id,)
            ).fetchone()
        return dict(row) if row else None

    def summary(self) -> dict:
        """Return counts by status. Useful for C8 dashboard and audit."""
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT status, COUNT(*) as n FROM staged_orders GROUP BY status"
            ).fetchall()
        return {row["status"]: row["n"] for row in rows}
