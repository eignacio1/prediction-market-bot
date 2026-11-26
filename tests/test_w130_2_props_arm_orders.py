"""W130.2 (EXP-NBAPROPS-002): kept-leaf demo orders for NBA props. Fake venue: fill, partial fill, reject, void (player sits)."""
import json
from datetime import datetime, timezone
from types import SimpleNamespace

import pytest

from prediction_market_bot.c5_execution.placement import join as pj
from prediction_market_bot.decision_trees import props_arm_orders as pao

NOW = datetime(2026, 12, 1, 23, 30, tzinfo=timezone.utc)
LEAF = "NBA|NBA_PLAYER_POINTS|T3|4|na"


class FakeClient:
    def __init__(self, ok=True):
        self.calls, self.ok = [], ok

    def submit_order(self, **kw):
        self.calls.append(kw)
        return SimpleNamespace(ok=self.ok, order_id="oid-%d" % len(self.calls) if self.ok else None,
                               error=None if self.ok else "insufficient_balance")


def row(ticker="KXNBAPTS-26DEC01AAABBB-P1-20", mid=0.70, leaf=LEAF, arm="RIDE", side="yes", kept=("zone_defence@player=soft->RIDE",),
        applied=True, conflict=False, start="2026-12-02T00:15:00+00:00"):
    rec = {"arm": arm, "branch": arm, "side": side, "leaf_id": leaf, "prop_split_kept": list(kept), "prop_split_earned": [],
           "prop_split_applied": applied, "prop_split_conflict": conflict, "reason": "x"}
    return {"run_id": "r1", "market_ticker": ticker, "event_ticker": "KXNBAPTS-26DEC01AAABBB", "sport": "NBA",
            "market_type": "NBA_PLAYER_POINTS", "band": "T3", "mid": mid, "yes_bid": mid - 0.01, "yes_ask": mid + 0.01,
            "horizon_hours_to_start": 0.75, "start_time_utc": start, "router_candidates": {"nba_props": rec}}


@pytest.fixture
def env(tmp_path, monkeypatch):
    sw = {"PROPS_ARM_ORDERS": "on"}
    monkeypatch.setattr(pao.pol, "switch_value", lambda n: sw.get(n, ""))
    monkeypatch.setattr(pao, "demo_host_ok", lambda: True)
    monkeypatch.setattr(pao.ksw, "halt_reason", lambda band_name=None: None)
    monkeypatch.setattr(pao.pol, "listing_skip_reason", lambda c, t: None)
    monkeypatch.setattr(pao.pol, "cash_skip_reason", lambda c, s: None)
    monkeypatch.setattr(pao.pol, "schedule_cancel", lambda *a, **k: None)
    monkeypatch.setattr(pao.pol, "refusal_context", lambda c, p: {})
    monkeypatch.setattr(pao.pol, "decide", lambda c, t, d, mid, rid: SimpleNamespace(action="SUBMIT", mid_price=mid, reason="ok", meta={}))
    return SimpleNamespace(log=tmp_path / "o.jsonl", client=FakeClient(), sw=sw)


def go(env, r, now=NOW):
    return pao.act(r, env.client, now=now, log=env.log)


def lines(env):
    return [json.loads(x) for x in env.log.read_text().splitlines()]


def test_the_candidate_map_has_14_kept_entries():
    kept, sha = pao.kept_entries()
    assert len(kept) == 14 and sum(1 for a in kept.values() if a == "FADE") == 2 and len(sha) == 64


def test_fill_places_flat_one_dollar_demo_order_with_kelly_zero(env):
    r = go(env, row())
    assert r["event"] == pao.ORDER_EVENT and r["ok"] and r["stake_usd"] == 1.0 and r["kelly_fraction"] == 0
    c = env.client.calls[0]
    assert c["side"] == "yes" and c["size_usd"] == 1.0 and c["band"] == pao.KILL_BAND
    assert r["leaf_id"] == LEAF and r["order_key"].startswith(LEAF) and r["prereg"] == "EXP-NBAPROPS-002"


def test_fade_leaf_backs_the_other_side(env):
    lf = "NBA|NBA_PLAYER_THREES|T2|2|na"
    r = go(env, row(ticker="KXNBA3PT-26DEC01AAABBB-P1-3", leaf=lf, arm="FADE", side="no", mid=0.70,
                    kept=("rest@player=normal->FADE",), start="2026-12-02T04:30:00+00:00"))
    assert r["event"] == pao.ORDER_EVENT and env.client.calls[0]["side"] == "no"


def test_reject_is_logged_and_counted_not_retried(env):
    env.client.ok = False
    r = go(env, row())
    assert r["event"] == pao.ORDER_EVENT and r["ok"] is False and r["reason"] == "submit_rejected"
    assert len(env.client.calls) == 1


def test_idempotent_per_leaf_market_day(env):
    assert go(env, row())["event"] == pao.ORDER_EVENT
    r2 = go(env, row())
    assert r2["event"] == pao.SKIP_EVENT and r2["reason"] == "already_ordered" and len(env.client.calls) == 1
    nxt = go(env, row(), now=NOW.replace(day=2, hour=0, minute=1, second=0) if False else datetime(2026, 12, 2, 23, 30, tzinfo=timezone.utc))
    assert nxt["reason"] != "already_ordered"


@pytest.mark.parametrize("kw,reason", [
    (dict(applied=False), "no_split_applied"),
    (dict(conflict=True), "conflict"),
    (dict(arm="NO_BET", side=None), "not_ride_or_fade"),
    (dict(kept=("rest@player=normal->RIDE",)), "not_a_kept_leaf"),
    (dict(leaf="NBA|NBA_PLAYER_POINTS|T3|1|na"), "not_a_kept_leaf"),
    (dict(side="no"), "side_disagrees"),
    (dict(start="2026-12-02T02:30:00+00:00"), "outside_band"),
    (dict(start="2026-12-01T23:00:00+00:00"), "tip_passed"),
])
def test_every_skip_has_its_own_counted_reason(env, kw, reason):
    r = go(env, row(**kw))
    assert r["event"] == pao.SKIP_EVENT and r["reason"] == reason and env.client.calls == []


def test_no_candidate_record_is_counted(env):
    r = row()
    r["router_candidates"] = {}
    assert go(env, r)["reason"] == "no_props_candidate"


def test_off_switch_does_nothing_and_dry_places_nothing(env):
    env.sw["PROPS_ARM_ORDERS"] = "off"
    assert go(env, row()) is None and not env.log.exists()
    env.sw["PROPS_ARM_ORDERS"] = "dry"
    r = go(env, row())
    assert r["event"] == pao.WOULD_EVENT and env.client.calls == []


def test_production_host_and_kill_switch_refuse(env, monkeypatch):
    monkeypatch.setattr(pao, "demo_host_ok", lambda: False)
    assert go(env, row())["reason"] == "production_host_refused"
    monkeypatch.setattr(pao, "demo_host_ok", lambda: True)
    monkeypatch.setattr(pao.ksw, "halt_reason", lambda band_name=None: {"halted": True})
    assert go(env, row())["reason"] == "kill_switch_halted" and env.client.calls == []


def test_event_and_day_caps_have_their_own_reasons(env):
    assert pao.EVENT_CAP_USD == 51.0 and pao.DAY_CAP_USD == 408.0
    day = NOW.strftime("%Y-%m-%d")
    prior = [{"event": pao.ORDER_EVENT, "ok": True, "ts": day + "T10:00:00Z", "event_ticker": "EV", "stake_usd": 1.0}] * 51
    assert pao.cap_reason("EV", 1.0, day, prior) == "demo_book_event_cap"
    assert pao.cap_reason("OTHER", 1.0, day, prior) is None
    big = [{"event": pao.ORDER_EVENT, "ok": True, "ts": day + "T10:00:00Z", "event_ticker": "E%d" % (i // 40), "stake_usd": 1.0}
           for i in range(408)]
    assert pao.cap_reason("NEW", 1.0, day, big) == "demo_book_day_cap"


def test_cash_and_placement_skips_are_prefixed(env, monkeypatch):
    monkeypatch.setattr(pao.pol, "cash_skip_reason", lambda c, s: "low_balance")
    assert go(env, row())["reason"] == "cash:low_balance"
    monkeypatch.setattr(pao.pol, "cash_skip_reason", lambda c, s: None)
    monkeypatch.setattr(pao.pol, "decide", lambda c, t, d, mid, rid: SimpleNamespace(action="SKIP", mid_price=None, reason="mid_gap", meta={}))
    assert go(env, row())["reason"] == "placement:mid_gap"


# --- settlement join: the order log feeds placement/join.records unchanged. Partial fill and void (player sits). -------------
def _orders(env):
    return [e for e in lines(env) if e["event"] == pao.ORDER_EVENT]


def _fill(oid, count, price=0.70, taker=False):
    return {"order_id": oid, "yes_price_dollars": price, "count_fp": count, "is_taker": taker, "created_time": "2026-12-01T23:31:00Z",
            "fee_cost_dollars": 0.02}


def test_join_fill_partial_and_void_known_answer(env):
    go(env, row())                                              # filled, wins
    go(env, row(ticker="KXNBAPTS-26DEC01AAABBB-P2-20"))          # partial fill, loses
    go(env, row(ticker="KXNBAPTS-26DEC01AAABBB-P3-20"))          # player sits: market finalizes with no yes/no result
    go(env, row(ticker="KXNBAPTS-26DEC01AAABBB-P4-20"))          # never filled, would have won
    orders = _orders(env)
    fills = [_fill("oid-1", 1.0), _fill("oid-2", 0.4), _fill("oid-3", 1.0)]
    res = {"KXNBAPTS-26DEC01AAABBB-P1-20": {"result": "yes"}, "KXNBAPTS-26DEC01AAABBB-P2-20": {"result": "no"},
           "KXNBAPTS-26DEC01AAABBB-P3-20": {"result": "", "status": "finalized"}, "KXNBAPTS-26DEC01AAABBB-P4-20": {"result": "yes"}}
    later = datetime(2026, 12, 3, tzinfo=timezone.utc)
    recs = {r["ticker"]: r for r in pj.records(orders, fills, res.get, None, later)}
    p1, p2, p3, p4 = (recs["KXNBAPTS-26DEC01AAABBB-P%d-20" % i] for i in (1, 2, 3, 4))
    assert (p1["filled"], p1["won"], p1["contracts"]) == (True, True, 1.0)
    assert (p2["filled"], p2["won"], p2["contracts"]) == (True, False, 0.4)       # partial counts as a fill at the filled size
    assert p3["outcome"] == "void" and p3["won"] is None                           # sits -> void, out of E2 / E3
    assert (p4["filled"], p4["won"]) == (False, True)                              # non-fill, counterfactual win
    pa = pj.per_arm(list(recs.values()))["RIDE|post_epoch_all_sides"]
    assert pa["E1_orders"] == 4 and pa["E1_fills"] == 3 and pa["n_settled_fills"] == 2 and pa["n_nonfills_resolved"] == 1
    assert pa["E3_win_rate_fills"] == 0.5 and pa["E3_win_rate_nonfills_counterfactual"] == 1.0
    assert pj.join_health(list(recs.values()))["void"] == 1


def test_read_wrapper_counts_skips_and_splits_leaves(env):
    import importlib.util, sys
    from pathlib import Path
    sys.path.insert(0, str(Path(pao.__file__).resolve().parents[3] / "scripts"))
    spec = importlib.util.spec_from_file_location("par", Path(pao.__file__).resolve().parents[3] / "scripts" / "props_arm_orders_read.py")
    par = importlib.util.module_from_spec(spec); spec.loader.exec_module(par)
    go(env, row()); go(env, row(applied=False)); go(env, row(applied=False)); go(env, row(side="no"))
    rows = lines(env)
    assert par.skip_counts(rows) == {"total": 3, "by_reason": {"no_split_applied": 2, "side_disagrees": 1}}
    orders = [e for e in rows if e["event"] == pao.ORDER_EVENT]
    recs = pj.records(orders, [_fill("oid-1", 1.0)], {row()["market_ticker"]: {"result": "yes"}}.get, None, datetime(2026, 12, 3, tzinfo=timezone.utc))
    s = par.summarise(rows, recs)
    assert s["orders_rejected"] == 0 and s["events"][pao.ORDER_EVENT] == 1
    assert list(s["per_leaf"]) == ["%s|RIDE|post_epoch_all_sides" % LEAF]


def test_install_script_is_wired_and_default_off():
    from pathlib import Path
    root = Path(pao.__file__).resolve().parents[3]
    conf = (root / "deploy" / "cron.props_arm_orders").read_text()
    assert "PROPS_ARM_ORDERS=on" in conf and "scripts/run_props_arm_orders.py" in conf
    bt = (root / "scripts" / "box_tasks.py").read_text()
    for t in ("install", "readback", "uninstall"):
        assert '"props_arm_orders_%s"' % t in bt
    assert "PROPS_ARM_ORDERS" not in (root / "deploy" / "demo_fill.env").read_text()
