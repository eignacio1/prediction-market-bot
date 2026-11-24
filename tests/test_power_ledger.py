"""W124.1 power ledger: projection rules and a smoke run on a tiny measurement file."""
import importlib.util
import json
import os
from datetime import date

P = os.path.join(os.path.dirname(__file__), "..", "12_EXPLORATORY", "edge_location", "power_ledger", "power_ledger.py")
spec = importlib.util.spec_from_file_location("power_ledger", P)
PL = importlib.util.module_from_spec(spec)
spec.loader.exec_module(PL)


def test_project_in_season_and_reached_and_zero_yield():
    d, _ = PL.project(date(2026, 11, 23), 10, 40, 10.0, "NBA")
    assert d == "2026-12-14"  # 3 weeks
    assert PL.project(date(2026, 11, 23), 50, 40, 5.0, "NBA")[1] == "reached"
    assert PL.project(date(2026, 11, 23), 0, 40, 0.0, "NBA")[0] is None


def test_project_rolls_to_next_season_and_caps_long_waits():
    d, note = PL.project(date(2026, 11, 23), 15, 234, 6.5, "NFL")
    assert d > "2027-09-09" and "resumes" in note
    assert PL.project(date(2026, 11, 23), 20, 3128, 8.0, "NBA")[0] is None


def test_sd_from_interval_and_ledger_smoke(tmp_path):
    assert abs(PL.sdg(-1.0, 1.0, 4) - 2.0 / (2 * 1.6448536269514722) * 2) < 1e-12
    meas = json.load(open(os.path.join(os.path.dirname(P), "variance_measurements.json")))
    led = PL.build(date(2026, 11, 23), meas)
    ids = {r["id"]: r for r in led["rows"]}
    assert ids["H-EDGE-3 NBA lineup confirmations"]["binding"] == "minimum n"
    assert ids["H-EXEC-2 FADE crossing the spread"]["judgeable"] is None
    assert led["p3"]["dated_after"] > led["p3"]["dated_before"]
    assert "RESULT (W124.1)" in PL.md(led, meas)
