"""Aggregation web (operator 2026-10-21): MUSE_WEB.json validates, the builder injects it, nothing green."""
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import build_visual_dashboard_html as bvd  # noqa: E402

WEB = ROOT / "02_ARCHITECTURE_DESIGN" / "QUAL_ARCHIVE" / "MUSE_WEB.json"


def test_source_file_validates():
    d = bvd.muse_web()
    assert d["ok"], d.get("error")
    assert d["sports"] == ["NFL", "NBA", "MLB", "NHL"]
    for sp in d["spokes"]:
        assert len(sp["states"]) == len(d["rings"])
        assert set(sp["states"]) <= set(bvd.MUSE_WEB_STATES)


def test_bad_state_is_rejected_not_drawn(tmp_path, monkeypatch):
    d = json.loads(WEB.read_text())
    d["spokes"][0]["states"][0] = "done"
    fake = tmp_path / "02_ARCHITECTURE_DESIGN" / "QUAL_ARCHIVE"
    fake.mkdir(parents=True)
    (fake / "MUSE_WEB.json").write_text(json.dumps(d))
    monkeypatch.setattr(bvd, "ROOT", tmp_path)
    assert bvd.muse_web()["ok"] is False


def test_build_injects_the_web(tmp_path):
    out = tmp_path / "vd.html"
    bvd.build(out)
    html = out.read_text()
    assert 'id="museweb"' in html and "function museWeb()" in html
    assert "__MUSEWEB__" not in html


def test_web_never_uses_green():
    # green is reserved for a cell that WINS (W82.2)
    vd = ROOT / "04_EXECUTION" / "visual_dashboard"
    css = (vd / "head.html").read_text()
    js = (vd / "script.js").read_text()
    web_css = css[css.index("AGGREGATION WEB"):css.index("@keyframes mwPulse")]
    web_js = js[js.index("function museWeb()"):]
    web_js = web_js[:web_js.index("\n}\n")]
    assert "--good" not in web_css and "--good" not in web_js
