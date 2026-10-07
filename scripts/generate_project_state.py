#!/usr/bin/env python3
"""Project-state snapshot for the analytical dashboard (Wave 47 / 47.1 D6 h).

Reads tracked files, git, live imports of the repo and (W56.3, scripts/project_ops.py) the
host's own on-disk logs/ledgers plus read-only systemctl/journalctl. Writes one JSON and,
optionally, a static offline HTML page. No network, no live calls, no writes into
exp_output/. Every item carries the repo-relative `source` it was read from, and
every section carries its own `as_of`.

    python3 scripts/generate_project_state.py                 # JSON to stdout
    python3 scripts/generate_project_state.py --json out.json
    python3 scripts/generate_project_state.py --html "Visual Dashboard.html"

Library use (served at /project by scripts/web_dashboard.py):
    from generate_project_state import build_state, render_html
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
import project_ops  # noqa: E402

GAP_LOG = "03_DECISIONS/GOVERNANCE_GAP_LOG.md"
DECISION_LOG = "03_DECISIONS/DECISION_LOG/DECISION_LOG.md"
QUEUE = "04_EXECUTION/ACTIVE_QUEUE.md"
QUEUE_ARCHIVE = "04_EXECUTION/ACTIVE_QUEUE_ARCHIVE.md"
EXP_DIR = "05_RESEARCH_EXPERIMENTS"
RESULTS_DIR = "05_RESEARCH_EXPERIMENTS/RESULTS_SUMMARIES"
ADR_DIR = "03_DECISIONS"
SEVERITY_ORDER = ["CRITICAL", "HIGH", "MEDIUM", "LOW", "UNSPECIFIED"]

# (label, repo-relative path). Newest record = last line's "ts"/"timestamp"/"game_date" if JSONL,
# or max "game_date" column if CSV. Missing path -> "awaiting".
DATA_STORES = [
    ("MLB feature matrix", "exp_output/MLB/mlb_feature_matrix.csv"),
    ("Price archive (shared)", "exp_output/PRICE_ARCHIVE"),
    ("Board survey G2 raw (KXMLBTOTAL)", "exp_output/BOARD_SURVEY_SPORTS_G2/KXMLBTOTAL"),
    ("EXP-032 cost surface", "exp_output/EXP-032-EXECUTION-COST-SURFACE"),
    ("EXP-033 coherence", "exp_output/EXP-033-MULTILEG-COHERENCE"),
    ("EXP-034 non-sports control", "exp_output/EXP-034-NONSPORTS-CONTROL"),
    ("Validated Kalshi history", "exp_output/KALSHI_HISTORY"),
]


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(dt: datetime | None = None) -> str:
    return (dt or _now()).strftime("%Y-%m-%dT%H:%M:%SZ")


def _git(repo: Path, *args: str) -> str | None:
    try:
        r = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, timeout=20)
        return r.stdout.strip() if r.returncode == 0 else None
    except Exception:
        return None


def _read(repo: Path, rel: str) -> str | None:
    try:
        return (repo / rel).read_text(encoding="utf-8", errors="replace")
    except Exception:
        return None


def _sec(source: str, as_of: str, **kw: Any) -> dict:
    return {"source": source, "as_of": as_of, **kw}


def _awaiting(source: str, why: str) -> dict:
    return {"source": source, "as_of": None, "awaiting": why}


def _file_as_of(repo: Path, rel: str) -> str:
    """Last commit time of the file (tracked-file as-of), falling back to mtime."""
    t = _git(repo, "log", "-1", "--format=%cI", "--", rel)
    if t:
        return t
    try:
        return _iso(datetime.fromtimestamp((repo / rel).stat().st_mtime, tz=timezone.utc))
    except Exception:
        return _iso()


# ── sections ────────────────────────────────────────────────────────────────

def sec_git(repo: Path) -> dict:
    sha = _git(repo, "rev-parse", "origin/main") or _git(repo, "rev-parse", "HEAD")
    if not sha:
        return _awaiting("git rev-parse origin/main", "not a git checkout")
    head = _git(repo, "rev-parse", "HEAD")
    subj = _git(repo, "log", "-1", "--format=%s", sha) or ""
    when = _git(repo, "log", "-1", "--format=%cI", sha)
    unmerged = _git(repo, "branch", "-r", "--no-merged", "origin/main")
    branches = [b.strip() for b in (unmerged or "").splitlines() if b.strip() and "->" not in b]
    return _sec("git rev-parse origin/main · git branch -r --no-merged origin/main", when or _iso(),
                origin_main=sha, origin_main_short=sha[:7], head=head, subject=subj,
                unmerged_branches=len(branches), unmerged_sample=branches[:12])


def sec_registry(repo: Path) -> dict:
    src = "src/prediction_market_bot/c5_execution/market_type_registry.py"
    try:
        sys.path.insert(0, str(repo / "src"))
        from prediction_market_bot.c5_execution import market_type_registry as R  # type: ignore
        cells = R.MARKET_TYPE_REGISTRY
        cells = list(cells.values()) if isinstance(cells, dict) else list(cells)
    except Exception as e:
        return _awaiting(src, f"import failed: {type(e).__name__}")
    counts: dict[str, int] = {}
    for c in cells:
        st = getattr(c.status, "name", str(c.status)).lower()
        counts[st] = counts.get(st, 0) + 1
    return _sec(src, _file_as_of(repo, src), total=len(cells), counts=counts)


def sec_governance(repo: Path) -> dict:
    txt = _read(repo, GAP_LOG)
    if txt is None:
        return _awaiting(GAP_LOG, "file missing")
    blocks = re.split(r"(?m)^(?=### GG-\d)", txt)
    gaps = []
    for b in blocks:
        m = re.match(r"### (GG-\d+)\s*(?:[—-]\s*)?(.*)", b)
        if not m:
            continue
        st = re.search(r"(?m)^\*\*Status:\*\*\s*([A-Z][A-Z \-]*)", b)
        sv = re.search(r"\*\*Severity:\*\*\s*([A-Z]+)", b)
        dt = re.search(r"(20\d\d-\d\d-\d\d)", b)
        gaps.append({"id": m.group(1), "title": m.group(2).strip()[:140],
                     "status": (st.group(1).strip() if st else "UNKNOWN"),
                     "severity": (sv.group(1) if sv else "UNSPECIFIED"),
                     "first_date": dt.group(1) if dt else None})
    opn = [g for g in gaps if g["status"] == "OPEN"]
    by_sev = {s: 0 for s in SEVERITY_ORDER}
    for g in opn:
        by_sev[g["severity"] if g["severity"] in by_sev else "UNSPECIFIED"] += 1
    now = _now()
    for g in opn:
        if g["first_date"]:
            try:
                g["age_days"] = (now - datetime.strptime(g["first_date"], "%Y-%m-%d").replace(tzinfo=timezone.utc)).days
            except ValueError:
                g["age_days"] = None
        else:
            g["age_days"] = None
    nums = sorted(opn, key=lambda g: -int(g["id"][3:]))
    return _sec(GAP_LOG, _file_as_of(repo, GAP_LOG), live_entries=len(gaps), open=len(opn),
                by_severity=by_sev, newest=nums[:8],
                oldest=sorted([g for g in opn if g["age_days"] is not None], key=lambda g: -g["age_days"])[:5])


def sec_decisions(repo: Path) -> dict:
    out: dict[str, Any] = {"source": DECISION_LOG}
    txt = _read(repo, DECISION_LOG)
    if txt is None:
        out.update(as_of=None, awaiting="DECISION_LOG missing")
        return out
    heads = re.findall(r"(?m)^## (20\d\d-\d\d-\d\d) — (.*)$", txt)
    out.update(as_of=_file_as_of(repo, DECISION_LOG), entries=len(heads),
               latest=[{"date": d, "title": t[:160]} for d, t in heads[-8:][::-1]])
    adrs = []
    for p in sorted((repo / ADR_DIR).glob("ADR-*.md")):
        head = p.read_text(encoding="utf-8", errors="replace")[:1500]
        m = re.search(r"(?m)^\*\*Status:\*\*\s*([A-Z]+)", head)
        t = re.match(r"# (ADR-\d+)[:\s]+(.*)", head)
        adrs.append({"id": t.group(1) if t else p.stem[:8], "title": (t.group(2) if t else p.stem)[:110],
                     "status": m.group(1) if m else "UNKNOWN", "source": f"{ADR_DIR}/{p.name}"})
    cnt: dict[str, int] = {}
    for a in adrs:
        cnt[a["status"]] = cnt.get(a["status"], 0) + 1
    out.update(adr_counts=cnt, adr_proposed=[a for a in adrs if a["status"] == "PROPOSED"])
    return out


def sec_experiments(repo: Path) -> dict:
    items = []
    for p in sorted((repo / EXP_DIR).glob("EXP*PREREGISTRATION*.md")):
        rel = f"{EXP_DIR}/{p.name}"
        head = p.read_text(encoding="utf-8", errors="replace")[:3000]
        title = re.match(r"# (.*)", head)
        first = _git(repo, "log", "--diff-filter=A", "--format=%h %cI", "--", rel)
        sha, when = (first.splitlines()[-1].split(" ", 1) if first else ("", ""))
        full = p.name.split("_PREREGISTRATION")[0]          # e.g. EXP035_GATE2 / EXP035_BOARD_SURVEY_SPORTS
        eid = full
        base = re.match(r"(EXP\d+)", p.name)
        base = base.group(1) if base else full
        siblings = [q.name.split("_PREREGISTRATION")[0] for q in (repo / EXP_DIR).glob(f"{base}*PREREGISTRATION*.md")]
        verdict, vsrc = None, None
        for r in sorted((repo / RESULTS_DIR).glob(f"{base}*.md")):
            tok = full[len(base):].strip("_")
            if len(siblings) > 1 and tok.split("_")[0] not in ("BOARD",) and tok.split("_")[0] not in r.name.upper():
                continue
            if len(siblings) > 1 and tok.split("_")[0] == "BOARD" and "GATE2" in r.name.upper():
                continue
            h = r.read_text(encoding="utf-8", errors="replace")[:2500]
            h1 = (re.match(r"# (.*)", h) or [None, ""])[1]
            m = re.search(r"(?im)^\*\*(?:Standing )?verdict[^\n]{0,200}", h) or re.search(r"(?im)^verdict:[^\n]{0,200}", h)
            verdict = (h1 if re.search(r"(?i)RESULT|PASS|FAIL|VERDICT", h1) else (m.group(0) if m else h1)).strip(" *#")[:220]
            vsrc = f"{RESULTS_DIR}/{r.name}"
        items.append({"id": eid, "question": (title.group(1) if title else p.stem)[:150],
                      "prereg_sha": sha, "prereg_date": when[:10], "verdict": verdict or "no results summary found",
                      "source": rel, "verdict_source": vsrc})
    if not items:
        return _awaiting(EXP_DIR, "no pre-registrations found")
    return _sec(f"{EXP_DIR}/EXP*PREREGISTRATION*.md · {RESULTS_DIR}/", _iso(), items=items)


def sec_queue(repo: Path) -> dict:
    q = _read(repo, QUEUE)
    a = _read(repo, QUEUE_ARCHIVE)
    if q is None and a is None:
        return _awaiting(QUEUE, "files missing")
    waves = []
    for src, txt in ((QUEUE, q), (QUEUE_ARCHIVE, a)):
        for m in re.finditer(r"(?m)^## (Wave \d+[^\n]*)$", txt or ""):
            waves.append({"line": m.group(1)[:260], "source": src})
    needs = []
    if q:
        m = re.search(r"(?ms)^## Needs your decision\s*(.*?)^---", q)
        if m:
            for row in re.findall(r"(?m)^\| \*\*(.+?)\*\* *\|\s*(.*?)\s*\|", m.group(1)):
                needs.append({"item": re.sub(r"\*+", "", row[0])[:90], "plain": row[1][:200]})
    return _sec(f"{QUEUE} · {QUEUE_ARCHIVE}", _file_as_of(repo, QUEUE), waves=waves[:10], needs_decision=needs)


def _store_stats(p: Path) -> dict:
    files = [p] if p.is_file() else [f for f in p.rglob("*") if f.is_file()] if p.is_dir() else []
    if not files:
        return {}
    size = sum(f.stat().st_size for f in files)
    newest_mtime = max(f.stat().st_mtime for f in files)
    rows, newest = None, None
    big = max(files, key=lambda f: f.stat().st_size)
    try:
        if big.suffix == ".csv":
            with open(big, newline="", encoding="utf-8", errors="replace") as fh:
                rd = csv.DictReader(fh)
                rows, dates = 0, []
                for r in rd:
                    rows += 1
                    if r.get("game_date"):
                        dates.append(r["game_date"])
                newest = max(dates) if dates else None
        elif big.suffix == ".jsonl":
            rows = 0
            last = ""
            with open(big, encoding="utf-8", errors="replace") as fh:
                for ln in fh:
                    if ln.strip():
                        rows += 1
                        last = ln
            try:
                j = json.loads(last)
                newest = j.get("ts") or j.get("timestamp") or j.get("game_date")
            except Exception:
                newest = None
    except Exception:
        pass
    return {"files": len(files), "bytes": size, "rows": rows, "newest_record": newest,
            "newest_mtime": _iso(datetime.fromtimestamp(newest_mtime, tz=timezone.utc))}


def sec_data(repo: Path) -> dict:
    out = []
    for label, rel in DATA_STORES:
        st = _store_stats(repo / rel)
        out.append({"label": label, "source": rel, **(st if st else {"awaiting": "path not present in this checkout"})})
    return _sec("exp_output/ (filesystem stat; read-only)", _iso(), stores=out)


CALIB_DIR = "exp_output/CALIBRATION"


def sec_calibration(repo: Path) -> dict:
    """Newest engine_<UTC>.json written by scripts/calibration_engine.py. Read-only; no score is computed here."""
    files = sorted((repo / CALIB_DIR).glob("engine_*.json")) if (repo / CALIB_DIR).is_dir() else []
    if not files:
        return _awaiting(CALIB_DIR, "the first calibration-engine run (no engine_<UTC>.json yet)")
    d = json.loads(files[-1].read_text())
    return _sec(f"{CALIB_DIR}/{files[-1].name}", d.get("generated"), **{k: d[k] for k in ("cells", "historical", "summary", "gg_open")})


def build_state(repo: Path | str = REPO) -> dict:
    repo = Path(repo)
    secs = {"calibration": sec_calibration, "git": sec_git, "registry": sec_registry, "governance": sec_governance,
            "decisions": sec_decisions, "experiments": sec_experiments, "queue": sec_queue, "data": sec_data}
    out: dict[str, Any] = {"generated": _iso(), "repo": repo.name, "sections": {}}
    for k, fn in secs.items():
        try:
            out["sections"][k] = fn(repo)
        except Exception as e:  # one broken source never blanks the page
            out["sections"][k] = _awaiting(k, f"{type(e).__name__}: {e}")
    out["ops"] = project_ops.build_ops(repo)
    return out


# ── HTML (analytical page: own look, separate from the black Live Terminal) ─

_CSS = """:root{--bg:#fafaf7;--fg:#1c1c1a;--mut:#6b6b64;--line:#dcdcd4;--card:#fff;--acc:#1f5f8b;--bad:#b3261e;--ok:#1b7a3d;--warn:#a15c00}
@media (prefers-color-scheme:dark){:root{--bg:#161615;--fg:#e8e8e2;--mut:#9a9a92;--line:#33332f;--card:#1d1d1b;--acc:#7db7e0;--bad:#ff8a80;--ok:#6fd08c;--warn:#f0b24a}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--fg);font:14px/1.5 -apple-system,Segoe UI,sans-serif}
header{padding:14px 20px;border-bottom:1px solid var(--line);display:flex;gap:16px;flex-wrap:wrap;align-items:baseline}
header h1{font-size:17px;margin:0}header .st{color:var(--mut);font-size:12.5px}
main{max-width:1100px;margin:0 auto;padding:16px 20px 60px}
section{background:var(--card);border:1px solid var(--line);border-radius:6px;margin:14px 0;padding:12px 16px}
h2{font-size:14px;margin:0 0 4px}.asof{color:var(--mut);font-size:11.5px;margin-bottom:8px}
table{border-collapse:collapse;width:100%;font-size:13px}td,th{text-align:left;padding:3px 8px;border-bottom:1px solid var(--line);vertical-align:top}
a{color:var(--acc)}code{font-size:12px}.aw{color:var(--mut);font-style:italic}.bad{color:var(--bad)}.ok{color:var(--ok)}
.num,.mono{font-variant-numeric:tabular-nums;font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:12.5px}
.warn{color:var(--warn)}.stale{opacity:.55}.nd{color:var(--mut);font-style:italic}
.strip{display:flex;flex-wrap:wrap;gap:8px;margin:14px 0}
.pill{display:inline-flex;gap:6px;align-items:center;border:1px solid var(--line);border-left-width:5px;border-radius:6px;
background:var(--card);padding:5px 10px;font-size:12.5px;text-decoration:none;color:var(--fg)}
.pill.ok{border-left-color:var(--ok)}.pill.warn{border-left-color:var(--warn)}.pill.bad{border-left-color:var(--bad)}
.pill.neu{border-left-color:var(--line)}.pill.nodata{border-left-color:var(--line);color:var(--mut)}.pill .v{font-weight:600}
.tag{border:1px solid var(--line);border-radius:3px;padding:0 5px;font-size:11px;color:var(--mut)}
.scroll{overflow-x:auto}
.bar{display:inline-block;width:70px;height:7px;background:var(--line);border-radius:3px;vertical-align:middle;overflow:hidden}
.bar i{display:block;height:100%;background:var(--acc)}
@media (max-width:640px){main{padding:10px 10px 40px}section{padding:10px}header{padding:10px}td,th{padding:3px 5px}}"""


def _md(x: Any) -> str:
    """Strip markdown emphasis markers from queue prose before it is shown as plain text (T-621)."""
    return str(x).replace("**", "")


def _e(x: Any) -> str:
    return (str(x).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;"))


def _lnk(src: str | None, prefix: str) -> str:
    if not src:
        return ""
    first = src.split(" · ")[0].split(" ")[0]
    if prefix is not None and "/" in first and not first.startswith("git"):
        return f'<a href="{_e(prefix + first)}"><code>{_e(src)}</code></a>'
    return f"<code>{_e(src)}</code>"


# ── W56.3 operational sections ──────────────────────────────────────────────

_STATE_WORD = {"ok": "healthy", "warn": "warning", "bad": "FAILING", "nodata": "no data"}


def _cell(state: str, text: Any, dim: bool = False) -> str:
    cls = {"ok": "ok", "warn": "warn", "bad": "bad", "nodata": "nd"}.get(state, "")
    return f"<span class='{cls}{' stale' if dim else ''}'>{_e(text)}</span>"


def _ago(row: dict) -> str:
    return project_ops.fmt_age(row.get("age_h"))


def _dd(r: dict) -> str:
    return f"{r['drawdown']:.1%} / {r['limit']:.0%}" if r.get("drawdown") is not None else "no data"


def _usd(x: Any) -> str:
    return f"${float(x):,.2f}" if isinstance(x, (int, float)) else "no data"


def _ops_tables(ops: dict, head: Any, aw: Any) -> dict[str, str]:
    """HTML for each new section, keyed by section id. A dead section says why; it never shows zeros."""
    out: dict[str, str] = {}

    def wrap(id_: str, title: str, sec: dict, body: str, note: str = "") -> str:
        inner = (f"<div class='nd'>no data — {_e(sec['nodata'])}</div>" if sec.get("nodata") else body)
        return f"<section id='{id_}'>{head(title, sec)}{note}<div class='scroll'>{inner}</div></section>"

    o = ops.get("operations", {})
    body = "<table><tr><th>Arm</th><th>Last run</th><th>Last success</th><th>Source</th></tr>" + "".join(
        f"<tr class='{'stale' if r['state'] in ('warn', 'bad') else ''}'><td>{_cell(r['state'], '● ')}{_e(r['label'])}</td>"
        f"<td class='num'>{_e(r['last_run'] or 'no data')} <span class='nd'>({_ago(r)})</span></td>"
        f"<td class='num'>{_e(r['last_success'] or 'no data — last lines show an error' if r.get('tail_error') else (r['last_success'] or 'no data'))}</td>"
        f"<td><code>{_e(r['source'])}</code> <span class='tag'>{_e(r['expect'])}</span></td></tr>"
        for r in o.get("rows", [])) + "</table>"
    out["operations"] = wrap("operations", "Operations — cron arms", o, body,
                             "<div class='asof'>Last run = log mtime. Last success is shown only when the log's final lines carry no error marker.</div>")

    f = ops.get("feeds", {})
    body = "<table><tr><th>Feed</th><th>Stamp</th><th>Age</th><th>Source</th></tr>" + "".join(
        f"<tr><td>{_cell(r['state'], '● ')}{_e(r['label'])}</td><td class='num'>{_e(r['stamp'] or 'no data')}</td>"
        f"<td class='num'>{_cell(r['state'], _ago(r))}</td><td><code>{_e(r['source'])}</code> <span class='tag'>{_e(r['expect'])}</span></td></tr>"
        for r in f.get("rows", [])) + "</table>"
    out["feeds"] = wrap("feeds", "Data-feed freshness", f, body)

    sv = ops.get("services", {})
    body = "<table><tr><th>Item</th><th>Value</th><th>Source</th></tr>" + "".join(
        f"<tr><td>{_cell(r['state'], '● ')}{_e(r['label'])}</td>"
        f"<td class='num'>{_cell(r['state'], r['value'] if r.get('value') else 'no data')}"
        f"{(' <span class=nd>' + _e(r['note']) + '</span>') if r.get('note') else ''}</td>"
        f"<td><code>{_e(r['source'])}</code></td></tr>" for r in sv.get("rows", [])) + "</table>"
    out["services"] = wrap("services", "Services, host health & deploy", sv, body)

    b = ops.get("books", {})
    body = ("<table><tr><th>Paper ledger</th><th>Bankroll</th><th>Realized P&amp;L</th><th>Drawdown vs 20% kill</th>"
            "<th>Open</th><th>Last write</th></tr>" + "".join(
                f"<tr class='{'stale' if (r.get('age_h') or 0) > 72 else ''}'><td>{_cell(r['state'], '● ')}{_e(r['label'])}<br><code>{_e(r['source'])}</code></td>"
                + ("<td colspan=5 class='nd'>no data — ledger unreadable</td>" if r.get("bankroll") is None and r["state"] == "nodata" else
                   f"<td class='num'>{_usd(r.get('bankroll'))} <span class='nd'>of {_usd(r.get('initial'))}</span></td>"
                   f"<td class='num'>{_usd(r.get('realized_pnl'))}</td>"
                   f"<td class='num'>{_cell(r['state'], _dd(r))}</td>"
                   f"<td class='num'>{_e(r['open_positions'] if r.get('open_positions') is not None else 'no data')}</td>"
                   f"<td class='num'>{_e(r['last_write'] or 'no data')} <span class='nd'>({_ago(r)})</span></td>") + "</tr>"
                for r in b.get("rows", [])) + "</table>")
    out["books"] = wrap("books", "Books & risk — paper ledgers", b, body,
                        "<div class='asof'>Paper money only. Drawdown is realized loss over initial bankroll, the quantity the kill switch reads. "
                        "A band at kelly_fraction 0.0 stakes $0 by design (ADR-0048).</div>"
                        "<div class='asof nd'>Not listed above: the NFL game-market paper book is <b>ARCHIVED</b> (frozen 2026-10-07, GG-490). "
                        "Final: realized P&amp;L <span class='num'>-$160.66</span> over 840 closed + 4 open (future games); "
                        "820 positions booked from Kalshi settlement under ADR-0071. "
                        "Source: <code>logs/w58_1_nfl_booking_report.json</code> (VPS), 2026-10-07. Paper money only, shadow.</div>")

    ev = ops.get("evidence", {})
    body = ("<table><tr><th>SHADOW cell</th><th>Rows</th><th>Settled games</th><th>Judged n (first look → judged)</th>"
            "<th>Last row</th></tr>" + "".join(
                f"<tr class='{'stale' if (r.get('age_h') or 0) > 72 else ''}'><td>{_e(r['cell'])} <span class='tag'>SHADOW · not trading</span></td>"
                + ("<td colspan=4 class='nd'>no data — no ledger found</td>" if r["state"] == "nodata" else
                   f"<td class='num'>{_e(r['rows'])}</td>"
                   f"<td class='num'>{_e(r['settled_games'] if r.get('settled_games') is not None else 'no data')}</td>"
                   f"<td class='num'>{_e(r['settled_games'] if r.get('settled_games') is not None else '?')} of "
                   f"{_e((str(r['first']) + ' → ') if r.get('first') else '')}{_e(r['judged'])} <span class='nd'>({_e(r['prereg'])})</span></td>"
                   f"<td class='num'>{_e(r['last_row'] or 'no data')} <span class='nd'>({_ago(r)})</span></td>") + "</tr>"
                for r in ev.get("rows", [])) + "</table>")
    out["evidence"] = wrap("evidence", "Evidence clocks — SHADOW cells", ev, body,
                           "<div class='asof'>Counts only: no score, no Brier. Nothing here places or sizes an order. "
                           "MLB 2026 postseason is too small to reach its judged n; the clock that matters is 2027.</div>")
    return out


def _calibration_html(sec: dict, head: Any) -> str:
    """Per sport, one row per cell. Scores appear only on cells the engine itself released (no `scores` key = none)."""
    if sec.get("awaiting") or not sec.get("summary"):
        sec = {**sec, "awaiting": sec.get("awaiting") or "the first calibration-engine run"}
        return f"<section id='calibration'>{head('Calibration — SHADOW cells', sec)}<div class='nd'>no data — awaiting {_e(sec['awaiting'])}</div></section>"
    sm = sec["summary"]
    try:
        age_h = (_now() - datetime.fromisoformat(str(sec["as_of"]).replace("Z", "+00:00"))).total_seconds() / 3600
    except Exception:
        age_h = None
    stale = age_h is not None and age_h > 36
    top = (f"<p class='num{' stale' if stale else ''}'><b>{sm['logging']}</b> of {sm['cells']} cells logging · "
           f"<b>{sm['with_outcomes']}</b> have outcomes · <b>{sm['reached_look']}</b> reached a look"
           f"{' · <span class=warn>engine output is ' + project_ops.fmt_age(age_h) + ' old</span>' if stale else ''}</p>")
    rows = []
    for sport in ("NFL", "MLB", "NHL"):
        cs = [c for c in sec["cells"] if c["sport"] == sport]
        if not cs:
            continue
        rows.append(f"<tr><th colspan=6>{sport} <span class='tag'>SHADOW · $0 stake · not trading</span></th></tr>")
        for c in cs:
            st = c["status"]
            cls = {"JUDGED": "ok", "PRELIMINARY": "warn"}.get(st, "nd")
            pct = c.get("pct_to_first_look")
            bar = (f"<span class='bar'><i style='width:{min(pct, 100)}%'></i></span> <span class='num'>{pct}%</span>"
                   if pct is not None else "<span class='nd'>no look registered</span>")
            pj = c["projection"]
            sc = c.get("scores")
            score = ("<span class='nd'>none released</span>" if not sc else
                     (f"<span class='tag'>{_e(c.get('scores_label', 'JUDGED'))}</span> Brier model {sc['brier_model']:.4f} / "
                      f"market {sc['brier_market']:.4f} · Δ vs mkt {sc['delta_brier_vs_market']['mean']:+.4f} "
                      f"[{sc['delta_brier_vs_market']['ci95'][0]:+.4f}, {sc['delta_brier_vs_market']['ci95'][1]:+.4f}]"))
            rows.append(f"<tr title='source: {_e(c['source'])}'><td>{_e(c['market_type'])} {_e(c['band'])}</td><td><span class='{cls}'>{_e(c['status_text'])}</span></td>"
                        f"<td class='num'>{c['rows']} rows · {c['settled_games']} games</td><td>{bar}</td>"
                        f"<td class='num'>{_e(pj['date'] or pj['note'])}</td><td class='num'>{score}</td>"
                        f"</tr>")
    hist = "".join(f"<tr><td>{_e(h['family'])}</td><td><span class='ok'>HISTORICAL</span></td>"
                   f"<td colspan=4>scored in Waves 38-44 — <code>{_e(h['source'])}</code></td></tr>" for h in sec.get("historical", []))
    body = ("<table><tr><th>Cell</th><th>Status</th><th>Counts</th><th>Progress to first look</th><th>Projected look</th>"
            f"<th>Scores (only where allowed)</th></tr>{''.join(rows)}{hist}</table>")
    note = ("<div class='asof'>Each cell follows its own pre-registration (EXP-036 NHL, EXP-037 NFL/MLB). SEALED cells show counts only. "
            "NHL T3 stays sealed while GG-401 is open. MLB 2026 postseason rows are counted, never scored; the clock that matters is 2027-03-01. "
            "Projection = trailing settle rate; early-season rates are noisy.</div>")
    return f"<section id='calibration' class='{'stale' if stale else ''}'>{head('Calibration — SHADOW cells', sec)}{top}{note}<div class='scroll'>{body}</div></section>"


def _strip(S: dict, ops: dict) -> str:
    pills = []
    for id_, name in (("operations", "Cron arms"), ("feeds", "Data feeds"), ("services", "Services & deploy"),
                      ("books", "Books & risk"), ("evidence", "Evidence clocks")):
        st = ops.get(id_, {}).get("status", "nodata")
        pills.append(f"<a class='pill {st}' href='#{id_}'>{_e(name)} <span class='v'>{_e(_STATE_WORD[st])}</span></a>")
    gv, qu, ex = S.get("governance", {}), S.get("queue", {}), S.get("experiments", {})
    cb = S.get("calibration", {})
    neutral = [
        ("calibration", "Calibration", (f"{cb['summary']['reached_look']} of {cb['summary']['cells']} at a look"
                                        if cb.get("summary") else "no data")),
        ("verdicts", "Verdicts", f"{len(ex.get('items', []))} EXP" if not ex.get("awaiting") else "no data"),
        ("governance", "Gaps", f"{gv.get('open')} open" if not gv.get("awaiting") else "no data"),
        ("queue", "Your desk", f"{len(qu.get('needs_decision', []))} to decide" if not qu.get("awaiting") else "no data"),
    ]
    for id_, name, val in neutral:
        pills.append(f"<a class='pill neu' href='#{id_}'>{_e(name)} <span class='v num'>{_e(val)}</span></a>")
    return "<div class='strip'>" + "".join(pills) + "</div>"


def render_html(state: dict, *, live_nav: str | None = None, link_prefix: str | None = "./", static: bool = False) -> str:
    S = state["sections"]
    g = S.get("git", {})
    sha = g.get("origin_main_short", "unknown")
    stamp = (f"as of origin/main {sha}, generated {state['generated']}" if not g.get("awaiting")
             else f"generated {state['generated']} (git unavailable)")

    def head(title: str, sec: dict) -> str:
        return (f"<h2>{_e(title)}</h2><div class='asof'>as of {_e(sec.get('as_of') or 'n/a')} · "
                f"source {_lnk(sec.get('source'), link_prefix)}</div>")

    def aw(sec: dict) -> str | None:
        return f"<div class='aw'>awaiting {_e(sec['awaiting'])}</div>" if sec.get("awaiting") else None

    parts: list[str] = []
    ops = state.get("ops", {})
    ops_html = _ops_tables(ops, head, aw)
    parts.append(_strip(S, ops))
    for k in ("operations", "feeds", "services", "books", "evidence"):
        parts.append(ops_html[k])
    parts.append(_calibration_html(S.get("calibration", _awaiting("calibration", "engine")), head))
    # verdict board = experiments
    ex = S.get("experiments", {})
    body = aw(ex) or ("<table><tr><th>EXP</th><th>Question</th><th>Pre-reg</th><th>Verdict</th></tr>" + "".join(
        f"<tr><td>{_e(i['id'])}</td><td>{_lnk(i['source'], link_prefix) and _e(i['question'])}</td>"
        f"<td class='num'>{_e(i['prereg_sha'])} {_e(i['prereg_date'])}</td>"
        f"<td>{_lnk(i['verdict_source'], link_prefix) + ' ' if i['verdict_source'] else ''}{_e(i['verdict'])}</td></tr>"
        for i in ex.get("items", [])) + "</table>")
    parts.append(f"<section id='verdicts'>{head('Verdict board & evidence ledger', ex)}{body}</section>")

    rg = S.get("registry", {})
    body = aw(rg) or ("<table><tr><th>Status</th><th>Cells</th></tr>" + "".join(
        f"<tr><td>{_e(k)}</td><td class='num'>{v}</td></tr>" for k, v in sorted(rg.get("counts", {}).items()))
        + f"<tr><th>total</th><th class='num'>{rg.get('total')}</th></tr></table>")
    parts.append(f"<section id='cells'>{head('Cell matrix (registry)', rg)}{body}</section>")

    gv = S.get("governance", {})
    body = aw(gv) or (f"<p><b class='num'>{gv.get('open')}</b> OPEN of {gv.get('live_entries')} live gaps. "
                      + " · ".join(f"{k} <span class='num'>{v}</span>" for k, v in gv.get("by_severity", {}).items())
                      + "</p><table><tr><th>Newest OPEN</th><th>Severity</th><th>Age (d)</th></tr>" + "".join(
                          f"<tr><td>{_e(x['id'])} — {_e(x['title'])}</td><td>{_e(x['severity'])}</td>"
                          f"<td class='num'>{_e(x.get('age_days') if x.get('age_days') is not None else '—')}</td></tr>"
                          for x in gv.get("newest", [])) + "</table>")
    parts.append(f"<section id='governance'>{head('Governance gaps', gv)}{body}</section>")

    dc = S.get("decisions", {})
    body = aw(dc) or ("<p>ADRs: " + ", ".join(f"{k} <span class='num'>{v}</span>" for k, v in dc.get("adr_counts", {}).items())
                      + f" · {dc.get('entries')} decision-log entries</p><table><tr><th>PROPOSED ADRs</th></tr>" + "".join(
                          f"<tr><td>{_lnk(a['source'], link_prefix) and _e(a['id'])} — {_e(a['title'])}</td></tr>"
                          for a in dc.get("adr_proposed", [])) + "</table><table><tr><th>Latest decisions</th></tr>" + "".join(
                          f"<tr><td class='num'>{_e(d['date'])}</td><td>{_e(d['title'])}</td></tr>" for d in dc.get("latest", [])) + "</table>")
    parts.append(f"<section id='decisions'>{head('Decisions & ADRs', dc)}{body}</section>")

    qu = S.get("queue", {})
    body = aw(qu) or ("<table><tr><th>Needs your decision</th><th></th></tr>" + "".join(
        f"<tr><td>{_e(_md(n['item']))}</td><td>{_e(_md(n['plain']))}</td></tr>" for n in qu.get("needs_decision", []))
        + "</table><table><tr><th>Wave history</th></tr>" + "".join(
            f"<tr><td>{_e(_md(w['line']))}</td></tr>" for w in qu.get("waves", [])) + "</table>")
    parts.append(f"<section id='queue'>{head('Your desk & wave history', qu)}{body}</section>")

    gt = S.get("git", {})
    body = aw(gt) or (f"<p>origin/main <code>{_e(gt.get('origin_main'))}</code> — {_e(gt.get('subject'))}<br>"
                      f"Unmerged remote branches: <b class='num'>{gt.get('unmerged_branches')}</b></p>")
    parts.append(f"<section id='git'>{head('Repository', gt)}{body}</section>")

    da = S.get("data", {})
    body = aw(da) or ("<table><tr><th>Store</th><th>Size</th><th>Rows</th><th>Newest record</th></tr>" + "".join(
        f"<tr><td>{_lnk(s['source'], link_prefix) and _e(s['label'])}</td>"
        + (f"<td colspan=3 class='aw'>awaiting {_e(s['awaiting'])}</td>" if s.get("awaiting") else
           f"<td class='num'>{s['bytes']/1e6:.1f} MB / {s['files']} files</td><td class='num'>{_e(s.get('rows') if s.get('rows') is not None else '—')}</td>"
           f"<td class='num'>{_e(s.get('newest_record') or s['newest_mtime'])}</td>") + "</tr>"
        for s in da.get("stores", [])) + "</table>")
    parts.append(f"<section id='data'>{head('Data assets', da)}{body}</section>")

    nav = f'<a href="{_e(live_nav)}">Live Terminal →</a>' if live_nav else ""
    offline = "OFFLINE SNAPSHOT — no live calls. " if static else ""
    return (f"<!doctype html><html lang='en'><head><meta charset='utf-8'>"
            f"<meta name='viewport' content='width=device-width,initial-scale=1'><title>Project State</title>"
            f"<style>{_CSS}</style></head><body><header><h1>PMBOT — project state</h1>"
            f"<span class='st'>{offline}{_e(stamp)}</span><span class='st'>{nav}</span></header>"
            f"<main>{''.join(parts)}</main></body></html>")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--repo", default=str(REPO))
    ap.add_argument("--json", dest="json_out")
    ap.add_argument("--html", dest="html_out")
    a = ap.parse_args(argv)
    st = build_state(a.repo)
    if a.json_out:
        Path(a.json_out).write_text(json.dumps(st, indent=1, default=str))
    if a.html_out:
        Path(a.html_out).write_text(render_html(st, static=True), encoding="utf-8")
    if not a.json_out and not a.html_out:
        print(json.dumps(st, indent=1, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
