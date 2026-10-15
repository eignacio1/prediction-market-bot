"""Real-store tests (W73.2): the point-in-time contract on sampled real games, and the store checks on every file.
Collected only when the store is built (see conftest.py)."""
import os
from pathlib import Path

import pandas as pd
import pytest

from prediction_market_bot.c1_signal_ingestion import nfl_store_checks as chk
from prediction_market_bot.c1_signal_ingestion.nfl_point_in_time import LeakError, PointInTime

STORE = Path(os.environ.get("NFL_STORE_DIR", "exp_output/NFL_EVENTS"))


def _latest(name):
    snaps = sorted((STORE / "raw" / name).glob(f"{name}_*.parquet"))
    return pd.read_parquet(snaps[-1])


def test_real_store_contract_on_sampled_games_every_source():
    games = _latest("schedules")
    pit = PointInTime(games)
    done = games[games.home_score.notna()]
    sample = pd.concat([done[done.season == s].sample(3, random_state=7) for s in (2012, 2016, 2020, 2022, 2024, 2025)])
    specs = {"pbp": ("post_game", "game_id"), "snaps": ("post_game", "game_id"),
             "pfr_pass": ("post_game", "game_id"), "ftn": ("post_game", "game_id"),
             "participation": ("post_game", "game_id"), "injuries": ("weekly", None), "rosters": ("weekly", None)}
    frames = {}
    for name, (kind, col) in specs.items():
        files = sorted((STORE / "raw" / name).glob(f"{name}_*.parquet"))
        frames[name] = pd.concat([pd.read_parquet(f, columns=_cols(kind)) for f in files if _season_in(f, sample)])
    for gid in sample.game_id:
        for name, (kind, col) in specs.items():
            df = frames[name]
            v = pit.view(df, kind, gid, col or "game_id")
            pit.assert_no_leak(v, kind, gid, col or "game_id")
            if kind == "post_game":
                assert gid not in set(v[col])
    # positive control on the real frame: dropping the contract (all rows of the season) must be flagged
    gid = sample.game_id.iloc[-1]
    with pytest.raises(LeakError):
        pit.assert_no_leak(frames["pbp"], "post_game", gid)


def _cols(kind):
    return ["game_id"] if kind == "post_game" else ["season", "week"]


def _season_in(path, sample):
    return int(path.stem.rsplit("_", 1)[1]) in set(sample.season)


def test_real_store_passes_all_checks():
    rep = chk.run_checks(STORE)
    assert rep.failures == []
    assert len(rep.rows) > 100 and len(rep.coverage) > 30
