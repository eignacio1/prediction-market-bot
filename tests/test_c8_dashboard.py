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
    compute_t4_contamination_stats,
    compute_t4_funnel_stats,
    compute_t4_reentry_stats,
    extract_forecast_outcomes,
    get_component_last_seen,
    get_pipeline_timestamps,
    get_recent_alerts,
    main,
    read_audit_log,
    read_jsonl_generic,
    read_portfolio,
    render_alert_feed,
    render_dashboard,
    render_drift_panel,
    render_portfolio_panel,
    render_system_health,
    render_t4_detail_panel,
    render_t4_subband_registry,
    render_throughput_panel,
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


def _make_portfolio(
    bankroll: float = 958.99,
    initial: float = 1000.0,
    pnl: float = 75.67,
    open_positions: list | None = None,
    closed_positions: list | None = None,
) -> dict:
    return {
        "bankroll_usd": bankroll,
        "initial_bankroll_usd": initial,
        "total_realized_pnl": pnl,
        "current_daily_loss": 0.0,
        "open_positions": open_positions or [],
        "closed_positions": closed_positions or [],
        "last_updated": "2026-06-08T20:00:00Z",
    }


def _make_position(
    player: str = "Test Player",
    size: float = 10.0,
    game_date: str = "2026-06-08",
    status: str = "OPEN",
    t3_signal: str = "NEUTRAL",
    outcome: str | None = None,
    pnl: float = 0.0,
) -> dict:
    pos: dict = {
        "position_id": "POS-TEST",
        "player_name": player,
        "kalshi_ticker": "KXNBAPTS-TEST",
        "kalshi_threshold": 20,
        "direction": "NO",
        "size_usd": size,
        "game_date": game_date,
        "entered_at": "2026-06-08T22:00:00Z",
        "status": status,
        "model_p": 0.05,
        "gross_edge": 0.10,
        "fee_net_edge": 0.09,
        "t3_signal": t3_signal,
        "t1_edge": 0.09,
    }
    if outcome is not None:
        pos["outcome"] = outcome
        pos["pnl"] = pnl
        pos["resolved_at"] = "2026-06-09T06:00:00Z"
    return pos


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

    @pytest.mark.unit
    def test_main_accepts_portfolio_path(self, tmp_path, capsys):
        log = tmp_path / "audit.jsonl"
        log.write_text("")
        port = tmp_path / "portfolio.json"
        port.write_text(
            '{"bankroll_usd": 500.0, "initial_bankroll_usd": 1000.0, '
            '"total_realized_pnl": -50.0, "open_positions": [], "closed_positions": []}'
        )
        main([
            "--log-path", str(log),
            "--portfolio-path", str(port),
            "--t4-portfolio-path", str(tmp_path / "no_t4.json"),
            "--log-dir", str(tmp_path),
        ])
        out = capsys.readouterr().out
        assert "500.00" in out

    @pytest.mark.unit
    def test_main_game_date_arg(self, tmp_path, capsys):
        log = tmp_path / "audit.jsonl"
        log.write_text("")
        main([
            "--log-path", str(log),
            "--log-dir", str(tmp_path),
            "--game-date", "2026-06-08",
        ])
        out = capsys.readouterr().out
        assert "2026-06-08" in out


# ---------------------------------------------------------------------------
# read_portfolio
# ---------------------------------------------------------------------------


class TestReadPortfolio:
    @pytest.mark.unit
    def test_missing_path_returns_empty(self, tmp_path):
        assert read_portfolio(tmp_path / "none.json") == {}

    @pytest.mark.unit
    def test_none_path_returns_empty(self):
        assert read_portfolio(None) == {}

    @pytest.mark.unit
    def test_valid_json_returned(self, tmp_path):
        p = tmp_path / "portfolio.json"
        p.write_text('{"bankroll_usd": 500.0}')
        result = read_portfolio(p)
        assert result["bankroll_usd"] == 500.0

    @pytest.mark.unit
    def test_malformed_json_returns_empty(self, tmp_path):
        p = tmp_path / "portfolio.json"
        p.write_text("{broken")
        assert read_portfolio(p) == {}


# ---------------------------------------------------------------------------
# get_pipeline_timestamps
# ---------------------------------------------------------------------------


class TestGetPipelineTimestamps:
    @pytest.mark.unit
    def test_empty_dir_returns_empty(self, tmp_path):
        result = get_pipeline_timestamps(tmp_path)
        assert result == {}

    @pytest.mark.unit
    def test_detects_pipe03_log(self, tmp_path):
        (tmp_path / "paper_early_cron.log").write_text("some output")
        result = get_pipeline_timestamps(tmp_path)
        assert "PIPE-03" in result

    @pytest.mark.unit
    def test_picks_newer_of_two_logs(self, tmp_path):
        import time
        (tmp_path / "paper_early_cron.log").write_text("early")
        time.sleep(0.05)
        (tmp_path / "paper_late_cron.log").write_text("late")
        result = get_pipeline_timestamps(tmp_path)
        assert "PIPE-03" in result

    @pytest.mark.unit
    def test_returns_utc_string_format(self, tmp_path):
        (tmp_path / "pregame_cron.log").write_text("x")
        result = get_pipeline_timestamps(tmp_path)
        ts = result.get("PIPE-02", "")
        assert "T" in ts and "Z" in ts


# ---------------------------------------------------------------------------
# render_portfolio_panel
# ---------------------------------------------------------------------------


class TestRenderPortfolioPanel:
    @pytest.mark.unit
    def test_shows_not_found_when_empty(self):
        lines = render_portfolio_panel({}, {})
        text = "\n".join(lines)
        assert "not found" in text

    @pytest.mark.unit
    def test_shows_bankroll(self):
        port = _make_portfolio(bankroll=958.99)
        lines = render_portfolio_panel(port, {})
        text = "\n".join(lines)
        assert "958.99" in text

    @pytest.mark.unit
    def test_shows_pnl(self):
        port = _make_portfolio(pnl=75.67)
        lines = render_portfolio_panel(port, {})
        text = "\n".join(lines)
        assert "75.67" in text

    @pytest.mark.unit
    def test_shows_win_rate_from_closed(self):
        closed = [
            _make_position(status="CLOSED", outcome="WIN"),
            _make_position(status="CLOSED", outcome="LOSS"),
        ]
        port = _make_portfolio(closed_positions=closed)
        lines = render_portfolio_panel(port, {})
        text = "\n".join(lines)
        assert "50.0%" in text

    @pytest.mark.unit
    def test_t4_no_portfolio_shown(self):
        lines = render_portfolio_panel({}, {})
        text = "\n".join(lines)
        assert "T4" in text
        assert "no portfolio" in text

    @pytest.mark.unit
    def test_t4_portfolio_stats_shown(self):
        t4 = _make_portfolio(bankroll=500.0, pnl=10.0)
        lines = render_portfolio_panel({}, t4)
        text = "\n".join(lines)
        assert "T4" in text

    @pytest.mark.unit
    def test_returns_list_of_strings(self):
        lines = render_portfolio_panel({}, {})
        assert isinstance(lines, list)
        assert all(isinstance(l, str) for l in lines)

    @pytest.mark.unit
    def test_panel_1_label_in_output(self):
        lines = render_portfolio_panel({}, {})
        text = "\n".join(lines)
        assert "PANEL 1" in text


# ---------------------------------------------------------------------------
# render_throughput_panel
# ---------------------------------------------------------------------------


class TestRenderThroughputPanel:
    @pytest.mark.unit
    def test_shows_game_date(self):
        lines = render_throughput_panel({}, {}, "2026-06-08")
        text = "\n".join(lines)
        assert "2026-06-08" in text

    @pytest.mark.unit
    def test_no_portfolio_shows_no_portfolio(self):
        lines = render_throughput_panel({}, {}, "2026-06-08")
        text = "\n".join(lines)
        assert "no portfolio" in text

    @pytest.mark.unit
    def test_counts_t1_positions_for_date(self):
        pos = [_make_position(game_date="2026-06-08", size=15.0)]
        port = _make_portfolio(open_positions=pos)
        lines = render_throughput_panel(port, {}, "2026-06-08")
        text = "\n".join(lines)
        assert "T1" in text
        assert "1 bet" in text

    @pytest.mark.unit
    def test_excludes_positions_on_other_date(self):
        pos = [_make_position(game_date="2026-06-07", size=15.0)]
        port = _make_portfolio(open_positions=pos)
        lines = render_throughput_panel(port, {}, "2026-06-08")
        text = "\n".join(lines)
        assert "0 position" in text or "no position" in text.lower()

    @pytest.mark.unit
    def test_shows_t3_signal_breakdown(self):
        pos = [
            _make_position(game_date="2026-06-08", t3_signal="CONFIRM"),
            _make_position(game_date="2026-06-08", t3_signal="NEUTRAL"),
            _make_position(game_date="2026-06-08", t3_signal="NEUTRAL"),
        ]
        port = _make_portfolio(open_positions=pos)
        lines = render_throughput_panel(port, {}, "2026-06-08")
        text = "\n".join(lines)
        assert "CONFIRM" in text
        assert "NEUTRAL" in text

    @pytest.mark.unit
    def test_t4_large_volume_aggregated(self):
        """~1000 T4 positions must aggregate, not list individually."""
        positions = [
            _make_position(player=f"Player {i % 10}", game_date="2026-06-08")
            for i in range(500)
        ]
        t4 = _make_portfolio(open_positions=positions)
        lines = render_throughput_panel({}, t4, "2026-06-08")
        text = "\n".join(lines)
        assert "500" in text
        assert len(lines) < 30

    @pytest.mark.unit
    def test_t4_resolved_shows_win_rate(self):
        closed = [
            _make_position(
                game_date="2026-06-08",
                status="CLOSED",
                outcome="WIN",
                pnl=5.0,
            ),
            _make_position(
                game_date="2026-06-08",
                status="CLOSED",
                outcome="LOSS",
                pnl=-5.0,
            ),
        ]
        t4 = _make_portfolio(closed_positions=closed)
        lines = render_throughput_panel({}, t4, "2026-06-08")
        text = "\n".join(lines)
        assert "50.0%" in text

    @pytest.mark.unit
    def test_returns_list_of_strings(self):
        lines = render_throughput_panel({}, {}, "2026-06-08")
        assert isinstance(lines, list)
        assert all(isinstance(l, str) for l in lines)

    @pytest.mark.unit
    def test_panel_2_label_in_output(self):
        lines = render_throughput_panel({}, {}, "2026-06-08")
        text = "\n".join(lines)
        assert "PANEL 2" in text


# ---------------------------------------------------------------------------
# render_alert_feed — deduplication
# ---------------------------------------------------------------------------


class TestRenderAlertFeedDedup:
    @pytest.mark.unit
    def test_deduplicates_consecutive_same_type(self):
        alerts = [
            _make_entry("C1", "player_game_log_empty", severity="WARNING")
            for _ in range(10)
        ]
        lines = render_alert_feed(alerts)
        text = "\n".join(lines)
        assert "×10" in text

    @pytest.mark.unit
    def test_does_not_collapse_different_types(self):
        alerts = [
            _make_entry("C1", "event_a", severity="WARNING"),
            _make_entry("C1", "event_b", severity="WARNING"),
        ]
        lines = render_alert_feed(alerts)
        text = "\n".join(lines)
        assert "event_a" in text
        assert "event_b" in text

    @pytest.mark.unit
    def test_panel_5_label(self):
        lines = render_alert_feed([])
        text = "\n".join(lines)
        assert "PANEL 5" in text


# ---------------------------------------------------------------------------
# render_system_health — pipeline timestamps
# ---------------------------------------------------------------------------


class TestRenderSystemHealthPipeline:
    @pytest.mark.unit
    def test_shows_pipeline_timestamps_when_provided(self):
        pipe_ts = {"PIPE-02": "2026-06-08T21:55:00Z", "PIPE-03": "2026-06-08T22:00:00Z"}
        lines = render_system_health(_make_health(), {}, pipeline_timestamps=pipe_ts)
        text = "\n".join(lines)
        assert "PIPE-02" in text
        assert "2026-06-08T21:55:00Z" in text

    @pytest.mark.unit
    def test_falls_back_to_audit_timestamps_when_none(self):
        last_seen = {"C3": "2026-05-28T10:00:00.000Z"}
        lines = render_system_health(_make_health(), last_seen, pipeline_timestamps=None)
        text = "\n".join(lines)
        assert "C3" in text

    @pytest.mark.unit
    def test_panel_3_label(self):
        lines = render_system_health(_make_health(), {})
        text = "\n".join(lines)
        assert "PANEL 3" in text


# ---------------------------------------------------------------------------
# render_dashboard — full integration with new panels
# ---------------------------------------------------------------------------


class TestRenderDashboardIntegration:
    @pytest.mark.unit
    def test_contains_all_five_panels(self):
        result = render_dashboard(_make_health(), [])
        for i in range(1, 6):
            assert f"PANEL {i}" in result

    @pytest.mark.unit
    def test_portfolio_data_appears_in_output(self):
        port = _make_portfolio(bankroll=958.99, pnl=75.67)
        result = render_dashboard(_make_health(), [], t1_portfolio=port)
        assert "958.99" in result
        assert "75.67" in result

    @pytest.mark.unit
    def test_t4_portfolio_appears_in_output(self):
        t4 = _make_portfolio(bankroll=500.0)
        result = render_dashboard(_make_health(), [], t4_portfolio=t4)
        assert "T4" in result

    @pytest.mark.unit
    def test_pipeline_timestamps_in_output(self):
        pipe_ts = {"PIPE-03": "2026-06-08T22:00:00Z"}
        result = render_dashboard(_make_health(), [], pipeline_timestamps=pipe_ts)
        assert "PIPE-03" in result

    @pytest.mark.unit
    def test_game_date_in_output(self):
        result = render_dashboard(_make_health(), [], game_date="2026-06-08")
        assert "2026-06-08" in result


# ---------------------------------------------------------------------------
# Panel 6 — T4 MLB Detail (added 2026-07-03, GG-076 follow-up, T-231)
# ---------------------------------------------------------------------------


def _make_cycle_row(
    game_date: str = "2026-07-02",
    session_id: str = "T4-MLB-TEST",
    cycle_id: str = "C0001-abc",
    ticker: str = "KXMLBHIT-TESTGAME-PLAYER1-1",
    p_t4: float = 0.5,
    mip: float = 0.4,
    vig: float = 0.04,
    gross_edge: float | None = None,
    net_edge: float | None = None,
    vig_skip: bool = False,
    ts: str = "2026-07-02T19:15:00.000000+00:00",
) -> dict:
    row = {
        "ts": ts,
        "cycle_id": cycle_id,
        "session_id": session_id,
        "game_date": game_date,
        "ticker": ticker,
        "player_name": "Test Player",
        "player_id": 1,
        "threshold": 1,
        "vig": vig,
        "ba_l10": 0.3,
        "h_so_far": 0,
        "ab_so_far": 1,
        "ab_remaining": 2,
        "inning": 3,
        "batting_slot": 5,
    }
    if vig_skip:
        row["vig_skip"] = True
        return row
    row["p_t4"] = p_t4
    row["mip"] = mip
    row["gross_edge"] = gross_edge if gross_edge is not None else round(p_t4 - mip, 6)
    row["net_edge"] = net_edge if net_edge is not None else row["gross_edge"]
    return row


def _make_t4_position(
    ticker: str = "KXMLBHIT-TESTGAME-PLAYER1-1",
    game_date: str = "2026-07-02",
    size_usd: float = 0.5,
) -> dict:
    return {
        "kalshi_ticker": ticker,
        "game_date": game_date,
        "size_usd": size_usd,
        "player_name": "Test Player",
        "pool_isolated": True,
    }


class TestReadJsonlGeneric:
    @pytest.mark.unit
    def test_missing_file_returns_empty(self, tmp_path):
        assert read_jsonl_generic(tmp_path / "nope.jsonl") == []

    @pytest.mark.unit
    def test_reads_valid_rows(self, tmp_path):
        p = tmp_path / "rows.jsonl"
        _write_jsonl(p, [{"a": 1}, {"a": 2}])
        assert read_jsonl_generic(p) == [{"a": 1}, {"a": 2}]

    @pytest.mark.unit
    def test_skips_malformed_line(self, tmp_path):
        p = tmp_path / "rows.jsonl"
        p.write_text('{"a": 1}\nnot json\n{"a": 2}\n')
        assert read_jsonl_generic(p) == [{"a": 1}, {"a": 2}]


class TestComputeT4FunnelStats:
    @pytest.mark.unit
    def test_empty_input(self):
        stats = compute_t4_funnel_stats([])
        assert stats["total"] == 0
        assert stats["evaluated"] == 0
        assert stats["vig_stats"]["mean"] is None

    @pytest.mark.unit
    def test_vig_skip_excluded_from_evaluated(self):
        rows = [
            _make_cycle_row(vig_skip=True),
            _make_cycle_row(p_t4=0.5, mip=0.4),
        ]
        stats = compute_t4_funnel_stats(rows)
        assert stats["total"] == 2
        assert stats["vig_skipped"] == 1
        assert stats["evaluated"] == 1

    @pytest.mark.unit
    def test_edge_threshold_counts(self):
        rows = [
            _make_cycle_row(gross_edge=-0.1, net_edge=-0.1),   # neither
            _make_cycle_row(gross_edge=0.02, net_edge=0.01),   # gross only
            _make_cycle_row(gross_edge=0.10, net_edge=0.06),   # gross, net, and clears MIN(0.04)
        ]
        stats = compute_t4_funnel_stats(rows)
        assert stats["evaluated"] == 3
        assert stats["gross_edge_pos"] == 2
        assert stats["net_edge_pos"] == 2
        assert stats["net_edge_min_approve"] == 1

    @pytest.mark.unit
    def test_vig_stats_computed_over_non_skipped_only(self):
        rows = [
            _make_cycle_row(vig_skip=True, vig=0.9),
            _make_cycle_row(vig=0.10),
            _make_cycle_row(vig=0.20),
        ]
        stats = compute_t4_funnel_stats(rows)
        assert stats["vig_stats"]["mean"] == pytest.approx(0.15)
        assert stats["vig_stats"]["max"] == pytest.approx(0.20)


class TestComputeT4ReentryStats:
    @pytest.mark.unit
    def test_empty_input(self):
        stats = compute_t4_reentry_stats([])
        assert stats["unique_tickers"] == 0
        assert stats["re_entries"] == 0

    @pytest.mark.unit
    def test_all_first_entries_no_reentry(self):
        positions = [
            _make_t4_position(ticker="A"),
            _make_t4_position(ticker="B"),
        ]
        stats = compute_t4_reentry_stats(positions)
        assert stats["unique_tickers"] == 2
        assert stats["re_entries"] == 0
        assert stats["tickers_with_reentry"] == 0

    @pytest.mark.unit
    def test_reentry_counted_correctly(self):
        positions = [
            _make_t4_position(ticker="A"),
            _make_t4_position(ticker="A"),  # re-entry
            _make_t4_position(ticker="A"),  # second re-entry
            _make_t4_position(ticker="B"),
        ]
        stats = compute_t4_reentry_stats(positions)
        assert stats["unique_tickers"] == 2
        assert stats["re_entries"] == 2
        assert stats["tickers_with_reentry"] == 1
        assert stats["max_entries_one_ticker"] == 3


class TestComputeT4ContaminationStats:
    @pytest.mark.unit
    def test_empty_input(self):
        stats = compute_t4_contamination_stats([])
        assert stats["total_halts"] == 0
        assert stats["staleness_halts"] == 0

    @pytest.mark.unit
    def test_takes_max_of_running_counters(self):
        entries = [
            _make_entry(
                component="PIPE-07-MLB", event_type="CONTAMINATION_HALT",
                severity="WARNING", timestamp="2026-07-02T19:00:00Z",
                payload={"total_halts": 1, "staleness_halts": 0, "failed_checks": ["market_active"]},
            ),
            _make_entry(
                component="PIPE-07-MLB", event_type="CONTAMINATION_HALT",
                severity="WARNING", timestamp="2026-07-02T20:00:00Z",
                payload={"total_halts": 3, "staleness_halts": 1, "failed_checks": ["game_state_fresh"]},
            ),
        ]
        stats = compute_t4_contamination_stats(entries)
        assert stats["total_halts"] == 3
        assert stats["staleness_halts"] == 1
        assert stats["event_count"] == 2
        assert stats["failed_check_counts"] == {"market_active": 1, "game_state_fresh": 1}

    @pytest.mark.unit
    def test_date_filter_excludes_other_days(self):
        entries = [
            _make_entry(
                event_type="CONTAMINATION_HALT", timestamp="2026-07-01T19:00:00Z",
                payload={"total_halts": 5, "staleness_halts": 2},
            ),
        ]
        stats = compute_t4_contamination_stats(entries, game_date="2026-07-02")
        assert stats["event_count"] == 0
        assert stats["total_halts"] == 0


class TestRenderT4SubbandRegistry:
    @pytest.mark.unit
    def test_shows_all_three_subbands_with_correct_status(self):
        text = "\n".join(render_t4_subband_registry())
        assert "T4M-PROJ" in text
        assert "[ACTIVE ]" in text
        assert "T4M-ARITH" in text
        assert "T4M-FLOW" in text
        assert text.count("[BLOCKED]") == 2
        assert "EXP-ARITH-MLB-01" in text
        assert "EXP-FLOW-MLB-01" in text


class TestRenderT4DetailPanel:
    @pytest.mark.unit
    def test_degrades_gracefully_on_all_empty_inputs(self):
        # Must not raise — this is the core design contract for Panel 6.
        lines = render_t4_detail_panel(
            t4_mlb_portfolio={},
            cycle_entries=[],
            t4_audit_entries=[],
            edge_log_path=None,
            game_date="2026-07-02",
        )
        text = "\n".join(lines)
        assert "PANEL 6" in text
        assert "not found" in text.lower() or "no cycle-log activity" in text.lower()

    @pytest.mark.unit
    def test_funnel_numbers_appear_with_real_cycle_data(self):
        rows = [
            _make_cycle_row(ticker="A-1", gross_edge=0.10, net_edge=0.06),
            _make_cycle_row(ticker="A-2", vig_skip=True),
        ]
        lines = render_t4_detail_panel(
            t4_mlb_portfolio={},
            cycle_entries=rows,
            t4_audit_entries=[],
            edge_log_path=None,
            game_date="2026-07-02",
        )
        text = "\n".join(lines)
        assert "Total rows 2" in text
        assert "Vig-skipped 1" in text

    @pytest.mark.unit
    def test_reentry_and_budget_appear_with_position_data(self):
        portfolio = _make_portfolio(
            bankroll=1000.0,
            open_positions=[
                _make_t4_position(ticker="A", size_usd=0.4),
                _make_t4_position(ticker="A", size_usd=0.4),
            ],
        )
        lines = render_t4_detail_panel(
            t4_mlb_portfolio=portfolio,
            cycle_entries=[],
            t4_audit_entries=[],
            edge_log_path=None,
            game_date="2026-07-02",
        )
        text = "\n".join(lines)
        assert "Re-entries: 1" in text
        assert "Band budget" in text

    @pytest.mark.unit
    def test_staleness_halt_shows_warning_marker(self):
        entries = [
            _make_entry(
                event_type="CONTAMINATION_HALT", timestamp="2026-07-02T19:00:00Z",
                payload={"total_halts": 1, "staleness_halts": 1, "failed_checks": ["snapshot_not_stale"]},
            ),
        ]
        lines = render_t4_detail_panel(
            t4_mlb_portfolio={},
            cycle_entries=[],
            t4_audit_entries=entries,
            edge_log_path=None,
            game_date="2026-07-02",
        )
        text = "\n".join(lines)
        assert "STALENESS DETECTED" in text


class TestRenderDashboardWithPanel6:
    @pytest.mark.unit
    def test_panel_6_appears_by_default(self):
        result = render_dashboard(_make_health(), [])
        assert "PANEL 6" in result

    @pytest.mark.unit
    def test_panel_6_omitted_when_disabled(self):
        result = render_dashboard(_make_health(), [], show_t4_mlb_detail=False)
        assert "PANEL 6" not in result

    @pytest.mark.unit
    def test_all_six_panels_present_by_default(self):
        result = render_dashboard(_make_health(), [])
        for i in range(1, 7):
            assert f"PANEL {i}" in result
