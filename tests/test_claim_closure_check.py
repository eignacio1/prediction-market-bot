"""Tests for scripts/lib/claim_closure_check.py (T-476/GG-199, GG-188 class).

No git repo or live SESSION_CLAIMS.md needed -- exercises find_unclosed_claims
directly against synthetic table text.
"""
from __future__ import annotations

import importlib.util
import sys
from datetime import datetime, timezone
from pathlib import Path

MODULE_PATH = Path(__file__).parent.parent / "scripts" / "lib" / "claim_closure_check.py"
_spec = importlib.util.spec_from_file_location("claim_closure_check", MODULE_PATH)
ccc = importlib.util.module_from_spec(_spec)
sys.modules["claim_closure_check"] = ccc
_spec.loader.exec_module(ccc)

CUTOFF = datetime(2026, 8, 7, tzinfo=timezone.utc)
HEADER = "| Timestamp | ID | Focus |\n| --- | --- | --- |\n"


def _table(*rows: str) -> str:
    return HEADER + "\n".join(rows) + "\n"


def test_unclosed_claim_flagged_after_bound():
    rows = [f"| 2026-08-08T00:00:0{i}Z | T-99{i} | did some work |" for i in range(4)]
    text = _table(*rows)
    alerts = ccc.find_unclosed_claims(text, cutoff=CUTOFF, bound_other_t=3)
    ids = [t for t, _, _ in alerts]
    assert "T-990" in ids


def test_closed_claim_never_flagged():
    rows = [
        "| 2026-08-08T00:00:00Z | T-500 | working on X |",
        "| 2026-08-08T01:00:00Z | T-500 | CLOSED - done, merged |",
        "| 2026-08-08T02:00:00Z | T-501 | other work |",
        "| 2026-08-08T03:00:00Z | T-502 | other work |",
        "| 2026-08-08T04:00:00Z | T-503 | other work |",
    ]
    text = _table(*rows)
    alerts = ccc.find_unclosed_claims(text, cutoff=CUTOFF, bound_other_t=3)
    ids = [t for t, _, _ in alerts]
    assert "T-500" not in ids


def test_bold_markdown_closed_row_recognized():
    # GG-199 regression: a bold "**CLOSED — ..." row (the real historical
    # convention, e.g. T-429/T-426) must still count as closed.
    rows = [
        "| 2026-08-08T00:00:00Z | T-600 | working on Y |",
        "| 2026-08-08T01:00:00Z | T-600 | **CLOSED — done, merged.** |",
        "| 2026-08-08T02:00:00Z | T-601 | other work |",
        "| 2026-08-08T03:00:00Z | T-602 | other work |",
        "| 2026-08-08T04:00:00Z | T-603 | other work |",
    ]
    text = _table(*rows)
    alerts = ccc.find_unclosed_claims(text, cutoff=CUTOFF, bound_other_t=3)
    ids = [t for t, _, _ in alerts]
    assert "T-600" not in ids


def test_pre_cutoff_claim_not_flagged():
    # Claims predating the CLOSED-convention adoption date must never be
    # in scope -- they used no such convention and would be pure noise
    # (a full-file dry run with no cutoff flagged 108/149 T-numbers).
    rows = [f"| 2026-07-01T00:00:0{i}Z | T-10{i} | pre-convention work |" for i in range(4)]
    text = _table(*rows)
    alerts = ccc.find_unclosed_claims(text, cutoff=CUTOFF, bound_other_t=3)
    assert alerts == []


def test_malformed_timestamp_does_not_crash():
    rows = [
        "| 2026-08-08T00:00:00Z | T-700 | working on Z |",
        "| 2026-08-18T[session-end] | T-700 | MERGED: NO -- placeholder timestamp |",
        "| 2026-08-08T02:00:00Z | T-701 | other work |",
        "| 2026-08-08T03:00:00Z | T-702 | other work |",
        "| 2026-08-08T04:00:00Z | T-703 | other work |",
    ]
    text = _table(*rows)
    alerts = ccc.find_unclosed_claims(text, cutoff=CUTOFF, bound_other_t=3)
    ids = [t for t, _, _ in alerts]
    assert "T-700" in ids  # never CLOSED, malformed row didn't crash the parse


def test_below_bound_not_flagged():
    rows = [
        "| 2026-08-08T00:00:00Z | T-800 | working |",
        "| 2026-08-08T01:00:00Z | T-801 | other |",
    ]
    text = _table(*rows)
    alerts = ccc.find_unclosed_claims(text, cutoff=CUTOFF, bound_other_t=3)
    ids = [t for t, _, _ in alerts]
    assert "T-800" not in ids
