"""T-602: depth writer -- same-slot idempotency, append-only, failure refusal, provenance, event balance."""
import importlib.util
import json
from datetime import datetime, timezone
from pathlib import Path

SPEC = importlib.util.spec_from_file_location(
    "capture_depth", Path(__file__).resolve().parents[1] / "scripts" / "capture_depth.py")
cd = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(cd)

NOW = datetime(2026, 10, 1, 12, 20, tzinfo=timezone.utc)


def fake(n_events=6, per_event=3, fail=None):
    mk = [{"ticker": f"S-E{e}-{k}", "event_ticker": f"E{e}", "status": "active",
           "close_time": "2026-10-02T00:00:00Z"} for e in range(n_events) for k in range(per_event)]
    calls = []

    def get(url):
        calls.append(url)
        if "/orderbook" in url:
            if fail and fail in url:
                raise cd.FetchFailed("boom")
            return {"orderbook_fp": {"yes_dollars": [["0.40", "100.00"], ["0.39", "50.00"]],
                                     "no_dollars": [["0.58", "80.00"]]}}
        return {"markets": mk, "cursor": ""}
    get.calls = calls
    return get


def rows(store):
    return [json.loads(x) for p in sorted(Path(store).glob("depth_*.jsonl")) for x in p.read_text().splitlines()]


def test_writes_full_ladder_and_provenance(tmp_path):
    s = cd.capture(tmp_path, ["S"], 5, get=fake(), now=NOW, sha="abc", sleep=lambda _: None)
    assert s["written"] == 5 and not s["failed"]
    for r in rows(tmp_path):
        assert r["book"]["yes"] and r["book_sha256"] and r["source_url"].endswith("/orderbook")
        assert r["runtime_commit_sha"] == "abc" and r["slot"] == "2026-10-01T12:00Z"


def test_event_balanced_maximises_distinct_events(tmp_path):
    cd.capture(tmp_path, ["S"], 6, get=fake(6, 3), now=NOW, sha="x", sleep=lambda _: None)
    assert len({r["event_ticker"] for r in rows(tmp_path)}) == 6


def test_rerun_same_slot_adds_nothing(tmp_path):
    cd.capture(tmp_path, ["S"], 5, get=fake(), now=NOW, sha="x", sleep=lambda _: None)
    before = (tmp_path / "depth_2026-10-01.jsonl").read_bytes()
    s = cd.capture(tmp_path, ["S"], 5, get=fake(), now=NOW, sha="x", sleep=lambda _: None)
    assert s["written"] == 0 and s["skipped_already_in_slot"] == 5
    assert (tmp_path / "depth_2026-10-01.jsonl").read_bytes() == before


def test_next_slot_appends_without_touching_prior_rows(tmp_path):
    cd.capture(tmp_path, ["S"], 5, get=fake(), now=NOW, sha="x", sleep=lambda _: None)
    before = (tmp_path / "depth_2026-10-01.jsonl").read_bytes()
    cd.capture(tmp_path, ["S"], 5, get=fake(), now=NOW.replace(hour=13), sha="x", sleep=lambda _: None)
    after = (tmp_path / "depth_2026-10-01.jsonl").read_bytes()
    assert after.startswith(before) and len(rows(tmp_path)) == 10


def test_failed_orderbook_writes_no_row_and_is_reported(tmp_path):
    s = cd.capture(tmp_path, ["S"], 5, get=fake(fail="/S-E"), now=NOW, sha="x", sleep=lambda _: None)
    assert s["written"] == 0 and len(s["failed"]) == 5 and rows(tmp_path) == []


def test_failed_listing_skips_series_only(tmp_path):
    def get(url):
        if "series_ticker=BAD" in url:
            raise cd.FetchFailed("x")
        return fake()(url)
    s = cd.capture(tmp_path, ["BAD", "S"], 3, get=get, now=NOW, sha="x", sleep=lambda _: None)
    assert [f["series"] for f in s["failed"]] == ["BAD"] and s["written"] == 3
