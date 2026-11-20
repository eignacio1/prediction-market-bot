"""W122.4 / GG-1957: the opening-day preflight fails loud on a stale cache or silent cells, and fail-closed exits are recorded."""
import importlib.util
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]


def _load(name):
    sp = importlib.util.spec_from_file_location(name, ROOT / "scripts" / f"{name}.py")
    m = importlib.util.module_from_spec(sp)
    sp.loader.exec_module(m)
    return m


NOW = datetime(2027, 4, 1, 12, tzinfo=timezone.utc)


def _setup(tmp, age_h, with_rows):
    cache = tmp / "exp_output" / "MLB_GAME" / "cache_w47"
    cache.mkdir(parents=True)
    (cache / "games_current.meta.json").write_text(json.dumps({"refreshed_at": (NOW - timedelta(hours=age_h)).isoformat()}))
    pd.DataFrame({"game_date": ["2027-04-01"]}).to_parquet(cache / "games_current.parquet")
    (tmp / "models").mkdir()
    (tmp / "models" / "mlb_game_pregame_v1.json").write_text("{}")
    led = tmp / "exp_output" / "PREGAME_SHADOW"
    led.mkdir(parents=True)
    if with_rows:
        for c in ("MLB_MONEYLINE", "MLB_RUN_LINE", "MLB_GAME_TOTAL", "MLB_TEAM_TOTAL"):
            (led / f"MLB_{c}_T1.jsonl").write_text(json.dumps({"ts_utc": (NOW - timedelta(hours=2)).isoformat()}) + "\n")


def test_ready_passes(tmp_path):
    _setup(tmp_path, 3, True)
    r = _load("mlb_opening_day_preflight").preflight(tmp_path, NOW)
    assert r["ok"], r


def test_stale_cache_and_silent_cells_fail(tmp_path):
    _setup(tmp_path, 60, False)
    r = _load("mlb_opening_day_preflight").preflight(tmp_path, NOW)
    assert not r["ok"]
    assert not r["checks"]["games_cache_fresh"]["ok"] and not r["checks"]["cells_logged_24h"]["ok"]


def test_failclosed_exit_leaves_a_record(tmp_path):
    m = _load("run_mlb_pregame_shadow")
    m.record_failclosed(tmp_path, NOW, "games cache refreshed ... old")
    line = json.loads((tmp_path / "_MLB_FAILCLOSED.jsonl").read_text().splitlines()[0])
    assert line["reason"].startswith("games cache") and line["ts"].startswith("2027-04-01")
