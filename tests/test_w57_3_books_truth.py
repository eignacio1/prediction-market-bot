"""W57.3: T4M-PROJ placements on the Live Terminal, blank-row handling, stdlib C4 limits (D2/D3)."""
from __future__ import annotations

import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

_REPO = Path(__file__).parent.parent
sys.path.insert(0, str(_REPO / "scripts"))
import web_dashboard as wd  # noqa: E402

NOW = datetime(2026, 10, 6, 12, 0, tzinfo=timezone.utc)


def _pos(i, band="T4M-PROJ", size=1.0, **kw):
    return {"band": band, "entered_at": f"2026-10-06T0{i}:00:00.000Z", "kalshi_ticker": f"KXMLBHIT-T{i}",
            "player_name": f"P{i}", "direction": "YES", "entry_price_paid": 0.2, "size_usd": size, **kw}


def test_placements_newest_first_open_and_closed_recorded_stake():
    t4p = {"open_positions": [_pos(5, size=0.05)],
           "closed_positions": [_pos(2, outcome="WIN", pnl=0.5), _pos(7, band="T1"), {"band": "T4M-PROJ"}]}
    pl = wd._placements(t4p)
    assert [p["market"] for p in pl] == ["KXMLBHIT-T5", "KXMLBHIT-T2"]  # T1 and undated rows excluded
    assert pl[0]["status"] == "OPEN" and pl[0]["size_usd"] == 0.05      # recorded stake, not forced to $1
    assert pl[1]["pnl"] == 0.5 and pl[1]["label"] == wd.FLAT_STAKE_LABEL


def test_placements_limit_and_empty():
    assert wd._placements({}) == []
    t4p = {"closed_positions": [_pos(i % 9) for i in range(50)]}
    assert len(wd._placements(t4p)) == wd.PLACEMENT_ROWS


def test_decisions_drops_blank_market_rows_and_reports_count():
    cyc = [{"ts": "2026-10-06T11:00:00Z", "ticker": "", "net_edge": 0.1},
           {"ts": "2026-10-06T11:01:00Z", "ticker": "KXMLBHIT-X", "net_edge": 0.1}]
    out = wd._decisions(NOW, {}, cyc, {}, {"closed_positions": [_pos(3)]})
    assert [r["market"] for r in out["rows"]] == ["KXMLBHIT-X"]
    assert out["blank_dropped"] == 1 and len(out["placements"]) == 1


def test_hard_limits_readable_without_importing_package():
    hl = wd._hard_limits_from_source()
    assert hl["max_drawdown_pct"] == 0.20 and hl["MAX_DAILY_LOSS_PCT"] == 0.15
    assert abs(hl["max_portfolio_deployment_pct"] - 0.60) < 1e-9


def test_hard_limits_source_matches_import_and_works_under_isolated_python():
    from prediction_market_bot.c4_risk_engine.risk import _HARD_LIMITS, MAX_DAILY_LOSS_PCT
    assert wd._hard_limits_from_source() == {**_HARD_LIMITS, "MAX_DAILY_LOSS_PCT": MAX_DAILY_LOSS_PCT}
    r = subprocess.run([sys.executable, "-I", "-c",
                        "import sys; sys.path.insert(0,'scripts'); import web_dashboard as w; "
                        "print(w._hard_limits_from_source()['max_drawdown_pct'])"],
                       cwd=_REPO, capture_output=True, text=True)
    assert r.stdout.strip() == "0.2", r.stderr


def test_page_has_placements_panel_and_phone_status_wrap():
    html = wd._HTML
    assert "plWrap" in html and "T4M-PROJ placements" in html
    assert ".status{height:auto; flex-wrap:wrap" in html
