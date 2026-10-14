"""W72.2 follow-up (GG-680): durable state/cache writers use atomic_io, so a crash mid-write leaves the old file."""
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

from prediction_market_bot.c1_signal_ingestion import nba_ingest, nba_player_ingest, nhl_ingest, validators
from prediction_market_bot.pregame_shadow import calibration_engine as ce

SRC = Path(__file__).resolve().parents[1] / "src" / "prediction_market_bot"
CONVERTED = [
    "reset_paper_portfolio.py",
    "run_pregame.py",
    "c1_signal_ingestion/validators.py",
    "c1_signal_ingestion/nba_ingest.py",
    "c1_signal_ingestion/nba_player_ingest.py",
    "c1_signal_ingestion/nba_injury_reports.py",
    "c1_signal_ingestion/nhl_ingest.py",
    "pregame_shadow/calibration_engine.py",
]


@pytest.fixture
def crash(monkeypatch):
    def boom(src, dst):
        raise OSError("crash before rename")

    monkeypatch.setattr(os, "replace", boom)


@pytest.mark.parametrize("rel", CONVERTED)
def test_converted_files_use_atomic_io(rel):
    src = (SRC / rel).read_text()
    assert "prediction_market_bot.atomic_io" in src
    if rel != "run_pregame.py":  # run_pregame also writes its (out-of-scope) report with write_text
        assert ".write_text(json.dumps" not in src
    else:
        assert "TEAM_STATS_CACHE.write_text" not in src


def test_row_count_state_survives_crash(tmp_path, monkeypatch):
    p = tmp_path / "state" / "rc.json"
    validators._save_row_count("src_a", 5, p)
    monkeypatch.setattr(os, "replace", lambda a, b: (_ for _ in ()).throw(OSError("x")))
    with pytest.raises(OSError):
        validators._save_row_count("src_a", 9, p)
    assert json.loads(p.read_text())["src_a"]["row_count"] == 5


def test_nba_season_store_survives_crash(tmp_path, monkeypatch):
    store = {"season": 2026, "games": {"1": {"x": 1}}}
    nba_ingest.save_season(store, tmp_path)
    monkeypatch.setattr(os, "replace", lambda a, b: (_ for _ in ()).throw(OSError("x")))
    with pytest.raises(OSError):
        nba_ingest.save_season({"season": 2026, "games": {}}, tmp_path)
    assert json.loads(nba_ingest.season_path(2026, tmp_path).read_text()) == store


def test_nba_player_store_survives_crash(tmp_path, monkeypatch):
    store = {"season": 2026, "games": {"1": {"rows": []}}}
    nba_player_ingest.save_players(store, tmp_path)
    monkeypatch.setattr(os, "replace", lambda a, b: (_ for _ in ()).throw(OSError("x")))
    with pytest.raises(OSError):
        nba_player_ingest.save_players({"season": 2026, "games": {}}, tmp_path)
    assert nba_player_ingest.load_players(2026, tmp_path) == store


def test_nhl_schedule_survives_crash(tmp_path, monkeypatch):
    nhl_ingest.save_schedule(2026, {1: {"game_id": 1}}, tmp_path)
    monkeypatch.setattr(os, "replace", lambda a, b: (_ for _ in ()).throw(OSError("x")))
    with pytest.raises(OSError):
        nhl_ingest.save_schedule(2026, {}, tmp_path)
    assert nhl_ingest.load_schedule(2026, tmp_path) == [{"game_id": 1}]


def test_nhl_boxscore_crash_leaves_no_torn_file(tmp_path, monkeypatch):
    monkeypatch.setattr(os, "replace", lambda a, b: (_ for _ in ()).throw(OSError("x")))
    opener = lambda url: (200, b'{"id": 7}')
    with pytest.raises(OSError):
        nhl_ingest.fetch_boxscore(7, nhl_ingest.Throttle(interval_s=0.0), root=tmp_path, opener=opener)
    assert not nhl_ingest.box_path(7, tmp_path).exists()
    assert list((tmp_path / "boxscore").glob("*.json")) == []
    monkeypatch.undo()
    w = nhl_ingest.fetch_boxscore(7, nhl_ingest.Throttle(interval_s=0.0), root=tmp_path, opener=opener)
    assert w["payload"] == {"id": 7}
    assert json.loads(nhl_ingest.box_path(7, tmp_path).read_text())["payload"] == {"id": 7}


def test_release_manifest_crash_does_not_block_retry(tmp_path, monkeypatch):
    cell = {"cell": "C1"}
    release = {"look": 1, "n": 5}
    now = datetime(2026, 10, 13, tzinfo=timezone.utc)
    monkeypatch.setattr(os, "replace", lambda a, b: (_ for _ in ()).throw(OSError("x")))
    with pytest.raises(OSError):
        ce.persist_release(tmp_path, cell, release, now)
    assert not ce.manifest_path(tmp_path, cell, 1).exists()   # no torn write-once manifest
    monkeypatch.undo()
    p = ce.persist_release(tmp_path, cell, release, now)
    assert json.loads(p.read_text())["n"] == 5
    assert ce.persist_release(tmp_path, cell, {"look": 1, "n": 9}, now) is None   # still write-once


def test_reset_portfolio_writes_atomically(tmp_path, monkeypatch):
    from prediction_market_bot import reset_paper_portfolio as rp

    p = tmp_path / "paper_portfolio.json"
    monkeypatch.setattr(sys, "argv", ["reset", "--confirm", "--path", str(p)])
    rp.main()
    assert json.loads(p.read_text())["bankroll_usd"] == rp.INITIAL_BANKROLL
    assert [f.name for f in tmp_path.iterdir()] == ["paper_portfolio.json"]
