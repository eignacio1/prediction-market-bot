#!/usr/bin/env python3
"""
Live Terminal — Bloomberg-style multi-pane dashboard for the Prediction Market Bot.

Each panel is an independent scrollable window.  Navigate with:
    Tab / Shift+Tab   cycle focused panel
    ↑ ↓               scroll one line in focused panel
    PgUp / PgDn       scroll one page in focused panel
    Home / End        jump to top / bottom of focused panel
    q / Ctrl+C        quit

Run locally (renders on Mac — curses double-buffer, zero flicker):
    python3 scripts/live_terminal.py --remote root@157.230.91.33 \\
        --log-dir /opt/prediction-market-bot/logs/
"""

from __future__ import annotations

import argparse
import curses
import json
import locale
import os
import re
import shlex
import shutil
import subprocess
import sys
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

locale.setlocale(locale.LC_ALL, "")

# ─────────────────────────────────────────────────────────────────────────────
# ANSI colour constants  (used when building content strings)
# ─────────────────────────────────────────────────────────────────────────────
RESET    = "\033[0m"
BOLD     = "\033[1m"
DIM      = "\033[2m"
GREEN    = "\033[32m"
RED      = "\033[31m"
YELLOW   = "\033[33m"
CYAN     = "\033[36m"
MAGENTA  = "\033[35m"
BG_RED   = "\033[41m"

_ANSI_RE       = re.compile(r"\033\[[0-9;]*m")
_ANSI_TOKEN_RE = re.compile(r"(\033\[[0-9;]*m)")


def _c(*parts: str) -> str:
    codes = [p for p in parts if p.startswith("\033")]
    text  = "".join(p for p in parts if not p.startswith("\033"))
    return "".join(codes) + text + RESET


def _vlen(s: str) -> int:
    return len(_ANSI_RE.sub("", s))


def _fit(s: str, w: int) -> str:
    """Pad or truncate a (possibly ANSI-coloured) string to exactly w visible chars."""
    vis = _vlen(s)
    if vis < w:
        return s + " " * (w - vis)
    if vis > w:
        # Strip colour codes and hard-truncate
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
_CP_FOCUS   = 7   # focused panel title

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
# Low-level ANSI → curses writer
# ─────────────────────────────────────────────────────────────────────────────
def _addstr(win, y: int, x: int, line: str, max_x: int) -> None:
    """Write one ANSI-coloured string into a curses window at (y, x)."""
    bold = False
    dim  = False
    cp   = 0
    cx   = x
    for token in _ANSI_TOKEN_RE.split(line):
        if not token:
            continue
        if token.startswith("\033[") and token.endswith("m"):
            codes_str = token[2:-1]
            for part in (codes_str.split(";") if codes_str else [""]):
                try:
                    n = int(part) if part else 0
                except ValueError:
                    continue
                if n == 0:
                    bold = dim = False; cp = 0
                elif n == 1: bold = True
                elif n == 2: dim = True
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
    return datetime.now(tz=timezone.utc).strftime("%Y%m%d")


def _ts(iso: str) -> str:
    return iso[:19].replace("T", " ") if iso else "—"


def _pnl(v: float) -> str:
    if v > 0: return _c(GREEN, BOLD, f"+${v:.2f}")
    if v < 0: return _c(RED, BOLD, f"-${abs(v):.2f}")
    return "$0.00"


def _edge(v: float | None) -> str:
    if v is None: return _c(DIM, "  N/A  ")
    if v >= 0.03: return _c(GREEN, f"{v:+.4f}")
    if v > 0:     return _c(YELLOW, f"{v:+.4f}")
    return _c(DIM, f"{v:+.4f}")


def _dir(d: str) -> str:
    if d == "YES": return _c(GREEN, BOLD, "YES")
    if d == "NO":  return _c(RED, "NO ")
    if d in ("PASS", "SKIP", ""): return _c(DIM, " — ")
    return _pad_s(d, 3)


def _outcome(o: str) -> str:
    if o == "WIN":  return _c(GREEN, BOLD, "WIN ")
    if o == "LOSS": return _c(RED, BOLD, "LOSS")
    return _pad_s(o, 4)


def _dd(pct: float) -> str:
    if pct >= 15: return _c(RED, BOLD, f"{pct:.2f}%")
    if pct >= 5:  return _c(YELLOW, f"{pct:.2f}%")
    return _c(GREEN, f"{pct:.2f}%")


def _ks(active: bool, reason: str | None) -> str:
    if active:
        return _c(BG_RED, BOLD, " ⚠  KILL SWITCH ACTIVE  ⚠ ") + (f" ({reason})" if reason else "")
    return _c(GREEN, "ARMED ✓")

# ─────────────────────────────────────────────────────────────────────────────
# Data loaders
# ─────────────────────────────────────────────────────────────────────────────
def _load_json(p: Path) -> dict | list:
    try:
        with open(p) as f:
            return json.load(f)
    except Exception:
        return {}


def _load_jsonl(p: Path, tail: int = 300) -> list[dict]:
    if not p.exists():
        return []
    entries: list[dict] = []
    with open(p) as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
    return entries[-tail:]


def _load_tail(p: Path, n: int = 10) -> list[str]:
    if not p.exists():
        return []
    with open(p) as f:
        lines = f.readlines()
    return [l.rstrip() for l in lines[-n:]]


def _data_from_local(log_dir: str) -> dict:
    d = Path(log_dir)
    td = _today()
    portfolio = _load_json(d / "paper_portfolio.json")
    bets_raw  = _load_json(d / f"paper_{td}.json")
    return {
        "portfolio":    portfolio,
        "t4_portfolio": _load_json(d / "paper_portfolio_t4.json"),
        "bets":         bets_raw.get("orders", []) if isinstance(bets_raw, dict) else [],
        "pregame":      _load_json(d / f"pregame_{td}.json"),
        "audit":        _load_jsonl(d / "audit.jsonl"),
        "t4_tail":      _load_tail(d / "t4_live_cron.log", n=25),
    }

# ─────────────────────────────────────────────────────────────────────────────
# Background fetch thread — decouples SSH latency from the render loop
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
# Remote fetch — single SSH round-trip with ControlMaster
# ─────────────────────────────────────────────────────────────────────────────
_SSH_CTL = "/tmp/pmbot-ssh-ctl"

_REMOTE_SCRIPT = r"""
import json, sys
from pathlib import Path
from datetime import datetime, timezone

log_dir = sys.argv[1]
today = datetime.now(tz=timezone.utc).strftime('%Y%m%d')
d = Path(log_dir)
result = {}

def rj(p):
    with open(p) as f: return json.load(f)

def rjl(p, tail=300):
    e = []
    with open(p) as f:
        for line in f:
            line = line.strip()
            if line:
                try: e.append(json.loads(line))
                except: pass
    return e[-tail:]

def rt(p, n=10):
    with open(p) as f: lines = f.readlines()
    return [l.rstrip() for l in lines[-n:]]

for key, path, fn, args in [
    ('portfolio',    d / 'paper_portfolio.json',    rj,  []),
    ('t4_portfolio', d / 'paper_portfolio_t4.json', rj,  []),
    ('bets_raw',     d / f'paper_{today}.json',     rj,  []),
    ('pregame',      d / f'pregame_{today}.json',   rj,  []),
    ('audit',        d / 'audit.jsonl',             rjl, [300]),
    ('t4_tail',      d / 't4_live_cron.log',         rt,  [25]),
]:
    try:
        result[key] = fn(path, *args)
    except Exception:
        result[key] = {} if key in ('portfolio', 'pregame', 'bets_raw', 't4_portfolio') else []

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
        if not raw:
            return {}
        d = json.loads(raw)
        # Normalise bets key
        bets_raw = d.get("bets_raw", {})
        d["bets"] = bets_raw.get("orders", []) if isinstance(bets_raw, dict) else []
        d.setdefault("t4_portfolio", {})
        return d
    except Exception:
        return {}

# ─────────────────────────────────────────────────────────────────────────────
# Panel content producers  (return list[str] of raw content lines, no borders)
# Each line is an ANSI string that will be _fit() to inner_w before display.
# ─────────────────────────────────────────────────────────────────────────────
def _hdr_row(cols: list[tuple[str, int, str]]) -> str:
    """Build a header row from (text, width, align) tuples."""
    return "  " + "  ".join(_pad_s(t, w, a) for t, w, a in cols)


def content_portfolio(data: dict, iw: int) -> list[str]:
    p = data.get("portfolio", {})
    if not p:
        return ["  (portfolio file not found)"]
    bankroll = float(p.get("bankroll_usd", 0))
    initial  = float(p.get("initial_bankroll_usd", 1000))
    pnl      = float(p.get("total_realized_pnl", 0))
    dl       = float(p.get("current_daily_loss", 0))
    open_p   = p.get("open_positions", [])
    closed_p = p.get("closed_positions", [])
    deployed = sum(float(x.get("size_usd", 0)) for x in open_p)
    dd_pct   = max(0.0, -pnl / initial * 100) if initial > 0 else 0.0
    wins     = sum(1 for x in closed_p if x.get("outcome") == "WIN")
    losses   = sum(1 for x in closed_p if x.get("outcome") == "LOSS")
    total    = wins + losses
    wr       = f"{wins/total:.1%}" if total else "N/A"
    dl_col   = _c(RED, f"${dl:.2f}") if dl > 0 else f"${dl:.2f}"

    return [
        f"  Bankroll: {_c(BOLD,CYAN,f'${bankroll:,.2f}')}   "
        f"Initial: ${initial:,.2f}   "
        f"P&L: {_pnl(pnl)}   "
        f"Drawdown: {_dd(dd_pct)}   "
        f"Daily Loss: {dl_col}",

        f"  Open: {_c(BOLD,str(len(open_p)))} pos   "
        f"Deployed: ${deployed:.2f}   "
        f"Win/Loss: {wins}/{losses}   "
        f"Win Rate: {wr}   "
        f"Resolved: {total}",
    ]


def content_live_positions(data: dict, iw: int) -> list[str]:
    open_pos = data.get("portfolio", {}).get("open_positions", [])
    if not open_pos:
        return ["  (no open positions)"]
    lines = [_c(DIM, f"  {'PLAYER':<20} {'DIR':<3}  {'SIZE':>8}  {'MODEL_P':>8}  {'MKT_P':>7}  {'NET_EDGE':>9}  ⚑  ENTERED")]
    lines.append("  " + "─" * (iw - 2))
    for pos in open_pos:
        player  = _pad_s(pos.get("player_name", "?"), 20)
        dirn    = _dir(pos.get("direction", "?"))
        size    = _pad_s(f"${pos.get('size_usd',0):.2f}", 8, "right")
        mp      = _pad_s(f"{pos.get('model_p',0):.4f}", 8, "right")
        mktp    = _pad_s(f"{pos.get('mid_price_at_entry',0):.4f}", 7, "right")
        ne      = _edge(pos.get("fee_net_edge"))
        inj     = _c(YELLOW, "⚑") if pos.get("probable_injury_signal") else " "
        entered = _ts(pos.get("entered_at", ""))[:16]
        lines.append(f"  {player} {dirn}  {size}  {mp}  {mktp}  {ne}  {inj}  {entered}")
    return lines


def content_market_snapshot(data: dict, iw: int) -> list[str]:
    pg = data.get("pregame", {})
    forecasts = pg.get("forecasts", [])
    if not forecasts:
        return [
            f"  Session: {pg.get('session_id','?')}   Run: {_ts(pg.get('run_at',''))}",
            "  (no forecasts — PIPE-02 fires at 21:55 UTC)",
        ]
    act  = sorted([f for f in forecasts if f.get("edge", -1) > 0], key=lambda x: -x.get("edge", 0))
    rest = [f for f in forecasts if f.get("edge", -1) <= 0]

    header = (f"  {pg.get('session_id','?')}  ·  "
              f"{pg.get('players_matched','?')} players  ·  "
              f"{pg.get('markets_logged','?')} markets  ·  "
              f"{_c(GREEN,str(pg.get('actionable','?')))} actionable")
    lines = [header, _c(DIM, f"  {'PLAYER':<18} {'THR':>4}  {'DIR':<3}  {'MODEL_P':>8}  {'MKT_P':>7}  {'EDGE':>8}  ACT")]
    lines.append("  " + "─" * (iw - 2))

    for bucket, rows in [(True, act), (False, rest)]:
        if not rows:
            continue
        if not bucket and act:
            lines.append(_c(DIM, "  — below threshold —"))
        for f in rows:
            player  = _pad_s(f.get("player_name", "?"), 18)
            thr     = _pad_s(str(f.get("kalshi_threshold", "?")), 4, "right")
            dirn    = _dir(f.get("direction", "?"))
            mp_val  = f.get("p_estimate", 0)
            mp      = _pad_s(f"{mp_val:.4f}", 8, "right")
            mkt_val = f.get("mid_price", 0)
            mkt     = _pad_s(f"{mkt_val:.4f}", 7, "right")
            e       = _edge(f.get("edge"))
            act_tag = _c(GREEN, BOLD, "✓") if f.get("edge", 0) > 0 else _c(DIM, " ")
            lines.append(f"  {player} {thr}  {dirn}  {mp}  {mkt}  {e}  {act_tag}")

    return lines


def content_today_bets(data: dict, iw: int) -> list[str]:
    bets = data.get("bets", [])
    td = _today()
    if not bets:
        return [f"  {td[:4]}-{td[4:6]}-{td[6:]} — (no bets yet / PIPE-03 at 22:00 UTC)"]
    lines = [_c(DIM, f"  {'#':>3}  {'PLAYER':<20}  {'DIR':<3}  {'SIZE':>8}  {'STATUS':<8}  {'KALSHI':<10}  ENTERED")]
    lines.append("  " + "─" * (iw - 2))
    for i, bet in enumerate(bets, 1):
        status = bet.get("status", "?")
        k_stat = bet.get("kalshi_order_status", "?")
        s_col  = (_c(GREEN, status) if status == "OPEN" else
                  _c(YELLOW, status) if status == "CLOSED" else _c(DIM, status))
        k_col  = (_c(GREEN, k_stat) if k_stat in ("resting", "filled") else
                  _c(RED, k_stat) if "failed" in k_stat else _c(DIM, k_stat))
        size   = f"${bet.get('size_usd', 0):.2f}"
        lines.append(
            f"  {i:>3}  {_pad_s(bet.get('player_name','?'),20)}  "
            f"{_dir(bet.get('direction','?'))}  "
            f"{_pad_s(size,8,'right')}  {s_col}  {k_col}  "
            f"{_ts(bet.get('entered_at',''))[:16]}"
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
        sev  = e.get("severity", "?")
        pl   = e.get("payload", {}) if isinstance(e.get("payload"), dict) else {}
        detail = str(pl.get("reason", pl.get("trigger", pl.get("error", "")))).strip()[:28]
        sev_col = (_c(BG_RED, BOLD, f" {sev:<8}") if sev == "CRITICAL" else
                   _c(RED, f"{sev:<8}") if sev == "ERROR" else
                   _c(YELLOW, f"{sev:<8}"))
        lines.append(
            f"  {_ts(e.get('timestamp',''))}  {sev_col}  "
            f"{_pad_s(e.get('component','?'),8)}  "
            f"{_pad_s(e.get('event_type','?'),22)}  {_c(DIM,detail)}"
        )
    return lines


def content_resolved(data: dict, iw: int) -> list[str]:
    closed = data.get("portfolio", {}).get("closed_positions", [])
    if not closed:
        return ["  (none resolved — PIPE-03R runs at 06:00 UTC)"]
    wins = sum(1 for p in closed if p.get("outcome") == "WIN")
    losses = sum(1 for p in closed if p.get("outcome") == "LOSS")
    total_pnl = sum(float(p.get("pnl", 0)) for p in closed)
    lines = [
        f"  {_c(BOLD,f'{wins}W / {losses}L')}   Cumulative P&L: {_pnl(total_pnl)}",
        _c(DIM, f"  {'PLAYER':<20}  {'DIR':<3}  {'ACTUAL':>6}  {'RESULT':<6}  {'P&L':>8}  RESOLVED"),
        "  " + "─" * (iw - 2),
    ]
    for pos in reversed(closed):
        actual = _pad_s(str(int(pos["actual_pts"])) if pos.get("actual_pts") is not None else "?", 6, "right")
        lines.append(
            f"  {_pad_s(pos.get('player_name','?'),20)}  "
            f"{_dir(pos.get('direction','?'))}  "
            f"{actual}  {_outcome(pos.get('outcome','?'))}  "
            f"{_pnl(float(pos.get('pnl',0)))}  "
            f"{_ts(pos.get('resolved_at',''))[:16]}"
        )
    return lines


def content_system_t4(data: dict, iw: int) -> list[str]:
    audit   = data.get("audit", [])
    t4_tail = data.get("t4_tail", [])

    ks_active = False
    ks_reason: str | None = None
    for e in reversed(audit):
        if e.get("event_type") == "kill_switch_triggered":
            ks_active = True
            ks_reason = (e.get("payload") or {}).get("reason") or (e.get("payload") or {}).get("trigger")
            break
        if e.get("event_type") == "kill_switch_reset":
            break

    game_status = "STATUS_SCHEDULED"
    last_poll   = "?"
    t4_hint     = ""
    for line in reversed(t4_tail):
        m_s = re.search(r"status=(STATUS_\w+)", line)
        m_t = re.search(r"(\d{2}:\d{2}:\d{2}),\d+", line)
        m_d = re.search(r"deployed[:\s]+\$?([\d.]+)", line, re.IGNORECASE)
        if m_s: game_status = m_s.group(1)
        if m_t: last_poll = m_t.group(1) + "Z"
        if m_d: t4_hint = f"  T4 deployed: ~${m_d.group(1)}"
        if m_s: break

    gs_col = (_c(GREEN, BOLD, game_status) if game_status == "STATUS_IN_PROGRESS" else
              _c(YELLOW, game_status) if game_status == "STATUS_FINAL" else
              _c(DIM, game_status))

    last_comp = last_evt = last_ts = "?"
    if audit:
        last = audit[-1]
        last_comp = last.get("component", "?")
        last_evt  = last.get("event_type", "?")
        last_ts   = _ts(last.get("timestamp", ""))

    last_seen: dict[str, str] = {}
    for e in audit:
        last_seen[e.get("component", "?")] = e.get("timestamp", "")[:16].replace("T", " ")

    comp_order = ["C1","C2","C3","C4","C5","C6","C7","PIPE-02","PIPE-03","PIPE-03R"]
    comp_line  = "  " + "  │  ".join(
        f"{c}: {_c(DIM, last_seen[c])}" for c in comp_order if c in last_seen
    )

    return [
        f"  KS: {_ks(ks_active, ks_reason)}   T4: {gs_col}   poll: {last_poll}{t4_hint}",
        f"  Last: {last_ts}  {last_comp}/{last_evt}",
        comp_line,
    ]


def content_t4_log(data: dict, iw: int) -> list[str]:
    lines = data.get("t4_tail", [])
    if not lines:
        return ["  (no t4_live.log)"]
    result = []
    for line in lines:
        col = (GREEN if "STATUS_IN_PROGRESS" in line else
               YELLOW if "STATUS_FINAL" in line else
               RED if ("ERROR" in line or "error" in line) else
               CYAN if ("bet" in line.lower() or "approved" in line.lower()) else
               DIM)
        bold_flag = BOLD if col == GREEN else ""
        result.append("  " + _c(col, bold_flag, line[:iw - 2]))
    return result

# ─────────────────────────────────────────────────────────────────────────────
# Panel drawing
# ─────────────────────────────────────────────────────────────────────────────
@dataclass
class PanelState:
    title:      str
    y: int;  x: int
    height: int;  width: int
    scrollable: bool
    scroll_y:   int = 0
    content:    list[str] = field(default_factory=list)
    pad:        object = field(default=None, repr=False)
    dirty:      bool = True


def _panel_max_scroll(ps: PanelState) -> int:
    inner_h = ps.height - 2
    return max(0, len(ps.content) - inner_h)


def _rebuild_pad(ps: PanelState) -> None:
    inner_h = max(1, ps.height - 2)
    inner_w = max(1, ps.width - 2)
    ph = max(len(ps.content) + 1, inner_h + 1)
    pw = inner_w + 1
    try:
        ps.pad = curses.newpad(ph, pw)
        for i, line in enumerate(ps.content):
            _addstr(ps.pad, i, 0, _fit(line, inner_w), inner_w)
    except curses.error:
        ps.pad = None
    ps.dirty = False


def draw_panel(stdscr, ps: PanelState, focused: bool, max_y: int, max_x: int) -> None:
    if ps.y >= max_y or ps.x >= max_x:
        return

    W = min(ps.width, max_x - ps.x)
    H = min(ps.height, max_y - ps.y)
    inner_w = W - 2
    inner_h = H - 2

    if ps.dirty:
        _rebuild_pad(ps)

    ms = _panel_max_scroll(ps)
    ps.scroll_y = max(0, min(ps.scroll_y, ms))

    # Top border
    focus_attr  = curses.color_pair(_CP_FOCUS) | curses.A_BOLD if focused else curses.A_NORMAL
    dim_attr    = curses.A_DIM
    title_seg   = f" {ps.title} "
    fill        = max(0, inner_w - len(title_seg))

    if ms > 0:
        pct       = int(ps.scroll_y / ms * 100) if ms else 0
        indicator = f" ↕{pct}% "
        fill      = max(0, fill - len(indicator))
    else:
        indicator = ""

    top = "┌─" + title_seg + "─" * fill + indicator + "─┐"
    try:
        if focused:
            stdscr.addstr(ps.y, ps.x, top[:W], curses.color_pair(_CP_FOCUS) | curses.A_BOLD)
        else:
            stdscr.addstr(ps.y, ps.x, top[:W], curses.A_NORMAL)
    except curses.error:
        pass

    # Side borders
    for dy in range(inner_h):
        ry = ps.y + 1 + dy
        if ry >= max_y:
            break
        try:
            stdscr.addstr(ry, ps.x, "│", curses.A_DIM)
        except curses.error:
            pass
        try:
            stdscr.addstr(ry, ps.x + W - 1, "│", curses.A_DIM)
        except curses.error:
            pass

    # Bottom border
    by = ps.y + H - 1
    if by < max_y:
        try:
            stdscr.addstr(by, ps.x, "└" + "─" * inner_w + "┘", curses.A_DIM)
        except curses.error:
            pass

    # NOTE: pad noutrefresh is NOT called here — it must happen AFTER stdscr.noutrefresh()
    # so pad content wins over the blank cells erased on stdscr. Call refresh_pad() separately.

def refresh_pad(ps: PanelState, max_y: int, max_x: int) -> None:
    """Flush a panel's pad to the physical screen region. Call AFTER stdscr.noutrefresh()."""
    if ps.pad is None:
        return
    W = min(ps.width, max_x - ps.x)
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
# Layout computation
# ─────────────────────────────────────────────────────────────────────────────
PANEL_ORDER = [
    "live_pos", "mkt_snap", "bets", "alerts", "resolved", "t4_log",
]
PANEL_SCROLL_ORDER = PANEL_ORDER  # all scrollable (system/portfolio are fixed)


def _compute_layout(max_y: int, max_x: int) -> dict[str, tuple[int,int,int,int]]:
    """Return {panel_id: (y, x, height, width)} for current terminal size."""
    HEADER_H    = 3
    PORTFOLIO_H = 4  # border + 2 content lines + border
    SYSTEM_H    = 5  # border + 3 content lines + border
    FOOTER_H    = 1
    FIXED       = HEADER_H + PORTFOLIO_H + SYSTEM_H + FOOTER_H

    available = max(4, max_y - FIXED)
    # Allocate: 2col_row1(4), 2col_row2(3), resolved(2), t4_log(3)  → weights sum=12
    w1  = max(5, available * 4 // 12)
    w2  = max(4, available * 3 // 12)
    w3  = max(4, available * 2 // 12)
    w4  = max(4, available - w1 - w2 - w3)

    LEFT_W  = (max_x - 1) * 56 // 100
    RIGHT_W = max_x - LEFT_W - 1

    y = HEADER_H
    portfolio_spec = (y, 0, PORTFOLIO_H, max_x)
    y += PORTFOLIO_H

    live_pos_spec = (y, 0,          w1, LEFT_W)
    mkt_snap_spec = (y, LEFT_W + 1, w1, RIGHT_W)
    y += w1

    bets_spec    = (y, 0,          w2, LEFT_W)
    alerts_spec  = (y, LEFT_W + 1, w2, RIGHT_W)
    y += w2

    resolved_spec = (y, 0, w3, max_x)
    y += w3

    system_spec = (y, 0, SYSTEM_H, max_x)
    y += SYSTEM_H

    t4_log_spec = (y, 0, w4, max_x)
    y += w4

    footer_y = y

    return {
        "portfolio": portfolio_spec,
        "live_pos":  live_pos_spec,
        "mkt_snap":  mkt_snap_spec,
        "bets":      bets_spec,
        "alerts":    alerts_spec,
        "resolved":  resolved_spec,
        "system":    system_spec,
        "t4_log":    t4_log_spec,
        "_footer_y": footer_y,
    }

# ─────────────────────────────────────────────────────────────────────────────
# Header renderer (full-width, 3 lines, drawn directly to stdscr)
# ─────────────────────────────────────────────────────────────────────────────
def draw_header(stdscr, remote: str | None, max_x: int) -> None:
    now   = datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    src   = remote if remote else "LOCAL"
    title = "  PREDICTION MARKET BOT — LIVE TERMINAL"
    tag   = f"  {now}  ◉ PAPER  {src}  "
    sep   = "═" * max_x

    try:
        stdscr.addstr(0, 0, sep[:max_x], curses.A_DIM)
    except curses.error:
        pass
    try:
        _addstr(stdscr, 1, 0, title, max_x)
        info_attr = curses.A_DIM
        try:
            stdscr.addstr(1, max(0, max_x - len(tag) - 1), tag[:max_x], info_attr)
        except curses.error:
            pass
    except curses.error:
        pass
    try:
        stdscr.addstr(2, 0, sep[:max_x], curses.A_DIM)
    except curses.error:
        pass

# ─────────────────────────────────────────────────────────────────────────────
# Footer (controls hint)
# ─────────────────────────────────────────────────────────────────────────────
def draw_footer(stdscr, footer_y: int, max_x: int) -> None:
    if footer_y >= stdscr.getmaxyx()[0]:
        return
    msg = "  [Tab] next panel  [↑↓] scroll  [PgUp/PgDn]  [Home/End]  [q] quit  │  BOT_ENV=paper  │  G6 OPEN"
    try:
        stdscr.addstr(footer_y, 0, msg[:max_x], curses.A_DIM)
    except curses.error:
        pass

# ─────────────────────────────────────────────────────────────────────────────
# Main curses loop
# ─────────────────────────────────────────────────────────────────────────────
_CONTENT_FN = {
    "portfolio": content_portfolio,
    "live_pos":  content_live_positions,
    "mkt_snap":  content_market_snapshot,
    "bets":      content_today_bets,
    "alerts":    content_alerts,
    "resolved":  content_resolved,
    "system":    content_system_t4,
    "t4_log":    content_t4_log,
}

_FIXED_PANELS  = {"portfolio", "system"}
_SCROLL_PANELS = [k for k in _CONTENT_FN if k not in _FIXED_PANELS]


def _curses_loop(stdscr, args: argparse.Namespace) -> None:
    _init_colors()
    curses.curs_set(0)
    stdscr.nodelay(True)

    # Panel state registry
    panels: dict[str, PanelState] = {}
    last_layout: tuple = (0, 0)

    focus_idx    = 0
    last_data_ts = 0.0
    data: dict   = {}

    _fetch_state = _FetchState()
    _stop_event  = threading.Event()
    _thread      = threading.Thread(
        target=_fetch_worker, args=(args, _fetch_state, _stop_event),
        daemon=True, name="pmbot-fetch",
    )
    _thread.start()

    def _make_panels(max_y: int, max_x: int) -> None:
        layout = _compute_layout(max_y, max_x)
        for pid, fn in _CONTENT_FN.items():
            spec = layout[pid]
            y0, x0, h, w = spec
            iw = max(1, w - 2)
            content = fn(data, iw)
            if pid in panels:
                ps = panels[pid]
                old_scroll = ps.scroll_y
                panels[pid] = PanelState(
                    title=ps.title, y=y0, x=x0, height=h, width=w,
                    scrollable=(pid not in _FIXED_PANELS),
                    scroll_y=old_scroll, content=content, dirty=True,
                )
            else:
                title_map = {
                    "portfolio": "PORTFOLIO",
                    "live_pos":  "LIVE POSITIONS",
                    "mkt_snap":  "MARKET SNAPSHOT",
                    "bets":      "TODAY'S BETS",
                    "alerts":    "ALERTS",
                    "resolved":  "RECENTLY RESOLVED",
                    "system":    "SYSTEM STATUS  │  T4 LIVE",
                    "t4_log":    "T4 LOG TAIL",
                }
                panels[pid] = PanelState(
                    title=title_map[pid], y=y0, x=x0, height=h, width=w,
                    scrollable=(pid not in _FIXED_PANELS),
                    scroll_y=0, content=content, dirty=True,
                )
        return layout.get("_footer_y", max_y - 1)

    footer_y = 0

    while True:
        now          = time.time()
        max_y, max_x = stdscr.getmaxyx()

        # ── Pick up fresh data from background fetch thread ────────────────
        with _fetch_state.lock:
            _ts_now = _fetch_state.last_ok
            _new    = _fetch_state.data

        if _ts_now != last_data_ts and _new:
            data         = _new
            last_data_ts = _ts_now
            footer_y     = _make_panels(max_y, max_x)
            last_layout  = (max_y, max_x)

        # ── Rebuild on terminal resize ─────────────────────────────────────
        if (max_y, max_x) != last_layout and panels:
            footer_y = _make_panels(max_y, max_x)
            last_layout = (max_y, max_x)

        # ── Initial render on startup ──────────────────────────────────────
        if not panels:
            # Show connecting message immediately while first fetch runs.
            # Still drain keys so 'q' works before data arrives.
            c = stdscr.getch()
            if c in (ord("q"), ord("Q"), 3):
                _stop_event.set()
                return
            stdscr.erase()
            stdscr.addstr(max_y // 2, max(0, max_x // 2 - 15),
                          "  Connecting to VPS...  ", curses.A_DIM)
            stdscr.refresh()
            time.sleep(0.05)
            continue

        # ── Input — drain full key queue before drawing ────────────────────
        # Processing all pending keys first means the draw reflects the final
        # scroll position immediately, and held-key acceleration works at
        # whatever rate the OS fires key-repeat events.
        focused_id = _SCROLL_PANELS[focus_idx % len(_SCROLL_PANELS)]
        while True:
            c = stdscr.getch()
            if c == -1:
                break
            if c in (ord("q"), ord("Q"), 3):
                _stop_event.set()
                return
            elif c == 9:  # Tab — next panel
                focus_idx  = (focus_idx + 1) % len(_SCROLL_PANELS)
                focused_id = _SCROLL_PANELS[focus_idx]
            elif c == curses.KEY_BTAB:  # Shift+Tab — prev panel
                focus_idx  = (focus_idx - 1) % len(_SCROLL_PANELS)
                focused_id = _SCROLL_PANELS[focus_idx]
            else:
                ps = panels.get(focused_id)
                if ps:
                    ms      = _panel_max_scroll(ps)
                    inner_h = ps.height - 2
                    if c == curses.KEY_DOWN:
                        ps.scroll_y = min(ps.scroll_y + 1, ms)
                    elif c == curses.KEY_UP:
                        ps.scroll_y = max(ps.scroll_y - 1, 0)
                    elif c == curses.KEY_NPAGE:
                        ps.scroll_y = min(ps.scroll_y + max(1, inner_h - 1), ms)
                    elif c == curses.KEY_PPAGE:
                        ps.scroll_y = max(ps.scroll_y - max(1, inner_h - 1), 0)
                    elif c == curses.KEY_HOME:
                        ps.scroll_y = 0
                    elif c == curses.KEY_END:
                        ps.scroll_y = ms

        # ── Draw ───────────────────────────────────────────────────────────
        stdscr.erase()
        draw_header(stdscr, args.remote, max_x)

        for pid, ps in panels.items():
            draw_panel(stdscr, ps, focused=(pid == focused_id), max_y=max_y, max_x=max_x)

        draw_footer(stdscr, footer_y, max_x)

        # stdscr MUST be noutrefreshed BEFORE pads. stdscr erased the content
        # areas with blank cells; pads must win by being queued last.
        stdscr.noutrefresh()
        for ps in panels.values():
            refresh_pad(ps, max_y, max_x)
        curses.doupdate()

        time.sleep(0.016)

# ─────────────────────────────────────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────────────────────────────────────
def main() -> None:
    p = argparse.ArgumentParser(description="Live Bloomberg-style multi-pane terminal dashboard")
    p.add_argument("--log-dir",  default=os.environ.get("LOG_DIR", "logs/"),
                   help="Logs directory (local or remote). Default: logs/")
    p.add_argument("--remote",   default=None,
                   help="SSH host, e.g. root@157.230.91.33")
    p.add_argument("--interval", type=int, default=1,
                   help="Data refresh interval in seconds (default: 1)")
    p.add_argument("--once", action="store_true",
                   help="Dump content panels to stdout (debug)")
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
