"""Tests for scripts/cron_log_aggregator.py — T-300 (A4), ADR-0041.

The production path runs `REMOTE_SCRIPT` on the VPS over ssh, so there is no
network-free way to test `main()` end-to-end. Instead these tests execute the
exact same `REMOTE_SCRIPT` string as a local subprocess (`python3 -`) against
synthetic fixture files in a tmp dir (passed as argv[2], the same override
hook a real ssh invocation never uses) — this exercises the real parsing and
aggregation logic with no mocking of the logic under test.
"""
from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

import cron_log_aggregator as cla

TODAY = datetime.now(timezone.utc).date()
D0 = str(TODAY)
D1 = str(TODAY - timedelta(days=1))
OLD = str(TODAY - timedelta(days=10))  # outside any --days window used below


def _run(tmp_path: Path, days: int = 3) -> str:
    result = subprocess.run(
        [sys.executable, "-", str(days), str(tmp_path)],
        input=cla.REMOTE_SCRIPT,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, result.stderr
    return result.stdout


def _write_jsonl(path: Path, records: list[dict]) -> None:
    with path.open("w") as fh:
        for r in records:
            fh.write(json.dumps(r) + "\n")


def _seed_empty_fixtures(tmp_path: Path) -> None:
    """Every source file must exist — an empty run should not crash."""
    for name in (
        "t4_mlb_cycle_log.jsonl",
        "audit_mlb_t4_edge_decisions.jsonl",
        "audit_mlb_t4.jsonl",
        "paper_mlb_cron.log",
    ):
        (tmp_path / name).write_text("")


def test_empty_fixtures_do_not_crash(tmp_path):
    _seed_empty_fixtures(tmp_path)
    out = _run(tmp_path)
    assert "T4 MLB" in out
    assert "T1 MLB" in out


def test_rows_and_games_per_day(tmp_path):
    _seed_empty_fixtures(tmp_path)
    rows = [
        {"game_date": D0, "ticker": "KXMLBHIT-26JULGAMEA-PLAYERX-1"},
        {"game_date": D0, "ticker": "KXMLBHIT-26JULGAMEA-PLAYERY-2"},
        {"game_date": D0, "ticker": "KXMLBHIT-26JULGAMEB-PLAYERZ-1"},
        {"game_date": OLD, "ticker": "KXMLBHIT-26JULGAMEC-PLAYERW-1"},  # outside window
    ]
    _write_jsonl(tmp_path / "t4_mlb_cycle_log.jsonl", rows)
    out = _run(tmp_path, days=3)
    line = [l for l in out.splitlines() if l.strip().startswith(D0 + ":")][0]
    assert "rows=3" in line
    assert "games=2" in line  # GAMEA, GAMEB distinct; OLD day excluded entirely
    # A plain substring check on OLD is unsafe: the script's footnote text cites
    # historical GG-080 dates (e.g. 2026-07-02/03) that can coincidentally equal
    # OLD depending on when the test runs. Check the per-day breakdown line only.
    assert not any(l.strip().startswith(OLD + ":") for l in out.splitlines())


def test_fire_rate_and_decision_counts(tmp_path):
    _seed_empty_fixtures(tmp_path)
    decisions = (
        [{"timestamp": f"{D0}T01:00:00Z", "payload": {"decision": "APPROVED"}}] * 2
        + [{"timestamp": f"{D0}T02:00:00Z", "payload": {"decision": "REJECTED:insufficient_edge"}}] * 8
    )
    _write_jsonl(tmp_path / "audit_mlb_t4_edge_decisions.jsonl", decisions)
    out = _run(tmp_path)
    line = [l for l in out.splitlines() if l.strip().startswith(D0 + ":")][0]
    assert "fires=2" in line
    assert "decisions=10" in line
    assert "fire_rate=20.00%" in line


def test_contamination_halt_count_per_day(tmp_path):
    _seed_empty_fixtures(tmp_path)
    halts = [
        {"timestamp": f"{D0}T03:00:00Z", "event_type": "CONTAMINATION_HALT",
         "payload": {"failed_checks": ["game_state_fresh"]}},
        {"timestamp": f"{D0}T03:01:00Z", "event_type": "CONTAMINATION_HALT",
         "payload": {"failed_checks": ["game_state_fresh"]}},
        {"timestamp": f"{D1}T03:00:00Z", "event_type": "CONTAMINATION_HALT",
         "payload": {"failed_checks": ["game_state_fresh"]}},
        {"timestamp": f"{D0}T03:02:00Z", "event_type": "edge_decision", "payload": {}},
    ]
    _write_jsonl(tmp_path / "audit_mlb_t4.jsonl", halts)
    out = _run(tmp_path)
    d0_line = [l for l in out.splitlines() if l.strip().startswith(D0 + ":")][0]
    d1_line = [l for l in out.splitlines() if l.strip().startswith(D1 + ":")][0]
    assert "contamination_halts=2" in d0_line
    assert "contamination_halts=1" in d1_line


def test_recency_window_alarm_triggers_on_recent_staleness(tmp_path):
    _seed_empty_fixtures(tmp_path)
    # 501 healthy records, then 1 stale record at the tail -> inside the last-500 window.
    healthy = [
        {"timestamp": f"{D0}T00:00:00Z", "event_type": "edge_decision", "payload": {}}
        for _ in range(501)
    ]
    stale = [{"timestamp": f"{D0}T00:00:01Z", "event_type": "CONTAMINATION_HALT",
              "payload": {"failed_checks": ["game_state_fresh"], "staleness_halts": 1}}]
    _write_jsonl(tmp_path / "audit_mlb_t4.jsonl", healthy + stale)
    out = _run(tmp_path)
    assert "game_state_fresh failures = 1 (ALARM" in out


def test_recency_window_healthy_when_staleness_outside_window(tmp_path):
    _seed_empty_fixtures(tmp_path)
    # Stale record buried further back than the last 500 -> should NOT alarm.
    stale = [{"timestamp": f"{D0}T00:00:00Z", "event_type": "CONTAMINATION_HALT",
              "payload": {"failed_checks": ["game_state_fresh"], "staleness_halts": 1}}]
    healthy = [
        {"timestamp": f"{D0}T00:00:01Z", "event_type": "edge_decision", "payload": {}}
        for _ in range(600)
    ]
    _write_jsonl(tmp_path / "audit_mlb_t4.jsonl", stale + healthy)
    out = _run(tmp_path)
    assert "game_state_fresh failures = 0 (healthy)" in out


def test_t1_run_parsing_and_semantic_floor_violation(tmp_path):
    _seed_empty_fixtures(tmp_path)
    compact = D0.replace("-", "")
    log_lines = [
        f"[PIPE-05] MLB Paper trading — {compact}",
        "[PIPE-05] No MLB games in progress on " + D0 + " — proceeding",
        "  12 players in live MLB markets | 40 market/threshold pairs",
        "  Bets placed today:  5",
    ]
    (tmp_path / "paper_mlb_cron.log").write_text("\n".join(log_lines) + "\n")
    out = _run(tmp_path)
    line = [l for l in out.splitlines() if l.strip().startswith(D0 + ":")][-1]
    assert "runs=1" in line
    assert "total_players_matched=12" in line
    assert "total_bets=5" in line
    assert "SemanticFloorViolation count (whole file, not date-filtered): 0 (healthy)" in out


def test_semantic_floor_violation_detected(tmp_path):
    _seed_empty_fixtures(tmp_path)
    (tmp_path / "paper_mlb_cron.log").write_text("ERROR: SemanticFloorViolation: ticker/name pipeline dead\n")
    out = _run(tmp_path)
    assert "SemanticFloorViolation count (whole file, not date-filtered): 1 (ALARM" in out


def test_contamination_guard_abort_counted(tmp_path):
    _seed_empty_fixtures(tmp_path)
    compact = D0.replace("-", "")
    log_lines = [
        f"[PIPE-05] MLB Paper trading — {compact}",
        "[PIPE-05] MLB game(s) in progress on " + D0 + " — aborting bet placement (live market contamination guard)",
    ]
    (tmp_path / "paper_mlb_cron.log").write_text("\n".join(log_lines) + "\n")
    out = _run(tmp_path)
    assert "contamination_guard_aborts=1" in out


def test_days_window_excludes_old_dates(tmp_path):
    _seed_empty_fixtures(tmp_path)
    rows = [{"game_date": OLD, "ticker": "KXMLBHIT-26JULGAMEA-PLAYERX-1"}]
    _write_jsonl(tmp_path / "t4_mlb_cycle_log.jsonl", rows)
    out = _run(tmp_path, days=3)
    # See test_rows_and_games_per_day for why this checks the per-day line
    # rather than a blind substring — OLD can coincidentally match unrelated
    # historical dates in the script's own footnote text.
    assert not any(l.strip().startswith(OLD + ":") for l in out.splitlines())
