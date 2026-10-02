"""generate_project_state.py (Wave 47 / 47.1 D6 h): fixture repo, missing sources, current main, /project route."""
from __future__ import annotations

import json
import subprocess
import sys
import threading
import urllib.request
from http.server import HTTPServer
from pathlib import Path

import pytest

_REPO = Path(__file__).parent.parent
sys.path.insert(0, str(_REPO / "scripts"))
import generate_project_state as gps  # noqa: E402
import web_dashboard as wd  # noqa: E402


def _w(root: Path, rel: str, text: str) -> None:
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text)


@pytest.fixture
def fixture_repo(tmp_path):
    r = tmp_path / "repo"
    r.mkdir()
    subprocess.run(["git", "-C", str(r), "init", "-q"], check=True)
    _w(r, gps.GAP_LOG,
       "### GG-001 — Old open\n\n**Status:** OPEN · **Severity:** HIGH\nregistered 2026-09-01\n"
       "### GG-002 — Closed one\n\n**Status:** RESOLVED · **Severity:** LOW\n"
       "### GG-003 — Newest open\n\n**Status:** OPEN · **Severity:** UNSPECIFIED\n2026-10-01\n")
    _w(r, gps.DECISION_LOG, "## 2026-10-01 — first\nx\n## 2026-10-02 — second\ny\n")
    _w(r, "03_DECISIONS/ADR-0001_a.md", "# ADR-0001: Alpha\n\n**Status:** ACCEPTED\n")
    _w(r, "03_DECISIONS/ADR-0002_b.md", "# ADR-0002: Beta (PROPOSED)\n\n**Status:** PROPOSED — drafted\n")
    _w(r, f"{gps.EXP_DIR}/EXP900_FOO_PREREGISTRATION_2026-10-01.md", "# EXP-900 — Does foo work?\n")
    _w(r, f"{gps.RESULTS_DIR}/EXP900_RESULTS_foo.md", "# EXP-900 results — FAILED\n")
    _w(r, gps.QUEUE, "## Wave 47 — fired\n\n## Needs your decision\n\n| Item | Plain | Cost |\n|---|---|---|\n"
                     "| **Thing A** | do it | cost |\n\n---\n")
    _w(r, gps.QUEUE_ARCHIVE, "## Wave 46 — CLOSED ok\n")
    _w(r, "exp_output/MLB/mlb_feature_matrix.csv", "game_date,x\n2026-09-27,1\n2026-09-26,2\n")
    return r


class TestFixtureRepo:
    def test_governance_counts_and_order(self, fixture_repo):
        g = gps.build_state(fixture_repo)["sections"]["governance"]
        assert g["open"] == 2 and g["live_entries"] == 3
        assert g["by_severity"]["HIGH"] == 1 and g["by_severity"]["UNSPECIFIED"] == 1
        assert g["newest"][0]["id"] == "GG-003"

    def test_adr_proposed_vs_accepted(self, fixture_repo):
        d = gps.build_state(fixture_repo)["sections"]["decisions"]
        assert d["adr_counts"] == {"ACCEPTED": 1, "PROPOSED": 1}
        assert d["latest"][0]["date"] == "2026-10-02"

    def test_experiment_question_and_verdict(self, fixture_repo):
        e = gps.build_state(fixture_repo)["sections"]["experiments"]["items"][0]
        assert "Does foo work" in e["question"] and "FAILED" in e["verdict"]
        assert e["verdict_source"].endswith("EXP900_RESULTS_foo.md")

    def test_queue_needs_decision_and_waves(self, fixture_repo):
        q = gps.build_state(fixture_repo)["sections"]["queue"]
        assert q["needs_decision"][0]["item"] == "Thing A"
        assert len(q["waves"]) == 2

    def test_data_store_rows_and_newest(self, fixture_repo):
        s = gps.build_state(fixture_repo)["sections"]["data"]["stores"][0]
        assert s["rows"] == 2 and s["newest_record"] == "2026-09-27"

    def test_missing_sources_say_awaiting_not_zero(self, tmp_path):
        S = gps.build_state(tmp_path)["sections"]
        assert S["governance"]["awaiting"] and S["queue"]["awaiting"] and S["experiments"]["awaiting"]
        assert all(s.get("awaiting") for s in S["data"]["stores"])

    def test_every_section_has_source_and_as_of_key(self, fixture_repo):
        for k, v in gps.build_state(fixture_repo)["sections"].items():
            assert "source" in v and "as_of" in v, k

    def test_html_stamp_links_and_no_live_calls(self, fixture_repo):
        st = gps.build_state(fixture_repo)
        h = gps.render_html(st, static=True)
        assert "generated " in h and "OFFLINE SNAPSHOT" in h
        assert 'href="./03_DECISIONS/GOVERNANCE_GAP_LOG.md"' in h
        assert "http://" not in h.replace("http://www.w3.org", "") and "<script" not in h

    def test_html_escapes_untrusted_text(self, fixture_repo):
        _w(fixture_repo, gps.QUEUE, "## Needs your decision\n\n| I | P |\n|--|--|\n| **<script>x</script>** | y |\n\n---\n")
        h = gps.render_html(gps.build_state(fixture_repo))
        assert "<script>x" not in h


class TestCurrentMain:
    def test_builds_on_this_checkout_without_exception(self):
        st = gps.build_state(_REPO)
        json.dumps(st, default=str)
        assert st["sections"]["governance"]["open"] > 0
        assert st["sections"]["registry"]["total"] >= 92
        assert st["sections"]["experiments"]["items"]

    def test_cli_writes_json_and_static_html(self, tmp_path):
        j, h = tmp_path / "s.json", tmp_path / "v.html"
        assert gps.main(["--json", str(j), "--html", str(h)]) == 0
        assert json.loads(j.read_text())["sections"] and "as of origin/main" in h.read_text()


class TestProjectRoute:
    @pytest.fixture
    def server(self, tmp_path, monkeypatch):
        monkeypatch.setattr(wd, "_log_dir", tmp_path)
        wd._PROJECT_CACHE.update(t=0.0, html="")
        srv = HTTPServer(("127.0.0.1", 0), wd.DashboardHandler)
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        yield srv
        srv.shutdown()

    def _get(self, srv, path):
        with urllib.request.urlopen(f"http://127.0.0.1:{srv.server_address[1]}{path}", timeout=30) as r:
            return r.status, r.read().decode()

    def test_project_served_with_back_link_and_cached(self, server, monkeypatch):
        st, body = self._get(server, "/project")
        assert st == 200 and 'href="/"' in body and "Project State" in body
        calls = []
        monkeypatch.setattr(wd, "_PROJECT_TTL_S", 60.0)
        orig = wd._PROJECT_CACHE["html"]
        st2, body2 = self._get(server, "/project")
        assert body2 == orig == body  # served from the <=60 s cache

    def test_terminal_links_to_project(self):
        assert 'href="/project"' in wd._HTML

    def test_project_never_500s_when_generator_breaks(self, server, monkeypatch):
        monkeypatch.setitem(sys.modules, "generate_project_state", None)
        st, body = self._get(server, "/project")
        assert st == 200 and "awaiting generate_project_state" in body
