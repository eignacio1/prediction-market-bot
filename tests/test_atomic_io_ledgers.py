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


# ---- W76.3 (GG-748): cross-process safety ------------------------------------------------------------

def _writer(args):
    base, worker, n = args
    from pathlib import Path
    led = CellLedger(Path(base), "mlb", "ml", "T1")  # fresh instance per process, shared file
    for i in range(n):
        r = {f: "x" * 200 for f in ROW_FIELDS}   # long rows make a torn/interleaved write likely
        r.update(run_id=f"w{worker}", market_ticker=f"T{i}")
        assert led.append(r)


def test_cellledger_concurrent_processes_no_row_lost_or_torn(tmp_path):
    import multiprocessing as mp
    workers, n = 6, 60
    with mp.get_context("fork").Pool(workers) as pool:
        pool.map(_writer, [(str(tmp_path), w, n) for w in range(workers)])
    lines = (tmp_path / "mlb_ml_T1.jsonl").read_text().splitlines()
    rows = [json.loads(l) for l in lines]            # any torn/interleaved line raises here
    assert len(rows) == workers * n
    assert len({(r["run_id"], r["market_ticker"]) for r in rows}) == workers * n


def test_cellledger_dedup_sees_other_process_append(tmp_path):
    a = CellLedger(tmp_path, "mlb", "ml", "T1")
    b = CellLedger(tmp_path, "mlb", "ml", "T1")
    assert a.append(_row(1))
    assert not b.append(_row(1))        # b never loaded this key itself; must see a's row under the lock
    assert a.append(_row(2)) and not b.append(_row(2))
    assert len((tmp_path / "mlb_ml_T1.jsonl").read_text().splitlines()) == 2


def test_file_lock_serialises_and_lock_file_is_beside_target(tmp_path):
    p = tmp_path / "led.json"
    with atomic_io.file_lock(p):
        assert (tmp_path / "led.json.lock").exists()
