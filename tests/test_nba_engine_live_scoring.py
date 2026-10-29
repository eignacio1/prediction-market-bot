from prediction_market_bot.nba_engine import live_scoring as S


def _row(fam, subj, n, pe, pm, ev="E1"):
    return {"family": fam, "subject": subj, "strike_n": n, "p_engine": pe, "p_market": pm, "home": "LAL",
            "away": "POR", "game_date": "2026-10-27", "event_ticker": ev}


RES = {("2026-10-27", "LAL", "POR"): (110, 100)}


def test_outcome_known_answers():
    f = (110, 100)
    assert S.outcome(_row("NBA_MONEYLINE", "LAL", 0, 0, 0), f) == 1
    assert S.outcome(_row("NBA_MONEYLINE", "POR", 0, 0, 0), f) == 0
    assert S.outcome(_row("NBA_SPREAD", "LAL", 10, 0, 0), f) == 1
    assert S.outcome(_row("NBA_SPREAD", "LAL", 11, 0, 0), f) == 0
    assert S.outcome(_row("NBA_SPREAD", "POR", 1, 0, 0), f) == 0
    assert S.outcome(_row("NBA_GAME_TOTAL", "", 210, 0, 0), f) == 1
    assert S.outcome(_row("NBA_TEAM_TOTAL", "POR", 101, 0, 0), f) == 0


def test_score_pairs_and_skips():
    rows = [_row("NBA_MONEYLINE", "LAL", 0, 0.9, 0.5), _row("NBA_MONEYLINE", "POR", 0, 0.1, 0.5),
            _row("NBA_MONEYLINE", "LAL", 0, 0.9, None, ev="E2")]
    s = S.score(rows, RES, b=200)
    m = s["NBA_MONEYLINE"]
    assert m["n_rows"] == 2 and m["n_games"] == 1
    assert abs(m["mean_diff"] - (0.01 - 0.25)) < 1e-12
    assert abs(m["w"] - (1 - 0.01 / 0.25)) < 1e-12
    assert s["NBA_SPREAD"]["n_rows"] == 0
