"""W118.4 / B-102 Part A + C: disk_guard growth and days-to-90%, scripts/disk_read.py, the allowlisted disk_read task, healthcheck WARN."""
from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
from prediction_market_bot import disk_guard as dg  # noqa: E402


def _load(name, rel):
    spec = importlib.util.spec_from_file_location(name, REPO / rel)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


NOW = datetime(2026, 11, 18, 17, 0, tzinfo=timezone.utc)


def _health(days_pcts):
    out = []
    for d, p in days_pcts:
        ts = (NOW - timedelta(days=d)).strftime("%Y-%m-%dT%H:%M:%SZ")
        out.append("=== VPS Health Check (W72.3) ===\n%s\n\n[OK] python\n[OK] disk %d%% used\n=== HEALTHY ===\n" % (ts, p))
    return "".join(out)


def test_parse_health_log_pairs_date_with_disk_line():
    s = dg.parse_health_log(_health([(3, 80), (2, 82), (1, 85)]))
    assert [p for _, p, _ in s] == [80.0, 82.0, 85.0]
    assert s[0][0] == NOW - timedelta(days=3)


def test_parse_health_log_ignores_garbage_and_lines_before_a_header():
    s = dg.parse_health_log("[OK] disk 50% used\nnoise\n" + _health([(1, 70)]))
    assert [p for _, p, _ in s] == [70.0]


def test_growth_and_days_to_90():
    s = dg.parse_health_log(_health([(6, 70), (4, 76), (2, 82), (0, 88)]))
    g = dg.growth(s, NOW)
    assert g["pct_per_day"] == pytest.approx(3.0)
    assert dg.days_to(90, 88, g["pct_per_day"]) == pytest.approx(2 / 3)


def test_growth_needs_a_day_of_history_and_two_samples():
    assert dg.growth(dg.parse_health_log(_health([(0, 70)])), NOW) is None
    assert dg.growth([(NOW - timedelta(hours=5), 70.0, None), (NOW, 71.0, None)], NOW) is None


def test_days_to_edge_cases():
    assert dg.days_to(90, 90, 1.0) == 0.0 and dg.days_to(90, 95, None) == 0.0
    assert dg.days_to(90, 80, 0.0) is None and dg.days_to(90, 80, -1.0) is None and dg.days_to(90, 80, None) is None


def test_window_is_seven_days():
    s = dg.parse_health_log(_health([(20, 10), (6, 70), (0, 80)]))   # the 20-day-old point must not bend the 7-day slope
    assert dg.growth(s, NOW)["pct_per_day"] == pytest.approx(10 / 6)


def _proj(tmp_path, health=None, samples=None):
    (tmp_path / "logs").mkdir(exist_ok=True)
    if health is not None:
        (tmp_path / "logs/health.log").write_text(health)
    if samples is not None:
        (tmp_path / "logs/disk_samples.jsonl").write_text("".join(json.dumps(r) + "\n" for r in samples))
    return tmp_path


def _usage(pct):
    return {"used_bytes": int(pct * 1e9), "total_bytes": int(100e9), "avail_bytes": int((100 - pct) * 1e9), "pct": float(pct)}


def test_assess_warns_when_90_is_within_14_days(tmp_path):
    p = _proj(tmp_path, health=_health([(6, 70), (0, 82)]))                 # 2 pct/day, 4 days to go
    a = dg.assess(p, NOW, _usage(82))
    assert a["warn"] and a["days_to_90"] == pytest.approx(4.0)
    assert dg.render(a).startswith("WARN: ") and "4.0 days" in dg.render(a)


def test_assess_does_not_warn_when_far_flat_or_unknown(tmp_path):
    far = dg.assess(_proj(tmp_path, health=_health([(6, 50), (0, 52)])), NOW, _usage(52))      # 0.33/day, 114 days
    assert not far["warn"] and dg.render(far).startswith("OK: ")
    flat = dg.assess(_proj(tmp_path, health=_health([(6, 60), (0, 60)])), NOW, _usage(60))
    assert not flat["warn"] and "flat or shrinking" in dg.render(flat)
    none = dg.assess(tmp_path / "empty_proj_does_not_exist", NOW, _usage(60))
    assert not none["warn"] and "not enough history" in dg.render(none)


def test_assess_at_or_past_90_is_not_a_warn(tmp_path):
    a = dg.assess(_proj(tmp_path, health=_health([(6, 80), (0, 92)])), NOW, _usage(92))
    assert not a["warn"] and "FAIL line" in dg.render(a)


def test_samples_beat_health_log_and_carry_bytes(tmp_path):
    t = lambda d: (NOW - timedelta(days=d)).strftime("%Y-%m-%dT%H:%M:%SZ")  # noqa: E731
    p = _proj(tmp_path, health=_health([(6, 10), (0, 11)]),
              samples=[{"ts": t(4), "pct": 70, "used_bytes": 70_000_000_000}, {"ts": t(0), "pct": 78, "used_bytes": 78_000_000_000}])
    a = dg.assess(p, NOW, _usage(78))
    assert a["source"] == "disk_samples" and a["pct_per_day"] == pytest.approx(2.0)
    assert a["growth"]["bytes_per_day"] == pytest.approx(2e9)


def test_record_appends_one_row_and_main_prints(tmp_path, capsys):
    _proj(tmp_path)
    os.environ["PMBOT_DISK_FAKE_PCT"] = "61"
    try:
        assert dg.main([str(tmp_path), "--record"]) == 0
    finally:
        del os.environ["PMBOT_DISK_FAKE_PCT"]
    assert capsys.readouterr().out.startswith("OK: disk 61% used")
    row = json.loads((tmp_path / "logs/disk_samples.jsonl").read_text())
    assert row["pct"] == 61.0 and row["ts"].endswith("Z")


def test_current_usage_is_a_real_percentage():
    u = dg.current_usage(REPO)
    assert 0 <= u["pct"] <= 100 and u["total_bytes"] > 0


# ---- disk_read -------------------------------------------------------------------------------------------------

dr = _load("disk_read", "scripts/disk_read.py")


def test_disk_read_reports_every_section_and_changes_nothing(tmp_path):
    (tmp_path / "logs").mkdir()
    (tmp_path / "exp_output/A").mkdir(parents=True)
    (tmp_path / "logs/big.jsonl").write_bytes(b"x" * 50_000)
    (tmp_path / "logs/old.log.gz").write_bytes(b"y" * 1000)
    (tmp_path / "exp_output/A/snap.json").write_bytes(b"z" * 20_000)
    (tmp_path / "logs/health.log").write_text(_health([(6, 70), (0, 76)]))
    before = sorted((str(p), p.stat().st_size, p.stat().st_mtime_ns) for p in tmp_path.rglob("*") if p.is_file())
    out = dr.report(tmp_path, NOW)
    after = sorted((str(p), p.stat().st_size, p.stat().st_mtime_ns) for p in tmp_path.rglob("*") if p.is_file())
    assert before == after
    for needle in ("## df -h", "25 largest directories", "## logs/ total", "## exp_output/ total", "## journald / system",
                   "growth and days to 90%", "logs/big.jsonl", "exp_output/A/snap.json"):
        assert needle in out, needle
    assert "jsonl 48.8 KB" in out and "gz 1000 B" in out


def test_top_directories_are_sorted_and_exclude_root(tmp_path):
    (tmp_path / "a").mkdir(); (tmp_path / "b/c").mkdir(parents=True)
    (tmp_path / "a/f").write_bytes(b"1" * 10_000); (tmp_path / "b/c/f").write_bytes(b"1" * 300_000)
    rows = dr.du_dirs(tmp_path)
    assert rows[0][1].endswith("/b") or rows[0][1].endswith("b/c")
    assert all(Path(p) != tmp_path for _, p in rows) and [b for b, _ in rows] == sorted((b for b, _ in rows), reverse=True)


def test_disk_read_script_runs_standalone(tmp_path):
    r = subprocess.run([sys.executable, str(REPO / "scripts/disk_read.py"), "--root", str(tmp_path)], capture_output=True, text=True)
    assert r.returncode == 0 and "# disk_read" in r.stdout


def test_task_is_allowlisted_and_read_only():
    bt = _load("box_tasks", "scripts/box_tasks.py")
    c = bt.TASKS["disk_read"]
    assert c.endswith("scripts/disk_read.py") and ">" not in c.replace("2>&1", "")

