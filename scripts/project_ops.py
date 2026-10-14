#!/usr/bin/env python3
"""Operational sections for the /project page (Wave 56.3).

Reads ONLY what the host already has on disk (logs/, data/shadow/, exp_output/, the paper
portfolio JSONs) plus read-only `systemctl show` / `journalctl -k` / `git rev-parse`. Never
writes, never places or changes anything. Every row carries its source and age; anything
unreadable is None / "no data" -- never a zero or a placeholder.

Each builder takes (repo, now, run) and returns a section dict:
    {"source", "as_of", "rows": [...], "status": "ok|warn|bad|nodata"}
`status` feeds the at-a-glance health strip. Row dicts carry `state` in ok/warn/bad/nodata.
"""
from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable

KILL_SWITCH_DRAWDOWN = 0.20          # risk._HARD_LIMITS["max_drawdown_pct"]
MAX_CACHE_AGE_H = 26                 # run_mlb_pregame_shadow.MAX_CACHE_AGE_H
ERR_MARKERS = ("Traceback", "SystemExit", "HALT", "ERROR", "Error:")

# (label, log file under logs/, amber after h, red after h). Daily arms: one missed day is amber.
CRON_ARMS = [
    ("T1 MLB paper (daily 11:00Z)", "paper_mlb_cron.log", 26, 50),
    ("T4 MLB live cron", "t4_mlb_live_cron.log", 6, 26),
    ("MLB resolver (daily 06:30Z)", "resolve_mlb_cron.log", 26, 50),
    ("Shadow settle (daily 09:30Z)", "pregame_shadow_settle.log", 26, 50),
    ("NHL shadow (T1/T2/T3 + settle)", "nhl_shadow_cron.log", 6, 26),
    ("NFL shadow T1", "pregame_shadow_t1.log", 26, 50),
    ("NFL shadow T2", "pregame_shadow_t2.log", 26, 50),
    ("NFL shadow T3", "pregame_shadow_t3.log", 26, 50),
    ("MLB postseason shadow T1", "mlb_pregame_shadow_t1.log", 26, 50),
    ("MLB postseason shadow T2", "mlb_pregame_shadow_t2.log", 26, 50),
    ("MLB postseason shadow T3", "mlb_pregame_shadow_t3.log", 26, 50),
    ("NBA schedule backfill (daily 09:47Z)", "nba_shadow_backfill.log", 26, 50),
    ("NBA shadow T1", "nba_pregame_shadow_t1.log", 26, 50),
    ("NBA shadow T2", "nba_pregame_shadow_t2.log", 26, 50),
    ("NBA shadow T3", "nba_pregame_shadow_t3.log", 26, 50),
]

# (label, repo-relative path, amber h, red h)
FEEDS = [
    ("Price archive (cron log)", "logs/price_archive_cron.log", 2, 26),
    ("MLB feature refresh", "logs/mlb_feature_refresh.log", 26, 50),
]

PAPER_BOOKS = [
    ("MLB T1/T2/T3 paper", "logs/paper_portfolio_mlb.json"),
    ("MLB T4 paper", "logs/paper_portfolio_mlb_t4.json"),
    ("NFL game-market paper", "logs/paper_portfolio_t1_nfl_game_market.json"),
]

# SHADOW evidence clocks: (label, ledger dir, filename prefix, first look, judged n, source prereg)
EVIDENCE = [
    ("NHL", "data/shadow/nhl", "NHL_", None, 2500, "EXP-036"),
    ("NFL", "exp_output/PREGAME_SHADOW", "NFL_NFL_", 60, 150, "EXP-037"),
    ("MLB", "exp_output/PREGAME_SHADOW", "MLB_MLB_", 150, 150, "EXP-037"),
    ("NBA", "exp_output/PREGAME_SHADOW", "NBA_NBA_", 150, 400, "EXP-038"),
]

Run = Callable[[list[str]], "str | None"]


def default_run(argv: list[str]) -> str | None:
    try:
        p = subprocess.run(argv, capture_output=True, text=True, timeout=8)
    except (OSError, subprocess.SubprocessError):
        return None
    return p.stdout if p.returncode == 0 else None


def _iso(dt: datetime | None) -> str | None:
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ") if dt else None


def _mtime(p: Path) -> datetime | None:
    try:
        return datetime.fromtimestamp(p.stat().st_mtime, tz=timezone.utc)
    except OSError:
        return None


def age_hours(ts: datetime | None, now: datetime) -> float | None:
    return None if ts is None else max(0.0, (now - ts).total_seconds() / 3600)


def fmt_age(h: float | None) -> str:
    if h is None:
        return "no data"
    if h < 1:
        return f"{int(h * 60)}m ago"
    if h < 48:
        return f"{h:.1f}h ago"
    return f"{h / 24:.1f}d ago"


def _age_state(h: float | None, amber: float, red: float) -> str:
    if h is None:
        return "nodata"
    return "bad" if h > red else ("warn" if h > amber else "ok")


def _worst(states: list[str]) -> str:
    """Section status: bad > warn > ok. All-nodata is nodata; some nodata alongside data stays visible as warn."""
    if not states or all(s == "nodata" for s in states):
        return "nodata"
    if "bad" in states:
        return "bad"
    if "warn" in states or "nodata" in states:
        return "warn"
    return "ok"


def _tail(p: Path, n: int = 60) -> list[str] | None:
    try:
        with p.open("rb") as f:
            f.seek(0, 2)
            size = f.tell()
            f.seek(max(0, size - 24000))
            return f.read().decode("utf-8", "replace").splitlines()[-n:]
    except OSError:
        return None


def _nodata(source: str, why: str) -> dict:
    return {"source": source, "as_of": None, "rows": [], "status": "nodata", "nodata": why}


# ── Operations ──────────────────────────────────────────────────────────────

def sec_operations(repo: Path, now: datetime, run: Run = default_run) -> dict:
    logs = repo / "logs"
    if not logs.is_dir():
        return _nodata("logs/", "no logs/ directory on this host")
    rows = []
    for label, fn, amber, red in CRON_ARMS:
        p = logs / fn
        ts = _mtime(p)
        h = age_hours(ts, now)
        tail = _tail(p)
        errs = None if tail is None else any(m in ln for ln in tail[-6:] for m in ERR_MARKERS)
        state = _age_state(h, amber, red)
        # Last SUCCESS is only claimed when the final lines carry no error marker; otherwise unknown.
        success = ts if errs is False else None
        if errs and state == "ok":
            state = "warn"
        rows.append({"label": label, "source": f"logs/{fn}", "last_run": _iso(ts), "age_h": h,
                     "last_success": _iso(success), "tail_error": errs, "state": state,
                     "expect": f"amber >{amber}h, red >{red}h"})
    return {"source": "logs/*.log mtime + last 6 lines", "as_of": _iso(now), "rows": rows,
            "status": _worst([r["state"] for r in rows])}


# ── Data feeds ──────────────────────────────────────────────────────────────

def sec_feeds(repo: Path, now: datetime, run: Run = default_run) -> dict:
    rows = []
    meta = repo / "exp_output/MLB_GAME/cache_w47/games_current.meta.json"
    ts = None
    try:
        raw = json.loads(meta.read_text())["refreshed_at"]
        ts = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except (OSError, ValueError, KeyError, TypeError):
        ts = None
    h = age_hours(ts, now)
    rows.append({"label": f"MLB games-cache stamp (limit {MAX_CACHE_AGE_H}h)", "source": str(meta.relative_to(repo)),
                 "stamp": _iso(ts), "age_h": h, "state": _age_state(h, MAX_CACHE_AGE_H * 0.85, MAX_CACHE_AGE_H),
                 "expect": f"shadow refuses to log past {MAX_CACHE_AGE_H}h"})
    for label, rel, amber, red in FEEDS:
        t = _mtime(repo / rel)
        hh = age_hours(t, now)
        rows.append({"label": label, "source": rel, "stamp": _iso(t), "age_h": hh,
                     "state": _age_state(hh, amber, red), "expect": f"amber >{amber}h, red >{red}h"})
    return {"source": "exp_output/MLB_GAME/cache_w47 meta · logs mtimes", "as_of": _iso(now), "rows": rows,
            "status": _worst([r["state"] for r in rows])}


# ── Services & deploy (t4-mlb, GG-477; VPS HEAD) ────────────────────────────

def _parse_show(out: str | None) -> dict[str, str] | None:
    if not out:
        return None
    d = dict(ln.split("=", 1) for ln in out.splitlines() if "=" in ln)
    return d or None


def sec_services(repo: Path, now: datetime, run: Run = default_run) -> dict:
    rows = []
    for unit in ("t4-mlb", "pmbot-web-dashboard"):
        d = _parse_show(run(["systemctl", "show", f"{unit}.service", "-p", "NRestarts,ActiveState,ActiveEnterTimestamp"]))
        if d is None or "ActiveState" not in d:
            rows.append({"label": f"{unit} service", "source": f"systemctl show {unit}", "value": None, "state": "nodata"})
            continue
        n = int(d["NRestarts"]) if d.get("NRestarts", "").isdigit() else None
        active = d["ActiveState"] == "active"
        state = "bad" if not active else ("warn" if n else ("ok" if n == 0 else "nodata"))
        rows.append({"label": f"{unit} service", "source": f"systemctl show {unit}",
                     "value": f"{d['ActiveState']} · {n if n is not None else 'no data'} restarts since "
                              f"{d.get('ActiveEnterTimestamp') or 'no data'}", "state": state})
    oom = run(["journalctl", "-k", "--since", "-7days", "--no-pager", "-o", "short-iso"])
    if oom is None:
        rows.append({"label": "Kernel OOM kills, 7d (GG-477)", "source": "journalctl -k", "value": None, "state": "nodata"})
    else:
        evs = [ln for ln in oom.splitlines() if "out of memory: killed" in ln.lower()]
        last = None
        if evs:
            try:
                last = datetime.fromisoformat(evs[-1].split()[0]).astimezone(timezone.utc)
            except ValueError:
                last = None
        h = age_hours(last, now)
        state = "ok" if not evs else ("bad" if h is None or h <= 24 else "warn")
        rows.append({"label": "Kernel OOM kills, 7d (GG-477)", "source": "journalctl -k --since -7days",
                     "value": f"{len(evs)} killed" + (f" · latest {_iso(last)} ({fmt_age(h)})" if last else ""),
                     "state": state})
    head = (run(["git", "-C", str(repo), "rev-parse", "HEAD"]) or "").strip() or None
    main = (run(["git", "-C", str(repo), "rev-parse", "origin/main"]) or "").strip() or None
    if head and main:
        same = head == main
        rows.append({"label": "VPS HEAD vs origin/main", "source": "git rev-parse (local ref; fetched at deploy)",
                     "value": f"{head[:7]} vs {main[:7]} — {'in sync' if same else 'DIFFERENT'}",
                     "state": "ok" if same else "warn"})
    else:
        rows.append({"label": "VPS HEAD vs origin/main", "source": "git rev-parse", "value": None, "state": "nodata"})
    # W72.3 (GG-661/GG-668): deploy status, pending t4-mlb restart, service code vs box HEAD (alarm > 6h)
    dt_out = run([sys.executable, str(repo / "scripts" / "ops" / "deploy_truth.py"), "--proj", str(repo), "check"])
    if dt_out is None:
        rows.append({"label": "Deploy truth (W72.3)", "source": "scripts/ops/deploy_truth.py check", "value": None,
                     "state": "nodata"})
    else:
        lines = [ln.strip() for ln in dt_out.splitlines() if ln.strip().split(" ", 1)[0] in ("OK", "ALARM", "UNKNOWN")]
        alarms = [ln for ln in lines if ln.startswith("ALARM")]
        rows.append({"label": "Deploy truth (W72.3)", "source": "scripts/ops/deploy_truth.py check",
                     "value": (" | ".join(a[6:] for a in alarms) if alarms else
                               f"{len(lines)} check(s) OK -- services run the code on the box"),
                     "state": "bad" if alarms else ("warn" if any(ln.startswith("UNKNOWN") for ln in lines) else "ok")})
    last = None
    try:
        for ln in (repo / "logs" / "vps_deploy_decisions.jsonl").read_text().splitlines():
            rec = json.loads(ln)
            if rec.get("t4_mlb_verdict") not in (None, "", "none", "not_applicable"):
                last = rec
    except (OSError, ValueError):
        pass
    rows.append({"label": "Last deploy's t4-mlb restart decision", "source": "logs/vps_deploy_decisions.jsonl (GG-432)",
                 "value": (f"{last['t4_mlb_verdict']} at {last['ts']} ({str(last.get('after', ''))[:7]})" if last else None),
                 "state": "ok" if last else "nodata"})
    # the unconfirmable decision row must not drag the strip amber on its own
    return {"source": "systemctl · journalctl -k · git", "as_of": _iso(now), "rows": rows,
            "status": _worst([r["state"] for r in rows[:-1]])}


# ── Books & risk ────────────────────────────────────────────────────────────

def _load_json(p: Path) -> Any:
    try:
        return json.loads(p.read_text())
    except (OSError, ValueError):
        return None


def sec_books(repo: Path, now: datetime, run: Run = default_run) -> dict:
    rows = []
    for label, rel in PAPER_BOOKS:
        d = _load_json(repo / rel)
        if not isinstance(d, dict):
            rows.append({"label": label, "source": rel, "state": "nodata"})
            continue
        init, rpnl = d.get("initial_bankroll_usd"), d.get("total_realized_pnl")
        dd = max(0.0, -float(rpnl)) / float(init) if init and rpnl is not None and float(init) > 0 else None
        op = d.get("open_positions")
        lu = None
        try:
            lu = datetime.fromisoformat(str(d.get("last_updated")).replace("Z", "+00:00"))
        except ValueError:
            pass
        h = age_hours(lu, now)
        state = "nodata" if dd is None else ("bad" if dd >= KILL_SWITCH_DRAWDOWN else
                                             ("warn" if dd >= 0.8 * KILL_SWITCH_DRAWDOWN else "ok"))
        row = {"label": label, "source": rel, "bankroll": d.get("bankroll_usd"), "initial": init,
               "realized_pnl": rpnl, "drawdown": dd, "limit": KILL_SWITCH_DRAWDOWN,
               "open_positions": len(op) if isinstance(op, list) else None,
               "last_write": _iso(lu), "age_h": h, "state": state}
        if rel.endswith("paper_portfolio_mlb_t4.json"):
            # GG-527: T4M-PROJ execution evidence = CONFIRMED_FILLED rows only
            try:
                import sys as _sys
                _sys.path.insert(0, str(repo / "src"))
                from prediction_market_bot import t4_fill_status as tfs
                row["execution"] = tfs.execution_summary(
                    d.get("closed_positions") or [],
                    tfs.load_fill_status(repo / "logs" / "t4_mlb_fill_status.jsonl"))
            except Exception:  # never break the page
                row["execution"] = None
        rows.append(row)
    return {"source": "logs/paper_portfolio_*.json (paper ledgers, no real capital)", "as_of": _iso(now),
            "rows": rows, "status": _worst([r["state"] for r in rows])}


# ── Evidence clocks (SHADOW: counts only) ───────────────────────────────────

def _count_ledger(p: Path) -> tuple[int | None, datetime | None]:
    try:
        n = sum(1 for ln in p.open("rb") if ln.strip())
    except OSError:
        return None, None
    return n, _mtime(p)


def _settled_games(p: Path) -> int | None:
    try:
        seen = set()
        with p.open() as f:
            for ln in f:
                if not ln.strip():
                    continue
                try:
                    r = json.loads(ln)
                except ValueError:
                    continue
                seen.add(r.get("event_ticker") or r.get("market_ticker"))
        seen.discard(None)
        return len(seen)
    except OSError:
        return None


def sec_evidence(repo: Path, now: datetime, run: Run = default_run) -> dict:
    rows = []
    for sport, rel, prefix, first, judged, prereg in EVIDENCE:
        d = repo / rel
        files = sorted(f for f in d.glob(f"{prefix}*.jsonl")) if d.is_dir() else []
        if not files:
            rows.append({"cell": f"{sport} (no ledgers)", "source": rel, "state": "nodata", "sport": sport,
                         "judged": judged, "first": first, "prereg": prereg})
            continue
        for f in files:
            n, ts = _count_ledger(f)
            sf = d / "settled" / f.name
            sg = _settled_games(sf) if sf.is_file() else None
            rows.append({"cell": f.stem, "sport": sport, "source": f"{rel}/{f.name}", "rows": n,
                         "settled_games": sg if sg is not None else (0 if n is not None and not sf.is_file() else None),
                         "first": first, "judged": judged, "prereg": prereg, "last_row": _iso(ts),
                         "age_h": age_hours(ts, now), "state": "ok" if n else "nodata"})
    return {"source": "SHADOW ledgers + settled/ copies (counts only; no score, no Brier)", "as_of": _iso(now),
            "rows": rows, "status": "ok" if any(r["state"] == "ok" for r in rows) else "nodata"}


SECTIONS = {"operations": sec_operations, "feeds": sec_feeds, "services": sec_services,
            "books": sec_books, "evidence": sec_evidence}


def build_ops(repo: Path, now: datetime | None = None, run: Run = default_run) -> dict[str, dict]:
    now = now or datetime.now(timezone.utc)
    out = {}
    for k, fn in SECTIONS.items():
        try:
            out[k] = fn(Path(repo), now, run)
        except Exception as e:  # one unreadable source never blanks the page
            out[k] = _nodata(k, f"{type(e).__name__}: {e}")
    return out
