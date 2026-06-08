"""
C8: Visual Dashboard — Terminal Renderer
=========================================
Component:    C8 (Visual Dashboard)
Phase active: Phase 5+ (read-only; never writes to C6 or C7 state)
Status:       IMPLEMENTED (Phase 5 2026-05-28); reworked 2026-06-08 for T4 scale
Upstream:     paper_portfolio.json (T1); paper_portfolio_t4.json (T4);
              C6 audit.jsonl (kill switch only); pipeline log file mtimes
Downstream:   Terminal output only (stdout)

Panels:
  1. Portfolio Summary   — T1 + T4 bankroll, P&L, positions, win rate
  2. Today's Throughput  — bets by band, T3 signals, T4 aggregated counts
  3. System Health       — kill switch state, pipeline last-run timestamps
  4. Drift Metrics       — rolling Brier, ECE, mean edge vs thresholds (C7)
  5. Alert Feed          — last N WARN/ERROR/CRITICAL, deduplicated by type

Data sources (in priority order):
  - logs/paper_portfolio.json        — T1 portfolio state
  - logs/paper_portfolio_t4.json     — T4 portfolio state (may not exist)
  - logs/audit.jsonl                 — kill switch state only
  - logs/*.log (file mtimes)         — pipeline last-run timestamps

Usage (CLI)::
    python -m prediction_market_bot.c8_dashboard.dashboard \\
        [--log-path logs/audit.jsonl] \\
        [--portfolio-path logs/paper_portfolio.json] \\
        [--t4-portfolio-path logs/paper_portfolio_t4.json] \\
        [--log-dir logs/] \\
        [--game-date YYYY-MM-DD] \\
        [--n-alerts 20]

The dashboard is stateless — each invocation reads current files and renders.
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

_ALERT_SEVERITIES = {"WARNING", "WARN", "ERROR", "CRITICAL"}

_BOX_WIDTH = 72
_HR = "─" * _BOX_WIDTH
_SEP = "│"

_ALERT_DISPLAY = {
    "OK": "  OK  ",
    "L1_WATCH": " WATCH",
    "L2_ALERT": "ALERT ",
    "L3_PAUSE": "PAUSE ",
    "L4_KILL": " KILL ",
}

# Map pipeline name → log file names to check (newest mtime wins)
_PIPE_LOG_FILES: dict[str, list[str]] = {
    "T-140":   ["t140_cache_check.log"],
    "PIPE-02": ["pregame_cron.log", "pregame_late_cron.log"],
    "PIPE-03": ["paper_early_cron.log", "paper_late_cron.log"],
    "PIPE-07": ["t4_live_cron.log", "t4_live.log"],
    "HEALTH":  ["health.log"],
}


# ---------------------------------------------------------------------------
# C6 audit log reader (IF-C6-C8) — kill switch state only
# ---------------------------------------------------------------------------


def read_audit_log(log_path: str | Path) -> list[dict[str, Any]]:
    """Read all entries from a C6 audit log (JSONL). Returns [] if missing."""
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
    """Return mapping of component → last log timestamp (from audit.jsonl)."""
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
    """Extract recent C3 forecast_emitted records with p_estimate."""
    forecasts = [
        e for e in entries
        if e.get("component") == "C3"
        and e.get("event_type") == "forecast_emitted"
        and isinstance(e.get("payload"), dict)
        and "p_estimate" in e["payload"]
    ]
    return forecasts[-n:]


# ---------------------------------------------------------------------------
# Portfolio reader
# ---------------------------------------------------------------------------


def read_portfolio(path: str | Path | None) -> dict[str, Any]:
    """Read a paper portfolio JSON file. Returns {} if missing or unreadable."""
    if path is None:
        return {}
    p = Path(path)
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text())
    except (json.JSONDecodeError, OSError):
        return {}


def get_pipeline_timestamps(log_dir: str | Path) -> dict[str, str]:
    """
    Return {pipe_name: last_modified_utc} by checking log file mtimes.
    For each pipeline, picks the most recently modified log file.
    """
    d = Path(log_dir)
    result: dict[str, str] = {}
    for pipe, filenames in _PIPE_LOG_FILES.items():
        latest: float | None = None
        for fn in filenames:
            p = d / fn
            if p.exists():
                mtime = p.stat().st_mtime
                if latest is None or mtime > latest:
                    latest = mtime
        if latest is not None:
            dt = datetime.fromtimestamp(latest, tz=timezone.utc)
            result[pipe] = dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    return result


# ---------------------------------------------------------------------------
# Portfolio stats helpers
# ---------------------------------------------------------------------------


def _compute_portfolio_stats(portfolio: dict[str, Any]) -> dict[str, Any]:
    bankroll = float(portfolio.get("bankroll_usd") or 0.0)
    initial = float(portfolio.get("initial_bankroll_usd") or bankroll or 1000.0)
    pnl = float(portfolio.get("total_realized_pnl") or 0.0)
    open_pos = portfolio.get("open_positions") or []
    closed_pos = portfolio.get("closed_positions") or []

    # open_positions may be list or dict
    if isinstance(open_pos, dict):
        open_pos = list(open_pos.values())
    if isinstance(closed_pos, dict):
        closed_pos = list(closed_pos.values())

    n_open = len(open_pos)
    n_closed = len(closed_pos)

    deployed = sum(float(p.get("size_usd") or 0.0) for p in open_pos)
    deployed_pct = deployed / initial * 100 if initial else 0.0
    # Reserve = liquid cash = bankroll minus deployed stakes
    reserve = bankroll - deployed

    wins = sum(1 for p in closed_pos if p.get("outcome") == "WIN")
    win_rate = wins / n_closed if n_closed else None

    # Drawdown = realized loss as % of initial. Total value = bankroll + deployed,
    # so comparing bankroll alone to initial would falsely show drawdown when stakes
    # are locked in open positions. Use realized P&L: if pnl < 0 → drawdown.
    drawdown_pct = max(0.0, -pnl / initial * 100) if initial else 0.0
    pnl_pct = pnl / initial * 100 if initial else 0.0

    return {
        "bankroll": bankroll,
        "initial": initial,
        "pnl": pnl,
        "pnl_pct": pnl_pct,
        "n_open": n_open,
        "n_closed": n_closed,
        "open_pos": open_pos,
        "closed_pos": closed_pos,
        "deployed": deployed,
        "deployed_pct": deployed_pct,
        "reserve": reserve,
        "win_rate": win_rate,
        "drawdown_pct": drawdown_pct,
    }


def _positions_for_date(positions: list[dict], date_str: str) -> list[dict]:
    return [p for p in positions if p.get("game_date") == date_str]


def _today_str() -> str:
    return datetime.now(tz=timezone.utc).strftime("%Y-%m-%d")


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
    """ASCII progress bar."""
    if value is None:
        return "[" + "?" * width + "]"
    frac = max(0.0, min(1.0, (value - min_val) / (max_val - min_val + 1e-9)))
    filled = int(round(frac * width))
    return "[" + "█" * filled + "░" * (width - filled) + "]"


def _fmt_float(v: float | None, decimals: int = 4) -> str:
    if v is None:
        return "  N/A  "
    return f"{v:.{decimals}f}"


def _fmt_pnl(v: float) -> str:
    sign = "+" if v >= 0 else ""
    return f"{sign}${v:.2f}"


# ---------------------------------------------------------------------------
# Panel 1 — Portfolio Summary
# ---------------------------------------------------------------------------


def render_portfolio_panel(
    t1_portfolio: dict[str, Any],
    t4_portfolio: dict[str, Any],
) -> list[str]:
    """Panel 1: Bankroll, P&L, positions, win rate for T1 and T4."""
    lines: list[str] = []
    lines.append("┌" + _HR + "┐")
    lines.append(_SEP + _pad(" PANEL 1 — PORTFOLIO SUMMARY", _BOX_WIDTH) + _SEP)
    lines.append("├" + _HR + "┤")

    # T1
    if not t1_portfolio:
        lines.append(_SEP + _pad("  T1: paper_portfolio.json not found.", _BOX_WIDTH) + _SEP)
    else:
        s = _compute_portfolio_stats(t1_portfolio)
        wr = f"{s['win_rate']:.1%}" if s["win_rate"] is not None else "N/A"
        pnl_str = _fmt_pnl(s["pnl"])
        pnl_pct = f"({'+' if s['pnl_pct'] >= 0 else ''}{s['pnl_pct']:.2f}%)"
        lines.append(_SEP + _pad("  T1  Pregame", _BOX_WIDTH) + _SEP)
        lines.append(_SEP + _pad(
            f"    Bankroll ${s['bankroll']:.2f}"
            f"  │  Initial ${s['initial']:.2f}"
            f"  │  P&L {pnl_str} {pnl_pct}",
            _BOX_WIDTH,
        ) + _SEP)
        lines.append(_SEP + _pad(
            f"    Open {s['n_open']}"
            f"  │  Closed {s['n_closed']}"
            f"  │  Win rate {wr}"
            f"  │  Drawdown {s['drawdown_pct']:.1f}%",
            _BOX_WIDTH,
        ) + _SEP)
        lines.append(_SEP + _pad(
            f"    Deployed ${s['deployed']:.2f} ({s['deployed_pct']:.1f}%)"
            f"  │  Reserve ${s['reserve']:.2f}",
            _BOX_WIDTH,
        ) + _SEP)

    lines.append(_SEP + _pad("", _BOX_WIDTH) + _SEP)

    # T4
    if not t4_portfolio:
        lines.append(_SEP + _pad("  T4  In-play  — no portfolio yet", _BOX_WIDTH) + _SEP)
    else:
        s4 = _compute_portfolio_stats(t4_portfolio)
        pnl4 = _fmt_pnl(s4["pnl"])
        wr4 = f"{s4['win_rate']:.1%}" if s4["win_rate"] is not None else "N/A"
        lines.append(_SEP + _pad("  T4  In-play", _BOX_WIDTH) + _SEP)
        lines.append(_SEP + _pad(
            f"    Open {s4['n_open']}"
            f"  │  Closed {s4['n_closed']}"
            f"  │  Win rate {wr4}"
            f"  │  P&L {pnl4}",
            _BOX_WIDTH,
        ) + _SEP)
        lines.append(_SEP + _pad(
            f"    Deployed ${s4['deployed']:.2f} ({s4['deployed_pct']:.1f}%)",
            _BOX_WIDTH,
        ) + _SEP)

    lines.append("└" + _HR + "┘")
    return lines


# ---------------------------------------------------------------------------
# Panel 2 — Today's Throughput
# ---------------------------------------------------------------------------


def _player_breakdown(positions: list[dict], max_players: int = 5) -> str:
    counts: dict[str, int] = {}
    for p in positions:
        name = p.get("player_name") or "?"
        counts[name] = counts.get(name, 0) + 1
    top = sorted(counts.items(), key=lambda x: -x[1])[:max_players]
    # Try full names first; fall back to last-name-only if line would be too wide
    full = "  ".join(f"{n} ×{c}" for n, c in top)
    if len(full) <= _BOX_WIDTH - 14:  # 14 = "    Players: " prefix
        return full
    short = "  ".join(f"{n.split()[-1]} ×{c}" for n, c in top)
    return short


def render_throughput_panel(
    t1_portfolio: dict[str, Any],
    t4_portfolio: dict[str, Any],
    game_date: str | None = None,
) -> list[str]:
    """Panel 2: Bets placed today by band, T3 signals, T4 aggregated metrics."""
    gd = game_date or _today_str()
    lines: list[str] = []
    lines.append("┌" + _HR + "┐")
    lines.append(_SEP + _pad(f" PANEL 2 — TODAY'S THROUGHPUT  ({gd})", _BOX_WIDTH) + _SEP)
    lines.append("├" + _HR + "┤")

    # --- T1 ---
    t1_s = _compute_portfolio_stats(t1_portfolio) if t1_portfolio else {}
    t1_open = t1_s.get("open_pos", [])
    t1_closed = t1_s.get("closed_pos", [])
    t1_today = _positions_for_date(t1_open, gd) + _positions_for_date(t1_closed, gd)
    n_t1 = len(t1_today)

    if not t1_portfolio:
        lines.append(_SEP + _pad("  T1: no portfolio loaded.", _BOX_WIDTH) + _SEP)
    elif n_t1 == 0:
        lines.append(_SEP + _pad(f"  T1: no positions for {gd}.", _BOX_WIDTH) + _SEP)
    else:
        staked = sum(float(p.get("size_usd") or 0.0) for p in t1_today)
        avg_size = staked / n_t1
        lines.append(_SEP + _pad(
            f"  T1: {n_t1} bets  │  Staked ${staked:.2f}  │  Avg ${avg_size:.2f}",
            _BOX_WIDTH,
        ) + _SEP)
        breakdown = _player_breakdown(t1_today)
        if breakdown:
            lines.append(_SEP + _pad(f"    Players: {breakdown}", _BOX_WIDTH) + _SEP)
        t3_confirm = sum(1 for p in t1_today if p.get("t3_signal") == "CONFIRM")
        t3_fade = sum(1 for p in t1_today if p.get("t3_signal") == "FADE")
        t3_neutral = sum(1 for p in t1_today if p.get("t3_signal") == "NEUTRAL")
        lines.append(_SEP + _pad(
            f"    T3 signals: {t3_confirm} CONFIRM  {t3_fade} FADE  {t3_neutral} NEUTRAL",
            _BOX_WIDTH,
        ) + _SEP)

    lines.append(_SEP + _pad("", _BOX_WIDTH) + _SEP)

    # --- T4 ---
    t4_s = _compute_portfolio_stats(t4_portfolio) if t4_portfolio else {}
    t4_open = t4_s.get("open_pos", [])
    t4_closed = t4_s.get("closed_pos", [])
    t4_today_open = _positions_for_date(t4_open, gd)
    t4_today_closed = _positions_for_date(t4_closed, gd)
    t4_today = t4_today_open + t4_today_closed
    n_t4 = len(t4_today)

    if not t4_portfolio:
        lines.append(_SEP + _pad("  T4: no portfolio (PIPE-07 not run yet).", _BOX_WIDTH) + _SEP)
    elif n_t4 == 0:
        lines.append(_SEP + _pad(f"  T4: 0 positions for {gd}.", _BOX_WIDTH) + _SEP)
    else:
        staked4 = sum(float(p.get("size_usd") or 0.0) for p in t4_today)
        n_players = len({p.get("player_name") for p in t4_today})
        lines.append(_SEP + _pad(
            f"  T4: {n_t4} positions  │  {n_players} players  │  Staked ${staked4:.2f}",
            _BOX_WIDTH,
        ) + _SEP)
        # Player breakdown — important for ~1000 bet volumes
        breakdown4 = _player_breakdown(t4_today, max_players=4)
        if breakdown4:
            lines.append(_SEP + _pad(f"    By player: {breakdown4}", _BOX_WIDTH) + _SEP)
        # Resolved subset
        n_res = len(t4_today_closed)
        if n_res > 0:
            wins4 = sum(1 for p in t4_today_closed if p.get("outcome") == "WIN")
            pnl4 = sum(float(p.get("pnl") or 0.0) for p in t4_today_closed)
            lines.append(_SEP + _pad(
                f"    Resolved: {n_res}  │  Win rate {wins4/n_res:.1%}"
                f"  │  P&L {_fmt_pnl(pnl4)}",
                _BOX_WIDTH,
            ) + _SEP)

    lines.append("└" + _HR + "┘")
    return lines


# ---------------------------------------------------------------------------
# Panel 3 — System Health
# ---------------------------------------------------------------------------


def render_system_health(
    health: dict[str, Any],
    component_last_seen: dict[str, str],
    pipeline_timestamps: dict[str, str] | None = None,
) -> list[str]:
    """Panel 3: Kill switch state + pipeline activity timestamps."""
    lines: list[str] = []
    lines.append("┌" + _HR + "┐")
    lines.append(_SEP + _pad(" PANEL 3 — SYSTEM HEALTH", _BOX_WIDTH) + _SEP)
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

    if pipeline_timestamps:
        lines.append(_SEP + _pad("  Pipeline last run (log file timestamps):", _BOX_WIDTH) + _SEP)
        for pipe in ["T-140", "PIPE-02", "PIPE-03", "PIPE-07", "HEALTH"]:
            ts = pipeline_timestamps.get(pipe, "no log")
            lines.append(_SEP + _pad(f"    {_pad(pipe, 8)} {ts}", _BOX_WIDTH) + _SEP)
    else:
        lines.append(_SEP + _pad("  Component last activity (audit.jsonl):", _BOX_WIDTH) + _SEP)
        for comp in ["C1", "C2", "C3", "C4", "C5", "C6", "C7"]:
            ts = component_last_seen.get(comp, "no events")
            lines.append(_SEP + _pad(f"    {_pad(comp, 4)} {ts}", _BOX_WIDTH) + _SEP)

    lines.append("└" + _HR + "┘")
    return lines


# ---------------------------------------------------------------------------
# Panel 4 — Drift Metrics
# ---------------------------------------------------------------------------


def render_drift_panel(health: dict[str, Any]) -> list[str]:
    """Panel 4: Rolling Brier, ECE, mean edge vs thresholds (from C7)."""
    lines: list[str] = []
    lines.append("┌" + _HR + "┐")
    lines.append(_SEP + _pad(" PANEL 4 — DRIFT METRICS (C7)", _BOX_WIDTH) + _SEP)
    lines.append("├" + _HR + "┤")

    alert_level = health.get("alert_level", "OK")
    n_events = health.get("n_events_in_window", 0)
    alert_tag = _ALERT_DISPLAY.get(alert_level, alert_level)
    alert_msg = health.get("alert_message") or "No alerts"

    lines.append(_SEP + _pad(
        f"  Alert Level: [{alert_tag}]  |  Window: {n_events} events",
        _BOX_WIDTH,
    ) + _SEP)
    lines.append(_SEP + _pad(f"  {alert_msg}", _BOX_WIDTH) + _SEP)
    lines.append(_SEP + _pad("", _BOX_WIDTH) + _SEP)

    brier = health.get("rolling_brier")
    ece = health.get("rolling_ece")
    mean_edge = health.get("mean_edge")
    brier_base = health.get("brier_baseline", 0.2416)
    ece_base = health.get("ece_baseline", 0.0247)
    brier_l2 = health.get("brier_l2_threshold", brier_base + 0.05)
    brier_l3 = health.get("brier_l3_threshold", brier_base + 0.10)

    brier_bar = _bar(brier, brier_base - 0.05, brier_l3 + 0.05)
    brier_status = "OK" if (brier is None or brier <= brier_l2) else "ALERT"
    lines.append(_SEP + _pad(
        f"  Brier  {_fmt_float(brier)} {brier_bar} baseline={brier_base:.4f} [{brier_status}]",
        _BOX_WIDTH,
    ) + _SEP)

    ece_l2 = ece_base + 0.05
    ece_bar = _bar(ece, 0.0, ece_l2 * 2)
    ece_status = "OK" if (ece is None or ece <= ece_l2) else "ALERT"
    lines.append(_SEP + _pad(
        f"  ECE    {_fmt_float(ece)} {ece_bar} baseline={ece_base:.4f} [{ece_status}]",
        _BOX_WIDTH,
    ) + _SEP)

    edge_bar = _bar(mean_edge, -0.10, 0.20)
    edge_status = "OK" if (mean_edge is None or mean_edge >= 0) else "WARN"
    lines.append(_SEP + _pad(
        f"  Edge   {_fmt_float(mean_edge)} {edge_bar} threshold=0.0000 [{edge_status}]",
        _BOX_WIDTH,
    ) + _SEP)

    lines.append("└" + _HR + "┘")
    return lines


# ---------------------------------------------------------------------------
# Panel 5 — Alert Feed
# ---------------------------------------------------------------------------


def render_alert_feed(
    alerts: list[dict[str, Any]],
    n: int = 20,
) -> list[str]:
    """Panel 5: Recent WARN/ERROR/CRITICAL events, deduplicated by type."""
    lines: list[str] = []
    lines.append("┌" + _HR + "┐")
    lines.append(_SEP + _pad(
        f" PANEL 5 — ALERT FEED (last {n}, deduplicated by type)",
        _BOX_WIDTH,
    ) + _SEP)
    lines.append("├" + _HR + "┤")

    if not alerts:
        lines.append(_SEP + _pad("  No alerts.", _BOX_WIDTH) + _SEP)
    else:
        # Collapse consecutive runs of the same (component, event_type) pair.
        # Iterating newest-first so the displayed timestamp is the most recent.
        deduped: list[tuple[dict, int]] = []
        for entry in reversed(alerts[-n:]):
            key = (entry.get("component"), entry.get("event_type"))
            if deduped and (
                deduped[-1][0].get("component"),
                deduped[-1][0].get("event_type"),
            ) == key:
                deduped[-1] = (deduped[-1][0], deduped[-1][1] + 1)
            else:
                deduped.append((entry, 1))

        for entry, count in deduped:
            ts = entry.get("timestamp", "")[:19]
            sev = _pad(entry.get("severity", "?"), 8)
            comp = _pad(entry.get("component", "?"), 3)
            evt = entry.get("event_type", "?")
            suffix = f" ×{count}" if count > 1 else ""
            lines.append(_SEP + _pad(
                f"  {ts} {sev} {comp} {evt}{suffix}",
                _BOX_WIDTH,
            ) + _SEP)

    lines.append("└" + _HR + "┘")
    return lines


# ---------------------------------------------------------------------------
# Main render
# ---------------------------------------------------------------------------


def render_dashboard(
    health: dict[str, Any],
    audit_entries: list[dict[str, Any]],
    n_alerts: int = 20,
    t1_portfolio: dict[str, Any] | None = None,
    t4_portfolio: dict[str, Any] | None = None,
    pipeline_timestamps: dict[str, str] | None = None,
    game_date: str | None = None,
) -> str:
    """
    Render the full C8 dashboard.

    Parameters
    ----------
    health:
        Health snapshot dict (from C7 SystemMonitor or inferred from audit log).
    audit_entries:
        All entries from C6 audit log (kill switch state + alert feed).
    n_alerts:
        Number of recent alerts in Panel 5.
    t1_portfolio:
        Loaded paper_portfolio.json dict. None → panel shows "not found".
    t4_portfolio:
        Loaded paper_portfolio_t4.json dict. None → panel shows "no portfolio yet".
    pipeline_timestamps:
        {pipe_name: utc_str} from get_pipeline_timestamps(). None → falls back
        to audit.jsonl component timestamps in Panel 3.
    game_date:
        YYYY-MM-DD for throughput panel. Defaults to today UTC.
    """
    now = _utc_now_display()
    header = [
        "",
        "  PREDICTION MARKET BOT — C8 VISUAL DASHBOARD",
        f"  Rendered: {now}",
        "",
    ]

    component_last_seen = get_component_last_seen(audit_entries)
    alerts = get_recent_alerts(audit_entries, n=n_alerts)

    panel1 = render_portfolio_panel(t1_portfolio or {}, t4_portfolio or {})
    panel2 = render_throughput_panel(t1_portfolio or {}, t4_portfolio or {}, game_date)
    panel3 = render_system_health(health, component_last_seen, pipeline_timestamps)
    panel4 = render_drift_panel(health)
    panel5 = render_alert_feed(alerts, n=n_alerts)

    all_lines = (
        header
        + panel1 + [""]
        + panel2 + [""]
        + panel3 + [""]
        + panel4 + [""]
        + panel5 + [""]
    )
    return "\n".join(all_lines)


# ---------------------------------------------------------------------------
# CLI entrypoint
# ---------------------------------------------------------------------------


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="C8 Visual Dashboard — render portfolio state and system health"
    )
    parser.add_argument(
        "--log-path",
        default=os.environ.get("BOT_AUDIT_LOG_PATH", "logs/audit.jsonl"),
        help="Path to C6 audit log (kill switch state; default: logs/audit.jsonl)",
    )
    parser.add_argument(
        "--portfolio-path",
        default="logs/paper_portfolio.json",
        help="Path to T1 paper portfolio JSON (default: logs/paper_portfolio.json)",
    )
    parser.add_argument(
        "--t4-portfolio-path",
        default="logs/paper_portfolio_t4.json",
        help="Path to T4 paper portfolio JSON (default: logs/paper_portfolio_t4.json)",
    )
    parser.add_argument(
        "--log-dir",
        default="logs",
        help="Dir containing pipeline log files for activity timestamps (default: logs/)",
    )
    parser.add_argument(
        "--game-date",
        default=None,
        help="Game date for throughput panel YYYY-MM-DD (default: today UTC)",
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
    t1_portfolio = read_portfolio(args.portfolio_path)
    t4_portfolio = read_portfolio(args.t4_portfolio_path)
    pipeline_timestamps = get_pipeline_timestamps(args.log_dir)

    # Infer kill switch state from audit log (scan newest-first)
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
        t1_portfolio=t1_portfolio,
        t4_portfolio=t4_portfolio,
        pipeline_timestamps=pipeline_timestamps,
        game_date=args.game_date,
    )
    print(output)


if __name__ == "__main__":
    main()
