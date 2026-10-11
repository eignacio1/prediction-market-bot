#!/usr/bin/env python3
"""
MLB Live Terminal — Bloomberg-style multi-pane dashboard.

Navigate with:
    Tab / Shift+Tab   cycle focused panel
    ↑ ↓               scroll one line
    PgUp / PgDn       scroll one page
    Home / End        top / bottom
    q / Ctrl+C        quit

Run (pulls data from VPS):
    python3 scripts/run_mlb_dashboard.py --remote root@157.230.91.33 \\
        --log-dir /opt/prediction-market-bot/logs/

Run locally:
    python3 scripts/run_mlb_dashboard.py --log-dir logs/
"""

from __future__ import annotations

import argparse
import curses
import json
import locale
import os
import re
import shlex
import subprocess
import sys
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

locale.setlocale(locale.LC_ALL, "")

# ─────────────────────────────────────────────────────────────────────────────
# ANSI constants
# ─────────────────────────────────────────────────────────────────────────────
RESET   = "\033[0m"
BOLD    = "\033[1m"
DIM     = "\033[2m"
GREEN   = "\033[32m"
RED     = "\033[31m"
YELLOW  = "\033[33m"
CYAN    = "\033[36m"
MAGENTA = "\033[35m"
BG_RED  = "\033[41m"

_ANSI_RE       = re.compile(r"\033\[[0-9;]*m")
_ANSI_TOKEN_RE = re.compile(r"(\033\[[0-9;]*m)")


def _c(*parts: str) -> str:
    codes = [p for p in parts if p.startswith("\033")]
    text  = "".join(p for p in parts if not p.startswith("\033"))
    return "".join(codes) + text + RESET


def _vlen(s: str) -> int:
    return len(_ANSI_RE.sub("", s))


def _fit(s: str, w: int) -> str:
    vis = _vlen(s)
    if vis < w:
        return s + " " * (w - vis)
    if vis > w:
        return _ANSI_RE.sub("", s)[:w]
    return s


def _pad_s(s: str, w: int, align: str = "left") -> str:
    s = str(s)
    if len(s) >= w:
        return s[:w]
    return s.rjust(w) if align == "right" else s.center(w) if align == "center" else s.ljust(w)


# ─────────────────────────────────────────────────────────────────────────────
# Curses colour pairs
# ─────────────────────────────────────────────────────────────────────────────
_CP_GREEN   = 1
_CP_RED     = 2
_CP_YELLOW  = 3
_CP_CYAN    = 4
_CP_MAGENTA = 5
_CP_BG_RED  = 6
_CP_FOCUS   = 7

_ANSI_TO_CP: dict[int, int] = {
    31: _CP_RED, 32: _CP_GREEN, 33: _CP_YELLOW,
    35: _CP_MAGENTA, 36: _CP_CYAN, 41: _CP_BG_RED,
}


def _init_colors() -> None:
    curses.start_color()
    curses.use_default_colors()
    curses.init_pair(_CP_GREEN,   curses.COLOR_GREEN,   -1)
    curses.init_pair(_CP_RED,     curses.COLOR_RED,     -1)
    curses.init_pair(_CP_YELLOW,  curses.COLOR_YELLOW,  -1)
    curses.init_pair(_CP_CYAN,    curses.COLOR_CYAN,    -1)
    curses.init_pair(_CP_MAGENTA, curses.COLOR_MAGENTA, -1)
    curses.init_pair(_CP_BG_RED,  curses.COLOR_WHITE,   curses.COLOR_RED)
    curses.init_pair(_CP_FOCUS,   curses.COLOR_CYAN,    -1)


# ─────────────────────────────────────────────────────────────────────────────
# ANSI → curses writer
# ─────────────────────────────────────────────────────────────────────────────
def _addstr(win, y: int, x: int, line: str, max_x: int) -> None:
    bold = False
    dim  = False
    cp   = 0
    cx   = x
    for token in _ANSI_TOKEN_RE.split(line):
        if not token:
            continue
        if token.startswith("\033[") and token.endswith("m"):
            for part in (token[2:-1].split(";") if token[2:-1] else [""]):
                try:
                    n = int(part) if part else 0
                except ValueError:
                    continue
                if n == 0:   bold = dim = False; cp = 0
                elif n == 1: bold = True
                elif n == 2: dim  = True
                elif n in _ANSI_TO_CP: cp = _ANSI_TO_CP[n]
        else:
            if cx >= max_x - 1:
                break
            chunk = token[:max_x - 1 - cx]
            if not chunk:
                continue
            attr = curses.A_NORMAL
            if bold: attr |= curses.A_BOLD
            if dim:  attr |= curses.A_DIM
            if cp:   attr |= curses.color_pair(cp)
            try:
                win.addstr(y, cx, chunk, attr)
            except curses.error:
                pass
            cx += len(chunk)


# ─────────────────────────────────────────────────────────────────────────────
# Formatters
# ─────────────────────────────────────────────────────────────────────────────
def _today() -> str:
    return datetime.now(tz=timezone.utc).strftime("%Y-%m-%d")


def _ts(iso: str) -> str:
    return iso[:19].replace("T", " ") if iso else "—"


def _pnl(v: float) -> str:
    if v > 0: return _c(GREEN, BOLD, f"+${v:.2f}")
    if v < 0: return _c(RED,   BOLD, f"-${abs(v):.2f}")
    return "$0.00"


def _edge(v: float | None) -> str:
    if v is None:  return _c(DIM, "  N/A  ")
    if v >= 0.04:  return _c(GREEN,  f"{v:+.4f}")
    if v > 0:      return _c(YELLOW, f"{v:+.4f}")
    return _c(DIM, f"{v:+.4f}")


def _dir(d: str) -> str:
    if d == "YES": return _c(GREEN, BOLD, "YES")
    if d == "NO":  return _c(RED,   "NO ")
    return _c(DIM, " — ")


def _outcome(o: str) -> str:
    if o == "WIN":  return _c(GREEN, BOLD, "WIN ")
    if o == "LOSS": return _c(RED,   BOLD, "LOSS")
    return _pad_s(o, 4)


def _dd(pct: float) -> str:
    if pct >= 15: return _c(RED,    BOLD, f"{pct:.2f}%")
    if pct >= 5:  return _c(YELLOW,       f"{pct:.2f}%")
    return _c(GREEN, f"{pct:.2f}%")


def _ks(active: bool, reason: str | None) -> str:
    if active:
        return _c(BG_RED, BOLD, " ⚠  KILL SWITCH ACTIVE  ⚠ ") + (f" ({reason})" if reason else "")
    return _c(GREEN, "ARMED ✓")


def _thresh(t) -> str:
    try:    return f"H≥{int(t)}"
    except: return str(t)


def _pos_pnl(p: dict) -> float:
    return float(p.get("pnl", 0.0)) + float(p.get("exit_pnl", 0.0))


# ─────────────────────────────────────────────────────────────────────────────
# Data loaders
# ─────────────────────────────────────────────────────────────────────────────
def _load_json(p: Path) -> dict:
    try:
        with open(p) as f:
            return json.load(f)
    except Exception:
        return {}


def _load_jsonl(p: Path, tail: int = 200) -> list[dict]:
    if not p.exists():
        return []
    entries: list[dict] = []
    try:
        with open(p) as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        entries.append(json.loads(line))
                    except json.JSONDecodeError:
                        pass
    except Exception:
        pass
    return entries[-tail:]


def _load_tail(p: Path, n: int = 20) -> list[str]:
    if not p.exists():
        return []
    try:
        with open(p) as f:
            lines = f.readlines()
        return [l.rstrip() for l in lines[-n:]]
    except Exception:
        return []


def _data_from_local(log_dir: str) -> dict:
    d = Path(log_dir)
    return {
        "portfolio": _load_json(d / "paper_portfolio_mlb.json"),
        "audit":     _load_jsonl(d / "audit_mlb.jsonl"),
        "pipe_log":  _load_tail(d / "paper_mlb_cron.log", n=25),
        "pipe_mtimes": _pipe_mtimes(d),
    }


def _pipe_mtimes(d: Path) -> dict[str, str]:
    pipes = {
        "PIPE-05  (23:30Z)": "paper_mlb_cron.log",
        "PIPE-05R (06:30Z)": "resolve_mlb_cron.log",
        "PIPE-05FX(22:30Z)": "mlb_feature_refresh.log",
        "PIPE-05C (Mon14Z)": "mlb_calib_monitor.log",
    }
    result: dict[str, str] = {}
    for label, fname in pipes.items():
        p = d / fname
        if p.exists():
            try:
                mtime = p.stat().st_mtime
                dt    = datetime.fromtimestamp(mtime, tz=timezone.utc)
                result[label] = dt.strftime("%Y-%m-%dT%H:%M:%SZ")
            except Exception:
                result[label] = "error"
        else:
            result[label] = "no log yet"
    return result


# ─────────────────────────────────────────────────────────────────────────────
# Background fetch thread
# ─────────────────────────────────────────────────────────────────────────────
@dataclass
class _FetchState:
    lock:        threading.Lock = field(default_factory=threading.Lock)
    data:        dict            = field(default_factory=dict)
    last_ok:     float           = 0.0
    error_count: int             = 0


def _fetch_worker(args: argparse.Namespace, state: _FetchState,
                  stop: threading.Event) -> None:
    while not stop.is_set():
        try:
            new = (fetch_remote(args.remote, args.log_dir)
                   if args.remote else _data_from_local(args.log_dir))
            if new:
                with state.lock:
                    state.data        = new
                    state.last_ok     = time.time()
                    state.error_count = 0
        except Exception:
            with state.lock:
                state.error_count += 1
        stop.wait(args.interval)


# ─────────────────────────────────────────────────────────────────────────────
# Remote fetch — single SSH round-trip
# ─────────────────────────────────────────────────────────────────────────────
_SSH_CTL = "/tmp/pmbot-mlb-ssh-ctl"

_REMOTE_SCRIPT = r"""
import json, sys, os
from pathlib import Path
from datetime import datetime, timezone

log_dir = sys.argv[1]
d = Path(log_dir)
result = {}

def rj(p):
    with open(p) as f: return json.load(f)

def rjl(p, tail=200):
    e = []
    try:
        with open(p) as f:
            for line in f:
                line = line.strip()
                if line:
                    try: e.append(json.loads(line))
                    except: pass
    except: pass
    return e[-tail:]

def rt(p, n=25):
    try:
        with open(p) as f: lines = f.readlines()
        return [l.rstrip() for l in lines[-n:]]
    except: return []

def mtime_str(p):
    try:
        mt = p.stat().st_mtime
        dt = datetime.fromtimestamp(mt, tz=timezone.utc)
        return dt.strftime('%Y-%m-%dT%H:%M:%SZ')
    except: return 'no log yet'

pipes = {
    'PIPE-05  (23:30Z)': 'paper_mlb_cron.log',
    'PIPE-05R (06:30Z)': 'resolve_mlb_cron.log',
    'PIPE-05FX(22:30Z)': 'mlb_feature_refresh.log',
    'PIPE-05C (Mon14Z)': 'mlb_calib_monitor.log',
}

result['portfolio']  = rj(d / 'paper_portfolio_mlb.json') if (d / 'paper_portfolio_mlb.json').exists() else {}
result['audit']      = rjl(d / 'audit_mlb.jsonl')
result['pipe_log']   = rt(d / 'paper_mlb_cron.log')
result['pipe_mtimes'] = {label: mtime_str(d / fname) for label, fname in pipes.items()}

print(json.dumps(result))
"""


def fetch_remote(host: str, log_dir: str) -> dict:
    try:
        proc = subprocess.run(
            ["ssh",
             "-o", "ControlMaster=auto",
             "-o", f"ControlPath={_SSH_CTL}",
             "-o", "ControlPersist=120",
             "-o", "ConnectTimeout=5",
             "-o", "BatchMode=yes",
             "-o", "StrictHostKeyChecking=no",
             host,
             f"python3 - {shlex.quote(log_dir)}"],
            input=_REMOTE_SCRIPT,
            capture_output=True, text=True, timeout=8,
        )
        raw = proc.stdout.strip()
        return json.loads(raw) if raw else {}
    except Exception:
        return {}


# ─────────────────────────────────────────────────────────────────────────────
# Content producers (return list[str] of ANSI lines, no borders)
# ─────────────────────────────────────────────────────────────────────────────
def content_portfolio(data: dict, iw: int) -> list[str]:
    p = data.get("portfolio", {})
    if not p:
        return ["  (paper_portfolio_mlb.json not found — PIPE-05 fires at 23:30Z)"]

    bankroll = float(p.get("bankroll_usd", 0))
    initial  = float(p.get("initial_bankroll_usd", 1000))
    open_pos   = p.get("open_positions",   [])
    closed_pos = p.get("closed_positions", [])
    if isinstance(open_pos,   dict): open_pos   = list(open_pos.values())
    if isinstance(closed_pos, dict): closed_pos = list(closed_pos.values())

    closed_pnl = sum(_pos_pnl(x) for x in closed_pos if not x.get("pool_isolated"))
    open_cost  = sum(float(x.get("size_usd", 0)) for x in open_pos if not x.get("pool_isolated"))
    pnl        = closed_pnl
    deployed   = sum(float(x.get("size_usd", 0)) for x in open_pos)
    dd_pct     = max(0.0, -pnl / initial * 100) if initial else 0.0
    wins       = sum(1 for x in closed_pos if x.get("outcome") == "WIN")
    losses     = sum(1 for x in closed_pos if x.get("outcome") == "LOSS")
    total      = wins + losses
    wr         = f"{wins/total:.1%}" if total else "N/A"
    dl         = float(p.get("daily_net_pnl", 0))
    dl_col     = _c(RED, f"${dl:.2f}") if dl < 0 else f"${dl:.2f}"
    # GG-536: T1 execution evidence = CONFIRMED_FILLED rows only; the totals above are ALL rows.
    try:
        from prediction_market_bot import t4_fill_status as _tfs
        _x = _tfs.execution_summary(closed_pos, _tfs.load_fill_status(
            Path(data.get("log_dir") or os.environ.get("LOG_DIR", "logs/")) / "t1_mlb_fill_status.jsonl"), band="T1")
        fills_line = (f"  T1 EXECUTION (CONFIRMED_FILLED only): {_x['fills_n']} fills, P&L ${_x['fills_pnl']:.2f}   "
                      + _c(DIM, f"(totals above = {_x['all_n']} ALL rows, calibration only - not execution evidence)"))
    except Exception:
        fills_line = _c(DIM, "  T1 EXECUTION: fill-status sidecar unavailable - totals above are calibration only")

    return [
        f"  Bankroll: {_c(BOLD, CYAN, f'${bankroll:,.2f}')}   "
        f"Initial: ${initial:,.2f}   "
        f"P&L: {_pnl(pnl)}   "
        f"Drawdown: {_dd(dd_pct)}   "
        f"Daily P&L: {dl_col}",

        f"  Open: {_c(BOLD, str(len(open_pos)))} pos   "
        f"Deployed: ${deployed:.2f}   "
        f"Win/Loss: {wins}/{losses}   "
        f"Win Rate: {wr}   "
        f"Resolved: {total}",

        fills_line,
    ]


def content_live_positions(data: dict, iw: int) -> list[str]:
    p        = data.get("portfolio", {})
    open_pos = p.get("open_positions", [])
    if isinstance(open_pos, dict): open_pos = list(open_pos.values())
    if not open_pos:
        return ["  (no open positions)"]

    lines = [_c(DIM, f"  {'PLAYER':<22} {'THOLD':>5}  {'DIR':<3}  {'SIZE':>8}  {'MODEL_P':>8}  {'MIP':>7}  {'EDGE':>9}  ENTERED")]
    lines.append("  " + "─" * (iw - 2))
    for pos in open_pos:
        player  = _pad_s(pos.get("player_name", "?"), 22)
        thold   = _pad_s(_thresh(pos.get("kalshi_threshold")), 5, "right")
        dirn    = _dir(pos.get("direction", "?"))
        size    = _pad_s(f"${pos.get('size_usd', 0):.2f}", 8, "right")
        mp      = _pad_s(f"{pos.get('model_p', 0):.4f}", 8, "right")
        mip     = _pad_s(f"{pos.get('mid_price_at_entry', 0):.4f}", 7, "right")
        ne      = _edge(pos.get("gross_edge"))
        entered = _ts(pos.get("entered_at", ""))[:16]
        lines.append(f"  {player} {thold}  {dirn}  {size}  {mp}  {mip}  {ne}  {entered}")
    return lines


def content_today_slate(data: dict, iw: int) -> list[str]:
    p        = data.get("portfolio", {})
    open_pos   = p.get("open_positions",   [])
    closed_pos = p.get("closed_positions", [])
    if isinstance(open_pos,   dict): open_pos   = list(open_pos.values())
    if isinstance(closed_pos, dict): closed_pos = list(closed_pos.values())

    today = _today()
    all_pos  = open_pos + closed_pos
    today_pos = [x for x in all_pos if x.get("game_date") == today]

    if not today_pos:
        return [f"  {today} — no positions yet (PIPE-05 fires at 23:30Z)"]

    n_yes = sum(1 for p in today_pos if p.get("direction") == "YES")
    n_no  = sum(1 for p in today_pos if p.get("direction") == "NO")
    staked = sum(float(p.get("size_usd", 0)) for p in today_pos)

    lines = [
        f"  {today}   {_c(BOLD, str(len(today_pos)))} bets   "
        f"Staked: ${staked:.2f}   YES: {n_yes}   NO: {n_no}",
        _c(DIM, f"  {'THOLD':>5}  {'N':>4}  {'STAKED':>8}  {'OPEN':>5}  {'CLOSED':>7}  {'WINS':>5}  P&L"),
        "  " + "─" * (iw - 2),
    ]

    by_thresh: dict = {}
    for pos in today_pos:
        t = pos.get("kalshi_threshold", "?")
        by_thresh.setdefault(t, []).append(pos)

    for t in sorted(by_thresh.keys(), key=lambda x: int(x) if str(x).isdigit() else 99):
        grp      = by_thresh[t]
        stk      = sum(float(x.get("size_usd", 0)) for x in grp)
        n_open   = sum(1 for x in grp if x.get("status") == "OPEN")
        n_closed = sum(1 for x in grp if x.get("status") == "CLOSED")
        n_wins   = sum(1 for x in grp if x.get("outcome") == "WIN")
        grp_pnl  = sum(_pos_pnl(x) for x in grp if x.get("status") == "CLOSED")
        pnl_str  = _pnl(grp_pnl) if n_closed else _c(DIM, "pending")
        lines.append(
            f"  {_pad_s(_thresh(t), 5, 'right')}  {len(grp):>4}  "
            f"${stk:>7.2f}  {n_open:>5}  {n_closed:>7}  {n_wins:>5}  {pnl_str}"
        )
    return lines


def content_alerts(data: dict, iw: int) -> list[str]:
    sev_set = {"WARNING", "WARN", "ERROR", "CRITICAL"}
    audit   = data.get("audit", [])
    alerts  = [e for e in audit if e.get("severity", "") in sev_set]
    if not alerts:
        return ["  (no alerts)"]

    lines = [_c(DIM, f"  {'TIMESTAMP':<19}  {'SEV':<9}  {'COMP':<8}  EVENT")]
    lines.append("  " + "─" * (iw - 2))
    for e in reversed(alerts[-30:]):
        sev    = e.get("severity", "?")
        pl     = e.get("payload", {}) if isinstance(e.get("payload"), dict) else {}
        detail = str(pl.get("reason", pl.get("trigger", pl.get("error", "")))).strip()[:28]
        sev_col = (_c(BG_RED, BOLD, f" {sev:<8}") if sev == "CRITICAL" else
                   _c(RED,          f"{sev:<8}") if sev == "ERROR" else
                   _c(YELLOW,       f"{sev:<8}"))
        lines.append(
            f"  {_ts(e.get('timestamp', ''))}  {sev_col}  "
            f"{_pad_s(e.get('component', '?'), 8)}  "
            f"{_pad_s(e.get('event_type', '?'), 24)}  {_c(DIM, detail)}"
        )
    return lines


def content_resolved(data: dict, iw: int) -> list[str]:
    p          = data.get("portfolio", {})
    closed_pos = p.get("closed_positions", [])
    if isinstance(closed_pos, dict): closed_pos = list(closed_pos.values())
    if not closed_pos:
        return ["  (none resolved — PIPE-05R runs at 06:30Z)"]

    wins      = sum(1 for x in closed_pos if x.get("outcome") == "WIN")
    losses    = sum(1 for x in closed_pos if x.get("outcome") == "LOSS")
    total_pnl = sum(_pos_pnl(x) for x in closed_pos)
    lines = [
        f"  {_c(BOLD, f'{wins}W / {losses}L')}   Cumulative P&L: {_pnl(total_pnl)}",
        _c(DIM, f"  {'PLAYER':<22}  {'THOLD':>5}  {'DIR':<3}  {'ACTUAL':>6}  {'RESULT':<6}  {'P&L':>8}  RESOLVED"),
        "  " + "─" * (iw - 2),
    ]
    for pos in reversed(closed_pos):
        actual = _pad_s(str(pos.get("actual_stat", "?"))[:6], 6, "right")
        lines.append(
            f"  {_pad_s(pos.get('player_name', '?'), 22)}  "
            f"{_pad_s(_thresh(pos.get('kalshi_threshold')), 5, 'right')}  "
            f"{_dir(pos.get('direction', '?'))}  "
            f"{actual}  {_outcome(pos.get('outcome', '?'))}  "
            f"{_pnl(_pos_pnl(pos))}  "
            f"{_ts(pos.get('resolved_at', ''))[:16]}"
        )
    return lines


def content_system(data: dict, iw: int) -> list[str]:
    audit      = data.get("audit", [])
    pipe_mtimes = data.get("pipe_mtimes", {})

    ks_active = False
    ks_reason: str | None = None
    for e in reversed(audit):
        if e.get("event_type") == "kill_switch_triggered":
            ks_active = True
            ks_reason = (e.get("payload") or {}).get("reason") or (e.get("payload") or {}).get("trigger")
            break
        if e.get("event_type") == "kill_switch_reset":
            break

    now_ts = datetime.now(tz=timezone.utc)

    def _since(ts_str: str) -> str:
        try:
            dt   = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
            secs = int((now_ts - dt).total_seconds())
            if secs < 60:    return f"{secs}s ago"
            if secs < 3600:  return f"{secs//60}m ago"
            if secs < 86400: return f"{secs//3600}h{(secs%3600)//60}m ago"
            return f"{secs//86400}d ago"
        except Exception:
            return ""

    pipe_parts = []
    for label, ts in pipe_mtimes.items():
        since = _since(ts) if ts not in ("no log yet", "error") else ""
        entry = f"{label}: {ts[:16] if len(ts) > 10 else ts}" + (f" [{since}]" if since else "")
        pipe_parts.append(entry)

    lines = [
        f"  KS: {_ks(ks_active, ks_reason)}",
    ]
    for part in pipe_parts:
        lines.append(f"  {part}")
    return lines


def content_pipe_log(data: dict, iw: int) -> list[str]:
    lines = data.get("pipe_log", [])
    if not lines:
        return ["  (no paper_mlb_cron.log — first run at 23:30Z)"]
    result = []
    for line in lines:
        col = (GREEN  if "SUMMARY" in line or "PLACED" in line.upper() else
               YELLOW if "WARN" in line or "SKIP" in line else
               RED    if "ERROR" in line or "error" in line or "FATAL" in line else
               CYAN   if "PIPE-05" in line else
               DIM)
        bold_flag = BOLD if col in (GREEN, RED) else ""
        result.append("  " + _c(col, bold_flag, line[:iw - 2]))
    return result


# ─────────────────────────────────────────────────────────────────────────────
# Panel drawing (identical to live_terminal.py)
# ─────────────────────────────────────────────────────────────────────────────
@dataclass
class PanelState:
    title:     str
    y: int;    x: int
    height: int; width: int
    scrollable: bool
    scroll_y:  int          = 0
    content:   list[str]    = field(default_factory=list)
    pad:       object       = field(default=None, repr=False)
    dirty:     bool         = True


def _panel_max_scroll(ps: PanelState) -> int:
    return max(0, len(ps.content) - (ps.height - 2))


def _rebuild_pad(ps: PanelState) -> None:
    inner_h = max(1, ps.height - 2)
    inner_w = max(1, ps.width  - 2)
    ph = max(len(ps.content) + 1, inner_h + 1)
    try:
        ps.pad = curses.newpad(ph, inner_w + 1)
        for i, line in enumerate(ps.content):
            _addstr(ps.pad, i, 0, _fit(line, inner_w), inner_w)
    except curses.error:
        ps.pad = None
    ps.dirty = False


def draw_panel(stdscr, ps: PanelState, focused: bool, max_y: int, max_x: int) -> None:
    if ps.y >= max_y or ps.x >= max_x:
        return
    W = min(ps.width,  max_x - ps.x)
    H = min(ps.height, max_y - ps.y)
    inner_w = W - 2
    inner_h = H - 2

    if ps.dirty:
        _rebuild_pad(ps)

    ms = _panel_max_scroll(ps)
    ps.scroll_y = max(0, min(ps.scroll_y, ms))

    title_seg   = f" {ps.title} "
    fill        = max(0, inner_w - len(title_seg))
    indicator   = ""
    if ms > 0:
        pct       = int(ps.scroll_y / ms * 100) if ms else 0
        indicator = f" ↕{pct}% "
        fill      = max(0, fill - len(indicator))

    top = "┌─" + title_seg + "─" * fill + indicator + "─┐"
    try:
        attr = (curses.color_pair(_CP_FOCUS) | curses.A_BOLD) if focused else curses.A_NORMAL
        stdscr.addstr(ps.y, ps.x, top[:W], attr)
    except curses.error:
        pass

    for dy in range(inner_h):
        ry = ps.y + 1 + dy
        if ry >= max_y:
            break
        try: stdscr.addstr(ry, ps.x,         "│", curses.A_DIM)
        except curses.error: pass
        try: stdscr.addstr(ry, ps.x + W - 1, "│", curses.A_DIM)
        except curses.error: pass

    by = ps.y + H - 1
    if by < max_y:
        try: stdscr.addstr(by, ps.x, "└" + "─" * inner_w + "┘", curses.A_DIM)
        except curses.error: pass


def refresh_pad(ps: PanelState, max_y: int, max_x: int) -> None:
    if ps.pad is None:
        return
    W = min(ps.width,  max_x - ps.x)
    H = min(ps.height, max_y - ps.y)
    inner_h = H - 2
    inner_w = W - 2
    if inner_h <= 0 or inner_w <= 0:
        return
    vy0 = ps.y + 1
    vx0 = ps.x + 1
    vy1 = min(ps.y + H - 2, max_y - 1)
    vx1 = min(ps.x + W - 2, max_x - 1)
    if vy1 >= vy0 and vx1 >= vx0:
        try:
            ps.pad.noutrefresh(ps.scroll_y, 0, vy0, vx0, vy1, vx1)
        except curses.error:
            pass


# ─────────────────────────────────────────────────────────────────────────────
# Layout
# ─────────────────────────────────────────────────────────────────────────────
_CONTENT_FN = {
    "portfolio":   content_portfolio,
    "live_pos":    content_live_positions,
    "today_slate": content_today_slate,
    "resolved":    content_resolved,
    "alerts":      content_alerts,
    "system":      content_system,
    "pipe_log":    content_pipe_log,
}

_FIXED_PANELS  = {"portfolio", "system"}
_SCROLL_PANELS = [k for k in _CONTENT_FN if k not in _FIXED_PANELS]

_PANEL_TITLES = {
    "portfolio":   "PORTFOLIO",
    "live_pos":    "LIVE POSITIONS",
    "today_slate": "TODAY'S BETS",
    "resolved":    "RECENTLY RESOLVED",
    "alerts":      "ALERTS",
    "system":      "SYSTEM STATUS  │  PIPE-05",
    "pipe_log":    "PIPE-05 LOG TAIL",
}


def _compute_layout(max_y: int, max_x: int) -> dict:
    HEADER_H    = 3
    PORTFOLIO_H = 4
    SYSTEM_H    = 6   # KS + 4 pipe timestamps + border
    FOOTER_H    = 1
    FIXED       = HEADER_H + PORTFOLIO_H + SYSTEM_H + FOOTER_H

    available = max(6, max_y - FIXED)
    w1 = max(5, available * 4 // 12)
    w2 = max(4, available * 3 // 12)
    w3 = max(4, available * 2 // 12)
    w4 = max(4, available - w1 - w2 - w3)

    LEFT_W  = (max_x - 1) * 56 // 100
    RIGHT_W = max_x - LEFT_W - 1

    y = HEADER_H
    portfolio_spec = (y, 0, PORTFOLIO_H, max_x); y += PORTFOLIO_H

    live_pos_spec    = (y, 0,          w1, LEFT_W)
    today_slate_spec = (y, LEFT_W + 1, w1, RIGHT_W)
    y += w1

    resolved_spec = (y, 0, w2, max_x); y += w2
    alerts_spec   = (y, 0, w3, max_x); y += w3

    system_spec = (y, 0, SYSTEM_H, max_x); y += SYSTEM_H

    pipe_log_spec = (y, 0, w4, max_x); y += w4

    return {
        "portfolio":   portfolio_spec,
        "live_pos":    live_pos_spec,
        "today_slate": today_slate_spec,
        "resolved":    resolved_spec,
        "alerts":      alerts_spec,
        "system":      system_spec,
        "pipe_log":    pipe_log_spec,
        "_footer_y":   y,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Header / Footer
# ─────────────────────────────────────────────────────────────────────────────
def draw_header(stdscr, remote: str | None, max_x: int) -> None:
    now   = datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    src   = remote if remote else "LOCAL"
    title = "  PREDICTION MARKET BOT — MLB LIVE TERMINAL"
    tag   = f"  {now}  ◉ PAPER  {src}  "
    sep   = "═" * max_x
    try: stdscr.addstr(0, 0, sep[:max_x], curses.A_DIM)
    except curses.error: pass
    try:
        _addstr(stdscr, 1, 0, title, max_x)
        try: stdscr.addstr(1, max(0, max_x - len(tag) - 1), tag[:max_x], curses.A_DIM)
        except curses.error: pass
    except curses.error: pass
    try: stdscr.addstr(2, 0, sep[:max_x], curses.A_DIM)
    except curses.error: pass


def draw_footer(stdscr, footer_y: int, max_x: int) -> None:
    if footer_y >= stdscr.getmaxyx()[0]:
        return
    msg = "  [Tab] next panel  [↑↓] scroll  [PgUp/PgDn]  [Home/End]  [q] quit  │  BOT_ENV=paper  │  G6 OPEN"
    try: stdscr.addstr(footer_y, 0, msg[:max_x], curses.A_DIM)
    except curses.error: pass


# ─────────────────────────────────────────────────────────────────────────────
# Main curses loop
# ─────────────────────────────────────────────────────────────────────────────
def _curses_loop(stdscr, args: argparse.Namespace) -> None:
    _init_colors()
    curses.curs_set(0)
    stdscr.nodelay(True)

    panels: dict[str, PanelState] = {}
    last_layout: tuple = (0, 0)
    focus_idx    = 0
    last_data_ts = 0.0
    data: dict   = {}
    footer_y     = 0

    _fetch_state = _FetchState()
    _stop_event  = threading.Event()
    _thread = threading.Thread(
        target=_fetch_worker, args=(args, _fetch_state, _stop_event),
        daemon=True, name="pmbot-mlb-fetch",
    )
    _thread.start()

    def _make_panels(max_y: int, max_x: int) -> int:
        layout = _compute_layout(max_y, max_x)
        for pid, fn in _CONTENT_FN.items():
            spec = layout[pid]
            y0, x0, h, w = spec
            iw = max(1, w - 2)
            content = fn(data, iw)
            if pid in panels:
                ps = panels[pid]
                panels[pid] = PanelState(
                    title=ps.title, y=y0, x=x0, height=h, width=w,
                    scrollable=(pid not in _FIXED_PANELS),
                    scroll_y=ps.scroll_y, content=content, dirty=True,
                )
            else:
                panels[pid] = PanelState(
                    title=_PANEL_TITLES[pid], y=y0, x=x0, height=h, width=w,
                    scrollable=(pid not in _FIXED_PANELS),
                    scroll_y=0, content=content, dirty=True,
                )
        return layout.get("_footer_y", max_y - 1)

    while True:
        max_y, max_x = stdscr.getmaxyx()

        with _fetch_state.lock:
            _ts_now = _fetch_state.last_ok
            _new    = _fetch_state.data

        if _ts_now != last_data_ts and _new:
            data         = _new
            last_data_ts = _ts_now
            footer_y     = _make_panels(max_y, max_x)
            last_layout  = (max_y, max_x)

        if (max_y, max_x) != last_layout and panels:
            footer_y    = _make_panels(max_y, max_x)
            last_layout = (max_y, max_x)

        if not panels:
            c = stdscr.getch()
            if c in (ord("q"), ord("Q"), 3):
                _stop_event.set()
                return
            stdscr.erase()
            stdscr.addstr(max_y // 2, max(0, max_x // 2 - 18),
                          "  Connecting...  ", curses.A_DIM)
            stdscr.refresh()
            time.sleep(0.05)
            continue

        focused_id = _SCROLL_PANELS[focus_idx % len(_SCROLL_PANELS)]
        while True:
            c = stdscr.getch()
            if c == -1:
                break
            if c in (ord("q"), ord("Q"), 3):
                _stop_event.set()
                return
            elif c == 9:          # Tab
                focus_idx  = (focus_idx + 1) % len(_SCROLL_PANELS)
                focused_id = _SCROLL_PANELS[focus_idx]
            elif c == curses.KEY_BTAB:
                focus_idx  = (focus_idx - 1) % len(_SCROLL_PANELS)
                focused_id = _SCROLL_PANELS[focus_idx]
            else:
                ps = panels.get(focused_id)
                if ps:
                    ms      = _panel_max_scroll(ps)
                    inner_h = ps.height - 2
                    if c == curses.KEY_DOWN:  ps.scroll_y = min(ps.scroll_y + 1, ms)
                    elif c == curses.KEY_UP:  ps.scroll_y = max(ps.scroll_y - 1, 0)
                    elif c == curses.KEY_NPAGE: ps.scroll_y = min(ps.scroll_y + max(1, inner_h - 1), ms)
                    elif c == curses.KEY_PPAGE: ps.scroll_y = max(ps.scroll_y - max(1, inner_h - 1), 0)
                    elif c == curses.KEY_HOME:  ps.scroll_y = 0
                    elif c == curses.KEY_END:   ps.scroll_y = ms

        stdscr.erase()
        draw_header(stdscr, args.remote, max_x)
        for pid, ps in panels.items():
            draw_panel(stdscr, ps, focused=(pid == focused_id), max_y=max_y, max_x=max_x)
        draw_footer(stdscr, footer_y, max_x)
        stdscr.noutrefresh()
        for ps in panels.values():
            refresh_pad(ps, max_y, max_x)
        curses.doupdate()
        time.sleep(0.016)


# ─────────────────────────────────────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────────────────────────────────────
def main() -> None:
    p = argparse.ArgumentParser(description="MLB Live Bloomberg-style terminal dashboard")
    p.add_argument("--log-dir",  default=os.environ.get("LOG_DIR", "logs/"),
                   help="Logs directory. Default: logs/")
    p.add_argument("--remote",   default=None,
                   help="SSH host, e.g. root@157.230.91.33")
    p.add_argument("--interval", type=int, default=30,
                   help="Data refresh interval in seconds (default: 30)")
    p.add_argument("--once", action="store_true",
                   help="Dump content to stdout (debug)")
    args = p.parse_args()

    if args.once:
        data = (fetch_remote(args.remote, args.log_dir)
                if args.remote else _data_from_local(args.log_dir))
        for pid, fn in _CONTENT_FN.items():
            print(f"\n=== {pid} ===")
            for line in fn(data, 100):
                print(_ANSI_RE.sub("", line))
        return

    try:
        curses.wrapper(lambda stdscr: _curses_loop(stdscr, args))
    except KeyboardInterrupt:
        pass
    print("\n  Terminal stopped.")


if __name__ == "__main__":
    main()
