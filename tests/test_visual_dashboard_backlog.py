"""Backlog panel (operator 2026-10-30): injected by the builder, error shown not blank, never green."""
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import build_visual_dashboard_html as bvd  # noqa: E402

VD = ROOT / "04_EXECUTION" / "visual_dashboard"


def _payload(html):
    line = next(l for l in html.splitlines() if l.startswith("const BACKLOG = "))
    return json.loads(line[len("const BACKLOG = "):].rstrip(";"))


def test_build_injects_the_panel(tmp_path):
    out = tmp_path / "vd.html"
    bvd.build(out)
    html = out.read_text()
    assert 'id="backlog"' in html and "function backlog()" in html and "__BACKLOG__" not in html
    d = _payload(html)
    assert d["ok"] and [g for g, _ in d["groups"]][0] == "NOW"


def test_missing_source_reaches_the_page_as_a_visible_error(tmp_path, monkeypatch):
    import rolling_backlog
    monkeypatch.setattr(bvd, "backlog", lambda: rolling_backlog.load(tmp_path))
    out = tmp_path / "vd.html"
    bvd.build(out)
    html = out.read_text()
    d = _payload(html)
    assert d["ok"] is False and d["error"]
    # the renderer branches on !ok into a visible card rather than an empty host
    js = (VD / "script.js").read_text()
    fn = js[js.index("function backlog()"):]
    fn = fn[:fn.index("\n}\n")]
    assert "bl-err" in fn and "did not validate" in fn


def test_panel_never_uses_green():
    css = (VD / "head.html").read_text()
    js = (VD / "script.js").read_text()
    pcss = css[css.index("ROLLING BACKLOG"):css.index("@media print{")]
    pjs = js[js.index("function backlog()"):]
    pjs = pjs[:pjs.index("\n}\n")]
    for tok in ("--good", "--s3"):
        assert tok not in pcss and tok not in pjs
