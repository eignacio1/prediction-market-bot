"""W112.2 Part B: arm_sizing.size_for on known answers (D6 layer 6)."""
import numpy as np
import pytest

from prediction_market_bot.c4_risk_engine import arm_sizing as a
from prediction_market_bot.c5_execution.market_type_registry import ExecutionBand, MarketType, get_cell

CELL = get_cell(MarketType.NFL_GAME_TOTAL, ExecutionBand.T1_MULTI_DAY)
rng = np.random.default_rng(7)
X = rng.normal(size=20000)
Y = rng.normal(size=20000)


def test_flat_demo_stake_when_no_cap_binds_and_kelly_is_zero_and_never_placed():
    d = a.size_for("RIDE", CELL, a.SizingContext(price=0.50, p_win=0.60))
    assert d.stake_usd == 1.00 and d.basis == "flat_demo" and d.binding_caps == ()
    assert d.kelly_fraction_live == 0.0 and d.kelly_placed is False


def test_kelly_shaped_stake_is_logged_with_known_value_and_not_the_placed_stake():
    # f* = (0.60 - 0.50) / 0.50 = 0.20; 0.25 * 0.20 * 1000 = 50.0
    d = a.size_for("FADE", CELL, a.SizingContext(price=0.50, p_win=0.60))
    assert d.kelly_shaped_usd == pytest.approx(50.0) and d.stake_usd == 1.00
    assert a.kelly_shaped_stake(0.40, 0.50) == 0.0           # no edge -> Kelly-shaped stake is 0
    assert a.kelly_shaped_stake(None, 0.5) is None and a.kelly_shaped_stake(0.6, 1.0) is None


def test_no_bet_sizes_to_zero_and_unknown_arm_sizes_to_zero():
    assert a.size_for("NO_BET", CELL, a.SizingContext(price=0.5, p_win=0.9)).stake_usd == 0.0
    d = a.size_for("WAT", CELL)
    assert d.stake_usd == 0.0 and "unknown arm" in d.reason


@pytest.mark.parametrize("ctx,cap", [
    (a.SizingContext(open_event_usd=4.60), "event"),
    (a.SizingContext(open_day_usd=49.60), "day"),
    (a.SizingContext(open_arm_usd=24.60), "arm_budget"),
])
def test_each_cap_binds_to_its_known_headroom(ctx, cap):
    d = a.size_for("RIDE", CELL, ctx)
    assert d.stake_usd == pytest.approx(0.40) and d.binding_caps == (cap,)


def test_a_full_cap_sizes_zero_with_the_reason():
    d = a.size_for("RIDE", CELL, a.SizingContext(open_event_usd=5.0))
    assert d.stake_usd == 0.0 and d.reason.startswith("cap binds, stake 0") and "event" in d.reason


def test_arm_budget_is_per_arm():
    ctx = a.SizingContext(arm_budget_usd={"POT_OF_GOLD": 0.25}, open_arm_usd=0.0)
    assert a.size_for("POT_OF_GOLD", CELL, ctx).stake_usd == 0.25
    assert a.size_for("RIDE", CELL, ctx).stake_usd == 1.00


def test_two_perfectly_correlated_legs_are_sized_as_one():
    leg = X >= 0.0
    first = a.size_for("RIDE", CELL, a.SizingContext(new_leg_draws=leg))
    assert first.stake_usd == 1.00 and first.merged_legs == 0
    second = a.size_for("RIDE", CELL, a.SizingContext(new_leg_draws=leg.copy(),
                                                       same_game_open=[a.OpenLeg(first.stake_usd, leg)]))
    assert second.stake_usd == 0.0 and second.binding_caps == ("same_game_cluster",)
    assert second.merged_legs == 1 and second.correlated_exposure_usd == 1.00
    assert first.stake_usd + second.stake_usd == 1.00        # the pair is one leg's exposure


def test_independent_legs_do_not_merge():
    d = a.size_for("RIDE", CELL, a.SizingContext(new_leg_draws=Y >= 0.0, same_game_open=[a.OpenLeg(1.0, X >= 0.0)]))
    assert d.stake_usd == 1.00 and d.merged_legs == 0


def test_a_partial_correlation_below_the_merge_threshold_does_not_merge_and_a_higher_cluster_cap_gives_headroom():
    base = X >= 0.0
    flipped = base.copy(); flipped[:200] = ~flipped[:200]    # phi ~ 0.98: merges
    d = a.size_for("RIDE", CELL, a.SizingContext(new_leg_draws=flipped, same_game_open=[a.OpenLeg(0.5, base)],
                                                  cluster_cap_usd=1.25))
    assert d.merged_legs == 1 and d.stake_usd == pytest.approx(0.75) and d.binding_caps == ("same_game_cluster",)
    mild = (0.6 * X + 0.8 * Y) >= 0.0                          # phi ~ 0.41 < 0.90
    assert a.size_for("RIDE", CELL, a.SizingContext(new_leg_draws=mild, same_game_open=[a.OpenLeg(1.0, base)])).merged_legs == 0


def test_unequal_draw_lengths_are_refused_not_guessed():
    with pytest.raises(ValueError):
        a.size_for("RIDE", CELL, a.SizingContext(new_leg_draws=X[:10] >= 0, same_game_open=[a.OpenLeg(1.0, X >= 0)]))


def test_a_closed_hypothesis_closes_no_arm_so_every_arm_is_sized_the_same():
    assert CELL.closed_hypotheses
    stakes = {arm: a.size_for(arm, CELL).stake_usd for arm in a.ARMS if arm != "NO_BET"}
    assert set(stakes.values()) == {1.00}


def test_row_fields_carry_a_size_for_decision_and_never_a_placed_kelly():
    f = a.size_for("RIDE", CELL, a.SizingContext(price=0.5, p_win=0.6)).as_row_fields()["size_for"]
    assert f["kelly_placed"] is False and f["basis"] == "flat_demo" and f["arm"] == "RIDE" and f["stake_usd"] == 1.0


def test_module_has_no_order_path_import():
    import inspect
    src = inspect.getsource(a)
    assert "ride_orders" not in src and "venue_adapter" not in src and "submit_order" not in src
