"""W60.3 — dashboard truth gaps: NBA shadow row always rendered (GG-525); no 390px overflow (GG-515)."""
import sys
from pathlib import Path

import pytest

_REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_REPO / "scripts"))

import generate_project_state as gps  # noqa: E402
import web_dashboard  # noqa: E402

_NONE_MSG = "no data - awaiting first regular-season rows"


@pytest.mark.unit
class TestNbaRowAlwaysRendered:
    def test_health_pushes_neutral_nba_row_when_no_ledger(self):
        html = (_REPO / "Live Terminal.html").read_text(encoding="utf-8")
        assert "else HEALTH.push({lbl:'SHADOW  NBA ledgers', none:'" + _NONE_MSG + "'})" in html

    def test_none_row_rendered_neutral_not_red(self):
        html = (_REPO / "Live Terminal.html").read_text(encoding="utf-8")
        i = html.index("if(h.none) return")
        row = html[i:i + 260]
        assert 'class="age dim"' in row and "bad" not in row and "warn" not in row

    def test_embedded_page_identical_to_source(self):
        assert web_dashboard._HTML.encode("utf-8") == (_REPO / "Live Terminal.html").read_bytes()


@pytest.mark.unit
class TestNoHorizontalOverflowRules:
    def test_css_wraps_long_cells_and_links(self):
        css = gps._CSS
        assert "td,th,code,.asof,.asof a{overflow-wrap:anywhere}" in css
        assert "section{overflow-x:auto}" in css

    def test_long_source_link_carries_full_url_in_title(self):
        src = "05_RESEARCH_EXPERIMENTS/RESULTS_SUMMARIES/" + "x" * 120 + ".md"
        out = gps._lnk(src, "https://example.test/blob/main/")
        assert f'title="{src}"' in out
        assert gps._lnk("not a path", "p") == '<code title="not a path">not a path</code>'
