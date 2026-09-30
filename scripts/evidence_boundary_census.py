#!/usr/bin/env python3
"""T-588 / GG-317: read-only census of pool files by evidence class (D1) and
the clean_n delta the band monitor WOULD show under is_countable_evidence()
(D3). Computes only; applies nothing, modifies no file, wires nothing.

Usage:
  python3 scripts/evidence_boundary_census.py --pool-dir <dir> [--out report.md]
<dir> holds paper_portfolio*.json and t4_mlb_resolved_ledger.jsonl (read-only copies).
The monitor's own loaders/regrouping/filter_clean are imported, not reimplemented.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import run_band_monitor as rbm  # noqa: E402

from prediction_market_bot.logic_epoch import (  # noqa: E402
    EVIDENCE_MODEL, EVIDENCE_STUB, EVIDENCE_UNATTRIBUTED,
    evidence_class, is_countable_evidence,
)

POOLS = (
    ("MLB T1/T2/T3", "paper_portfolio_mlb.json"),
    ("MLB T4M-PROJ", "paper_portfolio_mlb_t4.json"),
    ("NFL T1 game-market", "paper_portfolio_t1_nfl_game_market.json"),
    ("NBA T1 (dark)", "paper_portfolio.json"),
    ("NBA T4 (dark)", "paper_portfolio_t4.json"),
)
SECTIONS = ("open_positions", "closed_positions", "rejected_positions")
CLASSES = (EVIDENCE_MODEL, EVIDENCE_STUB, EVIDENCE_UNATTRIBUTED)


def _has_run_provenance(r: dict) -> bool:
    return r.get("run_id") not in (None, "", "UNKNOWN")


def _epoch_range(rows: list[dict]) -> str:
    e = [r["logic_epoch"] for r in rows if isinstance(r.get("logic_epoch"), int)]
    return f"{min(e)}-{max(e)}" if e else "none"


def census_rows(label: str, rows: list[dict]) -> list[str]:
    out = []
    for cls in CLASSES:
        sub = [r for r in rows if evidence_class(r) == cls]
        if not sub:
            continue
        ids = Counter(str(r.get("model_identity", "<absent>")) for r in sub)
        bands = Counter(str(r.get("band") or "<none>") for r in sub)
        prov = sum(1 for r in sub if _has_run_provenance(r))
        out.append(
            f"| {label} | {cls} | {len(sub)} | {dict(ids.most_common(3))} | "
            f"{_epoch_range(sub)} | {dict(bands.most_common(4))} | {prov} |"
        )
    return out


def run(pool_dir: Path) -> str:
    L = ["## D1 — Census by evidence class (read-only)", "",
         "| Pool / section | Class | Rows | model_identity values | Epochs | Bands | Rows with run_id |",
         "|---|---|---|---|---|---|---|"]
    for name, fname in POOLS:
        p = pool_dir / fname
        if not p.exists():
            L.append(f"| {name} | FILE MISSING | - | - | - | - | - |")
            continue
        d = json.loads(p.read_text())
        for sec in SECTIONS:
            rows = d.get(sec) or []
            if rows:
                L.extend(census_rows(f"{name} / {sec}", rows))
    ledger = rbm.load_t4_ledger(pool_dir / "t4_mlb_resolved_ledger.jsonl")
    L.extend(census_rows("MLB T4M-PROJ resolved ledger (monitor source, WIN/LOSS only)", ledger))

    L += ["", "## D3 — clean_n today vs under is_countable_evidence() (computed, NOT applied)", "",
          "| Cell:Band | raw_n | clean_n today | clean_n countable | difference |",
          "|---|---|---|---|---|"]
    by_band = rbm.load_pool_by_band(pool_dir / "paper_portfolio_mlb.json")
    plan = [(b, by_band.get(b, [])) for b in rbm.BOOK_BANDS]
    if "UNTAGGED" in by_band:
        plan.append(("UNTAGGED", by_band["UNTAGGED"]))
    plan.append(("T4M-PROJ", ledger))
    for band, recs in plan:
        for mt, cell in rbm._regroup_by_cell(band, recs).items():
            today = len(rbm.filter_clean(cell, band))
            new = sum(1 for r in cell if is_countable_evidence(r, band))
            L.append(f"| {mt.value}:{band} | {len(cell)} | {today} | {new} | {new - today} |")
    return "\n".join(L) + "\n"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pool-dir", required=True, type=Path)
    ap.add_argument("--out", type=Path)
    a = ap.parse_args(argv)
    text = run(a.pool_dir)
    print(text)
    if a.out:
        a.out.write_text(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
