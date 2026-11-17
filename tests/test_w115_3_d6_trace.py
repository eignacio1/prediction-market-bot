"""W115.3 / B-091 + B-092: the one-game trace read, the NHL router hook, the NFL layer-3 rule, the ERROR reason. No network."""
from __future__ import annotations

import importlib.util
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO / "src"))
import d6_trace_read as tr  # noqa: E402
import nhl_shadow_eval as ev  # noqa: E402
from prediction_market_bot.decision_trees import coverage, shadow_route as sr  # noqa: E402

NOW = datetime(2026, 11, 16, 12, 0, tzinfo=timezone.utc)


def _row(sport="NHL", mt="NHL_MONEYLINE", band="T1", game="26NOV15BOSNYR", series="KXNHLGAME", leg="BOS", router=None, **kw):
    r = {"run_id": "r1", "ts_utc": "2026-11-15T14:00:00+00:00", "sport": sport, "market_type": mt, "band": band,
         "horizon_hours_to_start": 20.0, "event_ticker": f"{series}-{game}", "market_ticker": f"{series}-{game}-{leg}",
         "p_yes": 0.55, "yes_bid": 0.48, "yes_ask": 0.52, "mid": 0.5, "half_spread": 0.02,
         "start_time_utc": "2026-11-16T00:00:00+00:00", "model_id": "m"}
    if router is not None:
        r["router"] = router
    r.update(kw)
    return r


def test_error_reason_carries_the_message():
    out = sr.router_fields({"market_ticker": "X-1"}, "X")["router"]  # no event_ticker / bid / ask
    assert out["branch"] == "ERROR" and out["reason"].startswith("KeyError:") and len(out["reason"]) <= 160


def test_nhl_row_routes_through_the_hook(tmp_path):
    hook = sr.hook_for(lambda r: ev.cell_path(tmp_path, r["market_type"], r["band"]))
    out = hook(_row())["router"]
    assert out["branch"] not in (None, "ERROR") and out["leaf_id"].startswith("NHL|NHL_MONEYLINE|T1")
    assert hook({"market_ticker": "KXNHLGAME-X-Y"})["router"]["branch"] == "ERROR"  # never raises


def test_nhl_writer_persists_the_router_block_and_hands_it_on(tmp_path):
    seen = []
    hook = sr.hook_for(lambda r: ev.cell_path(tmp_path, r["market_type"], r["band"]))
    n = ev.append_rows([_row()], tmp_path, on_row=seen.append, extra_for=hook)
    assert n == {"NHL_MONEYLINE_T1": 1}
    disk = json.loads((tmp_path / "NHL_MONEYLINE_T1.jsonl").read_text().splitlines()[0])
    assert disk["router"]["branch"] not in (None, "ERROR") and seen[0]["router"] == disk["router"]
    # second run: the previous mid comes from the NHL cell file, so the move bin is no longer always "na"
    r2 = _row(run_id="r2", yes_bid=0.50, yes_ask=0.54, mid=0.52)
    sr._SEEN.clear()
    ev.append_rows([r2], tmp_path, extra_for=hook)
    disk2 = json.loads((tmp_path / "NHL_MONEYLINE_T1.jsonl").read_text().splitlines()[1])
    assert disk2["router"]["move_source"] == "ledger_tail"


def test_nhl_writer_without_hook_is_unchanged_and_a_raising_hook_never_blocks(tmp_path):
    ev.append_rows([_row()], tmp_path / "a")
    assert "router" not in json.loads((tmp_path / "a" / "NHL_MONEYLINE_T1.jsonl").read_text())

    def boom(r):
        raise RuntimeError("x")
    assert ev.append_rows([_row()], tmp_path / "b", extra_for=boom) == {"NHL_MONEYLINE_T1": 1}


def test_nhl_eval_still_imports_no_router_code():
    src = (REPO / "scripts" / "nhl_shadow_eval.py").read_text()
    assert "decision_trees" not in src and "shadow_route" not in src


def test_nfl_layer3_rule_counts_when_the_committed_snapshots_load():
    from prediction_market_bot.nfl_engine.providers import default_nfl_providers
    assert default_nfl_providers() is not None  # the snapshots are committed
    assert "nfl" in coverage.filter_layer_sports()


def test_pick_game_prefers_started_then_most_cells():
    rows = [_row(game="A", start_time_utc="2026-11-17T00:00:00+00:00"), _row(game="A", band="T2", start_time_utc="2026-11-17T00:00:00+00:00"),
            _row(game="B"), _row(game="C"), _row(game="C", band="T2")]
    assert tr.pick_game(rows, NOW) == "C"
    assert tr.pick_game([], NOW) is None


def test_build_shows_each_layer_and_the_break():
    routed = {"branch": "RIDE", "leaf_id": "L1", "reason": "leaf_arm:RIDE", "filters_n": 3, "filters_note": None,
              "split_kept": ["a"], "move_source": "ledger_tail"}
    rows = [_row(router=routed), _row(leg="NYR", router={"branch": "ERROR", "reason": "KeyError"}), _row(mt="NHL_GAME_TOTAL", series="KXNHLTOTAL")]
    orders = [{"ts": "2026-11-15T14:00:01Z", "event": "arm_order", "ok": True, "order_id": "o1", "sport": "NHL", "market_type": "NHL_MONEYLINE",
               "band": "T1", "arm": "RIDE", "event_ticker": "KXNHLGAME-26NOV15BOSNYR", "ticker": "KXNHLGAME-26NOV15BOSNYR-BOS",
               "side": "yes", "stake_usd": 5.0, "size_for": {"stake_usd": 5.0}},
              {"ts": "2026-11-15T14:00:01Z", "event": "arm_skip", "reason": "unrouted", "sport": "NHL", "market_type": "NHL_GAME_TOTAL",
               "band": "T1", "arm": "UNROUTED", "event_ticker": "KXNHLTOTAL-26NOV15BOSNYR"}]
    doc = tr.build(rows, orders, lambda oid, tk: {"fills": 1}, NOW, leaf_doc={"leaves": {"L1": {"arm": "RIDE", "thin": False, "test": {"test_n_games": 12}}}},
                   d6_cells=[{"market_type": "NHL_MONEYLINE", "band": "T1", "layers": [True] * 6 + [False]}], with_reraise=False)
    nhl = doc["sports"]["NHL"]
    assert nhl["game"] == "26NOV15BOSNYR" and nhl["error_reasons"] == {"KeyError": 1}
    ml, tot = nhl["cells"]["NHL_MONEYLINE|T1"], nhl["cells"]["NHL_GAME_TOTAL|T1"]
    assert ml["L1_rows_with_p"] == 2 and ml["L4_branch"] == {"RIDE": 1, "ERROR": 1} and ml["L3_rows_with_kept_split"] == 1
    assert ml["L5_leaves_seen"]["L1"]["test_n_games"] == 12 and ml["L6_rows_with_size_for"] == 1
    assert ml["L7_fill_lookups"][0]["fills"] == 1 and ml["rule_says_layers"] == [1, 1, 1, 1, 1, 1, 0]
    assert tot["L4_branch"] == {"NO_ROUTER_BLOCK": 1} and tot["events"] == {"arm_skip|unrouted|UNROUTED": 1} and tot["rule_says_layers"] is None
    assert nhl["cells_in_window"]["NHL_GAME_TOTAL|T1"]["router"] == 0
    assert doc["sports"]["NBA"]["game"] is None


def test_tail_rows_window_and_bad_lines(tmp_path):
    p = tmp_path / "NHL_MONEYLINE_T1.jsonl"
    p.write_text("\n".join([json.dumps(_row()), "garbage", json.dumps(_row(ts_utc="2026-11-01T00:00:00+00:00")), json.dumps({"ts_utc": "2026-11-15T14:00:00Z"})]))
    got = tr.tail_rows(p, datetime(2026, 11, 13, tzinfo=timezone.utc))
    assert len(got) == 1 and got[0]["_file"] == p.name


def test_allowlist_entry_is_read_only_and_script_never_writes():
    spec = importlib.util.spec_from_file_location("box_tasks", REPO / "scripts" / "box_tasks.py")
    bt = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(bt)
    assert bt.TASKS["d6_trace_read"].endswith("scripts/d6_trace_read.py")
    src = (REPO / "scripts" / "d6_trace_read.py").read_text()
    assert not re.search(r"\.write_text\(|open\([^)]*[\"'][wa]b?[\"']|submit_order|\.unlink\(|os\.remove", src)
