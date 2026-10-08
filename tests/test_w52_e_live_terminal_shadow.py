"""W52.E (T-658): Live Terminal shadow panel shows every shadow cell, labelled truthfully.

Fixture ledgers are shaped like the real ones: data/shadow/nhl/<CELL>.jsonl (+ settled/ copies
from nhl_shadow_settle.py) and exp_output/PREGAME_SHADOW/<SPORT>_<TYPE>_<BAND>.jsonl (EXP-037).
"""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import web_dashboard as wd  # noqa: E402

NOW = datetime(2026, 10, 3, 20, 0, tzinfo=timezone.utc)
REG = {("NHL_MONEYLINE", "T3_PRE_TIP"): ("shadow", "NHL"),
       ("NHL_PUCK_LINE", "T1_MULTI_DAY"): ("shadow", "NHL"),
       ("NFL_MONEYLINE", "T2_SAME_DAY"): ("not_implemented", "NFL")}


def _row(sport, mt, band, ts, **kw):
    return {"ts_utc": ts, "sport": sport, "market_type": mt, "band": band, "market_ticker": "K",
            "p_yes": 0.5, "mid": 0.5, "e_net_yes_k007": 0.0, "e_net_no_k007": 0.0, **kw}


def _write(p: Path, rows):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("".join(json.dumps(r) + "\n" for r in rows))


def _fixture(tmp_path, monkeypatch):
    monkeypatch.setattr(wd, "_REPO_ROOT", tmp_path)
    monkeypatch.setattr(wd, "_registry_cells", lambda: REG)
    nhl = [_row("NHL", "NHL_MONEYLINE", "T3", f"2026-10-0{d}T23:00:00Z") for d in (2, 3, 3)]
    _write(tmp_path / "data/shadow/nhl/NHL_MONEYLINE_T3.jsonl", nhl)
    _write(tmp_path / "data/shadow/nhl/settled/NHL_MONEYLINE_T3.jsonl",
           [dict(nhl[0], outcome=1), dict(nhl[1], outcome=0)])
    _write(tmp_path / "exp_output/PREGAME_SHADOW/NFL_NFL_MONEYLINE_T2.jsonl",
           [_row("NFL", "NFL_MONEYLINE", "T2", "2026-10-03T12:00:00Z")])
    return {(c["market_type"], c["band"]): c for c in wd._shadow(NOW)["cells"]}, wd._shadow(NOW)


def test_settled_copies_are_not_counted_as_rows(tmp_path, monkeypatch):
    cells, sh = _fixture(tmp_path, monkeypatch)
    c = cells[("NHL_MONEYLINE", "T3")]
    assert c["rows_total"] == 3 and c["rows_today"] == 2 and c["settled_n"] == 2
    assert c["last_ts"] == "2026-10-03T23:00:00Z" and c["registry_status"] == "shadow"
    assert sum(1 for r in sh["tape"] if r["market_type"] == "NHL_MONEYLINE") == 3


def test_registry_shadow_cell_without_rows_is_listed(tmp_path, monkeypatch):
    cells, _ = _fixture(tmp_path, monkeypatch)
    c = cells[("NHL_PUCK_LINE", "T1_MULTI_DAY")]
    assert c["rows_total"] == 0 and c["registry_status"] == "shadow" and c["ledger"] == "no ledger rows found"


def test_ledger_rows_for_non_shadow_registry_cell_shown_as_such(tmp_path, monkeypatch):
    cells, _ = _fixture(tmp_path, monkeypatch)
    c = cells[("NFL_MONEYLINE", "T2")]
    assert c["registry_status"] == "not_implemented" and c["rows_total"] == 1


def test_unregistered_ledger_cell_labelled(tmp_path, monkeypatch):
    monkeypatch.setattr(wd, "_REPO_ROOT", tmp_path)
    monkeypatch.setattr(wd, "_registry_cells", lambda: {})
    _write(tmp_path / "exp_output/PREGAME_SHADOW/MLB_MLB_MONEYLINE_T1.jsonl",
           [_row("MLB", "MLB_MONEYLINE", "T1", "2026-10-03T12:00:00Z")])
    assert wd._shadow(NOW)["cells"][0]["registry_status"] == "unregistered"


def test_real_registry_shadow_cells_all_appear(tmp_path, monkeypatch):
    monkeypatch.setattr(wd, "_REPO_ROOT", tmp_path)          # no ledgers at all
    reg = wd._registry_cells()
    assert reg, "registry must be readable"
    want = {k for k, (st, _) in reg.items() if st == "shadow"}
    got = {(c["market_type"], c["band"]) for c in wd._shadow(NOW)["cells"]}
    assert want and want <= got
    nhl = {k for k in want if k[0].startswith("NHL_")}
    assert len(nhl) == 9                                      # 52.A flip


def test_frozen_label_shows_true_age():
    assert wd._frozen_label("2026-08-06T00:05:01Z", NOW) == "FROZEN (last write 2026-08-06, 58d ago)"


def test_page_labels_registry_status_and_frozen_age():
    src = (Path(wd.__file__).resolve().parents[1] / "Live Terminal.html").read_text()
    assert "<th>REGISTRY</th>" in src and "(ledger only)" in src and "<th>ROWS TOTAL</th>" in src
    assert "d ago)" in src


def test_settled_count_accepts_y_rows_from_nfl_and_mlb(tmp_path, monkeypatch):
    """W59.2 Part C (GG-499): NFL/MLB settled rows carry `y`, NHL carries `outcome`; all three count. y=0.0 and 0.5 are settled."""
    monkeypatch.setattr(wd, "_REPO_ROOT", tmp_path)
    reg = {("NFL_MONEYLINE", "T2_SAME_DAY"): ("shadow", "NFL"), ("MLB_MONEYLINE", "T1_MULTI_DAY"): ("shadow", "MLB")}
    monkeypatch.setattr(wd, "_registry_cells", lambda: reg)
    nfl = [_row("NFL", "NFL_MONEYLINE", "T2", "2026-10-03T12:00:00Z") for _ in range(4)]
    mlb = [_row("MLB", "MLB_MONEYLINE", "T1", "2026-10-03T12:00:00Z") for _ in range(3)]
    _write(tmp_path / "exp_output/PREGAME_SHADOW/NFL_NFL_MONEYLINE_T2.jsonl", nfl)
    _write(tmp_path / "exp_output/PREGAME_SHADOW/MLB_MLB_MONEYLINE_T1.jsonl", mlb)
    _write(tmp_path / "exp_output/PREGAME_SHADOW/settled/NFL_NFL_MONEYLINE_T2.jsonl",
           [dict(nfl[0], y=1.0), dict(nfl[1], y=0.0), dict(nfl[2], y=0.5), dict(nfl[3], y=None)])
    _write(tmp_path / "exp_output/PREGAME_SHADOW/settled/MLB_MLB_MONEYLINE_T1.jsonl", [dict(mlb[0], y=0.0), dict(mlb[1], y=1.0)])
    cells = {(c["market_type"], c["band"]): c for c in wd._shadow(NOW)["cells"]}
    assert cells[("NFL_MONEYLINE", "T2")]["settled_n"] == 3        # the unsettled (y=None) row is not counted
    assert cells[("MLB_MONEYLINE", "T1")]["settled_n"] == 2
    assert cells[("NFL_MONEYLINE", "T2")]["rows_total"] == 4        # settled copies still never counted as rows
