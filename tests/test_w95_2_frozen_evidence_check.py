"""W95.2 known-answer test: the reproduction harness returns the original numbers on a frozen synthetic archive."""
import datetime
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "12_EXPLORATORY", "frozen_evidence_check"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "12_EXPLORATORY"))
import repro as R  # noqa: E402
import calib as C  # noqa: E402

from prediction_market_bot.quant.money import fee_k007  # noqa: E402


def _write(tmp_path, n_games=40):
    """n_games MLB totals games, one snapshot each 1h before first pitch (tier T0-2h): bid 0.20 / ask 0.22.
    Every 4th game settles YES, the rest NO."""
    arch, settle = tmp_path / "arch", tmp_path / "settle"
    arch.mkdir()
    settle.mkdir()
    rows, res = [], {}
    for i in range(n_games):
        ev = f"KXMLBTOTAL-26OCT201905T{i:02d}"
        tk = ev + "-7"
        ts = C.game_start(ev)[0] - 3600
        iso = datetime.datetime.fromtimestamp(ts, datetime.timezone.utc).isoformat()
        rows.append({"series_ticker": "KXMLBTOTAL", "event_ticker": ev, "ticker": tk, "run_ts": iso,
                     "yes_bid": 0.20, "yes_ask": 0.22, "yes_mid": 0.21})
        res[tk] = {"result": "yes" if i % 4 == 0 else "no"}
    (arch / "prices_2026-10-20.jsonl").write_text("\n".join(json.dumps(r) for r in rows))
    json.dump(res, open(settle / "s.json", "w"))
    return str(arch), str(settle)


def test_inventory_known_answer(tmp_path):
    arch, _ = _write(tmp_path)
    inv = R.inventory(arch)
    assert inv["files"] == 1 and inv["first"] == inv["last"] == "2026-10-20"
    assert inv["rows_by_series"]["KXMLBTOTAL"] == 40 and inv["KXMLBHIT_two_sided_prestart"] == 0


def test_cell_reproduces_hand_computed_numbers(tmp_path):
    arch, settle = _write(tmp_path)
    import run_w89_2 as W
    first, _s, meta = W.scan(arch)
    assert len(first) == 40
    sett = C.load_settlements(settle)
    rows = [{"game": meta[tk][1], "p": mid, "y": sett[tk], "bid": b, "ask": a} for (tk, _t), (_ts, mid, b, a, _h) in first.items()]
    c = C.cell_test(rows)
    # f = 10/40 = 0.25 > pbar 0.21 -> YES at the ask 0.22; net = 0.25 - 0.22 - fee
    assert c["n"] == 40 and c["games"] == 40 and c["side"] == "yes"
    assert abs(c["net_mean"] - (0.25 - 0.22 - fee_k007(0.22))) < 1e-12


def test_classify_known_answers():
    assert R.classify(100, 0.050, 0.010, 100, 0.0503, 0.0098) == "REPRODUCED"
    assert R.classify(100, 0.050, 0.010, 99, 0.050, 0.010) == "DIFFERS"
    assert R.classify(100, 0.050, 0.010, 0, 0.0, 0.0) == "NOT REPRODUCED"


def test_subset_is_symlinks_with_exclusive_bound(tmp_path):
    arch, _ = _write(tmp_path)
    assert R.archive_files(R.subset(arch, "2026-10-20")) == []
    d = R.archive_files(R.subset(arch, "2026-10-21"))
    assert len(d) == 1 and os.path.islink(d[0])
    assert R.subset(arch, None) == arch


def test_regen_nfl_board_filters_nfl_rows_and_redirects_writes(tmp_path):
    """W96.2: only KXNFL* rows are streamed; the fence is redirected so no file lands in the repo tree."""
    import regen_nfl_board as G
    arch = tmp_path / "arch"
    arch.mkdir()
    rows = [{"series_ticker": "KXNFLTOTAL", "k": 1}, {"series_ticker": "KXMLBHIT", "k": 2}, {"series_ticker": "KXNFLSPREAD", "k": 3}]
    (arch / "prices_2026-10-20.jsonl").write_text("\n".join(json.dumps(r) for r in rows))
    dest = tmp_path / "out.jsonl"
    import _fence
    _real = _fence.safe_out
    _fence.safe_out = lambda p: __import__("pathlib").Path(p)  # fence is for the repo tree; this test writes to tmp_path
    assert G.nfl_rows(str(arch), str(dest)) == 2
    assert [json.loads(l)["k"] for l in dest.read_text().splitlines()] == [1, 3]
    import _fence
    orig = _real
    try:
        G.regenerate.__globals__["RUNS"] = ()  # no scripts: the inputs are box-only; the redirect is what is under test
        res = G.regenerate(str(arch), str(tmp_path / "scratch"))
        assert res["archive_nfl_rows"] == 2
        assert str(_fence.safe_out("12_EXPLORATORY/x.json")) == str(tmp_path / "scratch" / "x.json")
    finally:
        _fence.safe_out = orig
