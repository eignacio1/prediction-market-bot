"""W112.1: filters reach the router as tree splits, point in time; only tested (kept) splits change the logged arm."""
import json
from datetime import datetime, timezone
from types import SimpleNamespace

import pytest

from prediction_market_bot.decision_trees import coverage as cov
from prediction_market_bot.decision_trees import filter_supply as fsup
from prediction_market_bot.decision_trees import leaf_map as lm
from prediction_market_bot.decision_trees.router import Evidence, Situation, route
from prediction_market_bot.decision_trees.shadow_route import router_fields
from prediction_market_bot.pregame_shadow.runner import run_once

EV = "KXNBAGAME-26NOV12BOSCLE"  # away BOS, home CLE
ROW = {"sport": "NBA", "event_ticker": EV, "ts_utc": "2026-11-12T20:00:00+00:00"}
TABLE = {"data_through_utc": "2026-06-30T00:00:00+00:00", "teams": {
    "CLE": {"clutch_offence_ppp": 0.9, "clutch_defence_ppp": 0.2}, "BOS": {"clutch_offence_ppp": 0.7, "clutch_defence_ppp": 0.8}}}


def test_nba_adapter_known_answer():
    f, note = fsup.nba_adapter(ROW, TABLE)
    assert note is None
    assert f["clutch_offence_ppp@total"] == "high"          # mean(0.9, 0.7) = 0.8 > 2/3
    assert f["clutch_offence_ppp@side"] == "neutral"        # home-away goodness 0.2 < 1/3
    assert f["clutch_defence_ppp@side"] == "home_edge"      # lower is better: goodness 0.8 vs 0.2 -> +0.6
    assert f["pace_seconds_per_possession@total"] == "unknown"  # not in this table: unknown, never invented


def test_later_data_fails_point_in_time():
    late = {**TABLE, "data_through_utc": "2026-11-13T00:00:00+00:00"}  # built from a game after the row
    f, note = fsup.FilterSupply(nba_table_=late).for_row(ROW)
    assert f is None and note.startswith("pit_violation")
    with pytest.raises(fsup.PITViolation):
        fsup.assert_pit("2026-11-12T20:00:01Z", "2026-11-12T20:00:00Z")
    fsup.assert_pit("2026-11-12T20:00:00Z", "2026-11-12T20:00:00+00:00")  # equal is allowed (Z parses on 3.9)


def test_shipped_nba_table_is_prior_season():
    t = fsup.nba_table()
    assert fsup.parse_ts(t["data_through_utc"]) < datetime(2026, 10, 1, tzinfo=timezone.utc) and len(t["teams"]) == 30


def test_nfl_forecast_issued_after_row_is_refused():
    prov = SimpleNamespace(weather=lambda r: (None, "2026-11-13T00:00:00Z"), terms=lambda r: (None, None, "2026-11-01T00:00:00Z"),
                           lines=lambda r: (3.0, 44.0))
    f, note = fsup.FilterSupply(nfl_providers=prov).for_row({**ROW, "sport": "NFL"})
    assert f is None and note.startswith("pit_violation")


def test_nhl_and_other_sports_log_a_reason_not_a_guess():
    assert fsup.FilterSupply().for_row({**ROW, "sport": "NHL"})[1].startswith("filters_unavailable")
    assert fsup.FilterSupply().for_row({**ROW, "sport": "MLB"})[1] == "no_filter_adapter:mlb"
    assert fsup.FilterSupply().for_row({})[1].startswith("no_filter_adapter")


def _splits(*rows):
    return lm.FilterSplits({"splits": [dict(sport="NBA", series="KXNBATOTAL", why="kept" if k else "tested", kept=k, arm=a,
                                            filter=f, leaf=l) for f, l, a, k in rows]})


def _setup(arm="RIDE"):
    r = lm.LeafMap.row_for("NBA", "NBA_GAME_TOTAL", "T3", 0.70, 0.70)
    m = lm.LeafMap({"leaves": {}})
    m.leaves[m.leaf_id(r)] = {"arm": arm, "thin": False, "fit": {}, "test": None, "bh": False}
    s = Situation("NBA", "KXNBATOTAL", "T", "E", "T2-6h", 0.69, 0.71, 0.01, 0.5, None, None, "NBA_GAME_TOTAL", "T3", 0.70)
    return m, s


def test_kept_split_changes_arm_and_records_the_pre_split_arm():
    m, s = _setup("RIDE")
    ev = Evidence(leaf_map=m, filter_splits=_splits(("f@total", "high", "FADE", True)))
    r = route(Situation(**{**s.__dict__, "filters": {"f@total": "high"}}), ev)
    assert r.tree == "FADE" and r.arm_pre_split == "RIDE" and r.split["kept"] == ["f@total=high->FADE"]
    assert r.reasons[0].startswith("split_arm:FADE")


def test_untested_logged_only_and_conflicting_splits_leave_the_arm_alone():
    m, s = _setup("RIDE")
    for sp, fl in [(_splits(("f@total", "high", "FADE", False)), {"f@total": "high"}),   # tested, failed the rule
                   (_splits(), {"f@total": "high"}),                                     # never tested
                   (_splits(("a@total", "high", "FADE", True), ("b@total", "low", "RIDE", True)), {"a@total": "high", "b@total": "low"})]:
        r = route(Situation(**{**s.__dict__, "filters": fl}), Evidence(leaf_map=m, filter_splits=sp))
        assert r.tree == "RIDE" and r.arm_pre_split is None


def test_router_fields_logs_split_path_and_orders_stay_off():
    f = router_fields({"sport": "NBA", "market_type": "NBA_GAME_TOTAL", "band": "T3", "market_ticker": "KXNBATOTAL-26NOV12AAABBB-T220",
                       "event_ticker": "KXNBATOTAL-26NOV12AAABBB", "yes_bid": 0.69, "yes_ask": 0.71, "half_spread": 0.01, "p_yes": 0.5,
                       "horizon_hours_to_start": 5.0}, "KXNBATOTAL", prev_mid=0.70,
                      filters={"clutch_offence_ppp@total": "high", "x@total": "unknown"})["router"]
    assert f["orders"] == "off" and f["filters_n"] == 2 and f["filters_fired"] == ["clutch_offence_ppp@total"]
    assert f["split_path"].startswith("NBA|NBA_GAME_TOTAL|T3|") and isinstance(f["split_kept"], list)
    no = router_fields({}, "X")["router"]
    assert no["branch"] == "ERROR"
    miss = router_fields({"sport": "NHL", "market_type": "m", "band": "T3", "market_ticker": "t", "event_ticker": "e", "yes_bid": 0.4,
                          "yes_ask": 0.42, "horizon_hours_to_start": 5.0}, "S", prev_mid=0.4, filters=None,
                         filters_note="filters_unavailable:nhl_engine.filters_not_merged")["router"]
    assert miss["filters_note"] == "filters_unavailable:nhl_engine.filters_not_merged" and miss["filters_n"] == 0


def test_run_once_hands_filters_to_the_router(tmp_path):
    now = datetime(2026, 11, 12, 20, 0, tzinfo=timezone.utc)
    start = datetime(2026, 11, 13, 1, 0, tzinfo=timezone.utc)
    fc = SimpleNamespace(sport="NBA", forecast=lambda t, n: SimpleNamespace(p_yes=0.5, sport="NBA", model_id="m", model_sha256="s",
                                                                          feature_row_sha256="f", reasons=None))
    seen = []
    sup = SimpleNamespace(for_row=lambda row: (seen.append(row["ts_utc"]) or ({"clutch_offence_ppp@total": "high"}, None)))
    mk = {"ticker": EV + "-BOS", "event_ticker": EV, "yes_bid_dollars": "0.60", "yes_ask_dollars": "0.62"}
    res = run_once(forecaster=fc, cells=[("NBA_MONEYLINE", "KXNBAGAME")], list_markets=lambda s: (True, [mk]),
                   kickoff_for=lambda e: (start, "test"), ledger_dir=tmp_path, run_id="r", now_utc=now, code_sha="x", filter_supply=sup)
    assert sum(res["written"].values()) == 1 and seen == [now.isoformat()]
    row = json.loads(next(tmp_path.rglob("*.jsonl")).read_text().splitlines()[0])
    assert row["router"]["filters_n"] == 1 and row["router"]["orders"] == "off"


def test_coverage_layer3_needs_data_and_a_kept_split():
    splits = {"splits": [{"sport": "NBA", "series": "KXNBAGAME", "kept": True}]}
    on = cov.d6_summary(cov.d6_layers(splits_doc=splits, filter_sports={"nba"}))["by_sport"]
    off = cov.d6_summary(cov.d6_layers(splits_doc=splits, filter_sports=set()))["by_sport"]
    none = cov.d6_summary(cov.d6_layers(splits_doc={"splits": []}, filter_sports={"nba"}))["by_sport"]
    assert on["nba"]["per_layer"][2] > 0 and off["nba"]["per_layer"][2] == 0 and none["nba"]["per_layer"][2] == 0
    assert on["nfl"]["per_layer"][2] == 0  # NFL has no kept split and no data


def test_nba_adapter_adds_muse_distance_leaves_when_table_has_them():
    """W114.1 (B-087): known answer for the shot-distance entries; a table without them (older build) skips them."""
    from prediction_market_bot.archive_intake.nba_distance_filters import HIGHER_IS_BETTER
    # CLE allows few rim FG% (percentile 0.1 = good), BOS allows many (0.9): mean 0.5 -> mid; lower is better -> home_edge
    t = {**TABLE, "teams": {k: {**v, **{n: (0.1 if k == "CLE" else 0.9) for n in HIGHER_IS_BETTER}} for k, v in TABLE["teams"].items()}}
    f, note = fsup.nba_adapter(ROW, t)
    assert note is None
    assert f["opp_fg_pct_lt5@total"] == "mid"
    assert f["opp_fg_pct_lt5@side"] == "home_edge"
    assert "opp_fg_pct_lt5@total" not in fsup.nba_adapter(ROW, TABLE)[0]  # old table: not invented


def test_shipped_table_carries_all_distance_entries_and_kept_archive_splits_are_scored():
    from prediction_market_bot.archive_intake.nba_distance_filters import HIGHER_IS_BETTER
    t = fsup.nba_table()
    assert all(n in team for team in t["teams"].values() for n in HIGHER_IS_BETTER)
    sp = [s for s in lm.default_splits().doc["splits"] if s["source"].startswith("113.4")] if hasattr(lm.default_splits(), "doc") else None
    if sp is not None:
        assert len(sp) == 54 and all(s["test_games"] >= 10 and s["test_mean"] > 0 for s in sp if s["kept"])
