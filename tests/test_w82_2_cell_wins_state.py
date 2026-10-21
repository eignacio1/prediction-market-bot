"""W82.2 Part B: WINS is the only green state; RULED_OUT is mapped; an unresolvable join is never green."""
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "src"))

import cell_display_state as cds  # noqa: E402

POS = {"status": "JUDGED", "sport": "NFL", "band": "T1", "market_type": "GAME_TOTAL", "cell": "NFL_NFL_GAME_TOTAL_T1",
       "verdict": {"verdict": "CANDIDATE-PENDING-CAPACITY"}}


def test_wins_on_positive_released_verdict_for_shadow_cell():
    ec = cds.resolve_engine_cell([POS], "NFL_GAME_TOTAL", "T1")
    assert cds.display_state("shadow", ec) == "wins"


def test_not_wins_when_verdict_not_positive_or_not_judged():
    neg = {**POS, "verdict": {"verdict": "SHADOW"}}
    assert cds.display_state("shadow", neg) == "shadow"
    assert cds.display_state("shadow", {**POS, "status": "PRELIMINARY"}) == "shadow"
    assert cds.display_state("shadow", {**POS, "status": "SEALED", "verdict": None}) == "shadow"


def test_staked_cell_needs_pnl_ci_above_zero():
    assert cds.display_state("active", POS) == "active"
    assert cds.display_state("active", POS, (-0.2, 0.4)) == "active"
    assert cds.display_state("active", POS, (None, 0.4)) == "active"
    assert cds.display_state("active", POS, (0.01, 0.4)) == "wins"


def test_ruled_out_is_mapped_and_unknown_status_is_unmapped_not_green():
    assert cds.display_state("ruled_out", None) == "ruled_out"
    assert cds.display_state("brand_new_status", None) == "unmapped"


def test_unresolvable_join_is_not_green():
    assert cds.resolve_engine_cell([], "NFL_GAME_TOTAL", "T1") is None
    assert cds.resolve_engine_cell([POS], "NFL_SPREAD", "T1") is None          # no such engine cell
    assert cds.resolve_engine_cell([POS, dict(POS)], "NFL_GAME_TOTAL", "T1") is None   # ambiguous
    assert cds.resolve_engine_cell([{**POS, "cell": "BOGUS"}], "NFL_GAME_TOTAL", "T1") is None
    assert cds.display_state("shadow", cds.resolve_engine_cell([], "NFL_GAME_TOTAL", "T1")) == "shadow"


def test_every_registry_status_is_mapped_in_helper_and_dashboard_js():
    from prediction_market_bot.c5_execution.market_type_registry import CellStatus
    js = (ROOT / "04_EXECUTION/visual_dashboard/script.js").read_text()
    scls = re.search(r"const SCLASS=\{([^}]*)\}", js).group(1)
    for s in CellStatus:
        assert s.value in cds.DISPLAY_OF_STATUS, s
        assert re.search(rf"\b{s.value}:", scls), s


def test_builder_marks_no_cell_wins_without_engine_and_green_class_only_for_wins():
    import build_visual_dashboard_html as b
    cs = b.cells()
    assert all(c["d"] != "wins" for c in cs.values()) or b._engine_cells()
    head = (ROOT / "04_EXECUTION/visual_dashboard/head.html").read_text()
    green = [m for m in re.findall(r"\.cellbox\.(\w+)\{background:var\(--good\)", head)]
    assert green == ["win"]
