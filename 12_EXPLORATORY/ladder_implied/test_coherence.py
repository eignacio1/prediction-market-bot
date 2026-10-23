"""Known-answer tests for coherence.py: planted violations must be found, clean books must be clean,
and a violation smaller than its fees must show gross>0 but net<=0."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import coherence as C  # noqa: E402


def R(t, bid, ask, **k):
    return dict(ticker=t, bid=bid, ask=ask, **k)


def test_monotonic_planted_and_clean():
    clean = [R("KXNFLTOTAL-26SEP14DENKC-40", .60, .62), R("KXNFLTOTAL-26SEP14DENKC-45", .40, .42), R("KXNFLTOTAL-26SEP14DENKC-50", .20, .22)]
    assert C.monotonic("e", "", clean) == []
    bad = [R("KXNFLTOTAL-26SEP14DENKC-40", .30, .32), R("KXNFLTOTAL-26SEP14DENKC-45", .40, .42)]  # 45 bid .40 > 40 ask .32
    v = C.monotonic("e", "", bad)
    assert len(v) == 1 and abs(v[0]["gross"] - 0.08) < 1e-12 and v[0]["net"] < v[0]["gross"]


def test_fee_erases_small_violation():
    bad = [R("KXNFLTOTAL-26SEP14DENKC-40", .49, .50), R("KXNFLTOTAL-26SEP14DENKC-45", .51, .52)]  # gross .01
    v = C.monotonic("e", "", bad)[0]
    assert abs(v["gross"] - 0.01) < 1e-12 and v["net"] < 0  # 2 legs at ~.5 cost ~.035


def test_same_contract():
    assert C.same_contract(dict(ticker="X-1", event="e", bid=.4, ask=.5, no_bid=.5, no_ask=.6)) == []
    v = C.same_contract(dict(ticker="X-1", event="e", bid=.4, ask=.45, no_bid=.5, no_ask=.50))
    assert [x["type"] for x in v] == ["yes_no_buy"] and abs(v[0]["gross"] - 0.05) < 1e-12
    v = C.same_contract(dict(ticker="X-1", event="e", bid=.55, ask=.6, no_bid=.50, no_ask=.7))
    assert [x["type"] for x in v] == ["yes_no_sell"]


def test_exclusive_sets():
    two = [R("G-A", .40, .45), R("G-B", .50, .55)]
    assert C.exclusive_set("e", two, True) == []
    assert [v["type"] for v in C.exclusive_set("e", [R("G-A", .40, .42), R("G-B", .50, .52)], True)] == ["excl_sum_lt1"]
    assert [v["type"] for v in C.exclusive_set("e", [R("G-A", .55, .57), R("G-B", .50, .52)], True)] == ["excl_sum_gt1"]
    # non-exhaustive (ties): the <1 case is not a violation
    assert C.exclusive_set("e", [R("G-A", .40, .42), R("G-B", .50, .52)], False) == []


def test_dominates():
    assert C.dominates("e", R("SP-1", .50, .52), R("ML-A", .55, .57)) == []
    v = C.dominates("e", R("SP-1", .60, .62), R("ML-A", .50, .52))
    assert len(v) == 1 and abs(v[0]["gross"] - 0.08) < 1e-12


def test_sized_unknown_never_imputed():
    v = C.monotonic("e", "", [R("KXNFLTOTAL-26SEP14DENKC-40", .30, .32), R("KXNFLTOTAL-26SEP14DENKC-45", .40, .42)])[0]
    d = {"KXNFLTOTAL-26SEP14DENKC-45": {"yes": 10, "no": 3}, "KXNFLTOTAL-26SEP14DENKC-40": {"yes": 7, "no": 4}}
    assert C.sized(v, d) == min(10, 4)  # sell hi hits yes(10); buy lo takes no(4)
    assert C.sized(v, {"KXNFLTOTAL-26SEP14DENKC-45": {"yes": 10, "no": 3}}) is None
