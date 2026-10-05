"""GG-470: per-date refresh path (no network). Row schema must equal the range path's; failures must be loud."""
import importlib.util
from datetime import date
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location("fetch_mlb", ROOT / "scripts" / "fetch_mlb_game_history.py")
fm = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(fm)

COLS = ["game_pk", "game_type", "season", "game_date", "start_utc", "status", "double_header",
        "home", "away", "home_score", "away_score", "home_sp", "away_sp"]


def _row(pk, day, status="Final", season=2026, hs=3.0, as_=2.0):
    return {"game_pk": pk, "game_type": "R", "season": season, "game_date": day, "start_utc": f"{day}T23:00:00Z",
            "status": status, "double_header": "N", "home": "LAD", "away": "ATL", "home_score": hs,
            "away_score": as_, "home_sp": 1.0, "away_sp": 2.0}


def _api_game(pk, gtype="R"):
    t = lambda ab, **k: {"team": {"abbreviation": ab}, **k}
    return {"gamePk": pk, "gameType": gtype, "season": "2026", "officialDate": "2026-10-04",
            "gameDate": "2026-10-04T20:00:00Z", "status": {"abstractGameState": "Final"},
            "teams": {"home": t("LAD", score=4, probablePitcher={"id": 7}), "away": t("ATL", score=1)}}


class _Resp:
    def __init__(self, code, games=()):
        self.status_code, self._g = code, list(games)

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(self.status_code)

    def json(self):
        return {"dates": [{"games": self._g}]}


def test_rows_schema_and_missing_pitchers():
    r = fm._rows([_api_game(1)])[0]
    assert list(r) == COLS and r["home_sp"] == 7 and r["away_sp"] is None and r["home_score"] == 4


def test_fetch_day_filters_game_types_and_omits_gametype_param(monkeypatch):
    seen = {}

    def fake_get(url, params, timeout):
        seen.update(params)
        return _Resp(200, [_api_game(1, "R"), _api_game(2, "S"), _api_game(3, "E"), _api_game(4, "D")])

    monkeypatch.setattr(fm.requests, "get", fake_get)
    assert [r["game_pk"] for r in fm.fetch_day("2026-10-04")] == [1, 4]
    assert "gameType" not in seen and seen["date"] == "2026-10-04"


def test_fetch_day_retries_406_then_succeeds_and_raises_when_exhausted(monkeypatch):
    codes = iter([406, 406, 200])
    waits = []
    monkeypatch.setattr(fm.requests, "get", lambda *a, **k: _Resp(next(codes), [_api_game(1)]))
    assert len(fm.fetch_day("2026-10-04", sleep=waits.append)) == 1 and waits == [5, 15]
    monkeypatch.setattr(fm.requests, "get", lambda *a, **k: _Resp(406))
    with pytest.raises(RuntimeError, match="406"):
        fm.fetch_day("2026-10-04", sleep=lambda s: None)


def _seed(tmp_path, rows):
    base = tmp_path / "games.parquet"
    pd.DataFrame(rows).to_parquet(base)
    return base


def test_refresh_replaces_window_keeps_rest_and_writes_full_season(tmp_path):
    base = _seed(tmp_path, [_row(1, "2026-09-01"), _row(5, "2026-10-02"),
                            _row(2, "2026-10-03", "Preview", hs=None, as_=None),
                            _row(3, "2026-10-04", "Preview", hs=None, as_=None), _row(9, "2025-09-01", season=2025)])
    out = tmp_path / "games_current.parquet"
    fetched = []

    def fake(day):
        fetched.append(day)
        return {"2026-10-02": [_row(5, "2026-10-02")], "2026-10-03": [_row(2, "2026-10-03")]}.get(day, [])

    fm.refresh_recent(out, base, 2026, date(2026, 10, 5), back=2, ahead=1, fetch=fake, sleep=lambda s: None)
    got = pd.read_parquet(out).set_index("game_pk")
    assert fetched[0] == "2026-10-01" and fetched[-1] == "2026-10-06"          # window starts 1d before last Final
    assert got.loc[2, "status"] == "Final" and got.loc[2, "home_score"] == 3.0
    assert 3 not in got.index                       # window date refreshed with no game -> stale row dropped
    assert 1 in got.index and 9 not in got.index    # earlier rows kept; other seasons not carried
    assert str(got.home_score.dtype) == "float64"


def test_refresh_fails_closed(tmp_path):
    base = _seed(tmp_path, [_row(1, "2026-08-01")])
    out = tmp_path / "o.parquet"
    with pytest.raises(RuntimeError, match="re-seed"):
        fm.refresh_recent(out, base, 2026, date(2026, 10, 5), fetch=lambda d: [], sleep=lambda s: None)
    with pytest.raises(RuntimeError, match="seed it first"):
        fm.refresh_recent(out, tmp_path / "missing.parquet", 2026, date(2026, 10, 5))

    def boom(day):
        raise RuntimeError("406")

    base2 = _seed(tmp_path, [_row(1, "2026-10-03")])
    assert not out.exists()
    with pytest.raises(RuntimeError):
        fm.refresh_recent(out, base2, 2026, date(2026, 10, 5), fetch=boom, sleep=lambda s: None)
    assert not out.exists()                          # no partial write on failure
