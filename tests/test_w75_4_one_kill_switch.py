"""GG-745/W75.4: one kill switch for every order path (NFR-03).

Every order funnels through KalshiMarketClient.submit_order, which checks
kill_switch_state.halt_reason. These tests drive that real funnel.
"""
from unittest.mock import MagicMock

import pytest

from prediction_market_bot.c5_execution import kill_switch_state as ksw
from prediction_market_bot.c5_execution.kalshi_client import KalshiMarketClient


@pytest.fixture
def logs(tmp_path, monkeypatch):
    monkeypatch.setenv("PMBOT_KILL_SWITCH_DIR", str(tmp_path))
    monkeypatch.setenv("EXPOSURE_GATE_MODE", "log")  # W89.1: these test the kill switch, not the exposure gate
    return tmp_path


@pytest.fixture
def client():
    return KalshiMarketClient(api_key_id="x" * 20)


def _submit(client, band=None):
    return client.submit_order("KXMLBHIT-TEST", "yes", 5.0, 0.5, band=band)


@pytest.mark.unit
@pytest.mark.parametrize("band", [None, "t4_mlb", "t1_mlb", "t1_nba", "shadow", "t4"])
def test_global_flag_halts_every_band_and_unlabeled(logs, client, band):
    (logs / ksw.GLOBAL_FLAG).touch()
    o = _submit(client, band)
    assert o.ok is False and o.status == "halted"
    assert o.error.startswith("kill_switch_halted:kill_switch_flag:kill_switch.flag")


@pytest.mark.unit
def test_band_flag_halts_only_its_band(logs, client):
    ksw.band_flag_path("t4_mlb", logs).touch()
    assert _submit(client, "t4_mlb").status == "halted"
    assert _submit(client, "t1_mlb").status != "halted"
    assert _submit(client, "shadow").status != "halted"
    # unlabeled callers fail closed on any flag
    assert _submit(client, None).status == "halted"


@pytest.mark.unit
@pytest.mark.parametrize("name,halted,spared", [
    ("t4_mlb_kill_switch.flag", "t4_mlb", "shadow"),
    ("t4_kill_switch.flag", "t4", "t4_mlb"),
])
def test_legacy_aliases(logs, name, halted, spared):
    (logs / name).touch()
    assert ksw.halt_reason(band_name=halted, logs_dir=logs)
    assert ksw.halt_reason(band_name=spared, logs_dir=logs) is None


@pytest.mark.unit
def test_unrecognised_flag_fails_closed(logs):
    (logs / "weird_kill_switch.flag").touch()
    assert ksw.halt_reason(band_name="t1_mlb", logs_dir=logs)


@pytest.mark.unit
def test_refusal_within_one_loop_and_resume(logs, client):
    """Canary: flag appears -> very next order refused; removed -> next order proceeds past gate."""
    assert _submit(client, "t4_mlb").status != "halted"
    g = logs / ksw.GLOBAL_FLAG
    g.touch()
    assert _submit(client, "t4_mlb").status == "halted"
    g.unlink()
    assert _submit(client, "t4_mlb").status != "halted"


@pytest.mark.unit
def test_paper_trader_path_halts(logs, tmp_path):
    from prediction_market_bot.c5_execution.paper_trader import PaperTrader
    kc = MagicMock()
    pt = PaperTrader(tmp_path / "p.json", MagicMock(), kalshi_client=kc, kill_band="t1_mlb")
    assert pt._kill_band == "t1_mlb"
    (logs / ksw.GLOBAL_FLAG).touch()
    assert ksw.halt_reason(band_name=pt._kill_band)


@pytest.mark.unit
def test_t4_mlb_kill_switch_armed_reads_shared_state(logs):
    from prediction_market_bot.run_t4_mlb_live import kill_switch_armed
    legacy = logs / "t4_mlb_kill_switch.flag"
    assert kill_switch_armed(legacy) is False
    (logs / ksw.GLOBAL_FLAG).touch()
    assert kill_switch_armed(legacy) is True


@pytest.mark.unit
def test_c7_trip_writes_global_flag_and_drill_does_not(logs):
    from prediction_market_bot.c7_monitoring.monitor import SystemMonitor
    m = SystemMonitor(MagicMock(), "snap", session_id="s")
    m.trigger_kill_switch("drill", _is_drill=True)
    assert not (logs / ksw.GLOBAL_FLAG).exists()
    m2 = SystemMonitor(MagicMock(), "snap", session_id="s")
    m2.trigger_kill_switch("real trip")
    assert (logs / ksw.GLOBAL_FLAG).exists()
    m2.reset_kill_switch("test reset", "tester")
    assert not (logs / ksw.GLOBAL_FLAG).exists()
