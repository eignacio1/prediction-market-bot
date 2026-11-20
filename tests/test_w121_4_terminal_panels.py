"""W121.4: server helpers behind the Live Terminal's candidate-arms, weekly-look and box panels."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import pytest

_REPO = Path(__file__).parent.parent
sys.path.insert(0, str(_REPO / "scripts"))
import web_dashboard as wd  # noqa: E402


def _row(v1, cands, sport="NBA", ticker="K1"):
    return {"sport": sport, "ts_utc": "2026-11-20T01:00:00Z", "market_ticker": ticker, "band": "T1",
            "router": {"arm": v1}, "router_candidates": {n: {"arm": a} for n, a in cands.items()}}


@pytest.mark.unit
def test_candidate_tally_agreement_and_diffs():
    acc: dict = {}
    wd._candidate_tally(_row("RIDE", {"router_v2": "RIDE", "nba_depth": "NO_BET"}), acc)
    wd._candidate_tally(_row("FADE", {"router_v2": "FADE", "nba_depth": "ERROR"}, ticker="K2"), acc)
    wd._candidate_tally({"sport": "NBA", "router": {"arm": "RIDE"}}, acc)   # no candidates: ignored
    out = {(r["sport"], r["candidate"]): r for r in wd._candidate_summary(acc)["rows"]}
    v2 = out[("NBA", "router_v2")]
    assert v2["rows"] == 2 and v2["same_as_v1"] == 2 and v2["agree_pct"] == 100.0 and v2["diffs"] == []
    nd = out[("NBA", "nba_depth")]
    assert nd["rows"] == 2 and nd["same_as_v1"] == 0 and nd["errors"] == 1 and nd["agree_pct"] == 0.0
    assert nd["diffs"][0] == {"ts": "2026-11-20T01:00:00Z", "ticker": "K1", "band": "T1", "v1": "Ride", "cand": "No bet"}


@pytest.mark.unit
def test_candidate_tally_diffs_are_capped():
    acc: dict = {}
    for i in range(wd.CAND_DIFF_ROWS + 10):
        wd._candidate_tally(_row("RIDE", {"router_v2": "FADE"}, ticker=f"K{i}"), acc)
    x = wd._candidate_summary(acc)["rows"][0]
    assert x["rows"] == wd.CAND_DIFF_ROWS + 10 and len(x["diffs"]) == wd.CAND_DIFF_ROWS


@pytest.mark.unit
def test_candidate_summary_empty():
    assert wd._candidate_summary({}) == {"rows": []}


@pytest.mark.unit
def test_weekly_look_none_then_newest(tmp_path):
    assert wd._weekly_look(tmp_path) == {"awaiting": "first look not run yet"}
    d = tmp_path / "exp_output" / "EVIDENCE_WEEKLY"
    d.mkdir(parents=True)
    (d / "2026-11-13.json").write_text(json.dumps({"verdict": "old"}))
    (d / "2026-11-20.json").write_text(json.dumps({"verdict": "new", "n": 5, "nested": {"a": 1}}))
    os.utime(d / "2026-11-13.json", (1, 1))
    w = wd._weekly_look(tmp_path)
    assert w["file"] == "2026-11-20.json" and w["summary"] == {"verdict": "new", "n": 5}


@pytest.mark.unit
def test_box_health_mac_copy(tmp_path, monkeypatch):
    monkeypatch.setenv("PMBOT_DISK_FAKE_PCT", "87")
    b = wd._box_health(tmp_path)
    assert b["disk"]["pct"] == 87.0 and "awaiting" in b["mac_copy"]
    (tmp_path / "LAST_RUN.json").write_text(json.dumps(
        {"utc": "20261119T000000Z", "files": 12, "ok": True, "mismatch": 0, "size": "5G"}))
    m = wd._box_health(tmp_path)["mac_copy"]
    assert m == {"utc": "20261119T000000Z", "files": 12, "ok": True, "mismatch": 0, "size": "5G"}


@pytest.mark.unit
def test_d6_carries_cell_names():
    d = wd._d6()
    for v in d["by_sport"].values():
        assert len(v["cells"]) == v["registered"]
        assert sum(c["wired"] for c in v["cells"]) == v["wired"]
