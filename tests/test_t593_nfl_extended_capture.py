"""T-593: extended (opt-in) NFL ingestion allowlist + append-only capture.

Proves: default schemas are byte-for-byte unchanged; extended schemas add
exactly the named fields; market/outcome columns are never retained; a source
missing an extended field fails loudly; capture writes provenance and never
overwrites.
"""
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from prediction_market_bot.c1_signal_ingestion.nfl_ingestion import (
    NFLIngestionClient, _NFL_SCHEDULE_COLUMNS, _NFL_SCHEDULE_EXTENDED_COLUMNS,
    _NFL_SCHEDULE_EXTENDED_FIELDS, _NFL_TEAM_STATS_COLUMNS,
    _NFL_TEAM_STATS_EXTENDED_FIELDS, _NFL_TEAM_STATS_SPLIT_COLUMNS,
)

FORBIDDEN = {"away_moneyline", "home_moneyline", "spread_line", "total_line",
             "away_spread_odds", "home_spread_odds", "under_odds", "over_odds",
             "result", "total"}
SCHED_EXTRA_RAW = FORBIDDEN | {"weekday", "gametime", "location", "overtime"}


def _client():
    return NFLIngestionClient(logger=MagicMock(), snapshot_id="T593", request_delay=0)


def _resp(text):
    r = MagicMock(); r.status_code = 200; r.text = text
    r.content = text.encode(); r.raise_for_status.return_value = None
    return r


def _sched_csv(drop=()):
    cols = [c for c in (_NFL_SCHEDULE_EXTENDED_COLUMNS + sorted(SCHED_EXTRA_RAW)) if c not in drop]
    row = {c: 1 for c in cols}
    row.update(game_id="2026_04_A_B", season=2026, week=4, gameday="2026-10-04",
               home_team="B", away_team="A", roof="dome", surface="turf",
               away_qb_name="X", home_qb_name="Y", away_qb_id="1", home_qb_id="2",
               away_coach="c1", home_coach="c2", referee="r")
    return pd.DataFrame([row], columns=cols).to_csv(index=False)


def _stats_csv():
    cols = ["season", "week", "season_type", "game_id", "team", "opponent_team",
            "passing_epa", "rushing_epa", "def_tds"] + _NFL_TEAM_STATS_EXTENDED_FIELDS
    row = {c: 1.0 for c in cols}
    row.update(season=2026, week=3, season_type="REG", game_id="g", team="A", opponent_team="B")
    return pd.DataFrame([row], columns=cols).to_csv(index=False)


def test_default_schedule_unchanged_and_extended_adds_only_named():
    c = _client()
    with patch("prediction_market_bot.c1_signal_ingestion.nfl_ingestion.requests.get",
               return_value=_resp(_sched_csv())):
        _, d = c.fetch_schedule()
        _, e = c.fetch_schedule(include_extended=True)
    assert list(d.columns) == _NFL_SCHEDULE_COLUMNS
    assert list(e.columns) == _NFL_SCHEDULE_COLUMNS + _NFL_SCHEDULE_EXTENDED_FIELDS
    assert not (FORBIDDEN & set(e.columns))


def test_default_team_stats_unchanged_and_extended_adds_only_named():
    c = _client()
    with patch("prediction_market_bot.c1_signal_ingestion.nfl_ingestion.requests.get",
               return_value=_resp(_stats_csv())):
        _, d = c.fetch_team_stats(2026)
        _, e = c.fetch_team_stats(2026, include_extended=True)
        _, es = c.fetch_team_stats(2026, include_splits=True, include_extended=True)
        _, b = c.fetch_team_stats_bulk([2026], include_extended=True)
    assert list(d.columns) == _NFL_TEAM_STATS_COLUMNS
    assert list(e.columns) == _NFL_TEAM_STATS_COLUMNS + _NFL_TEAM_STATS_EXTENDED_FIELDS
    assert list(es.columns) == _NFL_TEAM_STATS_SPLIT_COLUMNS + _NFL_TEAM_STATS_EXTENDED_FIELDS
    assert list(b.columns) == list(e.columns)
    assert "def_tds" not in e.columns  # allowlist, not passthrough


def test_missing_extended_field_fails_loudly_only_when_extended():
    c = _client()
    with patch("prediction_market_bot.c1_signal_ingestion.nfl_ingestion.requests.get",
               return_value=_resp(_sched_csv(drop={"referee"}))):
        ok_d, _ = c.fetch_schedule()
        ok_e, _ = c.fetch_schedule(include_extended=True)
    assert ok_d is True and ok_e is False


def test_capture_writes_provenance_and_never_overwrites(tmp_path):
    c = _client()
    def get(url, timeout=None):
        return _resp(_sched_csv() if "games.csv" in url else _stats_csv())
    with patch("prediction_market_bot.c1_signal_ingestion.nfl_ingestion.requests.get", side_effect=get):
        ok, m = c.capture_extended(2026, tmp_path)
    assert ok
    sched = pd.read_parquet(tmp_path / m["datasets"]["schedule"]["file"])
    assert {"_retrieved_at_utc", "_source_url", "referee"} <= set(sched.columns)
    assert len(m["datasets"]["schedule"]["sha256"]) == 64
    assert (tmp_path / m["manifest_file"]).exists()
    # same-second re-capture must refuse, not overwrite
    with patch("prediction_market_bot.c1_signal_ingestion.nfl_ingestion.requests.get", side_effect=get), \
         patch.object(NFLIngestionClient, "_utc_now_iso", return_value=m["datasets"]["schedule"]["retrieved_at_utc"]):
        with pytest.raises(FileExistsError):
            _client().capture_extended(2026, tmp_path)
