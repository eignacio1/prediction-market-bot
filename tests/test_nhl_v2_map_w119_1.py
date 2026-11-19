"""W119.1: nhl_v2 map is opt-in, changes only NHL leaves versus v2, and routes every seen NHL leaf to an arm or NO_BET."""
import json

from prediction_market_bot.decision_trees import leaf_map as lm


def _doc(v):
    return json.load(open(lm.MAP_VERSIONS[v]))


def test_default_still_v1(monkeypatch):
    monkeypatch.delenv("PM_LEAF_MAP_VERSION", raising=False)
    assert lm.map_path() == lm.DEFAULT_MAP


def test_nhl_v2_selected_by_env(monkeypatch):
    monkeypatch.setenv("PM_LEAF_MAP_VERSION", "nhl_v2")
    assert lm.default_map().doc["version"] == "nhl_v2"


def test_only_nhl_leaves_differ_from_v2():
    a, b = _doc("v2")["leaves"], _doc("nhl_v2")["leaves"]
    assert set(a) == set(b)
    assert all(a[k] == b[k] for k in a if not k.startswith("NHL|"))


def test_seen_nhl_leaves_have_arm_or_no_bet():
    seen = [v for k, v in _doc("nhl_v2")["leaves"].items() if k.startswith("NHL|") and v.get("seen")]
    assert seen and all(v["arm"] in {"RIDE", "FADE", "MOMENTUM", "POT_OF_GOLD", "NO_BET"} for v in seen)
