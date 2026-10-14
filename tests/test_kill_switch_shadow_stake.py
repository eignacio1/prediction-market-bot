"""GG-667/W72.1: shadow stake path honours the shared kill-switch state."""
from unittest.mock import MagicMock

import pytest

from prediction_market_bot.c5_execution import kill_switch_state as ksw
from prediction_market_bot.c5_execution import shadow_flat_stake as sfs


@pytest.mark.unit
def test_halt_reason_flag_and_clear(tmp_path):
    assert ksw.halt_reason(logs_dir=tmp_path) is None
    (tmp_path / "t4_mlb_kill_switch.flag").touch()
    assert ksw.halt_reason(logs_dir=tmp_path).startswith("kill_switch_flag:")


@pytest.mark.unit
def test_maybe_place_refuses_when_halted(monkeypatch):
    monkeypatch.setattr(sfs, "is_enabled", lambda: True)
    monkeypatch.setattr(sfs, "demo_host_ok", lambda: True)
    monkeypatch.setattr(sfs.ksw, "halt_reason", lambda *a, **k: "kill_switch_flag:x.flag")
    logged = []
    monkeypatch.setattr(sfs.pol, "append_log", logged.append)
    client = MagicMock()
    row = {"run_id": "r", "market_ticker": "T", "mid": 0.5, "e_net_yes_k007": 0.1, "e_net_no_k007": -0.1}
    assert sfs.maybe_place(row, client) is None
    client.submit_order.assert_not_called()
    assert logged[0]["reason"] == "kill_switch_halted"


@pytest.mark.unit
def test_maybe_place_proceeds_past_gate_when_clear(monkeypatch):
    monkeypatch.setattr(sfs, "is_enabled", lambda: True)
    monkeypatch.setattr(sfs, "demo_host_ok", lambda: True)
    monkeypatch.setattr(sfs.ksw, "halt_reason", lambda *a, **k: None)
    logged = []
    monkeypatch.setattr(sfs.pol, "append_log", logged.append)
    monkeypatch.setattr(sfs.pol, "listing_skip_reason", lambda c, t: "not_listed_on_demo")
    row = {"run_id": "r", "market_ticker": "T", "mid": 0.5, "e_net_yes_k007": 0.1, "e_net_no_k007": -0.1}
    assert sfs.maybe_place(row, MagicMock()) is None
    assert logged[0]["reason"] == "not_listed_on_demo"  # got past the kill-switch check
