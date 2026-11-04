"""Known-answer tests for nba_engine/crew_archive.py (W99.1)."""
import json
import numpy as np
import pandas as pd

from prediction_market_bot.nba_engine.crew_archive import SHRINK_K, crew_features, load_ref_table, norm_name, ref_prior


def _tab():
    return pd.DataFrame([
        dict(ref="a b", box_season=2025, g=60.0, pf=44.0, fta=48.0, pts=230.0),
        dict(ref="c d", box_season=2025, g=60.0, pf=40.0, fta=40.0, pts=220.0),
        dict(ref="a b", box_season=2026, g=60.0, pf=0.0, fta=0.0, pts=0.0),
    ])


def test_norm_name_strips_accents_and_suffix():
    assert norm_name("Jacyn Goble") == "jacyn goble"
    assert norm_name("Marc Davis Jr.") == "marc davis"
    assert norm_name("Tomás Pérez") == "tomas perez"


def test_prior_excludes_same_season():
    f = ref_prior(_tab(), "a b", 2026, "pf")  # only 2025 counts; the 2026 zero row is the season being priced
    league = 42.0
    assert abs(f - ((44 * 60 + SHRINK_K * league) / (60 + SHRINK_K) - league)) < 1e-9 and f > 0
    assert ref_prior(_tab(), "a b", 2025, "pf") == 0.0
    assert ref_prior(_tab(), "zz", 2026, "pf") == 0.0


def test_crew_feature_is_mean_of_members_and_reports_match():
    crews = pd.DataFrame({"game_id": ["g1", "g1", "g1"], "ref": ["a b", "c d", "x y"]})
    cf = crew_features(_tab(), crews, {"g1": 2026}, cols=("pf",))
    a, c = ref_prior(_tab(), "a b", 2026, "pf"), ref_prior(_tab(), "c d", 2026, "pf")
    assert abs(cf.loc["g1", "crew_pf"] - (a + c + 0.0) / 3) < 1e-9
    assert abs(cf.loc["g1", "crew_matched"] - 2 / 3) < 1e-9


def test_loader_maps_archive_start_year_to_box_season(tmp_path):
    d = tmp_path / "L3-split" / "nba"; d.mkdir(parents=True)
    rows = [dict(subject="A B", season=2024, metric="games worked (x)", value=50, population_n=50),
            dict(subject="A B", season=2024, metric="personal fouls per game in games worked (x)", value=41.5, population_n=50),
            dict(subject="A B", season=2024, metric="free-throw attempts per game in games worked (x)", value=44.0, population_n=50),
            dict(subject="A B", season=2024, metric="total points per game in games worked (x)", value=225.0, population_n=50)]
    (d / "referees-2024-25.claims.jsonl").write_text("\n".join(json.dumps(r) for r in rows))
    t = load_ref_table(str(tmp_path))
    assert len(t) == 1 and t.box_season[0] == 2025 and t.pf[0] == 41.5 and t.g[0] == 50
