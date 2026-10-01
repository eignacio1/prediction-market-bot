"""T-601: pre-kickoff capture runner -- idempotency, append-not-overwrite,
partial-data refusal, provenance fields."""
import importlib.util
import json
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch

import pandas as pd
import requests
import pytest

from prediction_market_bot.c1_signal_ingestion.nfl_ingestion import (
    NFLIngestionClient, _NFL_SCHEDULE_EXTENDED_COLUMNS, _NFL_TEAM_STATS_EXTENDED_FIELDS,
)

_spec = importlib.util.spec_from_file_location(
    "nfl_prekickoff_capture", Path(__file__).resolve().parents[1] / "scripts" / "nfl_prekickoff_capture.py")
cap = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(cap)

NOW = datetime(2026, 9, 30, 12, 0, tzinfo=timezone.utc)
SHA = "deadbeef" * 5


def _resp(text):
    r = MagicMock(); r.status_code = 200; r.text = text
    r.content = text.encode(); r.raise_for_status.return_value = None
    return r


def _sched(qb="Q1", null_col=None):
    rows = []
    for w, day in ((3, "2026-09-20"), (4, "2026-10-04")):
        for i, (h, a) in enumerate((("AAA", "BBB"), ("CCC", "DDD"))):
            rows.append(dict(
                game_id=f"2026_{w:02d}_{i}", season=2026, game_type="REG", week=w,
                gameday=day, gametime="13:00", home_team=h, away_team=a,
                home_score=1, away_score=2, home_rest=7, away_rest=7,
                temp=60, wind=5, roof="outdoors", surface="grass",
                away_qb_id="a", away_qb_name=qb, home_qb_id="h", home_qb_name="H",
                away_coach="c", home_coach="d", referee=None))
    df = pd.DataFrame(rows)
    assert set(_NFL_SCHEDULE_EXTENDED_COLUMNS) <= set(df.columns)
    if null_col:
        df.loc[df.week == 4, null_col] = None
    return df.to_csv(index=False)


def _stats(teams=("AAA", "BBB", "CCC", "DDD")):
    rows = [dict(season=2026, week=3, season_type="REG", game_id="g", team=t,
                 opponent_team="X", passing_epa=1.0, rushing_epa=1.0,
                 **{f: 1.0 for f in _NFL_TEAM_STATS_EXTENDED_FIELDS}) for t in teams]
    return pd.DataFrame(rows).to_csv(index=False)


def _client():
    return NFLIngestionClient(logger=MagicMock(), snapshot_id="T601", request_delay=0)


def _run(tmp_path, sched, stats, **kw):
    def get(url, timeout=None):
        return _resp(sched if "games.csv" in url else stats)
    with patch("prediction_market_bot.c1_signal_ingestion.nfl_ingestion.requests.get", side_effect=get):
        return cap.run(2026, None, tmp_path, _client(), now=NOW, commit_sha=SHA, **kw)


def _index(tmp_path):
    p = tmp_path / "capture_index.jsonl"
    return [json.loads(x) for x in p.read_text().splitlines()] if p.exists() else []


def test_provenance_fields_present_and_week_autopicked(tmp_path):
    out = _run(tmp_path, _sched(), _stats())
    assert out["week"] == 4
    recs = _index(tmp_path)
    assert {r["source"] for r in recs} == {"schedule", "team_stats"}
    for r in recs:
        assert r["status"] == "complete"
        assert r["captured_at_utc"] and r["source_url"].startswith("https://")
        assert len(r["upstream_sha256"]) == 64 and len(r["content_sha256"]) == 64
        assert r["runtime_commit_sha"] == SHA
        assert r["kickoffs_preceded_utc"] == ["2026-10-04T17:00:00Z"] * 2  # 13:00 EDT
        assert (tmp_path / r["file"]).exists()


def test_idempotent_second_run_writes_nothing(tmp_path):
    _run(tmp_path, _sched(), _stats())
    files = sorted(p.name for p in tmp_path.glob("*.parquet"))
    lines = (tmp_path / "capture_index.jsonl").read_text()
    out = _run(tmp_path, _sched(), _stats())
    assert {v["action"] for v in out["results"].values()} == {"skipped_unchanged"}
    assert sorted(p.name for p in tmp_path.glob("*.parquet")) == files
    assert (tmp_path / "capture_index.jsonl").read_text() == lines


def test_changed_content_appends_new_record_and_preserves_old(tmp_path):
    _run(tmp_path, _sched(qb="Q1"), _stats())
    first = (tmp_path / "capture_index.jsonl").read_text()
    old_file = next(p for p in tmp_path.glob("schedule_ext_*.parquet"))
    old_bytes = old_file.read_bytes()
    later = datetime(2026, 9, 30, 12, 0, 5, tzinfo=timezone.utc)
    with patch.object(NFLIngestionClient, "_utc_now_iso", return_value=later.isoformat()):
        _run(tmp_path, _sched(qb="Q2"), _stats())
    recs = _index(tmp_path)
    sched_recs = [r for r in recs if r["source"] == "schedule"]
    assert len(sched_recs) == 2 and sched_recs[0]["content_sha256"] != sched_recs[1]["content_sha256"]
    assert len([r for r in recs if r["source"] == "team_stats"]) == 1  # unchanged -> skipped
    assert (tmp_path / "capture_index.jsonl").read_text().startswith(first)  # append-only
    assert old_file.read_bytes() == old_bytes  # old capture untouched


def test_partial_schedule_refused_and_not_recorded_complete(tmp_path):
    with pytest.raises(cap.PartialCapture, match="null away_qb_id"):
        _run(tmp_path, _sched(null_col="away_qb_id"), _stats())
    assert _index(tmp_path) == [] and not list(tmp_path.glob("*.parquet"))
    rej = (tmp_path / "capture_rejects.jsonl").read_text()
    assert "null away_qb_id" in rej


def test_partial_team_stats_refused(tmp_path):
    with pytest.raises(cap.PartialCapture, match="missing teams"):
        _run(tmp_path, _sched(), _stats(teams=("AAA", "BBB")))
    assert _index(tmp_path) == []


def test_upstream_failure_refused_not_recorded(tmp_path):
    r = MagicMock(); r.status_code = 500
    r.raise_for_status.side_effect = requests.HTTPError("boom")
    with patch("prediction_market_bot.c1_signal_ingestion.nfl_ingestion.requests.get", return_value=r), \
         patch("prediction_market_bot.c1_signal_ingestion.nfl_ingestion.time.sleep"):
        with pytest.raises(cap.PartialCapture, match="upstream fetch failed"):
            cap.run(2026, None, tmp_path, _client(), now=NOW, commit_sha=SHA)
    assert _index(tmp_path) == []
