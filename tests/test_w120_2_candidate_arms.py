"""W120.2 -- candidate maps (router v2, +nba_depth, nhl_v2) logged beside v1 on shadow rows. Shadow only; v1 orders unchanged."""
import json

from prediction_market_bot.decision_trees import shadow_route as sr


def _row(sport="NBA", mt="NBA_GAME_TOTAL", band="T3", tk="KXNBATOTAL-26NOV12AAABBB-T220"):
    return {"sport": sport, "market_type": mt, "band": band, "market_ticker": tk, "event_ticker": tk.rsplit("-", 1)[0],
            "yes_bid": 0.68, "yes_ask": 0.72, "half_spread": 0.02, "p_yes": 0.7, "horizon_hours_to_start": 3.0}


def test_off_by_default_row_has_only_v1(monkeypatch):
    monkeypatch.delenv("PM_CANDIDATE_ARMS", raising=False)
    assert "router_candidates" not in sr.router_fields(_row(), "KXNBATOTAL", prev_mid=0.7)


def test_on_adds_columns_and_leaves_v1_block_identical(monkeypatch):
    monkeypatch.delenv("PM_CANDIDATE_ARMS", raising=False)
    off = sr.router_fields(_row(), "KXNBATOTAL", prev_mid=0.7)["router"]
    monkeypatch.setenv("PM_CANDIDATE_ARMS", "on")
    on = sr.router_fields(_row(), "KXNBATOTAL", prev_mid=0.7)
    assert on["router"] == off
    c = on["router_candidates"]
    assert set(c) == {"router_v2", "nba_depth"}          # nhl_v2 does not apply to NBA
    for rec in c.values():
        assert rec["arm"] != "ERROR" and len(rec["map_sha256"]) == 64 and rec["map_version"] and rec["map"].endswith(".json")
    json.dumps(on)


def test_nhl_row_gets_router_v2_and_nhl_v2(monkeypatch):
    monkeypatch.setenv("PM_CANDIDATE_ARMS", "on")
    r = _row("NHL", "NHL_MONEYLINE", "T2", "KXNHLGAME-26NOV12AAABBB-AAA")
    assert set(sr.router_fields(r, "KXNHLGAME", prev_mid=0.7)["router_candidates"]) == {"router_v2", "nhl_v2"}


def test_erroring_map_logs_error_and_never_blocks_the_row(monkeypatch):
    monkeypatch.setenv("PM_CANDIDATE_ARMS", "on")
    monkeypatch.setitem(sr.CANDIDATES, "router_v2", ("nope_version", None, False))
    out = sr.router_fields(_row(), "KXNBATOTAL", prev_mid=0.7)
    assert out["router"]["branch"] != "ERROR"
    rec = out["router_candidates"]["router_v2"]
    assert rec["arm"] == "ERROR" and "nope_version" in rec["reason"]
    assert out["router_candidates"]["nba_depth"]["arm"] != "ERROR"


def test_candidate_uses_the_previous_mid_not_this_rows(monkeypatch):
    monkeypatch.setenv("PM_CANDIDATE_ARMS", "on")
    seen = {}
    real = sr.route

    def spy(s, ev):
        seen.setdefault("prev", []).append(s.prev_mid)
        return real(s, ev)
    monkeypatch.setattr(sr, "route", spy)
    sr._SEEN.clear()
    sr._SEEN["KXNBATOTAL-26NOV12AAABBB-T220"] = 0.55
    sr.router_fields(_row(), "KXNBATOTAL")
    assert seen["prev"] and all(p == 0.55 for p in seen["prev"])


# ---- Part B: NHL goalie + special-teams verdicts logged on NHL rows (not applied to v1) ----
import subprocess
from prediction_market_bot.decision_trees import leaf_map as lm


def test_goalie_st_verdicts_are_logged_and_never_applied():
    fs = lm.FilterSplits.load()
    new = [s for s in fs.doc["splits"] if s["sport"] == "NHL" and s["filter"].startswith(("goalie@", "special_teams@"))]
    assert len(new) == 42 and all(s["kept"] is False and s["why"].endswith("|logged_not_applied_to_v1") for s in new)
    assert sum(s["verdict"] == "kept" for s in new) == 8
    r = fs.lookup("NHL", "KXNHLGAME", {"goalie@side": new[0]["leaf"] if new[0]["filter"] == "goalie@side" else "home_edge"})
    assert r["arm"] is None and not r["conflict"]


def test_v1_nhl_row_logs_a_tested_split_and_keeps_its_arm():
    fs = lm.FilterSplits.load()
    s = next(x for x in fs.doc["splits"] if x["sport"] == "NHL" and x["filter"].startswith("goalie@") and x["series"] == "KXNHLGAME")
    look = fs.lookup("NHL", "KXNHLGAME", {s["filter"]: s["leaf"]})
    assert look["logged_only"] and not look["kept"] and look["arm"] is None


def test_existing_splits_unchanged_by_the_append():
    head = subprocess.run(["git", "show", "origin/main:src/prediction_market_bot/decision_trees/filter_splits.json"],
                          capture_output=True, text=True)
    if head.returncode != 0:
        return
    import json
    old = json.loads(head.stdout)["splits"]
    now = lm.FilterSplits.load().doc["splits"]
    assert now[:len(old)] == old
