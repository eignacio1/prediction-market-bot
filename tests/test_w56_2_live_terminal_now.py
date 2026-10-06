"""W56.2: Live Terminal NOW module — decision stream, drawdown vs kill switch, honest empty/stale shapes."""
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import web_dashboard as wd  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
NOW = datetime(2026, 10, 5, 20, 0, tzinfo=timezone.utc)


def _port(rp, init=1000.0, lu="2026-10-05T19:59:00Z"):
    return {"initial_bankroll_usd": init, "total_realized_pnl": rp, "last_updated": lu}


def _shadow(rows):
    return {"cells": [{"sport": "NHL", "band": "T2", "last_ts": rows[0]["ts_utc"], "rows_today": len(rows)}] if rows else [],
            "stream": rows}


def _srow(ts, yes, no):
    return {"ts_utc": ts, "sport": "NHL", "market_ticker": "K1", "market_type": "NHL_MONEYLINE", "band": "T2",
            "p_yes": 0.5, "mid": 0.5, "e_net_yes_k007": yes, "e_net_no_k007": no}


@pytest.mark.unit
def test_empty_shape_asserts_nothing():
    d = wd._decisions(NOW, {}, [], {}, {})
    assert d["rows"] == [] and d["arms"] == []
    assert [b["drawdown"] for b in d["books"]] == [None, None]
    assert all(b["awaiting"] == "portfolio" and not b["tripped"] for b in d["books"])


@pytest.mark.unit
def test_live_shape_merges_sorts_and_flags_would_fire():
    cyc = [{"ts": "2026-10-05T19:59:30Z", "ticker": "KXMLBHIT-X", "p_t4": 0.7, "mip": 0.6, "net_edge": 0.05}]
    d = wd._decisions(NOW, _shadow([_srow("2026-10-05T19:50:00Z", -0.02, 0.03)]), cyc, _port(-124.4), _port(-134.5))
    assert [r["src"] for r in d["rows"]] == ["t4_cycle", "shadow"]
    assert all(r["would_fire"] for r in d["rows"])
    assert d["rows"][1]["side"] == "NO" and d["rows"][1]["edge"] == 0.03
    b = {x["book"]: x for x in d["books"]}
    assert round(b["T1"]["drawdown"], 4) == 0.1244 and round(b["T4M-PROJ"]["drawdown"], 4) == 0.1345
    assert not b["T1"]["tripped"] and b["T1"]["age_s"] == 60.0
    assert d["sizing_live"] is False


@pytest.mark.unit
def test_stale_arm_reports_age_and_negative_edge_does_not_fire():
    d = wd._decisions(NOW, _shadow([_srow("2026-10-03T00:00:00Z", -0.01, -0.02)]), [], _port(-250.0), _port(0.0))
    assert d["rows"][0]["would_fire"] is False
    assert d["arms"][0]["age_s"] > 6 * 3600
    assert {x["book"]: x["tripped"] for x in d["books"]}["T1"] is True


@pytest.mark.unit
def test_page_has_now_module_and_truthful_labels():
    h = (ROOT / "Live Terminal.html").read_text(encoding="utf-8")
    for needle in ("STAKE", "$0 SHADOW", "WOULD-FIRE", "kill switch", "Real capital", "NOT LIVE", "no data"):
        assert needle in h, needle
    assert "--bg:#000" in h.replace(" ", "")
    assert "NOT CONNECTED" not in h
    assert h == wd._HTML


@pytest.mark.unit
def test_kill_switch_limit_resolves_without_risk_import(monkeypatch):
    def boom():
        raise ModuleNotFoundError("jsonlines")
    monkeypatch.setattr(wd, "_hard_limits", boom)
    assert wd._drawdown_limit() == 0.2
    assert wd._decisions(NOW, {}, [], _port(-250.0), _port(0.0))["books"][0]["tripped"] is True
