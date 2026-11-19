"""W119.2 -- NBA depth wired into the shadow path behind PM_LEAF_MAP_VERSION=...+nba_depth (EXP-NBADEPTH-001)."""
import json

import pytest

from prediction_market_bot.decision_trees import filter_supply as fs
from prediction_market_bot.decision_trees import leaf_map as lm
from prediction_market_bot.decision_trees import shadow_route as sr
from prediction_market_bot.decision_trees.filters import nba_depth as nd


def _prof(season=2025):
    teams = {t: {"pace": 95 + i, "net_rating": i - 3, "home_wp": 0.3 + 0.1 * i, "road_wp": 0.2 + 0.1 * i,
                 "zone_off_share": {z: 0.2 for z in nd.ZONES}, "zone_def_fg": {z: 45.0 for z in nd.ZONES}}
             for i, t in enumerate(["ATL", "BOS", "CHI", "DAL", "DEN", "DET"])}
    p = {"archive_sha": nd.ARCHIVE_SHA, "season": season, "teams": teams, "name2abbr": {}, "refs": {}}
    p["edges"] = nd._edges(p)
    return p


ROW = {"sport": "NBA", "event_ticker": "KXNBAGAME-26NOV19ATLBOS", "ts_utc": "2026-11-19T00:00:00Z"}


def test_shipped_profiles_pin_the_archive_sha_and_prior_season():
    p = fs.nba_depth_profiles()
    assert p["archive_sha"] == nd.ARCHIVE_SHA == "bafaeef4de9596fd7a69941b36ca16a34af2f344"
    assert p["season"] == nd.PRIOR_SEASON and len(p["teams"]) == 30


def test_depth_fields_present_with_pinned_sha_and_s3_s5_logged_not_split():
    d, note = fs.nba_depth_adapter(ROW, _prof())
    assert note is None and d["archive_sha"] == nd.ARCHIVE_SHA and d["season"] == 2025
    assert set(d["leaves"]) == {"pace_prod@total", "net_rating@side", "shotzone_matchup@total", "shotzone_matchup@side",
                                "home_road_gap@side"}
    assert set(d["logged_only"]) == {"lineup_status", "ref_crew@total"}


def test_no_look_ahead_same_or_later_season_profile_refused():
    with pytest.raises(fs.PITViolation):
        fs.nba_depth_adapter(ROW, _prof(season=2026))
    s = fs.FilterSupply(depth_profiles=_prof(season=2026))
    assert s.depth_for_row(ROW) is None                      # supply swallows it: no depth rather than future depth
    early = {**ROW, "ts_utc": "2026-03-01T00:00:00Z"}        # a 2025-26 row against the 2025-26 profile
    assert fs.FilterSupply(depth_profiles=_prof()).depth_for_row(early) is None


def test_snapshot_after_row_is_refused():
    snap = {"status_at_utc": "2026-11-19T06:00:00Z", "away_status": "Confirmed", "home_status": "Confirmed"}
    with pytest.raises(fs.PITViolation):
        fs.nba_depth_adapter(ROW, _prof(), lineup_snap=snap, rotation={})


def test_non_nba_rows_have_no_depth():
    assert fs.FilterSupply().depth_for_row({"sport": "NHL"}) is None


def test_switch_parsing(monkeypatch):
    monkeypatch.delenv("PM_LEAF_MAP_VERSION", raising=False)
    assert not lm.depth_enabled() and lm.map_path() == lm.MAP_VERSIONS["v1"]
    monkeypatch.setenv("PM_LEAF_MAP_VERSION", "v1+nba_depth")
    assert lm.depth_enabled() and lm.map_path() == lm.MAP_VERSIONS["v1"]
    monkeypatch.setenv("PM_LEAF_MAP_VERSION", "v2")
    assert not lm.depth_enabled()


def test_depth_splits_index_only_the_12_kept():
    d = lm.DepthSplits.load()
    assert sum(len(v) for v in d.kept.values()) >= 10 and len(d.kept) <= 12
    key = next(iter(d.kept))
    mt, band, name, leaf = key
    r = d.lookup(mt, band, {name: leaf})
    assert r["kept"] and r["arm"] in set(d.kept[key])
    assert d.lookup(mt, band, {name: "unknown"})["kept"] == []


def _book_row(depth_leaves=None):
    return {"sport": "NBA", "market_type": "NBA_GAME_TOTAL", "band": "T1", "market_ticker": "KXNBATOTAL-26NOV19ATLBOS-215",
            "event_ticker": "KXNBATOTAL-26NOV19ATLBOS", "yes_bid": 0.48, "yes_ask": 0.52, "p_yes": 0.55,
            "horizon_hours_to_start": 30.0}


def test_v1_router_output_unchanged_when_switch_off(monkeypatch):
    monkeypatch.delenv("PM_LEAF_MAP_VERSION", raising=False)
    a = sr.router_fields(_book_row(), "KXNBATOTAL", prev_mid=0.5, filters={})["router"]
    d = {"leaves": {"pace_prod@total": "mid"}, "logged_only": {}, "archive_sha": nd.ARCHIVE_SHA, "season": 2025}
    b = sr.router_fields(_book_row(), "KXNBATOTAL", prev_mid=0.5, filters={}, depth=d)["router"]
    for k in a:
        assert a[k] == b[k], k                              # every v1 field identical
    assert b["depth_archive_sha"] == nd.ARCHIVE_SHA and b["depth_split_applied"] is False
    assert "depth_leaves" not in a


def test_switch_on_applies_kept_depth_arm_and_logs_it(monkeypatch):
    dsp = lm.default_depth_splits()
    (mt, band, name, leaf), arms = next((k, v) for k, v in dsp.kept.items() if k[0] == "NBA_GAME_TOTAL" and k[1] == "T1")
    monkeypatch.setenv("PM_LEAF_MAP_VERSION", "v1+nba_depth")
    d = {"leaves": {name: leaf}, "logged_only": {}, "archive_sha": nd.ARCHIVE_SHA, "season": 2025}
    r = sr.router_fields(_book_row(), "KXNBATOTAL", prev_mid=0.5, filters={}, depth=d)["router"]
    assert r["depth_split_kept"] == [f"{name}={leaf}->{next(iter(arms))}"]
    assert r["depth_archive_sha"] == nd.ARCHIVE_SHA
