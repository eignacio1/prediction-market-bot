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
  6. T4 MLB Detail       — the T4 leg in full: evaluation funnel (raw cycle
                           context -> vig-skip -> gross edge -> net edge ->
                           C4 MIN_EDGE_TO_APPROVE -> approved -> fired),
                           re-entry vs first-entry breakdown (T-225), band
                           budget utilization, contamination guard health,
                           and sub-band registry status (T4M-PROJ ACTIVE vs
                           T4M-ARITH/T4M-FLOW BLOCKED). Added 2026-07-03
                           (post-T-225/226/227/228/229 confidence-gradient
                           follow-up) — see GG-076, TODO_NEXT.md T-231.
  7. Data Quality         — C1/C2 structural data contract results (GG-059
                           item 3, c1_signal_ingestion/validators.py's
                           emit_validation_result()): per-source_id HALT/WARN
                           status and recent failure detail, merged from the
                           main audit log (PIPE-05/PIPE-06pre) and
                           generate_mlb_features.py's own log (T187A). Added
                           2026-07-17 (T-381).

Data sources (in priority order):
  - logs/paper_portfolio.json              — T1 (NBA) portfolio state
  - logs/paper_portfolio_t4.json           — T4 (NBA) portfolio state (may not exist)
  - logs/paper_portfolio_mlb.json          — T1 MLB portfolio state (Panel 6 context)
  - logs/paper_portfolio_mlb_t4.json       — T4 MLB portfolio state (Panel 6)
  - logs/t4_mlb_cycle_log.jsonl            — T4 MLB per-cycle raw context (GG-067) — Panel 6 funnel
  - logs/audit_mlb_t4_edge_decisions.jsonl — T4 MLB C4 edge-decision sink (T-213/GG-060) — Panel 6 funnel
  - logs/audit_mlb_t4.jsonl                — T4 MLB C6 audit log (CONTAMINATION_HALT) — Panel 6 health
  - logs/audit.jsonl                       — kill switch state only; also carries
                                              PIPE-05/PIPE-06pre data_contract_*
                                              events (Panel 7)
  - exp_output/MLB/generate_features.jsonl — T187A's own data_contract_* events
                                              (Panel 7)
  - logs/*.log (file mtimes)               — pipeline last-run timestamps

Usage (CLI)::
    python -m prediction_market_bot.c8_dashboard.dashboard \\
        [--log-path logs/audit.jsonl] \\
        [--portfolio-path logs/paper_portfolio.json] \\
        [--t4-portfolio-path logs/paper_portfolio_t4.json] \\
        [--mlb-portfolio-path logs/paper_portfolio_mlb.json] \\
        [--t4-mlb-portfolio-path logs/paper_portfolio_mlb_t4.json] \\
        [--t4-mlb-cycle-log-path logs/t4_mlb_cycle_log.jsonl] \\
        [--t4-mlb-edge-log-path logs/audit_mlb_t4_edge_decisions.jsonl] \\
        [--t4-mlb-audit-log-path logs/audit_mlb_t4.jsonl] \\
        [--feature-gen-log-path exp_output/MLB/generate_features.jsonl] \\
        [--log-dir logs/] \\
        [--game-date YYYY-MM-DD] \\
        [--n-alerts 20]

The dashboard is stateless — each invocation reads current files and renders.
Every panel degrades gracefully: any missing file, or a source with zero
matching events, renders as "not found" / "no data for this window" for
that section rather than failing the whole dashboard render.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_SRC_ROOT = Path(__file__).resolve().parents[2]
if str(_SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(_SRC_ROOT))

# Panel 6 (T4 MLB Detail) dependencies. Wrapped defensively — the dashboard's
# design contract is "any missing file/import degrades that section, never
# crashes the whole render" (see module docstring). execution_bands.py is
# stdlib-only (safe); c4_risk_engine.risk pulls in pandas/jsonlines, which
# are already dashboard-adjacent dependencies but are guarded anyway so a
# broken venv on one component doesn't take down Panels 1-5.
try:
    from prediction_market_bot.execution_bands import (
        ExecutionBand as _ExecutionBand,
        T4_MLB_SUBBAND_REGISTRY as _T4_MLB_SUBBAND_REGISTRY,
    )
    from prediction_market_bot.c4_risk_engine.risk import (
        MIN_EDGE_TO_APPROVE as _MIN_EDGE_TO_APPROVE,
        summarize_edge_run as _summarize_edge_run,
    )
    _PANEL6_IMPORTS_OK = True
except Exception:  # pragma: no cover — defensive; see comment above
    _ExecutionBand = None
    _T4_MLB_SUBBAND_REGISTRY = None
    _MIN_EDGE_TO_APPROVE = 0.04
    _summarize_edge_run = None
    _PANEL6_IMPORTS_OK = False

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


def _positions_for_date(positions: list[dict[str, Any]], date_str: str) -> list[dict[str, Any]]:
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


def _player_breakdown(positions: list[dict[str, Any]], max_players: int = 5) -> str:
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
        deduped: list[tuple[dict[str, Any], int]] = []
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
# Panel 6 — T4 MLB Detail (the T4 leg in its entirety)
# ---------------------------------------------------------------------------
#
# Added 2026-07-03 as a direct follow-up to the T4 MLB throughput diagnosis
# (GG-076) and the T-225/226/227/228/229 remediation batch. Panels 1-2 only
# ever showed T4 as an aggregate bet count; this panel exposes the full
# evaluation funnel and sub-band governance state so "is T4 running at
# optimum" (correct math/filtering/decision trees/execution paths — not a
# P&L claim, per the operator's own definition) is answerable from one view
# instead of grepping four separate log files by hand.
#
# Every reader below is defensive: a missing/unreadable file renders its
# section as "not found," it never raises out of render_t4_detail_panel().


def read_jsonl_generic(path: str | Path) -> list[dict[str, Any]]:
    """Read any JSONL file into a list of dicts. Returns [] if missing/unreadable.

    Generic version of read_audit_log() — same tolerant-parse behavior
    (skips blank lines and malformed JSON lines rather than failing the
    whole read), used for the T4 MLB cycle log and edge-decision sink,
    which are not C6 audit-log-shaped but are line-delimited JSON the same
    way.
    """
    p = Path(path)
    if not p.exists():
        return []
    entries: list[dict[str, Any]] = []
    try:
        with open(p) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    except OSError:
        return []
    return entries


def _t4_cycle_log_for_date(cycle_entries: list[dict[str, Any]], game_date: str) -> list[dict[str, Any]]:
    """Filter t4_mlb_cycle_log.jsonl rows to a single game_date."""
    return [r for r in cycle_entries if r.get("game_date") == game_date]


def compute_t4_funnel_stats(cycle_entries: list[dict[str, Any]]) -> dict[str, Any]:
    """
    Reconstruct the T4 MLB evaluation funnel from raw per-cycle context
    (GG-067's cycle log — written for every ctx that reaches the p_t4/edge
    computation, independent of dry-run/fired status).

    Funnel stages, most permissive to least:
      total            — every row in the cycle log for this date
      vig_skipped      — T-228's pre-filter: vig > VIG_CEILING, never reached
                          the Binomial/C4 evaluation cost at all
      evaluated        — total - vig_skipped (rows that got a real p_t4)
      gross_edge_pos   — gross_edge > 0 (before Kalshi taker fee)
      net_edge_pos     — net_edge > 0 (after fee, before C4's MIN_EDGE gate)
      net_edge_min     — net_edge >= MIN_EDGE_TO_APPROVE (the real C4-eligible
                          threshold — this is what actually reaches C4, not
                          net_edge_pos)
    Also returns vig distribution (mean/median/max) over non-skipped rows,
    since a fat-tailed vig distribution was T-228's whole rationale.
    """
    total = len(cycle_entries)
    vig_skipped = sum(1 for r in cycle_entries if r.get("vig_skip") is True)
    scored = [r for r in cycle_entries if r.get("vig_skip") is not True and "p_t4" in r]
    evaluated = len(scored)
    gross_pos = sum(1 for r in scored if (r.get("gross_edge") or 0.0) > 0.0)
    net_pos = sum(1 for r in scored if (r.get("net_edge") or 0.0) > 0.0)
    net_min = sum(1 for r in scored if (r.get("net_edge") or 0.0) >= _MIN_EDGE_TO_APPROVE)

    vigs = [r["vig"] for r in scored if isinstance(r.get("vig"), (int, float))]
    vig_stats: dict[str, float | None] = {"mean": None, "median": None, "max": None}
    if vigs:
        vigs_sorted = sorted(vigs)
        n = len(vigs_sorted)
        vig_stats["mean"] = sum(vigs_sorted) / n
        vig_stats["median"] = vigs_sorted[n // 2]
        vig_stats["max"] = vigs_sorted[-1]

    return {
        "total": total,
        "vig_skipped": vig_skipped,
        "evaluated": evaluated,
        "gross_edge_pos": gross_pos,
        "net_edge_pos": net_pos,
        "net_edge_min_approve": net_min,
        "vig_stats": vig_stats,
    }


def compute_t4_reentry_stats(t4_positions_today: list[dict[str, Any]]) -> dict[str, Any]:
    """
    Split today's T4 MLB positions into first-entries vs re-entries per
    ticker (T-225 — re-entry is only possible post-deploy; pre-T-225
    positions are all first-entries by construction since re-entry didn't
    exist yet). Positions are read in list order, which PaperTrader appends
    in chronologically, so the first time a ticker is seen this call is its
    first entry.
    """
    seen: dict[str, int] = {}
    for p in t4_positions_today:
        ticker = p.get("kalshi_ticker") or "?"
        seen[ticker] = seen.get(ticker, 0) + 1

    unique_tickers = len(seen)
    first_entries = unique_tickers
    re_entries = sum(c - 1 for c in seen.values() if c > 1)
    tickers_with_reentry = sum(1 for c in seen.values() if c > 1)
    max_entries_one_ticker = max(seen.values()) if seen else 0

    return {
        "unique_tickers": unique_tickers,
        "first_entries": first_entries,
        "re_entries": re_entries,
        "tickers_with_reentry": tickers_with_reentry,
        "max_entries_one_ticker": max_entries_one_ticker,
    }


def compute_t4_contamination_stats(
    audit_entries: list[dict[str, Any]],
    game_date: str | None = None,
) -> dict[str, Any]:
    """
    Read CONTAMINATION_HALT events from the T4 MLB C6 audit log
    (LiveDataFreshnessGuard.check() in run_t4_mlb_live.py). Zero
    staleness_halts is healthy; market_active halts are expected/benign at
    game end. Uses the running total_halts/staleness_halts counters each
    event already carries (session-cumulative), taking the max seen rather
    than summing, since each event already reports the session total.
    """
    halts = [e for e in audit_entries if e.get("event_type") == "CONTAMINATION_HALT"]
    if game_date:
        halts = [h for h in halts if (h.get("timestamp") or "").startswith(game_date)]
    total_halts = 0
    staleness_halts = 0
    failed_check_counts: dict[str, int] = {}
    for h in halts:
        payload = h.get("payload") or {}
        total_halts = max(total_halts, int(payload.get("total_halts") or 0))
        staleness_halts = max(staleness_halts, int(payload.get("staleness_halts") or 0))
        for fc in payload.get("failed_checks") or []:
            failed_check_counts[fc] = failed_check_counts.get(fc, 0) + 1
    return {
        "event_count": len(halts),
        "total_halts": total_halts,
        "staleness_halts": staleness_halts,
        "failed_check_counts": failed_check_counts,
    }


def render_t4_subband_registry() -> list[str]:
    """Static sub-band governance table (execution_bands.T4_MLB_SUBBAND_REGISTRY).

    Not date-scoped — reflects code state, not today's activity. Shows every
    registered MLB T4 sub-band's activation status so "is T4 running at
    optimum" includes "is anything BLOCKED that shouldn't be, or ACTIVE that
    shouldn't be" — not just throughput.
    """
    lines: list[str] = []
    if not _PANEL6_IMPORTS_OK or _T4_MLB_SUBBAND_REGISTRY is None:
        lines.append(_SEP + _pad(
            "    Sub-band registry: import failed — execution_bands.py unavailable.",
            _BOX_WIDTH,
        ) + _SEP)
        return lines

    lines.append(_SEP + _pad("    Sub-band registry (execution_bands.T4_MLB_SUBBAND_REGISTRY):", _BOX_WIDTH) + _SEP)
    for band, spec in _T4_MLB_SUBBAND_REGISTRY.items():
        status = getattr(spec, "status", "?")
        tag = "ACTIVE " if status == "ACTIVE" else "BLOCKED"
        gate = ", ".join(getattr(spec, "exp_gate", ()) or ()) or "—"
        kelly = getattr(spec, "provisional_kelly", None)
        kelly_str = f"{kelly:.2f}" if isinstance(kelly, (int, float)) else "n/a"
        lines.append(_SEP + _pad(
            f"      [{tag}] {band.value:<10}  kelly={kelly_str}  exp_gate={gate}",
            _BOX_WIDTH,
        ) + _SEP)
    return lines


def render_t4_detail_panel(
    t4_mlb_portfolio: dict[str, Any],
    cycle_entries: list[dict[str, Any]],
    t4_audit_entries: list[dict[str, Any]],
    edge_log_path: str | Path | None,
    game_date: str | None = None,
) -> list[str]:
    """
    Panel 6: T4 MLB leg in full — evaluation funnel, re-entry breakdown, band
    budget, contamination guard health, and sub-band registry status.

    Every section degrades independently: a missing/empty source renders
    "not found for this section," it does not blank the whole panel.
    """
    gd = game_date or _today_str()
    lines: list[str] = []
    lines.append("┌" + _HR + "┐")
    lines.append(_SEP + _pad(f" PANEL 6 — T4 MLB DETAIL  ({gd})", _BOX_WIDTH) + _SEP)
    lines.append("├" + _HR + "┤")

    # --- Section A: session/service freshness ---
    day_cycles = _t4_cycle_log_for_date(cycle_entries, gd)
    if day_cycles:
        sessions_today = sorted({r.get("session_id", "?") for r in day_cycles})
        last_ts = max((r.get("ts") or "" for r in day_cycles), default="")
        cycle_ids_today = {r.get("cycle_id") for r in day_cycles}
        lines.append(_SEP + _pad(
            f"  Sessions today: {len(sessions_today)}  │  Cycles: {len(cycle_ids_today)}"
            f"  │  Last write: {last_ts[:19] or 'n/a'}",
            _BOX_WIDTH,
        ) + _SEP)
    else:
        lines.append(_SEP + _pad(
            f"  No cycle-log activity for {gd} yet (t4_mlb_cycle_log.jsonl).", _BOX_WIDTH
        ) + _SEP)

    lines.append(_SEP + _pad("", _BOX_WIDTH) + _SEP)

    # --- Section B: evaluation funnel ---
    lines.append(_SEP + _pad("  Evaluation funnel (raw cycle log):", _BOX_WIDTH) + _SEP)
    if day_cycles:
        f = compute_t4_funnel_stats(day_cycles)
        lines.append(_SEP + _pad(
            f"    Total rows {f['total']}  │  Vig-skipped {f['vig_skipped']}"
            f"  │  Evaluated {f['evaluated']}",
            _BOX_WIDTH,
        ) + _SEP)
        lines.append(_SEP + _pad(
            f"    Gross edge>0: {f['gross_edge_pos']}  │  Net edge>0: {f['net_edge_pos']}"
            f"  │  Net edge>=MIN({_MIN_EDGE_TO_APPROVE:.2f}): {f['net_edge_min_approve']}",
            _BOX_WIDTH,
        ) + _SEP)
        vs = f["vig_stats"]
        if vs["mean"] is not None:
            lines.append(_SEP + _pad(
                f"    Vig (non-skipped): mean={vs['mean']:.3f}  median={vs['median']:.3f}  max={vs['max']:.3f}",
                _BOX_WIDTH,
            ) + _SEP)
    else:
        lines.append(_SEP + _pad("    No data — see session/service line above.", _BOX_WIDTH) + _SEP)

    # --- Section B2: C4-side funnel (evaluate_forecast's own view) ---
    if edge_log_path is not None and _summarize_edge_run is not None:
        try:
            edge_summary = _summarize_edge_run(edge_log_path)
        except Exception:
            edge_summary = None
        if edge_summary:
            lines.append(_SEP + _pad(
                f"    C4 view: evals={edge_summary.get('total_evaluations', 0)}"
                f"  edge_signals={edge_summary.get('edge_signals_found', 0)}"
                f"  approved={edge_summary.get('bets_approved', 0)}"
                f"  state={edge_summary.get('run_state', '?')}",
                _BOX_WIDTH,
            ) + _SEP)
            if edge_summary.get("silent_success_flag"):
                lines.append(_SEP + _pad(
                    "    *** SILENT_SUCCESS_FLAG: >=50 evals, 0 edge signals — check upstream. ***",
                    _BOX_WIDTH,
                ) + _SEP)

    lines.append(_SEP + _pad("", _BOX_WIDTH) + _SEP)

    # --- Section C: fire / re-entry / budget ---
    lines.append(_SEP + _pad("  Positions fired (re-entry breakdown, T-225):", _BOX_WIDTH) + _SEP)
    if not t4_mlb_portfolio:
        lines.append(_SEP + _pad("    paper_portfolio_mlb_t4.json not found.", _BOX_WIDTH) + _SEP)
    else:
        s4 = _compute_portfolio_stats(t4_mlb_portfolio)
        t4_today = _positions_for_date(s4["open_pos"], gd) + _positions_for_date(s4["closed_pos"], gd)
        if not t4_today:
            lines.append(_SEP + _pad(f"    0 positions for {gd}.", _BOX_WIDTH) + _SEP)
        else:
            r = compute_t4_reentry_stats(t4_today)
            lines.append(_SEP + _pad(
                f"    Total fired: {len(t4_today)}  │  Unique tickers: {r['unique_tickers']}"
                f"  │  Re-entries: {r['re_entries']} (on {r['tickers_with_reentry']} tickers)",
                _BOX_WIDTH,
            ) + _SEP)
            if r["max_entries_one_ticker"] > 1:
                lines.append(_SEP + _pad(
                    f"    Max entries on one ticker today: {r['max_entries_one_ticker']}",
                    _BOX_WIDTH,
                ) + _SEP)

        bankroll = float(t4_mlb_portfolio.get("bankroll_usd") or 0.0)
        band_budget = bankroll * 0.27  # T4_BAND_WEIGHT, ADR-0023 — mirrors run_t4_mlb_live.py
        deployed_today = sum(
            float(p.get("size_usd") or 0.0)
            for p in _positions_for_date(s4["open_pos"], gd)
        )
        budget_bar = _bar(deployed_today, 0.0, band_budget) if band_budget > 0 else "[n/a]"
        lines.append(_SEP + _pad(
            f"    Band budget: ${deployed_today:.2f} / ${band_budget:.2f} {budget_bar}",
            _BOX_WIDTH,
        ) + _SEP)

    lines.append(_SEP + _pad("", _BOX_WIDTH) + _SEP)

    # --- Section D: contamination guard health ---
    cg = compute_t4_contamination_stats(t4_audit_entries, game_date=gd)
    health_tag = "OK" if cg["staleness_halts"] == 0 else "*** STALENESS DETECTED ***"
    lines.append(_SEP + _pad(
        f"  Contamination guard [{health_tag}]: halts={cg['total_halts']}"
        f"  staleness_halts={cg['staleness_halts']}  events={cg['event_count']}",
        _BOX_WIDTH,
    ) + _SEP)
    if cg["failed_check_counts"]:
        checks_str = "  ".join(f"{k}×{v}" for k, v in sorted(cg["failed_check_counts"].items()))
        lines.append(_SEP + _pad(f"    Failed checks: {checks_str}", _BOX_WIDTH) + _SEP)

    lines.append(_SEP + _pad("", _BOX_WIDTH) + _SEP)

    # --- Section E: sub-band registry (static, not date-scoped) ---
    lines.extend(render_t4_subband_registry())

    lines.append("└" + _HR + "┘")
    return lines


# ---------------------------------------------------------------------------
# Panel 7 — Data Quality (C1/C2 Contracts, GG-059 item 3)
# ---------------------------------------------------------------------------

_DATA_QUALITY_EVENT_TYPES = {"data_contract_violation", "data_contract_ok"}


def compute_data_quality_stats(
    entries: list[dict[str, Any]],
    game_date: str | None = None,
) -> dict[str, Any]:
    """
    Summarize C1/C2 structural data contract results (GG-059/T-212,
    c1_signal_ingestion/validators.py's emit_validation_result()) from any
    C6-shaped audit log/JSONL source.

    A source_id's status is the worst severity seen across this window
    (HALT > WARN > OK), not just the single latest event — one validation
    run emits one event per failure (assert_contract calls emit_validation_
    result once per ContractFailure), so "the last event by timestamp" can
    land on an arbitrary WARN sibling of a HALT from the same run. Counting
    per-source across the window answers "should I be worried about this
    source" directly. A source_id absent from this window has not run in
    it — that is distinct from having passed, and is shown as such by simply
    not appearing.
    """
    dq_events = [e for e in entries if e.get("event_type") in _DATA_QUALITY_EVENT_TYPES]
    if game_date:
        dq_events = [e for e in dq_events if (e.get("timestamp") or "").startswith(game_date)]

    per_source: dict[str, dict[str, Any]] = {}
    recent_failures: list[dict[str, Any]] = []

    for e in dq_events:
        payload = e.get("payload") or {}
        source_id = payload.get("source_id") or "?"
        ts = e.get("timestamp") or ""
        rec = per_source.setdefault(source_id, {
            "n_ok": 0, "n_halt": 0, "n_warn": 0,
            "last_ts": "", "last_row_count": None, "pipeline_id": "?",
        })
        if ts >= rec["last_ts"]:
            rec["last_ts"] = ts
            rec["last_row_count"] = payload.get("row_count")
            rec["pipeline_id"] = e.get("component") or "?"

        if e.get("event_type") == "data_contract_ok":
            rec["n_ok"] += 1
        else:
            sev = payload.get("severity")
            if sev == "HALT":
                rec["n_halt"] += 1
            elif sev == "WARN":
                rec["n_warn"] += 1
            recent_failures.append({
                "ts": ts,
                "source_id": source_id,
                "check_type": payload.get("check_type") or "?",
                "severity": sev or "?",
                "reason": payload.get("reason") or "",
                "pipeline_id": e.get("component") or "?",
            })

    recent_failures.sort(key=lambda f: f["ts"])
    n_halt = sum(r["n_halt"] for r in per_source.values())
    n_warn = sum(r["n_warn"] for r in per_source.values())

    return {
        "per_source": per_source,
        "n_sources": len(per_source),
        "n_halt": n_halt,
        "n_warn": n_warn,
        "recent_failures": recent_failures[-8:],
    }


def render_data_quality_panel(
    entries: list[dict[str, Any]],
    game_date: str | None = None,
) -> list[str]:
    """
    Panel 7: C1/C2 data contract validation status (GG-059 item 3).

    Degrades the same way as every other panel: zero data_contract_* events
    in the source logs renders "no data quality events for this window"
    rather than an empty or crashing panel — that is the expected state on
    a day no C1/C2 pipeline has called assert_contract() yet, not
    necessarily a failure.
    """
    gd = game_date or _today_str()
    lines: list[str] = []
    lines.append("┌" + _HR + "┐")
    lines.append(_SEP + _pad(f" PANEL 7 — DATA QUALITY (C1/C2 CONTRACTS)  ({gd})", _BOX_WIDTH) + _SEP)
    lines.append("├" + _HR + "┤")

    stats = compute_data_quality_stats(entries, game_date=gd)

    if stats["n_sources"] == 0:
        lines.append(_SEP + _pad(
            "  No data_contract_violation/data_contract_ok events for this window.",
            _BOX_WIDTH,
        ) + _SEP)
        lines.append("└" + _HR + "┘")
        return lines

    health_tag = "OK" if stats["n_halt"] == 0 else "*** HALT FAILURES DETECTED ***"
    lines.append(_SEP + _pad(
        f"  [{health_tag}] Sources: {stats['n_sources']}"
        f"  │  HALT: {stats['n_halt']}  │  WARN: {stats['n_warn']}",
        _BOX_WIDTH,
    ) + _SEP)
    lines.append(_SEP + _pad("", _BOX_WIDTH) + _SEP)

    for source_id, rec in sorted(stats["per_source"].items()):
        if rec["n_halt"] > 0:
            tag = "HALT"
        elif rec["n_warn"] > 0:
            tag = "WARN"
        else:
            tag = " OK "
        lines.append(_SEP + _pad(
            f"  [{tag}] {source_id:<28} pipeline={rec['pipeline_id']:<10}"
            f" rows={rec['last_row_count']}  last={rec['last_ts'][:19] or 'n/a'}",
            _BOX_WIDTH,
        ) + _SEP)

    if stats["recent_failures"]:
        lines.append(_SEP + _pad("", _BOX_WIDTH) + _SEP)
        lines.append(_SEP + _pad("  Recent failures:", _BOX_WIDTH) + _SEP)
        for f in stats["recent_failures"]:
            lines.append(_SEP + _pad(
                f"    {f['ts'][:19]} [{f['severity']}] {f['source_id']}/{f['check_type']}: {f['reason']}",
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
    t4_mlb_portfolio: dict[str, Any] | None = None,
    t4_mlb_cycle_entries: list[dict[str, Any]] | None = None,
    t4_mlb_audit_entries: list[dict[str, Any]] | None = None,
    t4_mlb_edge_log_path: str | Path | None = None,
    show_t4_mlb_detail: bool = True,
    data_quality_entries: list[dict[str, Any]] | None = None,
    show_data_quality: bool = True,
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
        Loaded paper_portfolio.json dict (NBA). None → panel shows "not found".
    t4_portfolio:
        Loaded paper_portfolio_t4.json dict (NBA). None → panel shows "no portfolio yet".
    pipeline_timestamps:
        {pipe_name: utc_str} from get_pipeline_timestamps(). None → falls back
        to audit.jsonl component timestamps in Panel 3.
    game_date:
        YYYY-MM-DD for throughput panel. Defaults to today UTC.
    t4_mlb_portfolio:
        Loaded paper_portfolio_mlb_t4.json dict. Feeds Panel 6 fire/re-entry/budget.
    t4_mlb_cycle_entries:
        Rows from t4_mlb_cycle_log.jsonl (via read_jsonl_generic). Feeds Panel 6 funnel.
    t4_mlb_audit_entries:
        Rows from audit_mlb_t4.jsonl (via read_jsonl_generic). Feeds Panel 6 contamination health.
    t4_mlb_edge_log_path:
        Path to audit_mlb_t4_edge_decisions.jsonl, passed through to
        summarize_edge_run() for Panel 6's C4-side funnel view.
    show_t4_mlb_detail:
        If False, Panel 6 is omitted entirely (e.g. for a lighter-weight render).
        Default True — T4 MLB is the active pool.
    data_quality_entries:
        Combined rows from any C6-shaped audit logs carrying C1/C2
        data_contract_violation / data_contract_ok events (GG-059 item 3) —
        typically the main audit log plus scripts/generate_mlb_features.py's
        own log. Feeds Panel 7. None/[] renders "no events for this window".
    show_data_quality:
        If False, Panel 7 is omitted entirely. Default True.
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

    if show_t4_mlb_detail:
        panel6 = render_t4_detail_panel(
            t4_mlb_portfolio=t4_mlb_portfolio or {},
            cycle_entries=t4_mlb_cycle_entries or [],
            t4_audit_entries=t4_mlb_audit_entries or [],
            edge_log_path=t4_mlb_edge_log_path,
            game_date=game_date,
        )
        all_lines = all_lines + panel6 + [""]

    if show_data_quality:
        panel7 = render_data_quality_panel(
            entries=data_quality_entries or [],
            game_date=game_date,
        )
        all_lines = all_lines + panel7 + [""]

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
        help="Path to T4 (NBA) paper portfolio JSON (default: logs/paper_portfolio_t4.json)",
    )
    parser.add_argument(
        "--t4-mlb-portfolio-path",
        default="logs/paper_portfolio_mlb_t4.json",
        help="Path to T4 MLB paper portfolio JSON, feeds Panel 6 "
             "(default: logs/paper_portfolio_mlb_t4.json)",
    )
    parser.add_argument(
        "--t4-mlb-cycle-log-path",
        default="logs/t4_mlb_cycle_log.jsonl",
        help="Path to T4 MLB per-cycle raw context log (GG-067), feeds Panel 6's "
             "evaluation funnel (default: logs/t4_mlb_cycle_log.jsonl)",
    )
    parser.add_argument(
        "--t4-mlb-edge-log-path",
        default="logs/audit_mlb_t4_edge_decisions.jsonl",
        help="Path to T4 MLB C4 edge-decision sink (T-213/GG-060), feeds Panel 6's "
             "C4-side funnel view (default: logs/audit_mlb_t4_edge_decisions.jsonl)",
    )
    parser.add_argument(
        "--t4-mlb-audit-log-path",
        default="logs/audit_mlb_t4.jsonl",
        help="Path to T4 MLB C6 audit log, feeds Panel 6's contamination guard health "
             "(default: logs/audit_mlb_t4.jsonl)",
    )
    parser.add_argument(
        "--no-t4-mlb-detail",
        action="store_true",
        help="Omit Panel 6 (T4 MLB Detail) from the render",
    )
    parser.add_argument(
        "--feature-gen-log-path",
        default="exp_output/MLB/generate_features.jsonl",
        help="Path to scripts/generate_mlb_features.py's own C6 audit log "
             "(pipeline_id=T187A), feeds Panel 7 alongside --log-path "
             "(default: exp_output/MLB/generate_features.jsonl)",
    )
    parser.add_argument(
        "--no-data-quality",
        action="store_true",
        help="Omit Panel 7 (Data Quality / C1-C2 Contracts) from the render",
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

    # Panel 6 (T4 MLB Detail) data sources — read defensively, same "missing
    # file degrades that section, never crashes the render" contract as
    # everything else in this module.
    t4_mlb_portfolio = read_portfolio(args.t4_mlb_portfolio_path)
    t4_mlb_cycle_entries = read_jsonl_generic(args.t4_mlb_cycle_log_path)
    t4_mlb_audit_entries = read_jsonl_generic(args.t4_mlb_audit_log_path)

    # Panel 7 (Data Quality) data sources — C1/C2 assert_contract() results
    # live in the main audit log (PIPE-05/PIPE-06pre, already read above as
    # audit_entries) plus generate_mlb_features.py's own separate log
    # (pipeline_id=T187A). Both are C6-shaped, so they merge directly.
    feature_gen_entries = read_jsonl_generic(args.feature_gen_log_path)
    data_quality_entries = audit_entries + feature_gen_entries

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
        t4_mlb_portfolio=t4_mlb_portfolio,
        t4_mlb_cycle_entries=t4_mlb_cycle_entries,
        t4_mlb_audit_entries=t4_mlb_audit_entries,
        t4_mlb_edge_log_path=args.t4_mlb_edge_log_path,
        show_t4_mlb_detail=not args.no_t4_mlb_detail,
        data_quality_entries=data_quality_entries,
        show_data_quality=not args.no_data_quality,
    )
    print(output)


if __name__ == "__main__":
    main()
