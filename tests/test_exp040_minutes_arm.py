"""EXP-040 wiring: sha guard, point-in-time injury snapshots, row schema, EXP-039 rows unchanged."""
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from prediction_market_bot.c1_signal_ingestion.nba_injury_reports import InjurySnapshots, parse_text
from prediction_market_bot.c1_signal_ingestion.nba_minutes_features import status_of
from prediction_market_bot.pregame_shadow import nba_player_points_minutes_forecaster as F
from prediction_market_bot.pregame_shadow.ledger import CellLedger, ROW_FIELDS
from prediction_market_bot.pregame_shadow.nba_player_points_minutes_model import NBAPlayerPointsMinutesModel

ROOT = Path(__file__).resolve().parent.parent
UTC = timezone.utc


def test_frozen_sha_pinned_and_artifact_loads():
    m = NBAPlayerPointsMinutesModel.load(ROOT / "models" / "nba_player_points_minutes_v1.json")
    assert m.sha256 == F.FROZEN_SHA256


def test_forecaster_refuses_wrong_sha():
    class M:
        sha256 = "0" * 64
    with pytest.raises(ValueError, match="refusing"):
        F.NBAPlayerPointsMinutesForecaster.__init__(object.__new__(F.NBAPlayerPointsMinutesForecaster),
                                                    M(), None, None, None, None)


def _snaps(tmp_path, calls):
    def fetch(url):
        calls.append(url)
        return url.encode()
    return InjurySnapshots(tmp_path, fetch=fetch, parse=lambda b: {"x y": b.decode()[-12:]})


def test_snapshot_never_after_now_or_within_4h_of_tip(tmp_path):
    calls: list = []
    s = _snaps(tmp_path, calls)
    tip = datetime(2026, 10, 21, 23, 30, tzinfo=UTC)           # 19:30 ET
    now = datetime(2026, 10, 21, 17, 0, tzinfo=UTC)            # 13:00 ET -> only 11:30 ET slot usable
    snap, label, t = s.snapshot(tip, now)
    assert snap is not None and t <= now and t <= tip - timedelta(hours=4)
    assert label.endswith("11:30 ET")
    assert not any("0130PM" in c or "0330PM" in c for c in calls)   # later slots never fetched


def test_snapshot_missing_when_nothing_published_yet(tmp_path):
    s = InjurySnapshots(tmp_path, fetch=lambda u: (_ for _ in ()).throw(OSError("404")), parse=lambda b: {})
    tip = datetime(2026, 10, 21, 23, 30, tzinfo=UTC)
    assert s.snapshot(tip, tip - timedelta(hours=20)) == (None, None, None)
    assert not list(tmp_path.glob("*.json"))                      # failures are never cached


def test_parse_and_status_match():
    snap = {"jayson tatum": "Out"}
    assert status_of(snap, "Jayson Tatum") == "Out" and status_of(snap, "Nobody Here") is None


def test_row_extra_default_is_byte_identical(tmp_path):
    row = {f: "v" for f in ROW_FIELDS}
    row["run_id"], row["market_ticker"] = "r1", "T1"
    a = CellLedger(tmp_path / "a", "NBA", "NBA_PLAYER_POINTS", "T1", None)
    b = CellLedger(tmp_path / "b", "NBA", "NBA_PLAYER_POINTS", "T1", None)
    a.append(row)
    b.append(row, None)
    assert a.path.read_bytes() == b.path.read_bytes()
    c = CellLedger(tmp_path / "c", "NBAMIN", "NBA_PLAYER_POINTS", "T1", None)
    c.append(row, {"artifact_sha256": F.FROZEN_SHA256, "injury_snapshot_utc": None})
    d = json.loads(c.path.read_text())
    assert d["artifact_sha256"] == F.FROZEN_SHA256 and "injury_snapshot_utc" in d


def test_strike_15_only():
    from prediction_market_bot.pregame_shadow.nba_player_points_minutes_model import REGISTERED_STRIKES
    assert REGISTERED_STRIKES == (15,)
