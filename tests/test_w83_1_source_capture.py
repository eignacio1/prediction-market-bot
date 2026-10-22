import gzip
import importlib.util
import json
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


def _load(name, rel):
    spec = importlib.util.spec_from_file_location(name, REPO / rel)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


sc = _load("source_capture_nfl", "scripts/source_capture_nfl.py")
si = _load("source_capture_install", "scripts/source_capture_install.py")
NOW = datetime(2026, 10, 21, 21, 41, tzinfo=timezone.utc)

WPDT = ('<script>{"datePublished":"2026-10-20T04:00:55-04:00","dateModified":"2026-10-20T12:18:53-04:00"}</script>'
        '<table id="jtrt_table_1"><thead><tr><th>Nav</th></tr></thead><tr><td>x</td></tr></table>'
        '<table id="table_1"><thead><tr><th>Team</th><th>Man Rate</th><th>Zone Rate</th></tr></thead><tbody>'
        '<tr id="r1"><td>Cleveland Browns</td><td>41.7</td><td>54.9</td></tr>'
        '<tr id="r2"><td>Chicago Bears</td><td>31.9</td><td>64.8</td></tr></tbody></table>')
PERS = ('<table class="pt-pre"><caption>Pers</caption><thead><tr><th scope="col">#</th><th scope="col">Offense</th>'
        '<th scope="col">11</th><th scope="col">Plays</th></tr></thead><tbody>'
        '<tr><td>1</td><th scope="row"><abbr title="Arizona Cardinals">ARI</abbr> Arizona Cardinals</th>'
        '<td>59%</td><td>399</td></tr></tbody></table>')


def test_parse_wpdt_ignores_nav_table_and_floats_values():
    p = sc.parse_wpdt(WPDT)
    assert p["columns"] == ["Team", "Man Rate", "Zone Rate"]
    assert p["rows"][0] == {"team": "Cleveland Browns", "values": {"Man Rate": 41.7, "Zone Rate": 54.9}}


def test_parse_personnel_uses_abbr_title_and_percent():
    r = sc.parse_personnel(PERS)["rows"][0]
    assert r["team"] == "Arizona Cardinals" and r["abbr"] == "ARI" and r["rank"] == 1.0
    assert r["values"] == {"11": 59.0, "Plays": 399.0}


def test_as_of_from_json_ld():
    assert sc.parse_as_of(WPDT) == ("2026-10-20T04:00:55-04:00", "2026-10-20T12:18:53-04:00")
    assert sc.parse_as_of("<html></html>") == (None, None)


def test_snapshot_written_once_then_unchanged_and_never_overwritten(tmp_path):
    r1 = sc.capture_card("sharp-coverage-schemes", tmp_path, NOW, WPDT)
    assert r1["status"] == "written"
    d = tmp_path / "sharp-coverage-schemes"
    snap = json.loads(next(d.glob("*.json")).read_text())
    assert snap["as_of"] == "2026-10-20T12:18:53-04:00" and snap["n_rows"] == 2
    assert gzip.decompress(next(d.glob("*.html.gz")).read_bytes()).decode() == WPDT
    r2 = sc.capture_card("sharp-coverage-schemes", tmp_path, NOW.replace(minute=50), WPDT)
    assert r2["status"] == "unchanged" and len(list(d.glob("*.json"))) == 1
    changed = WPDT.replace("41.7", "42.0")
    r3 = sc.capture_card("sharp-coverage-schemes", tmp_path, NOW.replace(hour=22), changed)
    assert r3["status"] == "written" and len(list(d.glob("*.json"))) == 2


def test_daily_cap_skips_write(tmp_path, monkeypatch):
    monkeypatch.setattr(sc, "DAILY_BYTES_CAP", 1)
    assert sc.capture_card("sharp-coverage-schemes", tmp_path, NOW, WPDT)["status"] == "daily_cap_skipped"
    assert not list(tmp_path.glob("*/*.json"))


def test_main_logs_error_per_page_and_continues(tmp_path, monkeypatch):
    calls = []

    def fake(url):
        calls.append(url)
        if "coverage" in url:
            raise OSError("boom")
        return PERS if "personnel" in url else WPDT
    monkeypatch.setattr(sc, "fetch", fake)
    assert sc.main(["--store", str(tmp_path)]) == 1
    lines = [json.loads(l) for l in (tmp_path / "checks.jsonl").read_text().splitlines()]
    assert len(lines) == len(sc.CARDS) == len(calls)
    assert {l["card"]: l["status"] for l in lines}["sharp-coverage-schemes"] == "error"
    assert sum(l["status"] == "written" for l in lines) == len(sc.CARDS) - 1


def test_fragment_is_the_registered_line_and_installer_is_idempotent():
    frag = (REPO / "deploy" / "cron.source_capture").read_text()
    blk = si.fragment_block(frag)
    assert blk[0] == si.BEGIN and blk[-1] == si.END
    assert any(l.startswith("41 21 * * 2,3 ") and "scripts/source_capture_nfl.py" in l for l in blk)
    assert frag.strip() in (REPO / "deploy" / "cron.conf").read_text()
    state = {"cron": "5 * * * * a\n"}
    green = lambda: {"budget": "GREEN"}  # noqa: E731
    si.install(live_fn=green, read=lambda: state["cron"], write=lambda t: state.update(cron=t))
    after = state["cron"]
    assert after.startswith("5 * * * * a\n") and after.count(si.BEGIN) == 1
    si.install(live_fn=green, read=lambda: state["cron"], write=lambda t: state.update(cron=t))
    assert state["cron"] == after


def test_install_refuses_when_red():
    w = []
    si.install(live_fn=lambda: {"budget": "RED", "reasons": ["x"]}, read=lambda: "", write=w.append)
    assert w == []
