"""W119.4 / B-103: every reader of PRICE_ARCHIVE (prices_*/depth_*) reads a day stored plain OR as .gz and sees the same rows."""
from __future__ import annotations

import gzip
import importlib.util
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
from prediction_market_bot import io_jsonl as J  # noqa: E402

ROWS = [{"run_ts": "2026-10-01T12:00:00Z", "ticker": "KXNBAGAME-26OCT01AAABBB-AAA", "series_ticker": "KXNBAGAME",
         "event_ticker": "KXNBAGAME-26OCT01AAABBB", "yes_bid": 0.4, "yes_ask": 0.44, "yes_mid": 0.42, "volume": 10},
        {"run_ts": "2026-10-01T12:20:00Z", "ticker": "KXNBAGAME-26OCT01AAABBB-AAA", "series_ticker": "KXNBAGAME",
         "event_ticker": "KXNBAGAME-26OCT01AAABBB", "yes_bid": 0.41, "yes_ask": 0.45, "yes_mid": 0.43, "volume": 12}]


def _write(d: Path, name: str, rows, gz: bool) -> Path:
    d.mkdir(parents=True, exist_ok=True)
    body = "".join(json.dumps(r) + "\n" for r in rows).encode()
    p = d / (name + (".gz" if gz else ""))
    p.write_bytes(gzip.compress(body) if gz else body)
    return p


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    sys.path.insert(0, str(path.parent))
    try:
        spec.loader.exec_module(m)
    finally:
        sys.path.pop(0)
    return m


# ---- the helper -----------------------------------------------------------------------------------------------------
def test_open_jsonl_plain_and_gz_are_byte_identical(tmp_path):
    a = _write(tmp_path / "a", "prices_2026-10-01.jsonl", ROWS, False)
    b = _write(tmp_path / "b", "prices_2026-10-01.jsonl", ROWS, True)
    with J.open_jsonl(a, "rb") as x, J.open_jsonl(tmp_path / "b" / "prices_2026-10-01.jsonl", "rb") as y:
        assert x.read() == y.read()
    assert list(J.iter_jsonl(a)) == list(J.iter_jsonl(b)) == ROWS


def test_open_jsonl_is_read_only_and_missing_raises(tmp_path):
    with pytest.raises(ValueError):
        J.open_jsonl(tmp_path / "x.jsonl", "w")
    with pytest.raises(FileNotFoundError):
        J.open_jsonl(tmp_path / "nope.jsonl")


def test_listing_helpers_dedupe_and_name_gz_days_plainly(tmp_path):
    _write(tmp_path, "prices_2026-10-01.jsonl", ROWS, True)
    _write(tmp_path, "prices_2026-10-02.jsonl", ROWS, False)
    _write(tmp_path, "prices_2026-10-02.jsonl", ROWS, True)  # both forms: listed once
    want = [str(tmp_path / "prices_2026-10-01.jsonl"), str(tmp_path / "prices_2026-10-02.jsonl")]
    assert J.jsonl_files(tmp_path, "prices_*.jsonl") == want == J.glob_files(str(tmp_path / "prices_*.jsonl"))
    assert [str(p) for p in J.jsonl_paths(tmp_path, "prices_*.jsonl")] == want
    assert J.resolve(want[0]).endswith(".gz") and not J.resolve(want[1]).endswith(".gz")


# ---- src readers: same answer plain vs gz ---------------------------------------------------------------------------
@pytest.mark.parametrize("gz", [False, True])
def test_archive_book_load_ticks(tmp_path, gz):
    from prediction_market_bot.c5_execution.placement import archive_book as ab
    _write(tmp_path, "prices_2026-10-01.jsonl", ROWS, gz)
    got = ab.load_ticks(tmp_path, {"KXNBAGAME-26OCT01AAABBB-AAA"}, ["2026-10-01", "2026-10-09"])
    assert [t[1:] for t in got["KXNBAGAME-26OCT01AAABBB-AAA"]] == [(0.4, 0.44), (0.41, 0.45)]


@pytest.mark.parametrize("gz", [False, True])
def test_nba_live_read_archive(tmp_path, gz):
    from prediction_market_bot.nba_engine import live
    _write(tmp_path, "prices_2026-10-01.jsonl", ROWS, gz)
    assert len(live.read_archive("2026-10-01", tmp_path)) == 2


@pytest.mark.parametrize("gz", [False, True])
def test_mlb_market_line_last_pregame(tmp_path, gz):
    from prediction_market_bot.mlb_engine import market_line as ml
    ev = "KXMLBGAME-26OCT011900NYYBOS"
    rows = [{"run_ts": "2026-10-01T18:00:00Z", "ticker": ev + "-NYY", "series_ticker": "KXMLBGAME", "event_ticker": ev,
             "yes_bid": 0.5, "yes_ask": 0.54, "volume": 3}]
    _write(tmp_path, "prices_2026-10-01.jsonl", rows, gz)
    df = ml.last_pregame(str(tmp_path / "prices_*.jsonl"))
    assert len(df) in (0, 1)  # parse_event decides eligibility; the point is that the .gz day does not raise or vanish
    plain = tmp_path / "plain"
    _write(plain, "prices_2026-10-01.jsonl", rows, False)
    assert len(df) == len(ml.last_pregame(str(plain / "prices_*.jsonl")))


# ---- script readers: loaders and subset builders --------------------------------------------------------------------
@pytest.mark.parametrize("gz", [False, True])
def test_exploratory_loaders_read_gz(tmp_path, gz):
    _write(tmp_path, "prices_2026-10-01.jsonl", ROWS, gz)
    for rel, nm in (("12_EXPLORATORY/fill_markout/fill_markout.py", "fm"), ("12_EXPLORATORY/forward_entry_cost/entry_cost.py", "ec")):
        m = _load(REPO / rel, nm)
        assert len(list(m.load_jsonl(tmp_path / "prices_2026-10-01.jsonl"))) == 2


@pytest.mark.parametrize("gz", [False, True])
def test_ladder_ride_load_and_repro_archive_files(tmp_path, gz):
    _write(tmp_path, "prices_2026-10-01.jsonl", ROWS, gz)
    repro = _load(REPO / "12_EXPLORATORY/frozen_evidence_check/repro.py", "repro")
    files = repro.archive_files(str(tmp_path))
    assert [os.path.basename(f) for f in files] == ["prices_2026-10-01.jsonl"]
    ll = _load(REPO / "12_EXPLORATORY/ride_ladder/ladder_ride.py", "ll")
    assert ll.load(str(tmp_path)) is not None


def test_repro_subset_links_a_gz_day_under_its_gz_name(tmp_path, monkeypatch):
    _write(tmp_path / "arch", "prices_2026-10-01.jsonl", ROWS, True)
    _write(tmp_path / "arch", "prices_2026-10-05.jsonl", ROWS, False)
    repro = _load(REPO / "12_EXPLORATORY/frozen_evidence_check/repro.py", "repro2")
    monkeypatch.setattr(repro, "under_fence", lambda rel: str(tmp_path / "fence" / rel), raising=False)
    monkeypatch.setattr(repro, "safe_out", lambda p: Path(p).parent.mkdir(parents=True, exist_ok=True) or Path(p), raising=False)
    d = repro.subset(str(tmp_path / "arch"), "2026-10-09")
    Path(d).mkdir(parents=True, exist_ok=True)
    names = sorted(os.listdir(d))
    assert names == ["prices_2026-10-01.jsonl.gz", "prices_2026-10-05.jsonl"]
    assert J.glob_files(os.path.join(d, "prices_*.jsonl")) == [os.path.join(d, n.replace(".gz", "")) for n in names]
    with J.open_jsonl(os.path.join(d, "prices_2026-10-01.jsonl")) as fh:
        assert len(fh.readlines()) == 2


# ---- audit: no reader of the archive is left on a plain glob/open ---------------------------------------------------
ARCHIVE_RE = re.compile(r"""(prices|depth)_(\*|\?\?|20\?\?|\{|2026-|\$\{)|PRICE_GLOB|ARCHIVE_GLOB""")
# 119.3 files adopt the helper next wave (their inputs stay plain until then); writers; comments/docs; separate datasets.
ALLOW = {
    "scripts/run_ride_board.py", "scripts/arm_orders_read.py", "scripts/demo_fill_forward_report.py",
    "scripts/archive_cron_install.py", "scripts/archive_market_prices.py", "scripts/box_tasks.py",
    "scripts/generate_project_state.py", "scripts/thin_market_depth_capture.py",
    "12_EXPLORATORY/quant_w103_prices/analyze.py", "12_EXPLORATORY/ladder_implied/part_b.py",  # already gz-aware
    "12_EXPLORATORY/quant_w94/exact_fee_recompute.py",  # delegates to the converted loaders; only comments name the glob
    "12_EXPLORATORY/mlb_engine/run_w106_4_market.py",  # only passes the glob to market_line.last_pregame (converted)
    "src/prediction_market_bot/disk_retention.py", "src/prediction_market_bot/io_jsonl.py",
}


def _py_files():
    for top in ("src", "scripts", "12_EXPLORATORY"):
        for p in (REPO / top).rglob("*.py"):
            rel = p.relative_to(REPO).as_posix()
            if rel in ALLOW or "/tests/" in rel or p.name.startswith("test_"):
                continue
            yield rel, p


def test_every_archive_reader_goes_through_io_jsonl():
    bad = []
    for rel, p in _py_files():
        code = "\n".join(ln for ln in p.read_text(errors="ignore").splitlines() if not ln.lstrip().startswith("#"))
        if ARCHIVE_RE.search(code) and re.search(r"glob|\.open\(|open\(", code) and "io_jsonl" not in code:
            bad.append(rel)
    assert not bad, f"readers of PRICE_ARCHIVE not on io_jsonl (would break once disk_retention compresses a day): {bad}"


def test_retention_policy_matches_the_audit():
    from prediction_market_bot import disk_retention as dr
    held = {t.name for t in dr.POLICY if not t.readers_verified}
    assert {"pregame_shadow_ledgers", "mlb_inplay_logs"} <= held
    ok = {t.name for t in dr.POLICY if t.readers_verified}
    assert {"price_archive", "price_archive_depth", "frozen_evidence_check_pre"} <= ok
