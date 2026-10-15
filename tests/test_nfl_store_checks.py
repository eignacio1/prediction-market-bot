"""Store-check tests (W73.2): injected faults must fire (positive controls); the real store must pass if built."""
import os
from pathlib import Path

import pandas as pd
import pytest

from prediction_market_bot.c1_signal_ingestion import nfl_store_checks as chk
from prediction_market_bot.c1_signal_ingestion.nfl_event_store import (
    NotPublished, SOURCES, build, canonicalise, seasons_for)


def pbp_frame(n=50_000, season=2020):
    return pd.DataFrame({"game_id": [f"{season}_{i % 250:03d}" for i in range(n)], "play_id": range(n),
                         "season": season})


def run(df, name="pbp", season=2020, completed=True):
    rep = chk.Report()
    chk.check_frame(name, season, df, completed, rep)
    return rep.failures


def test_clean_frame_passes():
    assert run(pbp_frame()) == []


def test_empty_file_fails_unless_documented():
    assert run(pbp_frame(0))
    assert run(pbp_frame(0).assign(), "snaps", 2012) == []        # documented empty
    assert run(pbp_frame(0), "snaps", 2013)


def test_truncated_completed_season_fails_but_in_progress_season_does_not():
    assert any("minimum" in f for f in run(pbp_frame(1_000)))
    assert run(pbp_frame(1_000), completed=False) == []


def test_null_key_and_duplicate_key_fire():
    df = pbp_frame()
    df.loc[0, "play_id"] = None
    assert any("null key" in f for f in run(df))
    df = pbp_frame()
    df.loc[1, ["game_id", "play_id"]] = df.loc[0, ["game_id", "play_id"]].values
    assert any("duplicate" in f for f in run(df))


def test_missing_key_column_and_wrong_season_fire():
    assert any("missing" in f for f in run(pbp_frame().drop(columns="play_id")))
    assert any("season column" in f for f in run(pbp_frame().assign(season=2019)))


def test_documented_tolerance_is_a_ceiling_not_a_pass():
    df = pd.DataFrame({"season": 2020, "week": 1, "team": "A", "player_id": [str(i) for i in range(20_000)]})
    assert run(df, "rosters") == []
    df.loc[:5_000, "player_id"] = None                       # 25% null is far above the 0.1% tolerance
    assert any("null key" in f for f in run(df, "rosters"))


def test_canonicalise_depth_chart_snapshot_distinguishes_dated_rows():
    src = SOURCES["depth_charts"]
    raw = pd.DataFrame({"dt": ["2025-09-01T00:00:00Z", "2025-09-02T00:00:00Z"], "team": "A", "gsis_id": "x",
                        "pos_abb": "QB", "pos_slot": 1, "pos_rank": 1})
    out = canonicalise(raw, src, 2025, "2026-01-01T00:00:00Z")
    assert not out.duplicated(list(src.key)).any()


def test_build_fails_closed_on_missing_past_season(tmp_path):
    def fetch(url):
        raise NotPublished(url)
    m = build(tmp_path, tmp_path / "m.json", only=["snaps"], current=2013, fetch=fetch)
    assert m["failures"] and "snaps 2012" in m["failures"][0]
    assert len(m["failures"]) == 1                              # 2013 is the in-progress season: may be absent


def test_seasons_for_respects_declared_last_season():
    from dataclasses import replace
    assert seasons_for(replace(SOURCES["pbp"], last_season=2020), 2026)[-1] == 2020
    assert seasons_for(SOURCES["participation"], 2026)[-1] == 2026   # in range; absence tolerated only for the current season
    assert seasons_for(SOURCES["pbp"], 2026)[-1] == 2026
