from prediction_market_bot.archive_intake import nba_distance_filters as df


def test_filters_cover_every_entry_both_ways():
    out = df.distance_filters({n: 0.9 for n in df.HIGHER_IS_BETTER}, {n: 0.1 for n in df.HIGHER_IS_BETTER})
    assert len(out) == 2 * len(df.HIGHER_IS_BETTER) == 24
    assert out["opp_fg_pct_lt5@total"] == "mid"
    # lower allowed is better: the away team (low percentile) is the better defence
    assert out["opp_fg_pct_lt5@side"] == "away_edge"


def test_missing_percentile_is_unknown():
    out = df.distance_filters({}, {"opp_fg_pct_lt5": 0.5})
    assert out["opp_fg_pct_lt5@total"] == "unknown" and out["opp_fg_pct_lt5@side"] == "unknown"
