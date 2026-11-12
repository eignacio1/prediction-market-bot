import numpy as np
import pandas as pd

from prediction_market_bot.nba_engine import situation_splits as S


def _poss(n_seasons=3, teams=10, per=30, seed=1):
    """Synthetic possession frame already in the module contract. Team T0 scores 1.4/poss in clutch, others 1.0."""
    rng = np.random.default_rng(seed)
    rows, gid = [], 0
    for s in range(2021, 2021 + n_seasons):
        wk = {t: 0 for t in range(teams)}
        for g in range(per):
            ts = rng.permutation(teams)
            for i in range(0, teams, 2):
                gid += 1
                a, b = int(ts[i]), int(ts[i + 1])
                wk[a] += 1; wk[b] += 1
                for off, dfn in ((a, b), (b, a)):
                    for _ in range(40):
                        clutch = rng.random() < 0.25
                        mu = 1.4 if (off == 0 and clutch) else 1.0
                        rows.append(dict(season=s, game_id=gid, off=f"T{off}", dfn=f"T{dfn}", off_week=wk[off], dfn_week=wk[dfn],
                                         points=float(rng.poisson(mu)), margin=float(rng.integers(-3, 4)) if clutch else 20.0,
                                         period=4, secs=100.0 if clutch else 600.0,
                                         off_lineup="a-b-c-d-e", dfn_lineup="f-g-h-i-j"))
    return pd.DataFrame(rows)


CLUTCH = S.Situation("clutch_off_ppp", "points", S.is_clutch, min_n=50)


def test_is_clutch_known_answers():
    f = pd.DataFrame({"period": [4, 4, 3, 4, 5], "secs": [300, 301, 100, 10, 200], "margin": [5, 0, 0, -6, -5]})
    assert list(S.is_clutch(f)) == [True, False, False, False, True]


def test_shot_zone_known_answers():
    assert S.shot_zone(2, 2, 0) == "rim" and S.shot_zone(6, 2, 10) == "paint" and S.shot_zone(15, 2, 80) == "midrange"
    assert S.shot_zone(22, 3, 230) == "corner3" and S.shot_zone(25, 3, 40) == "above_break3"


def test_plays_for_keeps_only_situation_rows_and_value_is_the_inside_rate():
    f = _poss()
    p = S.plays_for(f, CLUTCH)
    assert len(p) == int(S.is_clutch(f).sum()) and (p.bucket == "in").all()
    e = S.build_entry(f, CLUTCH, "T0", 2023, 30)
    assert e["ok"] and 1.2 < e["value"] < 1.6          # planted 1.4 recovered
    assert e["rank_league"] == 1 and e["percentile_history"] > 0.9


def test_point_in_time_never_reads_later_games():
    f = _poss()
    e10 = S.build_entry(f, CLUTCH, "T0", 2023, 10)
    f2 = f.copy()
    f2.loc[(f2.season == 2023) & (f2.off == "T0") & (f2.off_week > 10), "points"] = 99.0   # poison the future
    assert S.build_entry(f2, CLUTCH, "T0", 2023, 10)["value"] == e10["value"]


def test_stability_detects_the_planted_trait_and_not_noise():
    f = _poss(n_seasons=6, teams=12, per=40)
    e = S.build_entry(f, CLUTCH, "T0", 2025, 40)
    assert e["stability"]["ok"]
    noise = S.Situation("late_ppp", "points", lambda d: d.secs > 500, min_n=50)
    en = S.build_entry(f, noise, "T3", 2025, 40)
    assert en["stability"]["ok"] and not en["stability"]["trait"]


def test_frequency_is_share_of_unit_possessions():
    f = _poss()
    q = S.frequency(f, CLUTCH, "T1", 2022, 30)
    assert 0.15 < q["own_share"] < 0.35 and q["own_possessions"] == 30 * 40


def test_cross_adds_both_deviations_and_filter_lets_the_tail_through():
    f = _poss()
    e = S.build_entry(f, CLUTCH, "T0", 2023, 30, opp="T1")
    assert e["cross"]["delta_vs_league"] > 0.1           # T0 clutch offence vs an average defence is above league
    out = S.filter_entries([e, S.build_entry(f, CLUTCH, "T5", 2023, 30)], tail=0.1, min_n=50, require_trait=False)
    assert out[0]["pass"] and not out[1]["pass"]


def test_small_sample_is_unranked_not_guessed():
    e = S.build_entry(_poss(), S.Situation("x", "points", S.is_clutch, min_n=10**6), "T0", 2023, 30)
    assert e["ok"] is False


def test_possession_frame_forward_fills_blank_pbp_scores_and_signs_margin_by_side():
    poss = pd.DataFrame({"game_id": ["g"] * 3, "period": [1, 1, 1], "start_order_index": [1, 3, 5], "start_seconds_remaining": [700., 600., 500.],
                         "offense_team_id": [10, 20, 10], "defense_team_id": [20, 10, 20], "points": [2, 0, 3], "count_as_possession": [True] * 3,
                         "season": [2025] * 3, **{f"off_player_{i}": [i] * 3 for i in range(1, 6)}, **{f"def_player_{i}": [i + 5] * 3 for i in range(1, 6)}})
    pbp = pd.DataFrame({"game_id": ["g"] * 5, "order_index": [1, 2, 3, 4, 5], "score_home": ["0", "2", "", "", "5"], "score_away": ["0", "0", "", "", "0"]})
    games = pd.DataFrame({"game_id": ["g"], "season": [2025], "date": ["2025-10-22"], "home_team_id": [10], "away_team_id": [20]})
    f = S.possession_frame(poss, pbp, games)
    assert list(f.margin) == [0, -2, 5]          # home 10: 0; then away offence sees home +2 as -2; then home +5
    assert list(f.off_week) == [1, 1, 1] and f.off_lineup.iloc[0] == "1-2-3-4-5"
