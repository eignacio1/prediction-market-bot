from prediction_market_bot.quant import retro_route as rr


def _row(mid, y, move_open=None):
    return {"market_ticker": "KXNBAGAME-26NOV01AAABBB-AAA", "mid": mid, "yes_bid": mid - 0.01, "yes_ask": mid + 0.01,
            "y": y, "move_open": move_open}


def test_pot_of_gold_buys_longshot_side_only_in_pot_bucket():
    assert rr.extra_nets(_row(0.50, 1.0))["POT_OF_GOLD"] is None
    low = rr.extra_nets(_row(0.05, 1.0))["POT_OF_GOLD"]
    assert abs(low - rr.side_net(_row(0.05, 1.0), "YES")) < 1e-12 and low > 0.9
    high = rr.extra_nets(_row(0.95, 0.0))["POT_OF_GOLD"]
    assert abs(high - rr.side_net(_row(0.95, 0.0), "NO")) < 1e-12 and high > 0.9


def test_momentum_open_follows_sign_and_ignores_flat():
    assert rr.extra_nets(_row(0.5, 1.0, 0.02))["MOMENTUM_OPEN"] > 0
    assert rr.extra_nets(_row(0.5, 0.0, -0.02))["MOMENTUM_OPEN"] > 0
    assert rr.extra_nets(_row(0.5, 1.0, 0.001))["MOMENTUM_OPEN"] is None
    assert rr.extra_nets(_row(0.5, 1.0, None))["MOMENTUM_OPEN"] is None


def test_routed_arm_set_unchanged():
    assert rr.ARMS == ("RIDE", "FADE", "MODEL_FADE", "MOMENTUM")
