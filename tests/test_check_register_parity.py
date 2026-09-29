"""
Tests for scripts/check_register_parity.py's RESOLVED_PAT/is_resolved logic
(GG-178, GG-222) — a bare substring match on "ACCEPTED"/"ADOPTED"/"COMPLETE"/
"selected" false-flagged any Status line containing an explicit negation of
those words (e.g. "DRAFT -- NOT ACCEPTED", "PROPOSED ... Not yet ACCEPTED")
as resolved. Latent 2026-08-05/06 through 2026-08-29 (~3+ weeks; GG-222's own
record dates the defect to 2026-07-17, ~6 weeks).
"""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).parent.parent
_SCRIPTS = _ROOT / "scripts"
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from check_register_parity import is_resolved  # noqa: E402

# Exact live Status lines pinned so a regression must be caught verbatim,
# not just conceptually.
ADR_0051_STATUS = (
    "**Status:** DRAFT — NOT ACCEPTED. Proposal only, per T-422's hard scope "
    "fence (no `src/` changes this session). Requires operator review and "
    "explicit sign-off before any implementation."
)
ADR_0052_STATUS = (
    "**Status:** PROPOSED — drafted this session (T-433) under explicit task "
    "instruction; awaiting DS sign-off (Earl Ignacio). Not yet ACCEPTED. "
    "Treat as governing intent, not a closed decision, until sign-off is "
    "recorded here."
)
ADR_0056_STATUS = (
    "**Status:** ACCEPTED (Earl Ignacio, 2026-08-21, T-474 session, prior to "
    "the `nfl-skeleton-spike` worktree"
)


class TestIsResolvedNegation:
    def test_adr_0051_not_accepted_is_unresolved(self) -> None:
        assert is_resolved(ADR_0051_STATUS) is False

    def test_adr_0052_not_yet_accepted_is_unresolved(self) -> None:
        assert is_resolved(ADR_0052_STATUS) is False

    def test_adr_0056_accepted_is_resolved(self) -> None:
        # A true positive must still fire -- the fix must not blind the check.
        assert is_resolved(ADR_0056_STATUS) is True

    def test_bare_accepted_is_resolved(self) -> None:
        assert is_resolved("**Status:** ACCEPTED") is True

    def test_lowercase_selected_still_matches(self) -> None:
        assert is_resolved("the operator selected option B") is True

    def test_negated_selected(self) -> None:
        assert is_resolved("the operator has NOT selected an option yet") is False

    def test_word_boundary_no_false_match_on_substring(self) -> None:
        # "COMPLETE" must not match inside an unrelated longer word.
        assert is_resolved("this text is INCOMPLETE") is False

    def test_bare_not_accepted_is_unresolved(self) -> None:
        assert is_resolved("**Status:** NOT ACCEPTED") is False

    def test_bare_not_yet_accepted_is_unresolved(self) -> None:
        assert is_resolved("**Status:** NOT YET ACCEPTED") is False

    def test_lowercase_not_accepted_is_unresolved(self) -> None:
        assert is_resolved("**status:** not accepted") is False

    def test_never_accepted_is_unresolved(self) -> None:
        assert is_resolved("**Status:** NEVER ACCEPTED — proposal withdrawn") is False

    def test_lowercase_never_accepted_is_unresolved(self) -> None:
        assert is_resolved("this was never accepted by the operator") is False

    def test_accepted_with_date_is_resolved(self) -> None:
        # Positive control -- the fix must not blind a true positive that
        # carries a trailing date, the register's own common phrasing.
        assert is_resolved("**Status:** ACCEPTED 2026-08-21") is True

    def test_adopted_is_resolved(self) -> None:
        # Positive control -- ADOPTED is one of the four resolved keywords.
        assert is_resolved("**Status:** ADOPTED") is True


# ---------------------------------------------------------------------------
# Rule 5 (T-570, 2026-09-23): an ACCEPTED ADR must have its OWN register row,
# not merely a mention inside another row's evidence cell. All fixtures here
# are synthetic tmp_path trees -- never the real repo's 00_ADMIN/03_DECISIONS
# or APPROVALS_REGISTER.md.
# ---------------------------------------------------------------------------

import check_register_parity as crp  # noqa: E402


def _make_repo(tmp_path, *, register_text, adr_files):
    admin = tmp_path / "00_ADMIN"
    decisions = tmp_path / "03_DECISIONS"
    admin.mkdir()
    decisions.mkdir()
    (admin / "APPROVALS_REGISTER.md").write_text(register_text)
    for name, status_line in adr_files.items():
        (decisions / f"{name}.md").write_text(f"{status_line}\n\nBody text.\n")
    return tmp_path


def _patch_paths(monkeypatch, tmp_path):
    monkeypatch.setattr(crp, "ROOT", tmp_path)
    monkeypatch.setattr(crp, "REGISTER", tmp_path / "00_ADMIN" / "APPROVALS_REGISTER.md")
    monkeypatch.setattr(crp, "EXEMPTIONS", tmp_path / "00_ADMIN" / "REGISTER_PARITY_EXEMPTIONS.txt")


def test_rule5_flags_accepted_adr_mentioned_only_in_evidence_cell(tmp_path, monkeypatch, capsys):
    # ADR-9001 is ACCEPTED and appears only inside APR-9001's evidence cell --
    # never as its own `| ADR-9001 |` row.
    register = (
        "| ID | Decision | Status | Date | Evidence |\n"
        "|---|---|---|---|---|\n"
        "| APR-9001 | Some approval | ACCEPTED | 2026-09-01 | see ADR-9001 for detail |\n"
    )
    _make_repo(tmp_path, register_text=register, adr_files={"ADR-9001": "**Status:** ACCEPTED"})
    _patch_paths(monkeypatch, tmp_path)

    rc = crp.main()
    out = capsys.readouterr().out
    assert rc == 1
    assert "ADR-9001" in out
    assert "no OWN dedicated row" in out


def test_rule5_does_not_flag_adr_with_its_own_row(tmp_path, monkeypatch, capsys):
    register = (
        "| ID | Decision | Status | Date | Evidence |\n"
        "|---|---|---|---|---|\n"
        "| ADR-9002 | Some decision | ACCEPTED | 2026-09-01 | n/a |\n"
    )
    _make_repo(tmp_path, register_text=register, adr_files={"ADR-9002": "**Status:** ACCEPTED"})
    _patch_paths(monkeypatch, tmp_path)

    rc = crp.main()
    out = capsys.readouterr().out
    assert rc == 0
    assert "CLEAN" in out


def test_rule5_ignores_exemptions_list(tmp_path, monkeypatch, capsys):
    # T-584/GG-312: the exemptions file used to suppress rule 5, which hid 27
    # of the 36 unregistered accepted ADRs. It no longer suppresses anything.
    register = (
        "| ID | Decision | Status | Date | Evidence |\n"
        "|---|---|---|---|---|\n"
        "| APR-9003 | Some approval | ACCEPTED | 2026-09-01 | see ADR-9003 |\n"
    )
    _make_repo(tmp_path, register_text=register, adr_files={"ADR-9003": "**Status:** ACCEPTED"})
    (tmp_path / "00_ADMIN" / "REGISTER_PARITY_EXEMPTIONS.txt").write_text("ADR-9003\n")
    _patch_paths(monkeypatch, tmp_path)

    rc = crp.main()
    out = capsys.readouterr().out
    assert rc == 1
    assert "ADR-9003" in out


def test_rule5_does_not_fire_when_adr_is_not_resolved(tmp_path, monkeypatch, capsys):
    # Mirrors the real-data finding: ADR-0063-shaped PROPOSED doc, mentioned
    # only in an evidence cell, must NOT trigger rule 5 (only resolved ADRs
    # are in scope for the own-row requirement).
    register = (
        "| ID | Decision | Status | Date | Evidence |\n"
        "|---|---|---|---|---|\n"
        "| APR-9004 | Some approval | ACCEPTED | 2026-09-01 | see ADR-9004 |\n"
    )
    _make_repo(
        tmp_path,
        register_text=register,
        adr_files={"ADR-9004": "**Status:** PROPOSED — drafted, awaiting operator review."},
    )
    _patch_paths(monkeypatch, tmp_path)

    rc = crp.main()
    out = capsys.readouterr().out
    assert rc == 0
    assert "CLEAN" in out


# ---------------------------------------------------------------------------
# T-584 / GG-312 -- forward + reverse parity: one regression per Status format
# found in the 36 accepted-but-unregistered ADRs, plus ratification coverage.
# ---------------------------------------------------------------------------

import check_register_parity as crp  # noqa: E402
import pytest  # noqa: E402

RATIFIED_36 = {
    f"ADR-{n}" for n in (
        "0006 0007 0029 0031 0034 0036 0037 0039 0040 0041 0043 0044 0045 0046 "
        "0001 0002 0008 0009 0010 0011 0012 0013 0014 0015 0016 0017 0019 0020 "
        "0021 0022 0023 0024 0025 0032 0033 0038"
    ).split()
}


@pytest.mark.parametrize(
    "status_line",
    [
        "**Status:** ACCEPTED",
        "**Status:** ACCEPTED 2026-05-14",
        "**Status:** ACCEPTED (2026-05-14)",
        "**Status:** ACCEPTED (as amended)",
        "**Status:** ACCEPTED -- DS sign-off Earl Ignacio, 2026-06-01",
        "**Status:** **ACCEPTED — 2026-06-01**",
        "**Status:** ACCEPTED (Earl Ignacio, 2026-08-21, T-474 session",
    ],
)
def test_accepted_status_formats_resolve(status_line):
    assert is_resolved(status_line)


@pytest.mark.parametrize(
    "status_line",
    [
        "**Status:** DRAFT -- NOT ACCEPTED",
        "**Status:** PROPOSED. Not yet ACCEPTED.",
        "**Status:** DECISION REQUEST",
    ],
)
def test_negation_guards_still_hold(status_line):
    assert not is_resolved(status_line)


def test_doc_status_bold_line(tmp_path):
    p = tmp_path / "ADR-9001.md"
    p.write_text("# T\n\n**Status:** ACCEPTED (as amended)\n")
    assert is_resolved(crp.doc_status(p))


def test_doc_status_heading_format_with_backticks(tmp_path):
    # ADR-0006/0007 shape: `## Status` heading, value on next non-blank line.
    p = tmp_path / "ADR-9002.md"
    p.write_text("# T\n\n## Status\n\n`ACCEPTED`\n")
    s = crp.doc_status(p)
    assert s is not None and "`" not in s and is_resolved(s)


def test_doc_status_heading_negated(tmp_path):
    p = tmp_path / "ADR-9003.md"
    p.write_text("# T\n\n## Status\n\n`PROPOSED -- NOT ACCEPTED`\n")
    assert not is_resolved(crp.doc_status(p))


def test_doc_status_unparseable_returns_none(tmp_path):
    p = tmp_path / "ADR-9004.md"
    p.write_text("# T\n\nNo status header anywhere.\n")
    assert crp.doc_status(p) is None


def test_subject_lead_counts_only_subject_cell():
    rows = [
        "| APR-0001 | ADR-0003 amendment | x | 2026-01-01 | y | z |",
        "| APR-0002 | Something | mentions ADR-0018 | 2026-01-01 | y | ADR-0018 |",
        "| APR-0003 | **ADR-0026** retune | x | 2026-01-01 | y | z |",
    ]
    ids = crp.subject_led_ids(rows)
    assert "ADR-0003" in ids and "ADR-0026" in ids
    assert "ADR-0018" not in ids  # evidence-cell mention is not accountability


def test_pending_row_detection():
    assert crp.row_is_pending("| APR-0008 | s | c | PENDING | p | e |")
    assert not crp.row_is_pending("| APR-0008 | s | c | 2026-01-01 | p | e |")
    assert not crp.row_is_pending("| APR-0008 | s | c | PENDING -> ACCEPTED 2026-02-02 | p | e |")


def test_evidence_resolves_file_and_doc_id():
    row = "| APR-0099 | s | c | 2026-01-01 | see scripts/check_register_parity.py |"
    assert crp.evidence_resolves(row, {"check_register_parity.py"}, set(), "APR-0099")
    assert not crp.evidence_resolves(row, {"other.py"}, set(), "APR-0099")
    row2 = "| APR-0099 | s | c | 2026-01-01 | per ADR-0004 |"
    assert crp.evidence_resolves(row2, set(), {"ADR-0004"}, "APR-0099")
    assert not crp.evidence_resolves(row2, set(), set(), "APR-0099")
    row3 = "| APR-0099 | s | c | 2026-01-01 | self APR-0099 |"
    assert not crp.evidence_resolves(row3, set(), {"APR-0099"}, "APR-0099")


def test_ratified_ids_respects_population_and_not_covered():
    text = (
        "| RATIFY-X | s | c | 2026-09-29 | p | **Population (2 ADRs):** ADR-0001, "
        "ADR-0002. Not covered: ADR-0003 |\n"
        "| RATIFY-Y | s | c | 2026-09-29 | p | no marker, ADR-0004 |\n"
    )
    assert crp.ratified_ids(text) == {"ADR-0001", "ADR-0002"}


def test_live_ratification_row_covers_exactly_the_36():
    text = (_ROOT / "00_ADMIN" / "APPROVALS_REGISTER.md").read_text(encoding="utf-8")
    assert crp.ratified_ids(text) == RATIFIED_36


def test_live_36_have_docs_and_no_forward_finding_even_without_exemptions(monkeypatch):
    # The exemptions file must not be what makes these pass.
    monkeypatch.setattr(crp, "load_exemptions", lambda: set())
    findings, _ = crp.collect_findings()
    forward = [
        f for f in findings
        if any(i in f for i in RATIFIED_36)
        or "no register accountability" in f
    ]
    assert forward == [], forward
