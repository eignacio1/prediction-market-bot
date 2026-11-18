"""W117.3 Part A: NBA moneyline + team totals from the engine's own game simulation."""
import math

from prediction_market_bot.nba_engine import engine as E
from prediction_market_bot.nba_engine import ml_team_total as M

N = 100_000


def _sample(ppp_h=115.0, ppp_a=110.0, hca=2.0, seed=7):
    return E.simulate(mu_poss=99.0, ppp_h=ppp_h, ppp_a=ppp_a, hca=hca, s_p=3.0, s_e=11.0, n=N, seed=seed)


def test_moneyline_agrees_with_spread_implied_within_stated_tolerance():
    for ppp_h, ppp_a in ((115, 110), (110, 110), (108, 116)):
        s = _sample(ppp_h, ppp_a)
        p = M.price_moneyline_and_team_totals(s, [100], [100])
        assert abs(p["home_win"] - M.spread_implied_home_win(s)) <= M.SPREAD_IMPLIED_TOL
        assert abs(p["home_win"] + p["away_win"] - 1.0) < 1e-12  # no push: the engine breaks residual ties


def test_team_totals_are_consistent_with_the_game_total():
    s = _sample()
    p = M.price_moneyline_and_team_totals(s, range(95, 135, 5), range(90, 130, 5))
    c = M.consistency_checks(s, p)
    assert c["team_means_vs_total_gap"] < 1e-9 and c["win_sum_gap"] < 1e-12 and c["ladder_monotone_violations"] == 0
    # the same draws: home + away points are the game total, draw by draw
    assert (s.home_pts + s.away_pts == s.total).all()


def test_planted_case_recovers_the_price():
    # plant: even teams, no home edge -> ML 0.5; plant a +6.0 pts/100 edge -> ML must move to the normal-margin price
    even = M.price_moneyline_and_team_totals(_sample(112, 112, 0.0), [100], [100])
    assert abs(even["home_win"] - 0.5) < 0.01
    planted = _sample(118, 112, 0.0)
    p = M.price_moneyline_and_team_totals(planted, [100], [100])
    exp_margin = 99.0 * (118 - 112) / 100.0  # planted mean margin
    assert abs(float(planted.margin.mean()) - exp_margin) < 0.3
    # tolerance 1.0 pt: tied games go to overtime in the engine, adding ~0.4 pts per team over the regulation plant
    assert abs(p["mean_home"] - 99.0 * 118 / 100.0) < 1.0 and abs(p["mean_away"] - 99.0 * 112 / 100.0) < 1.0
    sd = float(planted.margin.std())
    want = 0.5 * math.erfc((0.5 - exp_margin) / (sd * math.sqrt(2)))
    assert abs(p["home_win"] - want) < M.SPREAD_IMPLIED_TOL


# --- Part B: layer 1 and layer 3 read from box rows (GG-1951) and the approved stump rule ---
from prediction_market_bot.decision_trees import coverage  # noqa: E402


def _row(mt, p=0.5, kept=(), logged=()):
    return {"market_type": mt, "band": "T1", "p_yes": p, "router": {"split_kept": list(kept), "split_logged_only": list(logged)}}


def test_stump_counts_tested_splits_kept_or_not_and_kept_is_reported_apart():
    ev = coverage.ledger_evidence([_row("NBA_SPREAD", kept=["f"]), _row("NBA_TOTAL", logged=["g"]), _row("NBA_ML", p=None)])
    rows = [{"market_type": m, "band": "T1", "sport": "NBA"} for m in ("NBA_SPREAD", "NBA_TOTAL", "NBA_ML")]
    cs = {c["market_type"]: c for c in coverage.d6_layers({"leaves": {}}, rows, {"splits": []}, set(), box_evidence=ev)}
    assert cs["NBA_SPREAD"]["layers"][2] and cs["NBA_SPREAD"]["l3_kept"]
    assert cs["NBA_TOTAL"]["layers"][2] and not cs["NBA_TOTAL"]["l3_kept"]      # stump only
    assert not cs["NBA_ML"]["layers"][2] and not cs["NBA_ML"]["layers"][0]      # no tested split, no logged p
    assert cs["NBA_SPREAD"]["layers"][0]                                         # layer 1 from the logged model p on box rows
    s = coverage.d6_summary(list(cs.values()))["by_sport"]["NBA"]
    assert s["l3_stump"] == 2 and s["l3_kept"] == 1


def test_split_file_is_not_layer_3_evidence_when_box_rows_are_supplied():
    splits = {"splits": [{"sport": "NBA", "series": None, "kept": True}]}
    rows = [{"market_type": "NBA_SPREAD", "band": "T1", "sport": "NBA"}]
    c = coverage.d6_layers({"leaves": {"NBA|NBA_SPREAD|T1|2|na": {"thin": False, "arm": "RIDE", "fit": {}}}}, rows, splits, {"nba"},
                           box_evidence={})[0]
    assert not c["layers"][2]
