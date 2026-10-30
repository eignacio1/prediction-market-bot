"""Rolling backlog (operator 2026-10-30): one reader, grouped in the file's order, bad input is an error not a blank."""
import json
import pathlib
import subprocess
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import rolling_backlog as rb  # noqa: E402


def _t(i, status, order, **kw):
    return {"id": i, "order": order, "status": status, "title": f"title {i}", **kw}


def _write(root, d):
    f = root / rb.SRC
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(d if isinstance(d, str) else json.dumps(d))


def _doc(tickets):
    return {"as_of": "2026-10-30T00:00Z", "ranking": ["a", "b"], "statuses": {"NOW": "in the wave"}, "tickets": tickets}


def test_real_file_validates():
    d = rb.load(ROOT)
    assert d["ok"], d.get("error")
    assert len(d["tickets"]) >= 1


def test_grouping_and_order_on_a_fixture(tmp_path):
    _write(tmp_path, _doc([
        _t("X-3", "LATER", 3), _t("X-1", "NOW", 1), _t("X-5", "DONE", 5),
        _t("X-2", "NOW", 2), _t("X-4", "PARKED", 4), _t("X-6", "NEXT", 6),
    ]))
    d = rb.load(tmp_path)
    assert d["ok"]
    assert [g for g, _ in d["groups"]] == ["NOW", "NEXT", "LATER", "PARKED", "DONE"]
    by = {g: [t["id"] for t in ts] for g, ts in d["groups"]}
    assert by == {"NOW": ["X-1", "X-2"], "NEXT": ["X-6"], "LATER": ["X-3"], "PARKED": ["X-4"], "DONE": ["X-5"]}


@pytest.mark.parametrize("bad", [
    "{not json",
    "[]",
    {"as_of": "x", "ranking": [], "tickets": []},
    {"ranking": [], "tickets": [{"id": "a", "order": 1, "status": "NOW", "title": "t"}]},
])
def test_malformed_file_is_ok_false(tmp_path, bad):
    _write(tmp_path, bad)
    d = rb.load(tmp_path)
    assert d["ok"] is False and d["error"]


def test_missing_file_is_ok_false(tmp_path):
    d = rb.load(tmp_path)
    assert d["ok"] is False and "FileNotFoundError" in d["error"]


def test_duplicate_id_order_and_bad_status_rejected(tmp_path):
    for tickets in (
        [_t("A", "NOW", 1), _t("A", "NOW", 2)],
        [_t("A", "NOW", 1), _t("B", "NOW", 1)],
        [_t("A", "SOON", 1)],
        [_t("A", "NOW", "1")],
    ):
        _write(tmp_path, _doc(tickets))
        assert rb.load(tmp_path)["ok"] is False


def test_markdown_render_greys_done_and_keeps_order(tmp_path):
    _write(tmp_path, _doc([_t("X-1", "DONE", 1, why="w"), _t("X-2", "NOW", 2)]))
    md = rb.render_md(rb.load(tmp_path))
    assert md.index("## NOW") < md.index("## DONE")
    assert "~~title X-1~~" in md and "**why:** w" in md


def test_committed_markdown_matches_the_json():
    r = subprocess.run([sys.executable, str(ROOT / "scripts" / "rolling_backlog.py"), "--check"], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
