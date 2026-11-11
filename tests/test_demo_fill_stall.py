"""W109.6 Part C: demo-fill stall alarm."""
import json
from datetime import datetime, timedelta, timezone

from prediction_market_bot.pregame_shadow import demo_fill_stall as ds

NOW = datetime(2026, 11, 11, 1, 0, tzinfo=timezone.utc)


def _rig(tmp_path, order_age_h=None, arm_age_h=None, override=False):
    (tmp_path / "logs").mkdir()
    (tmp_path / "deploy").mkdir()
    led = tmp_path / "exp_output" / "PREGAME_SHADOW"
    led.mkdir(parents=True)
    pol = tmp_path / "logs" / "demo_fill_policy.jsonl"
    rows = [{"ts": (NOW - timedelta(days=9)).isoformat(), "event": "shadow_order"}]
    if order_age_h is not None:
        rows.append({"ts": (NOW - timedelta(hours=order_age_h)).isoformat(), "event": "shadow_order"})
    pol.write_text("\n".join(json.dumps(r) for r in rows))
    if arm_age_h is not None:
        (led / "NBA_NBA_MONEYLINE_T1.jsonl").write_text(json.dumps({"ts_utc": (NOW - timedelta(hours=arm_age_h)).isoformat()}))
    if override:
        (tmp_path / "deploy" / "demo_fill.override.env").write_text(
            "# TURNED OFF by demo_fill_forward_report (treatment_markout_30m_worse_than_control). Delete this file.\n"
            "DEMO_FILL_PLACEMENT_RULE=off\nSHADOW_FLAT_STAKE=off\n")
    return tmp_path


def test_stalled_when_no_orders_but_arms_log_and_names_the_override(tmp_path):
    r = ds.stall(_rig(tmp_path, arm_age_h=2, override=True), NOW)
    assert r["status"] == "stalled" and r["orders_24h"] == 0 and r["arms_logging"] == ["NBA"]
    assert "demo_fill.override.env" in r["text"] and "treatment_markout_30m_worse_than_control" in r["text"]


def test_ok_when_a_recent_order_exists(tmp_path):
    assert ds.stall(_rig(tmp_path, order_age_h=3, arm_age_h=2, override=True), NOW)["status"] == "ok"


def test_off_day_is_not_an_alarm(tmp_path):
    assert ds.stall(_rig(tmp_path, arm_age_h=60), NOW)["status"] == "ok"


def test_old_order_outside_window_still_stalls(tmp_path):
    assert ds.stall(_rig(tmp_path, order_age_h=30, arm_age_h=1), NOW)["status"] == "stalled"


def test_missing_policy_log_is_unknown(tmp_path):
    assert ds.stall(tmp_path, NOW)["status"] == "unknown"
