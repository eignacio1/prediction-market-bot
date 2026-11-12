from prediction_market_bot.nba_engine import filters as f


def test_total_leaf_terciles():
    assert f.total_leaf(0.9, 0.8) == "high" and f.total_leaf(0.1, 0.2) == "low" and f.total_leaf(0.5, 0.5) == "mid"
    assert f.total_leaf(None, 0.5) == "unknown"


def test_side_leaf_direction_flips_for_lower_is_better():
    assert f.side_leaf("clutch_offence_ppp", 0.9, 0.1) == "home_edge"
    assert f.side_leaf("turnover_rate", 0.9, 0.1) == "away_edge"      # high turnover rate is bad for home
    assert f.side_leaf("turnover_rate", 0.5, 0.45) == "neutral"
    assert f.side_leaf("nope", 0.9, 0.1) == "unknown"


def test_nba_filters_keys_and_missing():
    out = f.nba_filters({"pace_after_made_shot": 0.9}, {"pace_after_made_shot": 0.9})
    assert out["pace_after_made_shot@total"] == "high"
    assert out["turnover_rate@total"] == "unknown" and len(out) == 2 * len(f.HIGHER_IS_BETTER)
