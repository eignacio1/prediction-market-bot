import json
import importlib.util
from pathlib import Path

_spec = importlib.util.spec_from_file_location("nfl_total_rows_read", Path(__file__).resolve().parent.parent / "scripts" / "nfl_total_rows_read.py")
m = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(m)


def _row(ts, tk, band="T1_MULTI_DAY", y=1.0, **kw):
    return {"ts_utc": ts, "market_ticker": tk, "band": band, "game_key": "2026-10-04:KC@BUF", "p_yes": 0.5, "y": y, **kw}


def test_first_row_per_market_and_exclusions(tmp_path):
    rows = [_row("2026-10-03T10", "KXNFLTOTAL-X-45"), _row("2026-10-03T12", "KXNFLTOTAL-X-45", y=0.0),
            _row("2026-09-01T10", "KXNFLTOTAL-Y-40", season_phase="preseason"),
            {"ts_utc": "t", "market_ticker": "KXNFLTOTAL-Z-41", "band": "T1_MULTI_DAY", "game_key": "g", "p_yes": 0.4, "y": None}]
    (tmp_path / "NFL_NFL_GAME_TOTAL_T1_MULTI_DAY.jsonl").write_text("\n".join(json.dumps(r) for r in rows))
    out = m.load_rows(str(tmp_path))
    assert len(out) == 1 and out[0]["ts_utc"] == "2026-10-03T10"


def test_allowlisted_and_read_only():
    import scripts.box_tasks as bt
    assert "nfl_total_rows_read" in bt.TASKS
    assert "write" not in bt.TASKS["nfl_total_rows_read"]


def test_agg_allowlisted_and_read_only():
    import scripts.box_tasks as bt
    assert bt.TASKS["nfl_total_agg_read"].endswith("nfl_total_rows_read.py --agg")


def test_median_total_and_aggregate_bins():
    assert m.median_total([(40.5, 0.6), (45.5, 0.4)]) == 43.0
    assert m.median_total([(40.5, 0.4), (45.5, 0.3)]) is None
    rows = [{"game_key": "g", "band": "b", "market_ticker": "T-40.5", "p_yes": 0.6, "mid": 0.5, "y": 1, "week": 5, "roof": "dome", "temp": None, "wind": None},
            {"game_key": "g", "band": "b", "market_ticker": "T-45.5", "p_yes": 0.4, "mid": 0.45, "y": 0, "week": 5, "roof": "dome", "temp": None, "wind": None}]
    (o,) = m.aggregate(rows)
    assert o["n"] == 2 and o["bm"] == 0.32 and o["bins"]["m1"][0] == 1 and o["bins"]["m2"][0] == 1


def test_weather_falls_back_to_previous_day():
    sched = {("2026-10-04", "KC", "BUF"): (5, "outdoors", 50, 8)}
    assert m.lookup_weather(sched, "2026-10-05:KC@BUF") == (5, "outdoors", 50, 8)
    assert m.lookup_weather(sched, "2026-10-09:KC@BUF", blank="") == ("", "", "", "")
