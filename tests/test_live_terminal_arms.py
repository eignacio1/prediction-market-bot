"""Live Terminal: the router's arm per row, arm-driven demo orders and D6 (SW-9, 2026-11-12; ADR-0077)."""
import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("wd_arms", ROOT / "scripts" / "web_dashboard.py")
wd = importlib.util.module_from_spec(spec)
spec.loader.exec_module(wd)


@pytest.mark.unit
def test_router_arm_reads_nested_router_fields():
    assert wd._router_arm({"router": {"arm": "ride", "branch": "RIDE"}}) == "RIDE"
    assert wd._router_arm({"router": {"branch": "NO_BET"}}) == "NO_BET"
    assert wd._router_arm({}) is None


@pytest.mark.unit
def test_arm_orders_counts_orders_would_and_skips(tmp_path):
    log = tmp_path / "arm_orders" / "orders.jsonl"
    log.parent.mkdir()
    rows = [{"ts": "2026-11-12T01:00:00Z", "event": "arm_order", "ok": True, "arm": "RIDE", "sport": "NHL"},
            {"ts": "2026-11-12T01:01:00Z", "event": "arm_order", "ok": False, "arm": "RIDE", "sport": "NHL"},
            {"ts": "2026-11-12T01:02:00Z", "event": "arm_would_order", "arm": "MODEL_FADE", "sport": "NBA"},
            {"ts": "2026-11-12T01:03:00Z", "event": "arm_skip", "reason": "no_bet", "arm": "NO_BET", "sport": "NFL"}]
    log.write_text("".join(json.dumps(r) + "\n" for r in rows))
    out = wd._arm_orders(tmp_path)
    assert len(out["rows"]) == 4
    assert out["per_arm"]["Ride"] == {"orders": 1, "would": 0, "skips": 0, "refused": 1}
    assert out["per_arm"]["Fade"]["would"] == 1
    assert out["per_arm"]["No bet"]["skips"] == 1
    assert out["mode"] in (None, "off", "dry", "on")


@pytest.mark.unit
def test_arm_orders_absent_log_is_empty(tmp_path):
    out = wd._arm_orders(tmp_path)
    assert out["rows"] == [] and out["per_arm"] == {}


@pytest.mark.unit
def test_d6_reports_seven_layers_per_sport():
    x = wd._d6()
    assert len(x["layers"]) == 7
    assert x["registered"] >= x["wired"] >= 0
    for v in x["by_sport"].values():
        assert len(v["per_layer"]) == 7


@pytest.mark.unit
def test_page_says_tests_close_not_cells():
    h = (ROOT / "Live Terminal.html").read_text(encoding="utf-8")
    assert "a losing look closes only its test" in h
    assert "fade arm closed (routed)" not in h
    assert h == wd._HTML
