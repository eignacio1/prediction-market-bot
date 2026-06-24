#!/usr/bin/env python3
"""
MLB Paper Trade Dashboard — Bloomberg Terminal Style
====================================================
Pipeline:  MLB paper trading (PIPE-05/05R/05FX/05C)
Data:      logs/paper_portfolio_mlb.json  +  logs/audit_mlb.jsonl
Refresh:   every --interval seconds (default 60); --once to render once and exit

Usage:
    python scripts/run_mlb_dashboard.py
    python scripts/run_mlb_dashboard.py --interval 30
    python scripts/run_mlb_dashboard.py --once

Crash resistance:
  - No curses: plain terminal clear + print (no ncurses state corruption)
  - All file I/O guarded with try/except
  - Each panel independently guarded: one bad panel never kills the render
  - Main loop catches all exceptions, shows last error inline, keeps running
  - Only exits on Ctrl+C
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import signal
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Paths (resolved relative to project root, overridable via env)
# ---------------------------------------------------------------------------

_HERE = Path(__file__).resolve().parent
_ROOT = _HERE.parent

LOG_DIR      = Path(os.environ.get("LOG_DIR",      str(_ROOT / "logs")))
PORTFOLIO    = Path(os.environ.get("MLB_PORTFOLIO", str(LOG_DIR / "paper_portfolio_mlb.json")))
AUDIT_LOG    = Path(os.environ.get("MLB_AUDIT",     str(LOG_DIR / "audit_mlb.jsonl")))

# PIPE-05 cron log files (names from deploy/cron.conf)
_PIPE_LOGS: dict[str, str] = {
    "PIPE-05  (23:30Z)":  "paper_mlb_cron.log",
    "PIPE-05R (06:30Z)":  "resolve_mlb_cron.log",
    "PIPE-05FX(22:30Z)":  "mlb_feature_refresh.log",
    "PIPE-05C (Mon14Z)":  "mlb_calib_monitor.log",
}

# ANSI codes — all wrapped so they degrade cleanly if not a tty
def _c(code: str, text: str) -> str:
    if sys.stdout.isatty():
        return f"\033[{code}m{text}\033[0m"
    return text

def _green(t: str)  -> str: return _c("32", t)
def _red(t: str)    -> str: return _c("31;1", t)
def _yellow(t: str) -> str: return _c("33", t)
def _cyan(t: str)   -> str: return _c("36", t)
def _bold(t: str)   -> str: return _c("1", t)
def _dim(t: str)    -> str: return _c("2", t)


# ---------------------------------------------------------------------------
# Terminal geometry
# ---------------------------------------------------------------------------

def _term_width() -> int:
    w = shutil.get_terminal_size(fallback=(120, 40)).columns
    return max(80, min(w - 2, 220))


# ---------------------------------------------------------------------------
# Box drawing helpers
# ---------------------------------------------------------------------------

def _hr(w: int, c: str = "─") -> str:
    return c * w

def _box_top(w: int, label: str = "") -> str:
    if label:
        inner = f" {label} "
        rest = w - len(inner) - 2
        left = rest // 2
        right = rest - left
        return "┌" + "─" * left + inner + "─" * right + "┐"
    return "┌" + _hr(w) + "┐"

def _box_bot(w: int) -> str:
    return "└" + _hr(w) + "┘"

def _box_mid(w: int) -> str:
    return "├" + _hr(w) + "┤"

def _row(content: str, w: int) -> str:
    """Pad or truncate content to exactly w chars, wrapped in │…│."""
    visible = _strip_ansi(content)
    # ansi codes add invisible chars; adjust padding by the invisible byte count
    padding = w - len(visible)
    if padding < 0:
        # truncate visible portion, keeping leading ansi if present
        content = _truncate_ansi(content, w)
        padding = 0
    return "│" + content + " " * padding + "│"

def _blank_row(w: int) -> str:
    return "│" + " " * w + "│"

def _strip_ansi(s: str) -> str:
    import re
    return re.sub(r"\033\[[0-9;]*m", "", s)

def _truncate_ansi(s: str, max_visible: int) -> str:
    """Truncate string to max_visible visible chars, preserving ansi codes."""
    import re
    result = []
    visible = 0
    i = 0
    while i < len(s):
        if s[i] == "\033":
            # consume the full escape sequence
            j = s.find("m", i)
            if j == -1:
                break
            result.append(s[i:j+1])
            i = j + 1
        else:
            if visible >= max_visible:
                break
            result.append(s[i])
            visible += 1
            i += 1
    return "".join(result)

def _col(text: str, width: int, align: str = "left") -> str:
    """Format a column value: truncate or pad to exactly width visible chars."""
    visible = _strip_ansi(str(text))
    if len(visible) > width:
        visible = visible[:width - 1] + "…"
        text = visible
    else:
        if align == "right":
            text = " " * (width - len(visible)) + str(text)
        elif align == "center":
            pad = width - len(visible)
            text = " " * (pad // 2) + str(text) + " " * (pad - pad // 2)
        else:
            text = str(text) + " " * (width - len(visible))
    return text


# ---------------------------------------------------------------------------
# File readers
# ---------------------------------------------------------------------------

def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text())
    except Exception:
        return {}

def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    entries = []
    try:
        with open(path) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    except Exception:
        pass
    return entries

def _pipe_timestamps() -> dict[str, str]:
    result: dict[str, str] = {}
    for label, fname in _PIPE_LOGS.items():
        p = LOG_DIR / fname
        if p.exists():
            try:
                mtime = p.stat().st_mtime
                dt = datetime.fromtimestamp(mtime, tz=timezone.utc)
                result[label] = dt.strftime("%Y-%m-%dT%H:%M:%SZ")
            except Exception:
                result[label] = "error reading mtime"
        else:
            result[label] = "no log yet"
    return result


# ---------------------------------------------------------------------------
# Portfolio helpers
# ---------------------------------------------------------------------------

def _position_pnl(p: dict) -> float:
    """GG-034: sum pnl + exit_pnl."""
    return float(p.get("pnl", 0.0)) + float(p.get("exit_pnl", 0.0))

def _portfolio_stats(port: dict) -> dict:
    bankroll = float(port.get("bankroll_usd") or 0.0)
    initial  = float(port.get("initial_bankroll_usd") or bankroll or 1000.0)
    # Use ledger-derived P&L if we have positions, else trust stored scalar
    open_pos   = port.get("open_positions",   [])
    closed_pos = port.get("closed_positions", [])
    if isinstance(open_pos,   dict): open_pos   = list(open_pos.values())
    if isinstance(closed_pos, dict): closed_pos = list(closed_pos.values())

    closed_pnl = sum(_position_pnl(p) for p in closed_pos
                     if not p.get("pool_isolated"))
    open_cost  = sum(float(p.get("size_usd", 0.0)) for p in open_pos
                     if not p.get("pool_isolated"))
    derived_bankroll = round(initial + closed_pnl - open_cost, 4)
    pnl = round(initial + closed_pnl - initial, 4)   # = closed_pnl

    deployed    = sum(float(p.get("size_usd", 0.0)) for p in open_pos)
    deployed_pct = deployed / initial * 100 if initial else 0.0
    reserve     = bankroll - deployed

    wins   = sum(1 for p in closed_pos if p.get("outcome") == "WIN")
    losses = sum(1 for p in closed_pos if p.get("outcome") in ("LOSS", "LOSE"))
    n_closed = len(closed_pos)
    win_rate = wins / n_closed if n_closed else None
    drawdown = max(0.0, -pnl / initial * 100) if initial else 0.0
    pnl_pct  = pnl / initial * 100 if initial else 0.0

    return {
        "bankroll": bankroll, "initial": initial, "pnl": pnl,
        "pnl_pct": pnl_pct, "drawdown": drawdown,
        "open_pos": open_pos, "closed_pos": closed_pos,
        "n_open": len(open_pos), "n_closed": n_closed,
        "wins": wins, "losses": losses,
        "win_rate": win_rate,
        "deployed": deployed, "deployed_pct": deployed_pct, "reserve": reserve,
        "derived_bankroll": derived_bankroll,
    }

def _today_str() -> str:
    return datetime.now(tz=timezone.utc).strftime("%Y-%m-%d")

def _utcnow() -> str:
    return datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

def _since(ts_str: str) -> str:
    """Human-readable elapsed time since an ISO timestamp."""
    try:
        dt = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
        secs = int((datetime.now(tz=timezone.utc) - dt).total_seconds())
        if secs < 60:    return f"{secs}s ago"
        if secs < 3600:  return f"{secs//60}m ago"
        if secs < 86400: return f"{secs//3600}h {(secs%3600)//60}m ago"
        return f"{secs//86400}d ago"
    except Exception:
        return "?"

def _fmt_pnl(v: float) -> str:
    sign = "+" if v >= 0 else ""
    s = f"{sign}${v:.2f}"
    return _green(s) if v >= 0 else _red(s)

def _fmt_edge(v: float) -> str:
    s = f"{v:+.3f}"
    return _green(s) if v > 0 else (_red(s) if v < -0.01 else _yellow(s))

def _fmt_threshold(t: Any) -> str:
    try:
        return f"H≥{int(t)}"
    except Exception:
        return str(t)


# ---------------------------------------------------------------------------
# Panel: Header
# ---------------------------------------------------------------------------

def render_header(w: int) -> list[str]:
    now = _utcnow()
    env = os.environ.get("BOT_ENV", "paper").upper()
    vps = "157.230.91.33"
    lines = []
    lines.append("═" * (w + 2))
    title = _bold(_cyan("  MLB PAPER TRADE TERMINAL  ─  PREDICTION MARKET BOT"))
    meta  = f"  {now}   BOT_ENV={env}   VPS {vps}   G6 OPEN"
    lines.append(_row(title, w))
    lines.append(_row(meta, w))
    lines.append("═" * (w + 2))
    return lines


# ---------------------------------------------------------------------------
# Panel: Portfolio Summary
# ---------------------------------------------------------------------------

def render_portfolio(stats: dict, w: int) -> list[str]:
    lines = [_box_top(w, "PORTFOLIO")]
    if not stats:
        lines += [_row("  paper_portfolio_mlb.json not found", w), _box_bot(w)]
        return lines

    pnl_str = _fmt_pnl(stats["pnl"])
    pnl_pct = f"({'+' if stats['pnl_pct'] >= 0 else ''}{stats['pnl_pct']:.2f}%)"
    wr_str  = f"{stats['win_rate']:.1%}" if stats["win_rate"] is not None else "N/A"
    dd_col  = _red(f"{stats['drawdown']:.1f}%") if stats["drawdown"] > 5 else f"{stats['drawdown']:.1f}%"
    dep_col = _yellow(f"{stats['deployed_pct']:.1f}%") if stats["deployed_pct"] > 50 else f"{stats['deployed_pct']:.1f}%"

    lines.append(_row(
        f"  Bankroll  ${stats['bankroll']:.2f}"
        f"  │  Initial ${stats['initial']:.2f}"
        f"  │  P&L  {pnl_str} {pnl_pct}", w))
    lines.append(_row(
        f"  Open  {stats['n_open']}"
        f"  │  Closed  {stats['n_closed']}"
        f"  │  Win/Loss  {stats['wins']}/{stats['losses']}"
        f"  │  Win Rate  {wr_str}", w))
    lines.append(_row(
        f"  Deployed  ${stats['deployed']:.2f} ({dep_col})"
        f"  │  Reserve  ${stats['reserve']:.2f}"
        f"  │  Drawdown  {dd_col}", w))
    lines.append(_box_bot(w))
    return lines


# ---------------------------------------------------------------------------
# Panel: Today's Slate
# ---------------------------------------------------------------------------

def render_today_slate(stats: dict, game_date: str, w: int) -> list[str]:
    lines = [_box_top(w, f"TODAY'S SLATE — {game_date}")]
    if not stats:
        lines += [_row("  No portfolio loaded.", w), _box_bot(w)]
        return lines

    all_pos = stats["open_pos"] + stats["closed_pos"]
    today   = [p for p in all_pos if p.get("game_date") == game_date]

    if not today:
        lines += [_row(f"  No positions for {game_date} yet.", w), _box_bot(w)]
        lines.append(_box_bot(w))
        return lines

    # Aggregate by threshold
    by_thresh: dict[Any, list] = {}
    for p in today:
        t = p.get("kalshi_threshold", "?")
        by_thresh.setdefault(t, []).append(p)

    total_staked = sum(float(p.get("size_usd", 0.0)) for p in today)
    n_yes = sum(1 for p in today if p.get("direction") == "YES")
    n_no  = sum(1 for p in today if p.get("direction") == "NO")

    lines.append(_row(
        f"  Total bets: {_bold(str(len(today)))}"
        f"  │  Staked: ${total_staked:.2f}"
        f"  │  YES: {n_yes}  NO: {n_no}", w))
    lines.append(_blank_row(w))

    for thresh in sorted(by_thresh.keys(), key=lambda x: int(x) if str(x).isdigit() else 99):
        grp = by_thresh[thresh]
        staked_t = sum(float(p.get("size_usd", 0.0)) for p in grp)
        open_t   = sum(1 for p in grp if p.get("status") == "OPEN")
        closed_t = sum(1 for p in grp if p.get("status") == "CLOSED")
        wins_t   = sum(1 for p in grp if p.get("outcome") == "WIN")
        pnl_t    = sum(_position_pnl(p) for p in grp if p.get("status") == "CLOSED")
        thresh_label = _fmt_threshold(thresh)
        pnl_fmt  = _fmt_pnl(pnl_t) if closed_t > 0 else _dim("pending")
        lines.append(_row(
            f"  {_bold(thresh_label)}  "
            f"n={len(grp)}  staked=${staked_t:.2f}  "
            f"open={open_t}  closed={closed_t}  wins={wins_t}  "
            f"P&L={pnl_fmt}", w))

    lines.append(_box_bot(w))
    return lines


# ---------------------------------------------------------------------------
# Panel: Open Positions (table)
# ---------------------------------------------------------------------------

_OPEN_COLS = [
    ("player_name",       22, "left"),
    ("kalshi_threshold",  6,  "right"),
    ("direction",         4,  "center"),
    ("gross_edge",        8,  "right"),
    ("mid_price_at_entry",7,  "right"),
    ("size_usd",          8,  "right"),
    ("game_date",         10, "left"),
]

def render_open_positions(stats: dict, w: int, max_rows: int = 25) -> list[str]:
    lines = [_box_top(w, "OPEN POSITIONS")]
    open_pos = stats.get("open_pos", []) if stats else []

    if not open_pos:
        lines += [_row("  No open positions.", w), _box_bot(w)]
        return lines

    # Header row
    hdr = (
        _col("PLAYER",    22) + " " +
        _col("THOLD",      6, "right") + " " +
        _col("DIR",        4, "center") + " " +
        _col("EDGE",       8, "right") + " " +
        _col("MIP",        7, "right") + " " +
        _col("SIZE",       8, "right") + " " +
        _col("GAME DATE", 10)
    )
    lines.append(_row("  " + _dim(hdr), w))
    lines.append(_row("  " + _dim("─" * min(w - 4, 80)), w))

    shown = 0
    for p in open_pos:
        if shown >= max_rows:
            remaining = len(open_pos) - max_rows
            lines.append(_row(f"  … {remaining} more open positions not shown", w))
            break
        edge = float(p.get("gross_edge", 0.0))
        mip  = float(p.get("mid_price_at_entry", 0.0))
        row = (
            _col(p.get("player_name", "?"), 22) + " " +
            _col(_fmt_threshold(p.get("kalshi_threshold")), 6, "right") + " " +
            _col(p.get("direction", "?"), 4, "center") + " " +
            _col(_fmt_edge(edge), 8, "right") + " " +
            _col(f"{mip:.3f}", 7, "right") + " " +
            _col(f"${float(p.get('size_usd', 0.0)):.2f}", 8, "right") + " " +
            _col(str(p.get("game_date", "?")), 10)
        )
        lines.append(_row("  " + row, w))
        shown += 1

    lines.append(_box_bot(w))
    return lines


# ---------------------------------------------------------------------------
# Panel: Recently Resolved
# ---------------------------------------------------------------------------

def render_recently_resolved(stats: dict, w: int, max_rows: int = 15) -> list[str]:
    lines = [_box_top(w, "RECENTLY RESOLVED")]
    closed = stats.get("closed_pos", []) if stats else []

    if not closed:
        lines += [_row("  No resolved positions yet.", w), _box_bot(w)]
        return lines

    # Sort newest-first by resolved_at or entered_at
    def _sort_key(p: dict) -> str:
        return p.get("resolved_at") or p.get("entered_at") or ""

    recent = sorted(closed, key=_sort_key, reverse=True)[:max_rows]

    hdr = (
        _col("PLAYER",    22) + " " +
        _col("THOLD",      6, "right") + " " +
        _col("DIR",        4, "center") + " " +
        _col("MODEL_P",    7, "right") + " " +
        _col("MIP",        6, "right") + " " +
        _col("RESULT",     6, "center") + " " +
        _col("P&L",        9, "right")
    )
    lines.append(_row("  " + _dim(hdr), w))
    lines.append(_row("  " + _dim("─" * min(w - 4, 80)), w))

    for p in recent:
        outcome = p.get("outcome", "?")
        result_str = (_green("WIN") if outcome == "WIN"
                      else (_red("LOSS") if outcome in ("LOSS", "LOSE")
                            else _yellow(str(outcome))))
        pnl = _position_pnl(p)
        row = (
            _col(p.get("player_name", "?"), 22) + " " +
            _col(_fmt_threshold(p.get("kalshi_threshold")), 6, "right") + " " +
            _col(p.get("direction", "?"), 4, "center") + " " +
            _col(f"{float(p.get('model_p', 0.0)):.3f}", 7, "right") + " " +
            _col(f"{float(p.get('mid_price_at_entry', 0.0)):.3f}", 6, "right") + " " +
            _col(result_str, 6, "center") + " " +
            _col(_fmt_pnl(pnl), 9, "right")
        )
        lines.append(_row("  " + row, w))

    lines.append(_box_bot(w))
    return lines


# ---------------------------------------------------------------------------
# Panel: System Status
# ---------------------------------------------------------------------------

def render_system_status(audit_entries: list[dict], pipe_ts: dict[str, str], w: int) -> list[str]:
    lines = [_box_top(w, "SYSTEM STATUS")]

    # Kill switch state: scan audit log newest-first
    ks_active = False
    ks_reason: str | None = None
    for entry in reversed(audit_entries):
        evt = entry.get("event_type", "")
        if evt == "kill_switch_triggered":
            ks_active = True
            ks_reason = entry.get("payload", {}).get("reason") if isinstance(entry.get("payload"), dict) else None
            break
        if evt == "kill_switch_reset":
            break

    if ks_active:
        ks_line = _red(f"  *** KILL SWITCH ACTIVE ***  Reason: {ks_reason or 'unknown'}")
    else:
        ks_line = _green("  Kill Switch: ARMED (inactive)")

    lines.append(_row(ks_line, w))
    lines.append(_blank_row(w))
    lines.append(_row(_dim("  Pipeline last run:"), w))

    for label, ts in pipe_ts.items():
        since = _since(ts) if ts not in ("no log yet", "error reading mtime") else ""
        status_str = ts + (f"  [{since}]" if since else "")
        color_fn = _dim if ts.startswith("no log") else (_green if since else str)
        lines.append(_row(f"    {_col(label, 20)}  {color_fn(status_str)}", w))

    lines.append(_box_bot(w))
    return lines


# ---------------------------------------------------------------------------
# Panel: Alert Feed
# ---------------------------------------------------------------------------

_ALERT_SEV = {"WARNING", "WARN", "ERROR", "CRITICAL"}

def render_alert_feed(audit_entries: list[dict], w: int, max_alerts: int = 15) -> list[str]:
    lines = [_box_top(w, f"ALERT FEED (last {max_alerts})")]

    alerts = [e for e in audit_entries if e.get("severity", "") in _ALERT_SEV]
    if not alerts:
        lines += [_row(_green("  No alerts."), w), _box_bot(w)]
        return lines

    # Deduplicate consecutive same (component, event_type) pairs, newest-first
    deduped: list[tuple[dict, int]] = []
    for entry in reversed(alerts[-max_alerts * 2:]):
        key = (entry.get("component"), entry.get("event_type"))
        if deduped and (deduped[-1][0].get("component"), deduped[-1][0].get("event_type")) == key:
            deduped[-1] = (deduped[-1][0], deduped[-1][1] + 1)
        else:
            deduped.append((entry, 1))

    for entry, count in deduped[:max_alerts]:
        ts   = str(entry.get("timestamp", ""))[:19]
        sev  = str(entry.get("severity", "?"))
        comp = str(entry.get("component", "?"))
        evt  = str(entry.get("event_type", "?"))
        suffix = f" ×{count}" if count > 1 else ""
        sev_colored = _red(sev) if sev in ("ERROR", "CRITICAL") else _yellow(sev)
        lines.append(_row(f"  {ts}  {_col(sev_colored, 8)}  {_col(comp, 8)} {evt}{suffix}", w))

    lines.append(_box_bot(w))
    return lines


# ---------------------------------------------------------------------------
# Footer
# ---------------------------------------------------------------------------

def render_footer(w: int, interval: int, last_error: str | None) -> list[str]:
    lines = []
    now = _utcnow()
    hint = f"  [Ctrl+C to exit]  refresh every {interval}s  rendered {now}"
    lines.append(_dim("─" * (w + 2)))
    lines.append(_row(_dim(hint), w))
    if last_error:
        lines.append(_row(_red(f"  LAST RENDER ERROR: {last_error[:w-30]}"), w))
    return lines


# ---------------------------------------------------------------------------
# Full render
# ---------------------------------------------------------------------------

def render_all(interval: int, last_error: str | None = None) -> str:
    w = _term_width()
    portfolio = _read_json(PORTFOLIO)
    stats = _portfolio_stats(portfolio) if portfolio else {}
    audit  = _read_jsonl(AUDIT_LOG)
    pipe_ts = _pipe_timestamps()
    game_date = _today_str()

    blocks: list[list[str]] = []

    def _safe_panel(fn, *args, fallback_label: str = "PANEL") -> list[str]:
        try:
            return fn(*args)
        except Exception as e:
            return [
                _box_top(w, fallback_label),
                _row(_red(f"  RENDER ERROR: {type(e).__name__}: {e}"), w),
                _box_bot(w),
            ]

    blocks.append(render_header(w))
    blocks.append(_safe_panel(render_portfolio,         stats, w,                         fallback_label="PORTFOLIO"))
    blocks.append(_safe_panel(render_today_slate,       stats, game_date, w,              fallback_label="TODAY'S SLATE"))
    blocks.append(_safe_panel(render_open_positions,    stats, w,                         fallback_label="OPEN POSITIONS"))
    blocks.append(_safe_panel(render_recently_resolved, stats, w,                         fallback_label="RECENTLY RESOLVED"))
    blocks.append(_safe_panel(render_system_status,     audit, pipe_ts, w,               fallback_label="SYSTEM STATUS"))
    blocks.append(_safe_panel(render_alert_feed,        audit, w,                         fallback_label="ALERT FEED"))
    blocks.append(render_footer(w, interval, last_error))

    return "\n".join(line for block in blocks for line in block)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="MLB Paper Trade Dashboard")
    p.add_argument("--interval", type=int, default=60,
                   help="Refresh interval in seconds (default: 60)")
    p.add_argument("--once", action="store_true",
                   help="Render once and exit (no loop)")
    return p.parse_args()


def _clear() -> None:
    sys.stdout.write("\033[2J\033[H")
    sys.stdout.flush()


def main() -> None:
    args = _parse_args()

    # Allow graceful SIGTERM in addition to Ctrl+C
    _stop = [False]
    def _handle_term(sig: int, frame: Any) -> None:
        _stop[0] = True
    signal.signal(signal.SIGTERM, _handle_term)

    last_error: str | None = None

    if args.once:
        try:
            output = render_all(interval=args.interval)
        except Exception as e:
            output = f"FATAL RENDER ERROR: {e}"
        print(output)
        return

    while not _stop[0]:
        try:
            output = render_all(interval=args.interval, last_error=last_error)
            last_error = None
        except Exception as e:
            last_error = f"{type(e).__name__}: {e}"
            output = last_error

        try:
            _clear()
            print(output)
        except Exception:
            # If even print fails (terminal error), just keep going
            pass

        try:
            for _ in range(args.interval * 10):
                if _stop[0]:
                    break
                time.sleep(0.1)
        except KeyboardInterrupt:
            break


if __name__ == "__main__":
    main()
