"""W98.2 Part B: entry-cost study arithmetic on a tiny synthetic book. Read-only module, no API."""
import importlib.util
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("ec", ROOT / "12_EXPLORATORY/forward_entry_cost/entry_cost.py")
ec = importlib.util.module_from_spec(spec)
sys.modules["ec"] = ec
spec.loader.exec_module(ec)

T0 = datetime(2026, 10, 20, 18, 0, tzinfo=timezone.utc)
TK = "KXNFLGAME-26OCT20AAABBB-AAA"


def _book(quote_age=10):
    q, d = ec.Series(), ec.Series()
    q.add(TK, T0 - timedelta(seconds=quote_age), {"bid": 0.48, "ask": 0.52})
    d.add(TK, T0 - timedelta(seconds=30), {"top": {"no": 100, "yes": 100}})
    q.sort(); d.sort()
    return q, d


def _order(oid, arm, price_yes=0.50):
    return {"oid": oid, "ticker": TK, "side": "yes", "arm": arm, "ts": T0, "price_yes": price_yes, "stake": 1.0}


def test_taken_at_quote_pays_the_ask_and_fee():
    q, d = _book()
    cache = {"o1": {"fills": 0, "nf_won": True, "settled": True}}
    rows, drop = ec.build_rows([_order("o1", "control")], cache, q, d)
    r = rows[0]
    assert r["quote_px"] == 0.52 and r["depth_holds"] is True and not r["filled"]
    assert abs(r["cf_net"] - (1.0 - 0.52 - ec.fee_rate(TK, 0.52, "taker"))) < 1e-12
    assert drop == {}


def test_as_entered_uses_fill_price_and_maker_fee_is_not_larger():
    q, d = _book()
    cache = {"o1": {"fills": 1.0, "price": 0.50, "won": False, "settled": True}}
    r = ec.build_rows([_order("o1", "control")], cache, q, d)[0][0]
    assert r["filled"] and r["asent_taker"] < 0 and r["asent_maker"] >= r["asent_taker"]
    assert abs(r["asent_taker"] - (0.0 - 0.50 - ec.fee_rate(TK, 0.50, "taker"))) < 1e-12


def test_stale_quote_is_excluded_and_counted_not_used():
    q, d = _book(quote_age=ec.MAX_QUOTE_AGE_S + 60)
    cache = {"o1": {"fills": 0, "nf_won": False, "settled": True}}
    r = ec.build_rows([_order("o1", "treatment")], cache, q, d)[0][0]
    assert r["stale_quote"] and "cf_net" not in r


def test_pending_outcome_and_missing_cache_are_dropped_with_reason():
    q, d = _book()
    cache = {"o1": {"fills": 0, "nf_pending": True}}
    rows, drop = ec.build_rows([_order("o1", "control"), _order("o2", "control")], cache, q, d)
    assert rows == [] and drop == {"outcome_pending": 1, "no_cache": 1}


def test_depth_too_thin_does_not_count_as_holding():
    q, d = ec.Series(), ec.Series()
    q.add(TK, T0 - timedelta(seconds=5), {"bid": 0.48, "ask": 0.52})
    d.add(TK, T0 - timedelta(seconds=5), {"top": {"no": 1}})
    q.sort(); d.sort()
    cache = {"o1": {"fills": 0, "nf_won": True, "settled": True}}
    r = ec.build_rows([_order("o1", "control")], cache, q, d)[0][0]
    assert r["depth_holds"] is False


def test_build_groups_by_sport_and_arm_and_reports_timeline():
    q, d = _book()
    cache = {"o1": {"fills": 1.0, "price": 0.5, "won": True, "settled": True},
             "o2": {"fills": 0, "nf_won": True, "settled": True}}
    rep = ec.build([_order("o1", "control"), _order("o2", "treatment")], cache, q, d, b=50)
    assert set(rep["cells"]) == {"NFL|control", "NFL|treatment", "ALL|control", "ALL|treatment"}
    assert rep["cells"]["NFL|control"]["fills"] == 1 and rep["cells"]["NFL|treatment"]["fills"] == 0
    assert "NFL|control" in ec.render(rep)
