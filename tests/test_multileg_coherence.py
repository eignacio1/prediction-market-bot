"""EXP-033 arithmetic tests. Pure functions only; no network, no archive."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
import multileg_coherence as m  # noqa: E402


def test_fee_is_adr0016_shape():
    assert m.fee(0.5) == 0.0175
    assert m.fee(0.0) == 0.0 and m.fee(1.0) == 0.0


def test_sum_buy_all_yes_gross_and_net():
    # asks .45 + .45 = .90 -> gross .10; fees 2*fee(.45)
    g, n = m.comp_margin([(0.45, 0.60), (0.45, 0.60)], "buy_all_yes")
    assert g == 0.10
    assert abs(n - (0.10 - 2 * m.fee(0.45))) < 1e-4


def test_sum_buy_all_no_pays_n_minus_1():
    # two legs, no asks .48 + .48 = .96 < 1 -> gross .04
    g, n = m.comp_margin([(0.60, 0.48), (0.60, 0.48)], "buy_all_no")
    assert g == 0.04 and n < g


def test_three_leg_no_payoff():
    g, _ = m.comp_margin([(0.5, 0.6)] * 3, "buy_all_no")  # payoff 2, cost 1.8
    assert g == 0.2


def test_no_violation_when_asks_sum_over_one():
    g, n = m.comp_margin([(0.52, 0.50), (0.52, 0.50)], "buy_all_yes")
    assert g < 0 and n < 0


def test_edge_margin_and_fees():
    g, n = m.edge_margin(0.40, 0.55)  # yes(super)=.40, no(sub)=.55 -> gross .05
    assert g == 0.05 and n == round(0.05 - m.fee(0.40) - m.fee(0.55), 4)


def test_mono_margin_tests_all_pairs_not_only_adjacent():
    # legs ascending by floor; leg0 is the super of both others. Only the (0,2) pair violates.
    q = [(0.30, 0.75), (0.31, 0.74), (0.10, 0.60)]
    g, _ = m.mono_margin(q)
    assert g == round(1 - 0.30 - 0.60, 4)  # pair (0,2) = .10; adjacent pairs give ~0 or negative
    assert g > m.edge_margin(q[0][0], q[1][1])[0]


def test_holm_monotone_and_known_values():
    adj = m.holm([0.01, 0.04, 0.03])
    assert adj == [0.03, 0.06, 0.06]
    assert m.holm([0.5])[0] == 0.5


def test_signflip_null_and_signal():
    assert m.signflip_p([0.0] * 40) > 0.99
    assert m.signflip_p([1.0] * 40, flips=2000) < 0.01
    assert m.signflip_p([-1.0] * 40, flips=2000) > 0.99


def test_persistence_requires_consecutive_runs():
    assert m.persistent([(1, True), (2, True), (3, False), (5, True)]) == 2
    assert m.persistent([(1, True), (3, True)]) == 0  # gap in run index
    assert m.persistent([(1, True), (2, True), (3, True)]) == 3


def test_game_key_is_event_suffix():
    assert m.game_key("KXMLBGAME-26OCT011400PHIATL") == "26OCT011400PHIATL"
