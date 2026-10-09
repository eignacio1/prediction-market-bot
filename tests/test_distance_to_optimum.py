"""W63.3: distance_to_optimum.py with a fixture registry, fixture sidecars/ledgers, fixture model metadata."""
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO / "src"))
import distance_to_optimum as d  # noqa: E402

MANIFEST = json.loads((REPO / d.MANIFEST_REL).read_text())

CELLS = [("A_ML", "T1", "shadow"), ("A_ML", "T2", "shadow"), ("A_ML", "T3", "not_implemented"),
         ("B_PLAYER_PROP", "T4", "active"), ("B_PLAYER_PROP", "T5", "not_implemented"), ("C_PARLAY", "T1", "blocked")]
FAMS = {"A_ML", "B_PLAYER_PROP", "C_PARLAY", "D_NONE"}


def by_id(ms):
    return {m["id"]: m for m in ms}


def test_breadth_counts_from_fixture_registry(tmp_path):
    m = by_id(d.breadth(tmp_path, (CELLS, FAMS)))
    assert m["B1"]["value"] == "3 / 6"
    assert m["B2"]["value"] == "2 / 4"
    assert m["B3"]["value"].startswith("3 of 5") and "T5" in m["B3"]["value"]
    assert m["B4"]["value"] == "1 · 0"


def test_breadth_real_registry_has_five_band_denominator():
    m = by_id(d.breadth(REPO))
    assert m["B1"]["status"] == "OK" and " / " in m["B1"]["value"]
    assert m["B3"]["value"].split()[2] == "5"


def _repo_with_models(tmp_path, feats, declared):
    (tmp_path / "scripts").mkdir()
    man = {**MANIFEST, "models": [{"id": "m1", "arm": "x", "meta": "models/m1.json", "features_key": "feature_names",
                                   "declared_classes": declared}]}
    (tmp_path / d.MANIFEST_REL).write_text(json.dumps(man))
    (tmp_path / "models").mkdir()
    (tmp_path / "models/m1.json").write_text(json.dumps({"feature_names": feats}))
    return tmp_path


def test_d1_match_ok(tmp_path):
    r = _repo_with_models(tmp_path, ["home_rs", "home_sp_ra", "is_home"], ["personnel", "team", "venue"])
    row = d.depth_models(r)[0]
    assert row["status"] == "OK" and row["qualitative"] == 0 and row["features"] == 3


def test_d1_undeclared_class_is_error(tmp_path):
    r = _repo_with_models(tmp_path, ["home_rs", "qual_scouting_grade"], ["team"])
    row = d.depth_models(r)[0]
    assert row["status"] == "ERROR" and "undeclared" in row["reason"] and row["qualitative"] == 1


def test_d1_declared_but_absent_is_error(tmp_path):
    r = _repo_with_models(tmp_path, ["home_rs"], ["team", "weather"])
    assert d.depth_models(r)[0]["status"] == "ERROR"


def test_d1_unclassifiable_feature_is_error(tmp_path):
    r = _repo_with_models(tmp_path, ["home_rs", "zzz"], ["team"])
    assert "unclassifiable" in d.depth_models(r)[0]["reason"]


def test_d1_missing_meta_is_unavailable_not_guess(tmp_path):
    r = _repo_with_models(tmp_path, ["home_rs"], ["team"])
    (r / "models/m1.json").unlink()
    assert d.depth_models(r)[0]["status"] == "UNAVAILABLE"


def test_d1_error_propagates_to_measure(tmp_path):
    r = _repo_with_models(tmp_path, ["home_rs", "qual_x"], ["team"])
    assert by_id(d.depth(r))["D1"]["status"] == "ERROR"


def test_d3_counts_only_proposed_or_accepted_challengers(tmp_path):
    (tmp_path / "12_EXPLORATORY").mkdir()
    (tmp_path / "03_DECISIONS").mkdir()
    (tmp_path / "12_EXPLORATORY/nfl_challenger_prereg.md").write_text("# x\n**Status:** PROPOSED\n**Arm:** NFL\n")
    (tmp_path / "03_DECISIONS/nhl_challenger.md").write_text("**Status:** ACCEPTED\n")
    (tmp_path / "03_DECISIONS/old_challenger.md").write_text("**Status:** DRAFT\n")
    (tmp_path / "03_DECISIONS/unrelated.md").write_text("**Status:** PROPOSED\n")
    r = d.d3(tmp_path)
    assert r["value"].startswith("2 ") and "NFL: 1" in r["value"] and "unspecified: 1" in r["value"]


def _book(tmp_path, key, closed, sidecar):
    pf, sc = d.BOOKS[key]
    (tmp_path / "logs").mkdir(exist_ok=True)
    (tmp_path / pf).write_text(json.dumps({"closed_positions": closed}))
    (tmp_path / sc).write_text("\n".join(json.dumps(r) for r in sidecar))


def _pos(i, outcome, pnl, tk):
    return {"position_id": f"p{i}", "outcome": outcome, "pnl": pnl, "kalshi_ticker": tk, "band": "T4M-PROJ"}


def test_execution_from_fixture_sidecars(tmp_path):
    closed = [_pos(1, "LOSS", -2.0, "KX-G1-A"), _pos(2, "WIN", 1.0, "KX-G2-A"), _pos(3, "LOSS", -2.0, "KX-G3-A"),
              _pos(4, "WIN", 1.0, "KX-G4-A"), _pos(5, "WIN", 1.0, "KX-G5-A")]
    side = [{"position_id": "p1", "fill_class": "CONFIRMED_FILLED"}, {"position_id": "p3", "fill_class": "CONFIRMED_FILLED"},
            {"position_id": "p2", "fill_class": "CONFIRMED_NOT_FILLED"}, {"position_id": "p4", "fill_class": "CONFIRMED_NOT_FILLED"},
            {"position_id": "p5", "fill_class": "UNVERIFIABLE"}]
    _book(tmp_path, "t4_mlb", closed, side)
    m = by_id(d.execution(tmp_path))
    assert "t4_mlb: 2 / 5 = 40.0%" in m["E1"]["value"]
    assert "-2.00" in m["E2"]["value"] and "n=2" in m["E2"]["value"]
    assert "fills 0.0% (n=2) vs non-fills 100.0% (n=2)" in m["E3"]["value"]
    assert any("t1_mlb" in x for x in m["E1"]["unavailable"])      # absent book reported, never guessed


def test_execution_missing_everything_is_unavailable(tmp_path):
    m = by_id(d.execution(tmp_path))
    assert all(m[k]["status"] == "UNAVAILABLE" and m[k]["reason"] for k in ("E1", "E2", "E3"))


def test_proof_unavailable_without_engine(tmp_path):
    assert all(x["status"] == "UNAVAILABLE" for x in d.proof(tmp_path))


def test_proof_from_fixture_engine(tmp_path):
    (tmp_path / "exp_output/CALIBRATION").mkdir(parents=True)
    cells = [{"cell": "a", "release": True, "verdict": "KEEP", "projection": {"date": "2026-11-02"}},
             {"cell": "b", "projection": {"date": "2026-11-09"}}, {"cell": "c", "projection": {"date": None}}]
    (tmp_path / "exp_output/CALIBRATION/engine_1.json").write_text(json.dumps({"generated": "2026-10-09T00:00:00Z", "cells": cells}))
    (tmp_path / "12_EXPLORATORY").mkdir()
    (tmp_path / d.EXPECT_REL).write_text("- **Vs market, every cell:** KEEP ACCRUING ≈ 91%. RULED_OUT ≈ 9%\n")
    m = by_id(d.proof(tmp_path))
    assert m["P1"]["value"] == "1 / 3" and m["P2"]["value"] == "1"
    assert m["P3"]["value"].startswith("2026-11-02") and "KEEP ACCRUING ~91%" in m["P3"]["value"]


def test_every_value_has_source_and_asof_key():
    for m in d.compute(REPO)["measures"]:
        assert m["source"] and "as_of" in m and (m["status"] == "OK" or m.get("reason"))


def test_exit_zero_unless_strict(tmp_path, capsys):
    assert d.main(["--repo", str(REPO)]) == 0
