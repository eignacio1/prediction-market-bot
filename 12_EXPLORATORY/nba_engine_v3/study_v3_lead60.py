"""W97.1 Part A: W96.1's held-out v3-vs-v2 study re-run with injury statuses cut at tip-60 (the instant the live arm prices), not tip.

Same protocol, code and bootstrap as study_v3.py (imported, not edited); only the factor frame differs (build_frozen_v3.py --lead-min 60).
Run: PYTHONPATH=src python3 12_EXPLORATORY/nba_engine_v3/study_v3_lead60.py <NBA_EVENTS raw dir> <out json, inside 12_EXPLORATORY/>
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import study_v3 as S  # noqa: E402

LEAD60 = HERE / "w97" / "v3_factors_lead60.parquet"
_real = pd.read_parquet


def _read(path, *a, **k):
    return _real(LEAD60 if Path(path).name == "v3_factors.parquet" else path, *a, **k)


if __name__ == "__main__":
    S.pd.read_parquet = _read
    S.main(sys.argv[1], sys.argv[2])
