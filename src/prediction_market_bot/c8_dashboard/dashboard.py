"""
C8: Visual Dashboard — Terminal Renderer
=========================================
Component:    C8 (Visual Dashboard)
Phase active: Phase 5+ (read-only; never writes to C6 or C7 state)
Status:       IMPLEMENTED (Phase 5 2026-05-28)
Upstream:     C6 Audit Logger log file (IF-C6-C8); C7 SystemMonitor (IF-C7-C8)
Downstream:   Terminal output only (stdout)
Interfaces:   IF-C6-C8 (reads audit.jsonl); IF-C7-C8 (reads health snapshot)
ADR refs:     ADR-0001 (Compass OS)

Panels rendered:
  1. System Health     — kill switch state, component last-seen timestamps
  2. Drift Metrics     — rolling Brier, ECE, mean edge vs. thresholds
  3. Alert Feed        — last N WARN/ERROR/CRITICAL audit events

Usage (CLI)::
    python -m prediction_market_bot.c8_dashboard.dashboard \\
        --log-path logs/audit.jsonl \\
        [--monitor <snapshot dict — for testing>] \\
        [--n-alerts 20]

The dashboard is stateless — each invocation reads the current log and renders.
It does NOT start a polling loop; wrap in a shell loop or cron if continuous
monitoring is needed.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

COMPONENT = "C8"

# Severity levels that appear in the alert feed
_ALERT_SEVERITIES = {"WARNING", "WARN", "ERROR", "CRITICAL"}

# Box-drawing characters for panels
_BOX_WIDTH = 72
_HR = "─" * _BOX_WIDTH
_SEP = "│"

# Alert level → display string
_ALERT_DISPLAY = {
    "OK": "  OK  ",
    "L1_WATCH": " WATCH",
    "L2_ALERT": "ALERT ",
    "L3_PAUSE": "PAUSE ",
    "L4_KILL": " KILL ",
}


# ---------------------------------------------------------------------------
# C6 audit log reader (IF-C6-C8)
# ---------------------------------------------------------------------------


def read_audit_log(log_path: str | Path) -> list[dict[str, Any]]:
    """
    Read all entries from a C6 audit log (JSONL format).
    Returns an empty list if the file does not exist.
    """
    path = Path(log_path)
    if not path.exists():
        return []
    entries: list[dict[str, Any]] = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return entries


def get_recent_alerts(
    entries: list[dict[str, Any]],
    n: int = 20,
) -> list[dict[str, Any]]:
    """Return the last n entries with severity in WARN/WARNING/ERROR/CRITICAL."""
    alerts = [e for e in entries if e.get("severity", "") in _ALERT_SEVERITIES]
    return alerts[-n:]


def get_component_last_seen(entries: list[dict[str, Any]]) -> dict[str, str]:
    """Return a mapping of component → last log timestamp."""
    last: dict[str, str] = {}
    for e in entries:
        comp = e.get("component", "UNKNOWN")
        ts = e.get("timestamp", "")
        if ts:
            last[comp] = ts
    return last


def extract_forecast_outcomes(
    entries: list[dict[str, Any]],
    n: int = 30,
) -> list[dict[str, Any]]:
    """
    Extract recent forecast records from C6 audit log for Brier trend.
    Looks for C3 forecast_emitted events with p_estimate in payload.
    """
    forecasts = [
        e for e in entries
        if e.get("component") == "C3" and e.get("event_type") == "forecast_emitted"
        and isinstance(e.get("payload"), dict)
        and "p_estimate" in e["payload"]
    ]
    return forecasts[-n:]


# ---------------------------------------------------------------------------
# Rendering helpers
# ---------------------------------------------------------------------------


def _utc_now_display() -> str:
    return datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _pad(s: str, width: int, align: str = "left") -> str:
    s = str(s)
    if len(s) >= width:
        return s[:width]
    if align == "right":
        return s.rjust(width)
    if align == "center":
        return s.center(width)
    return s.ljust(width)


def _bar(value: float | None, min_val: float, max_val: float, width: int = 20) -> str:
    """ASCII progress bar for a metric between min_val and max_val."""
    if value is None:
        return "[" + "?" * width + "]"
    frac = max(0.0, min(1.0, (value - min_val) / (max_val - min_val + 1e-9)))
    filled = int(round(frac * width))
    return "[" + "█" * filled + "░" * (width - filled) + "]"


def _fmt_float(v: float | None, decimals: int = 4) -> str:
    if v is None:
        return "  N/A  "
    return f"{v:.{decimals}f}"


# ---------------------------------------------------------------------------
# Panel renderers
# ---------------------------------------------------------------------------


def render_system_health(
    health: dict[str, Any],
    component_last_seen: dict[str, str],
) -> list[str]:
    """Panel 1: System health — kill switch state + component activity."""
    lines: list[str] = []
    lines.append("┌" + _HR + "┐")
    lines.append(_SEP + _pad(" PANEL 1 — SYSTEM HEALTH", _BOX_WIDTH) + _SEP)
    lines.append("├" + _HR + "┤")

    ks_active = health.get("kill_switch_active", False)
    ks_state = health.get("kill_switch_state", "UNKNOWN")
    ks_reason = health.get("kill_switch_reason") or "—"

    if ks_active:
        ks_line = f"  *** KILL SWITCH ACTIVE *** | Reason: {ks_reason}"
    else:
        ks_line = f"  Kill Switch: {ks_state}"

    lines.append(_SEP + _pad(ks_line, _BOX_WIDTH) + _SEP)
    lines.append(_SEP + _pad("", _BOX_WIDTH) + _SEP)
    lines.append(_SEP + _pad("  Component Last Activity:", _BOX_WIDTH) + _SEP)

    active_components = ["C1", "C2", "C3", "C4", "C5", "C6", "C7"]
    for comp in active_components:
        ts = component_last_seen.get(comp, "no events")
        row = f"    {_pad(comp, 4)} {ts}"
        lines.append(_SEP + _pad(row, _BOX_WIDTH) + _SEP)

    lines.append("└" + _HR + "┘")
    return lines


def render_drift_panel(health: dict[str, Any]) -> list[str]:
    """Panel 2: Drift metrics — rolling Brier, ECE, mean edge vs thresholds."""
    lines: list[str] = []
    lines.append("┌" + _HR + "┐")
    lines.append(_SEP + _pad(" PANEL 2 — DRIFT METRICS (C7)", _BOX_WIDTH) + _SEP)
    lines.append("├" + _HR + "┤")

    alert_level = health.get("alert_level", "OK")
    n_events = health.get("n_events_in_window", 0)
    alert_tag = _ALERT_DISPLAY.get(alert_level, alert_level)
    alert_msg = health.get("alert_message") or "No alerts"

    lines.append(_SEP + _pad(f"  Alert Level: [{alert_tag}]  |  Window: {n_events} events", _BOX_WIDTH) + _SEP)
    lines.append(_SEP + _pad(f"  {alert_msg}", _BOX_WIDTH) + _SEP)
    lines.append(_SEP + _pad("", _BOX_WIDTH) + _SEP)

    brier = health.get("rolling_brier")
    ece = health.get("rolling_ece")
    mean_edge = health.get("mean_edge")
    brier_base = health.get("brier_baseline", 0.2416)
    ece_base = health.get("ece_baseline", 0.0247)
    brier_l2 = health.get("brier_l2_threshold", brier_base + 0.05)
    brier_l3 = health.get("brier_l3_threshold", brier_base + 0.10)

    # Brier row
    brier_bar = _bar(brier, brier_base - 0.05, brier_l3 + 0.05)
    brier_status = "OK" if (brier is None or brier <= brier_l2) else "ALERT"
    lines.append(_SEP + _pad(
        f"  Brier  {_fmt_float(brier)} {brier_bar} baseline={brier_base:.4f} [{brier_status}]",
        _BOX_WIDTH
    ) + _SEP)

    # ECE row
    ece_l2 = ece_base + 0.05
    ece_bar = _bar(ece, 0.0, ece_l2 * 2)
    ece_status = "OK" if (ece is None or ece <= ece_l2) else "ALERT"
    lines.append(_SEP + _pad(
        f"  ECE    {_fmt_float(ece)} {ece_bar} baseline={ece_base:.4f} [{ece_status}]",
        _BOX_WIDTH
    ) + _SEP)

    # Mean edge row
    edge_bar = _bar(mean_edge, -0.10, 0.20)
    edge_status = "OK" if (mean_edge is None or mean_edge >= 0) else "WARN"
    lines.append(_SEP + _pad(
        f"  Edge   {_fmt_float(mean_edge)} {edge_bar} threshold=0.0000 [{edge_status}]",
        _BOX_WIDTH
    ) + _SEP)

    lines.append("└" + _HR + "┘")
    return lines


def render_alert_feed(
    alerts: list[dict[str, Any]],
    n: int = 20,
) -> list[str]:
    """Panel 3: Alert feed — recent WARN/ERROR/CRITICAL audit events."""
    lines: list[str] = []
    lines.append("┌" + _HR + "┐")
    lines.append(_SEP + _pad(f" PANEL 3 — ALERT FEED (last {n})", _BOX_WIDTH) + _SEP)
    lines.append("├" + _HR + "┤")

    if not alerts:
        lines.append(_SEP + _pad("  No alerts.", _BOX_WIDTH) + _SEP)
    else:
        for entry in reversed(alerts[-n:]):
            ts = entry.get("timestamp", "")[:19]
            sev = _pad(entry.get("severity", "?"), 8)
            comp = _pad(entry.get("component", "?"), 3)
            evt = entry.get("event_type", "?")
            row = f"  {ts} {sev} {comp} {evt}"
            lines.append(_SEP + _pad(row, _BOX_WIDTH) + _SEP)

    lines.append("└" + _HR + "┘")
    return lines


# ---------------------------------------------------------------------------
# Main render
# ---------------------------------------------------------------------------


def render_dashboard(
    health: dict[str, Any],
    audit_entries: list[dict[str, Any]],
    n_alerts: int = 20,
) -> str:
    """
    Render the full C8 dashboard as a single string.

    Parameters
    ----------
    health:
        Health snapshot dict from SystemMonitor.get_health_snapshot() (IF-C7-C8).
        If no live monitor is available, pass an empty dict.
    audit_entries:
        All entries read from C6 audit log (IF-C6-C8).
    n_alerts:
        Number of recent alerts to show in Panel 3.
    """
    now = _utc_now_display()
    header = [
        "",
        f"  PREDICTION MARKET BOT — C8 VISUAL DASHBOARD",
        f"  Rendered: {now}",
        "",
    ]

    component_last_seen = get_component_last_seen(audit_entries)
    alerts = get_recent_alerts(audit_entries, n=n_alerts)

    panel1 = render_system_health(health, component_last_seen)
    panel2 = render_drift_panel(health)
    panel3 = render_alert_feed(alerts, n=n_alerts)

    all_lines = header + panel1 + [""] + panel2 + [""] + panel3 + [""]
    return "\n".join(all_lines)


# ---------------------------------------------------------------------------
# CLI entrypoint
# ---------------------------------------------------------------------------


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="C8 Visual Dashboard — render system health and drift metrics"
    )
    parser.add_argument(
        "--log-path",
        default=os.environ.get("BOT_AUDIT_LOG_PATH", "logs/audit.jsonl"),
        help="Path to C6 audit log file (default: logs/audit.jsonl)",
    )
    parser.add_argument(
        "--n-alerts",
        type=int,
        default=20,
        help="Number of recent alerts to display (default: 20)",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = _parse_args(argv)
    audit_entries = read_audit_log(args.log_path)

    # Build a minimal health snapshot from audit log if no live monitor
    # In Phase 5+, a live SystemMonitor should be passed in directly.
    # For the CLI, we infer kill switch state from last kill_switch_triggered event.
    ks_active = False
    ks_reason: str | None = None
    for entry in reversed(audit_entries):
        if entry.get("event_type") == "kill_switch_triggered":
            ks_active = True
            ks_reason = entry.get("payload", {}).get("reason")
            break
        if entry.get("event_type") == "kill_switch_reset":
            break

    health: dict[str, Any] = {
        "kill_switch_active": ks_active,
        "kill_switch_state": "TRIGGERED" if ks_active else "ARMED",
        "kill_switch_reason": ks_reason,
        "alert_level": "OK",
        "n_events_in_window": 0,
        "rolling_brier": None,
        "rolling_ece": None,
        "mean_edge": None,
        "brier_baseline": 0.2416,
        "ece_baseline": 0.0247,
        "brier_l2_threshold": 0.2916,
        "brier_l3_threshold": 0.3416,
        "alert_message": None,
    }

    output = render_dashboard(
        health=health,
        audit_entries=audit_entries,
        n_alerts=args.n_alerts,
    )
    print(output)


if __name__ == "__main__":
    main()
