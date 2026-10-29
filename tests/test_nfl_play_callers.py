"""Known-answer tests for nfl_play_callers: a simulated caller with a known tendency is recovered, no leakage, reset rule."""
import numpy as np
import pandas as pd

from prediction_market_bot.c1_signal_ingestion import nfl_play_callers as pc

K = {f: 400.0 for f in pc.FEATURES}


def test_parse_and_oc_table_split_season():
    rows = [
        {"id": "buffalo-bills-r019-oc-2023", "team": "buffalo-bills", "season": 2023, "player": "Ken Dorsey", "claim": "was OC"},
        {"id": "buffalo-bills-r019-oc-2023b", "team": "buffalo-bills", "season": 2023, "player": "Joe Brady",
         "claim": "OC (interim) from Week 11 of the 2023 season onward."},
        {"id": "buffalo-bills-r019-dc-2023", "team": "buffalo-bills", "season": 2023, "player": "Leslie Frazier", "claim": "DC"},
    ]
    oc = pc.load_oc_table(rows)
    assert pc.caller_for(oc, "BUF", 2023, 10, "Sean McDermott") == ("OC:Ken Dorsey", "R-019 OC")
    assert pc.caller_for(oc, "BUF", 2023, 11, "Sean McDermott") == ("OC:Joe Brady", "R-019 OC")
    # no OC record -> head coach fallback, source named
    assert pc.caller_for(oc, "BUF", 2022, 1, "Sean McDermott") == ("HC:Sean McDermott", "HC fallback")
    assert pc.caller_for(oc, "BUF", 2022, 1, None) == (None, "none")


def test_ledger_recovers_known_tendency_and_prior_is_zero():
    rng = np.random.default_rng(7)
    led = pc.CallerLedger({f: 200.0 for f in pc.FEATURES})
    assert led.estimate("OC:new", 2020)["pass_oe"] == 0.0  # no history == the prior
    true = {"OC:A": 0.06, "OC:B": -0.06, "OC:C": 0.0}
    for g in range(60):
        for c, mu in true.items():
            x = rng.binomial(1, 0.5 + mu, 60) - 0.5  # residual vs an expected pass rate of 0.5
            led.update(c, 2020, {"pass_oe": (float(x.sum()), 60.0)})
    e = {c: led.estimate(c, 2020)["pass_oe"] for c in true}
    assert e["OC:A"] > 0.03 > -0.03 > e["OC:B"] and abs(e["OC:C"]) < 0.02
    # shrinkage: the estimate is pulled toward 0 relative to the raw mean (3600 plays, k=200 -> factor 0.947)
    assert e["OC:A"] < 0.06 + 0.02


def test_change_resets_toward_prior_and_follows_person():
    led = pc.CallerLedger({f: 100.0 for f in pc.FEATURES}, season_decay=0.5)
    led.update("OC:A", 2020, {"pass_oe": (50.0, 500.0)})
    a2020 = led.estimate("OC:A", 2020)["pass_oe"]
    assert a2020 > 0.07
    assert 0 < led.estimate("OC:A", 2022)["pass_oe"] < a2020  # confidence decays with elapsed seasons: back toward the prior
    assert led.estimate("OC:B", 2020)["pass_oe"] == 0.0  # a different caller on the same team starts at the prior


def test_no_leak_estimate_ignores_the_game_it_predicts():
    led = pc.CallerLedger(K)
    led.update("OC:A", 2020, {f: (5.0, 50.0) for f in pc.FEATURES})
    before = led.estimate("OC:A", 2020)
    # the estimate for the next game is read before its own update; changing that game's data cannot alter it
    assert led.estimate("OC:A", 2020) == before
    led.update("OC:A", 2020, {f: (-500.0, 50.0) for f in pc.FEATURES})
    assert led.estimate("OC:A", 2020) != before


def _synthetic_pbp(seed=3):
    """Two teams, one caller each with a known pass tendency, 3 seasons x 17 games."""
    rng = np.random.default_rng(seed)
    rows, gid = [], 0
    eff = {"AAA": 0.10, "BBB": -0.10}
    for season in (2016, 2017, 2018):
        for week in range(1, 18):
            gid += 1
            for team, opp in (("AAA", "BBB"), ("BBB", "AAA")):
                for i in range(110):
                    down = int(rng.integers(1, 4))
                    p = 0.35 + 0.1 * down + eff[team]
                    rows.append(dict(
                        game_id=f"g{gid}", season=season, season_type="REG", week=week, game_date=f"{season}-09-{week:02d}",
                        home_team="AAA", away_team="BBB", home_coach="HcA", away_coach="HcB", posteam=team, defteam=opp,
                        play_type="pass" if rng.random() < p else "run", down=down, ydstogo=int(rng.integers(1, 12)),
                        yardline_100=int(rng.integers(5, 95)), score_differential=0.0, qtr=2, game_seconds_remaining=2000.0,
                        half_seconds_remaining=1500.0, qb_kneel=0, qb_spike=0, two_point_attempt=0, drive=1, penalty=0,
                        timeout=0, out_of_bounds=0, play_id=len(rows),
                    ))
    return pd.DataFrame(rows)


def test_end_to_end_recovers_simulated_callers_without_future_data():
    pbp = _synthetic_pbp()
    seasons = {y: pbp[pbp.season == y] for y in (2016, 2017, 2018)}
    tg = pc.team_game_sums(seasons, first=2017)
    oc = {("AAA", 2017): [(1, "Ann")], ("AAA", 2018): [(1, "Ann")], ("BBB", 2017): [(1, "Bob")], ("BBB", 2018): [(1, "Bob")]}
    out = pc.replay(tg, oc, {f: 300.0 for f in pc.FEATURES})
    last = out[out.season == 2018].groupby("caller")["est_pass_oe"].last()
    # true effects are +/-0.10 around the league cell mean (which averages the two teams); recovered with the right sign and size
    assert last["OC:Ann"] > 0.05 and last["OC:Bob"] < -0.05
    first = out[(out.season == 2017) & (out.week == 1)]
    assert (first["est_pass_oe"] == 0.0).all()  # nothing earlier than the first replayed game
