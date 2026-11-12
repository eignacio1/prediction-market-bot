"""Known-answer tests for nhl_engine.factors_w112 (W112.4 Part A)."""
import numpy as np
import pandas as pd

from prediction_market_bot.nhl_engine import factors_w112 as f


def _games(rows):
    return pd.DataFrame([dict(game_id=i, start_time_utc=s, venue=v, game_type=2, neutral_site=False,
                              home_team_id=h, away_team_id=a) for i, (s, v, h, a) in enumerate(rows, 1)])


def test_haversine_known_distance():
    # Madison Square Garden -> TD Garden is about 300 km
    d = f.haversine_km(f.ARENAS["Madison Square Garden"], f.ARENAS["TD Garden"])
    assert 295 < d < 310
    assert f.haversine_km(f.ARENAS["TD Garden"], f.ARENAS["TD Garden"]) == 0


def test_schedule_context_rest_travel_density():
    g = _games([("2026-10-01T23:00:00Z", "TD Garden", 1, 2), ("2026-10-02T23:00:00Z", "Madison Square Garden", 2, 1),
                ("2026-10-05T23:00:00Z", "Rogers Arena", 3, 1)])
    c = f.schedule_context(g).set_index(["game_id", "team_id"])
    assert np.isnan(c.loc[(1, 1), "rest_days"])                       # no earlier game known
    assert abs(c.loc[(2, 1), "rest_days"] - 1.0) < 1e-9 and c.loc[(2, 1), "back_to_back"]
    assert 295 < c.loc[(2, 1), "travel_km"] < 310 and c.loc[(2, 1), "tz_shift_h"] == 0
    assert c.loc[(3, 1), "tz_shift_h"] == -3 and not c.loc[(3, 1), "back_to_back"]   # NYC -> Vancouver
    assert c.loc[(2, 1), "games_last_7d"] == 1 and c.loc[(3, 1), "games_last_7d"] == 2
    assert not bool(c.loc[(3, 1), "is_home"])


def test_unknown_venue_is_nan_not_guess():
    g = _games([("2026-10-01T23:00:00Z", "Mystery Rink", 1, 2), ("2026-10-03T23:00:00Z", "TD Garden", 2, 1)])
    c = f.schedule_context(g).set_index(["game_id", "team_id"])
    assert np.isnan(c.loc[(2, 1), "travel_km"])


def _events(n_games, hd_each):
    rows = []
    for gid in range(1, n_games + 1):
        for k in range(10):
            rows.append(dict(game_id=gid, type="shot-on-goal", owner_team_id=1, x=80.0 if k < hd_each else 40.0, y=5.0))
            rows.append(dict(game_id=gid, type="shot-on-goal", owner_team_id=2, x=40.0, y=30.0))
        rows.append(dict(game_id=gid, type="blocked-shot", owner_team_id=1, x=85.0, y=0.0))   # blocked: excluded
    return pd.DataFrame(rows)


def test_shot_quality_known_share_and_asof_excludes_self():
    g = _games([(f"2026-10-{d:02d}T23:00:00Z", "TD Garden", 1, 2) for d in range(1, 9)])
    q = f.shot_quality_rolling(_events(8, 3), g, window=20)
    r = q[(q.team_id == 1)].sort_values("game_id")
    assert r.iloc[4]["hd_for"] == 0.3 and r.iloc[4]["hd_against"] == 0.0   # 3 of 10 unblocked, blocked ignored
    assert np.isnan(r.iloc[3]["hd_for"])                                    # fewer than 5 games
    # as of game 6's puck drop only games finished >=4h before: games 1..5 -> state of game 5
    got = f.asof(q, 1, pd.Timestamp("2026-10-06T23:00:00Z"), ("hd_for",))
    assert got == {"hd_for": 0.3}
    assert f.asof(q, 1, pd.Timestamp("2026-10-01T23:00:00Z"), ("hd_for",)) == {}      # nothing earlier
    # at Oct 5 01:00Z only games 1-3 are finished (game 4 started 2h earlier): fewer than 5 games -> value None
    assert f.asof(q, 1, pd.Timestamp("2026-10-05T01:00:00Z"), ("hd_for",)) == {"hd_for": None}


def test_deployment_top_share_known_answer():
    rows = []
    for gid in range(1, 7):
        for p, dur in zip(range(10), [100, 100, 100, 100, 100, 100, 50, 50, 50, 50]):   # top six = 600 of 800
            rows.append(dict(game_id=gid, team_id=1, player_id=p, duration_s=dur))
    g = _games([(f"2026-10-{d:02d}T23:00:00Z", "TD Garden", 1, 2) for d in range(1, 7)])
    d = f.deployment_rolling(pd.DataFrame(rows), g)
    assert abs(d.sort_values("game_id").iloc[-1]["top_share"] - 0.75) < 1e-9


def test_filters_known_labels_and_unknowns():
    from prediction_market_bot.nhl_engine.filters import nhl_filters
    home = dict(rest_days=3.0, back_to_back=False, games_last_7d=2, travel_km=0.0, tz_shift_h=0, neutral_site=False,
                hd_for=0.9, hd_against=0.1, top_share=0.2)
    away = dict(rest_days=1.0, back_to_back=True, games_last_7d=4, travel_km=3500.0, tz_shift_h=-3, neutral_site=False,
                hd_for=0.1, hd_against=0.9, top_share=0.8)
    o = nhl_filters(home, away)
    assert o["rest@side"] == "home_rest_edge" and o["travel@side"] == "away_long" and o["density@total"] == "away_dense"
    assert o["venue@side"] == "home_ice" and o["shot_quality@side"] == "home_edge" and o["deployment@side"] == "home_edge"
    assert o["shot_quality@total"] == "mid" and o["deployment@total"] == "mid"
    u = nhl_filters({}, {})
    assert set(u.values()) == {"unknown"}
