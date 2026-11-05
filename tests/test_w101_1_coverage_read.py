"""W101.1 / B-030: the read-only coverage task, on a fixture night."""
import importlib.util
import json
from pathlib import Path

spec = importlib.util.spec_from_file_location("cov_read", Path(__file__).resolve().parents[1] / "scripts" / "nba_engine_coverage_read.py")
M = importlib.util.module_from_spec(spec)
spec.loader.exec_module(M)


def _w(p, rows):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("".join(json.dumps(r) + "\n" for r in rows))


def _row(ev, at, tip="2026-11-05T00:00:00+00:00"):
    return dict(event_ticker=ev, game_date="2026-11-04", logged_at=at, tip_utc=tip)


def test_per_arm_counts_and_reconstructed_v3(tmp_path):
    out = tmp_path / "exp_output"
    A, B, C = "KXNBAGAME-26NOV04AAABBB", "KXNBAGAME-26NOV04CCCDDD", "KXNBAGAME-26NOV04EEEFFF"
    ok, late = "2026-11-04T23:00:00+00:00", "2026-11-05T00:30:00+00:00"
    _w(out / "NBA_ENGINE_LIVE" / "rows.jsonl", [_row(A, ok), _row(B, ok), _row(C, late)])
    _w(out / "NBA_ENGINE_LIVE_V2" / "rows.jsonl", [_row(A, ok)])
    _w(out / "NBA_ENGINE_LIVE_V2" / "coverage.jsonl", [dict(event_ticker=B, reason="window_closed_without_a_successful_run")])
    _w(out / "NBA_ENGINE_LIVE_V3" / "rows.jsonl", [_row(A, ok)])  # no coverage file: B, C reconstructed
    res = M.build(M.per_arm(tmp_path, out), ["2026-11-04"])["2026-11-04"]
    assert res["v1"]["scheduled"] == 3 and res["v1"]["logged_before_tip"] == 2 and res["v1"]["logged_after_tip"] == 1
    assert res["v2"]["missed"] == 2 and "window_closed_without_a_successful_run|coverage.jsonl" in res["v2"]["reasons"]
    assert res["v2"]["reasons"]["not_in_rows_and_no_coverage_row|reconstructed"] == 1  # C
    assert res["v3"]["reasons"] == {"not_in_rows_and_no_coverage_row|reconstructed": 2}


def test_event_date_parse():
    assert M.event_date("KXNBAGAME-26NOV04LALDEN") == "2026-11-04"
