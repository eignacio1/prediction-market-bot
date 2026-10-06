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
import re
import subprocess
import sys
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Any, Callable

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

# Cycle-log tail bound (T-600/D2). ~460 B/row observed -> ~90 KB payload.
CYCLE_TAIL_ROWS = 200
_CYCLE_LOG_NAMES = (".vps_t4_mlb_cycle_log_cache.jsonl", "t4_mlb_cycle_log.jsonl")


def _resolve_running_sha() -> str:
    """Commit sha of the code this process loaded, captured ONCE at import.

    Deliberately not re-read per request: a `git pull` after process start
    changes the checkout but not the running code, and the status bar must
    report what is running, not what is on disk (GG-279).
    """
    try:
        out = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=str(Path(__file__).parent.parent),
            capture_output=True, text=True, timeout=5,
        )
        sha = out.stdout.strip()
        return sha if out.returncode == 0 and re.fullmatch(r"[0-9a-f]{40}", sha) else "unknown"
    except Exception:
        return "unknown"


_PROCESS_STARTED_AT = datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
_RUNNING_SHA = _resolve_running_sha()


# ─────────────────────────────────────────────────────────────────────────────
# Data loading
# ─────────────────────────────────────────────────────────────────────────────

def _load_json(p: Path) -> dict:
    try:
        with open(p) as f:
            return json.load(f)
    except Exception:
        return {}


_STRING_OR_BRACKET_RE = re.compile(r'"(?:\\.|[^"\\])*"|[\[\]]')


def _strip_json_array_key_scan(text: str, key: str, start: int) -> str:
    """General fallback: bracket-depth scan from `start` (index of the
    array's opening `[`) to find its matching `]`, string/escape aware via
    re.finditer so it works regardless of nested brackets/strings inside the
    array. No-ops (returns `text` unchanged) if no match is found.

    This is the correctness-preserving path for any key/position — including
    the fast path's own validation fallback below — but it's O(array size):
    a hand-rolled char-by-char version of this scan took 14.15s against the
    VPS's real 39MB t4 file, and this regex-token version (walking whole
    string tokens in one C-level step instead of one Python loop iteration
    per character) still takes ~4.6s (GG-272/T-540, measured directly). Both
    numbers are why `_strip_json_array_key` below tries an O(1) shortcut
    first and only falls back to this scan when that shortcut doesn't apply.
    """
    depth = 0
    for m in _STRING_OR_BRACKET_RE.finditer(text, start):
        tok = m.group()
        if tok == "[":
            depth += 1
        elif tok == "]":
            depth -= 1
            if depth == 0:
                return text[:start] + "[]" + text[m.end():]
        # else: a whole string token, matched (and skipped) in one step
    return text


def _strip_json_array_key(text: str, key: str) -> str:
    """Replace `"<key>": [...]` with `"<key>": []` in a raw JSON text blob.

    No-ops (returns text unchanged) if `key` isn't found or its value isn't
    an array — callers still json.load the result either way, so a no-op
    just means no memory was saved, never a parse failure.

    GG-272/T-540: the general scan (`_strip_json_array_key_scan`) is
    correct for any key/position but costs several seconds against the
    VPS's real 39MB t4 file — too slow for "comfortably under 2s" even after
    a regex-based speedup (see that function's docstring for the numbers).
    `rejected_positions` is confirmed (2026-09-11, GG-272) to be that file's
    *last* top-level key, so its closing `]` is necessarily the last `]` in
    the whole text, immediately followed (mod whitespace) by the object's
    final `}` — a fact checkable with a couple of C-level `rfind`/`strip`
    calls in ~O(1) time regardless of file size, instead of scanning the
    ~35MB array itself. That shortcut is verified before use by parsing the
    resulting (now-small) candidate text with `json.loads` — cheap once the
    huge array is gone (~0.1s on the real file) — and this function falls
    back to the general scan whenever the shortcut doesn't apply (wrong key,
    reordered fields, malformed candidate), so correctness never depends on
    this key staying last.
    """
    needle = f'"{key}"'
    i = text.find(needle)
    if i == -1:
        return text
    j = text.find(":", i + len(needle))
    if j == -1:
        return text
    j += 1
    while j < len(text) and text[j] in " \t\r\n":
        j += 1
    if j >= len(text) or text[j] != "[":
        return text
    start = j

    last_brace = text.rfind("}")
    if last_brace > start and not text[last_brace + 1:].strip():
        last_close = text.rfind("]", start, last_brace)
        if last_close != -1 and not text[last_close + 1:last_brace].strip():
            candidate = text[:start] + "[]" + text[last_close + 1:]
            try:
                json.loads(candidate)
            except ValueError:
                pass
            else:
                return candidate

    return _strip_json_array_key_scan(text, key, start)


def _load_json_dropping_key(p: Path, key: str) -> dict:
    """Like _load_json, but strips `key`'s array value out of the raw text
    before parsing, instead of letting json.load() materialize it.

    paper_portfolio_mlb_t4.json's `rejected_positions` list grows unbounded
    (24k+ entries, ~33MB of the file's ~38MB observed 2026-09-10) and is
    never read by the dashboard frontend (grep confirms only open_positions/
    closed_positions are consumed) — parsing it into Python objects on every
    /api/data request cost ~4.3s and ~96MB of peak memory per call, blowing
    past the service's 128M MemoryMax and OOM-killing the process in a
    restart loop (GG-270/T-539). This drops it before parse time so those
    objects are never constructed, while every other field stays
    byte-identical to a plain _load_json call.
    """
    try:
        with open(p) as f:
            text = f.read()
    except Exception:
        return {}
    text = _strip_json_array_key(text, key)
    try:
        return json.loads(text)
    except Exception:
        return {}


def _read_tail_lines(p: Path, n: int, chunk_size: int = 1 << 16) -> list[str]:
    """Return the last `n` non-empty lines of a file, seeking backward from
    EOF in chunks (like `tail -n`) instead of reading/iterating the whole
    file (GG-272/T-540).

    `audit_mlb_t4.jsonl` (433MB) and `audit_mlb.jsonl` (101MB) on the VPS
    made the previous approach — a bounded-memory deque fed by `for line in
    f` over the entire file — bounded in memory but not in *time*: it still
    read and split every byte of both files on every /api/data request,
    ~2s by itself even after the rejected_positions fix below brought that
    key's own cost to ~0.1s. Reading backward in fixed-size chunks until
    enough newlines are seen touches only the tail actually needed,
    regardless of how large the rest of the file grows.
    """
    with open(p, "rb") as f:
        f.seek(0, os.SEEK_END)
        pos = f.tell()
        blocks: list[bytes] = []
        newlines = 0
        while pos > 0 and newlines <= n:
            read_size = min(chunk_size, pos)
            pos -= read_size
            f.seek(pos)
            block = f.read(read_size)
            blocks.append(block)
            newlines += block.count(b"\n")
        data = b"".join(reversed(blocks))
    text = data.decode("utf-8", errors="replace")
    lines = [ln for ln in text.splitlines() if ln.strip()]
    return lines[-n:] if n else lines


def _load_jsonl(p: Path, tail: int = 500) -> list[dict]:
    if not p.exists():
        return []
    try:
        lines = _read_tail_lines(p, tail)
    except Exception:
        lines = []
    entries: list[dict] = []
    for line in lines:
        try:
            entries.append(json.loads(line))
        except json.JSONDecodeError:
            pass
    return entries


def _load_tail(p: Path, n: int = 40) -> list[str]:
    if not p.exists():
        return []
    try:
        return _read_tail_lines(p, n)
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


_JSON_TOKEN_RE = re.compile(r'"(?:\\.|[^"\\])*"|[\[\]{}]')
_REJECTED_COUNT_CACHE: dict[str, tuple[float, int, Any]] = {}
_COUNT_LINE_LIMIT = 1 << 20


def _count_json_array_key(p: Path, key: str) -> int | None:
    """Count the elements of `"<key>": [...]` WITHOUT materializing it.

    Streams the file line by line (bounded memory: one line <= 1 MiB), tracks
    bracket/brace depth with string-aware tokens, and counts elements that
    open at the array's top level (objects/arrays/strings; rejected_positions
    holds objects). Relies on the writer's indent=2 layout only for bounded
    line length: a line over the limit aborts with None ("unknown"), never a
    guess. Cached by (mtime, size) so unchanged files cost one stat.
    Returns None when the file or key is absent/unreadable.
    """
    try:
        st = p.stat()
    except OSError:
        return None
    ck = f"{p}:{key}"
    hit = _REJECTED_COUNT_CACHE.get(ck)
    if hit and hit[0] == st.st_mtime and hit[1] == st.st_size:
        return hit[2]
    needle = f'"{key}"'
    count = 0
    depth = 0          # 0 = before/after the array; 1 = directly inside it
    in_array = False
    done = False
    result: int | None = None
    with open(p, "rb") as f:
        while True:
            raw = f.readline(_COUNT_LINE_LIMIT)
            if not raw:
                break
            if len(raw) == _COUNT_LINE_LIMIT and not raw.endswith(b"\n"):
                return None
            line = raw.decode("utf-8", errors="replace")
            if not in_array:
                i = line.find(needle)
                if i == -1:
                    continue
                j = line.find("[", i + len(needle))
                if j == -1:
                    return None
                in_array = True
                line = line[j:]
            for m in _JSON_TOKEN_RE.finditer(line):
                tok = m.group()
                if tok in "[{":
                    if depth == 1:
                        count += 1
                    depth += 1
                elif tok in "]}":
                    depth -= 1
                    if depth == 0:
                        done = True
                        break
                elif depth == 1:
                    count += 1  # string element
            if done:
                result = count
                break
    _REJECTED_COUNT_CACHE[ck] = (st.st_mtime, st.st_size, result)
    return result


def _rejected_counts(d: Path) -> dict[str, int | None]:
    """Rejected-position COUNT per pool (T-600/D2). Counts only — the arrays
    themselves stay out of the payload. Each pool isolated so one bad file
    yields None for that pool alone."""
    pools = {
        "mlb": "paper_portfolio_mlb.json",
        "mlb_t4": "paper_portfolio_mlb_t4.json",
        "nfl": "paper_portfolio_t1_nfl_game_market.json",
    }
    out: dict[str, int | None] = {}
    for pool, fname in pools.items():
        try:
            out[pool] = _count_json_array_key(d / fname, "rejected_positions")
        except Exception:
            out[pool] = None
    return out


def _load_cycle_tail(d: Path, n: int = CYCLE_TAIL_ROWS) -> list[dict]:
    for name in _CYCLE_LOG_NAMES:
        if (d / name).exists():
            return _load_jsonl(d / name, tail=n)
    return []


# ─────────────────────────────────────────────────────────────────────────────
# Operator terminal v2 (Wave 47 / 47.1 D6) — additive, read-only keys.
# Every value is read from a file a block writes. A missing source yields
# {"awaiting": "<source>"} — never a placeholder number.
# ─────────────────────────────────────────────────────────────────────────────

_REPO_ROOT = Path(__file__).resolve().parent.parent
# Shadow ledgers are append-only JSONL, one row per (run_id, market_ticker) in
# the 47.2 schema. The writer's directory is not fixed yet, so several
# candidate globs (relative to the repo root) are scanned; rows self-describe
# their cell via sport/market_type/band, so filenames do not matter.
SHADOW_GLOBS = ("logs/shadow/*.jsonl", "logs/shadow_*.jsonl",
                "exp_output/PREGAME_SHADOW/**/*.jsonl",
                # T-621: NHL (EXP-036) and later runners write data/shadow/<sport>/<CELL>.jsonl;
                # the earlier globs missed them, so the SHADOW module read AWAITING over live rows.
                "data/shadow/**/*.jsonl")
SHADOW_TAIL_ROWS = 300
VERDICT_SOURCES = (
    ("GATE2", "exp_output/BOARD_SURVEY_SPORTS_G2/gate2_result.json"),
    ("EXP-034", "exp_output/EXP-034-NONSPORTS-CONTROL/d1b_gate_result.json"),
    ("EXP-035", "exp_output/EXP-035-BOARD-SURVEY-SPORTS/gate_result.json"),
)
_COVERAGE_RECENT_DAYS = 7


def _parse_ts(s: Any) -> float | None:
    try:
        return datetime.fromisoformat(str(s).replace("Z", "+00:00")).timestamp()
    except Exception:
        return None


def _season_state(now: datetime) -> dict:
    """Coarse season calendar per sport -> expected cadence (amber/red seconds).

    Idle in an off-window is not red: off-season panels get state 'off' and no
    thresholds, so the frontend greys them instead of alarming.
    """
    m, d = now.month, now.day
    def win(active: bool, amber: int, red: int) -> dict:
        return {"state": "in_season" if active else "off",
                "amber_s": amber if active else None, "red_s": red if active else None}
    nfl = m in (9, 10, 11, 12, 1) or (m == 2 and d <= 14)
    nhl = m in (10, 11, 12, 1, 2, 3, 4, 5) or (m == 6 and d <= 25)
    mlb_post = (m == 10) or (m == 9 and d >= 28)
    mlb = (4 <= m <= 9) or mlb_post or (m == 3 and d >= 26)
    return {"MLB": win(mlb, 6 * 3600, 24 * 3600),
            "MLB_POSTSEASON": win(mlb_post, 6 * 3600, 24 * 3600),
            "NFL": win(nfl, 3 * 86400, 7 * 86400),
            "NHL": win(nhl, 24 * 3600, 3 * 86400)}


def _file_age(p: Path, now_ts: float) -> float | None:
    try:
        return max(0.0, now_ts - p.stat().st_mtime)
    except Exception:
        return None


def _last_row_ts(p: Path) -> float | None:
    rows = _load_jsonl(p, tail=1) if p.exists() else []
    if not rows:
        return None
    r = rows[-1]
    return _parse_ts(r.get("ts") or r.get("ts_utc") or r.get("timestamp"))


def _freshness(d: Path, now: datetime) -> dict:
    now_ts = now.timestamp()
    season = _season_state(now)
    def cyc() -> float | None:
        for name in _CYCLE_LOG_NAMES:
            if (d / name).exists():
                t = _last_row_ts(d / name)
                return None if t is None else max(0.0, now_ts - t)
        return None
    panels = {
        "t1_mlb":    ("paper_portfolio_mlb.json", _file_age(d / "paper_portfolio_mlb.json", now_ts), "MLB"),
        "t4_mlb":    ("t4_mlb_cycle_log.jsonl", cyc(), "MLB"),
        "nfl":       ("audit_t1_nfl_game_market.jsonl",
                      _file_age(d / "audit_t1_nfl_game_market.jsonl", now_ts), "NFL"),
        "audit_mlb": ("audit_mlb.jsonl", _file_age(d / "audit_mlb.jsonl", now_ts), "MLB"),
    }
    out = {}
    for k, (src, age, sport) in panels.items():
        s = season[sport]
        if age is None:
            out[k] = {"source": src, "awaiting": src, "age_s": None, "level": "none"}
            continue
        lvl = "off" if s["state"] == "off" else (
            "red" if age > s["red_s"] else "amber" if age > s["amber_s"] else "ok")
        out[k] = {"source": src, "age_s": round(age, 1), "level": lvl,
                  "season": s["state"], "amber_s": s["amber_s"], "red_s": s["red_s"]}
    return out


_ORIGIN_CACHE: dict = {"at": 0.0, "val": None}


def _git(args: list[str]) -> str | None:
    try:
        r = subprocess.run(["git", *args], cwd=str(_REPO_ROOT), capture_output=True,
                           text=True, timeout=4)
        return r.stdout.strip() if r.returncode == 0 else None
    except Exception:
        return None


def _origin_status() -> dict:
    """origin/main sha vs the RUNNING sha. Reads the local remote-tracking ref
    (no network in the request path); `as_of` is FETCH_HEAD's mtime so a stale
    ref is visible rather than silently trusted. Cached 30s."""
    import time
    if _ORIGIN_CACHE["val"] is not None and time.time() - _ORIGIN_CACHE["at"] < 30:
        return _ORIGIN_CACHE["val"]
    sha = _git(["rev-parse", "origin/main"])
    if not sha or not re.fullmatch(r"[0-9a-f]{40}", sha):
        val = {"awaiting": "origin/main ref", "running_sha": _RUNNING_SHA}
    else:
        behind = None
        if _RUNNING_SHA != "unknown":
            n = _git(["rev-list", "--count", f"{_RUNNING_SHA}..origin/main"])
            behind = int(n) if n and n.isdigit() else None
        try:
            as_of = datetime.fromtimestamp(
                (_REPO_ROOT / ".git" / "FETCH_HEAD").stat().st_mtime, tz=timezone.utc
            ).strftime("%Y-%m-%dT%H:%M:%SZ")
        except Exception:
            as_of = None
        val = {"origin_sha": sha, "running_sha": _RUNNING_SHA,
               "commits_behind": behind, "ref_as_of": as_of}
    _ORIGIN_CACHE.update(at=time.time(), val=val)
    return val


def _coverage(now: datetime) -> dict:
    """92-cell (market type x band) grid from the registry, by status."""
    try:
        sys.path.insert(0, str(_REPO_ROOT / "src"))
        from prediction_market_bot.c5_execution import market_type_registry as R
        cells = list(R.MARKET_TYPE_REGISTRY.values()) if isinstance(
            R.MARKET_TYPE_REGISTRY, dict) else list(R.MARKET_TYPE_REGISTRY)
    except Exception as e:
        return {"awaiting": f"market_type_registry ({type(e).__name__})"}
    out, counts, bands, types = [], {}, [], []
    cutoff = now.timestamp() - _COVERAGE_RECENT_DAYS * 86400
    for c in cells:
        st = getattr(c.status, "name", str(c.status)).lower()
        mt = getattr(c.market_type, "name", str(c.market_type))
        bd = getattr(c.band, "name", str(c.band))
        md = getattr(c, "measured_date", None)
        mts = _parse_ts(md) if md else None
        recent = st == "shadow" or (mts is not None and mts >= cutoff)
        counts[st] = counts.get(st, 0) + 1
        if bd not in bands: bands.append(bd)
        if mt not in types: types.append(mt)
        out.append({"market_type": mt, "band": bd, "status": st, "recent": recent,
                    "reason": getattr(c, "reason", None)})
    return {"cells": out, "counts": counts, "total": len(out), "bands": bands,
            "market_types": types,
            "recent_rule": f"SHADOW status or measured_date within {_COVERAGE_RECENT_DAYS}d"}


# W52.E (T-658): ledger rows carry short bands; the registry keys on ExecutionBand names.
_SHADOW_BAND_NAMES = {"T1": "T1_MULTI_DAY", "T2": "T2_SAME_DAY", "T3": "T3_PRE_TIP"}


def _registry_cells() -> dict | None:
    """{(MarketType name, ExecutionBand name): (status, sport)} from the registry, or None if unreadable."""
    try:
        sys.path.insert(0, str(_REPO_ROOT / "src"))
        from prediction_market_bot.c5_execution import market_type_registry as R
        cells = R.MARKET_TYPE_REGISTRY.values() if isinstance(R.MARKET_TYPE_REGISTRY, dict) \
            else R.MARKET_TYPE_REGISTRY
        sports = getattr(R, "_SPORT_BY_MARKET_TYPE", {})
        return {(c.market_type.name, c.band.name): (c.status.name.lower(),
                                                    str(sports.get(c.market_type, "")).upper() or None)
                for c in cells}
    except Exception:
        return None


def _count_lines(p: Path) -> int | None:
    try:
        with p.open("rb") as fh:
            return sum(chunk.count(b"\n") for chunk in iter(lambda: fh.read(1 << 20), b""))
    except Exception:
        return None


def _shadow(now: datetime) -> dict:
    """Every shadow cell, labelled by what it is (W52.E / T-658):
    - each ledger with rows, with its registry status (a ledger whose registry cell is not
      SHADOW is shown as such -- not hidden, not upgraded);
    - each registry SHADOW cell, even with no ledger rows (rows 0, 'no ledger rows found');
    - rows_total / last row per cell; `settled/` copies (nhl_shadow_settle.py) are not ledgers:
      they feed settled_n only and are never counted as rows or shown on the tape."""
    files: list[Path] = []
    for g in SHADOW_GLOBS:
        files += sorted(_REPO_ROOT.glob(g))
    reg = _registry_cells()
    if not files and not reg:
        return {"awaiting": "shadow ledgers (47.2/47.3 runner)", "cells": [], "tape": []}
    day = now.strftime("%Y-%m-%d")
    cells: dict = {}
    tape: list = []
    settled_files = [f for f in files if "settled" in f.relative_to(_REPO_ROOT).parts[:-1]]
    files = [f for f in files if f not in settled_files]
    for f in files:
        rows = _load_jsonl(f, tail=SHADOW_TAIL_ROWS)
        file_cells: set = set()
        for r in rows:
            key = f"{r.get('sport')}|{r.get('market_type')}|{r.get('band')}"
            file_cells.add(key)
            c = cells.setdefault(key, {"sport": r.get("sport"), "market_type": r.get("market_type"),
                                       "band": r.get("band"), "rows_today": 0, "rows_total": 0,
                                       "last_ts": None,
                                       "latest_e_net": None, "settled_n": None, "judged_n": None,
                                       "delta_brier_market": None, "delta_brier_climo": None})
            ts = str(r.get("ts_utc") or "")
            if ts.startswith(day): c["rows_today"] += 1
            if c["last_ts"] is None or ts > c["last_ts"]:
                c["last_ts"] = ts
                c["latest_e_net"] = r.get("e_net_yes_k007")
            tape.append(r)
        if len(file_cells) == 1:            # one cell per file (both writers): exact total
            n = _count_lines(f)
            if n is not None:
                cells[next(iter(file_cells))]["rows_total"] += n
        else:                               # mixed file: only the tail is known
            for r in rows:
                cells[f"{r.get('sport')}|{r.get('market_type')}|{r.get('band')}"]["rows_total"] += 1
        # scored summary, if the settlement join has written one beside the ledger
        sc = f.with_name(f.stem + ".scored.json")
        if sc.exists():
            s = _load_json(sc)
            for key, c in cells.items():
                if s.get("cell") in (None, key):
                    for k in ("settled_n", "judged_n", "delta_brier_market", "delta_brier_climo"):
                        if k in s: c[k] = s[k]
    for sf in settled_files:            # settled copies: count settled rows per cell, nothing else
        for r in _load_jsonl(sf, tail=100000):
            c = cells.get(f"{r.get('sport')}|{r.get('market_type')}|{r.get('band')}")
            if c is not None and r.get("outcome") is not None:
                c["settled_n"] = (c["settled_n"] or 0) + 1
    seen = set()
    for c in cells.values():
        full = _SHADOW_BAND_NAMES.get(str(c["band"]), str(c["band"]))
        seen.add((c["market_type"], full))
        st = (reg or {}).get((c["market_type"], full))
        c["registry_status"] = st[0] if st else ("unregistered" if reg is not None else "unknown")
    for (mt, bd), (st, sport) in sorted((reg or {}).items()):
        if st == "shadow" and (mt, bd) not in seen:
            cells[f"{sport}|{mt}|{bd}"] = {
                "sport": sport, "market_type": mt, "band": bd, "rows_today": 0, "rows_total": 0,
                "last_ts": None, "latest_e_net": None, "settled_n": None, "judged_n": None,
                "delta_brier_market": None, "delta_brier_climo": None, "registry_status": "shadow",
                "ledger": "no ledger rows found"}
    tape.sort(key=lambda r: str(r.get("ts_utc") or ""), reverse=True)
    keep = ("ts_utc", "sport", "market_type", "band", "market_ticker", "p_yes", "mid",
            "e_net_yes_k007", "e_net_no_k007")
    stream_keep = keep + ("event_ticker", "run_id")
    return {"cells": list(cells.values()), "tape": [{k: r.get(k) for k in keep} for r in tape[:60]],
            "stream": [{k: r.get(k) for k in stream_keep} for r in tape[:DECISION_ROWS]]}


# W56.2: decision stream. One row per EVALUATION, never per order. WOULD-FIRE is a shadow
# computation -- fee-adjusted net edge > 0 -- not an order, not a sizing decision.
DECISION_ROWS = 150


def _decision_from_shadow(r: dict) -> dict:
    y, n = r.get("e_net_yes_k007"), r.get("e_net_no_k007")
    best, side = None, None
    cands = [(v, sd) for v, sd in ((y, "YES"), (n, "NO")) if isinstance(v, (int, float))]
    if cands:
        best, side = max(cands)
    p = r.get("p_yes")
    return {"ts": r.get("ts_utc"), "sport": r.get("sport"), "market": r.get("market_ticker"),
            "market_type": r.get("market_type"), "band": r.get("band"), "p": p,
            "price": r.get("mid"), "edge": best, "side": side,
            "would_fire": bool(best is not None and best > 0), "src": "shadow"}


def _decision_from_cycle(r: dict) -> dict:
    e = r.get("net_edge")
    ts = r.get("ts")
    return {"ts": ts, "sport": "MLB", "market": r.get("ticker"), "market_type": "MLB_PLAYER_PROP_HITS",
            "band": "T4M-PROJ", "p": r.get("p_t4"), "price": r.get("mip"),
            "edge": e if isinstance(e, (int, float)) else None, "side": "YES",
            "would_fire": bool(isinstance(e, (int, float)) and e > 0), "src": "t4_cycle"}


def _drawdown_limit():
    """Kill-switch drawdown limit. Import risk.py when possible; else read the literal from its source
    (the VPS dashboard python lacks jsonlines, so the import fails there). None if neither works."""
    try:
        return _hard_limits()["max_drawdown_pct"]
    except Exception:
        pass
    try:
        import re
        m = re.search(r'"max_drawdown_pct"\s*:\s*([0-9.]+)',
                      (_REPO_ROOT / "src/prediction_market_bot/c4_risk_engine/risk.py").read_text())
        return float(m.group(1)) if m else None
    except Exception:
        return None


def _book(p: dict, now: datetime, name: str) -> dict:
    """Realized drawdown (kill-switch basis, W51.1) for one paper book; None when unreadable."""
    init, rp = p.get("initial_bankroll_usd"), p.get("total_realized_pnl")
    lim = _drawdown_limit()
    dd = max(0.0, -rp) / init if isinstance(init, (int, float)) and init > 0 and isinstance(rp, (int, float)) else None
    lu = _parse_ts(p.get("last_updated"))
    return {"book": name, "initial": init, "realized_pnl": rp, "drawdown": dd, "limit": lim,
            "tripped": bool(dd is not None and lim is not None and dd >= lim),
            "age_s": None if lu is None else round(max(0.0, now.timestamp() - lu), 1),
            "awaiting": None if dd is not None else "portfolio"}


def _decisions(now: datetime, shadow: dict, cycle_tail: list, t1p: dict, t4p: dict) -> dict:
    rows = [_decision_from_shadow(r) for r in (shadow or {}).get("stream") or []]
    rows += [_decision_from_cycle(r) for r in cycle_tail or []]
    rows = [r for r in rows if r["ts"]]
    rows.sort(key=lambda r: str(r["ts"]), reverse=True)
    rows = rows[:DECISION_ROWS]
    arms: dict = {}
    for c in (shadow or {}).get("cells") or []:
        if not c.get("last_ts"):
            continue
        k = f"{c.get('sport') or c.get('market_type') or 'unlabelled'} {c.get('band') or '—'}"
        a = arms.setdefault(k, {"arm": k, "last_ts": None, "rows_today": 0})
        a["rows_today"] += c.get("rows_today") or 0
        if a["last_ts"] is None or c["last_ts"] > a["last_ts"]:
            a["last_ts"] = c["last_ts"]
    cyc = [r for r in cycle_tail or [] if r.get("ts")]
    if cyc:
        arms["MLB T4M-PROJ"] = {"arm": "MLB T4M-PROJ", "last_ts": max(str(r["ts"]) for r in cyc),
                                "rows_today": sum(1 for r in cyc if str(r["ts"])[:10] == now.strftime("%Y-%m-%d"))}
    for a in arms.values():
        t = _parse_ts(a["last_ts"])
        a["age_s"] = None if t is None else round(max(0.0, now.timestamp() - t), 1)
    try:
        kel = {k: v for k, v in _band_kelly().items() if k in ("T1", "T4M-PROJ")}
    except Exception:
        kel = None
    return {"rows": rows, "arms": sorted(arms.values(), key=lambda a: a["arm"]),
            "books": [_book(t1p, now, "T1"), _book(t4p, now, "T4M-PROJ")],
            "kelly": kel, "sizing_live": (None if kel is None else any(v for v in kel.values())),
            "fire_rule": "WOULD-FIRE = fee-adjusted net edge > 0 (shadow computation; no order, stake $0)"}


def _verdicts() -> dict:
    out = {}
    for name, rel in VERDICT_SOURCES:
        p = _REPO_ROOT / rel
        if not p.exists():
            out[name] = {"awaiting": rel}
            continue
        j = _load_json(p)
        g = j.get("gate")
        if isinstance(g, dict) and isinstance(g.get("gate"), str):
            j = {**j, "verdict": g["gate"]}      # EXP-034 shape: {"gate": {"gate": "FAIL"}}
        passed = j.get("ALL_PASSED", j.get("all_passed", j.get("passed")))
        if passed is None and isinstance(j.get("verdict"), str):
            passed = j["verdict"].upper() == "PASS"
        out[name] = {"file": rel, "passed": passed if isinstance(passed, bool) else None,
                     "verdict": j.get("verdict") or ("PASS" if passed is True else
                                                     "FAIL" if passed is False else None),
                     "written_at": datetime.fromtimestamp(p.stat().st_mtime, tz=timezone.utc
                                                          ).strftime("%Y-%m-%dT%H:%M:%SZ")}
    return out


def _mlb_postseason(d: Path, now: datetime, t1_port: dict, t4_port: dict) -> dict:
    now_ts = now.timestamp()
    ca = None
    for name in _CYCLE_LOG_NAMES:
        if (d / name).exists():
            t = _last_row_ts(d / name)
            ca = None if t is None else round(max(0.0, now_ts - t), 1)
            break
    matched = None
    for line in reversed(_load_tail(d / "paper_mlb_cron.log", n=200)):
        m = re.search(r"(\d+)\s+players in live MLB", str(line))
        if m:
            matched = int(m.group(1)); break
    def opens(p: dict) -> list:
        v = p.get("open_positions") or p.get("positions") or []
        return list(v.values()) if isinstance(v, dict) else list(v)
    allopen = opens(t1_port) + opens(t4_port)
    stuck = 0
    for p in allopen:
        t = _parse_ts(p.get("entry_time") or p.get("opened_at") or p.get("ts"))
        if t is not None and now_ts - t > 36 * 3600:
            stuck += 1
    return {"t1_players_matched_last_run": matched, "t4_cycle_age_s": ca,
            "open_positions": len(allopen), "stuck_positions": stuck,
            "stuck_rule": "open > 36h",
            "awaiting": None if (matched is not None or ca is not None) else "paper_mlb_cron.log / t4 cycle log"}


# ── PIPELINE (47.1 D6 g): C1-C8 as a flow, one tile per component per sport ──
# Each tile reads its component's real output. No observable output ->
# status "ni" ("not instrumented"), and the tile is listed under `gaps`.
_LAST_LOAD_MS: int | None = None
FEATURE_STORES = {"MLB": "exp_output/MLB/mlb_feature_matrix.csv"}
_PIPE_FEED_LOGS = ("paper_mlb_cron.log", "resolve_mlb_cron.log",
                   "mlb_feature_refresh.log", "mlb_calib_monitor.log")


FROZEN_AFTER_S = 72 * 3600


def _frozen_label(last_updated, now) -> str | None:
    """'FROZEN (last write YYYY-MM-DD)' when a book has had no write in >72h, else None."""
    try:
        lu = datetime.fromisoformat(str(last_updated).replace("Z", "+00:00"))
        if lu.tzinfo is None:
            lu = lu.replace(tzinfo=timezone.utc)
        ref = now if getattr(now, "tzinfo", None) else now.replace(tzinfo=timezone.utc)
        if (ref - lu).total_seconds() > FROZEN_AFTER_S:
            days = int((ref - lu).total_seconds() // 86400)
            return f"FROZEN (last write {lu.date().isoformat()}, {days}d ago)"
    except Exception:
        return None
    return None


def _tile(c: str, sport: str, status: str, headline: str, detail: str = "",
          source: str = "", age_s: float | None = None) -> dict:
    return {"c": c, "sport": sport, "status": status, "headline": headline,
            "detail": detail, "source": source, "age_s": age_s}


def _ni(c: str, sport: str, what: str) -> dict:
    return _tile(c, sport, "ni", "not instrumented", what)


def _newest_game_date(p: Path) -> str | None:
    """Newest game_date in a CSV feature store (tail read; header gives the column)."""
    with p.open("r", encoding="utf-8", errors="replace") as fh:
        header = fh.readline().strip().split(",")
    if "game_date" not in header:
        return None
    i = header.index("game_date")
    best = None
    for line in _read_tail_lines(p, 4000):
        cols = line.split(",")
        if len(cols) > i and re.fullmatch(r"\d{4}-\d{2}-\d{2}", cols[i].strip()):
            best = max(best or cols[i].strip(), cols[i].strip())
    return best


def _band_kelly() -> dict[str, float]:
    from prediction_market_bot.execution_bands import BAND_CONFIGS
    return {b.value: c.kelly_fraction for b, c in BAND_CONFIGS.items()}


def _hard_limits() -> dict:
    from prediction_market_bot.c4_risk_engine.risk import _HARD_LIMITS, MAX_DAILY_LOSS_PCT
    return {**_HARD_LIMITS, "MAX_DAILY_LOSS_PCT": MAX_DAILY_LOSS_PCT}


def _comp_stats(rows: list[dict], comp: str, now_ts: float) -> dict:
    mine = [r for r in rows if r.get("component") == comp]
    ts = [t for t in (_parse_ts(r.get("timestamp")) for r in mine) if t]
    last = max(ts) if ts else None
    last_ev = next((r.get("event_type") for r in reversed(mine)), None)
    h = sum(1 for t in ts if now_ts - t <= 3600)
    return {"n": len(mine), "last_age_s": (now_ts - last) if last else None,
            "last_event": last_ev, "last_hour": h}


def _pipeline(d: Path, now: datetime, data: dict | None = None) -> dict:
    now_ts = now.timestamp()
    season = _season_state(now)
    tiles: list[dict] = []
    gaps: list[str] = []
    audit = list((data or {}).get("audit") or []) + list((data or {}).get("t4_audit") or [])

    # ---- MLB ----
    # C1: last pull per feed + failures in the T1 cron log tail
    ages = {}
    for f in _PIPE_FEED_LOGS:
        a = _file_age(d / f, now_ts)
        if a is not None:
            ages[f] = a
    log_tail = _load_tail(d / "paper_mlb_cron.log", n=400) if (d / "paper_mlb_cron.log").exists() else []
    fails = sum(1 for ln in log_tail if re.search(r"\b406\b|Traceback|ERROR", ln))
    if ages:
        newest = min(ages.values())
        tiles.append(_tile("C1", "MLB", "bad" if fails else "ok",
                           f"{len(ages)}/{len(_PIPE_FEED_LOGS)} feeds seen · newest {int(newest // 3600)}h ago",
                           f"failures in last 400 log lines: {fails}",
                           "logs/{paper,resolve,mlb_feature_refresh,mlb_calib_monitor}*.log mtime",
                           newest))
    else:
        tiles.append(_ni("C1", "MLB", "awaiting cron logs"))
    # C2: newest game_date in the feature store
    fs = _REPO_ROOT / FEATURE_STORES["MLB"]
    try:
        gd = _newest_game_date(fs) if fs.exists() else None
    except Exception:
        gd = None
    if gd:
        lag = (now.date() - datetime.strptime(gd, "%Y-%m-%d").date()).days
        live_season = season.get("MLB", {}).get("state") in ("in_season", "postseason", "live")
        st = "ok" if lag <= 2 else ("bad" if live_season else "off")
        tiles.append(_tile("C2", "MLB", st, f"newest game_date {gd}",
                           f"{lag}d behind today" + ("" if live_season else " (MLB not in season)"),
                           FEATURE_STORES["MLB"], lag * 86400.0))
    else:
        tiles.append(_ni("C2", "MLB", "feature store not readable: " + FEATURE_STORES["MLB"]))
    # C3: model id/sha — no model sha is emitted by the T1/T4 MLB audit rows
    tiles.append(_ni("C3", "MLB", "no model id/sha in audit output (T1 LR+Platt, T4M binomial)"))
    # C4: kelly per band (live import), kill-switch, drawdown vs limit
    try:
        kel = _band_kelly()
        lim = _hard_limits()
        pf = (data or {}).get("portfolio") or {}
        init, bank = pf.get("initial_bankroll_usd"), pf.get("bankroll_usd")
        # W51.1: the kill switch reads REALIZED loss only (run_mlb_paper_trade.py:
        # max(0, -total_realized_pnl) / initial). (init - bank) / init also counts
        # stake locked in open positions, so it is a different, larger quantity.
        rpnl = pf.get("total_realized_pnl")
        dd = max(0.0, -rpnl) / init if init and rpnl is not None and init > 0 else None
        open_stake = sum(float(p.get("size_usd") or 0) for p in (pf.get("open_positions") or []))
        frozen = _frozen_label(pf.get("last_updated"), now)
        ks = any("KILL" in str(r.get("event_type", "")).upper() for r in audit[-500:])
        live_k = {k: v for k, v in kel.items() if k in ("T1", "T4M-PROJ")}
        st = "bad" if ks else ("warn" if dd is not None and dd >= 0.8 * lim["max_drawdown_pct"] else "ok")
        tiles.append(_tile("C4", "MLB", st,
                           "kill switch TRIPPED" if ks else "kill switch clear",
                           f"kelly {live_k} · drawdown "
                           + (f"{dd:.1%}" if dd is not None else "n/a")
                           + f" realized vs limit {lim['max_drawdown_pct']:.0%}"
                           + f" · open stake ${open_stake:,.2f}"
                           + (f" · {frozen}" if frozen else ""),
                           "execution_bands.BAND_CONFIGS · risk._HARD_LIMITS · paper_portfolio_mlb.json"))
    except Exception as e:
        tiles.append(_ni("C4", "MLB", f"risk config unreadable ({type(e).__name__})"))
    # C5: orders actually submitted are counted from audit rows, never asserted
    rej = {k: v for k, v in ((data or {}).get("rejected_counts") or {}).items() if v is not None}
    if audit:
        sub = sum(1 for r in audit if re.search(r"order.*(submit|placed)|submit.*order",
                                                str(r.get("event_type", "")), re.I))
        tiles.append(_tile("C5", "MLB", "warn" if sub else "ok",
                           f"{sub} order-submit events in audit tail",
                           "ledger: paper portfolios only · rejections: "
                           + (", ".join(f"{k}={v}" for k, v in rej.items()) or "none recorded"),
                           "audit_mlb*.jsonl event_type · rejected_counts"))
    else:
        tiles.append(_ni("C5", "MLB", "no audit rows to count order events"))
    # C6/C7: audit event rate, last event, alarms
    c6 = _comp_stats(audit, "C6", now_ts)
    allr = _comp_stats([dict(r, component="ALL") for r in audit], "ALL", now_ts)
    if audit:
        tiles.append(_tile("C6", "MLB", "ok" if allr["last_hour"] else "off",
                           f"{allr['last_hour']} events/h · last {allr['last_event']}",
                           f"{len(audit)} rows in tail; C6-tagged {c6['n']}", "audit_mlb*.jsonl", allr["last_age_s"]))
    else:
        tiles.append(_ni("C6", "MLB", "awaiting audit_mlb.jsonl"))
    alarms = [r for r in audit if r.get("component") == "C7" and r.get("severity") in ("WARNING", "ERROR", "CRITICAL")]
    if audit:
        recent = [r for r in alarms if (_parse_ts(r.get("timestamp")) or 0) >= now_ts - 86400]
        tiles.append(_tile("C7", "MLB", "warn" if recent else "ok",
                           f"{len(recent)} C7 alarms in 24h",
                           f"{len(alarms)} in audit tail; staleness/contamination via freshness panel",
                           "audit_mlb*.jsonl (component=C7)"))
    else:
        tiles.append(_ni("C7", "MLB", "awaiting audit rows"))

    # ---- NFL ----
    nfl_audit = list((data or {}).get("nfl_audit") or [])
    if nfl_audit:
        st = _comp_stats(nfl_audit, "C1", now_ts)
        newest = max((t for t in (_parse_ts(r.get("timestamp")) for r in nfl_audit) if t), default=None)
        tiles.append(_tile("C1", "NFL", "ok", f"{len(nfl_audit)} audit rows",
                           "NFL game-market pipeline", "audit_t1_nfl_game_market.jsonl",
                           (now_ts - newest) if newest else None))
    else:
        tiles.append(_ni("C1", "NFL", "no audit_t1_nfl_game_market.jsonl rows"))
    tiles.append(_ni("C2", "NFL", "no NFL feature store"))
    prov = str((data or {}).get("nfl_model_provenance") or _NFL_MODEL_PROVENANCE)
    tiles.append(_tile("C3", "NFL", "bad" if "STUB" in prov.upper() else "ok",
                       "STUB MODEL IN USE" if "STUB" in prov.upper() else "trained model",
                       prov, "run_t1_nfl_game_market (PROVENANCE)"))
    try:
        nk = _band_kelly().get("T1")
    except Exception:
        nk = None
    tiles.append(_tile("C4", "NFL", "ok", f"kelly T1 {nk}", "same C4 limits as MLB (sport-agnostic)",
                       "execution_bands.BAND_CONFIGS"))
    if nfl_audit:
        sub = sum(1 for r in nfl_audit if re.search(r"order.*(submit|placed)|submit.*order",
                                                    str(r.get("event_type", "")), re.I))
        tiles.append(_tile("C5", "NFL", "warn" if sub else "ok",
                           f"{sub} order-submit events in audit tail", "paper ledger only",
                           "audit_t1_nfl_game_market.jsonl event_type"))
    else:
        tiles.append(_ni("C5", "NFL", "no audit rows to count order events"))
    tiles.append(_ni("C6", "NFL", "no per-sport audit rate wired") if not nfl_audit else
                 _tile("C6", "NFL", "ok", f"{len(nfl_audit)} rows in tail", "", "audit_t1_nfl_game_market.jsonl"))
    tiles.append(_ni("C7", "NFL", "no NFL monitoring output"))

    # ---- C8 (server) ----
    ms = _LAST_LOAD_MS
    tiles.append(_tile("C8", "SERVER", "ok", f"sha {_RUNNING_SHA[:8] if _RUNNING_SHA else '?'}",
                       f"up since {_PROCESS_STARTED_AT} · last /api/data build "
                       + (f"{ms}ms" if ms is not None else "n/a (first request)"),
                       "web_dashboard process"))
    for t in tiles:
        if t["status"] == "ni":
            gaps.append(f"{t['c']} {t['sport']}: {t['detail']}")
    return {"tiles": tiles, "gaps": gaps, "as_of": now.strftime("%Y-%m-%dT%H:%M:%SZ")}


def _load_all_data() -> dict:
    global _LAST_LOAD_MS
    _t0 = datetime.now(tz=timezone.utc)
    d = _log_dir

    # Per-key isolation (GG-270/T-539): each loader already swallows its own
    # I/O/parse exceptions and returns an empty default, but this wraps the
    # call itself too, so no single key's loader — however it fails — can
    # take down the rest of the /api/data payload.
    def safe(fn: Callable[[], Any], default: Any) -> Any:
        try:
            return fn()
        except Exception:
            return default

    out = {
        "portfolio":    safe(lambda: _load_json(d / "paper_portfolio_mlb.json"), {}),
        # rejected_positions grows unbounded and isn't read by the frontend —
        # dropped before parse time, not after. See _load_json_dropping_key.
        "t4_portfolio": safe(lambda: _load_json_dropping_key(
            d / "paper_portfolio_mlb_t4.json", "rejected_positions"), {}),
        # Pull more audit history so the trade log is comprehensive
        "audit":        safe(lambda: _load_jsonl(d / "audit_mlb.jsonl",    tail=1000), []),
        "t4_audit":     safe(lambda: _load_jsonl(d / "audit_mlb_t4.jsonl", tail=500), []),
        "pipe_log":     safe(lambda: _load_tail(d / "paper_mlb_cron.log",  n=50), []),
        "pipe_mtimes":  safe(lambda: _pipe_mtimes(d), {}),
        "server_time":  datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "current_logic_epoch": CURRENT_LOGIC_EPOCH,  # T-321
        # NFL (T-534/GG-263) — additive only, above MLB keys unchanged.
        "nfl_portfolio": safe(lambda: _load_json(d / "paper_portfolio_t1_nfl_game_market.json"), {}),
        "nfl_audit":     safe(lambda: _load_jsonl(d / "audit_t1_nfl_game_market.jsonl", tail=1000), []),
        "nfl_model_provenance": _NFL_MODEL_PROVENANCE,
        # Live Terminal (T-600/D2) — additive only; every key above unchanged.
        "rejected_counts": safe(lambda: _rejected_counts(d), {}),
        "t4_cycle_tail":   safe(lambda: _load_cycle_tail(d), []),
        "process":         safe(lambda: {"started_at": _PROCESS_STARTED_AT,
                                         "sha": _RUNNING_SHA}, {}),
        # Operator terminal v2 (47.1 D6) — additive.
        "season":          safe(lambda: _season_state(datetime.now(tz=timezone.utc)), {}),
        "freshness":       safe(lambda: _freshness(d, datetime.now(tz=timezone.utc)), {}),
        "origin":          safe(_origin_status, {}),
        "coverage":        safe(lambda: _coverage(datetime.now(tz=timezone.utc)),
                                {"awaiting": "market_type_registry"}),
        "shadow":          safe(lambda: _shadow(datetime.now(tz=timezone.utc)),
                                {"awaiting": "shadow ledgers", "cells": [], "tape": []}),
        "verdicts":        safe(_verdicts, {}),
        "mlb_postseason":  safe(lambda: _mlb_postseason(
            d, datetime.now(tz=timezone.utc),
            _load_json(d / "paper_portfolio_mlb.json"),
            _load_json_dropping_key(d / "paper_portfolio_mlb_t4.json", "rejected_positions")),
            {"awaiting": "mlb sources"}),
    }
    out["decisions"] = safe(lambda: _decisions(
        datetime.now(tz=timezone.utc), out.get("shadow") or {}, out.get("t4_cycle_tail") or [],
        out.get("portfolio") or {}, out.get("t4_portfolio") or {}),
        {"awaiting": "decision sources", "rows": [], "arms": [], "books": []})
    out["pipeline"] = safe(lambda: _pipeline(d, datetime.now(tz=timezone.utc), out),
                           {"tiles": [], "gaps": [], "awaiting": "pipeline sources"})
    _LAST_LOAD_MS = int((datetime.now(tz=timezone.utc) - _t0).total_seconds() * 1000)
    return out


# ─────────────────────────────────────────────────────────────────────────────
# HTTP Handler
# ─────────────────────────────────────────────────────────────────────────────

_PROJECT_CACHE: dict = {"t": 0.0, "html": ""}
_PROJECT_TTL_S = 60.0


def _project_page() -> str:
    """/project: analytical page regenerated from this checkout, cached at most 60 s."""
    import time as _t
    now = _t.time()
    if _PROJECT_CACHE["html"] and now - _PROJECT_CACHE["t"] < _PROJECT_TTL_S:
        return _PROJECT_CACHE["html"]
    try:
        if str(_REPO_ROOT / "scripts") not in sys.path:
            sys.path.insert(0, str(_REPO_ROOT / "scripts"))
        import generate_project_state as gps
        html = gps.render_html(gps.build_state(_REPO_ROOT), live_nav="/", link_prefix=None)
    except Exception as e:  # never 500: say what is missing
        html = ("<!doctype html><meta charset='utf-8'><title>Project State</title>"
                f"<body style='font:14px sans-serif;padding:20px'><p>awaiting generate_project_state ({type(e).__name__})</p>"
                "<p><a href='/'>Live Terminal</a></p>")
    _PROJECT_CACHE.update(t=now, html=html)
    return html


class DashboardHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        path = self.path.split("?")[0]
        if path in ("/", "/index.html"):
            self._serve_html()
        elif path == "/api/data":
            self._serve_data()
        elif path == "/project":
            self._serve_project()
        elif path == "/favicon.ico":
            self.send_response(204)
            self.send_header("Content-Length", "0")
            self.end_headers()
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

    def _serve_project(self) -> None:
        body = _project_page().encode("utf-8")
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
<title>PMBOT — LIVE TERMINAL</title>
<style>
/* ══════════════════════════════════════════════════════════════════════
   PMBOT LIVE TERMINAL
   Pure black. Colour is rationed: green/red = P&L sign only,
   amber/red = severity only, amber = chrome. Band and sport identity is
   carried by LABEL, never by hue — nothing depends on colour vision.
   Contrast on #000: ink 17.1 · dim 6.1 · amber 11.5 · green 10.0 · red 6.4
   ══════════════════════════════════════════════════════════════════════ */
:root{
  --bg:#000; --hair:#1c1c1c; --hair-2:#121212; --raise:#0a0a0a;
  --ink:#e8e8e4; --dim:#8a8a84; --faint:#5a5a55;
  --amber:#ffb020; --amber-dim:#a8762a;
  --green:#2ecc71; --red:#ff4d4d; --cyan:#4dd0e1; --violet:#c9a0ff;
  --mono:"SF Mono",ui-monospace,SFMono-Regular,Menlo,Consolas,"Liberation Mono",monospace;
}
*{box-sizing:border-box}
html,body{height:100%}
body{margin:0; background:var(--bg); color:var(--ink); font-family:var(--mono);
  font-size:12px; line-height:1.4; font-variant-numeric:tabular-nums;
  -webkit-font-smoothing:antialiased; overflow-x:hidden}
::selection{background:var(--amber); color:#000}
::-webkit-scrollbar{width:9px;height:9px}
::-webkit-scrollbar-track{background:#000}
::-webkit-scrollbar-thumb{background:#242424}
::-webkit-scrollbar-thumb:hover{background:#3a3a3a}

/* ─── STATUS BAR ─── */
.status{position:sticky; top:0; z-index:60; background:#000; border-bottom:1px solid var(--hair);
  display:flex; align-items:center; height:32px; padding:0 12px}
.status .id{color:var(--amber); font-weight:700; letter-spacing:.11em; font-size:12.5px}
.status .sep{color:var(--faint); margin:0 10px}
.status .sub{color:var(--dim); letter-spacing:.04em}
.sp{flex:1}
.led{display:inline-flex; align-items:center; gap:6px; padding:2px 9px; border:1px solid var(--hair);
  letter-spacing:.08em; font-weight:700; font-size:11px}
.led b{width:7px;height:7px;border-radius:50%;display:inline-block}
.led.live{color:var(--green); border-color:#144d2b} .led.live b{background:var(--green); animation:pulse 2s infinite}
.led.stale{color:var(--amber); border-color:#4d3a10} .led.stale b{background:var(--amber)}
.led.down{color:var(--red); border-color:#4d1717} .led.down b{background:var(--red); animation:blink .9s steps(2) infinite}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:.35}}
@keyframes blink{0%{opacity:1}50%{opacity:0}}
.tbtn{background:none; border:1px solid var(--hair); color:var(--dim); font:inherit; font-size:11px;
  padding:2.5px 9px; cursor:pointer; letter-spacing:.06em}
.tbtn:hover{border-color:var(--amber-dim); color:var(--amber)}
.tbtn.on{border-color:var(--amber); color:var(--amber)}

/* ─── v2: freshness chips, NOT LIVE / DEMO states, new modules ─── */
.fr{font-size:10px; letter-spacing:.05em; padding:0 6px; border:1px solid var(--hair); color:var(--faint)}
.fr.ok{color:var(--green); border-color:#144d2b} .fr.warn{color:var(--amber); border-color:#4d3a10}
.fr.bad{color:var(--red); border-color:#4d1717} .fr.off{color:var(--faint)} .fr.aw{color:var(--faint); font-style:italic}
body.notlive .panel .pb{opacity:.28; filter:grayscale(1)}
body.demo .panel{position:relative}
body.demo .panel::after{content:"DEMO"; position:absolute; right:14px; top:36px; font-size:34px; font-weight:700;
  letter-spacing:.3em; color:var(--amber); opacity:.13; pointer-events:none; transform:rotate(-8deg)}
.aw{color:var(--faint); font-style:italic; padding:10px 12px}
.pipe-row{display:flex; gap:10px; padding:8px 10px; border-bottom:1px solid var(--line,#1a1a1a); align-items:stretch}
.pipe-sp{width:48px; color:var(--amber); font-weight:700; letter-spacing:.1em; padding-top:4px}
.pipe-flow{display:flex; flex-wrap:wrap; gap:4px; align-items:stretch; flex:1}
.pipe-tile{border:1px solid; padding:6px 8px; min-width:150px; max-width:230px; flex:1 1 150px; background:#050505}
.pipe-c{font-size:10.5px; letter-spacing:.1em; font-weight:700} .pipe-h{margin:3px 0; font-size:12px}
.pipe-d,.pipe-s{color:var(--faint); font-size:10.5px; word-break:break-word}
.pipe-ar{color:var(--faint); align-self:center}
.pipe-g{margin:0; padding:8px 12px 8px 28px; color:var(--amber)}
.cg{border-collapse:separate; border-spacing:2px; width:auto}
.cg td,.cg th{padding:3px 7px; text-align:center; font-size:10.5px; border:none}
.cg th{color:var(--faint); font-weight:400; position:static; cursor:default}
.cg th.rl{text-align:right}
.cg td.c{min-width:46px; border:1px solid var(--hair); color:#000; font-weight:700}
.cg td.c.recent{outline:2px solid var(--amber); outline-offset:1px}
.cg td.c.s-active{background:var(--green)} .cg td.c.s-shadow{background:var(--cyan)}
.cg td.c.s-blocked{background:var(--amber)} .cg td.c.s-dark{background:#555; color:var(--ink)}
.cg td.c.s-ruled_out{background:var(--red)} .cg td.c.s-not_implemented{background:#141414; color:var(--faint)}
.cg td.c.s-none{background:transparent; border-color:var(--hair-2); color:#222}
.lg{display:flex; gap:12px; flex-wrap:wrap; padding:8px 12px; color:var(--dim); font-size:10.5px}
.lg i{display:inline-block; width:10px; height:10px; margin-right:5px; vertical-align:-1px}

/* ─── MODULE BAR (ERP-style) ─── */
.modbar{position:sticky; top:32px; z-index:55; display:flex; align-items:stretch;
  background:#000; border-bottom:1px solid var(--hair); overflow-x:auto}
.mod{background:none; border:none; border-right:1px solid var(--hair-2); color:var(--dim);
  font:inherit; font-size:11px; letter-spacing:.11em; padding:7px 16px; cursor:pointer;
  white-space:nowrap; position:relative; text-transform:uppercase; font-weight:700}
.mod:hover{color:var(--ink); background:#080808}
.mod.on{color:var(--amber); background:#0c0a04}
.mod.on::after{content:""; position:absolute; left:0; right:0; bottom:-1px; height:2px; background:var(--amber)}
.mod .badge{margin-left:8px; color:var(--faint); font-weight:400; font-size:10px}
.mod.on .badge{color:var(--amber-dim)}
.mod .warn{color:var(--red)}

/* ─── BANNER ─── */
.banner{background:#170505; border-bottom:1px solid #4d1717; color:var(--red);
  padding:7px 12px; letter-spacing:.03em; display:none}
.banner.show{display:block}
.banner .dl{color:var(--dim); margin-left:10px}
.banner.demo{background:#171003; border-color:#4d3a10; color:var(--amber)}

/* ─── METRIC RAIL ─── */
.rail{display:grid; grid-template-columns:repeat(auto-fit,minmax(110px,1fr)); border-bottom:1px solid var(--hair)}
.met{padding:7px 12px; border-right:1px solid var(--hair-2); position:relative; overflow:hidden}
.met:last-child{border-right:none}
.met .k{color:var(--faint); font-size:9.4px; letter-spacing:.12em; text-transform:uppercase}
.met .v{font-size:16.5px; font-weight:700; letter-spacing:-.01em; margin-top:2px; white-space:nowrap}
.met .d{font-size:10px; color:var(--faint); margin-top:1px; white-space:nowrap; height:13px}
.pos{color:var(--green)} .neg{color:var(--red)} .amb{color:var(--amber)} .cy{color:var(--cyan)}
.vi{color:var(--violet)}
.met.flash::after{content:""; position:absolute; inset:0; background:var(--amber); opacity:.16;
  animation:fade .9s ease-out forwards; pointer-events:none}
@keyframes fade{to{opacity:0}}

/* ─── LAYOUT ─── */
.grid{display:grid; gap:0}
.g-7-5{grid-template-columns:minmax(0,7fr) minmax(0,5fr)}
.g-1{grid-template-columns:minmax(0,1fr)}
.g-2{grid-template-columns:repeat(2,minmax(0,1fr))}
@media(max-width:1180px){.g-7-5,.g-2{grid-template-columns:1fr}}
.col{min-width:0; border-right:1px solid var(--hair)}
.col:last-child{border-right:none}
.panel{border-bottom:1px solid var(--hair); min-width:0}
.ph{display:flex; align-items:center; gap:9px; padding:6px 12px;
  border-bottom:1px solid var(--hair-2); background:var(--raise); flex-wrap:wrap}
.ph .t{color:var(--amber); letter-spacing:.14em; font-size:10.5px; font-weight:700; text-transform:uppercase}
.ph .n{color:var(--faint); font-size:10.5px}
.pb{padding:10px 12px} .pb.flush{padding:0}

/* ─── TABLES ─── */
table{width:100%; border-collapse:collapse; font-size:11.4px}
thead th{position:sticky; top:0; background:#000; z-index:2; text-align:left; color:var(--faint);
  font-weight:400; letter-spacing:.1em; font-size:9.4px; text-transform:uppercase; padding:5px 8px;
  border-bottom:1px solid var(--hair); white-space:nowrap; cursor:pointer; user-select:none}
thead th:hover{color:var(--amber)}
thead th.na{cursor:default} thead th.na:hover{color:var(--faint)}
thead th .ar{color:var(--amber); font-size:8px}
tbody td{padding:4px 8px; border-bottom:1px solid var(--hair-2); white-space:nowrap}
tbody tr:hover td{background:#0c0c0c}
td.r{text-align:right} td.dim{color:var(--dim)}
.scroll{overflow:auto; max-height:var(--h,300px)}
tr.new td{animation:rowflash 1.6s ease-out}
@keyframes rowflash{0%{background:#3a2a06}100%{background:transparent}}

.tag{display:inline-block; border:1px solid var(--hair); padding:0 5px; font-size:9.6px;
  letter-spacing:.09em; color:var(--dim); font-weight:700}
.tag.t1{color:var(--cyan); border-color:#17414a}
.tag.t4{color:var(--amber); border-color:#4d3a10}
.tag.nfl{color:var(--violet); border-color:#33224d}
.tag.stub{color:var(--red); border-color:#4d1717; background:#150404}
.tag.real{color:var(--green); border-color:#144d2b}
.tag.unk{color:var(--faint)}
.dir{font-weight:700; font-size:10px; letter-spacing:.06em}
.dir.y{color:var(--green)} .dir.n{color:var(--red)}
.sev{font-size:9.6px; letter-spacing:.08em; font-weight:700}
.sev.WARNING{color:var(--amber)} .sev.ERROR,.sev.CRITICAL{color:var(--red)} .sev.INFO{color:var(--dim)}

/* ─── TAPE ─── */
.tl{display:grid; grid-template-columns:62px 34px 1fr; gap:8px; padding:3px 12px;
  border-bottom:1px solid var(--hair-2)}
.tl:hover{background:#0c0c0c}
.tl.new{animation:rowflash 1.6s ease-out}
.tl .ts{color:var(--faint); font-size:10.2px}
.tl .bd{font-size:9.6px; letter-spacing:.06em; font-weight:700}
.tl .msg{overflow:hidden; text-overflow:ellipsis}
.tl .msg em{color:var(--dim); font-style:normal}

/* ─── CHARTS ─── */
svg{display:block; width:100%; overflow:visible}
.ax{stroke:var(--hair); stroke-width:1}
.axl{fill:var(--faint); font-size:10px; font-family:var(--mono)}
.axl.sm{font-size:9px}
.ident{stroke:var(--amber-dim); stroke-width:1; stroke-dasharray:3 3}
.vigband{fill:var(--amber); opacity:.07}
.pt{stroke-width:1.2}
.legend{display:flex; gap:14px; font-size:10px; color:var(--dim); padding:6px 12px 0; flex-wrap:wrap}
.legend span{display:inline-flex; align-items:center; gap:5px}
.sw{width:9px;height:9px;display:inline-block;border-radius:50%}

/* ─── LANES / HEALTH ─── */
.lane{display:grid; grid-template-columns:46px 1fr 62px 66px; gap:8px; align-items:center;
  padding:6px 12px; border-bottom:1px solid var(--hair-2)}
.lane .bar{height:5px; background:#141414; position:relative}
.lane .bar i{position:absolute; left:0; top:0; bottom:0; display:block}
.lane .nn{text-align:right; font-size:11px}
.sublane{padding:0 12px 7px 66px; color:var(--dim); font-size:10px; border-bottom:1px solid var(--hair-2)}
.hw{display:grid; grid-template-columns:1fr auto auto; gap:10px; align-items:center;
  padding:5px 12px; border-bottom:1px solid var(--hair-2); font-size:11px}
.hw .lbl{color:var(--dim)}
.age.ok{color:var(--green)} .age.warn{color:var(--amber)} .age.bad{color:var(--red)}
.hw .dot{width:6px;height:6px;border-radius:50%;background:var(--faint)}
.hw .dot.ok{background:var(--green)} .hw .dot.warn{background:var(--amber)} .hw .dot.bad{background:var(--red)}

.note{border-left:2px solid var(--amber); background:#100c02; padding:8px 12px;
  color:var(--dim); font-size:11px; line-height:1.55; margin:10px 12px}
.note.bad{border-color:var(--red); background:#120404}
.note b{color:var(--ink); font-weight:400}
.note .hl{color:var(--red); font-weight:700}
.empty{color:var(--faint); padding:16px 12px; font-style:italic; font-size:11px}
.tt{position:fixed; z-index:200; pointer-events:none; opacity:0; background:#0a0a0a;
  border:1px solid var(--hair); padding:7px 10px; font-size:10.8px; color:var(--ink);
  max-width:320px; transition:opacity .08s; box-shadow:0 6px 24px rgba(0,0,0,.9)}
.tt .h{color:var(--amber); font-weight:700; margin-bottom:3px; letter-spacing:.06em}
.tt .r{display:flex; justify-content:space-between; gap:14px; color:var(--dim)}
.tt .r b{color:var(--ink); font-weight:400}
.filt{background:#000; border:1px solid var(--hair); color:var(--ink); font:inherit; font-size:11px;
  padding:2px 8px; width:150px; outline:none}
.filt:focus{border-color:var(--amber-dim)}
.filt::placeholder{color:var(--faint)}
.kv{display:grid; grid-template-columns:auto 1fr; gap:3px 14px; font-size:11px; padding:2px 0}
.kv dt{color:var(--faint)} .kv dd{margin:0}
/* ─── NOW: top strip + decision stream (W56.2) ─── */
.strip{display:grid; grid-template-columns:repeat(auto-fit,minmax(190px,1fr)); border-bottom:1px solid var(--hair); background:var(--raise)}
.sb{padding:9px 14px; border-right:1px solid var(--hair-2); min-width:0}
.sb:last-child{border-right:none}
.sb .k{color:var(--faint); font-size:9.4px; letter-spacing:.12em; text-transform:uppercase}
.sb .v{font-size:20px; font-weight:700; margin-top:2px; white-space:nowrap}
.sb .s{color:var(--dim); font-size:10.2px; margin-top:2px}
.sb .src{color:var(--faint); font-size:9.4px; margin-top:1px}
.ddbar{height:4px; background:#141414; margin-top:5px; position:relative}
.ddbar i{display:block; height:100%; background:var(--faint)}
.ddbar.warn i{background:var(--amber)} .ddbar.bad i{background:var(--red)}
.arms{display:flex; flex-wrap:wrap; gap:6px; padding:8px 14px; border-bottom:1px solid var(--hair)}
.arm{border:1px solid var(--hair); padding:2px 8px; font-size:10.5px; color:var(--dim)}
.arm b{font-weight:400; margin-left:6px}
.arm.fresh{border-color:#144d2b} .arm.fresh b{color:var(--green)}
.arm.old b{color:var(--amber)} .arm.old{border-color:#4d3a10}
tr.stale td{opacity:.5}
.wf{font-weight:700}
.stk{color:var(--faint)}
td.tk{max-width:300px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap}
@media(max-width:700px){.sb .v{font-size:17px} td.tk{max-width:150px}}
footer{padding:9px 12px; color:var(--faint); font-size:10.2px; border-top:1px solid var(--hair)}
</style>
</head>
<body>
<div class="tt" id="tt"></div>

<div class="status">
  <span class="id">PMBOT</span><span class="sep">│</span>
  <span class="sub">PAPER · DEMO VENUE · <span class="amb">NO REAL CAPITAL</span></span>
  <span class="sep">│</span><span class="sub">EPOCH <b id="epoch" class="cy">—</b></span>
  <span class="sep">│</span><span class="sub">RUN <b id="sha" class="cy" title="commit the running process loaded">—</b></span>
  <span class="sub"> · ORIGIN <b id="osha" class="cy" title="origin/main as of the last fetch on the server">—</b> <b id="obehind"></b></span>
  <span class="sep">│</span><span class="sub">T4 <b id="cyc" title="T4 cycle-log rate over the bounded tail">—</b></span>
  <span class="sp"></span>
  <span class="sub"><a href="/project" style="color:var(--amber)" title="analytical project-state page">PROJECT STATE →</a></span>
  <span class="sub" id="clock">--:--:--Z</span><span class="sep">│</span>
  <span class="led down" id="led"><b></b><span id="ledtxt">INIT</span></span><span class="sep">│</span>
  <button class="tbtn" id="pause" title="space">⏸ PAUSE</button>
  <button class="tbtn" id="refresh" title="r">⟳ <span id="cd">--</span>s</button>
</div>

<div class="modbar" id="modbar"></div>
<div class="banner" id="banner"></div>
<div class="rail" id="rail"></div>
<div id="work"></div>
<footer id="foot">—</footer>

<script>
"use strict";
/* ══════════════════════════════════════════════════════════════════════
   CONTRACT — /api/data exactly as scripts/web_dashboard.py emits it.
   portfolio | t4_portfolio | nfl_portfolio → {bankroll_usd,
     initial_bankroll_usd, total_realized_pnl, current_daily_loss,
     daily_net_pnl, open_positions[], closed_positions[], last_updated}
   position → {position_id, player_name, kalshi_ticker, kalshi_threshold,
     direction, size_usd, model_p, mid_price_at_entry, gross_edge,
     vig_at_entry, entered_at, status, outcome, pnl, actual_pts,
     resolved_at, game_date, model_identity, logic_epoch, ...}
   audit | t4_audit | nfl_audit → {timestamp, event_id, component,
     event_type, severity, payload{}}
   pipe_mtimes{label:isoZ} · server_time · current_logic_epoch
   nfl_model_provenance
   rejected_counts{mlb,mlb_t4,nfl → int|null}  (counts only; arrays never sent)
   t4_cycle_tail[{ts,cycle_id,session_id,ticker,...}]  (bounded, oldest→newest)
   process{started_at:isoZ, sha:40-hex|"unknown"}  (sha = code the process loaded)
   ══════════════════════════════════════════════════════════════════════ */

const REFRESH_S=30;
const $=s=>document.querySelector(s), $$=s=>[...document.querySelectorAll(s)];
const esc=s=>String(s??'').replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const num=(v,d=2)=>(v==null||v===''||isNaN(v))?'—':Number(v).toFixed(d);
const usd=v=>(v==null||isNaN(v))?'—':(v<0?'-':'')+'$'+Math.abs(Number(v)).toFixed(2);
const sgn=v=>(v==null||isNaN(v))?'':(v>0?'pos':v<0?'neg':'');
const toArr=a=>Array.isArray(a)?a:[];
const hhmm=t=>{const d=new Date(t);return isNaN(d)?'—':d.toISOString().slice(11,19)};
const mmdd=t=>{const d=new Date(t);return isNaN(d)?'—':d.toISOString().slice(5,16).replace('T',' ')};
const clip=(s,n)=>{s=String(s); if(s.length<=n)return s; const c=s.slice(0,n),i=c.lastIndexOf(' ');
  return (i>n*0.6?c.slice(0,i):c)+'…'};

/* model_identity classification — the difference between a row and evidence */
function evClass(p){
  const m=p.model_identity;
  if(m==null||m===''||m==='UNKNOWN') return 'UNATTRIBUTED';
  if(/stub/i.test(m)) return 'STUB';
  return 'MODEL';
}
const EVTAG={MODEL:['real','REAL'],STUB:['stub','STUB'],UNATTRIBUTED:['unk','UNATTR']};

const DEMO_FLAG=/[?&]demo(=|&|$)/.test(location.search);
let LASTPULL=0;
const EMPTY={portfolio:{},t4_portfolio:{},nfl_portfolio:{},audit:[],t4_audit:[],nfl_audit:[],pipe_log:[],
  pipe_mtimes:{},t4_cycle_tail:[],server_time:null};
let S={data:null, mod:'NOW', wfOnly:false, paused:false, cd:REFRESH_S, band:'ALL', filt:'',
       seenPos:new Set(), seenEvt:new Set(), first:true, lastOk:0, demo:false, notlive:false,
       sortKey:'entered_at', sortDir:-1};

const tt=$('#tt');
function tip(e,h){tt.innerHTML=h; tt.style.opacity='1';
  const r=tt.getBoundingClientRect(); let x=e.clientX+14,y=e.clientY+14;
  if(x+r.width>innerWidth-10)x=e.clientX-r.width-14;
  if(y+r.height>innerHeight-10)y=e.clientY-r.height-14;
  tt.style.left=x+'px'; tt.style.top=y+'px'}
function untip(){tt.style.opacity='0'}
function wireTips(root){ (root||document).querySelectorAll('[data-tip]').forEach(n=>{
  n.addEventListener('mousemove',e=>tip(e,decodeURIComponent(n.dataset.tip)));
  n.addEventListener('mouseleave',untip)}) }

/* ═══════════ FETCH ═══════════ */
async function pull(){
  try{
    if(DEMO_FLAG){ S.demo=true; S.notlive=false; banner('demo','DEMO — seed data shown because ?demo is set. Nothing on this page is live.'); apply(DEMO); S.first=false; return }
    const r=await fetch('/api/data',{cache:'no-store'});
    if(!r.ok) throw new Error('HTTP '+r.status+' from /api/data');
    const j=await r.json(); if(j.error) throw new Error(j.error);
    S.demo=false; S.notlive=false; S.lastOk=Date.now(); LASTPULL=Date.now(); banner(false); apply(j);
  }catch(err){
    if(!S.lastOk){ S.demo=false; S.notlive=true;
      banner('err','NOT LIVE — no data from /api/data ('+err.message+'). Panels are blank. Open the tunnel (Open Dashboard.command); add ?demo to preview layout with seed data.');
      apply(EMPTY);
    } else if(Date.now()-S.lastOk > 2*REFRESH_S*1000){
      /* Source gone for >2 refresh cycles: last-good numbers are no longer "read from a live
         source". Blank every panel, exactly as at first load, instead of freezing on old figures. */
      S.notlive=true; apply(EMPTY);
      banner('err','NOT LIVE — /api/data unreachable ('+err.message+'). Panels blanked; last good data was '+Math.round((Date.now()-S.lastOk)/1000)+'s ago. Check the SSH tunnel / service.');
      led('down','NOT LIVE');
    } else {
      banner('err','Cannot fetch /api/data — '+err.message+'. Check the SSH tunnel is open. Retrying in '+REFRESH_S+'s…');
      led('down','NO DATA');
    }
  }
  S.first=false;
}
function banner(k,msg){const b=$('#banner');
  if(!k){b.className='banner'; b.textContent=''; return}
  b.className='banner show'+(k==='demo'?' demo':'');
  b.innerHTML=esc(msg)+(k==='err'?`<span class="dl">last good data ${S.lastOk?Math.round((Date.now()-S.lastOk)/1000)+'s ago':'never this session'}</span>`:'')}
function led(k,t){$('#led').className='led '+k; $('#ledtxt').textContent=t}

/* ═══════════ DERIVE ═══════════ */
function derive(d){
  const P=d.portfolio||{}, T4=d.t4_portfolio||{}, NF=d.nfl_portfolio||{};
  const tag=(a,b,s)=>toArr(a).map(p=>({...p,_band:b,_sport:s}));
  return {P,T4,NF,
    open:[...tag(P.open_positions,'T1','MLB'),...tag(T4.open_positions,'T4','MLB'),...tag(NF.open_positions,'NFL','NFL')],
    closed:[...tag(P.closed_positions,'T1','MLB'),...tag(T4.closed_positions,'T4','MLB'),...tag(NF.closed_positions,'NFL','NFL')],
    events:[...tag(d.audit,'T1','MLB'),...tag(d.t4_audit,'T4','MLB'),...tag(d.nfl_audit,'NFL','NFL')]
      .filter(e=>e&&e.timestamp).sort((a,b)=>String(b.timestamp).localeCompare(String(a.timestamp)))};
}

/* ═══════════ MODULES ═══════════ */
const MODULES=[
  {k:'NOW',      label:'Now'},
  {k:'OVERVIEW', label:'Overview'},
  {k:'MLB',      label:'MLB · T1/T4'},
  {k:'NFL',      label:'NFL · T1'},
  {k:'EVIDENCE', label:'Evidence'},
  {k:'PIPELINE', label:'Pipeline C1–C8'},
  {k:'FEEDS',    label:'Feeds & Health'},
  {k:'COVERAGE', label:'Coverage'},
  {k:'SHADOW',   label:'Shadow'},
  {k:'POSTSEASON',label:'MLB Postseason'},
  {k:'VERDICTS', label:'Verdicts'},
];
function modbar(D){
  const stub=D.open.concat(D.closed).filter(p=>evClass(p)==='STUB').length;
  const errs=D.events.filter(e=>e.severity==='ERROR'||e.severity==='CRITICAL').length;
  const NL=S.notlive;   /* NOT LIVE: assert nothing — no counts, no 'clean'/'ok' */
  const badge=NL?{OVERVIEW:'—',NOW:'—',MLB:'—',NFL:'—',EVIDENCE:'—',FEEDS:'—',PIPELINE:'awaiting',COVERAGE:'awaiting',SHADOW:'awaiting',POSTSEASON:'',VERDICTS:''}:{
    NOW: LAST&&LAST.decisions&&(LAST.decisions.rows||[]).length?`${LAST.decisions.rows.length} evals`:'awaiting',
    OVERVIEW:`${D.open.length} open`,
    MLB:`${D.open.filter(p=>p._sport==='MLB').length} open`,
    NFL:`${D.open.filter(p=>p._sport==='NFL').length} open`,
    EVIDENCE: stub? `<span class="warn">${stub} stub</span>` : 'clean',
    FEEDS: errs? `<span class="warn">${errs} err</span>` : 'ok',
    PIPELINE: LAST&&LAST.pipeline&&LAST.pipeline.tiles&&LAST.pipeline.tiles.length?(LAST.pipeline.gaps.length?`<span class="warn">${LAST.pipeline.gaps.length} gaps</span>`:'wired'):'awaiting',
    COVERAGE: LAST&&LAST.coverage&&LAST.coverage.total?`${LAST.coverage.total} cells`:'awaiting',
    SHADOW: LAST&&LAST.shadow&&LAST.shadow.cells&&LAST.shadow.cells.length?`${LAST.shadow.cells.length} cells`:'awaiting',
    POSTSEASON: '', VERDICTS: '',
  };
  $('#modbar').innerHTML=MODULES.map(m=>
    `<button class="mod ${S.mod===m.k?'on':''}" data-m="${m.k}">${esc(m.label)}<span class="badge">${badge[m.k]||''}</span></button>`).join('');
  $$('.mod').forEach(b=>b.addEventListener('click',()=>{S.mod=b.dataset.m; S.filt=''; render()}));
}

/* ═══════════ APPLY / RENDER ═══════════ */
let LAST=null;
function apply(d){ LAST=d; render(); }
function render(){
  const d=LAST; if(!d) return;
  const D=derive(d);
  $('#epoch').textContent=d.current_logic_epoch??'—';
  modbar(D);
  rail(D,d);
  const w=$('#work');
  if(S.mod==='NOW') w.innerHTML=viewNow();
  else if(S.mod==='OVERVIEW') w.innerHTML=viewOverview();
  else if(S.mod==='MLB') w.innerHTML=viewSport('MLB');
  else if(S.mod==='NFL') w.innerHTML=viewSport('NFL');
  else if(S.mod==='EVIDENCE') w.innerHTML=viewEvidence();
  else if(S.mod==='COVERAGE') w.innerHTML=viewCoverage();
  else if(S.mod==='SHADOW') w.innerHTML=viewShadow();
  else if(S.mod==='POSTSEASON') w.innerHTML=viewPost();
  else if(S.mod==='VERDICTS') w.innerHTML=viewVerdicts();
  else if(S.mod==='PIPELINE') w.innerHTML=viewPipeline();
  else w.innerHTML=viewFeeds();
  fill(D,d);
  fillV2(d);
  fillNow(d);
  paintFresh();
  document.body.classList.toggle('notlive',!!S.notlive);
  document.body.classList.toggle('demo',!!S.demo);

  const lw=Math.max(...[D.P.last_updated,D.T4.last_updated,D.NF.last_updated]
    .map(t=>t?new Date(t).getTime():0),0);
  const age=lw?Math.round((Date.now()-lw)/1000):null;
  if(S.notlive) led('down','NOT LIVE');
  else if(S.demo) led('stale','DEMO');
  else if(age!=null&&age>3600) led('stale','DATA '+fmtAge(age));
  else led('live','LIVE');
  statusExtras(d);
  $('#foot').textContent=`server ${d.server_time||'—'} · epoch ${d.current_logic_epoch??'—'} · `+
    `${D.open.length} open / ${D.closed.length} closed / ${D.events.length} events in window · `+
    `NFL model ${d.nfl_model_provenance||'—'}`+rejFoot(d);
}

/* T-600/D2 — running sha + T4 cycle-rate readout. Both degrade to "—" when the
   server predates the keys (older dashboard) so the page never throws on them. */
function cycleRate(tail){
  if(!Array.isArray(tail)||!tail.length) return null;
  const ts=tail.map(r=>Date.parse(r&&r.ts)).filter(Number.isFinite);
  if(!ts.length) return null;
  const cycles=new Set(tail.map(r=>r&&r.cycle_id).filter(Boolean)).size;
  const lo=Math.min(...ts), hi=Math.max(...ts), spanMin=(hi-lo)/60000;
  return {cycles, rows:tail.length, perMin:spanMin>0?cycles/spanMin:null,
          ageS:Math.round((Date.now()-hi)/1000)};
}
function statusExtras(d){
  const pr=d.process||{}, sha=typeof pr.sha==='string'?pr.sha:'';
  const se=$('#sha');
  if(se){ se.textContent=sha&&sha!=='unknown'?sha.slice(0,7):'unknown';
    se.title='running commit '+(sha||'unknown')+(pr.started_at?' · started '+pr.started_at:''); }
  const og=d.origin||{}, oe=$('#osha'), ob=$('#obehind');
  if(oe){ oe.textContent=og.origin_sha?og.origin_sha.slice(0,7):'awaiting';
    oe.title='origin/main'+(og.ref_as_of?' · ref fetched '+og.ref_as_of:' · fetch time unknown'); }
  if(ob){ const n=og.commits_behind;
    ob.textContent=n==null?'':(n===0?'= in sync':n+' behind'); ob.className=n==null?'':n===0?'pos':'amb'; }
  const ce=$('#cyc'), r=cycleRate(d.t4_cycle_tail);
  if(ce){ ce.textContent=r?((r.perMin!=null?r.perMin.toFixed(1)+' cyc/min':r.cycles+' cyc')+' · last '+fmtAge(r.ageS)):'—'; }
}
function rejFoot(d){
  const c=d.rejected_counts; if(!c||typeof c!=='object') return '';
  return ' · rejected '+Object.entries(c).map(([k,v])=>k+' '+(v==null?'?':v)).join(' / ');
}

/* ═══════════ METRIC RAIL (per module) ═══════════ */
let PREVM=null, PREVKEY=null;
function ddOf(P){return(P&&P.initial_bankroll_usd&&P.total_realized_pnl!=null)?Math.max(0,-P.total_realized_pnl)/P.initial_bankroll_usd:null}
function railSpec(D,d){
  const sum=(a,f)=>a.reduce((s,x)=>s+(Number(f(x))||0),0);
  if(S.mod==='NOW'){ const x=d.decisions||{}, rows=x.rows||[];
    if(!rows.length) return [['DECISIONS','awaiting',null,'']];
    const day=new Date().toISOString().slice(0,10);
    const today=(x.arms||[]).reduce((n,a)=>n+(a.rows_today||0),0);
    const wf=rows.filter(r=>r.would_fire).length;
    return [['IN STREAM',String(rows.length),rows.length,''],
      ['WOULD-FIRE',String(wf),wf,''],['ARMS',String((x.arms||[]).length),(x.arms||[]).length,'']]; }
  if(S.mod==='COVERAGE'){ const c=d.coverage||{}, k=c.counts||{};
    if(!c.total) return [['COVERAGE','awaiting',null,'']];
    return [['CELLS',String(c.total),c.total,''],['ACTIVE',String(k.active||0),k.active||0,''],
      ['SHADOW',String(k.shadow||0),k.shadow||0,'cy'],['BLOCKED',String(k.blocked||0),k.blocked||0,'warnv'],
      ['DARK',String(k.dark||0),k.dark||0,''],['RULED OUT',String(k.ruled_out||0),k.ruled_out||0,''],
      ['NOT IMPL.',String(k.not_implemented||0),k.not_implemented||0,'']]; }
  if(S.mod==='SHADOW'){ const sh=d.shadow||{}, cs=sh.cells||[];
    if(!cs.length) return [['SHADOW','awaiting',null,'']];
    return [['CELLS',String(cs.length),cs.length,''],['ROWS TODAY',String(sum(cs,c=>c.rows_today)),sum(cs,c=>c.rows_today),'cy']]; }
  if(S.mod==='POSTSEASON'){ const m=d.mlb_postseason||{};
    return [['T1 MATCHED',m.t1_players_matched_last_run==null?'awaiting':String(m.t1_players_matched_last_run),m.t1_players_matched_last_run,''],
      ['T4 CYCLE AGE',m.t4_cycle_age_s==null?'awaiting':fmtAge(Math.round(m.t4_cycle_age_s)),m.t4_cycle_age_s,''],
      ['OPEN',m.open_positions==null?'awaiting':String(m.open_positions),m.open_positions,''],
      ['STUCK',m.stuck_positions==null?'awaiting':String(m.stuck_positions),m.stuck_positions,m.stuck_positions>0?'bad':'']]; }
  if(S.mod==='PIPELINE'){ const p=d.pipeline||{}, t=p.tiles||[];
    if(!t.length) return [['PIPELINE','awaiting',null,'']];
    const n=st=>t.filter(x=>x.status===st).length;
    return [['TILES',String(t.length),t.length,''],['OK',String(n('ok')),n('ok'),''],['WARN',String(n('warn')),n('warn'),'warnv'],
      ['BAD',String(n('bad')),n('bad'),n('bad')>0?'bad':''],['NOT INSTR.',String(n('ni')),n('ni'),n('ni')>0?'warnv':'']]; }
  if(S.mod==='VERDICTS') return [['VERDICTS',String(Object.keys(d.verdicts||{}).length),null,'']];
  if(S.mod==='NFL'){
    const o=D.open.filter(p=>p._sport==='NFL'), c=D.closed.filter(p=>p._sport==='NFL');
    const all=[...o,...c];
    const stub=all.filter(p=>evClass(p)==='STUB').length;
    const real=all.filter(p=>evClass(p)==='MODEL').length;
    const un=all.filter(p=>evClass(p)==='UNATTRIBUTED').length;
    const res=c.filter(p=>p.outcome==='WIN'||p.outcome==='LOSS');
    return [['BANKROLL',usd(D.NF.bankroll_usd),D.NF.bankroll_usd,''],
      ['REALISED P&L',usd(D.NF.total_realized_pnl),D.NF.total_realized_pnl,'sign'],
      ['OPEN',String(o.length),o.length,''],
      ['EXPOSURE',usd(sum(o,p=>p.size_usd)),sum(o,p=>p.size_usd),''],
      ['ROWS TOTAL',String(all.length),all.length,''],
      ['REAL MODEL',String(real),real,'cy'],
      ['STUB ROWS',String(stub),stub,'bad'],
      ['UNATTRIBUTED',String(un),un,'warnv'],
      ['SETTLED',String(res.length),res.length,''],
      ['LAST WRITE',D.NF.last_updated?fmtAge(Math.round((Date.now()-new Date(D.NF.last_updated))/1000)):'—',null,'']];
  }
  if(S.mod==='MLB'){
    const o=D.open.filter(p=>p._sport==='MLB'), c=D.closed.filter(p=>p._sport==='MLB');
    const res=c.filter(p=>p.outcome==='WIN'||p.outcome==='LOSS');
    const w=res.filter(p=>p.outcome==='WIN').length;
    return [['BANKROLL T1',usd(D.P.bankroll_usd),D.P.bankroll_usd,''],
      ['T1 P&L',usd(D.P.total_realized_pnl),D.P.total_realized_pnl,'sign'],
      ['T4 P&L',usd(D.T4.total_realized_pnl),D.T4.total_realized_pnl,'sign'],
      ['DAILY P&L',usd((Number(D.P.daily_net_pnl)||0)+(Number(D.T4.daily_net_pnl)||0)),
        (Number(D.P.daily_net_pnl)||0)+(Number(D.T4.daily_net_pnl)||0),'sign'],
      ['OPEN T1',String(o.filter(p=>p._band==='T1').length),o.filter(p=>p._band==='T1').length,''],
      ['OPEN T4',String(o.filter(p=>p._band==='T4').length),o.filter(p=>p._band==='T4').length,''],
      ['EXPOSURE',usd(sum(o,p=>p.size_usd)),sum(o,p=>p.size_usd),''],
      ['W / L',`${w}/${res.length-w}`,w,''],
      ['WIN RATE',res.length?(w/res.length*100).toFixed(1)+'%':'—',res.length?w/res.length:null,''],
      ['SETTLED',String(res.length),res.length,'']];
  }
  // OVERVIEW / EVIDENCE / FEEDS
  const cum=[D.P,D.T4,D.NF].reduce((s,x)=>s+(Number(x.total_realized_pnl)||0),0);
  const daily=[D.P,D.T4,D.NF].reduce((s,x)=>s+(Number(x.daily_net_pnl)||0),0);
  const dd=(D.P.initial_bankroll_usd&&D.P.total_realized_pnl!=null)?Math.max(0,-D.P.total_realized_pnl)/D.P.initial_bankroll_usd:null;
  const frozenT1=D.P.last_updated&&(Date.now()-new Date(D.P.last_updated))>72*3600*1000?' FROZEN '+String(D.P.last_updated).slice(0,10)+' ('+Math.floor((Date.now()-new Date(D.P.last_updated))/86400000)+'d ago)':'';
  const res=D.closed.filter(p=>p.outcome==='WIN'||p.outcome==='LOSS');
  const w=res.filter(p=>p.outcome==='WIN').length;
  const stub=D.open.concat(D.closed).filter(p=>evClass(p)==='STUB').length;
  return [['BANKROLL T1',usd(D.P.bankroll_usd),D.P.bankroll_usd,''],
    ['CUM P&L',usd(cum),cum,'sign'],
    ['DRAWDOWN T1 (REALIZED)',dd==null?'—':(dd*100).toFixed(2)+'%'+frozenT1,dd,'inv'],
    ['DRAWDOWN T4M-PROJ (REALIZED)',ddOf(D.T4)==null?'—':(ddOf(D.T4)*100).toFixed(2)+'%',ddOf(D.T4),'inv'],
    ['DAILY P&L',usd(daily),daily,'sign'],
    ['OPEN',String(D.open.length),D.open.length,''],
    ['EXPOSURE',usd(sum(D.open,p=>p.size_usd)),sum(D.open,p=>p.size_usd),''],
    ['W / L',`${w}/${res.length-w}`,w,''],
    ['WIN RATE',res.length?(w/res.length*100).toFixed(1)+'%':'—',res.length?w/res.length:null,''],
    ['STUB ROWS',String(stub),stub,stub?'bad':''],
    ['T1 P&L',usd(D.P.total_realized_pnl),D.P.total_realized_pnl,'sign'],
    ['T4 P&L',usd(D.T4.total_realized_pnl),D.T4.total_realized_pnl,'sign'],
    ['NFL P&L',usd(D.NF.total_realized_pnl),D.NF.total_realized_pnl,'sign']];
}
function rail(D,d){
  const spec=railSpec(D,d);
  const host=$('#rail');
  const cls=m=>m==='sign'?'':m==='inv'?'':m==='bad'?'neg':m==='cy'?'cy':m==='warnv'?'amb':'';
  host.innerHTML=spec.map(([k,txt,v,mode],i)=>{
    let c=mode==='sign'?sgn(v):mode==='inv'?(v>=0.2?'neg':v>=0.16?'amb':''):cls(mode);
    const pv=(PREVKEY===S.mod&&PREVM)?PREVM[i]?.[2]:null;
    let delta='';
    if(pv!=null&&v!=null&&!isNaN(v)&&!isNaN(pv)&&v!==pv){
      const dv=v-pv;
      delta=`<span class="${dv>0?'pos':'neg'}">${dv>0?'▲':'▼'} ${Math.abs(dv)>=1?Math.abs(dv).toFixed(2):Math.abs(dv).toFixed(3)}</span>`;
    }
    return `<div class="met" data-i="${i}"><div class="k">${esc(k)}</div>`+
      `<div class="v ${c}">${txt}</div><div class="d">${delta}</div></div>`;
  }).join('');
  if(PREVKEY===S.mod&&PREVM) spec.forEach(([,,v],i)=>{ if(PREVM[i]&&v!==PREVM[i][2]){
    const n=host.querySelector(`.met[data-i="${i}"]`); if(n){n.classList.remove('flash'); void n.offsetWidth; n.classList.add('flash')} }});
  PREVM=spec; PREVKEY=S.mod;
}

/* ═══════════ VIEW SHELLS ═══════════ */
const P_=(t,n,body,extra='',fr='')=>`<div class="panel"><div class="ph"><span class="t">${t}</span>`+
  `<span class="n" id="${n}">—</span><span class="sp"></span>${extra}`+
  (fr?`<span class="fr" data-fr="${fr}">…</span>`:'')+`</div>${body}</div>`;
const frKey=()=>S.mod==='NFL'?'nfl':'t1_mlb';
const SCROLL=(id,h)=>`<div class="pb flush"><div class="scroll" style="--h:${h}px" id="${id}"></div></div>`;

function viewNow(){return `<div id="strip" class="strip"></div><div id="arms" class="arms"></div><div class="grid g-1">
  ${P_('Decision stream','dsN',SCROLL('dsWrap',640),`<span class="n" id="dsRule"></span><button class="tbtn" id="wfBtn">WOULD-FIRE ONLY</button>`)}</div>`;}
function viewOverview(){return `<div class="grid g-7-5">
  <div class="col">
    ${P_('Model vs Market','scatN',`<div class="pb"><div id="scatter"></div>${LEGEND}</div>`,
      `<span class="n">off-diagonal = edge · above the line = model says cheaper than market</span>`,'t1_mlb')}
    ${P_('Open Positions','openN',SCROLL('posWrap',300),FILTERBAR,'t1_mlb')}
    ${P_('Recently Resolved','resN',SCROLL('resWrap',220),`<span class="n" id="resPnl"></span>`)}
  </div>
  <div class="col">
    ${P_('Live Tape','tapeN',SCROLL('tape',318),`<span class="n">newest first · flashes on arrival</span>`,'audit_mlb')}
    ${P_('Edge Ladder','ladN',`<div class="pb"><div id="ladder"></div></div>`)}
    ${P_('Band Lanes','lanesN',`<div class="pb flush"><div id="lanes"></div></div>`)}
    ${P_('Alerts','alertN',SCROLL('alerts',190),`<span class="n">deduped, most recent first</span>`)}
  </div></div>`;}

function viewSport(sport){
  const nflNote = sport==='NFL' ? `<div id="nflNote"></div>` : '';
  return `${nflNote}<div class="grid g-7-5">
  <div class="col">
    ${P_(sport+' — Model vs Market','scatN',`<div class="pb"><div id="scatter"></div>${LEGEND}</div>`)}
    ${P_(sport+' — Open Positions','openN',SCROLL('posWrap',320),`<input class="filt" id="posFilt" placeholder="filter…  /">`,sport==='NFL'?'nfl':'t1_mlb')}
    ${P_(sport+' — Recently Resolved','resN',SCROLL('resWrap',230),`<span class="n" id="resPnl"></span>`)}
  </div>
  <div class="col">
    ${P_(sport+' — Live Tape','tapeN',SCROLL('tape',330),`<span class="n">this sport only</span>`)}
    ${P_(sport+' — Edge Ladder','ladN',`<div class="pb"><div id="ladder"></div></div>`)}
    ${P_(sport+' — Alerts','alertN',SCROLL('alerts',210))}
    ${P_(sport+' — Pool',`poolN`,`<div class="pb"><div id="poolKv"></div></div>`)}
  </div></div>`;}

function viewEvidence(){return `<div class="grid g-2">
  <div class="col">
    ${P_('Evidence Class — every row in every pool','evN',`<div class="pb flush"><div id="evTable"></div></div>`,
      `<span class="n">model_identity decides whether a row can ever count</span>`)}
    ${P_('Band Lanes — clean vs raw','lanesN',`<div class="pb flush"><div id="lanes"></div></div>`)}
  </div>
  <div class="col">
    ${P_('Rows by model_identity','miN',`<div class="pb flush"><div id="miTable"></div></div>`)}
    ${P_('What this means','evNote',`<div id="evNote"></div>`)}
    ${P_('Evidence-relevant events','tapeN',SCROLL('tape',240),`<span class="n">provenance, stub and epoch traffic</span>`)}
  </div></div>`;}

function viewFeeds(){return `<div class="grid g-2">
  <div class="col">
    ${P_('Feed Health','healthN',`<div class="pb flush"><div id="health"></div></div>`,
      `<span class="n">staleness since last write · season-aware</span>`)}
    ${P_('Event Rate by Component','compN',`<div class="pb flush"><div id="compTable"></div></div>`)}
  </div>
  <div class="col">
    ${P_('Alerts — all severities','alertN',SCROLL('alerts',420))}
    ${P_('Live Tape','tapeN',SCROLL('tape',260))}
  </div></div>`;}

const AW=src=>`<div class="aw">awaiting ${esc(src)}</div>`;
function viewCoverage(){return `<div class="grid g-1">
  ${P_('Coverage — market type × band','covN',`<div class="pb flush"><div id="cov"></div></div>`,`<span class="n" id="covRule"></span>`)}</div>`;}
function viewShadow(){return `<div class="grid g-1">
  ${P_('Shadow cells','shN',`<div class="pb flush"><div id="shCells"></div></div>`,`<span class="n">no orders · no sizing</span>`)}
  ${P_('Shadow tape','shT',SCROLL('shTape',340),`<span class="n">newest first</span>`)}</div>`;}
function viewPost(){return `<div class="grid g-2"><div class="col">
  ${P_('MLB postseason — pipelines','psN',`<div class="pb flush"><div id="ps"></div></div>`,'','t4_mlb')}</div>
  <div class="col">${P_('Open positions (all MLB pools)','psO',SCROLL('posWrap',320),'','t1_mlb')}</div></div>`;}
function viewPipeline(){return `<div class="grid g-1">
  ${P_('Pipeline — C1 → C8, one tile per component per sport','pipN',`<div class="pb flush"><div id="pipe"></div></div>`,`<span class="n">each tile read from its real output</span>`)}
  ${P_('GAPS FOUND — not instrumented','pipG',`<div class="pb flush"><div id="pipeGaps"></div></div>`)}</div>`;}
function viewVerdicts(){return `<div class="grid g-1">
  ${P_('Latest verdicts','vN',`<div class="pb flush"><div id="verd"></div></div>`,`<span class="n">files are repo-relative paths</span>`)}</div>`;}
const PCOL={ok:'var(--green)',warn:'var(--amber)',bad:'var(--red)',ni:'var(--faint)',idle:'var(--faint)'};
function fillPipeline(d){
  if(!$('#pipe')) return;
  const p=d.pipeline, t=(p&&p.tiles)||[];
  if(!t.length){ $('#pipe').innerHTML=AW((p&&p.awaiting)||'/api/data pipeline'); $('#pipN').textContent='—'; $('#pipeGaps').innerHTML=AW('pipeline'); return; }
  $('#pipN').textContent=t.length+' tiles';
  const sports=[]; t.forEach(x=>{ if(sports.indexOf(x.sport)<0) sports.push(x.sport); });
  $('#pipe').innerHTML=sports.map(sp=>`<div class="pipe-row"><div class="pipe-sp">${esc(sp)}</div><div class="pipe-flow">`+
    t.filter(x=>x.sport===sp).map(x=>{ const c=PCOL[x.status]||'var(--faint)';
      return `<div class="pipe-tile" style="border-color:${c}"><div class="pipe-c" style="color:${c}">${esc(x.c)} · ${esc(String(x.status).toUpperCase())}</div>`+
        `<div class="pipe-h">${esc(x.headline||'')}</div><div class="pipe-d">${esc(x.detail||'')}</div>`+
        `<div class="pipe-s">${esc(x.source||'')}${x.age_s!=null?' · '+fmtAge(Math.round(x.age_s)):''}</div></div>`; }).join('<span class="pipe-ar">→</span>')+
    `</div></div>`).join('');
  const g=p.gaps||[];
  $('#pipeGaps').innerHTML=g.length?`<ul class="pipe-g">`+g.map(x=>`<li>${esc(x)}</li>`).join('')+`</ul>`:`<div class="aw">none — every component has observable output</div>`;
  $('#pipG').textContent=g.length+' gaps';
}
const f4=v=>v==null||isNaN(v)?'—':Number(v).toFixed(4);
function fillV2(d){
  fillPipeline(d);
  if($('#cov')){ const c=d.coverage;
    if(!c||!c.cells){ $('#cov').innerHTML=AW((c&&c.awaiting)||'/api/data coverage'); $('#covN').textContent='—'; }
    else { $('#covN').textContent=c.total+' cells'; $('#covRule').textContent='outlined = '+c.recent_rule;
      const m={}; c.cells.forEach(x=>m[x.market_type+'|'+x.band]=x);
      const L={active:'A',shadow:'S',blocked:'B',dark:'D',ruled_out:'R',not_implemented:'·'};
      $('#cov').innerHTML=`<table class="cg"><thead><tr><th></th>${c.bands.map(b=>`<th>${esc(b)}</th>`).join('')}</tr></thead><tbody>`+
        c.market_types.map(t=>`<tr><th class="rl">${esc(t)}</th>`+c.bands.map(b=>{const x=m[t+'|'+b];
          return x?`<td class="c s-${x.status}${x.recent?' recent':''}" title="${esc(t+' / '+b+' — '+x.status+(x.reason?' — '+x.reason:''))}">${L[x.status]||'?'}</td>`
                  :`<td class="c s-none">·</td>`}).join('')+`</tr>`).join('')+`</tbody></table>`+
        `<div class="lg">`+[['active','var(--green)'],['shadow','var(--cyan)'],['blocked','var(--amber)'],['dark','#555'],
          ['ruled out','var(--red)'],['not implemented','#141414']].map(([n,col])=>`<span><i style="background:${col}"></i>${n}</span>`).join('')+
        `<span>blank = unseeded</span></div>`; } }
  if($('#shCells')){ const sh=d.shadow;
    if(!sh||!sh.cells||!sh.cells.length){ $('#shCells').innerHTML=AW((sh&&sh.awaiting)||'shadow ledgers'); $('#shN').textContent='—'; $('#shTape').innerHTML=AW('shadow rows'); }
    else { $('#shN').textContent=sh.cells.length+' cells';
      $('#shCells').innerHTML=`<table><thead><tr><th>SPORT</th><th>MARKET</th><th>BAND</th><th>REGISTRY</th><th>ROWS TODAY</th><th>ROWS TOTAL</th><th>LAST ROW</th><th>SETTLED n</th><th>JUDGED n</th><th>ΔBRIER vs MKT</th><th>ΔBRIER vs CLIMO</th><th>LATEST E_NET</th></tr></thead><tbody>`+
        sh.cells.map(c=>{const rs=c.registry_status||'unknown', off=rs!=='shadow'||!c.rows_total;
          return `<tr${off?' class="dim"':''}><td>${esc(c.sport)}</td><td>${esc(c.market_type)}</td><td>${esc(c.band)}</td>`+
          `<td class="${rs==='shadow'?'':'neg'}">${rs==='shadow'?'SHADOW':esc(rs.toUpperCase())+' (ledger only)'}</td><td class="r">${c.rows_today}</td>`+
          `<td class="r">${c.rows_total==null?'—':c.rows_total}${c.ledger?' · '+esc(c.ledger):''}</td>`+
          `<td>${esc(c.last_ts||'—')}</td><td class="r">${c.settled_n==null?'awaiting':c.settled_n}</td><td class="r">${c.judged_n==null?'awaiting':c.judged_n}</td>`+
          `<td class="r">${c.delta_brier_market==null?'awaiting':f4(c.delta_brier_market)}</td><td class="r">${c.delta_brier_climo==null?'awaiting':f4(c.delta_brier_climo)}</td>`+
          `<td class="r">${f4(c.latest_e_net)}</td></tr>`}).join('')+`</tbody></table>`;
      $('#shTape').innerHTML=`<table><thead><tr><th>TS</th><th>SPORT</th><th>MARKET</th><th>TICKER</th><th>P_YES</th><th>MID</th><th>E_NET YES</th><th>E_NET NO</th></tr></thead><tbody>`+
        (sh.tape||[]).map(r=>`<tr><td>${esc(r.ts_utc)}</td><td>${esc(r.sport)}</td><td>${esc(r.market_type)}</td><td>${esc(r.market_ticker)}</td>`+
          `<td class="r">${f4(r.p_yes)}</td><td class="r">${f4(r.mid)}</td><td class="r">${f4(r.e_net_yes_k007)}</td><td class="r">${f4(r.e_net_no_k007)}</td></tr>`).join('')+`</tbody></table>`; } }
  if($('#ps')){ const m=d.mlb_postseason;
    if(!m||m.awaiting&&m.t1_players_matched_last_run==null&&m.t4_cycle_age_s==null){ $('#ps').innerHTML=AW((m&&m.awaiting)||'mlb sources'); }
    else { const row=(k,v)=>`<div class="hw"><span class="lbl">${k}</span><span class="age">${v}</span></div>`;
      $('#ps').innerHTML=row('T1 players matched (last run)',m.t1_players_matched_last_run==null?'awaiting paper_mlb_cron.log':m.t1_players_matched_last_run)+
        row('T4 cycle-log age',m.t4_cycle_age_s==null?'awaiting t4 cycle log':fmtAge(Math.round(m.t4_cycle_age_s)))+
        row('open positions',m.open_positions)+row('stuck positions ('+esc(m.stuck_rule)+')',m.stuck_positions); } }
  if($('#verd')){ const v=d.verdicts||{}, ks=Object.keys(v);
    if(!ks.length) $('#verd').innerHTML=AW('/api/data verdicts');
    else $('#verd').innerHTML=`<table><thead><tr><th>TEST</th><th>VERDICT</th><th>WRITTEN</th><th>FILE</th></tr></thead><tbody>`+
      ks.map(k=>{const x=v[k]; if(x.awaiting) return `<tr><td>${esc(k)}</td><td class="dim" colspan="3">awaiting ${esc(x.awaiting)}</td></tr>`;
        const c=x.passed===true?'pos':x.passed===false?'neg':'dim';
        return `<tr><td>${esc(k)}</td><td class="${c}">${esc(x.verdict||'unscored')}</td><td>${esc(x.written_at)}</td><td class="dim">${esc(x.file)}</td></tr>`}).join('')+`</tbody></table>`; }
}
function ageTxt(ts){const t=Date.parse(ts); return Number.isFinite(t)?Math.max(0,Math.round((Date.now()-t)/1000)):null}
function fillNow(d){
  const st=$('#strip'); if(!st) return;
  const x=d.decisions, rows=(x&&x.rows)||[];
  if(S.notlive||!x||(!rows.length&&!(x.books||[]).some(b=>b.drawdown!=null))){
    st.innerHTML=`<div class="sb"><div class="k">MODE</div><div class="v neg">${S.notlive?'NOT LIVE':'NO DATA'}</div><div class="s">${S.notlive?'terminal cannot reach /api/data':'awaiting '+esc((x&&x.awaiting)||'decision sources')}</div></div>`;
    $('#arms').innerHTML=''; $('#dsN').textContent='—'; $('#dsRule').textContent='';
    $('#dsWrap').innerHTML=AW((x&&x.awaiting)||'decision stream (shadow ledgers + t4 cycle log)'); return; }
  const sizing=x.sizing_live===true;
  const kel=x.kelly?Object.entries(x.kelly).map(([k,v])=>k+' '+v).join(' · '):'kelly unreadable';
  const mode=`<div class="sb"><div class="k">Mode</div><div class="v ${sizing?'amb':'cy'}">${sizing?'SIZING ON':'SHADOW'}</div>`+
    `<div class="s">${sizing?'a band has kelly &gt; 0':'evaluating · no orders · stake $0'}</div><div class="src">source: execution_bands · ${esc(kel)}</div></div>`;
  const cap=`<div class="sb"><div class="k">Real capital</div><div class="v">$0</div><div class="s">paper books · demo venue · none at risk</div><div class="src">source: standing rule (no live capital before G6)</div></div>`;
  const books=(x.books||[]).map(b=>{
    if(b.drawdown==null) return `<div class="sb"><div class="k">Drawdown ${esc(b.book)} (realized)</div><div class="v dim">no data</div><div class="src">awaiting ${esc(b.awaiting||'portfolio')}</div></div>`;
    const lim=b.limit||0.2, pct=Math.min(100,b.drawdown/lim*100), cls=b.tripped?'bad':b.drawdown>=0.8*lim?'warn':'';
    const age=b.age_s==null?null:Math.round(b.age_s+(LASTPULL?(Date.now()-LASTPULL)/1000:0));
    return `<div class="sb"><div class="k">Drawdown ${esc(b.book)} (realized)</div><div class="v ${b.tripped?'neg':b.drawdown>=0.8*lim?'amb':''}">${(b.drawdown*100).toFixed(2)}%</div>`+
      `<div class="ddbar ${cls}"><i style="width:${pct.toFixed(1)}%"></i></div>`+
      `<div class="s">${b.tripped?'KILL SWITCH LIMIT BREACHED · ':''}of ${(lim*100).toFixed(0)}% kill switch · realized ${usd(b.realized_pnl)}</div>`+
      `<div class="src ${age!=null&&age>72*3600?'amb':''}">source: portfolio book · written ${fmtAge(age)} ago</div></div>`; }).join('');
  const day=new Date().toISOString().slice(0,10);
  const evals=(x.arms||[]).reduce((n,a)=>n+(a.rows_today||0),0), wf=rows.filter(r=>r.would_fire).length;
  const ev=`<div class="sb"><div class="k">Evaluations today</div><div class="v cy">${evals}</div><div class="s">${wf} of last ${rows.length} would fire · $0 each</div><div class="src">source: shadow ledgers + t4 cycle log</div></div>`;
  st.innerHTML=mode+cap+books+ev;
  $('#arms').innerHTML=(x.arms||[]).length?(x.arms||[]).map(a=>{
    const age=ageTxt(a.last_ts), cls=age==null?'old':age<=1800?'fresh':age>6*3600?'old':'';
    return `<span class="arm ${cls}" title="${esc(a.arm)} · last row ${esc(a.last_ts)} · ${a.rows_today||0} rows today">${esc(a.arm)}<b>${age==null?'no rows':fmtAge(age)+' ago'}</b></span>`; }).join(''):`<span class="aw">no arm has written a row</span>`;
  $('#dsN').textContent=rows.length+' evaluations';
  $('#dsRule').textContent=x.fire_rule||'';
  const wb=$('#wfBtn'); if(wb){ wb.classList.toggle('on',S.wfOnly); wb.onclick=()=>{S.wfOnly=!S.wfOnly; fillNow(LAST)}; }
  const f4n=v=>v==null||!Number.isFinite(Number(v))?'—':Number(v).toFixed(4);
  const shown=S.wfOnly?rows.filter(r=>r.would_fire):rows;
  $('#dsWrap').innerHTML=shown.length?`<table><thead><tr><th>TIME (UTC)</th><th>SPORT</th><th>MARKET</th><th>BAND</th><th class="r">MODEL P</th><th class="r">MKT PRICE</th><th class="r">EDGE (NET)</th><th>WOULD-FIRE</th><th>STAKE</th></tr></thead><tbody>`+
    shown.map(r=>{ const a=ageTxt(r.ts), stale=a!=null&&a>6*3600, t=String(r.ts||'');
      const tm=t.slice(0,10)===day?t.slice(11,19):t.slice(5,10)+' '+t.slice(11,16);
      const e=Number(r.edge);
      return `<tr class="${stale?'stale':''}"><td title="${esc(t)} · ${fmtAge(a)} ago">${esc(tm)}</td><td>${esc(r.sport||'—')}</td>`+
        `<td class="tk" title="${esc(r.market||'')}">${esc(r.market||'—')}</td><td>${esc(r.band||'—')}</td>`+
        `<td class="r">${f4n(r.p)}</td><td class="r">${f4n(r.price)}</td><td class="r ${Number.isFinite(e)&&e>0?'pos':'dim'}">${Number.isFinite(e)?(e>0?'+':'')+e.toFixed(4):'—'}</td>`+
        `<td class="wf">${r.would_fire?'WOULD FIRE ('+esc(r.side||'?')+')':'<span class="dim">no</span>'}</td><td class="stk">$0 SHADOW</td></tr>`}).join('')+`</tbody></table>`
    :`<div class="aw">${S.wfOnly?'no would-fire rows in the window':'no evaluations in the window'}</div>`;
}
function paintFresh(){
  const f=(LAST&&LAST.freshness)||{}, el=Date.now()-LASTPULL;
  $$('[data-fr]').forEach(e=>{ const x=f[e.dataset.fr]; e.className='fr';
    if(S.demo){ e.textContent='DEMO'; e.className='fr off'; return }
    if(S.notlive||!x){ e.textContent='no data'; e.className='fr aw'; return }
    if(x.awaiting){ e.textContent='awaiting '+x.awaiting; e.className='fr aw'; return }
    const age=Math.round(x.age_s+(LASTPULL?el/1000:0));
    e.textContent='read '+fmtAge(age)+' ago'+(x.level==='off'?' · off-season':'');
    e.className='fr '+(x.level==='red'?'bad':x.level==='amber'?'warn':x.level==='ok'?'ok':'off'); });
}
const LEGEND=`<div class="legend">
  <span><span class="sw" style="background:var(--green)"></span>YES side</span>
  <span><span class="sw" style="background:transparent;border:1.4px solid var(--red)"></span>NO side</span>
  <span><span style="width:14px;height:0;border-top:1px dashed var(--amber-dim);display:inline-block"></span>model = market</span>
  <span><span class="sw" style="background:var(--amber);opacity:.35;border-radius:2px"></span>vig band (±3¢)</span>
  <span style="color:var(--faint)">radius = stake</span></div>`;
const FILTERBAR=`<input class="filt" id="posFilt" placeholder="filter…  /">
  <button class="tbtn bf on" data-b="ALL">ALL</button>
  <button class="tbtn bf" data-b="T1">T1</button>
  <button class="tbtn bf" data-b="T4">T4</button>
  <button class="tbtn bf" data-b="NFL">NFL</button>`;

/* ═══════════ FILL ═══════════ */
function fill(D,d){
  const sportOf=(S.mod==='MLB'||S.mod==='POSTSEASON')?'MLB':S.mod==='NFL'?'NFL':null;
  const open = sportOf?D.open.filter(p=>p._sport===sportOf):D.open;
  const closed = sportOf?D.closed.filter(p=>p._sport===sportOf):D.closed;
  const events = sportOf?D.events.filter(e=>e._sport===sportOf):D.events;

  if($('#scatter')) scatter(open);
  if($('#posWrap')) positions(open);
  if($('#resWrap')) resolved(closed);
  if($('#tape'))    tape(S.mod==='EVIDENCE'
      ? events.filter(e=>/stub|model|provenance|epoch|identity|refused|clean_n|calibration/i
          .test((e.event_type||'')+JSON.stringify(e.payload||{})))
      : events);
  if($('#ladder'))  ladder(open);
  if($('#lanes'))   lanes(D,d);
  if($('#alerts'))  alerts(events, S.mod==='FEEDS');
  if($('#health'))  {health(d,D); }
  if($('#nflNote')) nflNote(D,d);
  if($('#poolKv'))  poolKv(D,d,sportOf);
  if($('#evTable')) evidence(D,d);
  if($('#compTable')) components(D.events);
  if($('#posFilt')){ $('#posFilt').value=S.filt;
    $('#posFilt').addEventListener('input',e=>{S.filt=e.target.value.trim(); positions(open)}); }
  $$('.bf').forEach(b=>{ b.classList.toggle('on',b.dataset.b===S.band);
    b.addEventListener('click',()=>{S.band=b.dataset.b; $$('.bf').forEach(o=>o.classList.remove('on'));
      b.classList.add('on'); positions(open)}) });
}

/* ═══════════ SCATTER ═══════════ */
function scatter(open){
  const pts=open.filter(p=>p.model_p!=null&&p.mid_price_at_entry!=null);
  const n=$('#scatN'); if(n) n.textContent=pts.length+' open priced';
  const W=760,H=258,L=42,R=14,T=10,B=28;
  const x=v=>L+v*(W-L-R), y=v=>T+(1-v)*(H-T-B);
  let s=`<svg viewBox="0 0 ${W} ${H}" role="img" aria-label="Model probability versus market implied price">`;
  s+=`<polygon class="vigband" points="${x(0)},${y(0.03)} ${x(0.97)},${y(1)} ${x(1)},${y(1)} ${x(1)},${y(0.97)} ${x(0.03)},${y(0)} ${x(0)},${y(0)}"/>`;
  s+=`<line class="ident" x1="${x(0)}" y1="${y(0)}" x2="${x(1)}" y2="${y(1)}"/>`;
  for(let i=0;i<=5;i++){const v=i/5;
    s+=`<line class="ax" x1="${x(v)}" y1="${T}" x2="${x(v)}" y2="${H-B}" opacity=".45"/>`;
    s+=`<line class="ax" x1="${L}" y1="${y(v)}" x2="${W-R}" y2="${y(v)}" opacity=".45"/>`;
    s+=`<text class="axl sm" x="${x(v)}" y="${H-B+13}" text-anchor="middle">${v.toFixed(1)}</text>`;
    s+=`<text class="axl sm" x="${L-7}" y="${y(v)+3}" text-anchor="end">${v.toFixed(1)}</text>`}
  s+=`<text class="axl sm" x="${(L+W-R)/2}" y="${H-3}" text-anchor="middle" style="letter-spacing:.1em">MARKET IMPLIED PRICE →</text>`;
  s+=`<text class="axl sm" x="11" y="${(T+H-B)/2}" text-anchor="middle" transform="rotate(-90 11 ${(T+H-B)/2})" style="letter-spacing:.1em">MODEL P →</text>`;
  pts.forEach(p=>{
    const yes=String(p.direction||'').toUpperCase()==='YES', col=yes?'var(--green)':'var(--red)';
    const r=Math.max(3,Math.min(9,Math.sqrt(Math.abs(Number(p.size_usd)||1))*1.5));
    const ec=evClass(p);
    s+=`<circle class="pt" cx="${x(Math.max(0,Math.min(1,p.mid_price_at_entry))).toFixed(1)}" cy="${y(Math.max(0,Math.min(1,p.model_p))).toFixed(1)}" r="${r.toFixed(1)}" fill="${yes?col:'none'}" fill-opacity="${yes?.55:1}" stroke="${col}" stroke-dasharray="${ec==='STUB'?'2 2':''}" data-tip="${encodeURIComponent(
      `<div class="h">${esc(p.player_name||p.kalshi_ticker||'—')} · ${esc(p._band)}</div>`+
      `<div class="r"><span>threshold</span><b>H≥${esc(p.kalshi_threshold??'?')}</b></div>`+
      `<div class="r"><span>side</span><b>${esc(p.direction||'—')}</b></div>`+
      `<div class="r"><span>model p</span><b>${num(p.model_p,4)}</b></div>`+
      `<div class="r"><span>market mid</span><b>${num(p.mid_price_at_entry,4)}</b></div>`+
      `<div class="r"><span>gross edge</span><b>${num(p.gross_edge,4)}</b></div>`+
      `<div class="r"><span>size</span><b>${usd(p.size_usd)}</b></div>`+
      `<div class="r"><span>evidence</span><b>${ec}</b></div>`+
      `<div class="r"><span>entered</span><b>${mmdd(p.entered_at)}</b></div>`)}"/>`;
  });
  if(!pts.length) s+=`<text class="axl" x="${W/2}" y="${H/2}" text-anchor="middle" style="font-size:11px">no priced open positions</text>`;
  $('#scatter').innerHTML=s+`</svg>`; wireTips($('#scatter'));
}

/* ═══════════ POSITIONS ═══════════ */
const POSCOLS=[
  ['BAND','_band',p=>`<span class="tag ${p._band.toLowerCase()}">${p._band}</span>`],
  ['EVID','model_identity',p=>{const [c,l]=EVTAG[evClass(p)]; return `<span class="tag ${c}">${l}</span>`}],
  ['PLAYER / TICKER','player_name',p=>esc(p.player_name||p.kalshi_ticker||'—')],
  ['THR','kalshi_threshold',p=>p.kalshi_threshold==null?'—':'H≥'+esc(p.kalshi_threshold)],
  ['DIR','direction',p=>{const y=String(p.direction||'').toUpperCase()==='YES';
    return `<span class="dir ${y?'y':'n'}">${esc(p.direction||'—')}</span>`}],
  ['SIZE','size_usd',p=>usd(p.size_usd),'r'],
  ['MODEL P','model_p',p=>num(p.model_p,4),'r'],
  ['MKT','mid_price_at_entry',p=>num(p.mid_price_at_entry,4),'r'],
  ['EDGE','gross_edge',p=>`<span class="${sgn(p.gross_edge)}">${num(p.gross_edge,4)}</span>`,'r'],
  ['VIG','vig_at_entry',p=>num(p.vig_at_entry,3),'r'],
  ['EPOCH','logic_epoch',p=>`<span class="dim">${p.logic_epoch??'—'}</span>`,'r'],
  ['ENTERED','entered_at',p=>`<span class="dim">${mmdd(p.entered_at)}</span>`],
];
function positions(all){
  let rows=all;
  if(S.band!=='ALL') rows=rows.filter(p=>p._band===S.band);
  if(S.filt){const q=S.filt.toLowerCase();
    rows=rows.filter(p=>JSON.stringify([p.player_name,p.kalshi_ticker,p.direction,p._band,p.kalshi_threshold,p.model_identity]).toLowerCase().includes(q))}
  const k=S.sortKey,dir=S.sortDir;
  rows=[...rows].sort((a,b)=>{const A=a[k],B=b[k];
    if(A==null)return 1; if(B==null)return -1;
    return (typeof A==='number'&&typeof B==='number')?(A-B)*dir:String(A).localeCompare(String(B))*dir});
  const n=$('#openN'); if(n) n.textContent=`${rows.length}${rows.length!==all.length?' / '+all.length:''} open`;
  const host=$('#posWrap'); if(!host) return;
  if(!rows.length){host.innerHTML=`<div class="empty">no open positions match</div>`; return}
  const head=POSCOLS.map(([lab,key,,al])=>`<th data-k="${key}" class="${al==='r'?'r':''}">${lab}${k===key?` <span class="ar">${dir>0?'▲':'▼'}</span>`:''}</th>`).join('');
  const body=rows.map(p=>{
    const id=p.position_id||`${p._band}|${p.kalshi_ticker}|${p.entered_at}`;
    const isNew=!S.seenPos.has(id); S.seenPos.add(id);
    return `<tr class="${isNew&&!S.first?'new':''}">`+POSCOLS.map(([,,fn,al])=>`<td class="${al==='r'?'r':''}">${fn(p)}</td>`).join('')+`</tr>`}).join('');
  host.innerHTML=`<table><thead><tr>${head}</tr></thead><tbody>${body}</tbody></table>`;
  host.querySelectorAll('th[data-k]').forEach(th=>th.addEventListener('click',()=>{
    const key=th.dataset.k;
    if(S.sortKey===key)S.sortDir*=-1; else{S.sortKey=key;S.sortDir=-1}
    positions(all)}));
}

/* ═══════════ RESOLVED ═══════════ */
function resolved(closed){
  const rows=[...closed].filter(p=>p.resolved_at||p.outcome)
    .sort((a,b)=>String(b.resolved_at||'').localeCompare(String(a.resolved_at||''))).slice(0,150);
  const res=closed.filter(p=>p.outcome==='WIN'||p.outcome==='LOSS');
  const w=res.filter(p=>p.outcome==='WIN').length;
  const tot=closed.reduce((s,p)=>s+(Number(p.pnl)||Number(p.exit_pnl)||0),0);
  const n=$('#resN'); if(n) n.textContent=`${res.length} settled`;
  const pn=$('#resPnl'); if(pn) pn.innerHTML=`<span class="pos">${w}W</span> / <span class="neg">${res.length-w}L</span> · <span class="${sgn(tot)}">${usd(tot)}</span>`;
  const host=$('#resWrap'); if(!host) return;
  if(!rows.length){host.innerHTML=`<div class="empty">nothing resolved in window</div>`; return}
  host.innerHTML=`<table><thead><tr><th class="na">BAND</th><th class="na">EVID</th><th class="na">PLAYER</th>
    <th class="na">THR</th><th class="na">DIR</th><th class="na r">ACTUAL</th><th class="na">RESULT</th>
    <th class="na r">P&amp;L</th><th class="na">RESOLVED</th></tr></thead><tbody>`+
    rows.map(p=>{const y=String(p.direction||'').toUpperCase()==='YES';
      const pl=Number(p.pnl)||Number(p.exit_pnl)||0, win=p.outcome==='WIN';
      const [c,l]=EVTAG[evClass(p)];
      return `<tr><td><span class="tag ${p._band.toLowerCase()}">${p._band}</span></td>`+
        `<td><span class="tag ${c}">${l}</span></td>`+
        `<td>${esc(p.player_name||p.kalshi_ticker||'—')}</td>`+
        `<td>${p.kalshi_threshold==null?'—':'H≥'+esc(p.kalshi_threshold)}</td>`+
        `<td><span class="dir ${y?'y':'n'}">${esc(p.direction||'—')}</span></td>`+
        `<td class="r dim">${p.actual_stat??p.actual_pts??'—'}</td>`+
        `<td><span class="${win?'pos':'neg'}" style="font-weight:700">${esc(p.outcome||'—')}</span></td>`+
        `<td class="r ${sgn(pl)}">${usd(pl)}</td><td class="dim">${mmdd(p.resolved_at)}</td></tr>`}).join('')+`</tbody></table>`;
}

/* ═══════════ TAPE ═══════════ */
function summarise(e){
  const t=e.event_type||'event', pl=e.payload||{}, bits=[];
  if(pl.player_name)bits.push(pl.player_name);
  if(pl.ticker||pl.kalshi_ticker)bits.push(pl.ticker||pl.kalshi_ticker);
  if(pl.threshold!=null)bits.push('H≥'+pl.threshold);
  if(pl.direction)bits.push(pl.direction);
  if(pl.size_usd!=null)bits.push(usd(pl.size_usd));
  if(pl.gross_edge!=null)bits.push('edge '+num(pl.gross_edge,4));
  if(pl.p_model!=null||pl.model_p!=null)bits.push('p '+num(pl.p_model??pl.model_p,4));
  if(pl.clean_n!=null)bits.push('clean_n '+pl.clean_n);
  if(pl.verdict||pl.edge_monotonicity_verdict)bits.push(pl.verdict||pl.edge_monotonicity_verdict);
  if(pl.reason)bits.push(clip(pl.reason,64));
  if(pl.action_required)bits.push(clip(pl.action_required,74));
  return `<b style="color:var(--amber);font-weight:400">${esc(t)}</b>`+(bits.length?` <em>${esc(bits.join(' · '))}</em>`:'');
}
function tape(events){
  const rows=events.slice(0,220);
  const n=$('#tapeN'); if(n) n.textContent=`${events.length} in window`;
  const host=$('#tape'); if(!host) return;
  if(!rows.length){host.innerHTML=`<div class="empty">no audit events in window</div>`; return}
  host.innerHTML=rows.map(e=>{
    const id=e.event_id||`${e.timestamp}|${e.event_type}`;
    const isNew=!S.seenEvt.has(id); S.seenEvt.add(id);
    const bc=e._band==='T1'?'var(--cyan)':e._band==='T4'?'var(--amber)':'var(--violet)';
    return `<div class="tl ${isNew&&!S.first?'new':''}"><span class="ts">${hhmm(e.timestamp)}</span>`+
      `<span class="bd" style="color:${bc}">${esc(e._band)}</span><span class="msg">${summarise(e)}</span></div>`}).join('');
}

/* ═══════════ EDGE LADDER — 1:1 text scale ═══════════ */
function ladder(open){
  const rows=open.filter(p=>p.gross_edge!=null).sort((a,b)=>b.gross_edge-a.gross_edge);
  const n=$('#ladN');
  const host=$('#ladder'); if(!host) return;
  if(!rows.length){ if(n)n.textContent=''; host.innerHTML=`<div class="empty">no edges on open positions</div>`; return}
  const top=[...rows.slice(0,7),...rows.slice(-7)].filter((v,i,a)=>a.indexOf(v)===i);
  if(n) n.textContent=`widest ${Math.min(7,rows.length)} each way of ${rows.length}`;
  const mx=Math.max(...rows.map(p=>Math.abs(p.gross_edge)),0.01);
  // viewBox width ~ rendered width so 10px text renders at 10px
  const W=760, rowH=17, H=top.length*rowH+24, mid=W*0.50, half=W*0.34;
  let s=`<svg viewBox="0 0 ${W} ${H}" role="img" aria-label="Gross edge on open positions">`;
  s+=`<line class="ax" x1="${mid}" y1="2" x2="${mid}" y2="${H-19}"/>`;
  s+=`<text class="axl sm" x="${mid}" y="${H-5}" text-anchor="middle">0</text>`;
  s+=`<text class="axl sm" x="${mid-half}" y="${H-5}" text-anchor="middle">−${mx.toFixed(3)}</text>`;
  s+=`<text class="axl sm" x="${mid+half}" y="${H-5}" text-anchor="middle">+${mx.toFixed(3)}</text>`;
  top.forEach((p,i)=>{
    const y=4+i*rowH, v=p.gross_edge, w=Math.abs(v)/mx*half;
    const col=v>=0?'var(--green)':'var(--red)';
    s+=`<rect x="${v>=0?mid:mid-w}" y="${y}" width="${Math.max(w,0.8).toFixed(1)}" height="${rowH-6}" fill="${col}" fill-opacity=".8" data-tip="${encodeURIComponent(
      `<div class="h">${esc(p.player_name||p.kalshi_ticker||'—')} · ${esc(p._band)}</div>`+
      `<div class="r"><span>gross edge</span><b>${num(v,4)}</b></div>`+
      `<div class="r"><span>size</span><b>${usd(p.size_usd)}</b></div>`+
      `<div class="r"><span>model / market</span><b>${num(p.model_p,3)} / ${num(p.mid_price_at_entry,3)}</b></div>`+
      `<div class="r"><span>evidence</span><b>${evClass(p)}</b></div>`)}"/>`;
    s+=`<text class="axl" x="${v>=0?mid-6:mid+6}" y="${y+rowH-8}" text-anchor="${v>=0?'end':'start'}" style="fill:var(--dim)">${esc(clip(p.player_name||p.kalshi_ticker||'—',20))}</text>`;
    s+=`<text class="axl sm" x="${v>=0?mid+w+5:mid-w-5}" y="${y+rowH-8}" text-anchor="${v>=0?'start':'end'}" style="fill:${col}">${v>0?'+':''}${v.toFixed(3)}</text>`;
  });
  host.innerHTML=s+`</svg>`; wireTips(host);
}

/* ═══════════ BAND LANES ═══════════ */
function lanes(D,d){
  const ep=d.current_logic_epoch, host=$('#lanes'); if(!host) return;
  const B=[['T1','MLB'],['T4','MLB'],['NFL','NFL']];
  const mx=Math.max(1,...B.map(([b])=>D.closed.filter(p=>p._band===b).length));
  const n=$('#lanesN'); if(n) n.textContent='clean / raw · realised P&L';
  host.innerHTML=B.map(([b])=>{
    const o=D.open.filter(p=>p._band===b), c=D.closed.filter(p=>p._band===b);
    const clean=c.filter(p=>ep!=null&&Number(p.logic_epoch)>=Number(ep)).length;
    const countable=c.filter(p=>ep!=null&&Number(p.logic_epoch)>=Number(ep)&&evClass(p)==='MODEL').length;
    const pnl=c.reduce((s,p)=>s+(Number(p.pnl)||Number(p.exit_pnl)||0),0);
    return `<div class="lane"><span class="tag ${b.toLowerCase()}">${b}</span>
      <span class="bar"><i style="width:${(c.length/mx*100).toFixed(1)}%;background:#2a2a28"></i>
        <i style="width:${(clean/mx*100).toFixed(1)}%;background:var(--cyan);opacity:.85"></i>
        <i style="width:${(countable/mx*100).toFixed(1)}%;background:var(--green)"></i></span>
      <span class="nn dim">${o.length} open</span>
      <span class="nn ${sgn(pnl)}">${usd(pnl)}</span></div>
      <div class="sublane">raw ${c.length} · epoch-clean <span class="cy">${clean}</span> · countable <span class="${countable?'pos':'neg'}">${countable}</span>${ep!=null?` · floor ${ep}`:''}</div>`;
  }).join('');
}

/* ═══════════ ALERTS ═══════════ */
function alerts(events,all){
  const sev=events.filter(e=>e.severity&&(all||e.severity!=='INFO'));
  const seen=new Map();
  sev.forEach(e=>{const k=`${e._band}|${e.component}|${e.event_type}`;
    if(!seen.has(k))seen.set(k,{...e,_n:1}); else seen.get(k)._n++});
  const rows=[...seen.values()].slice(0,120);
  const n=$('#alertN'); if(n) n.textContent=`${sev.length} raised · ${rows.length} distinct`;
  const host=$('#alerts'); if(!host) return;
  if(!rows.length){host.innerHTML=`<div class="empty">no warnings or errors in window</div>`; return}
  host.innerHTML=`<table><thead><tr><th class="na">TIME</th><th class="na">BND</th><th class="na">SEV</th>
    <th class="na">COMP</th><th class="na">EVENT</th><th class="na r">×</th></tr></thead><tbody>`+
    rows.map(e=>`<tr><td class="dim">${hhmm(e.timestamp)}</td>`+
      `<td><span class="tag ${e._band.toLowerCase()}">${e._band}</span></td>`+
      `<td><span class="sev ${esc(e.severity)}">${esc(e.severity)}</span></td>`+
      `<td class="dim">${esc(e.component||'—')}</td><td>${esc(e.event_type||'—')}</td>`+
      `<td class="r ${e._n>1?'amb':'dim'}">${e._n}</td></tr>`).join('')+`</tbody></table>`;
}

/* ═══════════ NFL NOTE ═══════════ */
function nflNote(D,d){
  const all=[...D.open,...D.closed].filter(p=>p._sport==='NFL');
  const stub=all.filter(p=>evClass(p)==='STUB').length;
  const real=all.filter(p=>evClass(p)==='MODEL').length;
  const un=all.filter(p=>evClass(p)==='UNATTRIBUTED').length;
  const host=$('#nflNote'); if(!host) return;
  if(!all.length){ host.innerHTML=`<div class="note">NFL pool is empty in this payload. <b>/api/data</b> does carry
    <b>nfl_portfolio</b> and <b>nfl_audit</b> — an empty pool here means the T1 NFL run path has not written,
    not that the terminal is MLB-only.</div>`; return }
  const pctStub=(stub/all.length*100).toFixed(0);
  host.innerHTML= stub
    ? `<div class="note bad"><span class="hl">${stub} of ${all.length} NFL rows (${pctStub}%) are STUB-sourced and are not evidence.</span>
       The T1 NFL run path defaults to <b>StubNFLForecastModel</b> — a fixed p with no NFL feature store — so approval
       is driven by a constant versus each quote. Row counts here overstate usable evidence.
       Real model rows: <b>${real}</b> · unattributed: <b>${un}</b>. Model in use: <b>${esc(d.nfl_model_provenance||'—')}</b>.</div>`
    : `<div class="note">NFL rows: <b>${all.length}</b> · real model <b>${real}</b> · unattributed <b>${un}</b>.
       Model in use: <b>${esc(d.nfl_model_provenance||'—')}</b>.</div>`;
}

/* ═══════════ POOL KV ═══════════ */
function poolKv(D,d,sport){
  const host=$('#poolKv'); if(!host) return;
  const pools = sport==='NFL' ? [['NFL T1',D.NF]] : [['MLB T1',D.P],['MLB T4',D.T4]];
  host.innerHTML=pools.map(([lab,P])=>`<div style="margin-bottom:10px">
    <div style="color:var(--amber);font-size:10.5px;letter-spacing:.1em;margin-bottom:4px">${lab}</div>
    <dl class="kv">
      <dt>bankroll</dt><dd>${usd(P.bankroll_usd)}</dd>
      <dt>initial</dt><dd>${usd(P.initial_bankroll_usd)}</dd>
      <dt>realised P&L</dt><dd class="${sgn(P.total_realized_pnl)}">${usd(P.total_realized_pnl)}</dd>
      <dt>daily net</dt><dd class="${sgn(P.daily_net_pnl)}">${usd(P.daily_net_pnl)}</dd>
      <dt>open / closed</dt><dd>${toArr(P.open_positions).length} / ${toArr(P.closed_positions).length}</dd>
      <dt>last write</dt><dd>${P.last_updated?fmtAge(Math.round((Date.now()-new Date(P.last_updated))/1000))+' ago':'—'}</dd>
    </dl></div>`).join('');
  const n=$('#poolN'); if(n) n.textContent=pools.length+' pool'+(pools.length>1?'s':'');
}

/* ═══════════ EVIDENCE MODULE ═══════════ */
function evidence(D,d){
  const ep=d.current_logic_epoch;
  const rowsFor=(lab,arr)=>{
    const m=arr.filter(p=>evClass(p)==='MODEL').length;
    const st=arr.filter(p=>evClass(p)==='STUB').length;
    const un=arr.filter(p=>evClass(p)==='UNATTRIBUTED').length;
    const clean=arr.filter(p=>ep!=null&&Number(p.logic_epoch)>=Number(ep)).length;
    const cnt=arr.filter(p=>ep!=null&&Number(p.logic_epoch)>=Number(ep)&&evClass(p)==='MODEL').length;
    return `<tr><td class="k">${lab}</td><td class="r">${arr.length}</td>
      <td class="r cy">${clean}</td><td class="r ${m?'pos':'dim'}">${m}</td>
      <td class="r ${st?'neg':'dim'}">${st}</td><td class="r dim">${un}</td>
      <td class="r ${cnt?'pos':'neg'}" style="font-weight:700">${cnt}</td></tr>`};
  const groups=[['MLB T1',D.open.concat(D.closed).filter(p=>p._band==='T1')],
    ['MLB T4',D.open.concat(D.closed).filter(p=>p._band==='T4')],
    ['NFL T1',D.open.concat(D.closed).filter(p=>p._band==='NFL')]];
  const tot=D.open.concat(D.closed);
  $('#evTable').innerHTML=`<table><thead><tr><th class="na">POOL</th><th class="na r">ROWS</th>
    <th class="na r">EPOCH-CLEAN</th><th class="na r">MODEL</th><th class="na r">STUB</th>
    <th class="na r">UNATTR</th><th class="na r">COUNTABLE</th></tr></thead><tbody>`+
    groups.map(([l,a])=>rowsFor(l,a)).join('')+rowsFor('ALL',tot)+`</tbody></table>`;
  const n=$('#evN'); if(n) n.textContent=`${tot.length} rows across 3 pools`;

  const mi=new Map();
  tot.forEach(p=>{const k=p.model_identity||'(absent)'; mi.set(k,(mi.get(k)||0)+1)});
  const mis=[...mi.entries()].sort((a,b)=>b[1]-a[1]);
  $('#miTable').innerHTML=`<table><thead><tr><th class="na">MODEL_IDENTITY</th><th class="na">CLASS</th>
    <th class="na r">ROWS</th></tr></thead><tbody>`+mis.map(([k,v])=>{
      const c=/stub/i.test(k)?'STUB':(k==='(absent)'||k==='UNKNOWN')?'UNATTRIBUTED':'MODEL';
      const [cc,ll]=EVTAG[c];
      return `<tr><td style="white-space:normal">${esc(clip(k,70))}</td>`+
        `<td><span class="tag ${cc}">${ll}</span></td><td class="r">${v}</td></tr>`}).join('')+`</tbody></table>`;
  const mn=$('#miN'); if(mn) mn.textContent=`${mis.length} distinct`;

  const cnt=tot.filter(p=>ep!=null&&Number(p.logic_epoch)>=Number(ep)&&evClass(p)==='MODEL').length;
  $('#evNote').innerHTML=`<div class="note ${cnt?'':'bad'}">
    <b>Countable</b> means a row is both epoch-clean for its band <b>and</b> carries a real model identity.
    A row can be perfectly valid and still count for nothing — that is a provenance property, not a data problem.
    Right now <b class="${cnt?'pos':'hl'}">${cnt}</b> of ${tot.length} rows in these pools would survive a
    fail-closed evidence predicate. Epoch floor <b>${ep??'—'}</b>.</div>`;
}

/* ═══════════ COMPONENTS ═══════════ */
function components(events){
  const m=new Map();
  events.forEach(e=>{const k=e.component||'—';
    const o=m.get(k)||{n:0,w:0,er:0}; o.n++;
    if(e.severity==='WARNING')o.w++; if(e.severity==='ERROR'||e.severity==='CRITICAL')o.er++;
    m.set(k,o)});
  const rows=[...m.entries()].sort((a,b)=>b[1].n-a[1].n);
  const n=$('#compN'); if(n) n.textContent=`${rows.length} components · ${events.length} events`;
  $('#compTable').innerHTML=`<table><thead><tr><th class="na">COMPONENT</th><th class="na r">EVENTS</th>
    <th class="na r">WARN</th><th class="na r">ERROR</th></tr></thead><tbody>`+
    rows.map(([k,v])=>`<tr><td>${esc(k)}</td><td class="r">${v.n}</td>
      <td class="r ${v.w?'amb':'dim'}">${v.w}</td><td class="r ${v.er?'neg':'dim'}">${v.er}</td></tr>`).join('')+`</tbody></table>`;
}

/* ═══════════ HEALTH ═══════════ */
function fmtAge(s){if(s==null)return '—';
  if(s<60)return s+'s'; if(s<3600)return Math.floor(s/60)+'m'+(s%60)+'s';
  if(s<86400)return Math.floor(s/3600)+'h'+Math.floor((s%3600)/60)+'m';
  return Math.floor(s/86400)+'d'+Math.floor((s%86400)/3600)+'h'}
function ageCls(s,w,b){return s==null?'':s>b?'bad':s>w?'warn':'ok'}
let HEALTH=[];
function health(d,D){
  HEALTH=[...Object.entries(d.pipe_mtimes||{}).map(([k,v])=>({lbl:k,t:v,warn:26*3600,bad:50*3600})),
    {lbl:'PORTFOLIO  MLB T1', t:D.P.last_updated,  warn:26*3600, bad:72*3600},
    {lbl:'PORTFOLIO  MLB T4', t:D.T4.last_updated, warn:2*3600,  bad:12*3600},
    {lbl:'PORTFOLIO  NFL T1', t:D.NF.last_updated, warn:8*86400, bad:14*86400}];
  const sn=d.season||{};
  HEALTH.forEach(h=>{ const sp=/NFL/.test(h.lbl)?'NFL':/MLB/.test(h.lbl)?'MLB':null;
    if(sp&&sn[sp]&&sn[sp].state==='off') h.off=true; });
  const n=$('#healthN'); if(n) n.textContent=HEALTH.length+' feeds';
  paintHealth();
}
function paintHealth(){
  const host=$('#health'); if(!host) return;
  const now=Date.now();
  host.innerHTML=HEALTH.map(h=>{
    const ts=h.t&&!isNaN(new Date(h.t))?new Date(h.t).getTime():null;
    const age=ts?Math.round((now-ts)/1000):null;
    const c=age==null||h.off?'':ageCls(age,h.warn,h.bad);
    return `<div class="hw"><span class="lbl">${esc(h.lbl)}</span>`+
      `<span class="age ${c}">${age==null?esc(h.t||'no log yet'):fmtAge(age)+' ago'}${h.off?' · off-season':''}</span>`+
      `<span class="dot ${c}"></span></div>`}).join('');
}

/* ═══════════ LOOP ═══════════ */
function tick(){
  $('#clock').textContent=new Date().toISOString().slice(11,19)+'Z';
  paintHealth(); paintFresh();
  if(S.paused){$('#cd').textContent='||'; return}
  S.cd--; if(S.cd<=0){S.cd=REFRESH_S; pull()}
  $('#cd').textContent=String(S.cd).padStart(2,'0');
}
$('#refresh').addEventListener('click',()=>{S.cd=REFRESH_S; pull()});
$('#pause').addEventListener('click',()=>{S.paused=!S.paused;
  $('#pause').classList.toggle('on',S.paused);
  $('#pause').textContent=S.paused?'▶ RESUME':'⏸ PAUSE'});
addEventListener('keydown',e=>{
  if(e.target.tagName==='INPUT'){if(e.key==='Escape')e.target.blur(); return}
  if(e.key==='r'){S.cd=REFRESH_S; pull()}
  if(e.key===' '){e.preventDefault(); $('#pause').click()}
  if(e.key==='/'){e.preventDefault(); $('#posFilt')?.focus()}
  const mi=['1','2','3','4','5','6','7','8','9'].indexOf(e.key);
  if(mi>=0&&MODULES[mi]){S.mod=MODULES[mi].k; render()}
});

/* ═══════════ DEMO PAYLOAD (schema-accurate; only when /api/data is unreachable) ═══════════ */
const _now=Date.now(), _iso=s=>new Date(_now-s*1000).toISOString().replace(/\.\d+Z$/,'Z');
const NAMES=['CJ Abrams','Julio Rodríguez','Mike Trout','Nick Kurtz','Bobby Witt Jr.',
  'Freddie Freeman','Bryce Harper','Trea Turner','Kyle Schwarber','Francisco Lindor'];
const REAL_MLB='MLB LR+Platt QS-2026-05-28-002';
const STUB_NFL='STUB (StubNFLForecastModel — NOT a trained model, GG-255)';
const REAL_NFL='EXP-027 LR (T-531, HYP-012, verdict UNDERPOWERED)';
const _mk=(n,seed,mid_ident,tick_pfx)=>Array.from({length:n},(_,i)=>{
  const mp=+(0.18+((seed*7+i*13)%70)/100).toFixed(4);
  const md=+(mp+(((seed*3+i*11)%25)-12)/100).toFixed(4);
  return {position_id:`PT-${seed}${i}`, player_name:NAMES[(seed+i)%10],
    kalshi_ticker:`${tick_pfx}-26SEP-${seed}${i}`, kalshi_threshold:1+((i+seed)%2),
    direction:((i+seed)%3===0)?'YES':'NO', size_usd:+(3+((seed*5+i*7)%20)).toFixed(2),
    model_p:mp, mid_price_at_entry:Math.min(.98,Math.max(.02,md)),
    gross_edge:+(mp-md).toFixed(4), vig_at_entry:0.03, entered_at:_iso(600+i*420),
    status:'OPEN', logic_epoch:12, model_identity:(typeof mid_ident==='function')?mid_ident(i):mid_ident}});
const _mkc=(n,seed,mid_ident,pfx)=>_mk(n,seed,mid_ident,pfx).map((p,i)=>({...p,status:'RESOLVED',
  outcome:((i+seed)%2)?'WIN':'LOSS', pnl:+(((i+seed)%2?1:-1)*(.05+((i*seed)%150)/100)).toFixed(2),
  actual_pts:(i+seed)%4, resolved_at:_iso(3600+i*900)}));
const DEMO={
  server_time:new Date(_now).toISOString().replace(/\.\d+Z$/,'Z'), current_logic_epoch:12,
  nfl_model_provenance:REAL_NFL,
  rejected_counts:{mlb:212, mlb_t4:2000, nfl:0},
  process:{started_at:_iso(3600*5), sha:'0123456789abcdef0123456789abcdef01234567'},
  t4_cycle_tail:Array.from({length:40},(_,i)=>({ts:_iso(2400-i*60), cycle_id:'C'+String(900+Math.floor(i/2)).padStart(4,'0')+'-demo',
    session_id:'T4-MLB-DEMO', ticker:'KXMLBHIT-DEMO', mip:0.3})).reverse(),
  portfolio:{bankroll_usd:733.75, initial_bankroll_usd:838.00, total_realized_pnl:-106.01,
    daily_net_pnl:15.84, current_daily_loss:0, last_updated:_iso(240),
    open_positions:_mk(11,3,REAL_MLB,'KXMLBHIT'), closed_positions:_mkc(40,5,REAL_MLB,'KXMLBHIT')},
  t4_portfolio:{bankroll_usd:201.98, initial_bankroll_usd:200.00, total_realized_pnl:1.98,
    daily_net_pnl:0, last_updated:_iso(70),
    open_positions:_mk(6,9,'UNKNOWN','KXMLBHIT'), closed_positions:_mkc(60,2,'UNKNOWN','KXMLBHIT')},
  nfl_portfolio:{bankroll_usd:100.00, initial_bankroll_usd:100.00, total_realized_pnl:0,
    daily_net_pnl:0, last_updated:_iso(86400*2),
    open_positions:_mk(22,7,i=>i<3?REAL_NFL:STUB_NFL,'KXNFLGAME'),
    closed_positions:_mkc(30,4,i=>i<4?REAL_NFL:STUB_NFL,'KXNFLGAME')},
  audit:[
    {timestamp:_iso(45),event_id:'E1',component:'C5',event_type:'position_opened',severity:'INFO',
     payload:{player_name:'Bobby Witt Jr.',threshold:1,direction:'NO',size_usd:8.06,gross_edge:-0.1282,p_model:0.6418}},
    {timestamp:_iso(180),event_id:'E2',component:'C7',event_type:'band_monitor_calibration_alarm',severity:'WARNING',
     payload:{band:'T1',clean_n:60,edge_monotonicity_verdict:'ANTI-PREDICTIVE',
       action_required:'DS review required before any capital decision touches this band (GG-098) — warn-only'}},
    {timestamp:_iso(420),event_id:'E3',component:'C1',event_type:'pitcher_game_log_empty',severity:'WARNING',
     payload:{reason:'upstream returned 0 rows for probable starter'}},
    {timestamp:_iso(900),event_id:'E4',component:'C3',event_type:'forecast_emitted',severity:'INFO',
     payload:{player_name:'Mike Trout',threshold:1,p_model:0.5993}},
    {timestamp:_iso(1500),event_id:'E5',component:'PIPE-06pre',event_type:'data_contract_violation',severity:'WARNING',
     payload:{reason:"unexpected column 'ba_l10_shrunk' present"}}],
  t4_audit:[
    {timestamp:_iso(20),event_id:'T1e',component:'C5',event_type:'t4_evaluation_cycle',severity:'INFO',
     payload:{ticker:'KXMLBHIT-26SEP-91',p_model:0.7412,gross_edge:0.0181}},
    {timestamp:_iso(95),event_id:'T2e',component:'C5',event_type:'position_rejected',severity:'INFO',
     payload:{ticker:'KXMLBHIT-26SEP-92',reason:'edge below T4_MIN_DELTA_P after vig'}},
    {timestamp:_iso(310),event_id:'T3e',component:'C4',event_type:'staleness_halt',severity:'ERROR',
     payload:{reason:'ESPN feed age 214s exceeds 120s ceiling'}}],
  nfl_audit:[
    {timestamp:_iso(3000),event_id:'N1',component:'C5',event_type:'position_opened',severity:'INFO',
     payload:{ticker:'KXNFLGAME-26SEP-71',direction:'YES',size_usd:1.00,p_model:0.55}},
    {timestamp:_iso(3200),event_id:'N2',component:'C5',event_type:'stub_model_in_use',severity:'WARNING',
     payload:{reason:'default StubNFLForecastModel — rows are pipeline-shape evidence only (GG-317)'}},
    {timestamp:_iso(3400),event_id:'N3',component:'C5',event_type:'refused_no_model',severity:'WARNING',
     payload:{reason:'no NFL C2/C3 feature store for this market family (GG-255)'}}],
  decisions:{rows:[
    {ts:_iso(30),sport:'MLB',market:'KXMLBHIT-26SEP-91',market_type:'MLB_PLAYER_PROP_HITS',band:'T4M-PROJ',p:0.7412,price:0.64,edge:0.0612,side:'YES',would_fire:true,src:'t4_cycle'},
    {ts:_iso(190),sport:'NHL',market:'KXNHLGAME-26SEP-NSH',market_type:'NHL_MONEYLINE',band:'T2',p:0.52,price:0.55,edge:-0.0412,side:'NO',would_fire:false,src:'shadow'}],
   arms:[{arm:'MLB T4M-PROJ',last_ts:_iso(30),rows_today:412,age_s:30},{arm:'NHL T2',last_ts:_iso(190),rows_today:64,age_s:190}],
   books:[{book:'T1',initial:1000,realized_pnl:-124.44,drawdown:0.1244,limit:0.2,tripped:false,age_s:2700},
          {book:'T4M-PROJ',initial:1000,realized_pnl:-134.47,drawdown:0.1345,limit:0.2,tripped:false,age_s:60}],
   kelly:{T1:0,'T4M-PROJ':0},sizing_live:false,
   fire_rule:'WOULD-FIRE = fee-adjusted net edge > 0 (shadow computation; no order, stake $0)'},
  pipe_mtimes:{'PIPE-05  (23:30Z)':_iso(3600*7),'PIPE-05R (06:30Z)':_iso(3600*2),
    'PIPE-05FX(22:30Z)':_iso(3600*8),'PIPE-05C (Mon14Z)':_iso(3600*60)},
};

pull();
setInterval(tick,1000);
</script>
</body>
</html>
"""


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
