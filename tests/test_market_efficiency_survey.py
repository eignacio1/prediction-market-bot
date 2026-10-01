import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import market_efficiency_survey as m  # noqa: E402


def test_calib_gap_known_value():
    # one bucket: price 0.25, realised freq 0.75 -> |gap| 0.5, weight 1
    p = np.full(4, 0.25); y = np.array([1, 1, 1, 0.0])
    B, n, gap = m.calib_gap(p, y)
    assert abs(B - 0.5) < 1e-12 and n[2] == 4


def test_calib_gap_top_bucket_includes_one():
    B, n, _ = m.calib_gap(np.array([1.0, 1.0]), np.array([1.0, 1.0]))
    assert B == 0 and n[9] == 2


def test_null_band_covers_calibrated_market():
    rng = np.random.default_rng(1)
    p = rng.uniform(0.05, 0.95, 3000)
    y = (rng.random(3000) < p).astype(float)
    nb = m._null_B(p, np.random.default_rng(2))
    assert m.calib_gap(p, y)[0] < np.percentile(nb, 99.5)


def _row(t, ts, bid, ask, series="KXA", ev="E1"):
    return {"run_ts": ts, "series_ticker": series, "ticker": t, "event_ticker": ev, "yes_bid": bid, "yes_ask": ask,
            "no_ask": "0.5", "yes_mid": None if bid is None else (float(bid) + float(ask)) / 2, "half_spread": 0.01}


def test_decision_snapshot_is_earliest_two_sided(tmp_path):
    rows = [_row("T", "2026-09-02T00:00:00Z", "0.50", "0.52"), _row("T", "2026-09-01T00:00:00Z", None, "0.9"),
            _row("T", "2026-09-01T06:00:00Z", "0.40", "0.42")]
    (tmp_path / "prices_x.jsonl").write_text("\n".join(json.dumps(r) for r in rows))
    s = m.decision_snapshots(str(tmp_path))
    assert s["T"]["run_ts"] == "2026-09-01T06:00:00Z" and abs(s["T"]["p"] - 0.41) < 1e-9


def _fam(n, days, E, clears):
    return {"included_settled_tickers": n, "distinct_days": days, "E": E, "clears_null": clears}


def test_labels_and_order():
    res = {"KXMLBHIT": _fam(5000, 60, 0.01, True), "A": _fam(1000, 60, 0.02, True),
           "B": _fam(1000, 60, 0.03, False), "C": _fam(100, 60, 0.5, True), "D": _fam(1000, 10, 0.5, True),
           "F": _fam(1000, 60, 0.005, True)}
    o = m.label_and_rank(res)
    r = o["families"]
    assert r["A"]["label"] == "CANDIDATE" and r["B"]["label"] == "NO BETTER THAN KXMLBHIT"
    assert r["C"]["label"] == r["D"]["label"] == "INCONCLUSIVE" and r["F"]["label"] == "NO BETTER THAN KXMLBHIT"
    assert o["ranking"][0] == "A" and set(o["inconclusive"]) == {"C", "D"}


def test_tiebreak_more_tickers_wins():
    res = {"KXMLBHIT": _fam(5000, 60, 0.0, True), "X": _fam(400, 60, 0.0100, True), "Y": _fam(900, 60, 0.0102, True)}
    assert m.label_and_rank(res)["ranking"][:2] == ["Y", "X"]
