"""GG-527 / W61.1: fills-only execution evidence for T4M-PROJ."""
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "src"))

from prediction_market_bot import t4_fill_status as tfs  # noqa: E402
import run_band_monitor as rbm  # noqa: E402
import run_power_calc as rpc  # noqa: E402

T0 = datetime(2026, 9, 1, 12, 0, tzinfo=timezone.utc)


def _pos(pid, oid, ticker="KXMLBHIT-26SEP01-X", when=T0, side="yes"):
    return {"position_id": pid, "kalshi_order_id": oid, "kalshi_ticker": ticker,
            "direction": side.upper(), "entered_at": when.isoformat(), "band": "T4M-PROJ"}


def _fill(oid, ticker="KXMLBHIT-26SEP01-X", when=T0, side="yes", fid="f1"):
    return {"order_id": oid, "ticker": ticker, "side": side, "created_time": when.isoformat(), "fill_id": fid}


def test_classification_matrix():
    horizon_fill = _fill("old", when=T0 - timedelta(days=30), fid="h")
    fills = [_fill("o1", fid="f1"), _fill("zz", when=T0 + timedelta(seconds=60), fid="f2"), horizon_fill]
    positions = [
        _pos("A", "o1"),                                   # order_id match
        _pos("B", "nomatch"),                              # ticker+side within 180s of f2
        _pos("C", "o3", ticker="OTHER"),                   # inside horizon, no match
        _pos("D", "o4", ticker="OTHER", when=T0 - timedelta(days=60)),  # predates history
    ]
    rows = tfs.classify_new_positions(positions, fills, True, {})
    cls = {r["position_id"]: r["fill_class"] for r in rows}
    assert cls == {"A": tfs.CONFIRMED_FILLED, "B": tfs.CONFIRMED_FILLED,
                   "C": tfs.CONFIRMED_NOT_FILLED, "D": tfs.UNVERIFIABLE}


def test_incomplete_history_never_confirms_not_filled():
    rows = tfs.classify_new_positions([_pos("C", "o3", ticker="OTHER")], [_fill("x")], False, {})
    assert rows[0]["fill_class"] == tfs.UNVERIFIABLE


def test_idempotent_append_only(tmp_path):
    sc = tmp_path / "s.jsonl"
    rows = tfs.classify_new_positions([_pos("A", "o1")], [_fill("o1")], True, {})
    assert tfs.append_sidecar(rows, sc) == 1
    # a later run with a different verdict for the same position must not rewrite it
    flipped = [dict(rows[0], fill_class=tfs.CONFIRMED_NOT_FILLED)]
    assert tfs.append_sidecar(flipped, sc) == 0
    assert tfs.load_fill_status(sc)["A"]["fill_class"] == tfs.CONFIRMED_FILLED
    assert len(sc.read_text().splitlines()) == 1
    # already-classified positions are skipped by the classifier itself
    assert tfs.classify_new_positions([_pos("A", "o1")], [], True, tfs.load_fill_status(sc)) == []


def test_refuses_live(monkeypatch, tmp_path):
    monkeypatch.setenv("BOT_ENV", "live")
    out = tfs.run_classifier(tmp_path / "p.json", tmp_path / "s.jsonl", client=object())
    assert out["status"] == "SKIPPED" and not (tmp_path / "s.jsonl").exists()


def _ledger_row(pid, pnl, win):
    return {"band": "T4M-PROJ", "position_id": pid, "outcome": "WIN" if win else "LOSS",
            "model_p": 0.6, "mip": 0.5, "direction": "YES", "pnl": pnl, "size_usd": 1.0,
            "threshold": 1, "kalshi_ticker": "KXMLBHIT-26SEP01-X", "resolved_at": "2026-09-02T00:00:00Z"}


def test_g6_counting_uses_filled_rows_only(tmp_path):
    ledger = tmp_path / "t4_mlb_resolved_ledger.jsonl"
    rows = [_ledger_row(f"P{i}", 0.5 if i % 2 else -1.0, i % 2 == 1) for i in range(10)]
    ledger.write_text("".join(json.dumps(r) + "\n" for r in rows))
    # No sidecar: nothing counts as execution evidence
    assert rbm.load_t4_ledger_execution(ledger) == []
    side = tmp_path / "t4_mlb_fill_status.jsonl"
    side.write_text("".join(json.dumps({"position_id": f"P{i}", "fill_class": c}) + "\n" for i, c in
                            [(0, tfs.CONFIRMED_FILLED), (1, tfs.CONFIRMED_NOT_FILLED),
                             (2, tfs.UNVERIFIABLE), (3, tfs.CONFIRMED_FILLED)]))
    got = rbm.load_t4_ledger_execution(ledger)
    assert sorted(r["position_id"] for r in got) == ["P0", "P3"]
    assert len(rbm.load_t4_ledger(ledger)) == 10  # calibration record untouched
    (tmp_path / "portfolio.json").write_text(json.dumps({"closed_positions": [], "open_positions": []}))
    res = rpc.run_all_bands(tmp_path / "portfolio.json", ledger, 0.05, 0.95)["T4M-PROJ"]
    assert res["raw_n"] == 2
    assert res["calibration_all_rows_n"] == 10
    assert "not execution evidence" in res["calibration_all_rows_label"]


def test_execution_summary_and_dashboard_labels(tmp_path):
    closed = [
        {"band": "T4M-PROJ", "position_id": "A", "outcome": "LOSS", "pnl": -1.0},
        {"band": "T4M-PROJ", "position_id": "B", "outcome": "WIN", "pnl": 0.4},
        {"band": "T4M-PROJ", "position_id": "C", "outcome": "WIN", "pnl": 0.5},
        {"band": "T1", "position_id": "Z", "outcome": "WIN", "pnl": 9.0},
    ]
    status = {"A": {"fill_class": tfs.CONFIRMED_FILLED}, "B": {"fill_class": tfs.CONFIRMED_NOT_FILLED}}
    x = tfs.execution_summary(closed, status)
    assert (x["fills_n"], x["fills_pnl"], x["all_n"], x["all_pnl"]) == (1, -1.0, 3, -0.1)
    import generate_project_state as gps
    html = gps._exec_row({"execution": x})
    assert "real fills only" in html and "not execution evidence" in html
    assert gps._exec_row({}) == ""


def test_live_terminal_templates_carry_fills_labels():
    for f in (ROOT / "Live Terminal.html", ROOT / "scripts" / "web_dashboard.py"):
        t = f.read_text()
        assert t.count("T4 P&L · REAL FILLS") == 2 and "calibration, not execution" in t
