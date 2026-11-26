"""W127.3: demo-only RFQ client caps/host guard, sampler, quote metrics, and the run loop against a fake client."""
import importlib.util
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "src"))
from prediction_market_bot.c5_execution import kalshi_rfq as R  # noqa: E402
import combo_rfq_demo as D  # noqa: E402


def _row(t, n=3, p=0.3, **kw):
    return dict(market_ticker=t, n_legs=n, engine_p=p, p_product_of_legs=0.15, resolved=True, mc_se=0.004, flags=[], legs_unpriced=[],
                minutes_to_tip=300, quote_state="--", **kw)


def test_caps_are_written_in_code():
    assert R.MAX_RFQS_PER_NIGHT <= 12 and R.MAX_ACCEPTS_PER_RUN <= 6 and R.CONTRACTS_FP == "1.00"


def test_client_refuses_non_demo_and_non_paper(monkeypatch):
    c = R.DemoRfqClient("k" * 12, object())
    monkeypatch.setenv("BOT_ENV", "live")
    with pytest.raises(R.RfqRefused):
        c.create_rfq("X")
    monkeypatch.delenv("BOT_ENV")
    with pytest.raises(R.RfqRefused):
        c.market("X")


def test_run_cap_and_accept_cap(monkeypatch):
    monkeypatch.setenv("BOT_ENV", "paper")
    c = R.DemoRfqClient("k" * 12, object())
    c.sent["create"] = R.MAX_RFQS_PER_RUN
    with pytest.raises(R.RfqRefused):
        c.create_rfq("X")
    c.sent["accept"] = R.MAX_ACCEPTS_PER_RUN
    with pytest.raises(R.RfqRefused):
        c.accept("r", "q", "yes")


def test_pick_sample_filters_and_spreads():
    rows = [_row(f"A{i}", n=n) for i, n in enumerate([2, 3, 4, 5, 6, 7, 8, 9])] + [dict(_row("bad"), flags=["same_player"]), dict(_row("np"), engine_p=None)]
    s = D.pick_sample(rows, 6)
    assert len(s) == 6 and {r["market_ticker"] for r in s}.isdisjoint({"bad", "np"})
    assert {"2-3", "4-6", "7+"} == {("2-3" if r["n_legs"] <= 3 else "4-6" if r["n_legs"] <= 6 else "7+") for r in s}


def test_quote_metrics_and_side():
    m = D.quote_metrics({"yes_bid_dollars": "0.10", "no_bid_dollars": "0.80"}, 0.30, 0.25)
    assert m["buy_yes_price"] == 0.2 and m["buy_no_price"] == 0.9 and m["overround"] == 0.9
    assert m["yes_minus_engine"] == -0.1 and m["yes_minus_product"] == -0.05
    assert D.accept_side(m, 0.30) == "yes"
    assert D.accept_side({"buy_yes_price": None, "buy_no_price": None}, 0.3) is None


class Fake:
    def __init__(self, listed=True, rfq_status=201, quote=True, accept_ok=True):
        self.accept_ok = accept_ok
        self.listed, self.rfq_status, self.quote = listed, rfq_status, quote
        self.cancelled, self.n = [], 0
        self.sent = {"create": 0, "accept": 0}

    def market(self, t): return {"ok": self.listed, "status": 200 if self.listed else 404, "body": {}}
    def create_combo(self, c, legs): return {"ok": False, "status": 400, "body": {"error": "x"}}
    def create_rfq(self, t):
        self.n += 1
        ok = self.rfq_status == 201
        return {"ok": ok, "status": self.rfq_status, "body": {"id": f"r{self.n}"} if ok else {"error": "unsupported"}}
    def quotes(self, rid):
        return {"ok": True, "status": 200, "body": {"quotes": [{"id": "q" + rid, "yes_bid_dollars": "0.10", "no_bid_dollars": "0.80", "status": "executed"}] if self.quote else []}}
    def accept(self, *a):
        if self.sent["accept"] >= R.MAX_ACCEPTS_PER_RUN:
            raise R.RfqRefused("per-run accept cap reached")
        self.sent["accept"] += 1
        return {"ok": self.accept_ok, "status": 204 if self.accept_ok else 409, "body": {}}
    def cancel_rfq(self, rid): self.cancelled.append(rid); return {"ok": True, "status": 204, "body": {}}


def _run(tmp_path, fake, rows):
    t = [0.0]
    return D.run(fake, rows, {}, datetime(2026, 11, 25, tzinfo=timezone.utc), tmp_path, sleep=lambda s: t.__setitem__(0, t[0] + s), clock=lambda: t[0])


def test_run_quotes_accepts_and_cancels(tmp_path):
    f = Fake()
    s = _run(tmp_path, f, [_row(f"T{i}") for i in range(8)])
    assert s["created"] == 8 and s["quoted"] == 8 and s["accepted"] == R.MAX_ACCEPTS_PER_RUN and len(f.cancelled) == 8
    assert s["skips"] == {"cap": 2}
    assert (tmp_path / "COMBO_RFQ_DEMO.jsonl").exists()


def test_run_records_none_and_stops_when_demo_has_no_rfq(tmp_path):
    f = Fake(rfq_status=404)
    s = _run(tmp_path, f, [_row(f"T{i}") for i in range(5)])
    assert s["created"] == 0 and s["none_reason"]["status"] == 404 and f.n == 1


def test_no_quote_and_unlisted(tmp_path):
    assert _run(tmp_path, Fake(quote=False), [_row("A"), _row("B")])["no_quote"] == 2
    assert _run(tmp_path / "u", Fake(listed=False), [_row("A")])["not_listed_on_demo"] == 1


def test_nightly_budget_is_enforced_across_runs(tmp_path):
    _run(tmp_path, Fake(), [_row(f"T{i}") for i in range(R.MAX_RFQS_PER_NIGHT)])
    s = _run(tmp_path, Fake(), [_row(f"U{i}") for i in range(5)])
    assert s["created"] == 0 and s["nightly_budget"] == 0


def test_box_tasks_registered_and_demo_only():
    import box_tasks as bt
    assert "PM_COMBO_RFQ_DEMO=on" in bt.TASKS["combo_rfq_demo_run"] and "BOT_ENV=paper" in bt.TASKS["combo_rfq_demo_run"]


def test_tip_lookup_resolves_with_the_series_the_forecaster_accepts():
    """W127.3 defect: kickoff_for_event only parses KXNBAPTS/REB/AST/3PT, so a KXNBAGAME- key never found a tip and every combo was dropped."""
    from prediction_market_bot.pregame_shadow import nba_engine_props_forecaster as F
    t = datetime(2026, 11, 26, 0, 0, tzinfo=timezone.utc)
    fc = F.NBAEngineProps({}, {}, {("2026-11-25", frozenset(("MIA", "PHI"))): t})
    assert fc.kickoff_for_event("KXNBAGAME-26NOV25MIAPHI") is None
    assert fc.kickoff_for_event("KXNBAPTS-26NOV25MIAPHI")[0] == t
    for f in ("scripts/nba_combo_shadow.py", "scripts/combo_rfq_demo.py"):
        assert 'kickoff_for_event("KXNBAGAME' not in (ROOT / f).read_text()


def test_failed_accepts_count_against_cap_and_do_not_crash(tmp_path):
    f = Fake(accept_ok=False)
    s = _run(tmp_path, f, [_row(f"T{i}") for i in range(6)])
    assert s["quoted"] == 6 and s["accepted"] == 0 and f.sent["accept"] == R.MAX_ACCEPTS_PER_RUN


def test_accept_requires_edge_after_fee_and_counts_skip_reasons(tmp_path):
    m = D.quote_metrics({"yes_bid_dollars": "0.10", "no_bid_dollars": "0.80"}, 0.2, 0.15)   # buy yes 0.20, buy no 0.90
    assert D.accept_decision(m, 0.2) == (None, "edge_below_threshold")
    one = D.quote_metrics({"yes_bid_dollars": "0.0", "no_bid_dollars": "0.40"}, 0.2, 0.15)  # only buy yes at 0.60, engine 0.2
    assert D.accept_decision(one, 0.2) == (None, "one_sided_negative")
    s = _run(tmp_path, Fake(), [_row("A", p=0.2), _row("B", p=0.2)])
    assert s["quoted"] == 2 and s["accepted"] == 0 and s["skips"] == {"edge_below_threshold": 2}


def test_teammate_points_and_flagged_legs_are_never_ordered():
    L = lambda *t: [{"ticker": x, "side": "yes"} for x in t]
    mate = dict(_row("M"), legs=L("KXNBAPTS-26NOV25MIAPHI-MIAJBUTLER22-20", "KXNBAPTS-26NOV25MIAPHI-MIABADEBAYO13-15"))
    opp = dict(_row("O"), legs=L("KXNBAPTS-26NOV25MIAPHI-MIAJBUTLER22-20", "KXNBAPTS-26NOV25MIAPHI-PHITMAXEY0-20"))
    assert D.teammate_points(mate) and not D.eligible(mate)
    assert not D.teammate_points(opp) and D.eligible(opp)
