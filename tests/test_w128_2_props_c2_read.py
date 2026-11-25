"""W128.2 Part C: props_c2_read pairs C2 with EXP-047 rows and builds the schedule; read-only, in the box allowlist."""
import json
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import props_c2_read as R  # noqa: E402
import box_tasks  # noqa: E402


def _w(d, rows):
    d.mkdir(parents=True)
    (d / "NBAENG_NBA_PLAYER_POINTS_T1.jsonl").write_text("\n".join(json.dumps(r) for r in rows))


def test_compare_pairs_and_differences(tmp_path):
    row = lambda p, t="KXNBAPTS-26NOV25AAABBB-X-10": dict(market_type="NBA_PLAYER_POINTS", market_ticker=t, run_id="r1", ts_utc="2026-11-25T20:00:00+00:00", p_yes=p, event_ticker="KXNBAPTS-26NOV25AAABBB")
    _w(tmp_path / "b", [row(0.50), row(0.40, "T2"), row(0.3, "OLD")])
    _w(tmp_path / "c", [row(0.55), row(0.40, "T2")])
    o = R.compare(tmp_path / "b", tmp_path / "c", "2026-11-25")["points"]
    assert o["pairs"] == 2 and o["differ"] == 1 and abs(o["sum"] - 0.05) < 1e-9


def test_schedule_known_answer():
    res = {"stats": {"assists": {"ci95": [-0.0051, -0.0031], "ll_diff": -0.0041, "n_games": 100}}}
    s = R.schedule(res, {"assists": 5.0}, date(2026, 11, 25))["assists"]
    sd = (0.0020 / 3.92) * 10
    need = -(-(1.96 * sd / 0.0041) ** 2 // 1)
    assert s["games_to_judge"] == int(need) and s["date_reached"] is not None


def test_in_allowlist():
    assert "props_c2_read" in box_tasks.TASKS or any("props_c2_read" in v for v in vars(box_tasks).values() if isinstance(v, dict))
