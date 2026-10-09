"""W61.2 Part B: end-to-end rehearsal of the first-look release on a SYNTHETIC cell in a temp repo.
Cron (13:49 UTC) -> scripts/calibration_engine.py -> unseal at judged n -> frozen manifest -> REPORT -> dashboard.
Never touches real ledgers."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))
import generate_project_state as gps  # noqa: E402

CELL = "NFL_NFL_MONEYLINE_T1"


def _game(i: int) -> dict:
    st = f"2026-10-{1 + i // 20:02d}T{(i % 20):02d}:00:00Z"
    return {"market_ticker": f"SYN-{i:04d}", "band": "T1", "ts_utc": st, "game_key": f"SYNG{i:04d}", "p_yes": 0.62,
            "mid": 0.50, "yes_bid": 0.49, "yes_ask": 0.51, "y": 1.0 if i % 3 else 0.0, "p_clim": 0.5, "start_time_utc": st}


def _write(root: Path, n: int) -> None:
    d = root / "exp_output/PREGAME_SHADOW"
    (d / "settled").mkdir(parents=True, exist_ok=True)
    rows = [_game(i) for i in range(n)]
    for p in (d / f"{CELL}.jsonl", d / "settled" / f"{CELL}.jsonl"):
        p.write_text("".join(json.dumps(r) + "\n" for r in rows))


def _cron(root: Path) -> str:
    r = subprocess.run([sys.executable, str(REPO / "scripts/calibration_engine.py"), "--repo", str(root)],
                       capture_output=True, text=True, check=True)
    return r.stdout


def test_release_end_to_end(tmp_path):
    _write(tmp_path, 59)
    out = _cron(tmp_path)
    assert "SEALED (59 of 60)" in out
    cal = tmp_path / "exp_output/CALIBRATION"
    assert not list((cal / "release_manifests").glob("*")) if (cal / "release_manifests").exists() else True
    assert not (cal / "FIRST_LOOK_REPORT.md").exists()
    sealed_json = json.loads(sorted(cal.glob("engine_*.json"))[-1].read_text())
    assert not any("scores" in c or "verdict" in c for c in sealed_json["cells"])

    _write(tmp_path, 60)                                     # game 60 settles; next daily run
    out = _cron(tmp_path)
    assert "JUDGED" in out
    man = json.loads((cal / "release_manifests" / f"{CELL}.look60.json").read_text())
    assert len(man["games"]) == 60 and man["cell"] == CELL
    eng = json.loads(sorted(cal.glob("engine_*.json"))[-1].read_text())
    c = next(x for x in eng["cells"] if x["cell"] == CELL)
    assert c["verdict"]["verdict"] in {"RULED_OUT", "SHADOW", "CANDIDATE-PENDING-CAPACITY"} and c["scores"]
    rep = cal / "FIRST_LOOK_REPORT.md"                       # the operator-readable report lands next to the engine output
    txt = rep.read_text()
    assert CELL in txt and c["verdict"]["verdict"] in txt and "SYNTHETIC" not in txt.split("\n")[0]

    html = gps.render_html({"generated": "x", "repo": "r", "sections": {"calibration": gps.sec_calibration(tmp_path)}, "ops": {}})
    sec = html[html.index("id='calibration'"):html.index("</section>", html.index("id='calibration'"))]
    assert "JUDGED" in sec and "Brier model" in sec and f"verdict <b>{c['verdict']['verdict']}</b>" in sec

    before = man
    _write(tmp_path, 75)                                     # later games never rewrite the frozen look
    _cron(tmp_path)
    assert json.loads((cal / "release_manifests" / f"{CELL}.look60.json").read_text()) == before
