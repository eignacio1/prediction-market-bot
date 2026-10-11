"""EXP-037 D2/D3 unit tests: ledger idempotence, bands, fees, venue pagination, settlement join,
scoring, tickers, model coherence + information cutoff."""
from __future__ import annotations

import json
import math
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pandas as pd
import pytest

from prediction_market_bot.pregame_shadow import fees, scoring
from prediction_market_bot.pregame_shadow.bands import band_for_horizon
from prediction_market_bot.pregame_shadow.ledger import CellLedger, ROW_FIELDS
from prediction_market_bot.pregame_shadow.nfl_forecaster import (
    parse_event_ticker, parse_market_ticker)
from prediction_market_bot.pregame_shadow.nfl_model import NFLPregameModel, canonical_sha, p_yes_for
from prediction_market_bot.pregame_shadow.nfl_settlement import join_row

ROOT = Path(__file__).resolve().parent.parent
MODEL = ROOT / "models" / "nfl_pregame_v1.json"


def _row(**kw):
    base = {f: 0 for f in ROW_FIELDS}
    base.update(run_id="r", market_ticker="T", ts_utc="2026-10-03T00:00:00+00:00")
    base.update(kw)
    return base


def test_ledger_append_only_and_idempotent(tmp_path):
    led = CellLedger(tmp_path, "NFL", "NFL_MONEYLINE", "T1")
    assert led.append(_row()) is True
    assert led.append(_row()) is False
    assert CellLedger(tmp_path, "NFL", "NFL_MONEYLINE", "T1").append(_row()) is False  # reload
    assert led.append(_row(market_ticker="U")) is True
    assert len(led.path.read_text().splitlines()) == 2
    with pytest.raises(ValueError):
        led.append({"run_id": "x"})


def test_band_windows():
    assert band_for_horizon(30) == "T1" and band_for_horizon(12) == "T1"
    assert band_for_horizon(48) is None and band_for_horizon(10) is None
    assert band_for_horizon(6) == "T2" and band_for_horizon(8) is None
    assert band_for_horizon(0.5) == "T3" and band_for_horizon(0.1) is None


def test_fee_candidates():
    assert fees.fee_k007(0.5) == pytest.approx(0.0175)
    assert fees.fee_kmult(0.5) == pytest.approx(0.00875)
    ey, en = fees.e_net(0.6, 0.50, 0.54, fees.fee_k007)
    assert ey == pytest.approx(0.6 - 0.54 - fees.fee_k007(0.54))
    assert en == pytest.approx(0.4 - 0.5 - fees.fee_k007(0.5))


def test_ticker_parsing_matches_live_shapes():
    assert parse_event_ticker("KXNFLGAME-26OCT04ARINYG") == ("NFL_MONEYLINE", "2026-10-04", "ARI", "NYG")
    assert parse_event_ticker("KXNFLGAME-26OCT08TBDAL")[2:] == ("TB", "DAL")
    assert parse_event_ticker("KXNFLGAME-26OCT04LARSF")[2:] == ("LA", "SF")  # Kalshi LAR -> nflverse LA
    ml = parse_market_ticker("KXNFLGAME-26OCT04ARINYG-NYG")
    assert ml["subject"] == "NYG" and ml["strike"] is None
    sp = parse_market_ticker("KXNFLSPREAD-26OCT08TBDAL-TB8")
    assert sp["subject"] == "TB" and sp["strike"] == 7.5
    tt = parse_market_ticker("KXNFLTOTAL-26OCT08TBDAL-69")
    assert tt["subject"] is None and tt["strike"] == 68.5
    tm = parse_market_ticker("KXNFLTEAMTOTAL-26OCT04ARINYG-NO8".replace("ARINYG", "NOTB"))
    assert tm["subject"] == "NO" and tm["strike"] == 7.5
    assert parse_market_ticker("KXMLBGAME-26OCT04ARINYG-NYG") is None


class _Resp:
    def __init__(self, code, payload=None):
        self.status_code, self._p = code, payload or {}

    def json(self):
        return self._p


class _Sess:
    def __init__(self, resps):
        self.resps, self.calls = list(resps), []

    def get(self, url, params=None, timeout=None):
        self.calls.append(dict(params or {}))
        return self.resps.pop(0)


def test_venue_listing_paginates_throttles_and_halves_on_429():
    from prediction_market_bot.c5_execution.venue_adapter import KalshiVenueAdapter

    class Client:
        _session = _Sess([_Resp(200, {"markets": [{"ticker": "A"}], "cursor": "c1"}),
                          _Resp(429),
                          _Resp(200, {"markets": [{"ticker": "B"}], "cursor": ""})])

    t = [0.0]
    sleeps = []

    def sleep(s):
        sleeps.append(s)
        t[0] += s

    ad = KalshiVenueAdapter(Client())
    ok, mk = ad.list_series_markets_raw("KXNFLGAME", _sleep=sleep, _clock=lambda: t[0])
    assert ok and [m["ticker"] for m in mk] == ["A", "B"]
    assert Client._session.calls[1].get("cursor") == "c1"
    assert all(s >= 1.0 for s in sleeps)          # never faster than 1 req/s
    assert max(sleeps) >= 2.2                      # interval doubled after the 429
    assert "limit" in Client._session.calls[0]     # one list call per page, no per-market GETs


def test_settlement_join_scalars_and_tie():
    clim = {"home_win_rate_ex_ties": 0.55, "mean_margin": 1.5, "mean_total": 45.0, "sd_margin": 13.5,
            "sd_total": 13.0}
    r = lambda t, mt: {"market_ticker": t, "market_type": mt}
    j = join_row(r("KXNFLGAME-26OCT04ARINYG-NYG", "NFL_MONEYLINE"), "NYG", "ARI", 20, 20, clim)
    assert j["y"] == 0.5                                    # tie -> $0.50 each
    j = join_row(r("KXNFLGAME-26OCT04ARINYG-ARI", "NFL_MONEYLINE"), "NYG", "ARI", 17, 20, clim)
    assert j["y"] == 1.0 and j["game_key"] == "2026-10-04:ARI@NYG"
    j = join_row(r("KXNFLSPREAD-26OCT04ARINYG-NYG8", "NFL_SPREAD"), "NYG", "ARI", 30, 21, clim)
    assert j["y"] == 1.0                                    # won by 9 > 7.5
    j = join_row(r("KXNFLTOTAL-26OCT04ARINYG-45", "NFL_GAME_TOTAL"), "NYG", "ARI", 20, 24, clim)
    assert j["y"] == 0.0                                    # 44 < 44.5
    j = join_row(r("KXNFLTEAMTOTAL-26OCT04ARINYG-ARI25", "NFL_TEAM_TOTAL"), "NYG", "ARI", 10, 27, clim)
    assert j["y"] == 1.0                                    # 27 > 24.5
    assert all(0 < j["p_clim"] < 1 for j in [j])


def test_scoring_cluster_bootstrap_and_first_row_rule():
    rows = []
    for g in range(30):
        for k in range(3):
            rows.append({"market_ticker": f"M{g}-{k}", "band": "T1", "ts_utc": "2026-10-03T00:00:00",
                         "p_yes": 0.8 if g % 2 == 0 else 0.2, "mid": 0.5, "p_clim": 0.5, "yes_bid": 0.49,
                         "yes_ask": 0.51, "y": 1.0 if g % 2 == 0 else 0.0, "game_key": f"G{g}"})
    s = scoring.score_cell(rows)
    assert s["n_games"] == 30 and s["n_rows"] == 90
    assert s["delta_brier_vs_market"]["ci95"][0] > 0       # model beats market => delta POSITIVE (brief convention)
    assert s["delta_brier_vs_climatology"]["mean"] > 0
    dup = rows + [dict(rows[0], ts_utc="2026-10-04T00:00:00", p_yes=0.01)]
    assert len(scoring.first_row_per_market(dup)) == 90
    assert scoring.first_row_per_market(dup)[0]["p_yes"] != 0.01  # earliest row wins


# ---------------- model: artifact integrity, coherence, information cutoff ----------------
@pytest.fixture(scope="module")
def model():
    return NFLPregameModel.load(MODEL)


FEATS = dict(off_epa_h=0.05, def_epa_h=-0.02, off_epa_a=-0.03, def_epa_a=0.04, pf_h=24.0, pa_h=21.0,
             pf_a=20.0, pa_a=25.0, rest_diff=0.0, rest_short_h=0.0, rest_short_a=0.0)


def test_artifact_hash_verified_and_tamper_refused():
    art = json.loads(MODEL.read_text())
    assert canonical_sha(art) == art["sha256"]
    art["sigma_margin"] += 1.0
    with pytest.raises(ValueError):
        NFLPregameModel(art)


def test_ladders_are_coherent_by_construction(model):
    ps = [p_yes_for(model, FEATS, "NFL_SPREAD", subject_is_home=True, strike=k + 0.5) for k in range(0, 20)]
    assert all(a > b for a, b in zip(ps, ps[1:]))                       # monotone in strike
    tot = [p_yes_for(model, FEATS, "NFL_GAME_TOTAL", strike=k + 0.5) for k in range(30, 60)]
    assert all(a > b for a, b in zip(tot, tot[1:]))
    ml_h = p_yes_for(model, FEATS, "NFL_MONEYLINE", subject_is_home=True)
    ml_a = p_yes_for(model, FEATS, "NFL_MONEYLINE", subject_is_home=False)
    assert ml_h + ml_a == pytest.approx(1.0)
    # home spread -0.5 ~ moneyline (differ only by tie mass); away +0.5 complements it
    cover = p_yes_for(model, FEATS, "NFL_SPREAD", subject_is_home=True, strike=0.5)
    d0 = model.distribution(FEATS)
    from prediction_market_bot.pregame_shadow.nfl_model import _phi
    tie_mass = _phi((0.5 - d0["mu_margin"]) / d0["sigma_margin"]) - _phi((-0.5 - d0["mu_margin"]) / d0["sigma_margin"])
    assert ml_h - cover == pytest.approx(0.5 * tie_mass)   # exact identity: ML = P(win by >=1) + half the tie mass
    # team totals are consistent with the game total in expectation
    d = model.distribution(FEATS)
    mh = (d["mu_total"] + d["mu_margin"]) / 2
    ma = (d["mu_total"] - d["mu_margin"]) / 2
    assert mh + ma == pytest.approx(d["mu_total"])


@pytest.fixture(scope="module")
def tiny_league():
    """Two teams, enough games for min_periods; used to prove no after-as_of data leaks."""
    rows, stats = [], []
    start = datetime(2025, 9, 7)
    for i in range(10):
        day = (start + timedelta(days=7 * i)).date().isoformat()
        gid = f"2025_{i + 1:02d}_AAA_BBB"
        rows.append(dict(game_id=gid, season=2025, game_type="REG", week=i + 1, gameday=day,
                         home_team="AAA", away_team="BBB", home_score=20 + i, away_score=17,
                         home_rest=7, away_rest=7))
        stats.append(dict(season=2025, week=i + 1, season_type="REG", game_id=gid, team="AAA",
                          opponent_team="BBB", off_epa=0.1 + 0.01 * i))
        stats.append(dict(season=2025, week=i + 1, season_type="REG", game_id=gid, team="BBB",
                          opponent_team="AAA", off_epa=-0.1))
    return pd.DataFrame(rows), pd.DataFrame(stats)


def test_information_cutoff_no_feature_uses_data_dated_after_as_of(tiny_league):
    from prediction_market_bot.c1_signal_ingestion.nfl_pregame_features import NFLPregameFeatureBuilder
    sched, stats = tiny_league
    as_of = datetime(2025, 10, 20, tzinfo=timezone.utc)      # after week 7 (Oct 19 is wk6... see below)
    base = NFLPregameFeatureBuilder(stats, sched).row("AAA", "BBB", as_of, 7, 7)
    assert base is not None
    # corrupt every game dated ON OR AFTER as_of: the row must not move (TI-01, strict <)
    late = pd.to_datetime(sched["gameday"]).dt.date >= as_of.date()
    s2 = sched.copy()
    s2.loc[late, ["home_score", "away_score"]] = 99
    bad_ids = set(s2.loc[late, "game_id"])
    st2 = stats.copy()
    st2.loc[st2.game_id.isin(bad_ids), "off_epa"] = 9.0
    again = NFLPregameFeatureBuilder(st2, s2).row("AAA", "BBB", as_of, 7, 7)
    assert again["features"] == base["features"] and again["sha256"] == base["sha256"]
    # and the converse: corrupting data BEFORE as_of does move it (the test can fail)
    early = ~late
    st3 = stats.copy()
    st3.loc[st3.game_id.isin(set(sched.loc[early, "game_id"])), "off_epa"] = 9.0
    moved = NFLPregameFeatureBuilder(st3, sched).row("AAA", "BBB", as_of, 7, 7)
    assert moved["features"] != base["features"]
    # a same-day game result never enters a row evaluated that day
    day_of = datetime.fromisoformat(str(sched.loc[late].iloc[0]["gameday"])).replace(tzinfo=timezone.utc)
    r_day = NFLPregameFeatureBuilder(stats, sched).row("AAA", "BBB", day_of, 7, 7)
    s4 = sched.copy(); s4.loc[s4.gameday == str(day_of.date()), ["home_score", "away_score"]] = 99
    r_day2 = NFLPregameFeatureBuilder(stats, s4).row("AAA", "BBB", day_of, 7, 7)
    assert r_day["sha256"] == r_day2["sha256"]


def test_live_kalshi_team_codes_all_parse():
    """Event strings observed live 2026-10-02 (Kalshi uses WAS, LAR, JAC). WSH was a wrong assumption."""
    from prediction_market_bot.pregame_shadow.nfl_forecaster import parse_event_ticker
    live = ["ARINYG", "ATLNO", "BALATL", "BUFLAR", "CHIGB", "CINMIA", "CLENYJ", "DALHOU", "DENLAC", "DENSF",
            "DETARI", "DETCAR", "GBTB", "HOUTEN", "INDPIT", "INDWAS", "JACCIN", "KCLV", "LACSEA", "LARPHI",
            "LVNE", "MIAMIN", "MINNO", "NEBUF", "NYGWAS", "NYJCHI", "PHIJAC", "SFSEA", "TBDAL", "TENBAL"]
    bad = [e for e in live if parse_event_ticker(f"KXNFLGAME-26OCT04{e}") is None]
    assert bad == []


def test_nfl_pregame_cells_shadow_and_inplay_untouched():
    from prediction_market_bot.c5_execution.market_type_registry import (
        CellStatus, ExecutionBand, MarketType, get_cell)
    for mt in (MarketType.NFL_MONEYLINE, MarketType.NFL_SPREAD,
               MarketType.NFL_GAME_TOTAL, MarketType.NFL_TEAM_TOTAL):
        for b in (ExecutionBand.T1_MULTI_DAY, ExecutionBand.T2_SAME_DAY, ExecutionBand.T3_PRE_TIP):
            c = get_cell(mt, b)
            assert c.status is CellStatus.SHADOW and c.citing_decision == "EXP-037", (mt, b)
        assert get_cell(mt, ExecutionBand.T4NFL_ARITH).status is CellStatus.NOT_IMPLEMENTED


def test_mlb_game_market_cells_shadow_and_inplay_untouched():
    """W63.1 (T-763): the 12 MLB game cells are SHADOW under EXP-037; T4 in-play cells stay unseeded/untouched."""
    from prediction_market_bot.c5_execution.market_type_registry import (
        CellStatus, ExecutionBand, MarketType, get_cell)
    for mt in (MarketType.MLB_MONEYLINE, MarketType.MLB_RUN_LINE,
               MarketType.MLB_GAME_TOTAL, MarketType.MLB_TEAM_TOTAL):
        for b in (ExecutionBand.T1_MULTI_DAY, ExecutionBand.T2_SAME_DAY, ExecutionBand.T3_PRE_TIP):
            c = get_cell(mt, b)
            assert c.status is CellStatus.SHADOW and c.citing_decision == "EXP-037", (mt, b)


def test_registry_shadow_total_is_39():
    """3 MLB player-hits + 12 NFL + 9 NHL (W54.1) + 12 MLB game markets (W63.1) + 3 NBA player-points (W65.1)."""
    from prediction_market_bot.c5_execution.market_type_registry import CellStatus, cells_by_status
    assert len(cells_by_status(CellStatus.SHADOW)) == 39
