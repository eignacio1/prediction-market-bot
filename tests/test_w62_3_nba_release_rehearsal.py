"""W62.3 Part B: the W61.2 first-look release, rehearsed for an NBA cell (EXP-038 looks 150 / 400) on a SYNTHETIC
cell in a temp repo: seal at 149, unseal at 150 -> frozen manifest -> REPORT -> dashboard; preseason rows never count;
the n=400 second look writes its own manifest and leaves look150 untouched. Never touches real ledgers."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))
import generate_project_state as gps  # noqa: E402

CELL = "NBA_NBA_MONEYLINE_T1"


def _game(i: int, **kw) -> dict:
    st = f"2026-{10 + i // 600:02d}-{1 + (i // 20) % 28:02d}T{(i % 20):02d}:00:00Z"
    r = {"market_ticker": f"SYN-{i:04d}", "band": "T1", "ts_utc": st, "game_key": f"SYNG{i:04d}", "p_yes": 0.62,
         "mid": 0.50, "yes_bid": 0.49, "yes_ask": 0.51, "y": 1.0 if i % 3 else 0.0, "p_clim": 0.5, "start_time_utc": st}
    r.update(kw)
    return r


def _write(root: Path, n: int, preseason: int = 0) -> None:
    d = root / "exp_output/PREGAME_SHADOW"
    (d / "settled").mkdir(parents=True, exist_ok=True)
    rows = [_game(i) for i in range(n)] + [_game(9000 + i, season_phase="preseason", excluded_from_judged_n=True)
                                           for i in range(preseason)]
    for p in (d / f"{CELL}.jsonl", d / "settled" / f"{CELL}.jsonl"):
        p.write_text("".join(json.dumps(r) + "\n" for r in rows))


def _cron(root: Path) -> str:
    return subprocess.run([sys.executable, str(REPO / "scripts/calibration_engine.py"), "--repo", str(root)],
                          capture_output=True, text=True, check=True).stdout


def _cell(cal: Path) -> dict:
    eng = json.loads(sorted(cal.glob("engine_*.json"))[-1].read_text())
    return next(x for x in eng["cells"] if x["cell"] == CELL)


def test_nba_release_end_to_end(tmp_path):
    cal = tmp_path / "exp_output/CALIBRATION"
    _write(tmp_path, 149, preseason=40)                      # 189 settled rows, only 149 count: still sealed
    out = _cron(tmp_path)
    assert "SEALED (149 of 150)" in out
    assert not (cal / "FIRST_LOOK_REPORT.md").exists()
    c = _cell(cal)
    assert "scores" not in c and "verdict" not in c and c["judged_n"] == 149

    _write(tmp_path, 150, preseason=40)                      # 150th regular-season game settles
    out = _cron(tmp_path)
    assert "JUDGED" in out
    man = json.loads((cal / "release_manifests" / f"{CELL}.look150.json").read_text())
    assert len(man["games"]) == 150 and man["cell"] == CELL and not any(g.startswith("SYNG9") for g in man["games"])
    c = _cell(cal)
    assert c["verdict"]["verdict"] in {"RULED_OUT", "SHADOW", "CANDIDATE-PENDING-CAPACITY", "UNRESOLVED"} and c["scores"]
    txt = (cal / "FIRST_LOOK_REPORT.md").read_text()
    assert CELL in txt and c["verdict"]["verdict"] in txt

    html = gps.render_html({"generated": "x", "repo": "r", "sections": {"calibration": gps.sec_calibration(tmp_path)}, "ops": {}})
    sec = html[html.index("id='calibration'"):html.index("</section>", html.index("id='calibration'"))]
    assert "JUDGED" in sec and f"verdict <b>{c['verdict']['verdict']}</b>" in sec

    first = man
    _write(tmp_path, 300, preseason=40)                      # between looks: look150 stays frozen, no look400 yet
    _cron(tmp_path)
    assert json.loads((cal / "release_manifests" / f"{CELL}.look150.json").read_text()) == first
    assert not (cal / "release_manifests" / f"{CELL}.look400.json").exists()

    _write(tmp_path, 400, preseason=40)                      # second look
    _cron(tmp_path)
    assert json.loads((cal / "release_manifests" / f"{CELL}.look150.json").read_text()) == first
    m2 = json.loads((cal / "release_manifests" / f"{CELL}.look400.json").read_text())
    assert len(m2["games"]) == 400
    assert _cell(cal)["verdict"]["n"] == 400
