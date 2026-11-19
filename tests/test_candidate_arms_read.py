import importlib.util
import pathlib

p = pathlib.Path(__file__).resolve().parents[1] / "scripts" / "candidate_arms_read.py"
s = importlib.util.spec_from_file_location("car", p)
car = importlib.util.module_from_spec(s)
s.loader.exec_module(car)


def test_count_per_sport_and_candidate():
    rows = [{"sport": "NBA", "router": {"arm": "RIDE"}, "router_candidates": {
                "router_v2": {"arm": "RIDE", "map_version": "v2", "map_sha256": "a" * 64},
                "nba_depth": {"arm": "ERROR", "map_version": "v1+nba_depth", "map_sha256": "b" * 64}}},
            {"sport": "NBA", "router": {"arm": "FADE"}},
            {"sport": "NHL", "router": {"arm": "RIDE"}, "router_candidates": {"nhl_v2": {"arm": "FADE", "map_version": "nhl_v2"}}}]
    o = car.count(rows)
    assert o["rows_in_window"] == {"NBA": 2, "NHL": 1}
    assert o["candidates"]["NBA|router_v2"]["rows"] == 1 and o["candidates"]["NBA|router_v2"]["same_as_v1"] == 1
    assert o["candidates"]["NBA|nba_depth"]["errors"] == 1
    assert o["candidates"]["NHL|nhl_v2"]["arms"] == {"FADE": 1}
