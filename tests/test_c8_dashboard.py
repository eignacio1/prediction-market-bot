"""
Tests for src/prediction_market_bot/c8_dashboard/dashboard.py

Coverage areas:
  - read_audit_log: missing file → []; valid JSONL → list of dicts; malformed line skipped
  - get_recent_alerts: filters to WARN/WARNING/ERROR/CRITICAL; last n only
  - get_component_last_seen: returns most recent timestamp per component
  - extract_forecast_outcomes: filters C3 forecast_emitted with p_estimate
  - render_system_health: contains kill switch state; kill active shows *** marker
  - render_drift_panel: contains Brier/ECE/edge values; alert level displayed
  - render_alert_feed: shows recent alerts; "No alerts" on empty
  - render_dashboard: combines all panels; contains timestamp header
  - main CLI: renders to stdout; --log-path; missing log returns gracefully
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from io import StringIO
from unittest.mock import patch

import pytest

_SRC = Path(__file__).parent.parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from prediction_market_bot.c8_dashboard.dashboard import (
    extract_forecast_outcomes,
    get_component_last_seen,
    get_recent_alerts,
    main,
    read_audit_log,
    render_alert_feed,
    render_dashboard,
    render_drift_panel,
    render_system_health,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_entry(
    component: str = "C3",
    event_type: str = "forecast_emitted",
    severity: str = "INFO",
    timestamp: str = "2026-05-28T10:00:00.000Z",
    payload: dict | None = None,
) -> dict:
    return {
        "timestamp": timestamp,
        "component": component,
        "event_type": event_type,
        "severity": severity,
        "payload": payload or {},
    }


def _write_jsonl(path: Path, entries: list[dict]) -> None:
    with open(path, "w") as f:
        for e in entries:
            f.write(json.dumps(e) + "\n")


def _make_health(
    ks_active: bool = False,
    alert_level: str = "OK",
    rolling_brier: float | None = None,
    rolling_ece: float | None = None,
    mean_edge: float | None = None,
    n_events: int = 0,
) -> dict:
    return {
        "kill_switch_active": ks_active,
        "kill_switch_state": "TRIGGERED" if ks_active else "ARMED",
        "kill_switch_reason": "test reason" if ks_active else None,
        "kill_switch_triggered_at": "2026-05-28T10:00:00.000Z" if ks_active else None,
        "alert_level": alert_level,
        "alert_message": None,
        "n_events_in_window": n_events,
        "rolling_brier": rolling_brier,
        "rolling_ece": rolling_ece,
        "mean_edge": mean_edge,
        "brier_baseline": 0.2416,
        "ece_baseline": 0.0247,
        "brier_l1_threshold": 0.2616,
        "brier_l2_threshold": 0.2916,
        "brier_l3_threshold": 0.3416,
        "snapshot_computed_at": "2026-05-28T10:00:00.000Z",
    }


# ---------------------------------------------------------------------------
# read_audit_log
# ---------------------------------------------------------------------------


class TestReadAuditLog:
    @pytest.mark.unit
    def test_missing_file_returns_empty(self, tmp_path):
        result = read_audit_log(tmp_path / "nonexistent.jsonl")
        assert result == []

    @pytest.mark.unit
    def test_reads_valid_jsonl(self, tmp_path):
        path = tmp_path / "audit.jsonl"
        entries = [_make_entry(), _make_entry(component="C4")]
        _write_jsonl(path, entries)
        result = read_audit_log(path)
        assert len(result) == 2
        assert result[0]["component"] == "C3"
        assert result[1]["component"] == "C4"

    @pytest.mark.unit
    def test_skips_malformed_lines(self, tmp_path):
        path = tmp_path / "audit.jsonl"
        with open(path, "w") as f:
            f.write(json.dumps(_make_entry()) + "\n")
            f.write("not json {{{\n")
            f.write(json.dumps(_make_entry(component="C6")) + "\n")
        result = read_audit_log(path)
        assert len(result) == 2

    @pytest.mark.unit
    def test_empty_file_returns_empty(self, tmp_path):
        path = tmp_path / "audit.jsonl"
        path.write_text("")
        assert read_audit_log(path) == []


# ---------------------------------------------------------------------------
# get_recent_alerts
# ---------------------------------------------------------------------------


class TestGetRecentAlerts:
    @pytest.mark.unit
    def test_filters_alert_severities(self):
        entries = [
            _make_entry(severity="INFO"),
            _make_entry(severity="WARNING"),
            _make_entry(severity="ERROR"),
            _make_entry(severity="CRITICAL"),
            _make_entry(severity="DEBUG"),
        ]
        alerts = get_recent_alerts(entries)
        assert len(alerts) == 3  # WARNING, ERROR, CRITICAL

    @pytest.mark.unit
    def test_warn_without_ing_included(self):
        entries = [_make_entry(severity="WARN")]
        alerts = get_recent_alerts(entries)
        assert len(alerts) == 1

    @pytest.mark.unit
    def test_last_n_only(self):
        entries = [
            _make_entry(severity="WARNING", timestamp=f"2026-05-28T10:0{i}:00.000Z")
            for i in range(10)
        ]
        alerts = get_recent_alerts(entries, n=5)
        assert len(alerts) == 5
        assert alerts[-1]["timestamp"] == "2026-05-28T10:09:00.000Z"

    @pytest.mark.unit
    def test_empty_returns_empty(self):
        assert get_recent_alerts([]) == []


# ---------------------------------------------------------------------------
# get_component_last_seen
# ---------------------------------------------------------------------------


class TestGetComponentLastSeen:
    @pytest.mark.unit
    def test_returns_last_timestamp_per_component(self):
        entries = [
            _make_entry("C3", timestamp="2026-05-28T10:00:00.000Z"),
            _make_entry("C3", timestamp="2026-05-28T11:00:00.000Z"),
            _make_entry("C6", timestamp="2026-05-28T09:00:00.000Z"),
        ]
        last_seen = get_component_last_seen(entries)
        assert last_seen["C3"] == "2026-05-28T11:00:00.000Z"
        assert last_seen["C6"] == "2026-05-28T09:00:00.000Z"

    @pytest.mark.unit
    def test_empty_returns_empty(self):
        assert get_component_last_seen([]) == {}


# ---------------------------------------------------------------------------
# extract_forecast_outcomes
# ---------------------------------------------------------------------------


class TestExtractForecastOutcomes:
    @pytest.mark.unit
    def test_extracts_c3_forecast_emitted(self):
        entries = [
            _make_entry("C3", "forecast_emitted", payload={"p_estimate": 0.6}),
            _make_entry("C3", "forecast_emitted", payload={"p_estimate": 0.7}),
            _make_entry("C4", "risk_eval_start", payload={}),
        ]
        result = extract_forecast_outcomes(entries)
        assert len(result) == 2

    @pytest.mark.unit
    def test_excludes_entries_without_p_estimate(self):
        entries = [
            _make_entry("C3", "forecast_emitted", payload={}),
        ]
        result = extract_forecast_outcomes(entries)
        assert len(result) == 0

    @pytest.mark.unit
    def test_last_n_only(self):
        entries = [
            _make_entry("C3", "forecast_emitted", payload={"p_estimate": 0.5 + i * 0.01})
            for i in range(40)
        ]
        result = extract_forecast_outcomes(entries, n=10)
        assert len(result) == 10


# ---------------------------------------------------------------------------
# render_system_health
# ---------------------------------------------------------------------------


class TestRenderSystemHealth:
    @pytest.mark.unit
    def test_shows_armed_when_not_active(self):
        health = _make_health(ks_active=False)
        lines = render_system_health(health, {})
        text = "\n".join(lines)
        assert "ARMED" in text

    @pytest.mark.unit
    def test_shows_kill_switch_active_marker(self):
        health = _make_health(ks_active=True)
        lines = render_system_health(health, {})
        text = "\n".join(lines)
        assert "KILL SWITCH ACTIVE" in text
        assert "test reason" in text

    @pytest.mark.unit
    def test_shows_component_activity(self):
        last_seen = {"C3": "2026-05-28T10:00:00.000Z", "C6": "2026-05-28T09:00:00.000Z"}
        lines = render_system_health(_make_health(), last_seen)
        text = "\n".join(lines)
        assert "C3" in text
        assert "C6" in text

    @pytest.mark.unit
    def test_returns_list_of_strings(self):
        lines = render_system_health(_make_health(), {})
        assert isinstance(lines, list)
        assert all(isinstance(l, str) for l in lines)


# ---------------------------------------------------------------------------
# render_drift_panel
# ---------------------------------------------------------------------------


class TestRenderDriftPanel:
    @pytest.mark.unit
    def test_shows_ok_status(self):
        health = _make_health(alert_level="OK", rolling_brier=0.21)
        lines = render_drift_panel(health)
        text = "\n".join(lines)
        assert "OK" in text

    @pytest.mark.unit
    def test_shows_brier_value(self):
        health = _make_health(rolling_brier=0.2500, n_events=10)
        lines = render_drift_panel(health)
        text = "\n".join(lines)
        assert "0.2500" in text

    @pytest.mark.unit
    def test_shows_na_when_no_events(self):
        health = _make_health()
        lines = render_drift_panel(health)
        text = "\n".join(lines)
        assert "N/A" in text

    @pytest.mark.unit
    def test_shows_alert_level_l4(self):
        health = _make_health(alert_level="L4_KILL", rolling_brier=0.39)
        lines = render_drift_panel(health)
        text = "\n".join(lines)
        assert "KILL" in text

    @pytest.mark.unit
    def test_returns_list_of_strings(self):
        lines = render_drift_panel(_make_health())
        assert isinstance(lines, list)
        assert all(isinstance(l, str) for l in lines)


# ---------------------------------------------------------------------------
# render_alert_feed
# ---------------------------------------------------------------------------


class TestRenderAlertFeed:
    @pytest.mark.unit
    def test_shows_no_alerts_on_empty(self):
        lines = render_alert_feed([])
        text = "\n".join(lines)
        assert "No alerts" in text

    @pytest.mark.unit
    def test_shows_alert_entries(self):
        alerts = [
            _make_entry("C7", "kill_switch_triggered", severity="CRITICAL"),
        ]
        lines = render_alert_feed(alerts)
        text = "\n".join(lines)
        assert "kill_switch_triggered" in text

    @pytest.mark.unit
    def test_returns_list_of_strings(self):
        lines = render_alert_feed([])
        assert isinstance(lines, list)
        assert all(isinstance(l, str) for l in lines)


# ---------------------------------------------------------------------------
# render_dashboard
# ---------------------------------------------------------------------------


class TestRenderDashboard:
    @pytest.mark.unit
    def test_returns_string(self):
        result = render_dashboard(_make_health(), [])
        assert isinstance(result, str)

    @pytest.mark.unit
    def test_contains_dashboard_header(self):
        result = render_dashboard(_make_health(), [])
        assert "C8 VISUAL DASHBOARD" in result

    @pytest.mark.unit
    def test_contains_all_three_panels(self):
        result = render_dashboard(_make_health(), [])
        assert "PANEL 1" in result
        assert "PANEL 2" in result
        assert "PANEL 3" in result

    @pytest.mark.unit
    def test_kill_switch_active_in_output(self):
        health = _make_health(ks_active=True)
        result = render_dashboard(health, [])
        assert "KILL SWITCH ACTIVE" in result


# ---------------------------------------------------------------------------
# main CLI
# ---------------------------------------------------------------------------


class TestMainCli:
    @pytest.mark.unit
    def test_main_runs_with_missing_log(self, tmp_path, capsys):
        main(["--log-path", str(tmp_path / "nonexistent.jsonl")])
        out = capsys.readouterr().out
        assert "C8 VISUAL DASHBOARD" in out

    @pytest.mark.unit
    def test_main_reads_log_file(self, tmp_path, capsys):
        path = tmp_path / "audit.jsonl"
        entries = [
            _make_entry("C7", "kill_switch_triggered", severity="CRITICAL"),
        ]
        _write_jsonl(path, entries)
        main(["--log-path", str(path)])
        out = capsys.readouterr().out
        assert "kill_switch_triggered" in out

    @pytest.mark.unit
    def test_main_infers_kill_switch_from_log(self, tmp_path, capsys):
        path = tmp_path / "audit.jsonl"
        entries = [
            {
                "timestamp": "2026-05-28T10:00:00.000Z",
                "component": "C7",
                "event_type": "kill_switch_triggered",
                "severity": "CRITICAL",
                "payload": {"reason": "daily_loss_limit_breached"},
            }
        ]
        _write_jsonl(path, entries)
        main(["--log-path", str(path)])
        out = capsys.readouterr().out
        assert "KILL SWITCH ACTIVE" in out
        assert "daily_loss_limit_breached" in out

    @pytest.mark.unit
    def test_main_reset_clears_kill_switch(self, tmp_path, capsys):
        path = tmp_path / "audit.jsonl"
        entries = [
            {
                "timestamp": "2026-05-28T10:00:00.000Z",
                "component": "C7",
                "event_type": "kill_switch_triggered",
                "severity": "CRITICAL",
                "payload": {"reason": "drift"},
            },
            {
                "timestamp": "2026-05-28T10:01:00.000Z",
                "component": "C7",
                "event_type": "kill_switch_reset",
                "severity": "WARNING",
                "payload": {},
            },
        ]
        _write_jsonl(path, entries)
        main(["--log-path", str(path)])
        out = capsys.readouterr().out
        assert "ARMED" in out
