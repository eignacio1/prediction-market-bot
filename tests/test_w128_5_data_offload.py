"""W128.5 known-answer tests for scripts/data_offload.py: parsers on saved samples, refusal handling, idempotence, window, caps."""
from __future__ import annotations

import gzip
import importlib.util
import io
import json
import sys
import urllib.error
from datetime import date, datetime, timezone
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def _load():
    spec = importlib.util.spec_from_file_location("data_offload", ROOT / "scripts" / "data_offload.py")
    m = importlib.util.module_from_spec(spec)
    sys.modules["data_offload"] = m
    spec.loader.exec_module(m)
    return m


do = _load()

GOALIE_SAMPLE = {"data": [{"gameId": 2025020100, "gameDate": "2025-11-20", "playerId": 8478402, "goalieFullName": "Connor Hellebuyck",
                           "teamAbbrev": "WPG", "opponentTeamAbbrev": "MIN", "homeRoad": "H", "gamesStarted": 1, "decision": "W",
                           "saves": 27, "shotsAgainst": 29, "goalsAgainst": 2, "savePct": 0.931, "timeOnIce": 3600, "shutouts": 0,
                           "wins": 1, "losses": 0, "otLosses": 0, "extra": "dropped"}], "total": 1}

RAIL_SAMPLE = {"gameInfo": {"referees": [{"default": "x", "fullName": {"default": "Chris Lee"}}, {"fullName": {"default": "Wes McCauley"}}],
                            "linesmen": [{"fullName": {"default": "Steve Barton"}}]}}

BOX_SAMPLE = {"teams": {"away": {"team": {"id": 147}, "battingOrder": [1, 2, 3]}, "home": {"team": {"id": 111}, "battingOrder": [4, 5]}},
              "officials": [{"official": {"id": 9, "fullName": "Angel Hernandez"}, "officialType": "Home Plate"}]}


class FakeResp(io.BytesIO):
    status = 200

    def __enter__(self):
        return self

    def __exit__(self, *a):
        self.close()


def opener_for(mapping):
    def op(req, timeout=0):
        url = req.full_url
        for pat, val in mapping.items():
            if pat in url:
                if isinstance(val, int):
                    raise urllib.error.HTTPError(url, val, "x", {}, None)
                return FakeResp(val)
        raise urllib.error.HTTPError(url, 404, "nf", {}, None)
    return op


def make_http(mapping):
    return do.Http(pause={}, sleep=lambda s: None, opener=opener_for(mapping))


def test_goalie_rows_known_answer():
    rows = do.goalie_rows(GOALIE_SAMPLE, "2025-11-21T09:00:00Z")
    assert rows == [{"gameId": 2025020100, "gameDate": "2025-11-20", "playerId": 8478402, "goalieFullName": "Connor Hellebuyck",
                     "teamAbbrev": "WPG", "opponentTeamAbbrev": "MIN", "homeRoad": "H", "gamesStarted": 1, "decision": "W", "saves": 27,
                     "shotsAgainst": 29, "goalsAgainst": 2, "savePct": 0.931, "timeOnIce": 3600, "shutouts": 0, "wins": 1, "losses": 0,
                     "otLosses": 0, "fetched_at_utc": "2025-11-21T09:00:00Z"}]


def test_officials_row_known_answer():
    row = do.officials_row({"id": 2025020100, "gameDate": "2025-11-20", "season": 20252026, "gameType": 2}, RAIL_SAMPLE, "T")
    assert row["referees"] == ["Chris Lee", "Wes McCauley"] and row["linesmen"] == ["Steve Barton"] and row["has_officials"] is True
    empty = do.officials_row({"id": 1, "gameDate": "d"}, None, "T")
    assert empty["has_officials"] is False and empty["referees"] == []


def test_boxscore_row_known_answer():
    row = do.boxscore_row({"gamePk": 777, "officialDate": "2025-06-01", "gameType": "R"}, BOX_SAMPLE, "T")
    assert row["away"] == {"team_id": 147, "batting_order": [1, 2, 3]} and row["home"]["team_id"] == 111
    assert row["umpires"] == [{"id": 9, "name": "Angel Hernandez", "type": "Home Plate"}]


def test_moneypuck_urls_season_logic():
    in_season = list(do.mp_items(date(2025, 11, 24)))                    # Monday, NHL in season
    keys = [i["key"] for i in in_season]
    assert "moneypuck|summary|2025|lines@2025-11-24" in keys             # current season is a dated snapshot
    assert "moneypuck|summary|2024|lines" in keys                        # past seasons are once-only
    assert any(i["url"] == "https://moneypuck.com/moneypuck/playerData/seasonSummary/2025/regular/goalies.csv" for i in in_season)
    tue = [i["key"] for i in do.mp_items(date(2025, 11, 25))]
    assert not any(k.startswith("moneypuck|teamgame|2025|") for k in tue)  # in-season team files refresh Mondays only
    assert any(k.startswith("moneypuck|teamgame|2025|") for k in keys)
    assert len(set(keys)) == len(keys)


def test_savant_items_and_csv_validated_set():
    items = list(do.sv_items(date(2026, 7, 1)))
    assert items[0]["key"].endswith("@2026-07-01")                       # in season: today's snapshot first
    assert all("csv=true" in i["url"] for i in items)
    off = list(do.sv_items(date(2026, 12, 1)))
    assert not any("@" in i["key"] for i in off) and any(i["key"] == "savant|expected_batter|2026" for i in off)


def test_stream_gz_roundtrip_and_sha(tmp_path):
    body = b"a,b\n1,2\n" * 500
    http = make_http({"/x.csv": body})
    raw_n, gz_n, sha = http.stream_gz("https://moneypuck.com/x.csv", tmp_path / "o" / "x.csv.gz")
    assert raw_n == len(body) and gz_n < raw_n
    assert gzip.open(tmp_path / "o" / "x.csv.gz").read() == body
    assert not list((tmp_path / "o").glob("*.part"))


def test_html_challenge_is_a_refusal_not_data(tmp_path):
    http = make_http({"/x.csv": b"<!DOCTYPE html><html>Just a moment...</html>"})
    with pytest.raises(do.Refused):
        http.stream_gz("https://moneypuck.com/x.csv", tmp_path / "x.csv.gz")
    assert not (tmp_path / "x.csv.gz").exists() and not list(tmp_path.glob("*.part"))


@pytest.mark.parametrize("code", [401, 403, 429])
def test_refusal_codes_stop_without_retry(code):
    http = make_http({"/a": code})
    with pytest.raises(do.Refused):
        http.json("https://api.nhle.com/a")
    assert http.requests == 1                                            # never retried around


def test_retries_are_capped_on_5xx():
    http = make_http({"/a": 503})
    with pytest.raises(RuntimeError):
        http.json("https://api.nhle.com/a")
    assert http.requests == do.RETRIES


def test_family_stops_for_the_night_on_refusal(tmp_path):
    http = make_http({"seasonSummary": 403})
    res = do.run_family("moneypuck", tmp_path, http, date(2025, 11, 24), (50, 10**6), 5)
    assert res["error"].startswith("REFUSED") and res["requests"] == 1 and res["items"] == 0


def test_csv_family_idempotent_and_unchanged_snapshot(tmp_path):
    csvb = b"x,y\n1,2\n"
    http = make_http({"playerData": csvb})
    caps = (6, 10**6)
    r1 = do.run_family("moneypuck", tmp_path, http, date(2025, 11, 24), caps, 5)
    assert r1["items"] == 6 and r1["stop"] == "request cap"
    r2 = do.run_family("moneypuck", tmp_path, make_http({"playerData": csvb}), date(2025, 11, 24), caps, 5)
    assert r2["items"] == 6 and r2["requests"] == 6                      # resumes at the NEXT six; the first six are not refetched
    done = do.Manifest(tmp_path / "moneypuck").done
    assert len(done) == 12
    # next day, identical current-season content: recorded in the manifest, not stored a second time
    r3 = do.run_family("moneypuck", tmp_path, make_http({"playerData": csvb}), date(2025, 11, 25), (4, 10**6), 5)
    assert r3["unchanged"] == 4 and r3["bytes"] == 0
    assert not list((tmp_path / "moneypuck" / "seasonSummary" / "2025").glob("*2025-11-25*"))


def test_byte_cap_stops_run(tmp_path):
    big = (b"%d,%d\n" * 1)  # compressible; cap at 1 byte forces stop after the first item
    http = make_http({"playerData": b"a,b\n" * 100})
    res = do.run_family("moneypuck", tmp_path, http, date(2025, 11, 24), (100, 1), 5)
    assert res["stop"] == "byte cap" and res["items"] == 1


def test_officials_run_writes_rows_with_fetch_time_and_resumes(tmp_path):
    games = {"data": [{"id": 2025020100, "gameDate": "2025-11-20", "season": 20252026, "gameType": 2},
                      {"id": 2025020101, "gameDate": "2025-11-21", "season": 20252026, "gameType": 2}]}
    http = make_http({"stats/rest/en/game": json.dumps(games).encode(), "right-rail": json.dumps(RAIL_SAMPLE).encode()})
    res = do.run_family("nhl_officials", tmp_path, http, date(2025, 11, 24), (4, 10**6), 5)   # 1 list + 3 rails max, 2 seasons walked
    rows = [json.loads(line) for line in gzip.open(tmp_path / "nhl_officials" / "season_2025.jsonl.gz", "rt")]
    assert [r["game_id"] for r in rows] == [2025020100, 2025020101]
    assert all(r["fetched_at_utc"].endswith("Z") and r["referees"] == ["Chris Lee", "Wes McCauley"] for r in rows)
    again = do.run_family("nhl_officials", tmp_path, make_http({"stats/rest/en/game": json.dumps(games).encode(),
                                                                 "right-rail": json.dumps(RAIL_SAMPLE).encode()}), date(2025, 11, 24), (4, 10**6), 5)
    assert len([1 for _ in gzip.open(tmp_path / "nhl_officials" / "season_2025.jsonl.gz", "rt")]) == 2   # no duplicates
    assert res["items"] == 2 and again["items"] == 0


def test_window_and_caps():
    assert do.in_window(datetime(2025, 11, 24, 9, 0, tzinfo=timezone.utc))
    assert do.in_window(datetime(2025, 11, 24, 14, 59, tzinfo=timezone.utc))
    assert not do.in_window(datetime(2025, 11, 24, 15, 0, tzinfo=timezone.utc))
    assert not do.in_window(datetime(2025, 11, 24, 2, 0, tzinfo=timezone.utc))      # pre-game / live-game hours
    assert do.NIGHT_CAP_BYTES <= 15_000_000                                         # per-night compressed ceiling
    assert set(do.FAMILY_CAPS) == set(do.FAMILIES)


def test_run_outside_window_does_nothing(capsys):
    if do.in_window(do.now_utc()):
        pytest.skip("inside the window right now")
    assert do.main(["run", "--out", "/nonexistent-should-not-be-touched"]) == 0
    assert "outside" in capsys.readouterr().out


# ---------------------------------------------------------------- install script / box wiring
def _load_install():
    sys.path.insert(0, str(ROOT / "scripts"))
    sys.path.insert(0, str(ROOT / "src"))
    spec = importlib.util.spec_from_file_location("data_offload_install", ROOT / "scripts" / "data_offload_install.py")
    m = importlib.util.module_from_spec(spec)
    sys.modules["data_offload_install"] = m
    spec.loader.exec_module(m)
    return m


def test_gate_pass_and_refuse():
    di = _load_install()
    ok = di.gate_report({"total_bytes": 100e9, "pct": 40.0}, 0.1)
    assert ok["verdict"] == "PASS" and ok["approval_line"] == "approve data_offload_install"
    assert ok["numbers"]["new_mb_per_day"] == round(do.NIGHT_CAP_BYTES / 1e6, 1)
    full = di.gate_report({"total_bytes": 100e9, "pct": 79.9}, 0.1)
    assert full["verdict"] == "REFUSE" and full["approval_line"].startswith("do not approve")
    assert di.gate_report({"total_bytes": 100e9, "pct": 40.0}, None)["verdict"] == "REFUSE"      # unknown growth is a refusal


def test_cron_line_is_wanted_only_while_registered():
    di = _load_install()
    import runtime_registry as rr
    add = di.wanted_lines(di.CRON_CONF.read_text(), rr.load())
    assert len(add) == 1 and add[0][0] in di.OWN_KEYS
    line = add[0][1]
    assert "MemoryMax=150M" in line and "flock -n 9" in line and "nice -n 10" in line and line.startswith("17 9 ")   # inside 09-15 UTC
    assert di.wanted_lines(di.CRON_CONF.read_text(), []) == []                                                       # not registered -> nothing


def test_install_block_roundtrip():
    di = _load_install()
    cur = "MAILTO=x\n0 1 * * * echo hi\n"
    merged = di.merged_crontab(cur, [("k", "17 9 * * * job")])
    back, changed = di.without_block(merged)
    assert changed and back == cur


def test_box_tasks_allowlisted_and_probe_writes_no_file():
    sys.path.insert(0, str(ROOT / "scripts"))
    import box_tasks as bt
    for t in ("data_offload_gate_read", "data_offload_probe", "data_offload_install", "data_offload_readback", "data_offload_uninstall"):
        assert t in bt.TASKS
    assert ">" not in bt.TASKS["data_offload_probe"].replace("2>", "")
