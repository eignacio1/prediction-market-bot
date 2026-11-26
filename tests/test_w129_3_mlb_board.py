"""W129.3 Part B: MLB daily board runner (silent-exit rule) and installer (gate, block, arm-date alarm)."""
import importlib.util
import json
from datetime import date, datetime, timezone
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]


def _load(name, rel):
    import sys
    sys.path.insert(0, str(ROOT / "scripts")); sys.path.insert(0, str(ROOT / "src"))
    sp = importlib.util.spec_from_file_location(name, ROOT / rel)
    m = importlib.util.module_from_spec(sp); sp.loader.exec_module(m)
    return m


bd = _load("mlb_board_daily_t", "scripts/mlb_board_daily.py")
bi = _load("mlb_board_install_t", "scripts/mlb_board_install.py")
NOW = datetime(2027, 4, 2, 15, 0, tzinfo=timezone.utc)


def _root(tmp, n_games=3, inputs=True, age_h=1):
    s = tmp / "exp_output/MLB_GAME/cache_w47"; s.mkdir(parents=True)
    pd.DataFrame({"start_utc": ["2027-04-02T23:05:00Z"] * n_games + ["2027-04-03T23:05:00Z"]}).to_parquet(s / "games_current.parquet")
    if inputs:
        d = tmp / "exp_output/MLB_BOARD/inputs"; d.mkdir(parents=True)
        g = pd.DataFrame({"game_pk": range(n_games), "game_date": ["2027-04-02"] * n_games})
        for f in bd.INPUT_FILES:
            (g if f == "games.parquet" else pd.DataFrame({"x": [1]})).to_parquet(d / f)
        built = (NOW - pd.Timedelta(hours=age_h)).strftime("%Y-%m-%dT%H:%M:%SZ")
        (d / bd.STAMP).write_text(json.dumps({"built_at": built}))
    return tmp


def test_rows_written_pass(tmp_path):
    r = bd.run(_root(tmp_path), NOW, price_fn=lambda g, lu, pa: {"A|B|2027-04-02": {"p": .5}, "C|D|2027-04-02": {"p": .4}})
    assert r["games_scheduled"] == 3 and r["rows_written"] == 2 and not r["silent_exit"]
    assert (tmp_path / "exp_output/MLB_BOARD/board_2027-04-02.json").exists()
    assert json.loads((tmp_path / "logs/mlb_board.log").read_text())["rows_written"] == 2


def test_missing_inputs_is_silent_exit(tmp_path):
    r = bd.run(_root(tmp_path, inputs=False), NOW)
    assert r["status"].startswith("no_inputs") and r["rows_written"] == 0 and r["silent_exit"]


def test_stale_inputs_is_silent_exit(tmp_path):
    r = bd.run(_root(tmp_path, age_h=60), NOW)
    assert r["status"].startswith("stale_inputs") and r["silent_exit"]


def test_pricer_error_and_zero_priced(tmp_path):
    def boom(*a): raise ValueError("x")
    assert bd.run(_root(tmp_path), NOW, price_fn=boom)["status"] == "error:ValueError"
    assert bd.run(tmp_path, NOW, price_fn=lambda *a: {})["status"] == "priced_zero_games"


def test_no_games_day_is_not_silent(tmp_path):
    r = bd.run(_root(tmp_path, n_games=0), NOW)
    assert r["status"] == "no_games_today" and not r["silent_exit"]


def test_unreadable_schedule_reported(tmp_path):
    r = bd.run(tmp_path, NOW)
    assert r["status"].startswith("schedule_unreadable") and r["games_scheduled"] is None


def test_silent_exit_status():
    ok = json.dumps({"ts": "2027-04-02T14:10:00Z", "games_scheduled": 5, "rows_written": 5})
    bad = json.dumps({"ts": "2027-04-02T11:10:00Z", "games_scheduled": 5, "rows_written": 0, "status": "stale_inputs:60h"})
    old = json.dumps({"ts": "2027-03-30T11:10:00Z", "games_scheduled": 5, "rows_written": 0})
    assert bd.silent_exit_status([ok], NOW)[0] == "PASS"
    assert bd.silent_exit_status([ok, bad], NOW)[0] == "FAIL"
    assert bd.silent_exit_status([old], NOW)[0] == "WARN"
    assert bd.silent_exit_status(["garbage"], NOW)[0] == "WARN"


def test_arm_date_alarm():
    op = date(2027, 3, 25)
    assert bi.arm_date_status(date(2027, 3, 17), False, op)[0] == "WARN"
    assert bi.arm_date_status(date(2027, 3, 18), False, op)[0] == "FAIL"
    assert bi.arm_date_status(date(2027, 3, 18), True, op)[0] == "PASS"
    assert bi.arm_date_status(date(2026, 11, 25), False, op)[0] == "PASS"
    assert bi.arm_date_status(date(2027, 11, 25), False, op)[0] == "PASS"


def test_gate_refuses_unknown_growth_and_full_disk():
    u = {"total_bytes": 100e9, "pct": 50.0}
    assert bi.gate(u, 0.1)[0]
    assert not bi.gate(u, None)[0]
    assert not bi.gate({"total_bytes": 100e9, "pct": 79.9}, 0.1)[0]


def test_block_roundtrip():
    cur = "0 * * * * x\n"
    add = [("k", "10 14 * 3-10 * y scripts/mlb_board_daily.py")]
    m = bi.merged_crontab(cur, add)
    assert bi.BEGIN in m and bi.END in m and m.startswith(cur)
    back, changed = bi.without_block(m)
    assert changed and back == cur


def test_conf_key_is_registered_paused_and_own():
    rr = bi.aci._rr()
    reg = rr.load()
    got = bi.wanted_lines(bi.CRON_CONF.read_text(), reg)
    assert [k for k, _ in got] == sorted(bi.OWN_KEYS)
    c = [c for c in reg if c["key"] in bi.OWN_KEYS][0]
    assert c["status"] == "paused"


def test_box_tasks_rows():
    bt = _load("box_tasks_t", "scripts/box_tasks.py")
    assert bt.TASKS["mlb_board_install"].endswith("mlb_board_install.py install")
    assert bt.TASKS["mlb_board_dryrun"].endswith("--dry-run")


def test_board_file_loads_into_the_forecaster_shape(tmp_path):
    """Part C found the file keys ('HOME|AWAY|DATE') did not match the forecaster's tuple keys: no engine price ever reached a row."""
    import json
    from datetime import datetime, timezone
    import mlb_board_daily as bd
    from prediction_market_bot.mlb_engine.forecaster import MLBEngineForecaster
    f = tmp_path / "board.json"
    f.write_text(json.dumps({"LAD|ATL|2026-07-15": {"p_home_ml": 0.6}}))
    fc = MLBEngineForecaster(bd.load_board(f))
    out = fc.forecast("KXMLBGAME-26JUL151910ATLLAD-LAD", datetime(2026, 7, 15, 12, tzinfo=timezone.utc))
    assert out is not None and abs(out.p_yes - 0.6) < 1e-9
