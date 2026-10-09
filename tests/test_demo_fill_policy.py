"""W64.2 / ADR-0072: demo fill placement policy + shadow flat stake. Everything here is mocked;
no network, no order. The switch is ON only inside tests that set it."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

_SRC = Path(__file__).parent.parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))
os.environ.setdefault("BOT_ENV", "paper")

from prediction_market_bot.c5_execution import demo_fill_policy as pol
from prediction_market_bot.c5_execution import shadow_flat_stake as sfs
from prediction_market_bot.c5_execution.kalshi_client import KalshiOrder
from prediction_market_bot.c5_execution.paper_trader import PaperTrader


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch, tmp_path):
    for k in (pol.SWITCH_ENV, pol.CANCEL_AFTER_ENV, pol.MAX_GAP_ENV, pol.SHARE_ENV, pol.SEED_ENV,
              sfs.SWITCH_ENV):
        monkeypatch.delenv(k, raising=False)
    monkeypatch.setenv(pol.LOG_ENV, str(tmp_path / "pol.jsonl"))


def _events(tmp_path):
    p = tmp_path / "pol.jsonl"
    return [json.loads(x) for x in p.read_text().splitlines()] if p.exists() else []


def _client(bid=0.40, ask=0.44, ok=True):
    c = MagicMock()
    c.has_signing_key.return_value = True
    c.get_market_book.return_value = (True, {"yes_bid": bid, "yes_ask": ask})
    c.submit_order.return_value = KalshiOrder(ok=ok, order_id="OID1" if ok else "", client_order_id="x",
                                              ticker="T", side="yes", contracts=2, yes_price_cents=40,
                                              actual_cost_usd=0.8, status="resting",
                                              error="" if ok else "boom")
    c.cancel_order.return_value = (True, {})
    return c


def _approval(size=1.0, direction="YES"):
    return {"approval_status": "APPROVED", "approved_size": size, "approved_direction": direction,
            "risk_eval_id": "R", "forecast_id": "F"}


def _open(tmp_path, client, mid=0.42, direction="YES"):
    lg = MagicMock()
    t = PaperTrader(tmp_path / "p.json", lg, kalshi_client=client)
    return t.open_position(approval=_approval(direction=direction), player_name="P", player_id=1,
                           kalshi_ticker="KXMLBHIT-TEST", kalshi_threshold=1, mid_price=mid, vig=0.04,
                           game_date="2026-10-01")


# ---- switch semantics ------------------------------------------------------------------
@pytest.mark.parametrize("val", ["", "1", "true", "on", "BOOK_ANCHOR_CANCEL", "book_anchor"])
def test_only_exact_value_enables(monkeypatch, val):
    monkeypatch.setenv(pol.SWITCH_ENV, val)
    assert not pol.is_enabled()
    monkeypatch.setenv(pol.SWITCH_ENV, pol.SWITCH_ON_VALUE)
    assert pol.is_enabled()


def test_off_is_byte_identical_and_touches_nothing(tmp_path, monkeypatch):
    c = _client()
    ok, pos = _open(tmp_path, c, mid=0.42)
    assert ok and pos
    c.get_market_book.assert_not_called()
    c.cancel_order.assert_not_called()
    kw = c.submit_order.call_args.kwargs
    assert kw["mid_price"] == 0.42                      # the caller's model mid, unchanged
    assert "fill_policy" not in pos
    assert not (tmp_path / "pol.jsonl").exists()


# ---- ON: R2 ----------------------------------------------------------------------------
def test_on_yes_anchors_to_best_bid_and_schedules_cancel(tmp_path, monkeypatch):
    monkeypatch.setenv(pol.SWITCH_ENV, pol.SWITCH_ON_VALUE)
    monkeypatch.setenv(pol.CANCEL_AFTER_ENV, "3600")  # timer never fires in test
    c = _client(bid=0.40, ask=0.44)
    ok, pos = _open(tmp_path, c, mid=0.42, direction="YES")
    assert c.submit_order.call_args.kwargs["mid_price"] == 0.40
    assert pos["fill_policy"]["submit_mid"] == 0.40 and pos["fill_policy"]["model_mid"] == 0.42
    assert any(e["event"] == "cancel_scheduled" and e["order_id"] == "OID1" for e in _events(tmp_path))


def test_on_no_rests_at_own_side_best_bid(tmp_path, monkeypatch):
    monkeypatch.setenv(pol.SWITCH_ENV, pol.SWITCH_ON_VALUE)
    monkeypatch.setenv(pol.CANCEL_AFTER_ENV, "3600")
    c = _client(bid=0.40, ask=0.44)
    _open(tmp_path, c, mid=0.42, direction="NO")
    # YES-frame 0.44 -> NO price 0.56 == 1 - yes_ask: NO best bid
    assert c.submit_order.call_args.kwargs["mid_price"] == 0.44


@pytest.mark.parametrize("bid,ask,reason", [(0.0, 0.44, "one_sided_or_crossed_book"),
                                            (0.40, 0.0, "one_sided_or_crossed_book"),
                                            (0.30, 0.34, "mid_gap_above_threshold")])
def test_on_skips_logged_and_places_nothing(tmp_path, monkeypatch, bid, ask, reason):
    monkeypatch.setenv(pol.SWITCH_ENV, pol.SWITCH_ON_VALUE)
    c = _client(bid=bid, ask=ask)
    ok, pos = _open(tmp_path, c, mid=0.42)
    assert ok and pos == {}
    c.submit_order.assert_not_called()
    assert any(e["event"] == "skip" and e["reason"] == reason for e in _events(tmp_path))


def test_book_read_failure_is_a_skip_not_a_fallback_order(tmp_path, monkeypatch):
    monkeypatch.setenv(pol.SWITCH_ENV, pol.SWITCH_ON_VALUE)
    c = _client()
    c.get_market_book.return_value = (False, {})
    ok, pos = _open(tmp_path, c)
    assert pos == {}
    c.submit_order.assert_not_called()


# ---- R1 --------------------------------------------------------------------------------
def test_cancel_after_n_fires(monkeypatch, tmp_path):
    monkeypatch.setenv(pol.CANCEL_AFTER_ENV, "0.05")
    c = _client()
    t = pol.schedule_cancel(c, "OID9", "POS1", "TK")
    t.join(2)
    c.cancel_order.assert_called_once_with("OID9")
    assert [e["event"] for e in _events(tmp_path)] == ["cancel_scheduled", "cancel_ok"]


def test_cancel_failure_is_logged_not_raised(tmp_path):
    c = _client()
    c.cancel_order.side_effect = RuntimeError("net")
    assert pol.cancel_now(c, "O", "P", "T", "unfilled_after_N") is False
    assert _events(tmp_path)[-1]["event"] == "cancel_failed"


def test_sweep_overdue_finishes_orphaned_cancels(monkeypatch, tmp_path):
    c = _client()
    pol.append_log({"event": "cancel_scheduled", "order_id": "A", "position_id": "P", "ticker": "T",
                    "due_ts": 100.0})
    pol.append_log({"event": "cancel_scheduled", "order_id": "B", "position_id": "P", "ticker": "T",
                    "due_ts": 100.0})
    pol.append_log({"event": "cancel_ok", "order_id": "B"})
    assert pol.sweep_overdue(c, now_ts=200.0) == 1
    c.cancel_order.assert_called_once_with("A")


# ---- assignment ------------------------------------------------------------------------
def test_assignment_deterministic_and_share(monkeypatch):
    monkeypatch.setenv(pol.SHARE_ENV, "0.5")
    ids = [f"POS-{i}" for i in range(2000)]
    a1 = [pol.assigned(i) for i in ids]
    assert a1 == [pol.assigned(i) for i in ids]
    assert 0.45 < sum(a1) / len(a1) < 0.55
    monkeypatch.setenv(pol.SHARE_ENV, "0")
    assert not any(pol.assigned(i) for i in ids)


def test_control_arm_gets_todays_behaviour(tmp_path, monkeypatch):
    monkeypatch.setenv(pol.SWITCH_ENV, pol.SWITCH_ON_VALUE)
    monkeypatch.setenv(pol.SHARE_ENV, "0")
    c = _client()
    ok, pos = _open(tmp_path, c, mid=0.42)
    assert pos and c.submit_order.call_args.kwargs["mid_price"] == 0.42
    c.get_market_book.assert_not_called()


# ---- shadow flat stake -----------------------------------------------------------------
def _row(ey=0.05, en=-0.07, mid=0.42):
    return {"run_id": "RUN1", "market_ticker": "KXNBAGAME-X", "mid": mid,
            "e_net_yes_k007": ey, "e_net_no_k007": en, "p_yes": 0.5}


def test_shadow_off_places_nothing(monkeypatch):
    c = _client()
    assert sfs.maybe_place(_row(), c, lambda e: 1.0) is None
    c.submit_order.assert_not_called()


def test_shadow_requires_both_switches(monkeypatch):
    monkeypatch.setenv(sfs.SWITCH_ENV, "on")           # placement rule still OFF
    c = _client()
    assert sfs.maybe_place(_row(), c, lambda e: 1.0) is None
    c.submit_order.assert_not_called()


def test_shadow_on_places_flat_stake_under_policy_row_untouched(monkeypatch, tmp_path):
    monkeypatch.setenv(sfs.SWITCH_ENV, "on")
    monkeypatch.setenv(pol.SWITCH_ENV, pol.SWITCH_ON_VALUE)
    monkeypatch.setenv(pol.CANCEL_AFTER_ENV, "3600")
    c = _client(bid=0.40, ask=0.44)
    row = _row()
    before = json.dumps(row, sort_keys=True)
    res = sfs.maybe_place(row, c, lambda e: 1.0)
    assert res and res["ok"]
    assert json.dumps(row, sort_keys=True) == before            # shadow row never altered
    kw = c.submit_order.call_args.kwargs
    assert kw["size_usd"] == 1.0 and kw["side"] == "yes" and kw["mid_price"] == 0.40
    assert any(e["event"] == "cancel_scheduled" for e in _events(tmp_path))


def test_shadow_below_gate_or_skip_places_nothing(monkeypatch):
    monkeypatch.setenv(sfs.SWITCH_ENV, "on")
    monkeypatch.setenv(pol.SWITCH_ENV, pol.SWITCH_ON_VALUE)
    c = _client()
    assert sfs.maybe_place(_row(ey=-0.01, en=-0.02), c, lambda e: 1.0) is None
    c2 = _client(bid=0.0, ask=0.44)
    assert sfs.maybe_place(_row(), c2, lambda e: 1.0) is None
    c.submit_order.assert_not_called(); c2.submit_order.assert_not_called()


def test_make_on_row_none_when_off():
    assert sfs.make_on_row(MagicMock()) is None


def test_default_stake_is_adr0050_flat(monkeypatch):
    monkeypatch.setenv(sfs.SWITCH_ENV, "on")
    monkeypatch.setenv(pol.SWITCH_ENV, pol.SWITCH_ON_VALUE)
    monkeypatch.setenv(pol.CANCEL_AFTER_ENV, "3600")
    c = _client(bid=0.40, ask=0.44)
    sfs.maybe_place(_row(), c)
    from prediction_market_bot.run_t4_mlb_live import measurement_stake_and_stratum
    assert c.submit_order.call_args.kwargs["size_usd"] == measurement_stake_and_stratum(0.40)[0]
