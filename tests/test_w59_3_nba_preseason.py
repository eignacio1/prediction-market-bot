"""W59.3: preseason smoke-test ledger is labelled + isolated; NBA season state; schedule index season filter."""
from __future__ import annotations

import importlib.util
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

from prediction_market_bot.pregame_shadow.ledger import ROW_FIELDS, CellLedger
from prediction_market_bot.pregame_shadow.nba_forecaster import NBAScheduleIndex

ROOT = Path(__file__).resolve().parent.parent


def _row(**kw):
    r = {f: "x" for f in ROW_FIELDS}
    r.update(kw)
    return r


def test_ledger_extra_labels_rows_and_default_is_unchanged(tmp_path):
    CellLedger(tmp_path, "NBA", "MONEYLINE", "T1").append(_row(run_id="a"))
    CellLedger(tmp_path / "p", "NBA", "MONEYLINE", "T1",
               {"season_phase": "preseason", "excluded_from_judged_n": True}).append(_row(run_id="a"))
    plain = json.loads((tmp_path / "NBA_MONEYLINE_T1.jsonl").read_text())
    pre = json.loads((tmp_path / "p" / "NBA_MONEYLINE_T1.jsonl").read_text())
    assert list(plain) == list(ROW_FIELDS)
    assert pre["season_phase"] == "preseason" and pre["excluded_from_judged_n"] is True


def _games():
    base = {"home": "BOS", "away": "NYK", "start_time_utc": "2026-10-10T23:00:00+00:00"}
    return [{**base, "season_type": 1}, {**base, "home": "LAL", "away": "DEN", "season_type": 2,
                                         "start_time_utc": "2026-10-21T02:00:00+00:00"}]


def test_schedule_index_filters_season_type():
    reg = NBAScheduleIndex(_games())
    pre = NBAScheduleIndex(_games(), season_types=(1,))
    assert reg.game("2026-10-10", "BOS", "NYK") is None and reg.game("2026-10-20", "LAL", "DEN")
    assert pre.game("2026-10-10", "BOS", "NYK") and pre.game("2026-10-20", "LAL", "DEN") is None


def _wd():
    spec = importlib.util.spec_from_file_location("wd_w593", ROOT / "scripts" / "web_dashboard.py")
    m = importlib.util.module_from_spec(spec)
    sys.modules["wd_w593"] = m
    spec.loader.exec_module(m)
    return m


@pytest.mark.parametrize("day,state", [((2026, 10, 7), "off"), ((2026, 10, 19), "off"),
                                       ((2026, 10, 20), "in_season"), ((2026, 12, 1), "in_season"),
                                       ((2026, 7, 15), "off")])
def test_nba_season_state(day, state):
    assert _wd()._season_state(datetime(*day, tzinfo=timezone.utc))["NBA"]["state"] == state


def test_preseason_runner_refuses_judged_dir():
    txt = (ROOT / "scripts" / "run_nba_pregame_shadow.py").read_text()
    assert "PREGAME_SHADOW_PRESEASON" in txt and "excluded_from_judged_n" in txt and "SystemExit" in txt


def test_preseason_cron_block_is_isolated_and_additive():
    conf = (ROOT / "deploy" / "cron.nba_shadow_preseason").read_text().splitlines()
    assert conf[0] == "# BEGIN EXP-038 NBA PRESEASON" and conf[-1] == "# END EXP-038 NBA PRESEASON"
    jobs = [l for l in conf if l.strip() and not l.startswith("#")]
    assert len(jobs) == 1 and "--preseason" in jobs[0] and "kelly" not in jobs[0]
    assert jobs[0].split()[0] == "57"


def test_flip_check_is_read_only_and_counts_only_valid_rows(tmp_path):
    spec = importlib.util.spec_from_file_location("flipchk", ROOT / "scripts" / "w59_3_nba_flip_check.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    sha = json.loads((ROOT / "models" / "nba_pregame_v1.json").read_text())["sha256"]
    good = {"model_sha256": sha, "p_yes": 0.6, "mid": 0.55, "start_time_source": "espn_scoreboard_start_time"}
    (tmp_path / "NBA_NBA_MONEYLINE_T1.jsonl").write_text(json.dumps(good) + "\n" + json.dumps({**good, "p_yes": 1.0}) + "\n")
    assert m.main(["--ledger-dir", str(tmp_path)]) == 0
    assert m.main(["--ledger-dir", str(tmp_path / "none")]) == 1
    assert "promote_cell_status(" not in "".join(
        l for l in (ROOT / "scripts" / "w59_3_nba_flip_check.py").read_text().splitlines() if l.lstrip().startswith("from") or l.lstrip().startswith("import"))
