"""
Tests: C4 Staged Order Store
============================
Covers:
    - stage_order() creates STAGED record
    - get_staged() returns correct order, None if absent
    - mark_fired() transitions STAGED → FIRED
    - mark_cancelled() transitions STAGED → CANCELLED
    - expire_stale() transitions past-valid_until STAGED → EXPIRED
    - get_all_staged() returns only STAGED records
    - summary() counts by status
    - Duplicate market_id: get_staged() returns most recent
    - Validation: invalid direction/strategy/sized_amount raises ValueError
    - Fired/Cancelled orders not returned by get_staged()
    - Audit immutability: no rows deleted between tests
"""

import os
import tempfile
from datetime import datetime, timedelta, timezone

import pytest

from prediction_market_bot.c4_risk_engine.staged_order_store import StagedOrderStore


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def store(tmp_path):
    db = str(tmp_path / "test_staged.db")
    return StagedOrderStore(db)


def _valid_order(market_id="KXNBAPTS-25-LBJ-22", **kwargs):
    defaults = dict(
        market_id=market_id,
        player_id="LeBronJames",
        threshold=22.5,
        direction="YES",
        strategy="A",
        p_t1=0.61,
        p_entry=0.54,
        kelly_fraction=0.05,
        sized_amount_usd=10.0,
        valid_until_iso="2099-01-01T00:00:00+00:00",
    )
    defaults.update(kwargs)
    return defaults


def _past_iso(hours=1):
    dt = datetime.now(timezone.utc) - timedelta(hours=hours)
    return dt.isoformat()


def _future_iso(hours=24):
    dt = datetime.now(timezone.utc) + timedelta(hours=hours)
    return dt.isoformat()


# ---------------------------------------------------------------------------
# stage_order
# ---------------------------------------------------------------------------

class TestStageOrder:
    def test_returns_order_id_string(self, store):
        oid = store.stage_order(**_valid_order())
        assert isinstance(oid, str)
        assert len(oid) == 36  # uuid4

    def test_staged_status(self, store):
        oid = store.stage_order(**_valid_order())
        record = store.get_by_order_id(oid)
        assert record is not None
        assert record["status"] == "STAGED"

    def test_all_fields_stored(self, store):
        oid = store.stage_order(**_valid_order(notes="test note"))
        rec = store.get_by_order_id(oid)
        assert rec["market_id"] == "KXNBAPTS-25-LBJ-22"
        assert rec["player_id"] == "LeBronJames"
        assert rec["threshold"] == 22.5
        assert rec["direction"] == "YES"
        assert rec["strategy"] == "A"
        assert abs(rec["p_t1"] - 0.61) < 1e-9
        assert abs(rec["kelly_fraction"] - 0.05) < 1e-9
        assert abs(rec["sized_amount_usd"] - 10.0) < 1e-9
        assert rec["notes"] == "test note"

    def test_p_entry_nullable(self, store):
        kw = _valid_order()
        del kw["p_entry"]
        oid = store.stage_order(**kw)
        rec = store.get_by_order_id(oid)
        assert rec["p_entry"] is None

    def test_invalid_direction_raises(self, store):
        with pytest.raises(ValueError, match="direction"):
            store.stage_order(**_valid_order(direction="MAYBE"))

    def test_invalid_strategy_raises(self, store):
        with pytest.raises(ValueError, match="strategy"):
            store.stage_order(**_valid_order(strategy="Z"))

    def test_invalid_sized_amount_raises(self, store):
        with pytest.raises(ValueError, match="sized_amount_usd"):
            store.stage_order(**_valid_order(sized_amount_usd=-5.0))

    def test_invalid_kelly_fraction_raises(self, store):
        with pytest.raises(ValueError, match="kelly_fraction"):
            store.stage_order(**_valid_order(kelly_fraction=0.0))

    def test_multiple_orders_different_ids(self, store):
        oid1 = store.stage_order(**_valid_order(market_id="MKT-001"))
        oid2 = store.stage_order(**_valid_order(market_id="MKT-002"))
        assert oid1 != oid2


# ---------------------------------------------------------------------------
# get_staged
# ---------------------------------------------------------------------------

class TestGetStaged:
    def test_returns_none_when_absent(self, store):
        assert store.get_staged("KXNBAPTS-25-LBJ-99") is None

    def test_returns_order_when_staged(self, store):
        store.stage_order(**_valid_order(market_id="MKT-A"))
        result = store.get_staged("MKT-A")
        assert result is not None
        assert result["market_id"] == "MKT-A"
        assert result["status"] == "STAGED"

    def test_returns_most_recent_when_multiple(self, store):
        store.stage_order(**_valid_order(market_id="MKT-B", p_t1=0.50, notes="first"))
        store.stage_order(**_valid_order(market_id="MKT-B", p_t1=0.60, notes="second"))
        result = store.get_staged("MKT-B")
        assert result["notes"] == "second"

    def test_returns_none_after_fired(self, store):
        oid = store.stage_order(**_valid_order(market_id="MKT-C"))
        store.mark_fired(oid)
        assert store.get_staged("MKT-C") is None

    def test_returns_none_after_cancelled(self, store):
        oid = store.stage_order(**_valid_order(market_id="MKT-D"))
        store.mark_cancelled(oid, reason="test")
        assert store.get_staged("MKT-D") is None

    def test_returns_none_after_expired(self, store):
        store.stage_order(**_valid_order(
            market_id="MKT-E",
            valid_until_iso=_past_iso(hours=2),
        ))
        store.expire_stale()
        assert store.get_staged("MKT-E") is None


# ---------------------------------------------------------------------------
# mark_fired
# ---------------------------------------------------------------------------

class TestMarkFired:
    def test_transitions_to_fired(self, store):
        oid = store.stage_order(**_valid_order())
        store.mark_fired(oid)
        rec = store.get_by_order_id(oid)
        assert rec["status"] == "FIRED"
        assert rec["fired_at"] is not None

    def test_custom_fired_at(self, store):
        oid = store.stage_order(**_valid_order())
        fired_at = "2026-06-03T21:00:00+00:00"
        store.mark_fired(oid, fired_at_iso=fired_at)
        rec = store.get_by_order_id(oid)
        assert rec["fired_at"] == fired_at

    def test_idempotent_on_already_fired(self, store):
        oid = store.stage_order(**_valid_order())
        store.mark_fired(oid)
        store.mark_fired(oid)  # second call — should not raise
        rec = store.get_by_order_id(oid)
        assert rec["status"] == "FIRED"


# ---------------------------------------------------------------------------
# mark_cancelled
# ---------------------------------------------------------------------------

class TestMarkCancelled:
    def test_transitions_to_cancelled(self, store):
        oid = store.stage_order(**_valid_order())
        store.mark_cancelled(oid, reason="kill switch")
        rec = store.get_by_order_id(oid)
        assert rec["status"] == "CANCELLED"
        assert rec["notes"] == "kill switch"

    def test_no_effect_on_already_fired(self, store):
        oid = store.stage_order(**_valid_order())
        store.mark_fired(oid)
        store.mark_cancelled(oid)
        rec = store.get_by_order_id(oid)
        assert rec["status"] == "FIRED"  # not changed


# ---------------------------------------------------------------------------
# expire_stale
# ---------------------------------------------------------------------------

class TestExpireStale:
    def test_expires_past_orders(self, store):
        store.stage_order(**_valid_order(
            market_id="PAST", valid_until_iso=_past_iso(hours=1)
        ))
        count = store.expire_stale()
        assert count == 1
        assert store.get_staged("PAST") is None

    def test_does_not_expire_future_orders(self, store):
        store.stage_order(**_valid_order(
            market_id="FUTURE", valid_until_iso=_future_iso(hours=24)
        ))
        count = store.expire_stale()
        assert count == 0
        assert store.get_staged("FUTURE") is not None

    def test_returns_count_of_expired(self, store):
        for i in range(3):
            store.stage_order(**_valid_order(
                market_id=f"PAST-{i}",
                valid_until_iso=_past_iso(hours=i + 1),
            ))
        count = store.expire_stale()
        assert count == 3

    def test_expired_status_in_db(self, store):
        oid = store.stage_order(**_valid_order(
            valid_until_iso=_past_iso(hours=1)
        ))
        store.expire_stale()
        rec = store.get_by_order_id(oid)
        assert rec["status"] == "EXPIRED"

    def test_custom_cutoff(self, store):
        future = _future_iso(hours=12)
        store.stage_order(**_valid_order(market_id="FUTURE2", valid_until_iso=future))
        far_future_cutoff = _future_iso(hours=24)
        count = store.expire_stale(cutoff_iso=far_future_cutoff)
        assert count == 1  # future2 is now past the far_future cutoff


# ---------------------------------------------------------------------------
# get_all_staged
# ---------------------------------------------------------------------------

class TestGetAllStaged:
    def test_empty_when_none(self, store):
        assert store.get_all_staged() == []

    def test_returns_only_staged(self, store):
        oid1 = store.stage_order(**_valid_order(market_id="S1"))
        oid2 = store.stage_order(**_valid_order(market_id="S2"))
        store.mark_fired(oid1)
        results = store.get_all_staged()
        assert len(results) == 1
        assert results[0]["market_id"] == "S2"

    def test_returns_all_staged_count(self, store):
        for i in range(5):
            store.stage_order(**_valid_order(market_id=f"MKT-{i}"))
        assert len(store.get_all_staged()) == 5


# ---------------------------------------------------------------------------
# summary
# ---------------------------------------------------------------------------

class TestSummary:
    def test_empty_summary(self, store):
        assert store.summary() == {}

    def test_counts_by_status(self, store):
        oid1 = store.stage_order(**_valid_order(market_id="S1"))
        oid2 = store.stage_order(**_valid_order(market_id="S2"))
        oid3 = store.stage_order(**_valid_order(market_id="S3"))
        store.mark_fired(oid1)
        store.mark_cancelled(oid2)
        s = store.summary()
        assert s.get("STAGED") == 1
        assert s.get("FIRED") == 1
        assert s.get("CANCELLED") == 1

    def test_no_deletes_between_ops(self, store):
        oid = store.stage_order(**_valid_order())
        store.mark_fired(oid)
        rec = store.get_by_order_id(oid)
        assert rec is not None  # row still exists after state transition
