"""Proof-calendar age panel (W102.4 Part C): value, red past one day, visible error, injected into the page."""
import datetime as dt
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import build_visual_dashboard_html as bvd  # noqa: E402
import proof_calendar_age as pca  # noqa: E402

NOW = dt.datetime(2026, 11, 5, 12, 0, 0, tzinfo=dt.timezone.utc)


def _root(tmp_path, header):
    (tmp_path / "04_EXECUTION").mkdir()
    (tmp_path / "04_EXECUTION" / "PROOF_CALENDAR.md").write_text(f"# PROOF CALENDAR\n\n{header}\n")
    return tmp_path


def test_age_value_and_not_red(tmp_path):
    r = pca.load(_root(tmp_path, "from the box read of 2026-11-05T00:00:00Z."), NOW)
    assert r["ok"] and r["age_days"] == 0.5 and r["red"] is False


def test_red_when_older_than_one_day(tmp_path):
    r = pca.load(_root(tmp_path, "from the box read of 2026-11-03T12:00:00Z."), NOW)
    assert r["ok"] and r["age_days"] == 2.0 and r["red"] is True


def test_missing_file_and_bad_stamp_are_visible_errors(tmp_path):
    assert pca.load(tmp_path, NOW)["ok"] is False
    assert pca.load(_root(tmp_path, "no stamp here"), NOW)["error"]
    (tmp_path / "04_EXECUTION" / "PROOF_CALENDAR.md").write_text("x\nfrom the box read of 2026-13-45T99:00:00Z\n")
    assert pca.load(tmp_path, NOW)["ok"] is False


def test_real_file_parses():
    assert pca.load(ROOT)["ok"]


def test_build_injects_panel(tmp_path):
    out = tmp_path / "vd.html"
    bvd.build(out)
    html = out.read_text()
    assert 'id="caHost"' in html and "function calendarAge()" in html and "__CALAGE__" not in html
    line = next(l for l in html.splitlines() if l.startswith("const CALAGE = "))
    assert "ok" in json.loads(line[len("const CALAGE = "):].rstrip(";"))
    assert "ca-err" in html and "could not be read" in html
