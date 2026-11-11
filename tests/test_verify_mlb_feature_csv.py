"""W57.1 / GG-489: the off-box feature CSV gate must refuse a stale CSV and leave no meta file."""
import subprocess
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]


def test_refuses_stale_csv(tmp_path):
    csv = tmp_path / "f.csv"
    pd.DataFrame({"player_id": [1], "game_date": ["2026-01-01"]}).to_csv(csv, index=False)
    meta = tmp_path / "m.json"
    r = subprocess.run(
        [sys.executable, str(ROOT / "scripts/verify_mlb_feature_csv.py"), str(csv), "--meta-out", str(meta)],
        capture_output=True, text=True, env={"PYTHONPATH": str(ROOT / "src"), "PATH": ""},
    )
    assert r.returncode == 1
    assert not meta.exists()


# ---- W109.5: explicit off-season clean skip ----
import importlib.util
from datetime import date

from prediction_market_bot.c1_signal_ingestion.validators import ContractFailure

_spec = importlib.util.spec_from_file_location("vmfc", ROOT / "scripts/verify_mlb_feature_csv.py")
_v = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_v)


def _stale():
    return ContractFailure(source_id="s", check_type="staleness_halt", severity="HALT", reason="r", payload={})


def _other():
    return ContractFailure(source_id="s", check_type="schema_missing", severity="HALT", reason="r", payload={})


def test_skip_when_zero_games():
    r = _v.off_season_skip([_stale()], 7, date(2026, 11, 10), fetch=lambda u: {"dates": []})
    assert r and "off-season" in r


def test_no_skip_when_games_in_window():
    f = lambda u: {"dates": [{"games": [{"gamePk": 1}]}]}
    assert _v.off_season_skip([_stale()], 7, date(2026, 11, 10), fetch=f) is None


def test_no_skip_when_schedule_fetch_fails():
    def boom(u):
        raise OSError("down")
    assert _v.off_season_skip([_stale()], 7, date(2026, 11, 10), fetch=boom) is None


def test_no_skip_when_other_halt_present():
    assert _v.off_season_skip([_stale(), _other()], 7, date(2026, 11, 10), fetch=lambda u: {"dates": []}) is None
