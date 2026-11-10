"""W107.2 Part C: news-burst capture -- fixture client (no network), RSS, lock, cap, installer idempotency."""
import fcntl, json, resource, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import news_burst_capture as nb  # noqa: E402
import news_burst_capture_install as ins  # noqa: E402


class FakeClient:
    def __init__(self, n=15):
        self.calls = 0
        self.n = n

    def get(self, path, **p):
        self.calls += 1
        return {"markets": [{"ticker": f"KXNBAGAME-26NOV10AAABBB-{i}", "event_ticker": "E", "yes_bid": 40, "yes_ask": 42,
                             "volume": 5} for i in range(self.n)], "cursor": ""}, "h"


class Clock:
    def __init__(self): self.t = 1_800_000_000.0
    def now(self): return self.t
    def sleep(self, s): self.t += s


def test_sweeps_one_call_each_and_rows(tmp_path):
    c, k = FakeClient(), Clock()
    r = nb.run(c, tmp_path, minutes=2, interval=20, sha="x", now_fn=k.now, sleep=k.sleep)
    assert c.calls == r["sweeps"] == 6 and r["rows"] == 6 * 15
    f = next(tmp_path.glob("burst_*.jsonl"))
    row = json.loads(f.read_text().splitlines()[0])
    assert row["yes_bid"] == 40 and row["writer"] == nb.WRITER


def test_interval_and_minutes_are_clamped(tmp_path):
    c, k = FakeClient(1), Clock()
    r = nb.run(c, tmp_path, minutes=999, interval=1, sha="x", now_fn=k.now, sleep=k.sleep)
    assert r["sweeps"] == nb.MAX_MINUTES * 60 // nb.MIN_INTERVAL_S


def test_lock_blocks_second_burst(tmp_path):
    h = open(tmp_path / ".lock", "w"); fcntl.flock(h, fcntl.LOCK_EX)
    assert nb.run(FakeClient(), tmp_path, sha="x") == {"skipped": True}


def test_daily_cap_stops_writing(tmp_path, monkeypatch):
    monkeypatch.setattr(nb, "MAX_DAILY_BYTES", 1000)
    c, k = FakeClient(), Clock()
    r = nb.run(c, tmp_path, minutes=30, interval=20, sha="x", now_fn=k.now, sleep=k.sleep)
    assert r["capped"] == 1 and r["sweeps"] < 90


def test_peak_rss_fixture(tmp_path):
    """A full 30-min burst over a 60-market fixture must not grow memory (nothing is accumulated)."""
    c, k = FakeClient(60), Clock()
    before = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    nb.run(c, tmp_path, minutes=30, interval=20, sha="x", now_fn=k.now, sleep=k.sleep)
    grow = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss - before
    div = 1 if sys.platform == "darwin" else 1024
    assert grow / div / 1024 < 20      # < 20 MB growth (ru_maxrss bytes on macOS, KB on Linux)


def test_installer_refuses_when_red_and_is_idempotent():
    red = lambda: {"budget": "RED", "reasons": ["x"]}
    wrote = []
    assert ins.install(red, read=lambda: "a\n", write=wrote.append) == 0 and not wrote
    green = lambda: {"budget": "GREEN"}
    cur = "# keep\n0 1 * * * job\n"
    store = {"t": cur}
    ins.install(green, read=lambda: store["t"], write=lambda t: store.update(t=t))
    assert ins.BEGIN in store["t"] and "# keep" in store["t"] and "news_burst_capture.py" in store["t"]
    once = store["t"]
    ins.install(green, read=lambda: store["t"], write=lambda t: store.update(t=t))
    assert store["t"] == once
    ins.uninstall(read=lambda: store["t"], write=lambda t: store.update(t=t))
    assert store["t"] == cur
