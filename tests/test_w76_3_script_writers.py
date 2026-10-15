"""W76.3 (GG-748): ledger-rewriting scripts write atomically and hold the PaperTrader flock."""
import importlib.util
import json
import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent


def _load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / f"{name}.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def _ledger(tmp_path):
    p = tmp_path / "paper_portfolio_mlb_t4.json"
    p.write_text(json.dumps({
        "open_positions": [{"kalshi_ticker": "KXMLBHIT-26OCT011905X-Y", "game_date": "2026-10-02"}],
        "closed_positions": [],
    }))
    return p


def test_correct_t4_game_dates_apply_is_atomic_and_locked(tmp_path, monkeypatch):
    m = _load("correct_t4_game_dates")
    p = _ledger(tmp_path)
    monkeypatch.setattr(sys, "argv", ["x", "--apply", "--ledger", str(p)])
    assert m.main() == 0
    assert json.loads(p.read_text())["open_positions"][0]["game_date"] == "2026-10-01"
    assert (tmp_path / "paper_portfolio_mlb_t4.json.lock").exists()           # took the PaperTrader lock
    assert not [f for f in tmp_path.iterdir() if f.name.endswith(".tmp")]      # no stray tmp


def test_correct_t4_game_dates_crash_before_rename_leaves_ledger_intact(tmp_path, monkeypatch):
    m = _load("correct_t4_game_dates")
    p = _ledger(tmp_path)
    before = p.read_text()

    def boom(a, b):
        raise OSError("crash")

    monkeypatch.setattr(os, "replace", boom)
    monkeypatch.setattr(sys, "argv", ["x", "--apply", "--ledger", str(p)])
    with pytest.raises(OSError):
        m.main()
    assert p.read_text() == before


def test_no_script_rewrites_a_live_ledger_with_plain_open_w():
    """Pattern guard: the GG-748 scripts must not regress to non-atomic writes."""
    for n in ("correct_t4_game_dates", "gg271_bound_t4_rejected_positions", "replay_harness_t427",
              "tag_locked_pairs_t4_mlb", "t437_task3_rederive_outcomes"):
        src = (ROOT / "scripts" / f"{n}.py").read_text()
        assert "atomic_io" in src, n
        assert 'open("w")' not in src.replace(" ", "") and ".write_text(json.dumps(" not in src, n
