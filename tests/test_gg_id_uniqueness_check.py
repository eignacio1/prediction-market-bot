"""Tests for scripts/lib/gg_id_uniqueness_check.py (T-476/GG-199, GG-162 class)."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

MODULE_PATH = Path(__file__).parent.parent / "scripts" / "lib" / "gg_id_uniqueness_check.py"
_spec = importlib.util.spec_from_file_location("gg_id_uniqueness_check", MODULE_PATH)
gguc = importlib.util.module_from_spec(_spec)
sys.modules["gg_id_uniqueness_check"] = gguc
_spec.loader.exec_module(gguc)


def test_no_duplicates_in_clean_log():
    text = "### GG-100 — a\n**Status:** OPEN · **Severity:** LOW\n\n### GG-101 — b\n**Status:** OPEN · **Severity:** LOW\n"
    assert gguc.find_duplicate_ids(text) == []


def test_duplicate_within_one_file_detected():
    text = "### GG-187 — a\n**Status:** OPEN · **Severity:** LOW\n\n### GG-187 — b (collision)\n**Status:** OPEN · **Severity:** LOW\n"
    assert gguc.find_duplicate_ids(text) == ["GG-187"]


def test_duplicate_across_two_files_detected():
    live = "### GG-197 — live entry\n**Status:** OPEN · **Severity:** LOW\n"
    archive = "### GG-197 — archived entry reusing the same number\n**Status:** RESOLVED · **Severity:** LOW\n"
    assert gguc.find_duplicate_ids(live, archive) == ["GG-197"]


def test_template_example_header_not_a_false_trigger_by_itself():
    # A single mention (even inside a template/example fence) is not a
    # duplicate on its own -- only a repeat of the same id is.
    text = "### GG-NNN — [Short title]\n### GG-300 — real gap\n**Status:** OPEN · **Severity:** LOW\n"
    assert gguc.find_duplicate_ids(text) == []
