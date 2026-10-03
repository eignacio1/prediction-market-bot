"""T-621 / Wave 48.3 — defects found by the real-browser check."""
import json, sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import web_dashboard as wd
import generate_project_state as gps

NOW = datetime(2026, 10, 3, 0, 15, tzinfo=timezone.utc)


def test_shadow_reads_data_shadow_sport_dirs(tmp_path, monkeypatch):
    """NHL writes data/shadow/nhl/<CELL>.jsonl; the module must not read AWAITING over live rows."""
    monkeypatch.setattr(wd, "_REPO_ROOT", tmp_path)
    d = tmp_path / "data" / "shadow" / "nhl"; d.mkdir(parents=True)
    row = {"sport": "NHL", "market_type": "NHL_MONEYLINE", "band": "T3", "market_ticker": "K-1",
           "ts_utc": "2026-10-03T00:10:04+00:00", "p_yes": 0.58, "mid": 0.63, "e_net_yes_k007": -0.07}
    (d / "NHL_MONEYLINE_T3.jsonl").write_text(json.dumps(row) + "\n")
    s = wd._shadow(NOW)
    assert "awaiting" not in s
    assert s["cells"][0]["sport"] == "NHL" and s["cells"][0]["rows_today"] == 1


def test_project_page_strips_markdown_emphasis():
    state = {"generated": "t", "sections": {"queue": {"source": "q", "as_of": "x", "waves": [{"line": "Wave **9** done"}],
                       "needs_decision": [{"item": "Item", "plain": "Residual risks **L1** are yours."}]}}}
    html = gps.render_html(state)
    assert "**" not in html and "Residual risks L1 are yours." in html
