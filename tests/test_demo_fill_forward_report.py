"""W68.2 Part B: the daily ADR-0072 forward-test report. Pure-function tests; no network."""
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import demo_fill_forward_report as rpt  # noqa: E402

NOW = datetime(2026, 10, 12, 12, 0, tzinfo=timezone.utc)


def ev(minutes_ago, **kw):
    return {"ts": (NOW - timedelta(minutes=minutes_ago)).isoformat(), **kw}


def shadow_order(m, oid, tk="KXNHLGAME-26OCT12-X"):
    return ev(m, event="shadow_order", row_id=f"run|{tk}", ok=True, order_id=oid, ticker=tk)


def test_counts_skips_cancels_and_fills(monkeypatch):
    monkeypatch.setattr(rpt, "CANCEL_PATH_FIX_EPOCH", NOW - timedelta(days=2))  # GG-754: no_outcome is epoch-gated
    events = [
        shadow_order(300, "o1"), shadow_order(290, "o2"),
        ev(300, event="cancel_scheduled", order_id="o1", position_id="run|KXNHLGAME-26OCT12-X", ticker="KXNHLGAME-26OCT12-X"),
        ev(290, event="cancel_scheduled", order_id="o2", position_id="run|KXNHLGAME-26OCT12-X", ticker="KXNHLGAME-26OCT12-X"),
        ev(299, event="cancel_ok", order_id="o1", position_id="run|KXNHLGAME-26OCT12-X", ticker="KXNHLGAME-26OCT12-X"),
        ev(280, event="shadow_skip", reason="control_arm", row_id="run|KXNHLGAME-26OCT12-Y"),
        ev(270, event="shadow_skip", reason="not_listed_on_demo", row_id="run|KXNHLGAME-26OCT12-Z"),
    ]
    fills = {"o1": {"fills": 1.0, "settled": True, "won": True, "price": 0.40},
             "o2": {"fills": 1.0, "settled": True, "won": False, "price": 0.50}}
    rep = rpt.build_report(events, NOW, lambda oid, tk: fills[oid])
    (c,) = rep["cells"]
    assert (c["book"], c["sport"], c["orders"], c["fills"]) == ("shadow", "NHL", 2, 2)
    assert c["skips_by_reason"] == {"not_listed_on_demo": 1} and c["control_arm_skips"] == 1
    assert c["win_rate_on_fills"] == 0.5
    assert abs(c["settle_minus_price_on_fills"] - ((0.6) + (-0.5)) / 2) < 1e-9
    assert c["cancel_success_rate"] == 1.0 and c["cancels"]["no_outcome_over_15m"] == 1  # o2 never got one


def test_cancel_failure_rate_trips_and_turn_off_edits_repo_config(tmp_path, monkeypatch):
    monkeypatch.setattr(rpt, "CANCEL_PATH_FIX_EPOCH", NOW - timedelta(days=3))
    events = []
    for i in range(5):
        events.append(ev(60 + i, event="cancel_scheduled", order_id=f"p{i}", position_id=f"pid{i}", ticker="KXMLBHIT-X"))
        events.append(ev(59 + i, event="cancel_failed" if i < 2 else "cancel_ok", order_id=f"p{i}", position_id=f"pid{i}", ticker="KXMLBHIT-X"))
    rep = rpt.build_report(events, NOW, None)
    assert [t["condition"] for t in rep["tripped"]] == ["cancel_fail_rate_gt_10pct_in_a_day"]
    env = tmp_path / "demo_fill.env"
    env.write_text("# c\nDEMO_FILL_PLACEMENT_RULE=book_anchor_cancel\nSHADOW_FLAT_STAKE=on\nDEMO_FILL_SEED=w64-2\n")
    logged = []
    assert rpt.switches_active(env)
    assert rpt.turn_off(rep["tripped"], NOW, env, logged.append) is True
    assert not rpt.switches_active(env) and "DEMO_FILL_SEED=w64-2" in env.read_text().splitlines()
    assert logged[0]["event"] == "turn_off"
    assert rpt.turn_off(rep["tripped"], NOW, env, logged.append) is False  # idempotent


def test_healthy_run_trips_nothing_and_paper_orders_count_toward_skip_rate():
    events = [ev(60, event="skip", reason="mid_gap_above_threshold", position_id="a", ticker="KXMLBHIT-X"),
              ev(59, event="cancel_scheduled", order_id="o", position_id="b", ticker="KXMLBHIT-X"),
              ev(58, event="cancel_ok", order_id="o", position_id="b", ticker="KXMLBHIT-X")]
    rep = rpt.build_report(events, NOW, None)
    assert rep["tripped"] == [] and rep["cells"][0]["orders"] == 1
    assert "none tripped" in rpt.summary_line(rep)


def test_projection_against_550():
    events = [shadow_order(60 * 24 * 7, f"o{i}") for i in range(3)]
    rep = rpt.build_report(events, NOW, lambda oid, tk: {"fills": 1.0, "settled": False})
    c = rep["cells"][0]
    assert abs(c["fills_per_week"] - 3 * 7 / 7.0) < 0.05 and c["on_pace_for_550_in_8wk"] is False


def test_report_cron_line_is_new_demo_only_and_mirrored():
    root = Path(__file__).resolve().parents[1]
    frag = (root / "deploy" / "cron.demo_fill_report").read_text()
    conf = (root / "deploy" / "cron.conf").read_text()
    assert frag.strip() in conf
    (line,) = [l for l in frag.splitlines() if l and not l.startswith("#")]
    assert line.startswith("25 11 * * * ") and "BOT_ENV=paper" in line and "scripts/demo_fill_forward_report.py" in line
    assert ".env" not in line.replace("demo_fill.env", "")  # no prod credentials loaded by this job


# ---- W69.1 / GG-587: turn-off goes through an untracked override, tracked config untouched ----
def test_turn_off_writes_untracked_override_and_leaves_tracked_env_byte_identical(tmp_path, monkeypatch):
    from prediction_market_bot.c5_execution import demo_fill_policy as pol
    from prediction_market_bot.c5_execution import shadow_flat_stake as sfs
    env = tmp_path / "demo_fill.env"
    body = "DEMO_FILL_PLACEMENT_RULE=book_anchor_cancel\nSHADOW_FLAT_STAKE=on\nDEMO_FILL_SEED=w64-2\n"
    env.write_text(body)
    monkeypatch.setenv(pol.OVERRIDE_FILE_ENV, str(tmp_path / "demo_fill.override.env"))
    monkeypatch.setenv(pol.SWITCH_ENV, pol.SWITCH_ON_VALUE)
    monkeypatch.setenv(sfs.SWITCH_ENV, "on")
    assert pol.is_enabled() and sfs.is_enabled()
    trips = [{"condition": "cancel_fail_rate_gt_10pct_in_a_day"}]
    assert rpt.turn_off(trips, NOW, env) is True
    assert env.read_text() == body                                   # tracked file never edited
    assert (tmp_path / "demo_fill.override.env").exists()
    assert not rpt.switches_active(env)
    assert not pol.is_enabled() and not sfs.is_enabled()             # policy reads the override last
    (tmp_path / "demo_fill.override.env").unlink()                   # deleting it re-enables
    assert rpt.switches_active(env) and pol.is_enabled() and sfs.is_enabled()


def test_override_file_is_git_ignored():
    from pathlib import Path
    gi = (Path(__file__).parent.parent / ".gitignore").read_text().splitlines()
    assert "deploy/demo_fill.override.env" in gi


def test_historical_404_cancel_failed_reclassified_via_order_status(tmp_path, monkeypatch):
    monkeypatch.setattr(rpt, "CANCEL_PATH_FIX_EPOCH", NOW - timedelta(days=3))
    """GG-596: pre-fix cancel_failed rows with HTTP 404 on terminal orders do not trip the turn-off."""
    events = []
    for i in range(5):
        tk = "KXMLBHIT-X"
        events.append(ev(60 + i, event="cancel_scheduled", order_id=f"p{i}", position_id=f"pid{i}", ticker=tk))
        events.append(ev(59 + i, event="cancel_failed", order_id=f"p{i}", position_id=f"pid{i}", ticker=tk,
                         response={"error": "HTTP 404", "body": "nf"}))
    early = (NOW - timedelta(minutes=120)).isoformat()  # terminal before every attempt
    rep = rpt.build_report(events, NOW, lambda oid, tk: {"status": "canceled", "fills": 0, "last_update": early})
    assert rep["tripped"] == []
    cells = [c for c in rep["cells"] if c["cancels"]["scheduled"]]
    assert cells[0]["cancels"]["already_terminal"] == 5 and cells[0]["cancels"]["failed"] == 0
    # no lookup available -> cannot prove terminal -> stays a failure
    rep2 = rpt.build_report(events, NOW, None)
    assert [t["condition"] for t in rep2["tripped"]] == ["cancel_fail_rate_gt_10pct_in_a_day"]
    # GG-646: terminal only AFTER the attempt (exchange cancel at market close) stays a failure
    late = (NOW - timedelta(minutes=10)).isoformat()
    rep4 = rpt.build_report(events, NOW, lambda oid, tk: {"status": "canceled", "fills": 0, "last_update": late})
    assert [x["condition"] for x in rep4["tripped"]] == ["cancel_fail_rate_gt_10pct_in_a_day"]
    # terminal status with no timestamp is unverified -> failure
    rep5 = rpt.build_report(events, NOW, lambda oid, tk: {"status": "canceled", "fills": 0})
    assert rep5["tripped"]
    # resting orders with a 404 stay failures
    rep3 = rpt.build_report(events, NOW, lambda oid, tk: {"status": "resting", "fills": 0})
    assert rep3["tripped"]


def _three_days(reason):
    evs = []
    for d in (1, 2, 3):
        for i in range(10):
            evs.append(ev(d * 1440 + i, event="skip", reason=reason, position_id=f"p{d}{i}", ticker="KXMLBHIT-X"))
    return evs


def test_listing_skips_never_trip_skip_rate_turn_off():
    rep = rpt.build_report(_three_days("not_listed_on_demo"), NOW, None)
    assert rep["tripped"] == []
    chk = rep["turn_off_checks"]["skip_rate_gt_90pct_three_days"]
    assert not chk["tripped"] and sum(chk["listing_skips_by_day"].values()) == 30


def test_policy_skips_still_trip_skip_rate_turn_off():
    rep = rpt.build_report(_three_days("book_one_sided"), NOW, None)
    assert [t["condition"] for t in rep["tripped"]] == ["skip_rate_gt_90pct_three_days"]


def _cancel_events(failed, ok, base_min):
    evs = []
    for i in range(failed + ok):
        evs.append(ev(base_min + i, event="cancel_failed" if i < failed else "cancel_ok", order_id=f"c{base_min}{i}",
                      position_id=f"q{base_min}{i}", ticker="KXMLBHIT-X"))
    return evs


def test_pre_fix_cancel_failures_do_not_trip_turn_off(monkeypatch):
    monkeypatch.setattr(rpt, "CANCEL_PATH_FIX_EPOCH", NOW - timedelta(hours=1))
    evs = _cancel_events(8, 0, 600) + _cancel_events(0, 10, 10)  # 8/8 failed before the epoch, 10/10 ok after
    assert rpt.build_report(evs, NOW, None)["tripped"] == []


def test_post_fix_cancel_failures_still_trip(monkeypatch):
    monkeypatch.setattr(rpt, "CANCEL_PATH_FIX_EPOCH", NOW - timedelta(hours=1))
    rep = rpt.build_report(_cancel_events(3, 7, 10), NOW, None)
    assert [t["condition"] for t in rep["tripped"]] == ["cancel_fail_rate_gt_10pct_in_a_day"]


def _orphan(minutes_ago):
    tk = "KXMLBHIT-X"
    return [shadow_order(minutes_ago, "orph", tk),
            ev(minutes_ago, event="cancel_scheduled", order_id="orph", position_id="run|" + tk, ticker=tk)]


def test_pre_fix_no_outcome_orphan_does_not_trip_turn_off(monkeypatch):
    """GG-754: one orphan from before the cancel-path fix must not re-trip the turn-off forever."""
    monkeypatch.setattr(rpt, "CANCEL_PATH_FIX_EPOCH", NOW - timedelta(hours=1))
    rep = rpt.build_report(_orphan(600), NOW, None)
    assert rep["turn_off_checks"]["scheduled_cancel_no_outcome_15m"] == {"count": 0, "tripped": False}
    assert rep["tripped"] == []


def test_post_fix_no_outcome_orphan_still_trips(monkeypatch):
    monkeypatch.setattr(rpt, "CANCEL_PATH_FIX_EPOCH", NOW - timedelta(hours=2))
    rep = rpt.build_report(_orphan(60), NOW, None)
    assert [t["condition"] for t in rep["tripped"]] == ["scheduled_cancel_no_outcome_15m"]


def test_writes_are_atomic_no_tmp_left(tmp_path, monkeypatch):
    """GG-754: override file, report and cache go through atomic_write_text (temp + os.replace)."""
    env = tmp_path / "demo_fill.env"
    env.write_text("SHADOW_FLAT_STAKE=on\n")
    calls = []
    real = rpt.atomic_write_text
    monkeypatch.setattr(rpt, "atomic_write_text", lambda p, t: (calls.append(Path(p).name), real(p, t))[1])
    assert rpt.turn_off([{"condition": "x"}], NOW, env)
    assert calls == ["demo_fill.override.env"]
    assert "SHADOW_FLAT_STAKE=off" in (tmp_path / "demo_fill.override.env").read_text()
    assert not [p for p in tmp_path.iterdir() if p.name.endswith(".tmp")]


def test_since_window_and_non_fill_counterfactual():
    events = [shadow_order(600, "old"), shadow_order(60, "o1"), shadow_order(50, "o2")]
    fills = {"o1": {"fills": 1.0, "settled": True, "won": True, "price": 0.40},
             "o2": {"fills": 0.0, "settled": True, "nf_won": False}}
    rep = rpt.build_report(events, NOW, lambda oid, tk: fills[oid], since=NOW - timedelta(minutes=120))
    (c,) = rep["cells"]
    assert (c["orders"], c["fills"], c["non_fills_resolved"]) == (2, 1, 1)
    assert c["win_rate_on_fills"] == 1.0 and c["win_rate_on_non_fills"] == 0.0
    assert rep["since"] is not None
