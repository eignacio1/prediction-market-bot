from prediction_market_bot.quant import retro_route as rr


def row(ticker="KXNBAGAME-26OCT20BOSDET-DET", run="r1", y=1.0, bid=0.60, ask=0.62, mid=0.61, p=0.7, ts="2026-10-20T10:00:00", mt="NBA_MONEYLINE", ev="KXNBAGAME-26OCT20BOSDET"):
    return dict(market_ticker=ticker, run_id=run, y=y, yes_bid=bid, yes_ask=ask, mid=mid, p_yes=p, ts_utc=ts, market_type=mt,
                event_ticker=ev, sport="NBA", band="T2", start_time_utc="2026-10-20T19:00:00")


def test_side_net_yes_and_no():
    r = row(y=1.0)
    assert abs(rr.side_net(r, "YES") - (1 - 0.62 - rr.fee("KXNBAGAME", 0.62, 1))) < 1e-9
    assert abs(rr.side_net(r, "NO") - (0 - 0.40 - rr.fee("KXNBAGAME", 0.40, 1))) < 1e-9


def test_ride_fade_are_opposite_sides():
    a = rr.arm_nets(row(y=1.0))
    assert a["RIDE"] > 0 > a["FADE"]


def test_moneyline_dedupe_keeps_higher_mid():
    hi = row(ticker="KXNBAGAME-26OCT20BOSDET-DET", mid=0.61)
    lo = row(ticker="KXNBAGAME-26OCT20BOSDET-BOS", bid=0.37, ask=0.39, mid=0.38, y=0.0)
    out = rr.dedupe([lo, hi, hi])
    assert len(out) == 1 and out[0]["market_ticker"].endswith("DET")


def test_moves_and_momentum():
    a, b = row(run="r1", mid=0.55, ts="2026-10-20T09:00:00"), row(run="r2", mid=0.61, ts="2026-10-20T10:00:00")
    rr.add_moves([a, b])
    assert a["move"] is None and abs(b["move"] - 0.06) < 1e-9
    assert rr.arm_nets(a)["MOMENTUM"] is None and rr.arm_nets(b)["MOMENTUM"] is not None


def test_bh_and_boot_deterministic():
    assert rr.bh_reject({"a": 0.001, "b": 0.5}) == {"a"}
    by = {f"g{i}": [0.1, 0.2] for i in range(12)}
    m, lo, hi, p = rr.boot_ci(by)
    assert abs(m - 0.15) < 1e-9 and lo > 0 and p < 0.01


def test_split_is_by_game_date_and_route_no_lookahead():
    rows = []
    for i in range(100):
        rows.append(row(ticker=f"KXNBAGAME-26OCT{i:03d}AAABBB-A", run=f"r{i}", ev=f"KXNBAGAME-26OCT{i:03d}AAABBB",
                        y=1.0, ts=f"2026-10-20T{i%24:02d}:00:00") | {"start_time_utc": f"2026-10-{1+i//4:02d}T19:00:00" if i < 120 else ""})
    fit_g, test_g = rr.split_games(rows)
    assert len(fit_g) == 70 and len(test_g) == 30
    assert max(r["start_time_utc"] for r in rows if rr.game_id(r) in fit_g) <= min(r["start_time_utc"] for r in rows if rr.game_id(r) in test_g)
    out = rr.route(rows)
    assert out["fit_games"] == 70


# --- W114.3: game_rows / arm_report on a case where the truth is known ---------------------------------------------
def _hist(n=200, fav_wins=0.80, price=0.70):
    """Favourite priced 0.70 wins 80% of games: RIDE must be the routed arm in that leaf and net > 0; FADE must lose."""
    losers = round(1 / (1 - fav_wins))  # deterministic: every `losers`-th game loses, so the win rate is exact
    return [{"ticker": "KXNHLGAME-X%d-H" % i, "game_id": "G%03d" % i, "start_time_utc": "2025-01-%02dT00:00:00Z" % (1 + i // 10),
             "p_market": price, "spread": 0.02, "y": 0 if i % losers == 0 else 1, "p_model": 0.5} for i in range(n)]


def test_game_rows_ride_wins_when_favourite_underpriced():
    from prediction_market_bot.quant import retro_route as rr
    rows = rr.game_rows(_hist(), "NHL", "NHL_MONEYLINE")
    rep = rr.arm_report(rows)
    assert rep["family_heldout_by_arm"]["RIDE"]["net"] > 0 > rep["family_heldout_by_arm"]["FADE"]["net"]
    routed = [l for l in rep["leaves"] if l["arm"] != "NO_BET"]
    assert routed and all(l["arm"] == "RIDE" for l in routed)


def test_game_rows_overpriced_favourite_routes_to_no_bet_for_ride():
    from prediction_market_bot.quant import retro_route as rr
    rep = rr.arm_report(rr.game_rows(_hist(fav_wins=0.50), "NHL", "NHL_MONEYLINE"))
    assert rep["family_heldout_by_arm"]["RIDE"]["net"] < 0  # losing arm is routed away, not "no edge"
    assert not any(l["arm"] == "RIDE" for l in rep["leaves"])
