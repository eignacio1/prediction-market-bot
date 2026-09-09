#!/usr/bin/env python3
"""
Web Dashboard — Prediction Market Bot (MLB)
===========================================
Self-contained HTTP server. No external dependencies — stdlib only (Python 3.8+).

WHY THIS EXISTS
  The curses TUI (live_terminal.py / run_mlb_dashboard.py) crashes whenever:
    - Your terminal window is resized while curses is rendering
    - The SSH connection drops for any reason (network hiccup, laptop sleep, etc.)
    - The tmux session loses its controlling terminal
  Curses requires a live, stable terminal connection and a fixed size. It is
  structurally incompatible with how you use the dashboard (open a terminal,
  attach, close the terminal, reopen later).

  This replaces it with a process that runs permanently on the VPS and serves
  a browser page. If your SSH connection drops, the server keeps running. You
  just reconnect and reload the page. No state is lost, nothing crashes.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
DEPLOY (one-time setup on VPS)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  scp scripts/web_dashboard.py root@157.230.91.33:/opt/prediction-market-bot/scripts/
  scp scripts/pmbot-web-dashboard.service root@157.230.91.33:/etc/systemd/system/
  ssh root@157.230.91.33 "systemctl daemon-reload && systemctl enable --now pmbot-web-dashboard"

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ACCESS (from your Mac)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  ssh -fNL 8050:localhost:8050 root@157.230.91.33 && open http://localhost:8050

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
DATA SOURCES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  logs/paper_portfolio_mlb.json        T1 positions
  logs/paper_portfolio_mlb_t4.json     T4 positions
  logs/audit_mlb.jsonl                 T1 audit (all events incl. bets)
  logs/audit_mlb_t4.jsonl             T4 audit (all events incl. bets)
  logs/paper_mlb_cron.log             PIPE-05 log tail

  NFL (T-534/GG-263, added on top of MLB — additive only, MLB paths above
  are unchanged):
  logs/paper_portfolio_t1_nfl_game_market.json   T1 NFL game-market positions (PAPER, SHADOW)
  logs/audit_t1_nfl_game_market.jsonl            T1 NFL game-market audit log
  NFL is a separate, manually-invoked, pool-isolated shadow run — NOT on
  cron, NOT live capital. See the NFL panel's own header for model
  provenance (EXP-027 LR vs stub) on every render.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections import deque
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Any

_src = Path(__file__).parent.parent / "src"
if str(_src) not in sys.path:
    sys.path.insert(0, str(_src))
try:
    from prediction_market_bot.logic_epoch import CURRENT_LOGIC_EPOCH  # T-321
except Exception:
    CURRENT_LOGIC_EPOCH = None

# NFL model provenance label (T-534/GG-263) — read as a class attribute only,
# never instantiated here: instantiating EXP027NFLForecastModel re-fits the
# LR in-memory (expensive) and requires the import-order dance documented in
# nfl_exp027_adapter.py's own docstring. The dashboard only needs the label
# string, so it reads PROVENANCE off the class itself.
try:
    from prediction_market_bot.nfl_exp027_adapter import EXP027NFLForecastModel
    _NFL_MODEL_PROVENANCE = EXP027NFLForecastModel.PROVENANCE
except Exception:
    _NFL_MODEL_PROVENANCE = "UNAVAILABLE (adapter import failed — see dashboard logs)"

# ─────────────────────────────────────────────────────────────────────────────
# Configuration
# ─────────────────────────────────────────────────────────────────────────────
DEFAULT_PORT = 8050
DEFAULT_HOST = "127.0.0.1"   # Localhost only — SSH tunnel access

_log_dir: Path = Path("logs/")


# ─────────────────────────────────────────────────────────────────────────────
# Data loading
# ─────────────────────────────────────────────────────────────────────────────

def _load_json(p: Path) -> dict:
    try:
        with open(p) as f:
            return json.load(f)
    except Exception:
        return {}


def _load_jsonl(p: Path, tail: int = 500) -> list[dict]:
    if not p.exists():
        return []
    # Keep only the last `tail` raw lines in memory (bounded deque), then
    # parse just those. Audit logs grow unbounded (tens of MB after a few
    # days of live MLB activity) — parsing every line into a dict before
    # slicing to the tail held the entire file's worth of Python objects
    # in memory at once, which is what was blowing past the service's
    # 128M MemoryMax and OOM-killing the dashboard in a restart loop.
    buf: deque[str] = deque(maxlen=tail)
    try:
        with open(p) as f:
            for line in f:
                line = line.strip()
                if line:
                    buf.append(line)
    except Exception:
        pass
    entries: list[dict] = []
    for line in buf:
        try:
            entries.append(json.loads(line))
        except json.JSONDecodeError:
            pass
    return entries


def _load_tail(p: Path, n: int = 40) -> list[str]:
    if not p.exists():
        return []
    try:
        with open(p) as f:
            lines = f.readlines()
        return [ln.rstrip() for ln in lines[-n:]]
    except Exception:
        return []


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
                dt = datetime.fromtimestamp(mtime, tz=timezone.utc)
                result[label] = dt.strftime("%Y-%m-%dT%H:%M:%SZ")
            except Exception:
                result[label] = "error"
        else:
            result[label] = "no log yet"
    return result


def _load_all_data() -> dict:
    d = _log_dir
    return {
        "portfolio":    _load_json(d / "paper_portfolio_mlb.json"),
        "t4_portfolio": _load_json(d / "paper_portfolio_mlb_t4.json"),
        # Pull more audit history so the trade log is comprehensive
        "audit":        _load_jsonl(d / "audit_mlb.jsonl",    tail=1000),
        "t4_audit":     _load_jsonl(d / "audit_mlb_t4.jsonl", tail=500),
        "pipe_log":     _load_tail(d / "paper_mlb_cron.log",  n=50),
        "pipe_mtimes":  _pipe_mtimes(d),
        "server_time":  datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "current_logic_epoch": CURRENT_LOGIC_EPOCH,  # T-321
        # NFL (T-534/GG-263) — additive only, above MLB keys unchanged.
        "nfl_portfolio": _load_json(d / "paper_portfolio_t1_nfl_game_market.json"),
        "nfl_audit":     _load_jsonl(d / "audit_t1_nfl_game_market.jsonl", tail=1000),
        "nfl_model_provenance": _NFL_MODEL_PROVENANCE,
    }


# ─────────────────────────────────────────────────────────────────────────────
# HTTP Handler
# ─────────────────────────────────────────────────────────────────────────────

class DashboardHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        path = self.path.split("?")[0]
        if path in ("/", "/index.html"):
            self._serve_html()
        elif path == "/api/data":
            self._serve_data()
        else:
            self.send_error(404, "Not found")

    def _serve_html(self) -> None:
        body = _HTML.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store, no-cache")
        self.end_headers()
        self.wfile.write(body)

    def _serve_data(self) -> None:
        try:
            data = _load_all_data()
            body = json.dumps(data, default=str).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store, no-cache")
            self.end_headers()
            self.wfile.write(body)
        except Exception as exc:
            body = json.dumps({"error": str(exc)}).encode("utf-8")
            self.send_response(500)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    def log_message(self, fmt: str, *args: Any) -> None:
        pass


# ─────────────────────────────────────────────────────────────────────────────
# HTML / CSS / JS  (self-contained, zero CDN)
# ─────────────────────────────────────────────────────────────────────────────

_HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>PMBot — MLB Live</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
:root{
  --bg:#080c10;--bg1:#0d1117;--bg2:#111827;
  --border:#21262d;--border2:#1c2333;
  --text:#c9d1d9;--dim:#6b7280;--dim2:#374151;
  --g:#4ade80;--r:#f87171;--y:#facc15;--c:#22d3ee;--m:#c084fc;
  --gbg:#052e16;--rbg:#450a0a;--ybg:#422006;
  --t1:#22d3ee;--t4:#c084fc;
}
html{scrollbar-color:var(--border) var(--bg);scrollbar-width:thin}
body{
  background:var(--bg);color:var(--text);
  font-family:'SF Mono','Menlo','Cascadia Code','Consolas',monospace;
  font-size:12.5px;padding:14px;line-height:1.45;min-width:960px;
}
.hdr{display:flex;justify-content:space-between;align-items:flex-start;
  border-bottom:1px solid var(--border);padding-bottom:10px;margin-bottom:12px}
.hdr-title{color:var(--c);font-size:16px;font-weight:700;letter-spacing:.07em;margin-bottom:2px}
.hdr-sub{color:var(--dim);font-size:11px;letter-spacing:.04em}
.hdr-right{text-align:right;color:var(--dim);font-size:11px;line-height:1.9}
.hdr-right button{
  margin-left:8px;background:var(--bg2);border:1px solid var(--border);
  color:var(--c);border-radius:3px;padding:2px 10px;font-size:11px;
  cursor:pointer;font-family:inherit;letter-spacing:.04em}
.hdr-right button:hover{background:var(--border2);color:#fff}
/* portfolio bar */
.pbar{
  background:var(--bg1);border:1px solid var(--border);border-radius:4px;
  padding:10px 16px;margin-bottom:12px;display:flex;gap:20px;flex-wrap:wrap;align-items:center}
.metric{display:flex;flex-direction:column;gap:2px}
.metric-lbl{color:var(--dim);font-size:10px;text-transform:uppercase;letter-spacing:.07em}
.metric-val{font-size:14px;font-weight:700}
.pbar-sep{width:1px;background:var(--border2);align-self:stretch;margin:0 4px}
/* band totals */
.band-row{display:flex;gap:16px;font-size:11px;color:var(--dim);
  padding:5px 16px;background:var(--bg2);border-bottom:1px solid var(--border);
  border-radius:0 0 4px 4px;margin-top:-12px;margin-bottom:12px}
.b1{color:var(--t1)}.b4{color:var(--t4)}
/* grid */
.grid{display:grid;gap:10px;margin-bottom:10px}
.grid-2{grid-template-columns:1fr 1fr}
/* panels */
.panel{background:var(--bg1);border:1px solid var(--border);border-radius:4px;overflow:hidden}
.panel-hdr{
  background:var(--bg2);color:var(--dim);font-size:10.5px;font-weight:700;
  letter-spacing:.09em;text-transform:uppercase;
  padding:5px 10px;border-bottom:1px solid var(--border);
  display:flex;justify-content:space-between;align-items:center}
.panel-hdr-badge{font-size:10px;font-weight:400;color:var(--dim2)}
.panel-body{padding:8px 10px;max-height:280px;overflow-y:auto;overflow-x:auto}
.panel-body.tall{max-height:420px}
.panel-body::-webkit-scrollbar{width:4px;height:4px}
.panel-body::-webkit-scrollbar-track{background:var(--bg1)}
.panel-body::-webkit-scrollbar-thumb{background:var(--border)}
/* tables */
table{width:100%;border-collapse:collapse;white-space:nowrap}
th{
  color:var(--dim);font-size:10.5px;text-transform:uppercase;letter-spacing:.05em;
  padding:3px 8px;text-align:left;border-bottom:1px solid var(--border2);
  position:sticky;top:0;background:var(--bg1);z-index:1}
td{padding:3px 8px;border-bottom:1px solid #0a0e14;font-size:12px}
tr:hover td{background:#161b22}
.tr{text-align:right}
/* colors */
.g{color:var(--g)}.r{color:var(--r)}.y{color:var(--y)}
.c{color:var(--c)}.m{color:var(--m)}.dim{color:var(--dim)}.b{font-weight:700}
/* band chips */
.chip{display:inline-block;padding:1px 5px;border-radius:3px;font-size:10px;font-weight:700;letter-spacing:.04em}
.chip-t1{background:#0e3a4a;color:var(--t1)}
.chip-t4{background:#2d1a4a;color:var(--t4)}
/* outcome badges */
.badge{display:inline-block;padding:1px 6px;border-radius:3px;font-size:11px;font-weight:700}
.bg{background:var(--gbg);color:var(--g)}
.br{background:var(--rbg);color:var(--r)}
.by{background:var(--ybg);color:var(--y)}
.bd{background:var(--border2);color:var(--dim)}
/* kill switch */
.ks-ok{color:var(--g);font-weight:700}
.ks-fired{
  display:inline-block;background:var(--rbg);color:var(--r);
  font-weight:700;padding:2px 12px;border-radius:3px;
  border:1px solid #7f1d1d;animation:blink 1s step-end infinite}
@keyframes blink{50%{opacity:.35}}
/* log lines */
.ll{font-size:11px;padding:1.5px 0;border-bottom:1px solid var(--bg);word-break:break-all}
.lo{color:var(--g)}.lw{color:var(--y)}.le{color:var(--r);font-weight:700}
.li{color:var(--c)}.ld{color:var(--dim)}
/* system */
.sys-tbl td{border-bottom:1px solid #0a0e14;padding:3px 10px}
.sys-tbl td:first-child{color:var(--dim);white-space:nowrap;width:175px}
/* misc */
.empty{color:var(--dim2);padding:14px 4px;font-style:italic;font-size:12px}
.err-banner{
  background:var(--rbg);color:var(--r);border:1px solid #7f1d1d;
  border-radius:4px;padding:8px 14px;margin-bottom:10px;font-size:12px}
.footer{
  border-top:1px solid #0d1117;margin-top:12px;padding-top:8px;
  display:flex;justify-content:space-between;color:var(--dim2);font-size:11px}
.dot{display:inline-block;width:7px;height:7px;border-radius:50%;
  background:var(--dim2);margin-right:6px;vertical-align:middle;transition:background .3s}
.dot.live{background:var(--g);box-shadow:0 0 6px var(--g)}
.dot.err{background:var(--r)}
</style>
</head>
<body>

<div class="hdr">
  <div>
    <div class="hdr-title">◉ PREDICTION MARKET BOT — MLB LIVE</div>
    <div class="hdr-sub">PAPER TRADING &nbsp;·&nbsp; VPS 157.230.91.33 &nbsp;·&nbsp; G6 OPEN</div>
  </div>
  <div class="hdr-right">
    <div id="server-time" class="dim">—</div>
    <div><span class="dim" id="next-refresh">—</span>
    <button onclick="forceRefresh()">↻ Refresh</button></div>
  </div>
</div>

<div id="err-banner" class="err-banner" style="display:none"></div>

<!-- Portfolio summary bar (combined T1+T4) -->
<div class="pbar">
  <div class="metric"><div class="metric-lbl">Bankroll (T1)</div><div class="metric-val c" id="m-bankroll">—</div></div>
  <div class="metric"><div class="metric-lbl">Cum P&amp;L</div><div class="metric-val" id="m-pnl">—</div></div>
  <div class="metric"><div class="metric-lbl">Drawdown</div><div class="metric-val" id="m-dd">—</div></div>
  <div class="metric"><div class="metric-lbl">Daily P&amp;L</div><div class="metric-val" id="m-daily">—</div></div>
  <div class="pbar-sep"></div>
  <div class="metric"><div class="metric-lbl">Open (all)</div><div class="metric-val b" id="m-open">—</div></div>
  <div class="metric"><div class="metric-lbl">W / L</div><div class="metric-val" id="m-wl">—</div></div>
  <div class="metric"><div class="metric-lbl">Win Rate</div><div class="metric-val" id="m-wr">—</div></div>
  <div class="metric"><div class="metric-lbl">Resolved</div><div class="metric-val" id="m-resolved">—</div></div>
  <div class="pbar-sep"></div>
  <div class="metric"><div class="metric-lbl"><span class="b1">T1</span> P&amp;L</div><div class="metric-val" id="m-t1pnl">—</div></div>
  <div class="metric"><div class="metric-lbl"><span class="b4">T4</span> P&amp;L</div><div class="metric-val" id="m-t4pnl">—</div></div>
</div>

<!-- Clean-logic provenance (T-320/T-321): raw_n vs clean_n per band -->
<div class="band-row" id="clean-n-row" style="display:flex">
  <span>CLEAN-LOGIC (epoch <span id="cn-epoch">—</span>):</span>
  <span><span class="b1">T1</span> raw=<span id="cn-t1-raw">—</span> clean=<span id="cn-t1-clean">—</span></span>
  <span>T2 raw=<span id="cn-t2-raw">—</span> clean=<span id="cn-t2-clean">—</span></span>
  <span><span class="b4">T4M-PROJ</span> raw=<span id="cn-t4m-raw">—</span> clean=<span id="cn-t4m-clean">—</span></span>
</div>

<!-- Row 1: Live Positions + Today's Bets -->
<div class="grid grid-2">
  <div class="panel">
    <div class="panel-hdr">Live Positions <span class="panel-hdr-badge" id="hdr-live">T1 + T4</span></div>
    <div class="panel-body" id="c-live"><div class="empty">Loading…</div></div>
  </div>
  <div class="panel">
    <div class="panel-hdr">Today's Bets <span class="panel-hdr-badge" id="hdr-today"></span></div>
    <div class="panel-body" id="c-today"><div class="empty">Loading…</div></div>
  </div>
</div>

<!-- Trade Log — all bands, reverse-chron, paginated -->
<div class="panel" style="margin-bottom:10px">
  <div class="panel-hdr">
    Trade Log — All Bands
    <span class="panel-hdr-badge" id="hdr-trades"></span>
  </div>
  <div class="panel-body tall" id="c-trades"><div class="empty">Loading…</div></div>
</div>

<!-- Row 2: Recently Resolved + Alerts -->
<div class="grid grid-2">
  <div class="panel">
    <div class="panel-hdr">Recently Resolved <span class="panel-hdr-badge" id="hdr-resolved"></span></div>
    <div class="panel-body" id="c-resolved"><div class="empty">Loading…</div></div>
  </div>
  <div class="panel">
    <div class="panel-hdr">Alerts</div>
    <div class="panel-body" id="c-alerts"><div class="empty">Loading…</div></div>
  </div>
</div>

<!-- System status -->
<div class="panel" style="margin-bottom:10px">
  <div class="panel-hdr">System Status &nbsp;·&nbsp; Pipeline Health</div>
  <div class="panel-body" style="max-height:140px" id="c-system"><div class="empty">Loading…</div></div>
</div>

<!-- PIPE-05 log tail -->
<div class="panel">
  <div class="panel-hdr">PIPE-05 Log Tail</div>
  <div class="panel-body" style="max-height:220px" id="c-pipe-log"><div class="empty">Loading…</div></div>
</div>

<!-- NFL (T-534/GG-263) — SHADOW / PAPER ONLY, manually-invoked, additive only.
     Not on cron, not live capital, separate pool from MLB above. -->
<div class="panel" style="margin-bottom:10px">
  <div class="panel-hdr">
    NFL Game Markets &nbsp;·&nbsp; <span style="color:#e55;font-weight:700">SHADOW — PAPER ONLY</span>
    <span class="panel-hdr-badge" id="hdr-nfl-provenance"></span>
  </div>
  <div class="panel-body" id="c-nfl"><div class="empty">Loading…</div></div>
</div>

<div class="footer">
  <div><span class="dot" id="dot"></span><span id="status-text">Connecting…</span></div>
  <div id="countdown"></div>
</div>

<script>
// ═══════════════════════════════════════════════════════
// Utilities
// ═══════════════════════════════════════════════════════
const esc = s => String(s??'')
  .replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
const f2  = n => (parseFloat(n)||0).toFixed(2);
const f4  = n => (parseFloat(n)||0).toFixed(4);

function pnl(v){
  v=parseFloat(v)||0;
  if(v>0.005) return`<span class="g b">+$${f2(v)}</span>`;
  if(v<-0.005)return`<span class="r b">-$${f2(Math.abs(v))}</span>`;
  return'<span class="dim">$0.00</span>';
}
function dd(pct){
  pct=parseFloat(pct)||0;const s=pct.toFixed(2)+'%';
  if(pct>=20)return`<span class="r b">${s} ⚠</span>`;
  if(pct>=15)return`<span class="r">${s}</span>`;
  if(pct>=5) return`<span class="y">${s}</span>`;
  return`<span class="g">${s}</span>`;
}
function dir(d){
  if(d==='YES')return'<span class="badge bg">YES</span>';
  if(d==='NO') return'<span class="badge br">NO</span>';
  return'<span class="dim">—</span>';
}
function outcome(o){
  if(o==='WIN') return'<span class="g b">WIN</span>';
  if(o==='LOSS')return'<span class="r b">LOSS</span>';
  if(o==='PUSH')return'<span class="y">PUSH</span>';
  return`<span class="dim">${esc(o||'?')}</span>`;
}
function band(b){
  if(b==='T4')return'<span class="chip chip-t4">T4</span>';
  return'<span class="chip chip-t1">T1</span>';
}
function thresh(t){
  try{return'H≥'+parseInt(t);}catch{return String(t??'?');}
}
function edgeFmt(v){
  v=parseFloat(v);if(isNaN(v))return'<span class="dim">N/A</span>';
  const s=(v>=0?'+':'')+v.toFixed(4);
  if(v>=0.04)return`<span class="g">${s}</span>`;
  if(v>0)    return`<span class="y">${s}</span>`;
  return`<span class="dim">${s}</span>`;
}
function ts(s){if(!s)return'—';return esc(String(s).replace('T',' ').slice(0,16));}
function since(iso){
  try{
    const sec=Math.floor((Date.now()-new Date(iso).getTime())/1000);
    if(sec<60)return sec+'s';if(sec<3600)return Math.floor(sec/60)+'m';
    if(sec<86400)return Math.floor(sec/3600)+'h'+Math.floor((sec%3600)/60)+'m';
    return Math.floor(sec/86400)+'d';
  }catch{return'';}
}
function toArr(v){if(!v)return[];if(Array.isArray(v))return v;return Object.values(v);}
function posPnl(p){return(parseFloat(p.pnl)||0)+(parseFloat(p.exit_pnl)||0);}

// ═══════════════════════════════════════════════════════
// Merge T1 + T4 positions, tag each with band
// ═══════════════════════════════════════════════════════
function mergePositions(data){
  const tag=(arr,b)=>toArr(arr).map(p=>({...p,_band:b}));
  const p1=data.portfolio||{};
  const p4=data.t4_portfolio||{};
  return{
    open:[
      ...tag(p1.open_positions,'T1'),
      ...tag(p4.open_positions,'T4'),
    ],
    closed:[
      ...tag(p1.closed_positions,'T1'),
      ...tag(p4.closed_positions,'T4'),
    ],
  };
}

// ═══════════════════════════════════════════════════════
// Build trade log from audit files (all bands)
// Looks for any audit event that represents a placed bet
// ═══════════════════════════════════════════════════════
const BET_EVENTS = new Set([
  'paper_bet_placed','bet_placed','paper_trade','trade',
  'position_opened','bet_submitted','order_placed',
  // catch-all: any event whose payload has player_name + direction + size_usd
]);

function buildTradeLog(data){
  const trades=[];
  function ingest(entries, defaultBand){
    for(const e of entries){
      const et=(e.event_type||'').toLowerCase();
      const pl=e.payload||{};
      const isBet=BET_EVENTS.has(et)
        ||(pl.player_name&&pl.direction&&(pl.size_usd||pl.stake_usd));
      if(!isBet)continue;
      trades.push({
        ts:       e.timestamp||'',
        band:     pl.band||pl.execution_band||defaultBand,
        player:   pl.player_name||pl.player||'?',
        thresh:   pl.kalshi_threshold??pl.threshold??'?',
        dir:      pl.direction||'?',
        size:     parseFloat(pl.size_usd||pl.stake_usd||0),
        model_p:  parseFloat(pl.model_p||0),
        mip:      parseFloat(pl.mid_price_at_entry||pl.mip||pl.market_price||0),
        edge:     parseFloat(pl.gross_edge||pl.edge||0),
        status:   pl.status||e.event_type||'placed',
        outcome:  pl.outcome||'',
        pnl_val:  parseFloat(pl.pnl||pl.exit_pnl||0),
        game_date:pl.game_date||'',
      });
    }
  }
  ingest(data.audit||[],    'T1');
  ingest(data.t4_audit||[], 'T4');
  // Sort newest first
  trades.sort((a,b)=>b.ts.localeCompare(a.ts));
  return trades;
}

// ═══════════════════════════════════════════════════════
// Renderers
// ═══════════════════════════════════════════════════════

function renderPortfolio(data){
  const merged=mergePositions(data);
  const p1=data.portfolio||{};
  const p4=data.t4_portfolio||{};

  const bankroll=parseFloat(p1.bankroll_usd)||0;
  const initial =parseFloat(p1.initial_bankroll_usd)||1000;

  const t1Closed=toArr(p1.closed_positions);
  const t4Closed=toArr(p4.closed_positions);
  const allClosed=[...t1Closed,...t4Closed];

  const t1Pnl=t1Closed.reduce((s,p)=>s+posPnl(p),0);
  const t4Pnl=t4Closed.reduce((s,p)=>s+posPnl(p),0);
  const totalPnl=t1Pnl+t4Pnl;

  const ddPct=initial>0?Math.max(0,-totalPnl/initial*100):0;
  const wins=allClosed.filter(p=>p.outcome==='WIN').length;
  const losses=allClosed.filter(p=>p.outcome==='LOSS').length;
  const total=wins+losses;
  const wr=total?(wins/total*100).toFixed(1)+'%':'N/A';
  const daily=parseFloat(p1.daily_net_pnl)||0;
  const cur=n=>n.toLocaleString('en',{minimumFractionDigits:2,maximumFractionDigits:2});

  document.getElementById('m-bankroll').textContent=`$${cur(bankroll)}`;
  document.getElementById('m-pnl').innerHTML=pnl(totalPnl);
  document.getElementById('m-dd').innerHTML=dd(ddPct);
  document.getElementById('m-daily').innerHTML=daily<0
    ?`<span class="r">-$${f2(Math.abs(daily))}</span>`
    :`<span class="g">+$${f2(daily)}</span>`;
  document.getElementById('m-open').innerHTML=
    `<span class="b1">${merged.open.filter(p=>p._band==='T1').length}</span>`+
    `+<span class="b4">${merged.open.filter(p=>p._band==='T4').length}</span>`;
  document.getElementById('m-wl').innerHTML=
    `<span class="g b">${wins}</span>/<span class="r">${losses}</span>`;
  document.getElementById('m-wr').textContent=wr;
  document.getElementById('m-resolved').textContent=total;
  document.getElementById('m-t1pnl').innerHTML=pnl(t1Pnl);
  document.getElementById('m-t4pnl').innerHTML=pnl(t4Pnl);

  // T-320/T-321: clean-logic provenance — raw_n vs clean_n per band
  const curEpoch=data.current_logic_epoch;
  document.getElementById('cn-epoch').textContent=curEpoch??'?';
  const cleanCount=(rows,band)=>{
    const bandRows=rows.filter(p=>p.band===band);
    return [bandRows.length, bandRows.filter(p=>p.logic_epoch===curEpoch).length];
  };
  const [t1Raw,t1Clean]=cleanCount(t1Closed,'T1');
  const [t2Raw,t2Clean]=cleanCount(t1Closed,'T2');
  const [t4mRaw,t4mClean]=cleanCount(t4Closed,'T4M-PROJ');
  document.getElementById('cn-t1-raw').textContent=t1Raw;
  document.getElementById('cn-t1-clean').textContent=t1Clean;
  document.getElementById('cn-t2-raw').textContent=t2Raw;
  document.getElementById('cn-t2-clean').textContent=t2Clean;
  document.getElementById('cn-t4m-raw').textContent=t4mRaw;
  document.getElementById('cn-t4m-clean').textContent=t4mClean;
}

function renderLivePositions(data){
  const el=document.getElementById('c-live');
  const merged=mergePositions(data);
  const open=merged.open;
  if(!open.length){el.innerHTML='<div class="empty">No open positions</div>';return;}
  document.getElementById('hdr-live').textContent=`${open.length} open`;
  let rows='';
  for(const p of open){
    rows+=`<tr>
      <td>${band(p._band)}</td>
      <td>${esc(p.player_name||'?')}</td>
      <td class="dim">${esc(thresh(p.kalshi_threshold))}</td>
      <td>${dir(p.direction)}</td>
      <td class="c tr">$${f2(p.size_usd||0)}</td>
      <td class="dim tr">${f4(p.model_p||0)}</td>
      <td class="dim tr">${f4(p.mid_price_at_entry||0)}</td>
      <td class="tr">${edgeFmt(p.gross_edge)}</td>
      <td class="dim">${ts(p.entered_at)}</td>
    </tr>`;
  }
  el.innerHTML=`<table><thead><tr>
    <th>Band</th><th>Player</th><th>Thresh</th><th>Dir</th>
    <th class="tr">Size</th><th class="tr">Model P</th>
    <th class="tr">MIP</th><th class="tr">Edge</th><th>Entered</th>
  </tr></thead><tbody>${rows}</tbody></table>`;
}

function renderTodayBets(data){
  const el=document.getElementById('c-today');
  const today=new Date().toISOString().slice(0,10);
  const merged=mergePositions(data);
  const all=[...merged.open,...merged.closed];
  const todayPos=all.filter(p=>p.game_date===today);

  if(!todayPos.length){
    el.innerHTML=`<div class="empty">${esc(today)} — no bets yet</div>`;return;
  }
  const t1n=todayPos.filter(p=>p._band==='T1').length;
  const t4n=todayPos.filter(p=>p._band==='T4').length;
  const staked=todayPos.reduce((s,p)=>s+(parseFloat(p.size_usd)||0),0);
  document.getElementById('hdr-today').innerHTML=
    `<span class="b1">T1:${t1n}</span> <span class="b4">T4:${t4n}</span> &nbsp;·&nbsp; $${f2(staked)} staked`;

  // Group by band+threshold
  const byKey={};
  for(const p of todayPos){
    const k=`${p._band}:${p.kalshi_threshold??'?'}`;
    if(!byKey[k])byKey[k]=[];
    byKey[k].push(p);
  }
  let rows='';
  for(const[k,grp] of Object.entries(byKey).sort()){
    const[b,t]=k.split(':');
    const stk=grp.reduce((s,p)=>s+(parseFloat(p.size_usd)||0),0);
    const nOpen=grp.filter(p=>p.status==='OPEN').length;
    const nClosed=grp.filter(p=>p.status==='CLOSED').length;
    const nWins=grp.filter(p=>p.outcome==='WIN').length;
    const grpPnl=grp.filter(p=>p.status==='CLOSED').reduce((s,p)=>s+posPnl(p),0);
    rows+=`<tr>
      <td>${band(b)}</td>
      <td class="dim">${esc(thresh(t))}</td>
      <td class="b tr">${grp.length}</td>
      <td class="c tr">$${f2(stk)}</td>
      <td class="dim tr">${nOpen}</td>
      <td class="dim tr">${nClosed}</td>
      <td class="g tr">${nWins}</td>
      <td>${nClosed?pnl(grpPnl):'<span class="dim">pending</span>'}</td>
    </tr>`;
  }
  el.innerHTML=`<table><thead><tr>
    <th>Band</th><th>Thresh</th><th class="tr">N</th><th class="tr">Staked</th>
    <th class="tr">Open</th><th class="tr">Closed</th><th class="tr">W</th><th>P&amp;L</th>
  </tr></thead><tbody>${rows}</tbody></table>`;
}

function renderTradeLog(data){
  const el=document.getElementById('c-trades');
  const trades=buildTradeLog(data);
  document.getElementById('hdr-trades').textContent=
    trades.length+' total';

  if(!trades.length){
    el.innerHTML='<div class="empty">No bet events found in audit logs yet</div>';return;
  }

  let rows='';
  for(const t of trades.slice(0,200)){
    const pnlCell=t.outcome
      ?pnl(t.pnl_val)
      :'<span class="dim">—</span>';
    const outcomeCell=t.outcome?outcome(t.outcome):'<span class="dim">open</span>';
    rows+=`<tr>
      <td class="dim">${ts(t.ts)}</td>
      <td>${band(t.band)}</td>
      <td>${esc(t.player)}</td>
      <td class="dim">${esc(thresh(t.thresh))}</td>
      <td>${dir(t.dir)}</td>
      <td class="c tr">$${f2(t.size)}</td>
      <td class="dim tr">${t.model_p?f4(t.model_p):'—'}</td>
      <td class="dim tr">${t.mip?f4(t.mip):'—'}</td>
      <td class="tr">${t.edge?edgeFmt(t.edge):'—'}</td>
      <td>${outcomeCell}</td>
      <td>${pnlCell}</td>
    </tr>`;
  }
  el.innerHTML=`<table><thead><tr>
    <th>Time</th><th>Band</th><th>Player</th><th>Thresh</th><th>Dir</th>
    <th class="tr">Size</th><th class="tr">Model P</th><th class="tr">MIP</th>
    <th class="tr">Edge</th><th>Result</th><th>P&amp;L</th>
  </tr></thead><tbody>${rows}</tbody></table>`;
}

function renderResolved(data){
  const el=document.getElementById('c-resolved');
  const merged=mergePositions(data);
  const closed=merged.closed;
  if(!closed.length){
    el.innerHTML='<div class="empty">None resolved yet — PIPE-05R runs at 06:30Z</div>';return;
  }
  const wins=closed.filter(p=>p.outcome==='WIN').length;
  const losses=closed.filter(p=>p.outcome==='LOSS').length;
  const totalPnl=closed.reduce((s,p)=>s+posPnl(p),0);
  document.getElementById('hdr-resolved').innerHTML=
    `<span class="g">${wins}W</span>/<span class="r">${losses}L</span> &nbsp;${pnl(totalPnl)}`;

  let rows='';
  for(const p of [...closed].sort((a,b)=>
      (b.resolved_at||b.entered_at||'').localeCompare(a.resolved_at||a.entered_at||'')).slice(0,80)){
    const actual=p.actual_stat!=null?String(p.actual_stat):'?';
    rows+=`<tr>
      <td>${band(p._band)}</td>
      <td>${esc(p.player_name||'?')}</td>
      <td class="dim">${esc(thresh(p.kalshi_threshold))}</td>
      <td>${dir(p.direction)}</td>
      <td class="dim tr">${esc(actual)}</td>
      <td>${outcome(p.outcome)}</td>
      <td>${pnl(posPnl(p))}</td>
      <td class="dim">${ts(p.resolved_at)}</td>
    </tr>`;
  }
  el.innerHTML=`<table><thead><tr>
    <th>Band</th><th>Player</th><th>Thresh</th><th>Dir</th>
    <th class="tr">Actual</th><th>Result</th><th>P&amp;L</th><th>Resolved</th>
  </tr></thead><tbody>${rows}</tbody></table>`;
}

function renderAlerts(audit, t4_audit){
  const el=document.getElementById('c-alerts');
  const SEV=new Set(['WARNING','WARN','ERROR','CRITICAL']);
  const all=[
    ...(audit||[]).map(e=>({...e,_band:'T1'})),
    ...(t4_audit||[]).map(e=>({...e,_band:'T4'})),
  ].filter(e=>SEV.has(e.severity));
  if(!all.length){el.innerHTML='<div class="empty">No alerts — system clean</div>';return;}
  all.sort((a,b)=>(b.timestamp||'').localeCompare(a.timestamp||''));
  let rows='';
  for(const e of all.slice(0,30)){
    const sev=e.severity||'?';
    const pl=(e.payload&&typeof e.payload==='object')?e.payload:{};
    const detail=String(pl.reason||pl.trigger||pl.error||'').slice(0,40);
    let sevHtml=sev==='CRITICAL'
      ?`<span class="badge br">${esc(sev)}</span>`
      :sev==='ERROR'?`<span class="r">${esc(sev)}</span>`
      :`<span class="y">${esc(sev)}</span>`;
    rows+=`<tr>
      <td class="dim">${ts(e.timestamp)}</td>
      <td>${band(e._band)}</td>
      <td>${sevHtml}</td>
      <td class="dim">${esc(e.component||'?')}</td>
      <td class="dim">${esc((e.event_type||'?').slice(0,24))}</td>
      <td class="dim">${esc(detail)}</td>
    </tr>`;
  }
  el.innerHTML=`<table><thead><tr>
    <th>Time</th><th>Band</th><th>Sev</th><th>Comp</th><th>Event</th><th>Detail</th>
  </tr></thead><tbody>${rows}</tbody></table>`;
}

function renderSystem(data){
  const el=document.getElementById('c-system');
  const audit=data.audit||[];
  const mtimes=data.pipe_mtimes||{};
  let ksActive=false,ksReason='';
  for(const e of [...audit].reverse()){
    if(e.event_type==='kill_switch_triggered'){
      ksActive=true;ksReason=(e.payload||{}).reason||'';break;
    }
    if(e.event_type==='kill_switch_reset')break;
  }
  const ksHtml=ksActive
    ?`<span class="ks-fired">⚠ KILL SWITCH ACTIVE${ksReason?' — '+esc(ksReason):''} ⚠</span>`
    :`<span class="ks-ok">ARMED ✓</span>`;
  let pipeRows='';
  for(const[label,tsVal]of Object.entries(mtimes)){
    const isNoLog=(tsVal==='no log yet'||tsVal==='error');
    const ago=isNoLog?'':since(tsVal);
    const tsDisp=isNoLog
      ?`<span class="dim">${esc(tsVal)}</span>`
      :`<span class="dim">${esc(tsVal.slice(0,16))}</span>`
        +(ago?` <span class="dim" style="font-size:10px">[${esc(ago)} ago]</span>`:'');
    pipeRows+=`<tr><td>${esc(label)}</td><td>${tsDisp}</td></tr>`;
  }
  el.innerHTML=`<div style="margin-bottom:8px;font-size:12.5px">Kill Switch: ${ksHtml}</div>
    <table class="sys-tbl"><tbody>${pipeRows}</tbody></table>`;
}

function renderPipeLog(lines){
  const el=document.getElementById('c-pipe-log');
  if(!lines||!lines.length){
    el.innerHTML='<div class="empty">No logs yet</div>';return;
  }
  const html=lines.map(line=>{
    let cls='ld';
    if(/SUMMARY|BET PLACED|bets placed|PLACED/i.test(line))cls='lo';
    else if(/WARN|SKIP|warning/i.test(line))cls='lw';
    else if(/ERROR|error|FATAL|fatal/i.test(line))cls='le';
    else if(/PIPE-05|SemanticFloor/i.test(line))cls='li';
    return`<div class="ll ${cls}">${esc(line)}</div>`;
  }).join('');
  el.innerHTML=html;
  el.scrollTop=el.scrollHeight;
}

// ═══════════════════════════════════════════════════════
// NFL (T-534/GG-263) — SHADOW / PAPER ONLY, separate pool from MLB.
// Reuses the MLB position-rendering helpers above (dir/f2/f4/ts/outcome/
// toArr) since NFL positions are written by the same PaperTrader class and
// share its exact field schema.
//
// Provenance caveat: PaperTrader's stored position schema and this run's
// audit events do not record a per-row model identity (stub vs EXP-027 LR)
// — see GG-264 (registered T-534). The badge below is therefore a
// section-wide label sourced live from the run's model class, not a
// per-row-verified attribution. It is accurate for this run (one model is
// injected for the whole invocation) but would not distinguish rows if a
// future run ever mixed models mid-run.
// ═══════════════════════════════════════════════════════
function renderNFL(data){
  const el=document.getElementById('c-nfl');
  const badgeEl=document.getElementById('hdr-nfl-provenance');
  const provenance=data.nfl_model_provenance||'UNKNOWN';
  badgeEl.textContent='model: '+provenance;

  const portfolio=data.nfl_portfolio||{};
  const open=toArr(portfolio.open_positions);
  const closed=toArr(portfolio.closed_positions);
  const audit=data.nfl_audit||[];

  let tally={};
  for(const e of audit){
    const et=e.event_type||'unknown';
    tally[et]=(tally[et]||0)+1;
  }
  const tallyRows=Object.entries(tally)
    .sort((a,b)=>b[1]-a[1])
    .map(([et,n])=>`<tr><td>${esc(et)}</td><td style="text-align:right">${n}</td></tr>`)
    .join('');
  const tallyHtml=audit.length
    ?`<div style="margin-top:10px">
        <div class="dim" style="font-size:11px;margin-bottom:4px">Audit event tally (last ${audit.length} events, ${SESSION_LABEL_NFL}):</div>
        <table class="sys-tbl"><tbody>${tallyRows}</tbody></table>
      </div>`
    :'';

  if(!open.length && !closed.length){
    el.innerHTML=`<div class="empty">No NFL positions yet (this run opened zero paper positions — see audit tally below for why).</div>${tallyHtml}`;
    return;
  }

  const rows=(arr,isOpen)=>arr.map(p=>`<tr>
    <td>${esc(p.kalshi_ticker||'—')}</td>
    <td>${dir(p.direction)}</td>
    <td>$${f2(p.size_usd)}</td>
    <td>${f4(p.model_p)}</td>
    <td>${isOpen?'<span class="y">OPEN</span>':outcome(p.status)}</td>
    <td>${ts(p.entered_at)}</td>
    <td><span class="badge" style="background:#553;color:#fd5">PAPER</span></td>
  </tr>`).join('');

  el.innerHTML=`
    <table class="sys-tbl">
      <thead><tr><th>Ticker</th><th>Side</th><th>Stake</th><th>Model P</th><th>Status</th><th>Entered</th><th></th></tr></thead>
      <tbody>${rows(open,true)}${rows(closed,false)}</tbody>
    </table>${tallyHtml}`;
}
const SESSION_LABEL_NFL='PAPER/SHADOW, T-534/GG-263';

// ═══════════════════════════════════════════════════════
// Refresh loop
// ═══════════════════════════════════════════════════════
const REFRESH_S=30;
let countdown=0,timer=null;

function setStatus(ok,text){
  document.getElementById('dot').className='dot '+(ok?'live':'err');
  document.getElementById('status-text').textContent=text;
}
function setError(msg){
  const el=document.getElementById('err-banner');
  if(msg){el.style.display='block';el.textContent=msg;}
  else{el.style.display='none';}
}

async function refresh(){
  setStatus(true,'Refreshing…');
  try{
    const resp=await fetch('/api/data?t='+Date.now());
    if(!resp.ok)throw new Error(`HTTP ${resp.status}`);
    const data=await resp.json();
    if(data.error)throw new Error(data.error);
    setError(null);
    document.getElementById('server-time').textContent=
      (data.server_time||'').replace('T',' ').slice(0,19)+' UTC';

    renderPortfolio(data);
    renderLivePositions(data);
    renderTodayBets(data);
    renderTradeLog(data);
    renderResolved(data);
    renderAlerts(data.audit, data.t4_audit);
    renderSystem(data);
    renderPipeLog(data.pipe_log);
    renderNFL(data);

    setStatus(true,'Live');
    scheduleNext();
  }catch(err){
    setStatus(false,'Connection error');
    setError('Cannot fetch data: '+err.message+
      '. Check SSH tunnel is open. Retrying in '+REFRESH_S+'s…');
    scheduleNext();
  }
}

function scheduleNext(){
  if(timer)clearTimeout(timer);
  countdown=REFRESH_S;
  timer=setTimeout(refresh,REFRESH_S*1000);
}
function forceRefresh(){if(timer)clearTimeout(timer);countdown=0;refresh();}

setInterval(()=>{
  if(countdown>0)countdown--;
  document.getElementById('next-refresh').textContent='Refresh in '+countdown+'s';
  document.getElementById('countdown').textContent='Auto-refresh every '+REFRESH_S+'s';
},1000);

refresh();
</script>
</body>
</html>"""


# ─────────────────────────────────────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="PMBot Web Dashboard — localhost HTTP server"
    )
    parser.add_argument(
        "--log-dir",
        default=os.environ.get("LOG_DIR", "/opt/prediction-market-bot/logs/"),
    )
    parser.add_argument("--port", type=int,
        default=int(os.environ.get("DASHBOARD_PORT", str(DEFAULT_PORT))))
    parser.add_argument("--host", default=os.environ.get("DASHBOARD_HOST", DEFAULT_HOST))
    args = parser.parse_args()

    global _log_dir
    _log_dir = Path(args.log_dir)

    server = HTTPServer((args.host, args.port), DashboardHandler)
    print(f"PMBot Dashboard  http://{args.host}:{args.port}")
    print(f"Log dir          {_log_dir}")
    print(f"Access via       ssh -fNL {args.port}:localhost:{args.port} root@157.230.91.33")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")


if __name__ == "__main__":
    main()
