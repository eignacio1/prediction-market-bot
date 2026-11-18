"""W116.1: PM_LEAF_MAP_VERSION switch (default v1) and the v2 map's shape. The router itself is unchanged."""
import json

import pytest

from prediction_market_bot.decision_trees import leaf_map as lm


def test_default_is_v1(monkeypatch):
    monkeypatch.delenv("PM_LEAF_MAP_VERSION", raising=False)
    assert lm.map_path() == lm.DEFAULT_MAP
    assert lm.default_map().doc.get("version") != "v2"


def test_v2_selected_by_env(monkeypatch):
    monkeypatch.setenv("PM_LEAF_MAP_VERSION", "v2")
    m = lm.default_map()
    assert m.doc["version"] == "v2" and m.doc["arm_source"] == "leaf_map_v2_pooled_sequential_w115_1"


def test_unknown_version_refused(monkeypatch):
    monkeypatch.setenv("PM_LEAF_MAP_VERSION", "v3")
    with pytest.raises(ValueError):
        lm.default_map()


def test_v2_decision_carries_posterior_and_source():
    m = lm.LeafMap.load(lm.MAP_VERSIONS["v2"])
    lid, rec = next((k, v) for k, v in m.leaves.items() if v["seen"])
    sport, mt, band, b, mv = lid.split("|")
    doc = {"version": "v2", "leaves": {lid: {**rec, "arm": "RIDE"}}}
    r = {"sport": sport, "market_type": mt, "band": band}
    one = lm.LeafMap(doc)
    one.leaf_id = lambda _r: lid  # isolate decide() from the bin arithmetic
    d = one.decide({**r, "mid": 0.6, "move": None, "yes_ask": 0.61, "yes_bid": 0.59, "market_ticker": "X-Y"})
    assert d.arm == "RIDE" and d.posterior == rec["posterior"] and d.source == rec["source"] and d.known and not d.thin
    no = lm.LeafMap({"version": "v2", "leaves": {lid: {**rec, "arm": "NO_BET"}}})
    no.leaf_id = lambda _r: lid
    assert no.decide(r).reason == "leaf_no_arm_earned_v2"


def test_v1_decision_fields_default_none():
    m = lm.LeafMap.load(lm.MAP_VERSIONS["v1"])
    lid = next(iter(m.leaves))
    m.leaf_id = lambda _r: lid
    d = m.decide({"move": None, "mid": 0.6, "yes_ask": 0.61, "yes_bid": 0.59, "market_ticker": "X-Y"}, p_yes=0.6)
    assert d.posterior is None and d.source is None


def test_v2_map_covers_every_bin_and_move_of_each_family():
    doc = json.load(open(lm.MAP_VERSIONS["v2"]))
    fams = {tuple(k.split("|")[:3]) for k in doc["leaves"]}
    assert len(doc["leaves"]) == len(fams) * (len({k.split("|")[3] for k in doc["leaves"]})) * 4
    for v in doc["leaves"].values():
        assert set(v) >= {"arm", "posterior", "source", "rows", "games", "seen"}


def test_v2_map_bytes_match_the_frozen_preregistration():
    """The src/ copy is a reviewed promotion of 12_EXPLORATORY/evidence_design/run.py output; any change to it
    needs a new pre-registration (ROUTER_V2_PREREGISTRATION_2026-11-17.md)."""
    import hashlib
    from prediction_market_bot.decision_trees import leaf_map as lm
    digest = hashlib.sha256(open(lm.MAP_VERSIONS["v2"], "rb").read()).hexdigest()
    assert digest == "79f46cb4ae1fded6d01f5e8e59cb816848294b550061566c3b8779e7721bad5b"
