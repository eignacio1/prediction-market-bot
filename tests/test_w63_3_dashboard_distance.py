"""W63.3 — Distance-to-optimum panel on /project is rendered from the generator, stacked for 390px."""
import sys
from pathlib import Path

import pytest

_REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_REPO / "scripts"))

import generate_project_state as gps  # noqa: E402


def _render(state):
    return gps.render_html(state)


@pytest.mark.unit
class TestDistancePanel:
    def test_section_present_with_all_measures(self):
        sec = gps.sec_distance(_REPO)
        ids = {m["id"] for m in sec["measures"]}
        assert {"B1", "B2", "B3", "B4", "D1", "D2", "D3", "E1", "E2", "E3", "P1", "P2", "P3"} <= ids
        html = gps._distance_html(sec, lambda t, s: f"<h2>{t}</h2>")
        assert "id='distance'" in html
        for i in ("B1", "E3", "P3"):
            assert f">{i}</td>" in html

    def test_unavailable_and_error_styled_never_guessed(self):
        sec = {"source": "x", "as_of": "t", "measures": [
            {"id": "E1", "status": "UNAVAILABLE", "reason": "no sidecar", "value": None, "source": "s", "as_of": None},
            {"id": "D1", "status": "ERROR", "reason": "declared != meta", "value": None, "source": "s", "as_of": "t"}]}
        html = gps._distance_html(sec, lambda t, s: "")
        assert "class='aw'>UNAVAILABLE: no sidecar" in html
        assert "class='bad'>ERROR: declared != meta" in html

    def test_awaiting_renders_neutral(self):
        html = gps._distance_html(gps._awaiting("distance", "why"), lambda t, s: "")
        assert "no data" in html and "<table" not in html

    def test_390px_layout_is_two_column_stacked(self):
        html = gps._distance_html(gps.sec_distance(_REPO), lambda t, s: "")
        for row in html.split("<tr class='dist'>")[1:]:
            assert row.count("<td") == 2
        assert ".distt td{overflow-wrap:anywhere}" in gps._CSS
