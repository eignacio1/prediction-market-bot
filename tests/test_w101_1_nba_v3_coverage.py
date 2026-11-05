"""W101.1 / B-030: the v3 runner writes coverage.jsonl like v1 / v2, in its own out_dir, and never alters rows."""
import json
from datetime import datetime, timedelta, timezone

import pandas as pd

from prediction_market_bot.nba_engine import live as L, live_v3 as L3

NOW = datetime(2026, 11, 5, 1, 0, tzinfo=timezone.utc)
TICK = {"E_OK": dict(event_ticker="E_OK", game_date="2026-11-04", home="BOS", away="NYK", market_type="NBA_SPREAD", subject="BOS", strike=3.5),
        "E_MISS": dict(event_ticker="E_MISS", game_date="2026-11-04", home="DAL", away="OKC", market_type="NBA_SPREAD", subject="DAL", strike=1.5),
        "E_NOTIP": dict(event_ticker="E_NOTIP", game_date="2026-11-04", home="MIA", away="ORL", market_type="NBA_SPREAD", subject="MIA", strike=1.5),
        "E_LATER": dict(event_ticker="E_LATER", game_date="2026-11-05", home="LAL", away="DEN", market_type="NBA_SPREAD", subject="LAL", strike=1.5)}


def _patch(monkeypatch, tmp_path):
    tips = {("2026-11-04", "BOS", "NYK"): NOW + timedelta(minutes=30),     # inside the window -> logged
            ("2026-11-04", "DAL", "OKC"): NOW - timedelta(minutes=20),     # tip passed unlogged -> miss
            ("2026-11-05", "LAL", "DEN"): NOW + timedelta(hours=9)}        # future -> neither
    monkeypatch.setattr(L3, "load_frozen", lambda p=None: {"sha256": "ab" * 32})
    monkeypatch.setattr(L3, "build_model", lambda art: (None, None))
    monkeypatch.setattr(L, "load_history", lambda raw: pd.DataFrame(columns=["season_type"]))
    monkeypatch.setattr(L3.glob, "glob", lambda pat: ["x"])
    monkeypatch.setattr(L3.pd, "read_parquet", lambda f: pd.DataFrame(dict(home_team_id=[1], away_team_id=[2], home_team_abbreviation=["BOS"], away_team_abbreviation=["NYK"])))
    monkeypatch.setattr(L, "tip_index", lambda s: tips)
    monkeypatch.setattr(L, "read_archive", lambda day, d: [dict(ticker=t) for t in TICK])
    monkeypatch.setattr(L3, "parse_market_ticker", lambda t: TICK[t])
    monkeypatch.setattr(L, "quote_at", lambda rows, at: {r["ticker"]: dict(yes_mid=0.5) for r in rows})
    monkeypatch.setattr(L3, "price_event_rows", lambda q, parsed, *a, **k: [dict(ticker=t, event_ticker=parsed[t]["event_ticker"]) for t in q])
    monkeypatch.setattr(L3, "append_snapshot", lambda *a, **k: False)


def test_v3_run_writes_coverage_for_past_tip_games_and_leaves_rows_alone(monkeypatch, tmp_path):
    _patch(monkeypatch, tmp_path)
    st = L3.run("raw", None, pd.DataFrame(columns=["season_type"]), now=NOW, out_dir=tmp_path, archive_dir=tmp_path, state_path=tmp_path / "s.json")
    cov = [json.loads(l) for l in (tmp_path / "coverage.jsonl").read_text().splitlines()]
    got = {c["event_ticker"]: c["reason"] for c in cov}
    assert got["E_MISS"].startswith("window_closed") and got["E_NOTIP"] == "no_tip_in_schedule"
    assert "E_OK" not in got and "E_LATER" not in got
    assert st["unlogged_past_tip"] == 2
    rows = [json.loads(l)["event_ticker"] for l in (tmp_path / "rows.jsonl").read_text().splitlines()]
    assert set(rows) == {"E_OK"}                                   # rows contain only the logged game; coverage is a separate file
    before = (tmp_path / "coverage.jsonl").read_text()
    L3.run("raw", None, pd.DataFrame(columns=["season_type"]), now=NOW + timedelta(minutes=10), out_dir=tmp_path, archive_dir=tmp_path, state_path=tmp_path / "s.json")
    assert (tmp_path / "coverage.jsonl").read_text() == before     # idempotent: one row per (event, reason)
