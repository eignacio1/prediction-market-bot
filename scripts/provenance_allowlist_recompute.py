#!/usr/bin/env python3
"""T-592 / Wave 40.2: recompute the T-588 evidence-boundary delta with a
provenance allowlist overlaid. COMPUTES ONLY. Applies nothing, edits no
counter, no ledger, no pool, and not logic_epoch.py. The allowlist is a data
file read here and nowhere else.

Baseline columns come from scripts/evidence_boundary_census.run() (imported,
not reimplemented). The overlay is: a row counts with the allowlist iff
  is_countable_evidence(row, band)                       (unchanged predicate), OR
  (row is epoch-clean for band per rbm.filter_clean
   AND evidence_class(row) == UNATTRIBUTED
   AND row carries no model_identity or the literal UNKNOWN
   AND row.band == window.band AND entered_at within a window).
STUB rows and rows that carry any other identity string are never admitted.
Nothing is written into a row (GG-228).

Usage:
  python3 scripts/provenance_allowlist_recompute.py --pool-dir <dir> \
      --allowlist 05_RESEARCH_EXPERIMENTS/provenance/t4m_proj_provenance_allowlist.json [--out f.md]
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import evidence_boundary_census as census  # noqa: E402
import run_band_monitor as rbm  # noqa: E402

from prediction_market_bot.logic_epoch import (  # noqa: E402
    EVIDENCE_UNATTRIBUTED, evidence_class, is_countable_evidence,
)

REQUIRED = ("window_id", "band", "market_type", "session_id", "window_start_utc",
            "window_end_utc", "commit_sha", "model_identity_asserted", "citation")
CITATION_KEYS = ("process_start", "commit", "session_to_process", "code")


def _ts(s: str) -> datetime:
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def load_allowlist(path: Path) -> list[dict]:
    """Load and validate. Raises ValueError on any uncited or malformed entry:
    an entry without a citation is a manufactured one and is refused whole."""
    windows = json.loads(Path(path).read_text())["windows"]
    seen, spans = set(), []
    for w in windows:
        for k in REQUIRED:
            if not w.get(k):
                raise ValueError(f"{w.get('window_id')}: missing {k}")
        for k in CITATION_KEYS:
            if not str(w["citation"].get(k, "")).strip():
                raise ValueError(f"{w['window_id']}: citation.{k} empty")
        if not re.fullmatch(r"[0-9a-f]{40}", w["commit_sha"]):
            raise ValueError(f"{w['window_id']}: commit_sha not a full sha")
        if w["window_id"] in seen:
            raise ValueError(f"duplicate {w['window_id']}")
        seen.add(w["window_id"])
        a, b = _ts(w["window_start_utc"]), _ts(w["window_end_utc"])
        if a > b:
            raise ValueError(f"{w['window_id']}: start after end")
        spans.append((a, b, w["window_id"]))
    spans.sort()
    for (a1, b1, i1), (a2, b2, i2) in zip(spans, spans[1:]):
        if a2 <= b1:
            raise ValueError(f"windows overlap: {i1} {i2}")
    return windows


def in_window(row: dict, band: str, windows: list[dict]) -> dict | None:
    t = row.get("entered_at")
    if not isinstance(t, str):
        return None
    try:
        ts = _ts(t)
    except ValueError:
        return None
    for w in windows:
        if w["band"] == band and _ts(w["window_start_utc"]) <= ts <= _ts(w["window_end_utc"]):
            return w
    return None


def countable_with_allowlist(row: dict, band: str, windows: list[dict]) -> bool:
    if is_countable_evidence(row, band):
        return True
    if evidence_class(row) != EVIDENCE_UNATTRIBUTED:
        return False
    ident = row.get("model_identity")
    if isinstance(ident, str) and ident.strip() and ident.strip().upper() != "UNKNOWN":
        return False
    if not rbm.filter_clean([row], band):
        return False
    return in_window(row, band, windows) is not None


def recompute(pool_dir: Path, windows: list[dict]) -> tuple[str, dict]:
    ledger = rbm.load_t4_ledger(pool_dir / "t4_mlb_resolved_ledger.jsonl")
    by_band = rbm.load_pool_by_band(pool_dir / "paper_portfolio_mlb.json")
    plan = [(b, by_band.get(b, [])) for b in rbm.BOOK_BANDS]
    if "UNTAGGED" in by_band:
        plan.append(("UNTAGGED", by_band["UNTAGGED"]))
    plan.append(("T4M-PROJ", ledger))
    base = census.run(pool_dir)  # baseline stays the census script's own output
    L = ["| Cell:Band | raw_n | clean_n today | countable without allowlist | countable with allowlist | recovered |",
         "|---|---|---|---|---|---|"]
    stats = {}
    for band, recs in plan:
        for mt, cell in rbm._regroup_by_cell(band, recs).items():
            today = len(rbm.filter_clean(cell, band))
            without = sum(1 for r in cell if is_countable_evidence(r, band))
            withal = sum(1 for r in cell if countable_with_allowlist(r, band, windows))
            key = f"{mt.value}:{band}"
            stats[key] = dict(raw_n=len(cell), today=today, without=without, with_=withal)
            L.append(f"| {key} | {len(cell)} | {today} | {without} | {withal} | {withal - without} |")
    per_win = []
    cell = rbm._regroup_by_cell("T4M-PROJ", ledger)
    rows = [r for c in cell.values() for r in c]
    for w in windows:
        n = sum(1 for r in rows if countable_with_allowlist(r, "T4M-PROJ", [w]) and not is_countable_evidence(r, "T4M-PROJ"))
        per_win.append((w["window_id"], w["session_id"], w["commit_sha"][:8], n))
    L += ["", "| Window | Session | Commit | Rows recovered |", "|---|---|---|---|"]
    L += [f"| {a} | {b} | {c} | {n} |" for a, b, c, n in per_win]
    stats["_baseline_census_chars"] = len(base)
    return "\n".join(L) + "\n", stats


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pool-dir", required=True, type=Path)
    ap.add_argument("--allowlist", required=True, type=Path)
    ap.add_argument("--out", type=Path)
    a = ap.parse_args(argv)
    text, _ = recompute(a.pool_dir, load_allowlist(a.allowlist))
    print(text)
    if a.out:
        a.out.write_text(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
