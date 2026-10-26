"""W87.1 Part A: the reconciliation table is a test. No BUG row; MATCH rows < 1e-6; DEFINITION rows are the registered ones."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import quant_reconcile as qr  # noqa: E402

ROWS = qr.reconcile()


def _v(path_part):
    return {r["verdict"] for r in ROWS if path_part in r["path"]}


def test_no_unexplained_difference():
    assert not [r for r in ROWS if r["verdict"] == "BUG"]


def test_match_rows_agree_below_tolerance():
    for r in ROWS:
        if r["verdict"] == "MATCH":
            assert r["diff"] < qr.TOL, r


def test_rounding_rows_agree_after_the_old_path_rounds():
    from prediction_market_bot import quant as Q
    s = qr.snapshot()
    from prediction_market_bot import t4_fill_status as tfs
    _, lo, hi = Q.cluster_bootstrap(s["byg"], b=4000, seed=20261009)
    assert tfs.cluster_bootstrap_ci(s["byg"]) == (round(lo, 4), round(hi, 4))


def test_paths_with_a_registered_definition_difference():
    assert _v("monitor.py") == {"DEFINITION"}
    assert _v("irls_logistic") == {"DEFINITION"}
    assert _v("_best_side_e_net") == {"DEFINITION"}
    assert "DEFINITION" in _v("demo_fill_forward_report")


def test_snapshot_is_frozen():
    s = qr.snapshot()
    assert len(s["ps"]) == 511 and abs(sum(s["ps"]) - 245.11143414073115) < 1e-9 and s["ys"][:3] == qr.snapshot()["ys"][:3]


def test_monitor_ece_float_edge_is_the_cause():
    """Known answer: p=0.3 sits in decile bin 3 for the core, bin 2 under np.linspace edges."""
    import numpy as np
    edges = np.linspace(0.0, 1.0, 11)
    assert edges[3] > 0.3 and int(0.3 * 10) == 3
