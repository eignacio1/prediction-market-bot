"""Tests for scripts/lib/governance_gap_burndown.py (T-368).

GOVERNANCE_GAP_LOG.md has no structured per-gap open/close date field, so
this module tracks OPEN/total counts via a self-maintained JSONL snapshot
history rather than parsing the log's prose. Tests exercise the pure
render/load/save functions directly against synthetic history — no git repo
or real gap log needed.
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

MODULE_PATH = Path(__file__).parent.parent / "scripts" / "lib" / "governance_gap_burndown.py"
_spec = importlib.util.spec_from_file_location("governance_gap_burndown", MODULE_PATH)
gg_burndown = importlib.util.module_from_spec(_spec)
sys.modules["governance_gap_burndown"] = gg_burndown
_spec.loader.exec_module(gg_burndown)

DAY = 86400


def test_render_summary_counts_and_percentage():
    out = gg_burndown.render_summary(open_n=15, total_n=119, history=[], now=1000.0)

    assert "15 open / 119 total (104 resolved, 12.6% open)" in out


def test_render_summary_zero_total_no_division_error():
    out = gg_burndown.render_summary(open_n=0, total_n=0, history=[], now=1000.0)

    assert "0 open / 0 total (0 resolved, 0.0% open)" in out


def test_render_summary_no_history_reports_insufficient():
    out = gg_burndown.render_summary(open_n=15, total_n=119, history=[], now=1000.0)

    assert "insufficient history yet (0 prior snapshot(s)" in out


def test_render_summary_shrinking_trend():
    now = 10 * DAY
    history = [{"ts": now - 5 * DAY, "open": 20, "total": 119}]

    out = gg_burndown.render_summary(open_n=15, total_n=119, history=history, now=now)

    assert "Burn-down: -5 over 5.0d (-1.00/day) — trend: SHRINKING" in out


def test_render_summary_growing_trend():
    now = 10 * DAY
    history = [{"ts": now - 5 * DAY, "open": 10, "total": 119}]

    out = gg_burndown.render_summary(open_n=15, total_n=119, history=history, now=now)

    assert "Burn-down: +5 over 5.0d (+1.00/day) — trend: GROWING" in out


def test_render_summary_flat_trend():
    now = 10 * DAY
    history = [{"ts": now - 5 * DAY, "open": 15, "total": 119}]

    out = gg_burndown.render_summary(open_n=15, total_n=119, history=history, now=now)

    assert "Burn-down: +0 over 5.0d (+0.00/day) — trend: FLAT" in out


def test_render_summary_ignores_history_older_than_lookback_window():
    now = 30 * DAY
    # 20 days old — outside the 14-day lookback window, must be excluded.
    history = [{"ts": now - 20 * DAY, "open": 5, "total": 119}]

    out = gg_burndown.render_summary(open_n=15, total_n=119, history=history, now=now)

    assert "insufficient history yet (1 prior snapshot(s)" in out


def test_render_summary_uses_oldest_candidate_as_baseline():
    now = 10 * DAY
    history = [
        {"ts": now - 2 * DAY, "open": 12, "total": 119},
        {"ts": now - 8 * DAY, "open": 22, "total": 119},  # oldest within window
    ]

    out = gg_burndown.render_summary(open_n=15, total_n=119, history=history, now=now)

    assert "Burn-down: -7 over 8.0d" in out


def test_load_history_missing_file_returns_empty_list(tmp_path):
    history = gg_burndown.load_history(str(tmp_path / "does_not_exist.jsonl"))

    assert history == []


def test_load_history_skips_malformed_lines(tmp_path):
    hist_path = tmp_path / "history.jsonl"
    hist_path.write_text('{"ts": 1.0, "open": 5, "total": 10}\nnot json\n\n{"ts": 2.0, "open": 4, "total": 10}\n')

    history = gg_burndown.load_history(str(hist_path))

    assert history == [{"ts": 1.0, "open": 5, "total": 10}, {"ts": 2.0, "open": 4, "total": 10}]


def test_save_history_round_trips(tmp_path):
    hist_path = tmp_path / "sub" / "history.jsonl"
    data = [{"ts": 1.0, "open": 5, "total": 10}, {"ts": 2.0, "open": 4, "total": 10}]

    gg_burndown.save_history(str(hist_path), data)
    reloaded = gg_burndown.load_history(str(hist_path))

    assert reloaded == data


def test_save_history_caps_at_200_entries(tmp_path):
    hist_path = tmp_path / "history.jsonl"
    data = [{"ts": float(i), "open": i, "total": 300} for i in range(250)]

    gg_burndown.save_history(str(hist_path), data)
    reloaded = gg_burndown.load_history(str(hist_path))

    assert len(reloaded) == 200
    assert reloaded[0]["ts"] == 50.0  # oldest 50 entries dropped
    assert reloaded[-1]["ts"] == 249.0


def test_main_appends_snapshot_and_prints_summary(tmp_path, capsys):
    hist_path = tmp_path / "history.jsonl"

    rc = gg_burndown.main(["prog", "3", "20", str(hist_path)])

    assert rc == 0
    captured = capsys.readouterr()
    assert "3 open / 20 total (17 resolved, 15.0% open)" in captured.out
    saved = [json.loads(line) for line in hist_path.read_text().splitlines()]
    assert saved == [{"ts": saved[0]["ts"], "open": 3, "total": 20}]
