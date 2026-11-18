"""W118.2 -- NBA depth splits: point-in-time guards, leaf grammar, join coverage stated (EXP-NBADEPTH-001)."""
import pytest

from prediction_market_bot.decision_trees.filters import nba_depth as nd


def _team(pace, net, hwp, rwp, share=None, fg=None):
    share = share or {z: 0.2 for z in nd.ZONES}
    fg = fg or {z: 45.0 for z in nd.ZONES}
    return {"pace": pace, "net_rating": net, "home_wp": hwp, "road_wp": rwp, "zone_off_share": share, "zone_def_fg": fg}


def _prof(n=6, season=2025):
    teams = {f"T{i}": _team(95 + i, i - 3, 0.3 + 0.1 * i, 0.2 + 0.1 * i) for i in range(n)}
    refs = {f"R{i}": {"games": 40, "pts": 215 + i, "fta": 40 + i} for i in range(6)}
    p = {"archive_sha": nd.ARCHIVE_SHA, "season": season, "teams": teams, "name2abbr": {}, "refs": refs}
    p["edges"] = nd._edges(p)
    return p


def test_refuses_same_or_future_season_profile():
    with pytest.raises(nd.PITViolation):
        nd.depth_filters("T0", "T1", _prof(season=2026), row_season=2026)
    with pytest.raises(nd.PITViolation):
        nd.depth_filters("T0", "T1", _prof(season=2027), row_season=2026)


def test_prior_season_leaves_follow_percentiles():
    p = _prof()
    f = nd.depth_filters("T5", "T0", p, row_season=2026)
    assert f["pace_prod@total"] in ("high", "mid", "low")
    assert f["net_rating@side"] == "home_edge"
    assert f["home_road_gap@side"] == "home_edge"
    assert nd.depth_filters("T0", "T5", p, row_season=2026)["net_rating@side"] == "away_edge"
    assert set(f) == set(nd.SPLIT_NAMES)


def test_unknown_team_is_unknown_not_guessed():
    f = nd.depth_filters("ZZZ", "T0", _prof(), row_season=2026)
    assert f["pace_prod@total"] == f["net_rating@side"] == f["shotzone_matchup@side"] == f["home_road_gap@side"] == "unknown"
    assert f["lineup_status"] == f["ref_crew@total"] == "unknown"


def test_lineup_snapshot_after_row_time_is_look_ahead():
    snap = {"status_at_utc": "2026-11-12T20:00:00Z", "away_status": "Confirmed", "home_status": "Confirmed"}
    with pytest.raises(nd.PITViolation):
        nd.lineup_leaf(snap, "2026-11-12T19:59:59+00:00", {})
    assert nd.lineup_leaf(snap, "2026-11-12T20:00:00+00:00", {}) == "confirmed"


def test_lineup_leaves():
    ts = "2026-11-12T21:00:00+00:00"
    base = {"status_at_utc": "2026-11-12T20:00:00Z", "out_list": {"away": ["Star Guy, knee, back Nov 20"], "home": []}}
    assert nd.lineup_leaf({**base, "away_status": "Confirmed", "home_status": "Expected"}, ts, {}) == "mixed"
    assert nd.lineup_leaf({**base, "away_status": "Expected", "home_status": "Expected"}, ts, {"away": {"Other"}}) == "projected_clean"
    assert nd.lineup_leaf({**base, "away_status": "Expected", "home_status": "Expected"}, ts, {"away": {"Star Guy"}}) == "projected_rotation_out"
    assert nd.lineup_leaf(None, ts, {}) == "unknown"


def test_referee_snapshot_look_ahead_and_join_rule():
    p = _prof()
    with pytest.raises(nd.PITViolation):
        nd.ref_leaf(p, ["R0", "R1", "R2"], "2026-11-12T15:00:00Z", "2026-11-12T14:00:00+00:00")
    ts = "2026-11-12T16:00:00+00:00"
    assert nd.ref_leaf(p, ["R5", "R4", "R3"], "2026-11-12T15:00:00Z", ts) == "high"
    assert nd.ref_leaf(p, ["R0", "R1", "R2"], "2026-11-12T15:00:00Z", ts) == "low"
    assert nd.ref_leaf(p, ["R0", "X", "Y"], "2026-11-12T15:00:00Z", ts) == "unknown"  # <2 of 3 join


def test_matchup_value_requires_all_zones():
    t = _team(100, 0, 0.5, 0.5)
    assert nd.matchup_value(t, t) is not None
    t2 = dict(t, zone_def_fg={z: 45.0 for z in nd.ZONES[:-1]})
    assert nd.matchup_value(t, t2) is None


def test_corner_aggregate_only():
    assert nd._zone_of("left corner 3. field goal attempts per game") is None
    assert nd._zone_of("corner 3 field goals attempted") == "corner 3"
    assert nd._zone_of("above the break 3. field goal attempts per game") == "above the break 3"
