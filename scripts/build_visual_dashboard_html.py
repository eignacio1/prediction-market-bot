#!/usr/bin/env python3
"""Build the standalone Visual Dashboard (one self-contained HTML file, no network, Safari-safe).

The operator opens it from his Mac with "Open Visual Dashboard.command". It mirrors the Claude Dashboard
artifact (https://claude.ai/artifact/4f6kWqRGqXYcbvfwwQGdYf), which his Safari version cannot render.

Data: 04_EXECUTION/visual_dashboard/data/*.json (edited by the strategic window at each wave close).
Template: 04_EXECUTION/visual_dashboard/template.html.

Usage: python3 scripts/build_visual_dashboard_html.py [OUTPUT_PATH]
Default output: "PMBot Visual Dashboard.html" at the repo root (git-ignored is not required; it is a build product).
"""
from __future__ import annotations

import datetime as dt
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
SRC = ROOT / "04_EXECUTION" / "visual_dashboard"
DATASETS = ["distance", "execution", "books", "registry", "arms", "waves", "desk", "calendar"]
SOURCES = (
    "distance — scripts/distance_to_optimum.py (VPS run 2026-10-09 16:18 UTC) + wave-close changes; "
    "execution — W61.1 / W62.3 / W63.3 fill-status measurements; books — Live Terminal 2026-10-09 18:05 UTC; "
    "registry — MARKET_TYPE_REGISTRY at 0fe57086; arms, waves, decisions, dates — RUNNING SITREP in 04_EXECUTION/ACTIVE_QUEUE.md."
)


def build(out: pathlib.Path) -> None:
    data = {name: json.loads((SRC / "data" / f"{name}.json").read_text()) for name in DATASETS}
    meta_path = SRC / "data" / "meta.json"
    meta = json.loads(meta_path.read_text()) if meta_path.exists() else {}
    data["meta"] = {
        "built_at": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "sources": meta.get("sources", SOURCES),
    }
    blob = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
    html = (SRC / "template.html").read_text().replace("/*__DATA__*/", blob)
    out.write_text(html)
    print(f"wrote {out} ({len(html):,} bytes)")


if __name__ == "__main__":
    target = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "PMBot Visual Dashboard.html"
    build(target)
