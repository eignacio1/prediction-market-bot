"""W118.4 Part B: retention compresses, never deletes evidence; every reader of a compressed target still reads it."""
from __future__ import annotations

import gzip
import importlib.util
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))
from prediction_market_bot import disk_retention as dr  # noqa: E402
import board_survey_sports_gate as gate  # noqa: E402
import board_survey_sports_store as bs  # noqa: E402

NOW = datetime.now(timezone.utc)
ROWS = [{"kind": "markets_page", "key": "A", "payload": {"markets": [{"ticker": "T1"}]}, "content_sha256": "h1"},
        {"kind": "candles", "key": "T1|1|0|1", "payload": {"candlesticks": []}, "content_sha256": "h2"}]


def _age(p: Path, days: float) -> None:
    t = time.time() - days * 86400
    os.utime(p, (t, t))


def _raw(d: Path, day: str = "2026-10-02", age: float = 40) -> Path:
    d.mkdir(parents=True, exist_ok=True)
    p = d / f"raw_{day}.jsonl"
    p.write_text("".join(json.dumps(r) + "\n" for r in ROWS) * 50)
    _age(p, age)
    return p


def test_open_text_and_dated_files_see_plain_and_gz(tmp_path):
    a, b = _raw(tmp_path, "2026-10-01"), _raw(tmp_path, "2026-10-02")
    want = b.read_bytes()
    ok, msg, freed = dr.compress_verified(str(b))
    assert ok and not b.exists() and Path(str(b) + ".gz").exists() and freed > 0
    assert dr.dated_files(tmp_path, "raw_????-??-??.jsonl") == [str(a), str(b)]      # each once, plain name
    assert dr.read_bytes(b) == want and dr.open_text(b).read().encode() == want
    assert dr.read_bytes(a) == a.read_bytes()


def test_compress_verified_keeps_original_when_verify_fails(tmp_path, monkeypatch):
    p = _raw(tmp_path)
    monkeypatch.setattr(dr, "_sha_stream", lambda fh, chunk=1 << 20: "0" * 64)
    ok, msg, freed = dr.compress_verified(str(p))
    assert not ok and "verify FAILED" in msg and p.exists() and not Path(str(p) + ".gz").exists() and not Path(str(p) + ".gz.tmp").exists()


def test_compress_skips_when_no_space(tmp_path, monkeypatch):
    p = _raw(tmp_path)
    monkeypatch.setattr(dr.shutil, "disk_usage", lambda d: type("U", (), {"free": 1})())
    ok, msg, _ = dr.compress_verified(str(p))
    assert not ok and "free" in msg and p.exists()


def test_only_old_files_and_only_verified_targets_are_compressed(tmp_path):
    old = _raw(tmp_path / "exp_output/KALSHI_HISTORY/raw", "2026-10-02", age=40)
    fresh = _raw(tmp_path / "exp_output/KALSHI_HISTORY/raw", "2026-11-18", age=0.1)
    held = _raw(tmp_path / "exp_output/PRICE_ARCHIVE", "2026-10-02", age=40)
    held.rename(held.with_name("prices_2026-10-02.jsonl"))
    held = held.with_name("prices_2026-10-02.jsonl")
    pl = dr.plan(tmp_path, NOW)
    assert [r["path"] for r in pl["compress"]] == ["exp_output/KALSHI_HISTORY/raw/raw_2026-10-02.jsonl"]
    assert [r["path"] for r in pl["held"]] == ["exp_output/PRICE_ARCHIVE/prices_2026-10-02.jsonl"]
    assert pl["saved_compress"] > 0 and pl["saved_held"] > 0
    res = dr.apply(tmp_path, NOW)
    assert [(r[0], r[1]) for r in res] == [("exp_output/KALSHI_HISTORY/raw/raw_2026-10-02.jsonl", True)]
    assert not old.exists() and fresh.exists() and held.exists()                       # fresh + held untouched


def test_dry_run_changes_nothing(tmp_path, capsys):
    p = _raw(tmp_path / "exp_output/KALSHI_HISTORY/thin")
    before = (p.stat().st_size, p.stat().st_mtime)
    assert dr.main(["--root", str(tmp_path)]) == 0
    out = capsys.readouterr().out
    assert "dry run" in out and "raw_2026-10-02.jsonl" in out and "journald" in out
    assert (p.stat().st_size, p.stat().st_mtime) == before and not Path(str(p) + ".gz").exists()


def test_every_policy_target_with_verified_readers_is_covered_by_a_reader_test():
    # adding a verified target requires adding its reader test here (this list is the checklist)
    assert {t.name for t in dr.POLICY if t.readers_verified} == {"kalshi_history_raw", "kalshi_history_thin_raw", "json_bak"}


# ---- each reader of the KALSHI_HISTORY raw stores still reads a compressed day -----------------------------------------------------
def _write_store(d: Path):
    s = bs.Store(d, now=datetime(2026, 10, 2, tzinfo=timezone.utc), sha="x")
    s.put("markets_page", "A", {"markets": [{"ticker": "T1"}]}, "u")
    s.put("candles", "T1|1|0|1", {"candlesticks": []}, "u")
    s._lock.close()
    return d / "raw_2026-10-02.jsonl"


def test_store_rows_index_and_digest_unchanged_after_compression(tmp_path):
    p = _write_store(tmp_path)
    s1 = bs.Store(tmp_path, now=datetime(2026, 10, 3, tzinfo=timezone.utc), sha="x")
    d1, rows1 = s1.digest(), list(s1.rows())
    s1._lock.close()
    _age(p, 40)
    assert dr.compress_verified(str(p))[0] and not p.exists()
    s2 = bs.Store(tmp_path, now=datetime(2026, 10, 3, tzinfo=timezone.utc), sha="x")
    assert s2.digest() == d1                                       # decompressed bytes identical -> digest identical
    assert list(s2.rows()) == rows1 and list(s2.rows("candles")) == [r for r in rows1 if r["kind"] == "candles"]
    assert s2.put("markets_page", "A", {"markets": [{"ticker": "T1"}]}, "u") == "skipped"     # index was rebuilt from the .gz
    s2._lock.close()


def test_gate_done_keys_reads_gz(tmp_path):
    p = _write_store(tmp_path)
    want = gate.done_keys(str(tmp_path))
    _age(p, 40)
    dr.compress_verified(str(p))
    assert want and gate.done_keys(str(tmp_path)) == want


def test_efficiency_load_and_store_glob_read_gz(tmp_path):
    spec = importlib.util.spec_from_file_location("thin_eff2", REPO / "12_EXPLORATORY" / "thin_markets" / "efficiency.py")
    ef = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(ef)
    p = tmp_path / "raw_2026-10-16.jsonl"
    p.write_text("".join(json.dumps(r) + "\n" for r in ROWS))
    want = ef.load([str(p)])
    _age(p, 40)
    assert dr.compress_verified(str(p))[0]
    paths = sorted(ef._dated_files(tmp_path, "raw_*.jsonl"))
    assert paths == [str(p)] and ef.load(paths) == want
    assert gzip.open(str(p) + ".gz").read()                         # the file is really gzip on disk
