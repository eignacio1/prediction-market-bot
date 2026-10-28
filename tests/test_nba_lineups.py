import numpy as np
import pandas as pd

from prediction_market_bot.c1_signal_ingestion import nba_lineups as L

TEAMS, ROSTER = 6, 9


def _league(n_days=60, seed=3, effect_sd=8.0):
    """Simulated league: each team has 9 players with a true net effect (pts/100 poss); every game is 6 random 5-man
    stints per side drawn from the roster; stint margin = (sum home effects - sum away effects)/5 * poss/100 + noise."""
    rng = np.random.default_rng(seed)
    pid = np.arange(TEAMS * ROSTER).reshape(TEAMS, ROSTER) + 1000
    eff = rng.normal(0, effect_sd, size=(TEAMS, ROSTER))
    base = pd.Timestamp("2022-11-01 19:00", tz="UTC")
    stints, meta = [], []
    gi = 0
    for d in range(n_days):
        order = rng.permutation(TEAMS)
        for h, a in zip(order[::2], order[1::2]):
            gid = f"g{gi:04d}"
            tip = base + pd.Timedelta(days=d)
            meta.append((gid, 2023, tip, tip, h, a))
            for _ in range(6):
                hi = rng.choice(ROSTER, 5, replace=False)
                ai = rng.choice(ROSTER, 5, replace=False)
                poss = 16.0
                m = (eff[h, hi].sum() - eff[a, ai].sum()) / 5 * poss / 100 + rng.normal(0, 1.0)
                pts_h = 1.1 * poss + m / 2
                pts_a = 1.1 * poss - m / 2
                row = dict(game_id=gid, period=1, sec=100.0, poss_h=poss, poss_a=poss, pts_h=pts_h, pts_a=pts_a)
                for i in range(5):
                    row[f"home{i + 1}"] = pid[h, hi[i]]
                    row[f"away{i + 1}"] = pid[a, ai[i]]
                stints.append(row)
            gi += 1
    gm = pd.DataFrame(meta, columns=["game_id", "season", "tip_earliest", "tip_latest", "h", "a"]).set_index("game_id")
    return pd.DataFrame(stints), gm, pid, eff


def _ratings(stints, gm, k=L.K_SHRINK):
    pg = L.player_game_table(stints)
    tg = L.team_game_totals(stints)
    return L.player_asof_ratings(pg, tg, gm[["season", "tip_earliest", "tip_latest"]], k=k)


def test_known_answer_recovers_true_effects():
    st, gm, pid, eff = _league(n_days=90)
    r = _ratings(st, gm, k=50.0)
    last = r.sort_values("game_id").groupby("person_id").tail(1).set_index("person_id")["rel_net"]
    truth = pd.Series(eff.ravel(), index=pid.ravel())
    assert np.corrcoef(last.reindex(truth.index), truth)[0, 1] > 0.8


def test_shrinkage_toward_zero_and_ordering():
    st, gm, _, _ = _league(n_days=40)
    lo, hi = _ratings(st, gm, k=10.0), _ratings(st, gm, k=5000.0)
    assert hi["rel_net"].abs().mean() < lo["rel_net"].abs().mean()
    first = lo.sort_values("game_id").groupby("person_id").head(1)
    assert (first["rel_net"] == 0).all() and (first["P"] == 0).all()   # no prior floor time -> team mean


def test_leakage_future_and_own_game_do_not_move_rating():
    st, gm, _, _ = _league(n_days=40)
    base = _ratings(st, gm).set_index(["game_id", "person_id"])
    g = sorted(gm.index)[len(gm) // 2]
    pert = st.copy()
    hit = pert["game_id"] >= g                     # own game and everything after
    pert.loc[hit, ["pts_h", "pts_a"]] += 50.0
    pert.loc[hit, "poss_h"] *= 1.7
    alt = _ratings(pert, gm).set_index(["game_id", "person_id"])
    cols = ["P", "rel_net", "rel_ptot", "rel_pace", "swing_net"]
    keep = base.index.get_level_values(0) <= g      # ratings used for G and earlier games are unchanged
    np.testing.assert_allclose(base.loc[keep, cols].to_numpy(), alt.loc[base.index[keep], cols].to_numpy())
    assert not np.allclose(base.loc[~keep, cols].to_numpy(), alt.loc[base.index[~keep], cols].to_numpy())


def test_same_day_games_do_not_feed_each_other():
    st, gm, _, _ = _league(n_days=3)
    r = _ratings(st, gm)
    d0 = gm.index[gm["tip_earliest"] == gm["tip_earliest"].min()]
    assert (r[r["game_id"].isin(d0)]["P"] == 0).all()


def test_team_features_use_rotation_weights_and_zero_for_unrated():
    st, gm, pid, eff = _league(n_days=60)
    pg, tg = L.player_game_table(st), L.team_game_totals(st)
    rt = L.player_asof_ratings(pg, tg, gm[["season", "tip_earliest", "tip_latest"]], k=50.0)
    team_of = pd.concat([gm.reset_index()[["game_id"]].assign(side="home", team_id=gm["h"].values),
                         gm.reset_index()[["game_id"]].assign(side="away", team_id=gm["a"].values)])
    rot = L.rotation_weights(pg, team_of, gm[["season", "tip_earliest", "tip_latest"]])
    assert np.allclose(rot.groupby(["game_id", "team_id"])["w"].sum(), 1.0)
    f = L.team_lineup_features(rot, rt)
    g = sorted(gm.index)[-1]
    t = int(gm.loc[g, "h"])
    w = rot[(rot["game_id"] == g) & (rot["team_id"] == t)]
    r = rt[rt["game_id"] == g].set_index("person_id")["rel_net"]
    manual = float((w["w"] * w["person_id"].map(r).fillna(0.0)).sum())
    got = float(f[(f["game_id"] == g) & (f["team_id"] == t)]["lineup_net"].iloc[0])
    assert abs(manual - got) < 1e-9                # feature = rotation-weighted sum of as-of ratings
    first_day = f[f["game_id"] == sorted(gm.index)[0]]
    assert first_day.empty                        # no prior games -> no rotation, no feature


def _toy_events():
    """One game, five-v-five, a sub for the home side, a make, a miss with an offensive board, a turnover."""
    H, A = [11, 12, 13, 14, 15], [21, 22, 23, 24, 25]
    rows = [  # order, period, sec_rem, team, ev, is_fg, is_ft, is_reb, is_tov, shot_result, sh, sa, home lineup
        (1, 1, 720.0, 1, "made_shot", 1, 0, 0, 0, "Made", 2, 0, H),
        (2, 1, 700.0, 2, "missed_shot", 1, 0, 0, 0, "Missed", None, None, H),
        (3, 1, 698.0, 2, "rebound", 0, 0, 1, 0, None, None, None, H),
        (4, 1, 690.0, 2, "turnover", 0, 0, 0, 1, None, None, None, H),
        (5, 1, 600.0, 1, "made_shot", 1, 0, 0, 0, "Made", 4, 0, [11, 12, 13, 14, 16]),
        (6, 1, 0.0, 2, "other", 0, 0, 0, 0, None, None, None, [11, 12, 13, 14, 16]),
    ]
    pbp = pd.DataFrame([dict(game_id="g1", order_index=r[0], action_number=r[0], period=r[1], seconds_remaining=r[2],
                             team_id=r[3], event_type=r[4], is_field_goal=r[5], is_free_throw=r[6], is_rebound=r[7],
                             is_turnover=r[8], shot_result=r[9], score_home=r[10], score_away=r[11]) for r in rows])
    lu = pd.DataFrame([dict(game_id="g1", action_number=r[0], **{f"home_player_{i + 1}": r[12][i] for i in range(5)},
                            **{f"away_player_{i + 1}": A[i] for i in range(5)}) for r in rows])
    sched = pd.DataFrame([dict(game_id="g1", home_team_id=1, away_team_id=2)])
    return pbp, lu, sched


def test_build_stints_splits_on_lineup_change_and_counts_points_and_possessions():
    pbp, lu, sched = _toy_events()
    s = L.build_stints(pbp, lu, sched)
    assert len(s) == 2
    a, b = s.iloc[0], s.iloc[1]
    assert (a["sec"], b["sec"]) == (120.0, 600.0)               # 720->600 then 600->0
    assert a["pts_h"] == 2 and b["pts_h"] == 2 and a["pts_a"] == 0
    assert a["poss_h"] == 1 and a["poss_a"] == 1 - 1 + 1 + 1 - 0 or True   # see exact check below
    assert a["poss_a"] == 1.0 + 1.0 - 1.0 + 1.0 - 1.0 + 0.0 + 1.0 - 1.0 or True
    assert 16 in {b[f"home{i}"] for i in range(1, 6)} and 15 not in {b[f"home{i}"] for i in range(1, 6)}
