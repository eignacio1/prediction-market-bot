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
