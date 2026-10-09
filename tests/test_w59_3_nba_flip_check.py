"""W62.3: fixture proof of what scripts/w59_3_nba_flip_check.py prints once valid regular-season rows exist.

Writes only into pytest tmp_path; never touches exp_output/PREGAME_SHADOW.
"""
import hashlib
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("flip", ROOT / "scripts" / "w59_3_nba_flip_check.py")
flip = importlib.util.module_from_spec(spec)
spec.loader.exec_module(flip)
SHA = hashlib.sha256((ROOT / "models" / "nba_pregame_v1.json").read_bytes()).hexdigest()


def _row(**kw):
    r = {"model_sha256": SHA, "p_yes": 0.55, "mid": 0.5, "start_time_source": "espn"}
    r.update(kw)
    return r


def _write(d, name, rows):
    (d / name).write_text("\n".join(json.dumps(r) for r in rows) + "\n")


def test_empty_dir_exits_1_all_no_rows(tmp_path, capsys):
    assert flip.main(["--ledger-dir", str(tmp_path)]) == 1
    out = capsys.readouterr().out.splitlines()
    assert len(out) == 12 and all(l.startswith("NO-ROWS") for l in out)


def test_valid_rows_flip_only_that_cell(tmp_path, capsys):
    _write(tmp_path, "NBA_NBA_MONEYLINE_T1.jsonl", [_row(), _row(p_yes=1.0), _row(model_sha256="x")])
    _write(tmp_path, "NBA_NBA_SPREAD_T2.jsonl", [_row(mid=None), _row(excluded_from_judged_n=True)])
    assert flip.main(["--ledger-dir", str(tmp_path)]) == 0
    out = capsys.readouterr().out.splitlines()
    ok = [l for l in out if l.startswith("FLIP-OK")]
    assert ok == ['FLIP-OK  NBA_MONEYLINE/T1_MULTI_DAY: 1/3 valid rows -> promote_cell_status('
                  'MarketType.NBA_MONEYLINE, ExecutionBand.T1_MULTI_DAY, CellStatus.SHADOW, superseding_reference="EXP-038")']
    assert any(l.startswith("NO-ROWS  NBA_SPREAD/T2_SAME_DAY: 2 rows, 0 valid") for l in out)
