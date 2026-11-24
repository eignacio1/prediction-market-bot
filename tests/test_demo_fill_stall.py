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


# W125.2 / GG-2006: two order paths; the alarm fires only when both are zero.
def _arm_log(root, *events):
    d = root / "logs" / "arm_orders"
    d.mkdir(parents=True, exist_ok=True)
    (d / "orders.jsonl").write_text("\n".join(json.dumps(e) for e in events))


def _arm(age_h, ok=True, event="arm_order"):
    return {"ts": (NOW - timedelta(hours=age_h)).isoformat(), "event": event, "ok": ok}


def test_arm_orders_alone_keep_the_alarm_quiet(tmp_path):
    root = _rig(tmp_path, arm_age_h=2)               # old path: zero orders in 24h; arms logged rows
    _arm_log(root, _arm(1), _arm(3))
    r = ds.stall(root, NOW)
    assert r["status"] == "ok" and r["shadow_orders_24h"] == 0 and r["arm_orders_24h"] == 2 and "arm_order 2" in r["text"]


def test_stalls_only_when_both_paths_are_zero(tmp_path):
    root = _rig(tmp_path, arm_age_h=2)
    _arm_log(root, _arm(30), _arm(1, ok=False), _arm(1, event="arm_skip"))  # old, refused, and a skip: none count
    r = ds.stall(root, NOW)
    assert r["status"] == "stalled" and "shadow_order 0, arm_order 0" in r["text"]


def test_arm_log_missing_or_policy_log_missing_still_reads_the_other(tmp_path):
    root = _rig(tmp_path, order_age_h=2, arm_age_h=2)   # shadow path alone, no arm log
    assert ds.stall(root, NOW)["status"] == "ok"
    (root / "logs" / "demo_fill_policy.jsonl").unlink()
    _arm_log(root, _arm(1))                             # arm log alone, no policy log
    assert ds.stall(root, NOW)["status"] == "ok"
