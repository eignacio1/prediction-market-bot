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
