"""Edge map panel (W107.1, B-059): injected by the builder, error shown not blank, green only when net > 0 held out."""
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import build_visual_dashboard_html as bvd  # noqa: E402

VD = ROOT / "04_EXECUTION" / "visual_dashboard"


def _payload(html):
    line = next(l for l in html.splitlines() if l.startswith("const EDGEMAP = "))
    return json.loads(line[len("const EDGEMAP = "):].rstrip(";"))


def _fn():
    js = (VD / "script.js").read_text()
    fn = js[js.index("function edgeMap()"):]
    return fn[:fn.index("\n}\n")]


def test_build_injects_the_panel(tmp_path):
    out = tmp_path / "vd.html"
    bvd.build(out)
    html = out.read_text()
    assert 'id="edgemap"' in html and "function edgeMap()" in html and "__EDGEMAP__" not in html
    d = _payload(html)
    assert d["ok"] and len(d["rows"]) >= 30


def test_missing_source_reaches_the_page_as_a_visible_error(tmp_path, monkeypatch):
    monkeypatch.setattr(bvd, "ROOT", tmp_path)
    assert bvd.edge_map()["ok"] is False
    assert "em-err" in _fn() and "did not validate" in _fn()


def test_malformed_row_is_an_error(tmp_path, monkeypatch):
    d = tmp_path / "12_EXPLORATORY" / "edge_map"
    d.mkdir(parents=True)
    (d / "edge_map.json").write_text(json.dumps({"rows": [{"id": "x"}]}))
    monkeypatch.setattr(bvd, "ROOT", tmp_path)
    assert bvd.edge_map()["ok"] is False


def test_green_only_when_net_positive_held_out():
    fn = _fn()
    # green comes solely from the held-out flag, never from a status (redesign SW-9 2026-11-10: family bars + folded rows)
    assert "r.held_out_net_positive===true?'NET POSITIVE':r.status" in fn
    assert "'NET POSITIVE':'pos'" in fn and fn.count("'pos'") == 1
    css = (VD / "head.html").read_text()
    assert ".em-dot.pos,.em-bar .pos{background:var(--good)}" in css
    assert css.count("var(--good)}") >= 1 and ".em-dot.acc" in css


def test_every_green_row_is_flagged_in_the_data():
    rows = json.loads((ROOT / "12_EXPLORATORY" / "edge_map" / "edge_map.json").read_text())["rows"]
    for r in rows:
        if r["held_out_net_positive"]:
            assert r["note"], r["id"]  # a green row must carry its caveat
        assert r["status"] in {"RULED_OUT", "NO EFFECT NET", "ACCRUING", "UNTESTED"}
