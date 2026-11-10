"""W108.5: /visual and /project follow the checkout HEAD (a docs-only deploy never restarts the service), a failed rebuild is
logged and shown, the footer states the served build, and /api/data is encoded without a str+bytes double copy."""
import json
import sys
import threading
import time
import urllib.request
from http.server import HTTPServer
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import web_dashboard as wd  # noqa: E402


def test_head_change_refreshes_without_waiting_for_the_ttl():
    cache = {"t": time.time(), "key": "aaa", "html": "old"}
    calls = []
    build = lambda: calls.append(1) or "new"  # noqa: E731
    out = wd._serve_cached("h1", cache, "html", 300.0, build, key="bbb", key_async_wait_s=5.0)
    assert out == "new" and cache["key"] == "bbb" and len(calls) == 1


def test_head_change_serves_stale_when_the_build_is_slow():
    cache = {"t": time.time(), "key": "aaa", "html": "old"}
    gate = threading.Event()

    def build():
        gate.wait(5)
        return "new"
    t0 = time.time()
    assert wd._serve_cached("h2", cache, "html", 300.0, build, key="bbb", key_async_wait_s=0.2) == "old"
    assert time.time() - t0 < 2
    gate.set()
    for _ in range(100):
        if cache["html"] == "new":
            break
        time.sleep(0.05)
    assert cache["html"] == "new"


def test_failed_rebuild_is_logged_keeps_last_good_and_retries_soon(capsys):
    cache = {"t": time.time() - 1000, "html": "good"}

    def boom():
        raise RuntimeError("disk full")
    wd._serve_cached("h3", cache, "html", 300.0, boom)
    for _ in range(100):
        if cache.get("err"):
            break
        time.sleep(0.05)
    assert cache["html"] == "good" and "RuntimeError: disk full" in cache["err"]
    assert "rebuild of h3 FAILED" in capsys.readouterr().err
    assert time.time() - cache["t"] >= 300.0 - wd._RETRY_AFTER_FAIL_S - 1   # due again within ~15 s, not a full TTL


def test_first_build_failure_uses_fallback():
    cache = {"t": 0.0, "html": ""}

    def boom():
        raise ValueError("x")
    out = wd._serve_cached("h4", cache, "html", 300.0, boom, fallback=lambda e: "fallback:" + type(e).__name__)
    assert out == "fallback:ValueError"


def test_footer_states_build_head_and_failure():
    cache = {"t": 1_700_000_000.0, "built_head": "a" * 40, "err": "OSError: <bad>", "err_t": 1_700_000_100.0}
    f = wd._build_footer(cache).decode()
    assert 'id="dash-build"' in f and "aaaaaaa" in f and "LAST REBUILD FAILED" in f and "&lt;bad&gt;" in f
    assert "2023-11-14T22:13:20Z" in f


def test_footer_flags_behind_checkout(monkeypatch):
    monkeypatch.setattr(wd, "_checkout_head", lambda: "b" * 40)
    f = wd._build_footer({"t": time.time(), "built_head": "a" * 40}).decode()
    assert "BEHIND checkout bbbbbbb" in f


def test_visual_route_has_footer_before_body_end():
    wd._VISUAL_CACHE.update(t=0.0, html="")
    srv = HTTPServer(("127.0.0.1", 0), wd.DashboardHandler)
    t = threading.Thread(target=srv.handle_request, daemon=True)
    t.start()
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{srv.server_port}/visual", timeout=60) as r:
            body = r.read()
            assert int(r.headers["Content-Length"]) == len(body)
            assert b'id="dash-build"' in body and body.rstrip().endswith(b"</html>")
            assert body.rfind(b'id="dash-build"') < body.rfind(b"</body>")
    finally:
        t.join(timeout=5)
        srv.server_close()


def test_data_body_is_identical_compact_json(monkeypatch):
    monkeypatch.setattr(wd, "_load_all_data", lambda: {"a": [1, 2.5, "é"], "t": Path("/x")})
    assert wd._build_data_body() == json.dumps({"a": [1, 2.5, "é"], "t": "/x"}, separators=(",", ":")).encode("utf-8")
