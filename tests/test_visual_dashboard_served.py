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


def test_visual_route_serves_200():
    wd._VISUAL_CACHE.update(t=0.0, html="")
    srv = HTTPServer(("127.0.0.1", 0), wd.DashboardHandler)
    t = threading.Thread(target=srv.handle_request, daemon=True)
    t.start()
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{srv.server_port}/visual", timeout=60) as r:
            assert r.status == 200 and b'id="museweb"' in r.read()
    finally:
        t.join(timeout=5)
        srv.server_close()


def test_launcher_opens_the_live_page_not_a_file():
    cmd = (ROOT / "Open Visual Dashboard.command").read_text()
    assert "/visual" in cmd and ".html" not in cmd
