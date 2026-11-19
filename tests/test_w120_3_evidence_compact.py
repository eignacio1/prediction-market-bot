"""W120.3 / B-103: the Mac evidence copy is compacted without ever dropping bytes that are not proven kept."""
from __future__ import annotations

import gzip
import importlib.util
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
spec = importlib.util.spec_from_file_location("evidence_compact", REPO / "scripts" / "ops" / "evidence_compact.py")
EC = importlib.util.module_from_spec(spec)
spec.loader.exec_module(EC)

BODY = b"".join(b'{"i": %d, "pad": "xxxxxxxxxxxxxxxx"}\n' % i for i in range(2000))


def _day(root: Path, name: str, body: bytes = BODY, age_days: float = 30, gz: bool = False, plain: bool = True, gz_body: bytes = None):
    d = root / "exp_output" / "PRICE_ARCHIVE"
    d.mkdir(parents=True, exist_ok=True)
    t = time.time() - age_days * 86400
    if plain:
        (d / name).write_bytes(body)
        os.utime(d / name, (t, t))
    if gz:
        (d / (name + ".gz")).write_bytes(gzip.compress(BODY if gz_body is None else gz_body))
        os.utime(d / (name + ".gz"), (t, t))
    return d


def test_plain_duplicate_removed_only_when_gz_matches(tmp_path):
    d = _day(tmp_path, "prices_2026-09-01.jsonl", gz=True)
    r = EC.run(tmp_path, now=datetime.now(timezone.utc))
    assert not (d / "prices_2026-09-01.jsonl").exists() and (d / "prices_2026-09-01.jsonl.gz").exists()
    assert r["dup_removed"][0][1] == "equal" and r["after"] < r["before"]
    with gzip.open(d / "prices_2026-09-01.jsonl.gz", "rb") as g:
        assert g.read() == BODY


def test_plain_prefix_of_newer_gz_is_covered(tmp_path):
    d = _day(tmp_path, "prices_2026-09-02.jsonl", body=BODY[:5000], gz=True)
    r = EC.run(tmp_path, now=datetime.now(timezone.utc))
    assert r["dup_removed"][0][1] == "prefix" and not (d / "prices_2026-09-02.jsonl").exists()


def test_differing_gz_keeps_both(tmp_path):
    d = _day(tmp_path, "prices_2026-09-03.jsonl", gz=True, gz_body=BODY[::-1])
    r = EC.run(tmp_path, now=datetime.now(timezone.utc))
    assert (d / "prices_2026-09-03.jsonl").read_bytes() == BODY and (d / "prices_2026-09-03.jsonl.gz").exists()
    assert r["dup_kept"] == ["exp_output/PRICE_ARCHIVE/prices_2026-09-03.jsonl"]


def test_old_plain_is_compressed_verified_and_young_plain_is_left(tmp_path):
    d = _day(tmp_path, "prices_2026-09-04.jsonl", age_days=30)
    _day(tmp_path, "prices_2026-11-18.jsonl", age_days=1)
    r = EC.run(tmp_path, now=datetime.now(timezone.utc))
    assert not (d / "prices_2026-09-04.jsonl").exists()
    with gzip.open(d / "prices_2026-09-04.jsonl.gz", "rb") as g:
        assert g.read() == BODY
    assert (d / "prices_2026-11-18.jsonl").exists() and not (d / "prices_2026-11-18.jsonl.gz").exists()
    assert len(r["compressed"]) == 1 and not r["failed"]


def test_dry_run_changes_nothing(tmp_path):
    d = _day(tmp_path, "prices_2026-09-05.jsonl", gz=True)
    before = sorted(p.name for p in d.iterdir())
    r = EC.run(tmp_path, dry=True, now=datetime.now(timezone.utc))
    assert sorted(p.name for p in d.iterdir()) == before and r["before"] == r["after"]
