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


def cells() -> dict:
    from prediction_market_bot.c5_execution.market_type_registry import MARKET_TYPE_REGISTRY

    out = {}
    for (mt, band), cell in MARKET_TYPE_REGISTRY.items():
        status = cell.status.value
        note = (cell.notes or cell.reason or "") if status != "not_implemented" else ""
        out[f"{mt.name}|{band.value}"] = {"s": status, "n": note[:220]}
    return out


def build(out: pathlib.Path) -> None:
    sha = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "--short=7", "HEAD"],
                         capture_output=True, text=True).stdout.strip() or "unknown"
    date = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d")
    body = (SRC / "body.html").read_text().replace("__SHA__", sha).replace("__DATE__", date)
    script = (SRC / "script.js").read_text().replace(
        "__CELLS__", json.dumps(cells(), ensure_ascii=False).replace("</", "<\\/"))
    html = (SRC / "head.html").read_text() + body + "\n<script>\n" + script + "\n</script>\n</body>\n</html>\n"
    out.write_text(html)
    print(f"wrote {out} ({len(html):,} bytes) at {sha}")


if __name__ == "__main__":
    build(pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "PMBot Visual Dashboard.html")
