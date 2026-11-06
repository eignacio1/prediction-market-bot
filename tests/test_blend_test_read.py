"""W105.1 Part C: the gated read prints nothing but counts before a planned look."""
import datetime as dt
import importlib.util
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("blend_test_read", ROOT / "scripts" / "blend_test_read.py")
btr = importlib.util.module_from_spec(spec)
spec.loader.exec_module(btr)

DAY = dt.date(2026, 11, 1)


def _rows_finals(n_games, fam="NBA_MONEYLINE", seed=1):
    rng = random.Random(seed)
    rows, finals = [], {}
    for g in range(n_games):
        d = DAY + dt.timedelta(days=g // 9)
        h, a = f"H{g}", f"A{g}"
        pm = rng.uniform(0.3, 0.7)
        rows.append({"family": fam, "game_date": d.isoformat(), "home": h, "away": a, "subject": h, "strike_n": None,
                     "p_market": pm, "p_engine": min(0.95, pm + rng.uniform(-0.1, 0.1))})
        finals[(h, a)] = [(d, (100 + rng.randint(-9, 9), 100))]
    return rows, finals


def test_before_first_look_prints_only_counts():
    rows, finals = _rows_finals(40)
    data = btr.cell_rows(rows, "NBA_MONEYLINE", finals)
    c = btr.cell_at_look(data, "v1", dt.date(2026, 12, 1))
    assert c["reads"] == {} and c["n"] > 0
    out = btr.render({"cells": {"v1/NBA_MONEYLINE": {**c, "decision": "NOT AT A LOOK"}}, "holm": {}})
    assert "n so far" in out and "z=" not in out and "w~" not in out


def test_look_uses_only_first_n_games():
    rows, finals = _rows_finals(150)
    data = btr.cell_rows(rows, "NBA_MONEYLINE", finals)
    c = btr.cell_at_look(data, "v1", dt.date(2026, 12, 1))
    assert c["reached"] == [1] and c["reads"][1]["games"] == 100
    c2 = btr.cell_at_look(data[:140], "v1", dt.date(2026, 12, 1))
    assert c2["reads"][1]["z"] == c["reads"][1]["z"]


def test_after_hard_stop_no_reads():
    rows, finals = _rows_finals(150)
    c = btr.cell_at_look(btr.cell_rows(rows, "NBA_MONEYLINE", finals), "v1", dt.date(2027, 5, 1))
    assert c["reads"] == {}


def test_v3_looks_scaled():
    assert btr.look_counts("v3") == [25, 50, 75, 100] and btr.look_counts("v1") == [100, 200, 300, 400]


def test_build_empty_box(tmp_path):
    res = btr.build(tmp_path, {}, DAY)
    assert len(res["cells"]) == 12 and all(c["decision"] == "NOT AT A LOOK" for c in res["cells"].values())
    assert len(btr.render(res)) < 60_000
