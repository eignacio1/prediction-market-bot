"""GG-228: build_t4_resolved_ledger.py must never overwrite a changed/removed existing row."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import build_t4_resolved_ledger as b  # noqa: E402


def _row(pid, pnl=1.0):
    return {"position_id": pid, "outcome": "WIN", "pnl": pnl, "resolved_at": f"2026-10-0{pid[-1]}"}


def _seed(path, rows):
    path.write_text("".join(json.dumps(r) + "\n" for r in rows))


def _rebuilds(tmp_path):
    return list(tmp_path.glob("ledger.rebuild_*.jsonl"))


def test_identical_overwrites_in_place(tmp_path):
    out = tmp_path / "ledger.jsonl"
    rows = [_row("P1"), _row("P2")]
    _seed(out, rows)
    written, diff = b.guarded_write(rows, out)
    assert written == out and not _rebuilds(tmp_path)
    assert diff == {"changed": [], "removed": [], "added": []}


def test_append_only_growth_is_allowed(tmp_path):
    out = tmp_path / "ledger.jsonl"
    _seed(out, [_row("P1")])
    written, diff = b.guarded_write([_row("P1"), _row("P2")], out)
    assert written == out and diff["added"] == ["P2"] and not _rebuilds(tmp_path)
    assert len(out.read_text().splitlines()) == 2


def test_changed_row_blocks_overwrite(tmp_path, caplog):
    out = tmp_path / "ledger.jsonl"
    _seed(out, [_row("P1", pnl=-1.0), _row("P2")])
    before = out.read_text()
    with caplog.at_level("WARNING"):
        written, diff = b.guarded_write([_row("P1", pnl=1.0), _row("P2")], out)
    assert out.read_text() == before
    assert written != out and written in _rebuilds(tmp_path)
    assert diff["changed"] == ["P1"]
    assert "GG-228 GUARD" in caplog.text and "changed=1" in caplog.text


def test_removed_row_blocks_overwrite(tmp_path, caplog):
    out = tmp_path / "ledger.jsonl"
    _seed(out, [_row("P1"), _row("P2")])
    before = out.read_text()
    with caplog.at_level("WARNING"):
        written, diff = b.guarded_write([_row("P1")], out)
    assert out.read_text() == before and written in _rebuilds(tmp_path)
    assert diff["removed"] == ["P2"] and "removed=1" in caplog.text


def test_main_exits_zero_when_guard_trips(tmp_path):
    pf = tmp_path / "pf.json"
    pf.write_text(json.dumps({"closed_positions": [], "open_positions": []}))
    out = tmp_path / "ledger.jsonl"
    _seed(out, [_row("P1")])
    assert b.main(["--portfolio", str(pf), "--out", str(out)]) == 0
    assert _rebuilds(tmp_path) and "P1" in out.read_text()
