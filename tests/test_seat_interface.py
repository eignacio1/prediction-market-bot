"""W75.3 Part A: seat files cover every registered cell of NFL/NBA and cite only evidence that exists."""
import sys, tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
SEATS = ROOT / "02_ARCHITECTURE_DESIGN" / "SEATS"
STAGES = {"aggregated", "interpreted", "applied", "none"}


def _seat(sport):
    return tomllib.loads((SEATS / f"{sport}.toml").read_text())


def _registry_cells(prefix):
    from prediction_market_bot.c5_execution import market_type_registry as r
    reg = r.MARKET_TYPE_REGISTRY
    cells = reg.values() if hasattr(reg, "values") else reg
    return {(c.market_type.value, c.band.value): c.status.value for c in cells if c.market_type.value.startswith(prefix)}


def test_every_registered_cell_has_a_seat_entry_all_sports():
    for sport in ("nfl", "nba", "mlb", "nhl"):
        want = _registry_cells(sport + "_")
        got = {(c["market"], c["band"]): c["status"] for c in _seat(sport)["cell"]}
        assert set(want) <= set(got), (sport, sorted(set(want) - set(got)))
        for k, st in want.items():
            assert got[k] == st, (sport, k)


def test_every_evidence_path_exists_and_stage_is_valid():
    for sport in ("nfl", "nba"):
        d = _seat(sport)
        for x in d["factor"] + d["cell"]:
            assert (ROOT / x["evidence"]).exists(), (sport, x["evidence"])
        for f in d["factor"]:
            assert f["stage"] in STAGES, f
            if f["stage"] != "none":
                assert f["evidence"], f


def test_cell_factor_ids_reference_declared_factors():
    for sport in ("nfl", "nba"):
        d = _seat(sport)
        ids = {f["id"] for f in d["factor"]}
        for c in d["cell"]:
            assert set(c["factors"]) <= ids, (sport, c)


def test_stub_sports_have_no_factors_and_drafts_say_so():
    for sport in ("mlb", "nhl"):
        assert not _seat(sport).get("factor")
    for sport in ("nfl", "nba"):
        assert "v0 DRAFT" in _seat(sport)["meta"]["banner"]


def test_rendered_md_is_current():
    sys.path.insert(0, str(ROOT / "scripts"))
    import render_seat
    for sport in ("nfl", "nba"):
        p = SEATS / f"{sport}.toml"
        assert (SEATS / f"{sport.upper()}_SEAT.md").read_text() == render_seat.render(p)
