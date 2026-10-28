"""W92.2 known-answer tests for the exact Kalshi fee (schedule 2026-07-07 formula and examples)."""
import pytest

from prediction_market_bot.quant.money import fee, fee_k007, fee_multiplier, fee_rate


def test_taker_100_at_50c_is_1_75():
    assert fee("KXNFLGAME-X", 0.50, 100, "taker") == pytest.approx(1.75)


def test_maker_100_at_50c_is_0_4375():
    assert fee("KXNFLGAME-X", 0.50, 100, "maker") == pytest.approx(0.4375)


def test_unrounded_95c_matches_schedule_raw():
    assert fee_rate("KXNFLGAME", 0.95, "taker") * 100 == pytest.approx(0.3325)
    assert fee("KXNFLGAME", 0.95, 100) == pytest.approx(0.3325)  # already a whole centicent


def test_centicent_round_up():
    # 1 contract at 0.50: 0.0175 exactly -> 0.0175; at 0.01: 0.000693 -> 0.0007
    assert fee("KXNFLGAME", 0.50, 1) == pytest.approx(0.0175)
    assert fee("KXNFLGAME", 0.01, 1) == pytest.approx(0.0007)
    assert fee("KXNFLGAME", 0.01, 100) == pytest.approx(0.0693)


def test_exact_tie_not_pushed_up():
    assert fee("KXNFLGAME", 0.50, 100) == 1.75  # no float-noise bump to 1.7501


def test_mlb_prelive_half_live_full():
    assert fee_multiplier("KXMLBTOTAL-26OCT01", "taker", "prelive") == 0.5
    assert fee_multiplier("KXMLBTOTAL", "taker", "live") == 1.0
    assert fee_rate("KXMLBTOTAL", 0.5, "taker", "prelive") == pytest.approx(0.5 * fee_k007(0.5))
    assert fee_rate("KXMLBTOTAL", 0.5, "taker", "live") == pytest.approx(fee_k007(0.5))


def test_nfl_taker_equals_k007():
    for p in (0.05, 0.3, 0.5, 0.9):
        assert fee_rate("KXNFLTOTAL", p) == pytest.approx(fee_k007(p))


def test_maker_defaults_and_overrides():
    assert fee("KXMLBTOTAL", 0.5, 100, "maker") == 0.0       # taker-only on the web page
    assert fee("KXUNLISTED", 0.5, 100, "maker") == 0.0       # unlisted: maker 0
    assert fee("KXUNLISTED", 0.5, 100, "taker") == pytest.approx(1.75)
    assert fee("KXMVE-X", 0.5, 100, "maker") == pytest.approx(0.875)  # M=2
    assert fee("KXMLBGAME", 0.5, 100, "maker", "prelive") == pytest.approx(0.2188)


def test_zero_fee_series():
    assert fee("KXBTCY-X", 0.5, 100) == 0.0


def test_bad_args():
    with pytest.raises(ValueError):
        fee("KXNFLGAME", 0.5, 1, side="x")
