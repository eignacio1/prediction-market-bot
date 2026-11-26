import pytest
from prediction_market_bot.decision_trees.filters import nhl_depth as nd

TS = "2026-11-12T23:00:00Z"
SNAP = {"home_goalie": "B", "away_goalie": "C", "home_confirmed": True, "away_confirmed": True, "snapshot_at_utc": "2026-11-12T20:00:00Z"}
PRIOR = {"home": ["A"] * 6 + ["B"] * 2, "away": ["C"] * 5}


def test_flag_default_off(monkeypatch):
    monkeypatch.delenv("PM_NHL_DEPTH", raising=False)
    assert not nd.nhl_depth_on()
    monkeypatch.setenv("PM_NHL_DEPTH", "on")
    assert nd.nhl_depth_on()


def test_planted_backup_start_moves_leaf():
    base = dict(SNAP, home_goalie="A")
    assert nd.split_leaves(TS, base, PRIOR, None, None)["goalie@game"] == "both_expected"
    planted = dict(SNAP, home_goalie="B")  # A is expected; B starts
    assert nd.split_leaves(TS, planted, PRIOR, None, None)["goalie@game"] == "any_backup"


def test_unconfirmed_and_missing_use_prior_only():
    unconf = dict(SNAP, home_goalie="A", home_confirmed=False)
    assert nd.split_leaves(TS, unconf, PRIOR, None, None)["goalie@game"] == "prior_only"
    assert nd.split_leaves(TS, None, PRIOR, None, None)["goalie@game"] == "prior_only"  # no Muse file: the store prior alone, not unknown
    assert nd.split_leaves(TS, dict(SNAP, home_goalie="A"), {"home": [], "away": ["C"]}, None, None)["goalie@game"] == "unknown"  # no history: no imputation


def test_norm_name_folds_accents_and_case():
    assert nd.norm_name("Jüse Saros") == nd.norm_name("juse  SAROS")


def test_snapshot_after_row_raises():
    with pytest.raises(nd.PITViolation):
        nd.split_leaves(TS, dict(SNAP, snapshot_at_utc="2026-11-13T00:00:00Z"), PRIOR, None, None)


def test_referee_leaves_and_unknown():
    cuts = (-0.2, 0.2)
    assert nd.ref_leaf(nd.crew_prior([1.0] * 20), cuts) == "ref_high"
    assert nd.ref_leaf(nd.crew_prior([-2.0] * 20), cuts) == "ref_low"
    assert nd.ref_leaf(nd.crew_prior([0.0] * 5), cuts) == "ref_mid"
    assert nd.ref_leaf(nd.crew_prior([]), cuts) == "unknown"
    assert nd.ref_leaf(0.5, None) == "unknown"


def test_availability_always_abstains():
    assert nd.split_leaves(TS, SNAP, PRIOR, 0.1, (-0.2, 0.2))["availability@game"] == "unknown"


def _w(tmp_path, day, rows):
    import json
    (tmp_path / f"goalies-{day}.jsonl").write_text("\n".join(json.dumps(r) for r in rows))


def _g(gid, h, a, hc=True, ac=True, at="2026-11-12T20:00:00Z"):
    return {"game_id": gid, "home_goalie": h, "away_goalie": a, "home_confirmed": hc, "away_confirmed": ac, "snapshot_at_utc": at}


def test_loader_planted_backup_moves_leaf_and_no_data_abstains(tmp_path):
    for d in range(1, 6):  # five prior days of confirmed starts: TOR=A, COL=C
        _w(tmp_path, f"2026-11-0{d}", [_g(f"TOR-COL-2026-11-0{d}", "A", "C", at=f"2026-11-0{d}T20:00:00Z")])
    row = {"event_ticker": "KXNHLGAME-26NOV12COLTOR", "ts_utc": TS}
    _w(tmp_path, "2026-11-12", [_g("TOR-COL-2026-11-12", "A", "C")])
    assert nd.leaves_for_row(row, str(tmp_path))["goalie@game"] == "both_expected"
    _w(tmp_path, "2026-11-12", [_g("TOR-COL-2026-11-12", "B", "C")])  # planted backup
    assert nd.leaves_for_row(row, str(tmp_path))["goalie@game"] == "any_backup"
    assert nd.leaves_for_row(dict(row, event_ticker="KXNHLGAME-26NOV12XXXYYY"), str(tmp_path)) is None
    assert nd.leaves_for_row(row, str(tmp_path / "missing")) is None


def test_snapshot_after_row_is_not_read(tmp_path):
    _w(tmp_path, "2026-11-12", [_g("TOR-COL-2026-11-12", "B", "C", at="2026-11-13T00:00:00Z")])
    assert nd.leaves_for_row({"event_ticker": "KXNHLGAME-26NOV12COLTOR", "ts_utc": TS}, str(tmp_path)) is None


def test_marker_rows_without_game_id_are_skipped(tmp_path):
    import json
    (tmp_path / "goalies-2026-11-12.jsonl").write_text(json.dumps({"status": "NO_GAMES", "snapshot_at_utc": "2026-11-12T15:00:00Z"}) + "\n")
    assert nd.leaves_for_row({"event_ticker": "KXNHLGAME-26NOV12COLTOR", "ts_utc": TS}, str(tmp_path)) is None


def _store(starts, games):
    return nd.StarterStore([{"date": d, "home": h, "away": a} for d, h, a in games], [dict(s, season=2026, game_id=i) for i, s in enumerate(starts)])


def _prior_store():
    st = [{"date": f"2026-11-0{d}", "team": "TOR", "goalie": "a"} for d in range(1, 6)]
    st += [{"date": f"2026-11-0{d}", "team": "COL", "goalie": "c"} for d in range(1, 6)]
    return _store(st, [("2026-11-12", "TOR", "COL")])


def test_store_prior_alone_when_no_muse_file():
    row = {"event_ticker": "KXNHLGAME-26NOV12COLTOR", "ts_utc": TS}
    leaves, exp = nd.depth_for_row(row, None, _prior_store())
    assert leaves["goalie@game"] == "prior_only" and exp["source"] == "store"
    assert exp["home"]["goalie"] == "a" and exp["home"]["n_prior"] == 5


def test_store_prior_plus_planted_backup_start(tmp_path):
    _w(tmp_path, "2026-11-12", [_g("TOR-COL-2026-11-12", "a", "c")])
    row = {"event_ticker": "KXNHLGAME-26NOV12COLTOR", "ts_utc": TS}
    assert nd.leaves_for_row(row, str(tmp_path), _prior_store())["goalie@game"] == "both_expected"
    _w(tmp_path, "2026-11-12", [_g("TOR-COL-2026-11-12", "b", "c")])
    assert nd.leaves_for_row(row, str(tmp_path), _prior_store())["goalie@game"] == "any_backup"


def test_kalshi_two_letter_alias_resolves():
    st = _store([{"date": "2026-11-01", "team": "LAK", "goalie": "x"}, {"date": "2026-11-01", "team": "NJD", "goalie": "y"}],
                [("2026-11-12", "LAK", "NJD")])
    row = {"event_ticker": "KXNHLGAME-26NOV12NJLA", "ts_utc": TS}
    assert nd.leaves_for_row(row, None, st)["goalie@game"] == "prior_only"


def test_store_prior_excludes_game_day_and_later():
    st = _store([{"date": "2026-11-12", "team": "TOR", "goalie": "a"}, {"date": "2026-11-13", "team": "COL", "goalie": "c"}],
                [("2026-11-12", "TOR", "COL")])
    assert nd.leaves_for_row({"event_ticker": "KXNHLGAME-26NOV12COLTOR", "ts_utc": TS}, None, st)["goalie@game"] == "unknown"


def test_muse_confirmed_fills_days_after_store(tmp_path):
    _w(tmp_path, "2026-11-10", [_g("TOR-COL-2026-11-10", "b", "c", at="2026-11-10T20:00:00Z")])
    st = _store([{"date": "2026-11-01", "team": "TOR", "goalie": "a"}, {"date": "2026-11-01", "team": "COL", "goalie": "c"}],
                [("2026-11-12", "TOR", "COL")])
    _, exp = nd.depth_for_row({"event_ticker": "KXNHLGAME-26NOV12COLTOR", "ts_utc": TS}, str(tmp_path), st)
    assert exp["source"] == "store+muse" and exp["home"]["n_prior"] == 2
