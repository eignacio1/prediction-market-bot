"""
Tests for scripts/retire_resolved_gaps.py (T-570, retirement-mechanism, 2026-09-23).

The whole safety margin for this tool is the resolved-class classifier: it must
move every real resolved-class Status variant seen in the live log (bare RESOLVED,
dated RESOLVED, RESOLVED+note, RESOLVED+compound-suffix, CLOSED-AS-ARTIFACT, and a
full-paragraph resolved value) while never moving any of the seven explicit STAY
tokens -- including the two adversarial near-misses that contain resolved-sounding
prose ("fixed and verified") while still starting with a stay token.

No test here ever writes to the real GOVERNANCE_GAP_LOG.md / _ARCHIVE.md -- all
fixtures are synthetic in-memory strings or tmp_path files.
"""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).parent.parent
_SCRIPTS = _ROOT / "scripts"
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from retire_resolved_gaps import (  # noqa: E402
    apply_move,
    is_resolved_class,
    parse_entries,
    plan_move,
    preamble,
)

# ---------------------------------------------------------------------------
# is_resolved_class: real resolved-class variants observed in the live log,
# 2026-09-23 (GG-251, GG-223, GG-271, and a live CLOSED-AS-ARTIFACT example
# from the archive), plus a synthetic full-paragraph case (no real example
# exists in the live log today).
# ---------------------------------------------------------------------------

RESOLVED_CLASS_EXAMPLES = [
    "RESOLVED",
    "RESOLVED (2026-09-11)",
    "RESOLVED 2026-08-28 (T-502)",
    "RESOLVED (2026-09-11, code+migration)",
    "RESOLVED (2026-09-11, code+migration) · ACTIVATED (2026-09-15, confirmed live in running process)",
    "CLOSED-AS-ARTIFACT",
    "CLOSED-AS-DUPLICATE · duplicate of GG-430",
    "CLOSED-AS-SUPERSEDED · ADR-0048",
    "CLOSED-AS-ARTIFACT · superseded by ADR-0060, see GG-300",
    (
        "RESOLVED. This is a synthetic full-paragraph Status value constructed "
        "because no real example of this length exists in the live log as of "
        "2026-09-23 -- it exercises the classifier's lack of any length limit: "
        "the fix landed across three commits, was verified against the paper "
        "ledger for two full game-days, and the operator signed off on "
        "2026-09-20 after reviewing the diff line by line, so this entry is "
        "resolved-class regardless of how much narrative follows the token."
    ),
]

STAY_TOKEN_EXAMPLES = [
    "PARTIALLY RESOLVED",
    "PARTIAL RESOLVE",
    "LIKELY RESOLVED",
    "IN PROGRESS",
    "PLAN ACCEPTED",
    "ACCEPTED UNCERTAINTY",
    "WATCH ITEM",
    "OPEN",
    # Adversarial near-misses: resolved-sounding prose, but a stay-class prefix.
    "PARTIALLY RESOLVED (T-568 — first confirmed real fill)",
    (
        "PARTIALLY RESOLVED (2026-09-15, T-551) — Floor A fixed and verified; "
        "Floor B investigated, decision requested via APR-0034, not decided"
    ),
]


def test_resolved_class_examples_all_classify_true():
    for token in RESOLVED_CLASS_EXAMPLES:
        assert is_resolved_class(token), f"expected resolved-class: {token!r}"


def test_stay_tokens_all_classify_false():
    for token in STAY_TOKEN_EXAMPLES:
        assert not is_resolved_class(token), f"expected stay-class: {token!r}"


def test_resolved_prefix_must_be_at_start_not_substring():
    # A token that merely *contains* "RESOLVED" later in the string, but does
    # not start with it, must stay -- this is what makes it a prefix match
    # and not a substring search.
    assert not is_resolved_class("IN PROGRESS -- expected RESOLVED by 2026-10-01")


# ---------------------------------------------------------------------------
# Entry extraction + whole-entry move, against a small synthetic log shaped
# exactly like the real file (header / blank / Status / blank / <details>
# fold / table / </details> / --- / blank / next header).
# ---------------------------------------------------------------------------

def _entry(gid: str, title: str, status_line: str, body: str = "body text") -> str:
    return (
        f"### {gid} — {title}\n"
        "\n"
        f"{status_line}\n"
        "\n"
        "<details>\n"
        "<summary>Full record ▸</summary>\n"
        "\n"
        "| Field | Detail |\n"
        "|---|---|\n"
        f"| Gap ID | {gid} |\n"
        f"| Detail | {body} |\n"
        "\n"
        "</details>\n"
        "\n"
        "---\n"
        "\n"
    )


SYNTHETIC_PREAMBLE = "# Governance Gap Log\n\nSome front matter.\n\n---\n\n"

SYNTHETIC_LOG = (
    SYNTHETIC_PREAMBLE
    + _entry("GG-901", "Stay open A", "**Status:** OPEN · **Severity:** HIGH")
    + _entry("GG-902", "Resolved bare", "**Status:** RESOLVED · **Severity:** LOW")
    + _entry(
        "GG-903",
        "Stay partial (adversarial near-miss)",
        "**Status:** PARTIALLY RESOLVED (2026-09-01) — fixed and verified in part · **Severity:** MEDIUM",
    )
    + _entry(
        "GG-904",
        "Resolved dated",
        "**Status:** RESOLVED (2026-09-11) · **Severity:** MEDIUM",
    )
    + _entry(
        "GG-905",
        "Closed as artifact",
        "**Status:** CLOSED-AS-ARTIFACT · **Severity:** UNSPECIFIED",
    )
)

SYNTHETIC_ARCHIVE = "# Archive\n\nExisting archived history.\n\n---\n\n" + _entry(
    "GG-800", "Already archived", "**Status:** RESOLVED · **Severity:** LOW"
)


def test_parse_entries_classifies_synthetic_log_correctly():
    entries = parse_entries(SYNTHETIC_LOG)
    resolved_ids = {e["id"] for e in entries if e["resolved_class"]}
    stay_ids = {e["id"] for e in entries if not e["resolved_class"]}
    assert resolved_ids == {"GG-902", "GG-904", "GG-905"}
    assert stay_ids == {"GG-901", "GG-903"}


def test_plan_move_whole_entries_only_and_verbatim():
    to_move, to_stay, warnings = plan_move(SYNTHETIC_LOG, SYNTHETIC_ARCHIVE)
    assert warnings == []
    assert {e["id"] for e in to_move} == {"GG-902", "GG-904", "GG-905"}
    assert {e["id"] for e in to_stay} == {"GG-901", "GG-903"}
    # Each moved block is byte-for-byte the same slice parse_entries produced.
    for e in to_move:
        assert e["block"].startswith(f"### {e['id']} — ")
        assert e["block"].endswith("---\n\n")


def test_apply_move_reconstructs_losslessly_and_appends_verbatim():
    to_move, to_stay, _ = plan_move(SYNTHETIC_LOG, SYNTHETIC_ARCHIVE)
    new_src, new_archive = apply_move(SYNTHETIC_LOG, SYNTHETIC_ARCHIVE, to_move, to_stay)

    # Lossless: preamble + every original entry (order-independent reassembly
    # of stayed+moved) reconstructs the original text exactly.
    all_entries = parse_entries(SYNTHETIC_LOG)
    assert preamble(SYNTHETIC_LOG) + "".join(e["block"] for e in all_entries) == SYNTHETIC_LOG

    # New src retains only the stay entries, nothing partial.
    remaining = parse_entries(new_src)
    assert {e["id"] for e in remaining} == {"GG-901", "GG-903"}
    assert "GG-902" not in new_src and "GG-904" not in new_src and "GG-905" not in new_src

    # New archive is old archive + moved blocks, each appearing exactly once,
    # verbatim (not reformatted/re-wrapped).
    assert new_archive.startswith(SYNTHETIC_ARCHIVE)
    for e in to_move:
        assert new_archive.count(e["block"]) == 1


def test_apply_move_is_idempotent_on_second_pass():
    to_move, to_stay, _ = plan_move(SYNTHETIC_LOG, SYNTHETIC_ARCHIVE)
    new_src, new_archive = apply_move(SYNTHETIC_LOG, SYNTHETIC_ARCHIVE, to_move, to_stay)

    to_move_2, to_stay_2, warnings_2 = plan_move(new_src, new_archive)
    assert to_move_2 == []
    assert warnings_2 == []
    new_src_2, new_archive_2 = apply_move(new_src, new_archive, to_move_2, to_stay_2)
    assert new_src_2 == new_src
    assert new_archive_2 == new_archive


def test_duplicate_id_already_in_archive_is_skipped_with_warning():
    # GG-800 exists in the archive fixture; if a same-id entry also (wrongly)
    # exists in the live log, the idempotency guard must skip moving it again
    # rather than duplicate it, and must say so.
    log_with_dupe = SYNTHETIC_LOG + _entry(
        "GG-800", "Duplicate of already-archived id", "**Status:** RESOLVED · **Severity:** LOW"
    )
    to_move, to_stay, warnings = plan_move(log_with_dupe, SYNTHETIC_ARCHIVE)
    assert "GG-800" not in {e["id"] for e in to_move}
    assert "GG-800" in {e["id"] for e in to_stay}
    assert any("GG-800" in w for w in warnings)


def test_preamble_untouched_by_move():
    to_move, to_stay, _ = plan_move(SYNTHETIC_LOG, SYNTHETIC_ARCHIVE)
    new_src, _ = apply_move(SYNTHETIC_LOG, SYNTHETIC_ARCHIVE, to_move, to_stay)
    assert new_src.startswith(SYNTHETIC_PREAMBLE)


# ---------------------------------------------------------------------------
# CLI safety: --apply with no explicit output paths must refuse, not guess.
# ---------------------------------------------------------------------------

def test_cli_apply_without_out_paths_refuses(tmp_path, capsys, monkeypatch):
    import retire_resolved_gaps as mod

    src = tmp_path / "src.md"
    archive = tmp_path / "archive.md"
    src.write_text(SYNTHETIC_LOG)
    archive.write_text(SYNTHETIC_ARCHIVE)

    monkeypatch.setattr(
        sys, "argv",
        ["retire_resolved_gaps.py", "--src", str(src), "--archive", str(archive), "--apply"],
    )
    rc = mod.main()
    assert rc == 2
    err = capsys.readouterr().err
    assert "requires both --out-src and --out-archive" in err
    # Nothing should have been written to the real source files.
    assert src.read_text() == SYNTHETIC_LOG
    assert archive.read_text() == SYNTHETIC_ARCHIVE


def test_cli_dry_run_writes_nothing(tmp_path, monkeypatch):
    import retire_resolved_gaps as mod

    src = tmp_path / "src.md"
    archive = tmp_path / "archive.md"
    src.write_text(SYNTHETIC_LOG)
    archive.write_text(SYNTHETIC_ARCHIVE)

    monkeypatch.setattr(
        sys, "argv",
        ["retire_resolved_gaps.py", "--src", str(src), "--archive", str(archive)],
    )
    rc = mod.main()
    assert rc == 0
    assert src.read_text() == SYNTHETIC_LOG
    assert archive.read_text() == SYNTHETIC_ARCHIVE
