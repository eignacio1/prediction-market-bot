"""H4 quote simulation: fill rule, AS fallback, verdict logic (W123.4)."""
import gzip
import importlib.util
from pathlib import Path

_spec = importlib.util.spec_from_file_location("h4", Path(__file__).resolve().parent.parent / "scripts" / "h4_quote_sim.py")
h4 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(h4)


def _archive(tmp_path, rows):
    p = tmp_path / "a.tsv.gz"
    with gzip.open(p, "wt") as f:
        for r in rows:
            f.write("\t".join(r) + "\n")
    return p


def _row(ts, bid, ask, tk="KXNBAGAME-26NOV12AAABBB-AAA"):
    return [ts, "KXNBAGAME", tk, "KXNBAGAME-26NOV12AAABBB", bid, ask, ask, "2026-11-13T04:00:00Z"]


def test_bid_fills_when_next_ask_trades_through(tmp_path):
    p = _archive(tmp_path, [_row("2026-11-12T10:00:00Z", "0.40", "0.46"), _row("2026-11-12T10:10:00Z", "0.38", "0.41")])
    fills = h4.simulate(p, {"KXNBAGAME-26NOV12AAABBB-AAA": 1.0}, 900)
    assert [(f["side"], f["price"]) for f in fills] == [("bid", 0.41)]
    assert abs(fills[0]["gross"] - 0.59) < 1e-9


def test_no_quote_on_tight_spread_or_long_gap(tmp_path):
    p = _archive(tmp_path, [_row("2026-11-12T10:00:00Z", "0.40", "0.42"), _row("2026-11-12T10:10:00Z", "0.30", "0.32")])
    assert h4.simulate(p, {"KXNBAGAME-26NOV12AAABBB-AAA": 1.0}, 900) == []
    q = _archive(tmp_path, [_row("2026-11-12T10:00:00Z", "0.40", "0.46"), _row("2026-11-12T10:40:00Z", "0.30", "0.32")])
    assert h4.simulate(q, {"KXNBAGAME-26NOV12AAABBB-AAA": 1.0}, 900) == []
    assert len(h4.simulate(q, {"KXNBAGAME-26NOV12AAABBB-AAA": 1.0}, 2400)) == 1


def test_as_fallback_and_bootstrap():
    rows = [dict(fam="F", bucket="2-6h", filled=i < 12, edge=0.0 if i < 12 else 0.1) for i in range(30)]
    tab, _ = h4.as_table(rows)
    assert abs(tab[("F", "2-6h")][0] - 0.1) < 1e-9 and tab[("F", "2-6h")][2] == "cell"
    pt, lo, hi, *_ = h4.cluster_boot([("g%d" % (i % 25), 0.05) for i in range(100)])
    assert abs(lo - 0.05) < 1e-9 and abs(hi - 0.05) < 1e-9 and abs(pt - 0.05) < 1e-9
    assert h4.bh({"a": 0.001, "b": 0.5}) == {"a"}
