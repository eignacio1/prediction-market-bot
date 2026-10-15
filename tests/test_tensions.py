"""W75.3 Part B: tension registers have the required fields, seeds are present, evidence names real files, renders are current."""
import re, sys, tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
T = ROOT / "02_ARCHITECTURE_DESIGN" / "TENSIONS"
FIELDS = ("id", "title", "status", "where", "evidence", "pillar", "relief")


def _reg(sport):
    return tomllib.loads((T / f"{sport}.toml").read_text())


def test_every_tension_has_all_fields_and_unique_ids():
    for sport in ("nfl", "nba"):
        ids = []
        for t in _reg(sport)["tension"]:
            for f in FIELDS:
                assert t.get(f, "").strip(), (sport, t.get("id"), f)
            ids.append(t["id"])
        assert len(ids) == len(set(ids))


def test_evidence_cites_an_existing_file_or_gap():
    for sport in ("nfl", "nba"):
        for t in _reg(sport)["tension"]:
            paths = re.findall(r"[\w./-]+\.(?:md|toml|py|json)\b", t["evidence"])
            gaps = re.findall(r"GG-\d+", t["evidence"])
            assert paths or gaps, (sport, t["id"])
            for p in paths:
                assert (ROOT / p).exists(), (sport, t["id"], p)


def test_nfl_seeds_present():
    text = " ".join(t["title"] + t["evidence"] + t["where"] for t in _reg("nfl")["tension"])
    for needle in ("GG-730", "GG-756", "GG-746", "treatment", "E3", "interpretation", "ADR-0075"):
        assert needle in text, needle


def test_renders_current():
    sys.path.insert(0, str(ROOT / "scripts"))
    import render_tensions
    for sport in ("nfl", "nba"):
        assert (T / f"{sport.upper()}_TENSIONS.md").read_text() == render_tensions.render(T / f"{sport}.toml")
