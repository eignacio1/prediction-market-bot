"""W119.2 Part C: layer-4 stump rule (operator-approved 11-17 17:45 PT)."""
from prediction_market_bot.decision_trees import coverage as cv


def _leaf(arm="NO_BET", thin=True, fit=None, test_n=0):
    return {"arm": arm, "thin": thin, "fit": fit or {}, "test": {"test_n_games": test_n}}


def test_stump_root_no_bet_when_pooled_mean_not_positive():
    ls = [_leaf(fit={"FADE": [-0.05, 20], "RIDE": [-0.02, 20]}), _leaf(fit={"FADE": [-0.03, 20], "RIDE": [-0.01, 20]})]
    s = cv.stump_root(ls)
    assert s["arm"] == "NO_BET" and s["rows"] == 40


def test_stump_root_picks_best_positive_arm_row_weighted():
    ls = [_leaf(fit={"RIDE": [0.10, 10]}), _leaf(fit={"RIDE": [0.02, 30], "FADE": [-0.01, 40]})]
    s = cv.stump_root(ls)
    assert s["arm"] == "RIDE" and abs(s["pooled_mean_net"]["RIDE"] - 0.04) < 1e-9


def test_stump_root_none_below_min_rows_or_empty_fit():
    assert cv.stump_root([_leaf(fit={"RIDE": [0.5, cv.MIN_STUMP_ROWS - 1]})]) is None
    assert cv.stump_root([_leaf()]) is None


def _cell(mt="NBA_SPREAD", band="T1"):
    return [{"market_type": mt, "band": band, "sport": "NBA", "family": None}]


def _run(leaves):
    doc = {"leaves": {f"NBA|NBA_SPREAD|T1|{i}": l for i, l in enumerate(leaves)}}
    return cv.d6_layers(leaf_map_doc=doc, rows=_cell(), splits_doc={"splits": []}, filter_sports=set())[0]


def test_layer4_credited_for_stump_not_for_empty_cell():
    c = _run([_leaf(fit={"FADE": [-0.04, 40]})])
    assert c["layers"][3] and c["l4_stump"] and c["stump_arm"] == "NO_BET" and not c["wired"]
    c = _run([_leaf()])
    assert not c["layers"][3] and not c["l4_stump"]


def test_arm_leaf_beats_stump():
    c = _run([_leaf(arm="RIDE", thin=False, fit={"RIDE": [0.1, 50]})])
    assert c["layers"][3] and not c["l4_stump"]
