"""Known-answer tests for 12_EXPLORATORY/edge_location/exec_fills/exec_fills.py (W124.3)."""
import importlib.util
import os
import random

_P = os.path.join(os.path.dirname(__file__), "..", "12_EXPLORATORY", "edge_location", "exec_fills", "exec_fills.py")
_s = importlib.util.spec_from_file_location("exec_fills", _P)
ef = importlib.util.module_from_spec(_s)
_s.loader.exec_module(ef)


def _rec(g, arm, won, price=0.5, fee=0.01, ts="2026-11-21T00:00:00+00:00", hours=3.0):
    return {"ticker": "KXNBASPREAD-%s-X" % g, "arm": arm, "series": "KXNBASPREAD", "filled": True, "won": won,
            "fill_price": price, "fee_per_contract": fee, "fill_ts": ts, "hours": hours}


def test_net_after_fee_known_answer():
    assert abs(ef.net_of(_rec("a", "RIDE", True)) - 0.49) < 1e-9
    assert abs(ef.net_of(_rec("a", "RIDE", False)) - (-0.51)) < 1e-9
    r = _rec("a", "RIDE", True); r["fee_per_contract"] = None
    assert ef.net_of(r) is None


def test_cut_split_and_buckets():
    pre, fwd = ef.split_by_cut([_rec("a", "RIDE", True, ts="2026-11-20T19:59:59+00:00"), _rec("b", "RIDE", True)])
    assert len(pre) == 1 and len(fwd) == 1
    assert ef.bucket(3.0) == "2-6h" and ef.bucket(30) == "24h+" and ef.bucket(None) is None


def test_isotonic_monotone_and_pooling():
    k = ef.isotonic([0.1, 0.2, 0.3, 0.4], [0.5, 0.2, 0.6, 0.9])
    ys = [y for _, y in k]
    assert ys == sorted(ys)
    assert abs(ef.apply_iso(k, 0.15) - 0.35) < 1e-9


def test_control_variate_reduces_variance_and_keeps_mean():
    rng = random.Random(3)
    c = [rng.gauss(0, 0.1) for _ in range(500)]
    y = [2.0 * ci + rng.gauss(0, 0.02) for ci in c]
    r = ef.cv_adjust(y, c, ["g"] * 500)
    assert r["var_reduction"] > 0.9 and abs(sum(r["adj"]) / 500 - sum(y) / 500) < 1e-9


def test_pairing_is_within_game():
    recs = [_rec("1", "RIDE", True), _rec("1", "FADE", False), _rec("2", "RIDE", True)]
    d = ef.paired_arm_diff(recs, "RIDE", "FADE")
    assert list(d) == ["KXNBASPREAD-1"] and abs(d["KXNBASPREAD-1"] - 1.0) < 1e-9


def test_eb_pool_shrinks_and_homogeneous_gives_zero_tau():
    r = ef.eb_pool([0.1, 0.1, 0.1], [0.05, 0.05, 0.05])
    assert r["tau2"] == 0 and all(abs(s - 0.1) < 1e-9 for s in r["shrunk"])
    r = ef.eb_pool([0.0, 0.4], [0.3, 0.3])
    assert 0.0 < r["shrunk"][1] < 0.4


def test_planted_positive_cell_supported_null_collecting():
    rng = random.Random(5)
    pos = [_rec("p%d" % i, "RIDE", rng.random() < 0.65) for i in range(200)]
    nul = [_rec("n%d" % i, "FADE", rng.random() < 0.51) for i in range(40)]
    t = {c["arm"]: c for c in ef.cell_table(pos + nul)}
    assert ef.classify(t["RIDE"]["lo"], t["RIDE"]["hi"]) == "SUPPORTED"
    assert ef.classify(t["FADE"]["lo"], t["FADE"]["hi"]) in ("COLLECTING", "NOT SUPPORTED")
