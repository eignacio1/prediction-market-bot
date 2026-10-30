"""GG-1460: safe_out() resolves relative paths against 12_EXPLORATORY/, so a literal that already starts with
'12_EXPLORATORY/' writes to 12_EXPLORATORY/12_EXPLORATORY/. No exploratory script may do that."""
import re
from pathlib import Path

EXPLORATORY = Path(__file__).resolve().parent.parent / "12_EXPLORATORY"
PAT = re.compile(r"""safe_out\(\s*f?["']12_EXPLORATORY/""")


def test_no_safe_out_literal_has_doubled_prefix():
    bad = [str(p.relative_to(EXPLORATORY)) for p in EXPLORATORY.rglob("*.py") if PAT.search(p.read_text())]
    assert bad == []


def test_pattern_catches_the_original_defect():
    assert PAT.search('open(safe_out("12_EXPLORATORY/nfl_board_v2/x.json"), "w")')
    assert not PAT.search('open(safe_out("nfl_board_v2/x.json"), "w")')
