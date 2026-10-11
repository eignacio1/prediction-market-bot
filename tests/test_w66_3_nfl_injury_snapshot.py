import importlib.util
import json
from datetime import datetime, timezone
from pathlib import Path

spec = importlib.util.spec_from_file_location(
    "nfl_injury_snapshot", Path(__file__).resolve().parents[1] / "scripts" / "nfl_injury_snapshot.py")
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

NOW = datetime(2026, 10, 11, 12, 0, tzinfo=timezone.utc)


def ev(eid, date, state, home, away):
    return {"id": eid, "date": date, "status": {"type": {"state": state}},
            "competitions": [{"competitors": [{"homeAway": "home", "team": {"abbreviation": home}},
                                              {"homeAway": "away", "team": {"abbreviation": away}}]}]}


def player(team, name, pos, status, pid="1"):
    return {"id": "x" + pid, "status": status, "date": "2026-10-10T20:00Z", "source": {"description": "basic/manual"},
            "details": {"type": "Ankle", "returnDate": "2026-10-18"} if status != "Active" else None,
            "athlete": {"id": pid, "displayName": name, "position": {"abbreviation": pos},
                        "team": {"abbreviation": team}}}


SB = {"week": {"number": 5}, "events": [
    ev("1", "2026-10-11T13:30Z", "pre", "JAX", "PHI"),
    ev("2", "2026-10-11T11:00Z", "in", "GB", "CHI"),      # already started
    ev("3", "2026-10-11T11:30Z", "pre", "NE", "LV")]}      # stale 'pre' but kickoff passed
INJ = {"timestamp": "t", "injuries": [
    {"injuries": [player("JAX", "A QB", "QB", "Active", "10"), player("JAX", "A WR", "WR", "Out", "11"),
                  player("JAX", "A RB", "RB", "Active", "12"), player("GB", "G", "WR", "Out", "13")]},
    {"injuries": [player("PHI", "P QB", "QB", "Questionable", "20")]}]}


def test_only_pre_kickoff_games_and_qb_rows(tmp_path):
    games = m.upcoming_games(SB, NOW)
    assert [g["event_id"] for g in games] == ["1"] and games[0]["minutes_to_kickoff"] == 90
    rows = m.build_rows(INJ, games)
    assert {r["name"] for r in rows} == {"A QB", "A WR", "P QB"}   # active RB dropped, GB excluded
    assert all(r["event_id"] == "1" for r in rows)


def test_append_only_and_dedupe(tmp_path):
    a = m.run(tmp_path, NOW, SB, INJ)
    assert a["status"] == "written" and a["qb_rows"] == 2
    b = m.run(tmp_path, NOW, SB, INJ)
    assert b["status"] == "unchanged"
    assert len((tmp_path / "snapshots.jsonl").read_text().splitlines()) == 1
    assert len((tmp_path / "checks.jsonl").read_text().splitlines()) == 2
    INJ2 = json.loads(json.dumps(INJ))
    INJ2["injuries"][0]["injuries"][0]["status"] = "Out"
    c = m.run(tmp_path, NOW, SB, INJ2)
    assert c["status"] == "written"
    assert len((tmp_path / "snapshots.jsonl").read_text().splitlines()) == 2


def test_no_games_writes_no_snapshot(tmp_path):
    out = m.run(tmp_path, datetime(2026, 10, 13, 6, 0, tzinfo=timezone.utc), {"events": []}, INJ)
    assert out["status"] == "no_upcoming_games" and not (tmp_path / "snapshots.jsonl").exists()
