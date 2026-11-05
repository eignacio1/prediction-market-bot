import math

from prediction_market_bot.quant.multiplicity import (
    benjamini_hochberg, holm, one_sided_p, repeated_look_false_positive,
    spend_obrien_fleming, spend_pocock)


def test_holm_known_answer():
    # textbook: p = .01 .04 .03 .005 , m=4 -> adj .04 .06 .06 .02 (monotone)
    r = holm([0.01, 0.04, 0.03, 0.005])
    got = [x["p_adj"] for x in r]
    assert all(math.isclose(a, b) for a, b in zip(got, [0.03, 0.06, 0.06, 0.02]))
    assert [x["reject"] for x in r] == [True, False, False, True]


def test_bh_known_answer():
    # classic: p sorted .001 .008 .039 .041 .042 .06 .074 .205 ; q=.05 rejects first 2... check q-values
    p = [0.001, 0.008, 0.039, 0.041, 0.042, 0.06, 0.074, 0.205]
    r = benjamini_hochberg(p, q=0.05)
    assert math.isclose(r[0]["q"], 0.008) and math.isclose(r[1]["q"], 0.032)
    assert math.isclose(r[4]["q"], 0.0672, rel_tol=1e-3)
    assert [x["reject"] for x in r] == [True, True, False, False, False, False, False, False]


def test_single_test_unchanged():
    assert holm([0.03])[0]["p_adj"] == 0.03
    assert benjamini_hochberg([0.03])[0]["q"] == 0.03


def test_spending_endpoints_and_monotone():
    for f in (spend_obrien_fleming, spend_pocock):
        assert f(0) == 0 and math.isclose(f(1.0), 0.05)
        assert f(0.25) < f(0.5) < f(0.75) < 0.05
    assert spend_obrien_fleming(0.5) < spend_pocock(0.5)  # OBF spends late


def test_repeated_looks_inflate():
    one = repeated_look_false_positive(1, reps=20000)
    assert abs(one - 0.05) < 0.01
    many = repeated_look_false_positive(30, reps=4000)
    assert many > 0.20  # known: ~0.3 at 30 looks
    assert math.isclose(one_sided_p(1.645), 0.05, abs_tol=1e-3)
