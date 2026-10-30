"""W97.4 Part A: point-in-time contract and known-answer recovery for the NHL engine inputs."""
import numpy as np
import pandas as pd

from prediction_market_bot.nhl_engine import inputs as I


def _league(n_teams=12, n_days=160, seed=0, att=None, dfn=None):
    """Synthetic team-game table: team t has true 5v5 xG-for rate exp(att[t]) and against rate exp(dfn[t]) per 60."""
    rng = np.random.default_rng(seed)
    att = rng.normal(0, 0.15, n_teams) if att is None else att
    dfn = rng.normal(0, 0.15, n_teams) if dfn is None else dfn
    rows, gid = [], 1
    t0 = pd.Timestamp("2022-10-10", tz="UTC")
    for d in range(n_days):
        perm = rng.permutation(n_teams)
        for i in range(0, n_teams, 2):
            h, a = int(perm[i]), int(perm[i + 1])
            sec = 3000.0
            for me, op, ih in ((h, a, True), (a, h, False)):
                mu = 2.4 * np.exp(att[me] + dfn[op]) * sec / 3600
                mu_against = 2.4 * np.exp(att[op] + dfn[me]) * sec / 3600
                rows.append(dict(game_id=gid, season=2022, game_type=2, start_time_utc="x", is_home=ih, team=f"T{me}", team_id=me,
                                 opp=f"T{op}", s5v5=sec, spp=300.0, spk=300.0, xf5=rng.poisson(mu * 20) / 20, xfpp=0.4, xfpk=0.05,
                                 xa5=rng.poisson(mu_against * 20) / 20, xa_on_our_pk=0.4, xa_on_our_pp=0.05, reg_goals=0.0,
                                 start=t0 + pd.Timedelta(days=d, hours=1 if ih else 1)))
            gid += 1
    return pd.DataFrame(rows), att, dfn


def _gs(tg):
    return pd.DataFrame({"game_id": tg["game_id"], "team_id": tg["team_id"], "prev_gsax_per_shot": 0.0})


def test_leakage_a_games_own_outcome_and_all_later_games_cannot_change_its_features():
    tg, _, _ = _league()
    base = I.game_features(tg, _gs(tg))
    rng = np.random.default_rng(3)
    for gid in rng.choice(tg["game_id"].unique(), size=15, replace=False):
        cut = tg.loc[tg["game_id"] == gid, "start"].iloc[0]
        bad = tg.copy()
        m = bad["start"] >= cut                      # this game and everything after it
        for c in ("xf5", "xa5", "xfpp", "xa_on_our_pk", "reg_goals", "s5v5", "spp", "spk"):
            bad.loc[m, c] = 1e6                      # poison every outcome column
        alt = I.game_features(bad, _gs(bad))
        a = base[base["game_id"] == gid].drop(columns=["start"]).iloc[0]
        b = alt[alt["game_id"] == gid].drop(columns=["start"]).iloc[0]
        keep = [c for c in a.index]
        pd.testing.assert_series_equal(a[keep].astype(float), b[keep].astype(float), check_names=False)


def test_known_answer_league_strengths_recovered():
    tg, att, dfn = _league(n_days=200, seed=1, att=np.linspace(-0.25, 0.25, 12), dfn=np.linspace(0.25, -0.25, 12))
    f = I.game_features(tg, _gs(tg), half_life=1000.0, prior_sec=3 * 3600.0)
    last = f.iloc[-60:]
    long = pd.concat([
        pd.DataFrame({"team": last["team_id_h"], "f5": last["f5_h"], "a5": last["a5_h"]}),
        pd.DataFrame({"team": last["team_id_a"], "f5": last["f5_a"], "a5": last["a5_a"]})]).groupby("team").mean()
    assert np.corrcoef(long["f5"], np.exp(att[long.index.to_numpy()]))[0, 1] > 0.9
    assert np.corrcoef(long["a5"], np.exp(dfn[long.index.to_numpy()]))[0, 1] > 0.9


def test_shrinkage_with_no_history_equals_league_rate():
    r = I.decayed_shrunk_rates(np.array([1, 1, 2]), np.array([5.0, 5.0, 5.0]), np.array([10.0, 10.0, 10.0]), 40.0, 100.0, 0.3)
    assert r[0] == 0.3 and abs(r[2] - 0.3) < 1e-12 and r[1] > 0.3 - 1e-12


def test_rate_reads_before_folding():
    r = I.decayed_shrunk_rates(np.array([1, 1]), np.array([1e9, 0.0]), np.array([1.0, 1.0]), 40.0, 1.0, 0.0)
    assert r[0] == 0.0 and r[1] > 1e6


def test_game_features_have_no_outcome_column():
    tg, _, _ = _league(n_days=5)
    f = I.game_features(tg, _gs(tg))
    assert not any(c.startswith("reg_goals") for c in f.columns)
