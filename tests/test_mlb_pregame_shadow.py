"""EXP-037 / T-608 MLB: forecaster, model integrity, as-of cutoff, strike coherence (no network)."""
import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import pytest

from prediction_market_bot.c1_signal_ingestion.mlb_game_pregame_features import (
    FEATURE_NAMES, MLBGameFeatureBuilder)
from prediction_market_bot.pregame_shadow.mlb_forecaster import (
    MLBForecaster, MLBScheduleIndex, parse_event_ticker, parse_market_ticker)
from prediction_market_bot.pregame_shadow.mlb_model import MLBPregameModel

MODEL = Path(__file__).resolve().parent.parent / "models" / "mlb_game_pregame_v1.json"
pytestmark = pytest.mark.skipif(not MODEL.exists(), reason="frozen artifact not present")


def _games():
    rows, pk = [], 1
    for day in range(1, 61):
        for h, a, hs, as_ in (("LAD", "ATL", 5, 3), ("ATL", "LAD", 2, 4)):
            rows.append({"game_pk": pk, "game_type": "R", "season": 2026, "game_date": f"2026-05-{(day % 28) + 1:02d}"
                         if day < 29 else f"2026-06-{(day % 28) + 1:02d}", "start_utc": "2026-05-01T23:00:00Z",
                         "status": "Final", "home": h, "away": a, "home_score": hs, "away_score": as_,
                         "home_sp": 1.0, "away_sp": 2.0})
            pk += 1
    rows.append({"game_pk": 9999, "game_type": "D", "season": 2026, "game_date": "2026-10-03",
                 "start_utc": "2026-10-03T20:00:00Z", "status": "Preview", "home": "LAD", "away": "ATL",
                 "home_score": None, "away_score": None, "home_sp": 1.0, "away_sp": None})
    return pd.DataFrame(rows)


def test_ticker_grammar():
    ev = parse_event_ticker("KXMLBGAME-26OCT031600ATLLAD")
    assert (ev["away"], ev["home"]) == ("ATL", "LAD")
    assert ev["start_utc"] == datetime(2026, 10, 3, 20, 0, tzinfo=timezone.utc)   # 16:00 ET (EDT)
    s = parse_market_ticker("KXMLBSPREAD-26OCT031600ATLLAD-LAD4")
    assert s["strike"] == 3.5 and s["subject"] == "LAD"
    assert parse_market_ticker("KXMLBTOTAL-26OCT031600ATLLAD-9")["strike"] == 8.5
    assert parse_market_ticker("KXMLBTEAMTOTAL-26OCT031600ATLLAD-LAD8")["strike"] == 7.5
    assert parse_market_ticker("KXMLBGAME-26OCT031600ATLLAD-XXX") is None
    assert parse_market_ticker("KXMLBTOTAL-26OCT031600ATLLAD-LAD9") is None


def test_sha_tamper_refused(tmp_path):
    art = json.loads(MODEL.read_text())
    art["sigma_margin"] += 0.1
    p = tmp_path / "m.json"
    p.write_text(json.dumps(art))
    with pytest.raises(ValueError):
        MLBPregameModel.load(p)


def test_as_of_cutoff_excludes_same_day_and_later():
    fb = MLBGameFeatureBuilder(_games())
    before = fb.row("LAD", "ATL", datetime(2026, 6, 30, tzinfo=timezone.utc), 1, 2)
    g = _games()
    g.loc[len(g)] = {**g.iloc[0].to_dict(), "game_pk": 5000, "game_date": "2026-06-30",
                     "home_score": 30, "away_score": 0}
    after = MLBGameFeatureBuilder(g).row("LAD", "ATL", datetime(2026, 6, 30, tzinfo=timezone.utc), 1, 2)
    assert before["sha256"] == after["sha256"]          # same-day game is invisible


def test_strikes_coherent_and_starter_unknown_falls_back():
    games = _games()
    fc = MLBForecaster(MLBPregameModel.load(MODEL), MLBGameFeatureBuilder(games), MLBScheduleIndex(games))
    as_of = datetime(2026, 10, 3, 8, 0, tzinfo=timezone.utc)
    t = lambda s: fc.forecast(f"KXMLBGAME-26OCT031600ATLLAD-{s}", as_of)  # noqa: E731
    home, away = t("LAD"), t("ATL")
    assert abs(home.p_yes + away.p_yes - 1.0) < 1e-3
    tot = [fc.forecast(f"KXMLBTOTAL-26OCT031600ATLLAD-{n}", as_of).p_yes for n in (6, 8, 10)]
    assert tot[0] > tot[1] > tot[2]
    rl = [fc.forecast(f"KXMLBSPREAD-26OCT031600ATLLAD-LAD{n}", as_of).p_yes for n in (2, 3, 4)]
    assert rl[0] > rl[1] > rl[2] and home.p_yes > rl[0]
    assert home.feature_row_sha256 and home.model_sha256 == fc.model.sha256
