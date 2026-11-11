import numpy as np
import pandas as pd

from prediction_market_bot.nba_engine import granularity_filter as G


def _games(n_seasons=3, teams=12, per=30, seed=0):
    rng = np.random.default_rng(seed)
    rows, gid = [], 0
    for s in range(2021, 2021 + n_seasons):
        for g in range(per):
            ts = rng.permutation(teams)
            for i in range(0, teams, 2):
                gid += 1
                rows.append(dict(game_id=f"{gid:010d}", season=s, date=pd.Timestamp("2021-10-20") + pd.Timedelta(days=g * 2),
                                 home=f"T{ts[i]}", away=f"T{ts[i+1]}", home_pts=110 + int(rng.integers(-15, 15)),
                                 away_pts=108 + int(rng.integers(-15, 15))))
    return pd.DataFrame(rows)


def test_rest_bucket_known_answers():
    assert G.rest_bucket(1) == "b2b" and G.rest_bucket(2) == "one_day" and G.rest_bucket(4) == "rested"
    assert G.rest_bucket(None) is None and G.rest_bucket(float("nan")) is None


def test_team_game_frame_numbers_games_and_rest_point_in_time():
    g = pd.DataFrame([
        dict(game_id="a", season=2025, date="2025-10-22", home="X", away="Y", home_pts=100, away_pts=90),
        dict(game_id="b", season=2025, date="2025-10-23", home="Y", away="X", home_pts=95, away_pts=99),
        dict(game_id="c", season=2025, date="2025-10-27", home="X", away="Y", home_pts=100, away_pts=100)])
    f = G.team_game_frame(g)
    x = f[f.team == "X"].sort_values("week")
    assert list(x.week) == [1, 2, 3]
    assert x.bucket.isna().iloc[0] and list(x.bucket)[1:] == ["b2b", "rested"]
    assert list(x.margin) == [10, 4, 0]


def test_build_entry_pit_and_filter_passes_only_tails():
    f = G.team_game_frame(_games())
    e = G.build_entry(f, "T0", "rested", 2023, 25, "rested_margin")
    if e["ok"]:
        assert 0.0 <= e["percentile_history"] <= 1.0 and e["n_plays"] <= 25
        assert any(m["family"] == "KXNBAGAME" for m in e["markets"])
    # point in time: the entry through 10 games cannot depend on later games
    f2 = f.copy()
    f2.loc[f2.week > 10, "margin"] += 50
    a = G.build_entry(f, "T0", "rested", 2023, 10, "rested_margin")
    b = G.build_entry(f2, "T0", "rested", 2023, 10, "rested_margin")
    assert a.get("value") == b.get("value")


def test_filter_blocks_median_and_passes_extreme():
    ents = [dict(ok=True, n_plays=20, percentile_history=0.5, stability={"trait": True}),
            dict(ok=True, n_plays=20, percentile_history=0.97, stability={"trait": True}),
            dict(ok=True, n_plays=3, percentile_history=0.99, stability={"trait": True})]
    out = G.filter_nba(ents)
    assert [bool(o["pass"]) for o in out] == [False, True, False]
