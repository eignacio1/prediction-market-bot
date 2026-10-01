"""T-602: settlement writer -- idempotency, append-not-overwrite, partial-fetch refusal, provenance."""
import importlib.util
import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

SPEC = importlib.util.spec_from_file_location(
    "capture_settlements", Path(__file__).resolve().parents[1] / "scripts" / "capture_settlements.py")
cs = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(cs)

NOW = datetime(2026, 10, 1, 12, 0, 0, tzinfo=timezone.utc)
PROVENANCE = ("ticker", "family", "result", "settlement_ts", "source_url", "content_sha256",
              "retrieved_utc", "runtime_commit_sha")


def mk(ticker, result="yes", ts="2026-09-30T03:00:00Z", status="finalized", **kw):
    m = {"ticker": ticker, "event_ticker": "EV-" + ticker, "status": status, "result": result,
         "settlement_ts": ts, "expiration_value": "", "settlement_value_dollars": "1.0000",
         "market_type": "binary"}
    m.update(kw)
    return m


@pytest.fixture
def archive(tmp_path):
    d = tmp_path / "arch"
    d.mkdir()
    rows = [{"ticker": "A-1", "series_ticker": "KXA"}, {"ticker": "A-2", "series_ticker": "KXA"},
            {"ticker": "B-1", "series_ticker": "KXB"}]
    (d / "prices_2026-09-30.jsonl").write_text("\n".join(json.dumps(r) for r in rows) + "\n")
    # the set-aside file must never be read
    (d / "prices_2026-08-01.jsonl.BROKEN_FIRSTRUN").write_text(
        json.dumps({"ticker": "Z-9", "series_ticker": "KXZ"}) + "\n")
    return str(d)


def getter(markets, fail_on=None):
    calls = []

    def get(url):
        calls.append(url)
        if fail_on and fail_on in url:
            raise cs.FetchFailed("boom")
        t = url.rsplit("/", 1)[-1]
        if t in markets:
            return {"market": markets[t]}
        raise cs.FetchFailed("404 " + url)
    get.calls = calls
    return get


def rows_of(store):
    out = []
    for p in sorted(Path(store).glob("settlements_*.jsonl")):
        out += [json.loads(x) for x in p.read_text().splitlines()]
    return out


def test_capture_writes_provenance(archive, tmp_path):
    store = tmp_path / "s"
    mkts = {t: mk(t) for t in ("A-1", "A-2", "B-1")}
    s = cs.capture(archive, store, get=getter(mkts), now=NOW, sha="abc123")
    assert s["written"] == 3 and not s["failed_series"]
    for r in rows_of(store):
        for f in PROVENANCE:
            assert r[f] not in (None, ""), f
        assert r["runtime_commit_sha"] == "abc123" and r["retrieved_utc"] == "2026-10-01T12:00:00Z"
    assert "Z-9" not in {r["ticker"] for r in rows_of(store)}


def test_idempotent_second_run_writes_nothing_and_does_not_fetch(archive, tmp_path):
    store = tmp_path / "s"
    mkts = {t: mk(t) for t in ("A-1", "A-2", "B-1")}
    cs.capture(archive, store, get=getter(mkts), now=NOW, sha="x")
    before = (store / "settlements_2026-10-01.jsonl").read_bytes()
    g = getter(mkts)
    s = cs.capture(archive, store, get=g, now=NOW, sha="x")
    assert s["written"] == 0 and s["already_captured"] == 3 and g.calls == []
    assert (store / "settlements_2026-10-01.jsonl").read_bytes() == before


def test_append_never_overwrites_existing(archive, tmp_path):
    store = tmp_path / "s"
    cs.capture(archive, store, get=getter({"A-1": mk("A-1"), "A-2": mk("A-2")}), now=NOW, sha="x",
               series_filter=["KXA"])
    first = (store / "settlements_2026-10-01.jsonl").read_bytes()
    # B-1 arrives later; prior bytes must be a strict prefix
    cs.capture(archive, store, get=getter({"A-1": mk("A-1", result="no"), "B-1": mk("B-1")}),
               now=NOW, sha="x")
    after = (store / "settlements_2026-10-01.jsonl").read_bytes()
    assert after.startswith(first) and len(after) > len(first)
    a1 = [r for r in rows_of(store) if r["ticker"] == "A-1"]
    assert len(a1) == 1 and a1[0]["result"] == "yes"       # upstream flip NOT applied by capture


def test_changed_upstream_appends_revision_row(archive, tmp_path):
    store = tmp_path / "s"
    cs.capture(archive, store, get=getter({"A-1": mk("A-1"), "A-2": mk("A-2")}), now=NOW, sha="x",
               series_filter=["KXA"])
    first = rows_of(store)[0]
    assert cs.apply_revision(store, mk("A-1", result="no"), "KXA", "u", NOW, "x") is True
    assert cs.apply_revision(store, mk("A-1", result="no"), "KXA", "u", NOW, "x") is False
    rs = [r for r in rows_of(store) if r["ticker"] == "A-1"]
    assert len(rs) == 2 and rs[0] == first and rs[1]["revises_content_sha256"] == first["content_sha256"]


def test_failed_fetch_writes_nothing_for_series_and_other_series_survive(archive, tmp_path):
    store = tmp_path / "s"
    mkts = {t: mk(t) for t in ("A-1", "A-2", "B-1")}
    s = cs.capture(archive, store, get=getter(mkts, fail_on="A-2"), now=NOW, sha="x")
    assert [f["series"] for f in s["failed_series"]] == ["KXA"]
    assert {r["ticker"] for r in rows_of(store)} == {"B-1"}      # no partial KXA rows
    assert cs.main.__name__ == "main"


def test_non_terminal_not_written(archive, tmp_path):
    store = tmp_path / "s"
    mkts = {"A-1": mk("A-1", status="active", result=""), "A-2": mk("A-2", ts=""), "B-1": mk("B-1")}
    s = cs.capture(archive, store, get=getter(mkts), now=NOW, sha="x")
    assert {r["ticker"] for r in rows_of(store)} == {"B-1"} and s["not_terminal_or_absent"] == 2


def test_hash_ignores_volatile_fields_but_tracks_result():
    a, b = mk("T"), mk("T", volume=99, last_price=5)
    assert cs.content_hash(a) == cs.content_hash(b)
    assert cs.content_hash(a) != cs.content_hash(mk("T", result="no"))


def test_reconcile_reports_mismatch_and_missing(archive, tmp_path):
    store = tmp_path / "s"
    cs.capture(archive, store, get=getter({t: mk(t) for t in ("A-1", "A-2", "B-1")}), now=NOW, sha="x")
    cache = tmp_path / "c"
    cache.mkdir()
    (cache / "KXA.json").write_text(json.dumps({
        "A-1": {"result": "yes", "expiration_value": "", "settlement_ts": "2026-09-30T03:00:00Z"},
        "A-2": {"result": "no", "expiration_value": "", "settlement_ts": "2026-09-30T03:00:00Z"},
        "OTHER": {"result": "yes", "expiration_value": "", "settlement_ts": "t"}}))
    rep = cs.reconcile(store, str(cache), archive)
    assert rep["series"]["KXA"]["agree"] == 1 and rep["series"]["KXA"]["field_mismatch"] == 1
    assert rep["series"]["KXA"]["cache_only_not_in_archive"] == 1
    assert [d["ticker"] for d in rep["discrepancies"]] == ["A-2"]
