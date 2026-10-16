"""Real-store tests (W78.4): the PIT contract on sampled real games for every source, and the store checks."""
import os
from pathlib import Path

import pandas as pd
import pytest

from prediction_market_bot.c1_signal_ingestion import nba_store_checks as chk
from prediction_market_bot.c1_signal_ingestion.nba_event_store import SOURCES
from prediction_market_bot.c1_signal_ingestion.nba_point_in_time import LeakError, PointInTime, tip_table

STORE = Path(os.environ.get("NBA_STORE_DIR", "exp_output/NBA_EVENTS"))


def _season(name, s, cols=None):
    return pd.read_parquet(STORE / "raw" / name / f"{name}_{s}.parquet", columns=cols)


@pytest.fixture(scope="module")
def tips():
    frames = [tip_table(_season("schedule", s), _season("espn_schedule", s)) for s in (2016, 2019, 2022, 2025, 2026)]
    return pd.concat(frames)


def test_store_checks_pass_on_the_real_store():
    assert chk.run_checks(STORE).failures == []


def test_contract_on_sampled_real_games_every_post_game_source(tips):
    pit = PointInTime(tips)
    real = tips[~tips.tip_imputed & (tips.season_type == "regular-season")]
    sample = pd.concat([real[real.season == s].sample(3, random_state=11) for s in (2016, 2019, 2022, 2025, 2026)])
    for name in ("pbp", "possessions", "team_box", "officials", "player_box"):
        df = pd.concat([_season(name, s, ["game_id"]) for s in (2016, 2019, 2022, 2025, 2026)])
        for gid in sample.index:
            v = pit.view(df, "post_game", gid)
            pit.assert_no_leak(v, "post_game", gid)
            assert gid not in set(v.game_id)


def test_positive_control_on_real_frame(tips):
    pit = PointInTime(tips)
    gid = tips[(tips.season == 2026) & ~tips.tip_imputed].index[100]
    df = _season("team_box", 2026, ["game_id"])
    with pytest.raises(LeakError):
        pit.assert_no_leak(df, "post_game", gid)        # the whole season is not knowable at game 100's tip-off


def test_real_snapshot_never_backfills_history(tips):
    pit = PointInTime(tips)
    inj = pd.read_parquet(sorted((STORE / "raw" / "injuries").glob("injuries_*.parquet"))[-1])
    old = tips[tips.season == 2016].index[0]
    assert pit.view(inj, "snapshot", old).empty         # 2016 game: no 2026 injury row may be visible
    assert set(SOURCES) >= {"injuries", "coaches"}
