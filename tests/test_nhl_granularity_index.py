"""W109.2 -- NHL granularity index (rest-state split): known answers and point-in-time."""
import numpy as np
import pandas as pd

from prediction_market_bot.nhl_engine import granularity_index as gi


def _frame(n_games=82, n_teams=8, seasons=(2022, 2023), seed=0, b2b_effect=0.0, shift_after=None):
    """Round-robin-ish synthetic frame. Home/away reg goals ~ Poisson(3) (+ b2b_effect for a team on a back-to-back)."""
    rng = np.random.default_rng(seed)
    rows, gid = [], 0
    for s in seasons:
        t0 = pd.Timestamp(f"{s}-10-10")
        rest = {t: 3.0 for t in range(n_teams)}
        for g in range(n_games * n_teams // 2):
            h, a = rng.choice(n_teams, 2, replace=False)
            day = t0 + pd.Timedelta(days=g // 4)
            rh = 1.0 if rng.random() < 0.3 else 3.0
            ra = 1.0 if rng.random() < 0.3 else 3.0
            lh = 3.0 + (b2b_effect if rh < 1.5 else 0.0)
            la = 3.0 + (b2b_effect if ra < 1.5 else 0.0)
            gid += 1
            rows.append({"game_id": gid, "season": s, "start": day + pd.Timedelta(minutes=g), "team_id_h": int(h), "team_id_a": int(a),
                         "rest_h": rh, "rest_a": ra, "reg_h": float(rng.poisson(lh)), "reg_a": float(rng.poisson(la))})
    return pd.DataFrame(rows)


def test_team_games_shape_and_game_no():
    fr = _frame(n_games=20, n_teams=4, seasons=(2022,))
    tg = gi.team_games(fr)
    assert len(tg) == 2 * len(fr)
    assert (tg["total"] == tg["gf"] + tg["ga"]).all()
    assert tg.groupby("team")["game_no"].max().sum() == len(tg)
    assert (tg.groupby("team")["game_no"].min() == 1).all()


def test_planted_b2b_effect_is_recovered_by_split():
    fr = _frame(n_games=160, n_teams=6, seasons=(2022,), b2b_effect=-0.8, seed=3)
    tg = gi.team_games(fr)
    d = gi.asof_split(tg, "gf", k=0.0)
    late = d[(d["game_no"] > 100) & (d["b2b"] == 1)]
    assert abs(late["delta_raw_gf"].mean() - (-0.8 * 0.7)) < 0.15   # planted -0.8 on b2b (share 0.3): bucket-minus-all mean = -0.56
    null = gi.asof_split(gi.team_games(_frame(n_games=160, n_teams=6, seasons=(2022,), seed=3)), "gf", k=0.0)
    nl = null[(null["game_no"] > 100) & (null["b2b"] == 1)]
    assert abs(nl["delta_raw_gf"].mean()) < 0.25                # no plant, no effect


def test_shrinkage_pulls_small_buckets_to_zero():
    tg = gi.team_games(_frame(n_games=30, n_teams=4, seasons=(2022,), b2b_effect=-1.0, seed=1))
    d0, d1 = gi.asof_split(tg, "gf", k=0.0), gi.asof_split(tg, "gf", k=50.0)
    assert (d1["delta_gf"].abs() <= d0["delta_gf"].abs() + 1e-12).all()
    first = d1[d1["game_no"] == 1]
    assert (first["delta_gf"] == 0).all()                       # nothing earlier -> no shift


def test_split_is_point_in_time_future_game_does_not_change_earlier_rows():
    fr = _frame(n_games=60, n_teams=4, seasons=(2022,), seed=2)
    a = gi.asof_split(gi.team_games(fr), "gf")
    fr2 = fr.copy()
    last = fr2["start"].idxmax()
    fr2.loc[last, ["reg_h", "reg_a"]] = 40.0                    # corrupt the very last game
    b = gi.asof_split(gi.team_games(fr2), "gf")
    ka = a.sort_values(["game_id", "is_home"]).reset_index(drop=True); kb = b.sort_values(["game_id", "is_home"]).reset_index(drop=True)
    gid = fr.loc[last, "game_id"]
    m = ka["game_id"] != gid
    assert np.allclose(ka.loc[m, "delta_gf"], kb.loc[m, "delta_gf"])
    assert np.allclose(ka.loc[m, "n_b_gf"], kb.loc[m, "n_b_gf"])


def test_rank_vs_history_uses_only_earlier_seasons():
    tg = gi.team_games(_frame(n_games=82, n_teams=8, seasons=(2022, 2023), b2b_effect=-0.5, seed=4))
    d = gi.asof_split(tg, "gf")
    r = gi.rank_vs_history(d, "delta_gf")
    s22 = d["season"].to_numpy() == 2022
    assert np.isnan(r.to_numpy()[s22]).all()                    # the first season has no history
    assert np.nanmin(r.to_numpy()) >= 0 and np.nanmax(r.to_numpy()) <= 1


def test_stability_detects_planted_effect_and_not_null():
    # team-specific planted effects: some teams suffer on b2b, some do not -> split-half reliability > 0
    rng = np.random.default_rng(7)
    rows = []
    for s in range(2020, 2026):
        for t in range(30):
            eff = -1.0 if t % 2 == 0 else 0.0
            for g in range(1, 83):
                b2b = int(rng.random() < 0.2)
                rows.append({"team": t, "season": s, "game_no": g, "b2b": b2b, "gf": float(rng.poisson(3.0 + eff * b2b))})
    tg = pd.DataFrame(rows)
    st = gi.stability(tg, "gf")
    assert st["sb"] > 0.4 and st["lo"] > 0
    tg["gf"] = rng.poisson(3.0, len(tg)).astype(float)         # null: no team-specific effect
    sn = gi.stability(tg, "gf")
    assert sn["lo"] < 0.2 and sn["lo"] <= sn["sb"] <= sn["hi"]


def test_game_cross_adds_own_offence_and_opponent_defence():
    fr = pd.DataFrame({"game_id": [1], "team_id_h": [10], "team_id_a": [20]})
    base = {"b2b": 1, "n_b_gf": 10.0}
    gf = pd.DataFrame([{**base, "game_id": 1, "is_home": 1, "delta_gf": -0.2}, {**base, "game_id": 1, "is_home": 0, "delta_gf": -0.4}])
    ga = pd.DataFrame([{**base, "game_id": 1, "is_home": 1, "delta_ga": 0.5}, {**base, "game_id": 1, "is_home": 0, "delta_ga": 0.1}])
    x = gi.game_cross(fr, gf, ga)
    assert np.isclose(x.loc[0, "shift_h"], -0.2 + 0.1)          # home offence + road defence
    assert np.isclose(x.loc[0, "shift_a"], -0.4 + 0.5)          # road offence + home defence
    assert np.isclose(x.loc[0, "shift_total"], x.loc[0, "shift_h"] + x.loc[0, "shift_a"])


def test_filter_gate_and_min_n():
    x = pd.DataFrame({"shift_total": [0.5, -0.5, 0.01], "min_n_b": [10.0, 2.0, 10.0]})
    assert len(gi.filter_entries(x, stable=False)) == 0         # failed stability gate passes nothing
    assert list(gi.filter_entries(x, stable=True, min_n=5.0, tail=0.1).index) == [0]


def test_fit_shift_weight_known_answer_and_apply():
    rng = np.random.default_rng(0)
    s = rng.normal(0, 0.3, 5000)
    r = 0.6 * s + rng.normal(0, 1.0, 5000)
    assert abs(gi.fit_shift_weight(s, r) - 0.6) < 0.1
    assert gi.fit_shift_weight(s, -r) == 0.0                    # wrong sign is not applied
    lh, la = gi.apply_shift(np.array([3.0]), np.array([0.4]), np.array([0.5]), np.array([-1.0]), 1.0)
    assert np.isclose(lh[0], 3.5) and np.isclose(la[0], 0.3)    # floor
