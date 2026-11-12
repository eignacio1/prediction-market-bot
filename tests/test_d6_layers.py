from prediction_market_bot.decision_trees import coverage


def _doc():
    full = {"arm": "RIDE", "thin": False, "fit": {"RIDE": [0.1, 80], "MODEL_FADE": [0.0, 80]}, "test": {"test_n_games": 12}}
    thin = {"arm": "NO_BET", "thin": True, "fit": {}, "test": None}
    return {"leaves": {"NBA|NBA_SPREAD|T1|2|na": full, "NBA|NBA_TOTAL|T1|2|na": thin}}


def _rows():
    return [{"market_type": m, "band": "T1", "sport": "NBA"} for m in ("NBA_SPREAD", "NBA_TOTAL", "NBA_ML")]


def test_layers_need_evidence_and_nothing_is_wired_without_sizing_and_fills():
    cs = {c["market_type"]: c for c in coverage.d6_layers(_doc(), _rows())}
    assert cs["NBA_SPREAD"]["layers"] == [True, True, False, True, True, False, False]
    assert cs["NBA_TOTAL"]["layers"] == [False, True, False, False, False, False, False]
    assert cs["NBA_ML"]["n_layers"] == 0
    assert not any(c["wired"] for c in cs.values())


def test_summary_counts_per_layer_and_wired_requires_all_seven(monkeypatch):
    cells = [{"sport": "NBA", "layers": [True] * 7, "wired": True}, {"sport": "NBA", "layers": [True] + [False] * 6, "wired": False}]
    s = coverage.d6_summary(cells)
    assert s["wired"] == 1 and s["by_sport"]["NBA"]["per_layer"] == [2, 1, 1, 1, 1, 1, 1]


def test_real_registry_reports_a_number():
    s = coverage.d6_summary(coverage.d6_layers())
    assert s["registered"] > 0 and s["wired"] == 0
