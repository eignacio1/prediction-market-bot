import hashlib
from pathlib import Path

import pytest

from prediction_market_bot.archive_intake import closing_lines as cl


def _mk(tmp_path, body: bytes, monkeypatch):
    d = tmp_path / cl.FOLDER
    d.mkdir(parents=True)
    (d / cl.CSV_NAME).write_bytes(body)
    monkeypatch.setattr(cl, "CSV_SHA256", hashlib.sha256(body).hexdigest())
    monkeypatch.setattr(cl, "CSV_BYTES", len(body))


def test_splits_seasons_and_parses(tmp_path, monkeypatch):
    body = (b"season_type,open_home_win_prob,close_home_win_prob,open_spread_home,close_spread_home,close_home_cover_prob,"
            b"open_total,close_total,close_over_prob,home_score,away_score\n"
            b"regular,0.5,0.55,-1.5,-1.5,0.4,6,6.5,0.5,3,2\npostseason,,0.6,,,,,,,1,0\n")
    _mk(tmp_path, body, monkeypatch)
    d = cl.load_nhl_closing(tmp_path)
    assert len(d["regular"]) == 1 and len(d["postseason"]) == 1
    assert d["regular"][0]["close_home_win_prob"] == 0.55 and d["postseason"][0]["open_home_win_prob"] is None


def test_hash_mismatch_refused(tmp_path, monkeypatch):
    _mk(tmp_path, b"season_type\nregular\n", monkeypatch)
    (tmp_path / cl.FOLDER / cl.CSV_NAME).write_bytes(b"tampered")
    with pytest.raises(cl.ClosingLinesError):
        cl.load_nhl_closing(tmp_path)


def test_unpinned_sha_refused(tmp_path):
    with pytest.raises(cl.ClosingLinesError):
        cl.load_nhl_closing(tmp_path, sha="deadbeef")
