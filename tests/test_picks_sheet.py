"""Picks sheet (W97.3, B-026): fixture night -> pick rule, orders, results, builder JSON, panel visible-error."""
import datetime as dt
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import build_picks_sheet as bps  # noqa: E402
import build_visual_dashboard_html as bvd  # noqa: E402
from prediction_market_bot.pregame_shadow import picks_sheet as ps  # noqa: E402

T0 = "2026-10-30T23:10:00+00:00"


def _row(tk, p, bid, ask, ts=T0, ev="KXNBAGAME-26OCT30LALDEN"):
    return {"ts_utc": ts, "sport": "NBA", "market_type": "NBA_MONEYLINE", "event_ticker": ev, "market_ticker": tk,
            "p_yes": p, "yes_bid": bid, "yes_ask": ask}


def _w(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(r) + "\n" for r in rows))


def test_parse_ts_tolerates_five_digit_fraction():
    assert ps.parse_ts("2026-10-30T23:10:00.12345Z").microsecond == 123450
    assert ps.parse_ts("garbage") is None


def test_pick_rule_matches_net_edge_gate():
    yes = ps.pick_from_row(_row("KXNBAGAME-26OCT30LALDEN-LAL", 0.70, 0.55, 0.57), "a")
    no = ps.pick_from_row(_row("KXNBAGAME-26OCT30LALDEN-DEN", 0.30, 0.55, 0.57), "a")
    none = ps.pick_from_row(_row("KXNBAGAME-26OCT30LALDEN-X", 0.56, 0.55, 0.57), "a")
    assert yes["side"] == "yes" and yes["edge_after_fee"] > 0.09
    assert no["side"] == "no" and none is None
    assert yes["reasons"] == [ps.NO_REASONS]


def test_one_sided_or_crossed_quote_gives_no_pick():
    assert ps.pick_from_row(_row("K-A", 0.9, None, 0.5), "a") is None
    assert ps.pick_from_row(_row("K-A", 0.9, 0.6, 0.5), "a") is None


def test_latest_row_wins_and_can_retract():
    since = dt.datetime(2026, 10, 30, tzinfo=dt.timezone.utc)
    rows = [_row("K-A", 0.70, 0.55, 0.57, "2026-10-30T22:00:00+00:00"), _row("K-A", 0.56, 0.55, 0.57, T0)]
    assert ps.latest_picks(rows, "a", since) == {}


def test_tail_rows_drops_partial_first_line_and_missing_file(tmp_path):
    f = tmp_path / "x.jsonl"
    _w(f, [{"i": i, "pad": "x" * 50} for i in range(100)])
    got = list(ps.tail_rows(str(f), max_bytes=400))
    assert got and got[-1]["i"] == 99 and all("i" in r for r in got)
    assert list(ps.tail_rows(str(tmp_path / "nope.jsonl"))) == []


def test_orders_and_results_attach():
    since = dt.datetime(2026, 10, 30, tzinfo=dt.timezone.utc)
    p1 = ps.pick_from_row(_row("K-A", 0.70, 0.55, 0.57), "a")
    p2 = ps.pick_from_row(_row("K-B", 0.30, 0.55, 0.57), "a")
    orders = ps.orders_by_ticker([
        {"event": "shadow_order", "ts": T0, "ok": True, "ticker": "K-A", "stake_usd": 1.0, "side": "yes", "price_yes": 0.57},
        {"event": "shadow_skip", "ts": T0, "row_id": "T2-r|K-B", "reason": "mid_gap_above_threshold"}], since)
    ps.attach_orders([p1, p2], orders)
    assert p1["demo_order"]["placed"] and p2["demo_order"] == {"placed": False, "reason": "mid_gap_above_threshold"}
    ps.attach_results([p1, p2], [{"market_ticker": "K-A", "y": 1}, {"market_ticker": "K-B", "outcome": 1}])
    assert p1["result"]["outcome"] == "hit" and p1["result"]["pnl_per_contract"] > 0.3
    assert p2["result"]["outcome"] == "miss" and p2["result"]["pnl_per_contract"] < -0.45


def test_arms_disagreeing_on_one_ticker_are_flagged():
    a = ps.pick_from_row(_row("K-A", 0.70, 0.55, 0.57), "arm1")
    b = ps.pick_from_row(_row("K-A", 0.30, 0.55, 0.57), "arm2")
    g = ps.group_by_game([a, b])
    assert len(g) == 1 and g[0]["arms_disagree"] and len(g[0]["picks"]) == 2


def test_builder_end_to_end_on_a_fixture_night(tmp_path):
    _w(tmp_path / "exp_output/PREGAME_SHADOW/NBA_NBA_MONEYLINE_T2.jsonl",
       [_row("KXNBAGAME-26OCT30LALDEN-LAL", 0.70, 0.55, 0.57)])
    _w(tmp_path / "logs/demo_fill_policy.jsonl", [{"event": "shadow_order", "ts": T0, "ok": True,
       "ticker": "KXNBAGAME-26OCT30LALDEN-LAL", "stake_usd": 1.0, "side": "yes", "price_yes": 0.57}])
    assert bps.main(["--root", str(tmp_path), "--date", "2026-10-30"]) == 0
    doc = json.loads((tmp_path / "exp_output/PICKS_SHEET/picks_latest.json").read_text())
    assert doc["n_picks"] == 1 and doc["games"][0]["picks"][0]["demo_order"]["placed"]
    assert any("nba_engine_v1" in n for n in doc["notes"])  # absent engine rows are noted, not fatal


def test_dashboard_shows_visible_message_when_sheet_missing_or_empty(tmp_path, monkeypatch):
    monkeypatch.setattr(bvd, "ROOT", tmp_path)
    assert bvd.picks()["ok"] is False and bvd.picks()["error"]
    (tmp_path / "exp_output/PICKS_SHEET").mkdir(parents=True)
    (tmp_path / "exp_output/PICKS_SHEET/picks_latest.json").write_text("")
    assert bvd.picks()["ok"] is False
    js = (ROOT / "04_EXECUTION/visual_dashboard/script.js").read_text()
    fn = js[js.index("function picksSheet()"):]
    fn = fn[:fn.index("\n}\n")]
    assert "No picks sheet to show" in fn and "has no picks" in fn


def test_build_injects_the_picks_panel(tmp_path):
    out = tmp_path / "vd.html"
    bvd.build(out)
    html = out.read_text()
    assert 'id="picks"' in html and "function picksSheet()" in html and "__PICKS__" not in html


def test_reasons_from_row_in_plain_words_and_flip_with_side():
    r = {"factor": "home team points scored per game, last 10", "value": 118.2, "pts": 2.4, "toward_yes": 2.4}
    yes_row = dict(_row("KXNBAGAME-26OCT30LALDEN-LAL", 0.70, 0.55, 0.57), reasons=[r])
    no_row = dict(_row("KXNBAGAME-26OCT30LALDEN-DEN", 0.30, 0.55, 0.57), reasons=[r])
    assert "supports this pick" in ps.pick_from_row(yes_row, "a")["reasons"][0]
    assert "works against this pick" in ps.pick_from_row(no_row, "a")["reasons"][0]
    assert "118.2" in ps.pick_from_row(yes_row, "a")["reasons"][0]


def test_arm_without_reasons_says_so():
    row = dict(_row("KXNBAGAME-26OCT30LALDEN-LAL", 0.70, 0.55, 0.57), reasons=None, reasons_note="no per-factor model")
    out = ps.pick_from_row(row, "a")["reasons"]
    assert len(out) == 1 and out[0].startswith(ps.NO_REASONS) and "no per-factor model" in out[0]


def test_dedupe_merges_arms_and_mirror_sides_gg1690():
    ev = "KXNBAGAME-26OCT30LALDEN"
    rows = [
        ("t1", _row(ev + "-LAL", 0.70, 0.55, 0.57)),
        ("t2", _row(ev + "-LAL", 0.70, 0.55, 0.57)),
        ("t1", _row(ev + "-DEN", 0.30, 0.55, 0.57)),   # NO on DEN == YES on LAL
    ]
    picks = [ps.pick_from_row(r, a) for a, r in rows]
    out = ps.dedupe(picks)
    assert len(out) == 1
    assert out[0]["side"] == "yes" and out[0]["ticker"].endswith("-LAL")
    assert out[0]["arms"] == ["t1", "t2"]
    assert out[0]["also_seen_as"] == ["DEN NO"]
    sheet = ps.build("2026-10-30", picks)
    assert sheet["n_picks"] == 1 and sheet["n_rows_before_dedupe"] == 3


def test_dedupe_keeps_distinct_bets_and_non_mirror_tickers():
    ev = "KXNBAGAME-26OCT30LALDEN"
    a = ps.pick_from_row(_row(ev + "-LAL", 0.70, 0.55, 0.57), "t1")
    b = ps.pick_from_row(_row(ev + "-DEN", 0.70, 0.55, 0.57), "t1")   # YES on both teams: conflicting, not mirror
    c = ps.pick_from_row(_row("KXNBASPREAD-26OCT30LALDEN-LAL5", 0.70, 0.55, 0.57), "t1")
    assert len(ps.dedupe([a, b, c])) == 3
