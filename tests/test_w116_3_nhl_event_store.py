"""W116.3: the NHL event store refresh installer is gated, reversible, accepts only its own paused key, and installs nothing here."""
import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
spec = importlib.util.spec_from_file_location("nhl_store_inst", ROOT / "scripts" / "nhl_event_store_install.py")
I = importlib.util.module_from_spec(spec)
spec.loader.exec_module(I)

CONF = (ROOT / "deploy" / "cron.nhl_event_store").read_text()


def _reg(status, key=None):
    return [{"key": key or I.OWN_KEY, "kind": "cron", "status": status}]


def test_paused_own_key_is_wanted_and_other_paused_key_is_not():
    assert len(I.wanted_lines(CONF, _reg("paused"))) == 1
    assert len(I.wanted_lines(CONF, _reg("live"))) == 1
    assert I.wanted_lines(CONF, _reg("paused", key="cron|1 * * * *|scripts/other.py")) == []


def test_line_is_evaluate_only_flocked_and_marked():
    (k, line), = I.wanted_lines(CONF, _reg("paused"))
    assert k == I.OWN_KEY and "flock -n 9" in line and "run_nhl_event_store_refresh.py" in line
    assert "ORDERS" not in line.upper() and "kelly" not in line.lower()


def test_merge_then_remove_preserves_every_other_line():
    cur = "0 1 * * * echo a\n5 2 * * * echo b\n"
    add = I.wanted_lines(CONF, _reg("paused"))
    merged = I.merged_crontab(cur, add)
    assert all(l in merged.splitlines() for l in cur.splitlines()) and I.BEGIN in merged
    back, changed = I.without_block(merged)
    assert changed and back == cur


def test_install_refused_when_budget_red_and_writes_nothing():
    wrote = []
    rc = I.install(live_fn=lambda: {"error": "boom"}, read=lambda: "", write=wrote.append, backup=lambda c: "b", conf_text=CONF, reg=_reg("paused"))
    assert rc == 0 and wrote == []


def test_registry_entry_is_paused_or_live_and_task_is_allowlisted():
    import box_tasks as bt
    assert all(t in bt.TASKS for t in ("nhl_event_store_install", "nhl_event_store_readback", "nhl_event_store_uninstall"))
    import runtime_registry as rr
    e = [c for c in rr.load() if c["key"] == I.OWN_KEY]
    assert len(e) == 1 and e[0]["status"] == "paused" and e[0]["reviewed"] is True  # paused until the operator approves nhl_event_store_install


# ---- W116.3 (GG-1953): streamed two-season compile, the seasons the box keeps, the refresh runner
import datetime as dt
import json

import pandas as pd

from prediction_market_bot.c1_signal_ingestion import nhl_event_store as es

PBP_FULL = {
    "homeTeam": {"id": 10}, "awayTeam": {"id": 20},
    "plays": [{"eventId": 1, "periodDescriptor": {"number": 1, "periodType": "REG"}, "timeInPeriod": "01:30",
               "situationCode": "1551", "typeCode": 506, "typeDescKey": "shot-on-goal", "sortOrder": 10,
               "details": {"xCoord": 60, "yCoord": -5, "shootingPlayerId": 7, "eventOwnerTeamId": 10}}],
    "rosterSpots": [{"teamId": 10, "playerId": 7, "firstName": {"default": "A"}, "lastName": {"default": "B"},
                     "sweaterNumber": 9, "positionCode": "C"}],
}
PBP_NULL_XY = {  # a game whose events carry no coordinates: x / y are all-null in its chunk
    "homeTeam": {"id": 10}, "awayTeam": {"id": 20},
    "plays": [{"eventId": 2, "periodDescriptor": {"number": 1, "periodType": "REG"}, "timeInPeriod": "02:00",
               "situationCode": "1551", "typeCode": 505, "typeDescKey": "goal", "sortOrder": 20,
               "details": {"scoringPlayerId": 8, "eventOwnerTeamId": 20}}],
    "rosterSpots": [],
}
SHIFTS = {"data": [{"playerId": 7, "typeCode": 517, "period": 1, "shiftNumber": 1, "startTime": "00:10", "endTime": "00:50",
                    "duration": "00:40", "teamId": 10}]}


def _cache(tmp_path):
    games = []
    for season, gid, pbp in ((2024, 1, PBP_FULL), (2025, 2, PBP_FULL), (2025, 3, PBP_FULL), (2025, 4, PBP_NULL_XY), (2025, 5, PBP_FULL)):
        games.append({"game_id": gid, "season": season, "game_type": 2, "start_time_utc": f"2025-11-0{gid}T00:00:00Z"})
        es.write_cache(es.cache_path(tmp_path, "pbp", season, gid), "u", pbp)
        es.write_cache(es.cache_path(tmp_path, "shifts", season, gid), "u", SHIFTS)
    (tmp_path / "schedule_games.json").write_text(json.dumps(games))
    return games


def test_streamed_compile_equals_one_whole_season_frame_and_keeps_only_asked_seasons(tmp_path, monkeypatch):
    games = _cache(tmp_path)
    monkeypatch.setattr(es, "COMPILE_CHUNK_GAMES", 2)          # 4 games in 2025 -> two chunks; the second has all-null x / y
    counts = es.compile_store(tmp_path, [2025])
    assert counts["events"] == {2025: 4} and not (tmp_path / "events_2024.parquet").exists()
    ev = [e for g in games if g["season"] == 2025
          for e in es.parse_events(g["game_id"], 2025, PBP_NULL_XY if g["game_id"] == 4 else PBP_FULL)]
    want = pd.read_parquet(_roundtrip(tmp_path, ev))
    got = pd.read_parquet(tmp_path / "events_2025.parquet")
    pd.testing.assert_frame_equal(got.reset_index(drop=True), want.reset_index(drop=True), check_dtype=False)
    assert got["x"].isna().sum() == 1 and len(pd.read_parquet(tmp_path / "games_2025.parquet")) == 4
    assert not list(tmp_path.glob("*.tmp")) and not list(tmp_path.glob(".compile_parts_*"))   # renamed into place, parts removed
    assert {r["season"] for r in json.loads((tmp_path / "recon.json").read_text())} == {2025}


def _roundtrip(tmp_path, rows):
    p = tmp_path / "ref.parquet"
    pd.DataFrame(rows).to_parquet(p, index=False)
    return p


def test_store_seasons_are_the_current_and_previous_and_roll_in_september():
    assert es.store_seasons(dt.date(2026, 11, 17)) == [2025, 2026]
    assert es.store_seasons(dt.date(2027, 8, 31)) == [2025, 2026]
    assert es.store_seasons(dt.date(2027, 9, 1)) == [2026, 2027]


def test_refresh_fetches_then_compiles_exactly_the_kept_seasons(tmp_path, capsys):
    import run_nhl_event_store_refresh as rf
    calls = []
    rc = rf.main(tmp_path, fetch=lambda r, s, rps, th, lim: calls.append(("fetch", s, rps)) or {"fetched": 0},
                 compile_=lambda r, s: calls.append(("compile", s)) or {"events": {}})
    assert rc == 0 and calls == [("fetch", es.store_seasons(), rf.RPS), ("compile", es.store_seasons())] and rf.RPS <= 2.0
    assert json.loads(capsys.readouterr().out)["runner"] == "nhl_event_store_refresh"


def test_filter_state_reads_only_the_kept_seasons_files():
    import inspect
    from prediction_market_bot.decision_trees import filter_supply as fs
    src = inspect.getsource(fs._nhl_state)
    assert "store_seasons()" in src and "202[56]" not in src and "columns=cols" in src
