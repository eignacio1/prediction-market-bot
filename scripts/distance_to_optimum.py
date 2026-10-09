#!/usr/bin/env python3
"""Distance to optimum, COMPUTED (W63.3, Hard Rule 12). Read-only; writes nothing.

Every measure defined in CLAUDE.md § "What winning looks like" → "Distance to optimum"
(B1-B4, D1-D3, E1-E3, P1-P3) is derived here from its source of truth, so the table cannot
drift from the data. Every value carries its source path and as-of timestamp. A missing input
prints UNAVAILABLE with the reason -- never a guess. D1 is checked against a declared manifest
(scripts/distance_to_optimum_d1_manifest.json); any mismatch is an ERROR, not a warning.

Alarm-only: exit code is 0 unless --strict is passed (then 1 if any measure is ERROR).
Usage: python3 scripts/distance_to_optimum.py [--repo PATH] [--json]
"""
from __future__ import annotations

import argparse
import glob
import json
import re
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

REPO = Path(__file__).resolve().parent.parent
MANIFEST_REL = "scripts/distance_to_optimum_d1_manifest.json"
REGISTRY_SRC = "src/prediction_market_bot/c5_execution/market_type_registry.py"
LOGGING = {"active", "shadow"}
BOOKS = {"t4_mlb": ("logs/paper_portfolio_mlb_t4.json", "logs/t4_mlb_fill_status.jsonl"),
         "t1_mlb": ("logs/paper_portfolio_mlb.json", "logs/t1_mlb_fill_status.jsonl")}
BANDS5 = ("T1", "T2", "T3", "T4", "T5")


def _iso(ts: Optional[float] = None) -> str:
    return datetime.fromtimestamp(ts, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ") if ts else \
        datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _mtime(p: Path) -> str:
    """As-of for a file: last commit time when tracked (a checkout's mtime is just clone time), else mtime."""
    import subprocess
    try:
        t = subprocess.run(["git", "-C", str(p.parent), "log", "-1", "--format=%cI", "--", p.name],
                           capture_output=True, text=True, timeout=10).stdout.strip()
        if t:
            return datetime.fromisoformat(t).astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    except Exception:
        pass
    return _iso(p.stat().st_mtime)


def m_ok(mid: str, value: str, source: str, as_of: str, **extra: Any) -> dict:
    return {"id": mid, "status": "OK", "value": value, "source": source, "as_of": as_of, **extra}


def m_na(mid: str, reason: str, source: str) -> dict:
    return {"id": mid, "status": "UNAVAILABLE", "value": "UNAVAILABLE", "reason": reason, "source": source, "as_of": None}


def m_err(mid: str, reason: str, source: str, as_of: Optional[str] = None) -> dict:
    return {"id": mid, "status": "ERROR", "value": "ERROR", "reason": reason, "source": source, "as_of": as_of}


# --------------------------------------------------------------------------- BREADTH
def registry_cells(repo: Path) -> list[tuple[str, str, str]]:
    """[(family_name, band_group, status_value)] from the real registry. Band groups: T1..T5; any T4* -> T4."""
    sys.path.insert(0, str(repo / "src"))
    from prediction_market_bot.c5_execution import market_type_registry as r
    out = []
    for c in r.MARKET_TYPE_REGISTRY.values():
        b = c.band.value
        out.append((c.market_type.name, "T4" if b.startswith("T4") else b, c.status.value))
    # families = every MarketType, including ones with no registered cell
    fams = {m.name for m in r.MarketType}
    return out, fams  # type: ignore[return-value]


def breadth(repo: Path, cells_fams: Optional[tuple] = None) -> list[dict]:
    src = REGISTRY_SRC
    try:
        cells, fams = cells_fams or registry_cells(repo)
        p = repo / src
        as_of = _mtime(p) if p.exists() else _iso()
    except Exception as e:
        return [m_na(i, f"registry import failed: {type(e).__name__}: {e}", src) for i in ("B1", "B2", "B3", "B4")]
    logging_cells = [c for c in cells if c[2] in LOGGING]
    lf = {c[0] for c in logging_cells}
    lb = {c[1] for c in logging_cells}
    props = sorted(f for f in fams if "PLAYER" in f)
    parl = sorted(f for f in fams if "PARLAY" in f)
    pl, ql = [f for f in props if f in lf], [f for f in parl if f in lf]
    return [
        m_ok("B1", f"{len(logging_cells)} / {len(cells)}", src, as_of, note="registered cells logging (ACTIVE+SHADOW) / registered cells"),
        m_ok("B2", f"{len(lf)} / {len(fams)}", src, as_of, note="market families with a logging cell / registered families"),
        m_ok("B3", f"{len([b for b in BANDS5 if b in lb])} of 5 (missing: {', '.join(b for b in BANDS5 if b not in lb) or 'none'})",
             src, as_of, note="execution bands with a logging cell; T4 sub-bands collapsed to T4"),
        m_ok("B4", f"{len(pl)} · {len(ql)}", src, as_of,
             note=f"props families logging · parlay families logging (of {len(props)} props, {len(parl)} parlay registered)"),
    ]


# --------------------------------------------------------------------------- DEPTH
def classify_feature(f: str, manifest: dict) -> Optional[str]:
    for cls in manifest["rule_order"]:
        if any(k in f for k in manifest["keyword_rules"][cls]):
            return cls
    return None


def depth_models(repo: Path, manifest: Optional[dict] = None) -> list[dict]:
    """Per model: {id, status, features, classes, qualitative, reason}. Mismatch with the declaration -> ERROR."""
    if manifest is None:
        manifest = json.loads((repo / MANIFEST_REL).read_text())
    rows = []
    for m in manifest["models"]:
        meta = repo / m["meta"]
        if not meta.exists():
            rows.append({"id": m["id"], "status": "UNAVAILABLE", "reason": f"{m['meta']} not present" + (" (VPS-only artifact)" if m.get("vps_only") else ""),
                         "source": m["meta"]})
            continue
        try:
            feats = list(json.loads(meta.read_text())[m["features_key"]])
        except Exception as e:
            rows.append({"id": m["id"], "status": "ERROR", "reason": f"cannot read {m['features_key']}: {e}", "source": m["meta"]})
            continue
        derived: dict[str, str] = {}
        unclassified = []
        for f in feats:
            c = classify_feature(f, manifest)
            (derived.__setitem__(f, c) if c else unclassified.append(f))
        got, decl = set(derived.values()), set(m["declared_classes"])
        errs = []
        if unclassified:
            errs.append(f"unclassifiable features {unclassified}")
        if got - decl:
            errs.append(f"model conditions on undeclared classes {sorted(got - decl)}")
        if decl - got:
            errs.append(f"declared classes absent from the model {sorted(decl - got)}")
        rows.append({"id": m["id"], "arm": m["arm"], "status": "ERROR" if errs else "OK", "reason": "; ".join(errs),
                     "features": len(feats), "classes": sorted(got), "declared": sorted(decl),
                     "qualitative": sum(1 for c in derived.values() if c == "qualitative"),
                     "source": m["meta"], "as_of": _mtime(meta)})
    return rows


def depth(repo: Path) -> list[dict]:
    try:
        manifest = json.loads((repo / MANIFEST_REL).read_text())
    except Exception as e:
        return [m_na(i, f"manifest unreadable: {e}", MANIFEST_REL) for i in ("D1", "D2")] + [d3(repo)]
    rows = depth_models(repo, manifest)
    all_classes = manifest["classes"]
    errs = [r for r in rows if r["status"] == "ERROR"]
    ok = [r for r in rows if r["status"] == "OK"]
    na = [r for r in rows if r["status"] == "UNAVAILABLE"]
    cls_txt = "; ".join(f"{r['id']}: {', '.join(r['classes']) or 'none'}" for r in ok)
    union = sorted({c for r in ok for c in r["classes"]})
    missing = [c for c in all_classes if c not in union]
    msrc = MANIFEST_REL + " + model metadata"
    if errs:
        d1 = m_err("D1", " | ".join(f"{r['id']}: {r['reason']}" for r in errs), msrc)
    elif not ok:
        d1 = m_na("D1", "no model metadata readable", msrc)
    else:
        d1 = m_ok("D1", f"{cls_txt}. Classes no live model conditions on: {', '.join(missing) or 'none'}", msrc,
                  max(r["as_of"] for r in ok), unavailable_models=[f"{r['id']} ({r['reason']})" for r in na])
    if ok:
        big = max(ok, key=lambda r: r["features"])
        d2 = m_ok("D2", f"{big['features']} ({big['id']}, {big['qualitative']} qualitative)", big["source"], big["as_of"],
                  note="largest readable pre-game feature set; " + (f"unreadable here: {', '.join(r['id'] for r in na)}" if na else "all models readable"))
    else:
        d2 = m_na("D2", "no model metadata readable", msrc)
    return [d1, d2, d3(repo)]


STATUS_RE = re.compile(r"^\*\*Status:\*\*\s*(PROPOSED|ACCEPTED)\b", re.M)
ARM_RE = re.compile(r"^\*\*Arm:\*\*\s*(.+)$", re.M)


def d3(repo: Path) -> dict:
    """Challenger pre-registrations: .md under 12_EXPLORATORY/ or 03_DECISIONS/ whose name contains 'challenger'
    and that carry a `**Status:** PROPOSED|ACCEPTED` line. Arm from an `**Arm:**` line (else 'unspecified')."""
    src = "12_EXPLORATORY/ + 03_DECISIONS/ (*challenger*.md with Status PROPOSED|ACCEPTED)"
    found: dict[str, list[str]] = defaultdict(list)
    newest = 0.0
    for sub in ("12_EXPLORATORY", "03_DECISIONS"):
        for p in sorted((repo / sub).rglob("*.md")) if (repo / sub).is_dir() else []:
            if "challenger" not in p.name.lower():
                continue
            t = p.read_text(errors="replace")
            if not STATUS_RE.search(t):
                continue
            a = ARM_RE.search(t)
            found[a.group(1).strip() if a else "unspecified"].append(str(p.relative_to(repo)))
            newest = max(newest, p.stat().st_mtime)
    n = sum(len(v) for v in found.values())
    val = f"{n}" + (" (" + "; ".join(f"{a}: {len(v)}" for a, v in sorted(found.items())) + ")" if n else
                    " (no PROPOSED/ACCEPTED challenger pre-registration found)")
    return m_ok("D3", val, src, _iso(newest) if newest else _iso(), files=sorted(x for v in found.values() for x in v))


# --------------------------------------------------------------------------- EXECUTION
def _load_book(repo: Path, key: str):
    pf, sc = BOOKS[key]
    pp, sp = repo / pf, repo / sc
    if not pp.exists():
        return None, f"{pf} not present"
    if not sp.exists():
        return None, f"{sc} not present"
    sys.path.insert(0, str(repo / "src"))
    from prediction_market_bot import t4_fill_status as tfs
    closed = [p for p in json.loads(pp.read_text()).get("closed_positions", []) if p.get("position_id")]
    status = tfs.load_fill_status(sp)
    return (closed, status, tfs, max(pp.stat().st_mtime, sp.stat().st_mtime)), None


def execution(repo: Path) -> list[dict]:
    e1, e2, e3 = [], [], []
    for key in BOOKS:
        src = f"{BOOKS[key][0]} + {BOOKS[key][1]}"
        loaded, why = _load_book(repo, key)
        if loaded is None:
            for lst, mid in ((e1, "E1"), (e2, "E2"), (e3, "E3")):
                lst.append((key, m_na(mid, why, src)))
            continue
        closed, status, tfs, mt = loaded
        as_of = _iso(mt)
        filled = sum(1 for p in closed if tfs.is_confirmed_filled(p, status))
        rep = tfs.book_fill_report(closed, status)
        f, nf = rep["filled"], rep["not_filled"]
        e1.append((key, m_ok("E1", f"{filled} / {len(closed)} = {100*filled/len(closed):.1f}%" if closed else "0 / 0", src, as_of)))
        if f["n"]:
            ci = f["pnl_per_bet_ci95_game_clustered"]
            e2.append((key, m_ok("E2", f"${f['pnl_per_bet']:+.2f} (n={f['n']}, {f['games']} games, 95% CI "
                                       f"{'[%.2f, %.2f]' % ci if ci else 'n/a'}; ledger-priced, not fill-priced)", src, as_of)))
        else:
            e2.append((key, m_na("E2", "no CONFIRMED_FILLED settled rows", src)))
        if f["n"] and nf["n"]:
            e3.append((key, m_ok("E3", f"fills {100*f['win_rate']:.1f}% (n={f['n']}) vs non-fills {100*nf['win_rate']:.1f}% (n={nf['n']})", src, as_of)))
        else:
            e3.append((key, m_na("E3", f"need both classes settled (filled n={f['n']}, not-filled n={nf['n']})", src)))
    out = []
    for lst, mid in ((e1, "E1"), (e2, "E2"), (e3, "E3")):
        oks = [(k, m) for k, m in lst if m["status"] == "OK"]
        if oks:
            val = " · ".join(f"{k}: {m['value']}" for k, m in lst if m["status"] == "OK")
            na = [f"{k}: {m['reason']}" for k, m in lst if m["status"] != "OK"]
            out.append(m_ok(mid, val, "; ".join(m["source"] for _, m in oks), max(m["as_of"] for _, m in oks),
                            unavailable=na))
        else:
            out.append(m_na(mid, "; ".join(f"{k}: {m['reason']}" for k, m in lst), "logs/*fill_status.jsonl + logs/paper_portfolio_mlb*.json"))
    return out


# --------------------------------------------------------------------------- PROOF
EXPECT_REL = "12_EXPLORATORY/NFL_FIRST_LOOK_EXPECTATIONS.md"
MODAL_RE = re.compile(r"Vs market, every cell:\*\*\s*([A-Z][A-Z ]+?)\s*≈\s*(\d+)%")


def proof(repo: Path) -> list[dict]:
    cdir = repo / "exp_output" / "CALIBRATION"
    files = sorted(cdir.glob("engine_*.json")) if cdir.is_dir() else []
    src = "exp_output/CALIBRATION/engine_<UTC>.json"
    if not files:
        na = "no calibration-engine output present (VPS-only artifact)"
        return [m_na("P1", na, src), m_na("P2", na, src), m_na("P3", na, src)]
    f = files[-1]
    try:
        d = json.loads(f.read_text())
        cells = d["cells"]
    except Exception as e:
        return [m_err(i, f"engine file unreadable: {e}", f"exp_output/CALIBRATION/{f.name}") for i in ("P1", "P2", "P3")]
    s = f"exp_output/CALIBRATION/{f.name}"
    as_of = d.get("generated") or _mtime(f)
    scored = [c for c in cells if c.get("release") and c.get("verdict")]
    verdicts = [c for c in cells if c.get("verdict")]
    p1 = m_ok("P1", f"{len(scored)} / {len(cells)}", s, as_of, note="cells released at a scored look / cells the engine tracks")
    p2 = m_ok("P2", f"{len(verdicts)}", s, as_of)
    dates = sorted((c["projection"]["date"], c["cell"]) for c in cells if (c.get("projection") or {}).get("date"))
    if not dates:
        return [p1, p2, m_na("P3", "engine projects no first-look date", s)]
    nxt = dates[0][0]
    n_same = sum(1 for x in dates if x[0] == nxt)
    ep = repo / EXPECT_REL
    modal = ""
    if ep.exists() and (mm := MODAL_RE.search(ep.read_text())):
        modal = f"; pre-registered modal outcome ({EXPECT_REL}): {mm.group(1).strip()} ~{mm.group(2)}%"
    else:
        modal = f"; modal outcome UNAVAILABLE ({EXPECT_REL} missing or unparseable)"
    return [p1, p2, m_ok("P3", f"{nxt} ({n_same} cell(s), e.g. {dates[0][1]}){modal}", s, as_of)]


# --------------------------------------------------------------------------- assemble/render
def compute(repo: Path | str = REPO) -> dict:
    repo = Path(repo)
    ms: list[dict] = []
    for fn in (breadth, depth, execution, proof):
        try:
            ms.extend(fn(repo))
        except Exception as e:  # one broken source never blanks the table
            ms.append(m_err(fn.__name__, f"{type(e).__name__}: {e}", fn.__name__))
    return {"generated": _iso(), "repo": repo.name, "measures": ms}


def render(res: dict) -> str:
    lines = [f"DISTANCE TO OPTIMUM — computed {res['generated']} (alarm-only; values only from sources, never typed)"]
    for m in res["measures"]:
        v = m["value"] if m["status"] == "OK" else f"{m['status']}: {m.get('reason')}"
        lines.append(f"  {m['id']:3} {v}")
        lines.append(f"      source: {m['source']} · as of {m['as_of'] or 'n/a'}")
        for k in ("unavailable", "unavailable_models"):
            if m.get(k):
                lines.append(f"      unavailable: {'; '.join(m[k])}")
    return "\n".join(lines)


def main(argv: Optional[list[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--repo", default=str(REPO))
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--strict", action="store_true", help="exit 1 if any measure is ERROR (off by default; alarm-only)")
    a = ap.parse_args(argv)
    res = compute(a.repo)
    print(json.dumps(res, indent=1) if a.json else render(res))
    return 1 if a.strict and any(m["status"] == "ERROR" for m in res["measures"]) else 0


if __name__ == "__main__":
    raise SystemExit(main())
