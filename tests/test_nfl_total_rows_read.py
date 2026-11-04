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
