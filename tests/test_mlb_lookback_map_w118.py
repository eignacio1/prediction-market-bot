"""W118.1: the frozen MLB 2026 look-back leaf map is pinned and NOT wired into the router default."""
import hashlib, json, os

from prediction_market_bot.decision_trees import leaf_map as lm

P = os.path.join(os.path.dirname(lm.__file__), "leaf_maps", "mlb_2026_lookback.json")
SHA256 = "898b48554bd39d717372cdbe06db5409bd03725932fc373b77f1e2cdf37992be"


def test_frozen_sha():
    assert hashlib.sha256(open(P, "rb").read()).hexdigest() == SHA256


def test_not_wired_and_every_cell_has_a_routing():
    assert "mlb_2026_lookback" not in lm.MAP_VERSIONS
    doc = json.load(open(P))
    assert len(doc["cells"]) == 12 and all(c["routing"] for c in doc["cells"].values())
    assert all(l["arm"] in ("NO_BET", "RIDE", "FADE", "MODEL_FADE", "MOMENTUM", "POT_OF_GOLD") for l in doc["leaves"].values())
