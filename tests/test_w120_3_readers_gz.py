"""W120.3 / B-103: the three readers held back in W119.4 read a plain OR .gz input and see the same rows."""
from __future__ import annotations

import gzip
import importlib.util
import json
import sys
import time
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))


def _load(rel: str, name: str):
    sys.path.insert(0, str(REPO / "12_EXPLORATORY" / "longshot_bias"))
    spec = importlib.util.spec_from_file_location(name, REPO / rel)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def _put(path: Path, rows, gz: bool) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    body = "".join(json.dumps(r) + "\n" for r in rows).encode()
    out = Path(str(path) + (".gz" if gz else ""))
    out.write_bytes(gzip.compress(body) if gz else body)
    return path  # always the PLAIN name: readers must resolve it


ORDERS = [{"ts": "2026-11-07T12:00:00Z", "event": "arm_order", "arm": "RIDE"},
          {"ts": "2026-11-05T12:00:00Z", "event": "arm_skip", "arm": "FADE"}]


@pytest.mark.parametrize("gz", [False, True])
def test_arm_orders_read_load_rows(tmp_path, gz):
    m = _load("scripts/arm_orders_read.py", "arm_orders_read_t")
    p = _put(tmp_path / "orders.jsonl", ORDERS, gz)
    assert m.load_rows(p) == ORDERS
    assert m.load_rows(tmp_path / "missing.jsonl") == []


@pytest.mark.parametrize("gz", [False, True])
def test_demo_fill_forward_report_load_events_and_markouts(tmp_path, gz):
    m = _load("scripts/demo_fill_forward_report.py", "dfr_t")
    p = _put(tmp_path / "orders.jsonl", ORDERS, gz)
    assert m.load_events(p) == ORDERS
    assert m.load_events(tmp_path / "missing.jsonl") == []
    mk = [{"order_id": "a", "mid_5m": 0.5}, {"order_id": "b", "mid_5m": 0.4}]
    q = _put(tmp_path / "markouts.jsonl", mk, gz)
    assert m.load_markouts(q) == mk
    assert m.load_markouts(tmp_path / "missing.jsonl") == []


@pytest.mark.parametrize("gz", [False, True])
@pytest.mark.parametrize("big", [False, True])
def test_run_ride_board_recent_mids(tmp_path, gz, big):
    m = _load("scripts/run_ride_board.py", "rrb_t")
    now = time.time()
    iso = lambda t: time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(t))
    rows = [{"run_ts": iso(now - 600 + i), "ticker": "T-A", "yes_mid": 0.40 + i / 1000} for i in range(50)]
    if big:  # more than tail_bytes of earlier noise, so the tail logic (not a whole-file read) is what is exercised
        rows = [{"run_ts": iso(now - 3000), "ticker": "T-OTHER", "yes_mid": 0.1, "pad": "x" * 200} for _ in range(100)] + rows
    d = tmp_path / "PRICE_ARCHIVE"
    _put(d / "prices_2026-11-01.jsonl", [{"run_ts": iso(now - 99999), "ticker": "T-A", "yes_mid": 0.99}], gz)  # older day, ignored
    _put(d / "prices_2026-11-02.jsonl", rows, gz)
    out = m.recent_mids(d, {"T-A"}, now, tail_bytes=4000 if big else 10_000_000)
    assert out["T-A"][-1][1] == pytest.approx(0.449)
    assert all(v != 0.99 for _, v in out["T-A"])
    if big:
        assert "T-OTHER" not in out
