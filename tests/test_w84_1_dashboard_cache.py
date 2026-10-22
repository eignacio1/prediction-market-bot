"""W84.1: /api/data, /project and /visual are served from a cache refreshed off the request path."""
import sys
import threading
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import web_dashboard as wd  # noqa: E402


def _fresh():
    return {"t": 0.0, "html": ""}


def test_first_request_builds_synchronously_then_serves_cached():
    cache, calls = _fresh(), []
    build = lambda: calls.append(1) or "v%d" % len(calls)  # noqa: E731
    assert wd._serve_cached("t1", cache, "html", 60.0, build) == "v1"
    assert wd._serve_cached("t1", cache, "html", 60.0, build) == "v1"
    assert len(calls) == 1


def test_stale_copy_served_immediately_and_refreshed_once_in_background():
    cache, calls = {"t": time.time() - 100, "html": "old"}, []
    gate = threading.Event()

    def build():
        calls.append(1)
        gate.wait(5)
        return "new"

    # stale -> old returned without waiting for the (blocked) build; repeat requests spawn no second refresh
    assert wd._serve_cached("t2", cache, "html", 60.0, build) == "old"
    assert wd._serve_cached("t2", cache, "html", 60.0, build) == "old"
    gate.set()
    for _ in range(100):
        if cache["html"] == "new":
            break
        time.sleep(0.05)
    assert cache["html"] == "new"
    assert len(calls) == 1


def test_ttl_zero_always_rebuilds():
    cache, calls = _fresh(), []
    build = lambda: calls.append(1) or len(calls)  # noqa: E731
    assert wd._serve_cached("t3", cache, "html", 0.0, build) == 1
    assert wd._serve_cached("t3", cache, "html", 0.0, build) == 2


def test_key_change_forces_synchronous_rebuild():
    cache = {"t": time.time(), "key": "a", "body": b"A"}
    assert wd._serve_cached("t4", cache, "body", 60.0, lambda: b"B", key="b") == b"B"
