#!/usr/bin/env python3
"""Build the Visual Dashboard: one self-contained HTML file (no network) the operator opens in Safari.

Design: the operator's hand-built Visual Dashboard (Wave 42 era) — sidebar rail, hero, verdict forest,
cell matrix, wave timeline, desk. Its stylesheet is kept verbatim in 04_EXECUTION/visual_dashboard/head.html.
Content: body.html (narrative, edited by the strategic window at each wave close) + script.js (data arrays and
renderers). The cell matrix is read live from MARKET_TYPE_REGISTRY, so it is always the code's own truth.

Usage: python3 scripts/build_visual_dashboard_html.py [OUTPUT_PATH]
Default output: "PMBot Visual Dashboard.html" at the repo root. The window copies it to the operator's Mac folder,
where "Open Visual Dashboard.command" opens it in Safari.
"""
from __future__ import annotations

import datetime as dt
import json
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
SRC = ROOT / "04_EXECUTION" / "visual_dashboard"
sys.path.insert(0, str(ROOT / "src"))


def _engine_cells() -> list:
    """Newest calibration-engine output's cells ([] when none): the source of a cell's released verdict (W82.2)."""
    try:
        f = sorted((ROOT / "exp_output" / "CALIBRATION").glob("engine_*.json"))[-1]
        return json.loads(f.read_text()).get("cells", [])
    except Exception:
        return []


def cells() -> dict:
    from prediction_market_bot.c5_execution.market_type_registry import MARKET_TYPE_REGISTRY
    sys.path.insert(0, str(ROOT / "scripts"))
    import cell_display_state as cds

    engine = _engine_cells()
    out = {}
    for (mt, band), cell in MARKET_TYPE_REGISTRY.items():
        status = cell.status.value
        note = (cell.notes or cell.reason or "") if status != "not_implemented" else ""
        d = cds.display_state(status, cds.resolve_engine_cell(engine, mt.name, band.value))
        out[f"{mt.name}|{band.value}"] = {"s": status, "d": d, "n": note[:220]}
    return out


def runtime() -> list:
    """ADR-0074: the runtime registry, for the Process integrity section (same loader as the scan)."""
    sys.path.insert(0, str(ROOT / "scripts"))
    import runtime_registry as rr
    keep = ("key", "kind", "schedule", "purpose", "pillar", "alarm", "reviewed", "status", "writes", "source", "max_age_h")
    try:
        return [{k: c.get(k) for k in keep} for c in rr.load()]
    except Exception:
        return []


def runtime_live() -> dict:
    """W76.4: the last live box probe (scripts/runtime_registry.py live), if one is cached on this machine.
    {} when absent -- the page then says the live columns are not available instead of showing blanks."""
    sys.path.insert(0, str(ROOT / "scripts"))
    try:
        import runtime_registry as rr
        ev = json.loads(rr.live_cache_path().read_text())
    except Exception:
        return {}
    if not isinstance(ev, dict) or "rows" not in ev:
        return {}
    return {"as_of": ev.get("as_of"), "head": ev.get("head"), "budget": ev.get("budget"), "reasons": ev.get("reasons", []),
            "counts": ev.get("counts", {}),
            "rows": {r["key"]: {"state": r["state"], "age_h": r.get("age_h"), "detail": r.get("detail") or ""}
                     for r in ev["rows"] if r.get("key")}}


def gg_agent() -> dict:
    """W78.1: the standing gap agent's burn-down (03_DECISIONS/GG_BURNDOWN.md), same parser as the scan and /project."""
    sys.path.insert(0, str(ROOT / "scripts"))
    try:
        import gg_burndown
        return gg_burndown.summary(ROOT)
    except Exception as e:
        return {"ok": False, "error": e.__class__.__name__}


def window_errors() -> dict:
    """ADR-0074: rows and pattern tally of 04_EXECUTION/WINDOW_ERROR_LOG.md."""
    import re
    f = ROOT / "04_EXECUTION" / "WINDOW_ERROR_LOG.md"
    rows, tally = [], []
    if f.exists():
        section = "rows"
        for line in f.read_text().splitlines():
            if line.startswith("## Pattern tally"):
                section = "tally"
            if not line.startswith("| ") or line.startswith("|---") or line.startswith("| #") or line.startswith("| Pattern"):
                continue
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if section == "rows" and len(cells) >= 8:
                rows.append(dict(zip(("id", "date", "wave", "what", "cost", "caught", "pattern", "rule"), cells[:8])))
            elif section == "tally" and len(cells) >= 3:
                tally.append({"pattern": cells[0], "count": int(re.sub(r"\D", "", cells[1]) or 0), "last": cells[2]})
    return {"rows": rows, "tally": tally}


def governance() -> dict:
    """Live gap-log counts, so the Governance section never goes stale (ADR-0074 lesson)."""
    import re
    live = (ROOT / "03_DECISIONS" / "GOVERNANCE_GAP_LOG.md").read_text()
    arch = (ROOT / "03_DECISIONS" / "GOVERNANCE_GAP_LOG_ARCHIVE.md").read_text()
    sev, n_open, n_live = {}, 0, 0
    for line in live.splitlines():
        if not line.startswith("**Status:**"):
            continue
        n_live += 1
        st = re.match(r"\*\*Status:\*\* ([A-Z][A-Z \-]*?)(?: —| ·|$)", line)
        sv = re.search(r"\*\*Severity:\*\* ([A-Z]+)", line)
        if st and st.group(1).strip() == "OPEN":
            n_open += 1
            s = sv.group(1) if sv else "UNSPECIFIED"
            sev[s] = sev.get(s, 0) + 1
    retired = len(re.findall(r"^### GG-[0-9]", arch, re.M))
    return {"open": n_open, "live": n_live, "retired": retired, "ever": n_live + retired, "sev": sev}


MUSE_WEB_STATES = ("built", "pending", "future")


def muse_web() -> dict:
    """The aggregation web (operator 2026-10-21): 02_ARCHITECTURE_DESIGN/QUAL_ARCHIVE/MUSE_WEB.json, maintained by the strategic
    window at every wave close. Validated here; on any defect the section says so instead of drawing a wrong web."""
    f = ROOT / "02_ARCHITECTURE_DESIGN" / "QUAL_ARCHIVE" / "MUSE_WEB.json"
    try:
        d = json.loads(f.read_text())
        rings, sports = d["rings"], d["sports"]
        for sp in d["spokes"]:
            if sp["sport"] not in sports:
                raise ValueError(f"unknown sport {sp['sport']!r}")
            if len(sp["states"]) != len(rings) or any(x not in MUSE_WEB_STATES for x in sp["states"]):
                raise ValueError(f"bad states on {sp['name']!r}")
            sp.setdefault("notes", [""] * len(rings))
            if len(sp["notes"]) != len(rings):
                raise ValueError(f"bad notes on {sp['name']!r}")
        return {"ok": True, "as_of": d.get("as_of"), "archive_commit": d.get("archive_commit"), "about": d.get("about", ""),
                "rings": rings, "sports": sports, "spokes": d["spokes"]}
    except Exception as e:
        return {"ok": False, "error": f"{e.__class__.__name__}: {e}"}


def wave_chip() -> str:
    import re
    q = (ROOT / "04_EXECUTION" / "ACTIVE_QUEUE.md").read_text()
    now = re.search(r"^## ⬛ NOW — Wave (\d+)", q, re.M)
    closed = re.search(r"^### ✅ WAVE (\d+) — CLOSED", q, re.M)
    return (f"Wave {closed.group(1)} closed · " if closed else "") + (f"{now.group(1)} in flight" if now else "")


def build(out: pathlib.Path) -> None:
    sha = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "--short=7", "HEAD"],
                         capture_output=True, text=True).stdout.strip() or "unknown"
    date = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d")
    body = (SRC / "body.html").read_text().replace("__SHA__", sha).replace("__DATE__", date).replace(
        "__WAVECHIP__", wave_chip())

    def js(obj) -> str:
        return json.dumps(obj, ensure_ascii=False).replace("</", "<\\/")

    script = ((SRC / "script.js").read_text().replace("__CELLS__", js(cells())).replace("__RUNTIME__", js(runtime())).replace("__LIVE__", js(runtime_live()))
              .replace("__WINERR__", js(window_errors())).replace("__GAGENT__", js(gg_agent())).replace("__GOV__", js(governance())).replace("__MUSEWEB__", js(muse_web())))
    html = (SRC / "head.html").read_text() + body + "\n<script>\n" + script + "\n</script>\n</body>\n</html>\n"
    out.write_text(html)
    print(f"wrote {out} ({len(html):,} bytes) at {sha}")


if __name__ == "__main__":
    build(pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "PMBot Visual Dashboard.html")
