"""W102.2 Part B: read-only proof that every legacy markout row (no `book` key) is a shadow_order.
Prints counts only. Usage: python3 scripts/markout_book_proof_read.py [markouts.jsonl] [demo_fill_policy.jsonl]"""
from __future__ import annotations

import json
import sys
from pathlib import Path


def _lines(p: Path):
    if p.exists():
        for ln in p.read_text().splitlines():
            try:
                yield json.loads(ln)
            except ValueError:
                continue


def proof(markouts: Path, log: Path) -> dict:
    shadow_ids = {r["order_id"] for r in _lines(log) if r.get("event") == "shadow_order" and r.get("order_id")}
    rows = list(_lines(markouts))
    legacy = [r for r in rows if "book" not in r]
    return {"rows": len(rows), "with_book": len(rows) - len(legacy), "legacy_no_book": len(legacy),
            "legacy_in_shadow_order": sum(1 for r in legacy if r.get("order_id") in shadow_ids),
            "legacy_not_shadow_order": sum(1 for r in legacy if r.get("order_id") not in shadow_ids),
            "book_values": sorted({str(r.get("book")) for r in rows if "book" in r})}


if __name__ == "__main__":
    a = sys.argv[1:]
    print(json.dumps(proof(Path(a[0] if a else "exp_output/FORWARD_TEST/markouts/markouts.jsonl"),
                           Path(a[1] if len(a) > 1 else "logs/demo_fill_policy.jsonl")), indent=1))
