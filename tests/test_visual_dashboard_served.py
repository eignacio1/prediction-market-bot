"""The box serves the Visual Dashboard live at /visual (operator 2026-10-21: one current dashboard, no stale copies)."""
import pathlib
import sys
import threading
import urllib.request
from http.server import HTTPServer

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import web_dashboard as wd  # noqa: E402


def test_visual_page_renders_the_current_build():
    wd._VISUAL_CACHE.update(t=0.0, html="")
    html = wd._visual_page()
    assert 'id="museweb"' in html and "__MUSEWEB__" not in html
    assert 'id="backlog"' in html and "__BACKLOG__" not in html


def test_visual_route_serves_200():
    wd._VISUAL_CACHE.update(t=0.0, html="")
    srv = HTTPServer(("127.0.0.1", 0), wd.DashboardHandler)
    t = threading.Thread(target=srv.handle_request, daemon=True)
    t.start()
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{srv.server_port}/visual", timeout=60) as r:
            body = r.read()
            assert r.status == 200 and b'id="museweb"' in body and b'id="backlog"' in body
    finally:
        t.join(timeout=5)
        srv.server_close()


def test_launcher_opens_the_live_page_not_a_file():
    cmd = (ROOT / "Open Visual Dashboard.command").read_text()
    assert "/visual" in cmd and ".html" not in cmd


def test_page_caches_expire_on_new_checkout_head(monkeypatch):
    """/visual and /project refresh in the background when the checkout moves; the request itself never rebuilds."""
    src = (pathlib.Path(__file__).resolve().parent.parent / "scripts" / "web_dashboard.py").read_text()
    assert src.count("_expire_on_new_head(_") == 2
    cache = {"t": 123.0, "html": "old"}
    monkeypatch.setattr(wd, "_checkout_head", lambda: "a" * 40)
    wd._expire_on_new_head(cache)
    assert cache["t"] == 123.0 and cache["head"] == "a" * 40  # first sighting: no expiry
    monkeypatch.setattr(wd, "_checkout_head", lambda: "b" * 40)
    wd._expire_on_new_head(cache)
    assert cache["t"] == 0.0 and cache["head"] == "b" * 40 and cache["html"] == "old"  # served stale, refreshed off-thread
