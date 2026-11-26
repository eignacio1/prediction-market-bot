"""W130.5: d6_read must print on a small box. The 11-26 00:30Z read timed out (exit 124, empty output)."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "scripts"), str(ROOT / "src")]

import d6_read as d  # noqa: E402
from prediction_market_bot.decision_trees import coverage  # noqa: E402


def _row(i, **kw):
    r = {"event": "arm_order", "ts": "2026-11-10T00:00:00Z", "market_type": "NBA_SPREAD", "band": "T3", "ok": True,
         "order_id": "o%d" % i, "ticker": "K", "side": "yes", "size_for": {"arm": "RIDE", "big": "x" * 500}, "junk": "y" * 500}
    r.update(kw)
    return r


def test_slim_load_keeps_only_needed_fields(tmp_path):
    p = tmp_path / "orders.jsonl"
    p.write_text("\n".join(json.dumps(_row(i)) for i in range(3)) + "\nnot json\n")
    rows = d.load_rows_slim(p)
    assert len(rows) == 3
    assert "junk" not in rows[0] and rows[0]["size_for"] == {"arm": "RIDE"}


def test_order_evidence_stops_lookups_once_cell_proven():
    calls = []

    def fills_for(oid, tk):
        calls.append(oid)
        return {"fills": 0}
    l6, l7 = coverage.order_evidence([_row(i) for i in range(50)], fills_for)
    assert l7 == {("NBA_SPREAD", "T3")} and len(calls) == 1


def test_fills_budget_exhaustion_returns_none_not_hang():
    t = [0.0]
    fn, state = d.budgeted(lambda o, k: {"fills": 1}, budget_s=10, clock=lambda: t[0])
    assert fn("a", "k") == {"fills": 1}
    t[0] = 11
    assert fn("b", "k") is None and state["exhausted"] and state["calls"] == 1
