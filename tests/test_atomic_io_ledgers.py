"""W72.2 (GG-663/664/672): ledger writers are crash-safe and never reset on a read error."""
import json
import os

import pytest

from prediction_market_bot import atomic_io
from prediction_market_bot.atomic_io import LedgerCorruptError, LedgerWriteError
from prediction_market_bot.c5_execution.paper_trader import PaperTrader
from prediction_market_bot.pregame_shadow.ledger import ROW_FIELDS, CellLedger


def _row(i):
    r = {f: "x" for f in ROW_FIELDS}
    r.update(run_id="r", market_ticker=f"T{i}")
    return r


def test_crash_mid_write_leaves_old_file_intact(tmp_path, monkeypatch):
    p = tmp_path / "s.json"
    atomic_io.atomic_write_json(p, {"v": 1})

    def boom(src, dst):
        raise OSError("crash before rename")

    monkeypatch.setattr(os, "replace", boom)
    with pytest.raises(OSError):
        atomic_io.atomic_write_json(p, {"v": 2})
    assert json.loads(p.read_text()) == {"v": 1}
    assert [f.name for f in tmp_path.iterdir()] == ["s.json"]  # tmp cleaned up


def test_paper_trader_corrupt_file_quarantined_and_halts(tmp_path):
    p = tmp_path / "portfolio.json"
    p.write_text('{"bankroll_usd": 1000, "open_pos')  # torn write
    with pytest.raises(LedgerCorruptError):
        PaperTrader(portfolio_path=p, logger=None)
    assert not p.exists()
    q = list(tmp_path.glob("portfolio.json.corrupt.*"))
    assert len(q) == 1 and q[0].read_text().startswith('{"bankroll_usd"')


def test_paper_trader_save_failure_raises(tmp_path, monkeypatch):
    t = PaperTrader(portfolio_path=tmp_path / "p.json", logger=None)

    def boom(*a, **k):
        raise OSError("disk full")

    monkeypatch.setattr("prediction_market_bot.c5_execution.paper_trader.atomic_write_json", boom)
    with pytest.raises(LedgerWriteError):
        t._save()


def test_shadow_torn_trailing_line_skipped_and_next_row_parseable(tmp_path):
    led = CellLedger(tmp_path, "mlb", "ml", "T1")
    assert led.append(_row(1))
    with led.path.open("a") as fh:
        fh.write('{"run_id": "r", "market_tick')  # torn, no newline
    led2 = CellLedger(tmp_path, "mlb", "ml", "T1")  # fresh process: dedup reload must not raise
    assert led2.append(_row(2))
    assert not led2.append(_row(1))  # earlier row still dedups
    lines = led.path.read_text().splitlines()
    parsed = []
    for ln in lines:
        try:
            parsed.append(json.loads(ln)["market_ticker"])
        except ValueError:
            pass
    assert parsed == ["T1", "T2"]
