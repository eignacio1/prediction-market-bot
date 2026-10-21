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
    (c,) = [x for x in rep["cells"] if x["arm"] != "control"]
    assert (c["book"], c["sport"], c["orders"], c["fills"]) == ("shadow", "NHL", 2, 2)
    assert c["skips_by_reason"] == {"not_listed_on_demo": 1}
    assert [x["control_arm_skips"] for x in rep["cells"] if x["arm"] == "control"] == [0 + 1]  # W81.1: the control skip is the control arm's row
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


def _503_events(n, ok, base_min):
    evs = []
    for i in range(n + ok):
        bad = i < n
        evs.append(ev(base_min + i, event="cancel_failed" if bad else "cancel_ok", order_id=f"v{base_min}{i}",
                      position_id=f"v{base_min}{i}", ticker="KXMLBHIT-X",
                      **({"response": {"error": "HTTP 503"}} if bad else {})))
    return evs


def test_exchange_5xx_only_day_never_trips_and_is_reported_apart(monkeypatch):
    """ADR-0072 addendum 2026-10-15 (operator: 'Exclude exchange 503s')."""
    monkeypatch.setattr(rpt, "CANCEL_PATH_FIX_EPOCH", NOW - timedelta(hours=1))
    rep = rpt.build_report(_503_events(8, 2, 10), NOW, None)
    assert rep["tripped"] == []
    chk = rep["turn_off_checks"]["cancel_fail_rate_gt_10pct_in_a_day"]
    assert sum(chk["venue_transient_failures_by_day"].values()) == 8
    assert sum(c["cancels"]["failed_venue_transient"] for c in rep["cells"]) == 8


def test_code_side_failures_still_trip_alongside_5xx(monkeypatch):
    monkeypatch.setattr(rpt, "CANCEL_PATH_FIX_EPOCH", NOW - timedelta(hours=1))
    evs = _503_events(8, 0, 100) + _cancel_events(3, 7, 10)
    assert [t["condition"] for t in rpt.build_report(evs, NOW, None)["tripped"]] == ["cancel_fail_rate_gt_10pct_in_a_day"]


# --- W81.1: every row carries its recorded arm; nothing unknown folds into "treatment" ----------------------------
START = NOW - timedelta(days=1)  # the test start for these cases


def armed(m, oid, arm, tk="KXNHLGAME-26OCT12AAABBB-X"):
    r = shadow_order(m, oid, tk)
    if arm:
        r["arm"] = arm
    return r


def _rows(rep):
    return {(c["book"], c["sport"], c["arm"]): c for c in rep["cells"]}


def test_arm_label_comes_from_the_record_and_unarmed_or_pre_start_is_unassigned(monkeypatch):
    monkeypatch.setattr(rpt, "CANCEL_PATH_FIX_EPOCH", START)
    events = [armed(60, "c1", "control"), armed(50, "t1", "treatment"), armed(40, "u1", None),
              armed(60 * 30, "p1", "treatment")]  # p1: carries an arm but predates the test start
    rep = rpt.build_report(events, NOW, None)
    rows = _rows(rep)
    assert rows[("shadow", "NHL", "control")]["orders"] == 1
    assert rows[("shadow", "NHL", "treatment")]["orders"] == 1
    assert rows[("shadow", "NHL", "unassigned_pre_test")]["orders"] == 2  # the no-arm order and the pre-start order
    assert "treatment" not in {a for (_, _, a), c in rows.items() if c["orders"] and a == "unassigned_pre_test"}


def test_paper_rows_have_no_recorded_arm_so_they_are_unassigned(monkeypatch):
    monkeypatch.setattr(rpt, "CANCEL_PATH_FIX_EPOCH", START)
    tk = "KXMLBHIT-26OCT12AAABBB-X"
    events = [ev(30, event="cancel_scheduled", order_id="pp1", position_id="pos1", ticker=tk),
              ev(29, event="cancel_ok", order_id="pp1", position_id="pos1", ticker=tk)]
    rows = _rows(rpt.build_report(events, NOW, None))
    assert set(rows) == {("paper", "MLB", "unassigned_pre_test")}
    assert rows[("paper", "MLB", "unassigned_pre_test")]["orders"] == 1


def test_cancel_events_inherit_the_arm_of_their_order(monkeypatch):
    monkeypatch.setattr(rpt, "CANCEL_PATH_FIX_EPOCH", START)
    events = [armed(60, "t1", "treatment"), armed(30, "u1", None),
              ev(59, event="cancel_ok", order_id="t1", position_id="run|X", ticker="KXNHLGAME-26OCT12AAABBB-X"),
              ev(29, event="cancel_ok", order_id="u1", position_id="run|X", ticker="KXNHLGAME-26OCT12AAABBB-X")]
    rows = _rows(rpt.build_report(events, NOW, None))
    assert rows[("shadow", "NHL", "treatment")]["cancels"]["ok"] == 1
    assert rows[("shadow", "NHL", "unassigned_pre_test")]["cancels"]["ok"] == 1


def test_distinct_games_and_fills_per_game_and_topup_split(monkeypatch):
    monkeypatch.setattr(rpt, "CANCEL_PATH_FIX_EPOCH", NOW - timedelta(days=10))
    monkeypatch.setattr(rpt, "TOPUP_TS", NOW - timedelta(days=3))
    g1, g2 = "KXNHLGAME-26OCT12AAABBB-X", "KXNHLGAME-26OCT09CCCDDD-Y"
    events = [armed(60, "a", "treatment", g1), armed(50, "b", "treatment", g1), armed(40, "c", "treatment", g1),
              armed(60 * 24 * 4, "d", "treatment", g2)]
    fills = {k: {"fills": 1.0, "settled": True, "won": True, "price": 0.5} for k in "abcd"}
    (c,) = rpt.build_report(events, NOW, lambda oid, tk: fills[oid])["cells"]
    assert c["distinct_games"] == 2 and c["fills_per_game_max"] == 3 and c["fills_per_game_median"] == 2.0
    assert (c["fills_pre_topup"], c["fills_post_topup"]) == (1, 3)
    assert (c["orders_pre_topup"], c["orders_post_topup"]) == (1, 3)


def test_assignment_check_recomputes_the_hash_and_reports_mismatches(monkeypatch):
    monkeypatch.setattr(rpt, "CANCEL_PATH_FIX_EPOCH", START)
    tk = "KXNHLGAME-26OCT12AAABBB-X"
    ids = [f"run{i}|{tk}" for i in range(40)]
    want = {i: ("treatment" if rpt.hash_assigned(i, "w64-2", 0.5) else "control") for i in ids}
    events = [{**ev(60 - j, event="shadow_order", row_id=i, ok=True, order_id=f"o{j}", ticker=tk), "arm": want[i]}
              for j, i in enumerate(ids)]
    chk = rpt.assignment_check(events, "w64-2", 0.5)
    assert chk["checked"] == 40 and chk["mismatches"] == 0
    flip = [dict(e, arm="control" if e["arm"] == "treatment" else "treatment") if e["row_id"] == ids[0] else e for e in events]
    bad = rpt.assignment_check(flip, "w64-2", 0.5)
    assert bad["mismatches"] == 1 and bad["examples"][0]["row_id"] == ids[0]


def test_summary_line_names_every_arm():
    rep = {"generated_utc": "2026-10-12T12:00:00+00:00", "tripped": [],
           "cells": [{"book": "shadow", "sport": "NHL", "arm": a, "orders": 3, "fills": 2, "distinct_games": 1,
                      "settle_minus_price_on_fills": None} for a in ("control", "treatment", "unassigned_pre_test")]}
    line = rpt.summary_line(rep)
    assert "shadow/NHL/control" in line and "shadow/NHL/treatment" in line and "shadow/NHL/unassigned_pre_test" in line
    assert "games=1" in line


# ---- W81.1-B: per-(book, sport) verdict under the ADR-0072 addendum 2026-10-20 ----
def _arm(vals_by_game, orders_post, fills_post):
    return {"vals_by_game": vals_by_game, "orders_post": orders_post, "fills_post": fills_post}


def _games(mean, n_games, per_game):
    # alternating +/- so each game's mean is `mean`+-0.05 and the pooled mean is exactly `mean`
    return {f"g{i}": [mean + (0.05 if (i + j) % 2 else -0.05) for j in range(per_game)] for i in range(n_games)}


def test_verdict_below_judged_n_is_no_verdict():
    arms = {"control": _arm(_games(0.0, 10, 5), 100, 50), "treatment": _arm(_games(0.3, 10, 5), 100, 50)}
    v = rpt.verdict_for(arms, {"judged": False})
    assert v["state"].startswith("NO VERDICT YET") and v["judged"] is False


def test_a_and_b_hold_but_c_unjudged_reads_pending_never_adopt():
    arms = {"control": _arm(_games(0.0, 30, 20), 1000, 600), "treatment": _arm(_games(0.4, 30, 20), 1000, 300)}
    v = rpt.verdict_for(arms, {"judged": False, "holds": None})
    assert v["state"] == "(a)/(b) hold, pending (c)"


def test_adopt_only_when_c_judged_and_holds():
    arms = {"control": _arm(_games(0.0, 30, 20), 1000, 600), "treatment": _arm(_games(0.4, 30, 20), 1000, 300)}
    assert rpt.verdict_for(arms, {"judged": True, "holds": True})["state"].startswith("ADOPT")
    assert "(c) fails" in rpt.verdict_for(arms, {"judged": True, "holds": False})["state"]


def test_a_holds_b_fails_is_removed_fills():
    arms = {"control": _arm(_games(0.0, 30, 20), 1000, 600), "treatment": _arm(_games(0.4, 30, 20), 1000, 100)}
    assert "removed fills, not adverse selection" in rpt.verdict_for(arms, {"judged": False})["state"]


def test_reject_when_upper_bound_below_005():
    arms = {"control": _arm(_games(0.10, 30, 20), 1000, 600), "treatment": _arm(_games(0.0, 30, 20), 1000, 500)}
    assert rpt.verdict_for(arms, {"judged": False})["state"].startswith("REJECT")


def test_game_clustering_widens_se_vs_independent_fills():
    one_game_each = {"g0": [0.5] * 600, "g1": [-0.5] * 600}  # two games, wildly different
    m = rpt._clustered(one_game_each)
    assert m["n"] == 1200 and m["games"] == 2 and m["var"] > 0.1


def test_markout_c_excludes_pre_collection_and_needs_judged_n():
    epoch = NOW - timedelta(days=1)
    rows = [{"sport": "NFL", "arm": "treatment", "game": "g", "h30": -0.1, "fill_ts": (NOW - timedelta(days=2)).isoformat()},
            {"sport": "NFL", "arm": "control", "game": "g", "h30": 0.0, "fill_ts": NOW.isoformat()}]
    m = rpt.markout_c(rows, "NFL", epoch)
    assert m["treatment_n"] == 0 and m["control_n"] == 1 and m["judged"] is False and m["holds"] is None


def test_build_report_verdict_counts_only_post_topup_orders(monkeypatch):
    monkeypatch.setattr(rpt, "CANCEL_PATH_FIX_EPOCH", NOW - timedelta(days=9))
    monkeypatch.setattr(rpt, "TOPUP_TS", NOW - timedelta(hours=2))
    tk = "KXNFLGAME-26OCT11AAABBB-AAA"
    events, fills = [], {}
    for i, (mins, arm) in enumerate([(600, "control"), (60, "control"), (600, "treatment"), (60, "treatment")]):
        oid = f"o{i}"
        events.append(ev(mins, event="shadow_order", row_id=f"run|{tk}|{i}", ok=True, order_id=oid, ticker=tk, arm=arm))
        fills[oid] = {"fills": 1.0, "settled": True, "won": True, "price": 0.4}
    rep = rpt.build_report(events, NOW, lambda oid, t: fills[oid])
    v = rep["verdicts"]["shadow|NFL"]
    assert (v["control_n"], v["treatment_n"]) == (1, 1)  # the two pre-top-up orders are descriptive only
    assert v["state"].startswith("NO VERDICT YET")
