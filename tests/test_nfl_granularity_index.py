"""W80.3: granularity-index machine. Point-in-time positive control, rank hand-check, cross symmetry."""
import numpy as np
import pandas as pd
import pytest

from prediction_market_bot.nfl_engine import granularity_index as gi

SPEC = gi.SplitSpec(unit="posteam", by="box", metric="success", min_n=1)


def _plays(rows):
    return pd.DataFrame(rows, columns=["season", "week", "game_id", "posteam", "box", "success"])


def _mk():
    # team A: weeks 1-3 light box, success 1,0 / 1,1 / 0,0 ; week 4 all success (the "future")
    r = []
    for wk, vals in {1: [1, 0], 2: [1, 1], 3: [0, 0], 4: [1, 1]}.items():
        for v in vals:
            r.append((2025, wk, f"g{wk}", "A", "light", v))
    return _plays(r)


def test_split_point_in_time_week_reads_earlier_weeks_only():
    p = _mk()
    s = gi.split(p, SPEC, season=2025, before_week=4)
    assert int(s.n.iloc[0]) == 6 and s.value.iloc[0] == pytest.approx(3 / 6)


def test_leaky_variant_is_detected():
    """Positive control: reading through week 4 changes the week-4 value, so a pipeline that does so leaks."""
    p = _mk()
    clean = gi.split(p, SPEC, season=2025, before_week=4).value.iloc[0]
    leaky = gi.split(p, SPEC, season=2025, before_week=5).value.iloc[0]
    assert leaky != clean


def test_games_cut_uses_unit_game_number():
    s = gi.split(_mk(), SPEC, season=2025, games=2)
    assert int(s.n.iloc[0]) == 4 and s.value.iloc[0] == pytest.approx(3 / 4)


def test_rank_hand_computed():
    rows = []
    for season, team, v in [(2024, "A", 0.5), (2024, "B", 0.7), (2025, "A", 0.6), (2025, "B", 0.4), (2025, "C", 0.9)]:
        for i in range(10):  # 10 plays in one game
            rows.append((season, 1, f"{season}{team}", team, "light", 1 if i < round(v * 10) else 0))
    p = _plays(rows)
    spec = gi.SplitSpec("posteam", "box", "success", True, min_n=5)
    r = gi.rank(p, spec, "A", "light", 2025, games=1)
    assert r["rank_league"] == 2 and r["of_league"] == 3          # C .9 > A .6 > B .4
    assert r["rank_history"] == 3 and r["of_history"] == 5        # .9, .7, then .6
    assert r["percentile_history"] == pytest.approx(1 - 2 / 4)


def test_rank_direction_flag():
    p = _plays([(2025, 1, "g1", "A", "x", 1)] * 6 + [(2025, 1, "g2", "B", "x", 0)] * 6)
    lo = gi.SplitSpec("posteam", "box", "success", False, min_n=1)
    assert gi.rank(p, lo, "A", "x", 2025, 1)["rank_league"] == 2


def test_cross_symmetric_in_roles():
    league = {"L": 0.5, "H": 0.5}
    k = {"L": 20.0, "H": 20.0}
    freq = {"L": 0.6, "H": 0.4}
    a = {"L": (100, 60.0), "H": (50, 20.0)}
    b = {"L": (80, 30.0), "H": (60, 33.0)}
    x = gi.cross(a, b, league, freq, k).expected
    y = gi.cross(b, a, league, freq, k).expected
    assert x == pytest.approx(y)


def test_cross_no_data_returns_league_and_delta_zero():
    r = gi.cross({}, {}, {"L": 0.45}, {"L": 1.0}, {"L": 10.0})
    assert r.expected == pytest.approx(0.45) and r.delta == 0.0


def test_show_frequency_normalised_and_neutral():
    f = gi.show_frequency({"L": .5, "H": .5}, {"L": .5, "H": .5}, {"L": .5, "H": .5})
    assert f == {"L": pytest.approx(.5), "H": pytest.approx(.5)}
    f2 = gi.show_frequency({"L": .8, "H": .2}, {"L": .5, "H": .5}, {"L": .5, "H": .5})
    assert sum(f2.values()) == pytest.approx(1) and f2["L"] > .5


def test_stability_trait_vs_noise():
    rng = np.random.default_rng(1)
    rows = []
    for s in range(2022, 2026):
        for t in range(32):
            talent = rng.normal(0, .15)
            for g in range(1, 9):
                for _ in range(8):
                    rows.append((s, g, f"{s}{t}{g}", f"T{t}", "x", int(rng.random() < .45 + talent)))
    sig = gi.stability(_plays(rows), SPEC, "x", games=8)
    assert sig["ok"] and sig["trait"]
    for i, r in enumerate(rows):  # shuffle outcomes: no talent
        rows[i] = r[:5] + (int(rng.random() < .45),)
    noise = gi.stability(_plays(rows), SPEC, "x", games=8)
    assert noise["ok"] and not noise["trait"]


def test_market_map_joins_inventory():
    inv = {"KXNFLRSHYDS": {"events": 285, "open_now": 3, "settled_since_floor": 9083}}
    m = gi.market_map("rush_success", inv)
    f = {x["family"]: x for x in m}
    assert f["KXNFLRSHYDS"]["settled_since_floor"] == 9083 and f["KXNFLSPREAD"]["events"] is None


def test_filter_entries_median_fails_tail_passes():
    es = [{"ok": True, "n_plays": 100, "percentile_history": 0.5, "stability": {"trait": True}},
          {"ok": True, "n_plays": 100, "percentile_history": 0.97, "stability": {"trait": True}},
          {"ok": True, "n_plays": 100, "percentile_history": 0.97, "stability": {"trait": False}},
          {"ok": True, "n_plays": 10, "percentile_history": 0.99, "stability": {"trait": True}}]
    assert [e["pass"] for e in gi.filter_entries(es)] == [False, True, False, False]
