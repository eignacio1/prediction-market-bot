"""
Tests for scripts/backfill_logic_epoch.py — T-321 historical logic_epoch backfill.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

_ROOT = Path(__file__).parent.parent
_SCRIPTS = _ROOT / "scripts"
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))
_SRC = _ROOT / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from backfill_logic_epoch import backfill, derive_logic_epoch, main  # noqa: E402
from prediction_market_bot.logic_epoch import (  # noqa: E402
    CURRENT_APPROVAL_COMMIT,
    CURRENT_LOGIC_EPOCH,
    approval_commit_for_epoch,
)

_PRE_HISTORY = "2026-06-01T00:00:00.000Z"          # before any boundary -> epoch 1
_POST_GG087_PRE_GG077 = "2026-07-05T12:00:00.000Z"  # between GG-087/GG-077 -> epoch 2
_POST_GG077 = "2026-07-06T00:00:00.000Z"            # after GG-077, before GG-113 -> epoch 3
# GG-113 (ADR-0043) added epoch 4 at commit 2026-07-15T01:56:45Z (91111b7,
# the band-gated self-correction — not the earlier, never-deployed 2569c1f
# unconditional draft).
_POST_GG113 = "2026-07-15T02:00:00.000Z"            # after GG-113, before GG-119 -> epoch 4
# GG-119 (ADR-0045) added epoch 5 at commit 2026-07-15T23:52:42Z (53a9208,
# T1's NO-direction vig sign fix, band-gated + fixed in the same commit —
# unlike GG-113 this needed no self-correction).
_POST_GG119 = "2026-07-16T00:00:00.000Z"            # after GG-119, before GG-123 -> epoch 5
# GG-123 (APR-0028) added epoch 6 at commit 2026-07-15T17:13:46-07:00 /
# (variable name below retains this task's original informal "GG122" numbering;
#  comments updated to reference the corrected canonical GG-123 post-renumbering)
# 2026-07-16T00:13:46Z (cc887e8, T2's full-vig-vs-half-spread magnitude
# fix, D2 actioned once the concurrent GG-119 branch's merge confirmed
# its epoch=5 boundary was T1-scoped only). This must stay ahead of every
# LogicEpochBoundary in logic_epoch.py for "is_current_epoch" tests to
# mean what they claim.
_POST_GG122 = "2026-07-16T00:20:00.000Z"            # after all boundaries -> current epoch


def _pos(**overrides) -> dict:
    base = {
        "position_id": "POS-TEST001",
        "entered_at": _POST_GG122,
        "band": "T1",
    }
    base.update(overrides)
    return base


class TestDeriveLogicEpoch:
    @pytest.mark.unit
    def test_pre_history_timestamp_is_epoch_1(self):
        assert derive_logic_epoch(_PRE_HISTORY) == 1

    @pytest.mark.unit
    def test_between_boundaries_is_epoch_2(self):
        assert derive_logic_epoch(_POST_GG087_PRE_GG077) == 2

    @pytest.mark.unit
    def test_after_gg077_before_gg113_is_epoch_3(self):
        assert derive_logic_epoch(_POST_GG077) == 3

    @pytest.mark.unit
    def test_after_gg113_before_gg119_is_epoch_4(self):
        assert derive_logic_epoch(_POST_GG113) == 4

    @pytest.mark.unit
    def test_after_gg119_before_gg122_is_epoch_5(self):
        assert derive_logic_epoch(_POST_GG119) == 5

    @pytest.mark.unit
    def test_after_all_boundaries_is_current_epoch(self):
        assert derive_logic_epoch(_POST_GG122) == CURRENT_LOGIC_EPOCH

    @pytest.mark.unit
    def test_missing_entered_at_is_unresolvable(self):
        assert derive_logic_epoch("") is None

    @pytest.mark.unit
    def test_unparseable_entered_at_is_unresolvable(self):
        assert derive_logic_epoch("not-a-timestamp") is None


class TestBackfill:
    @pytest.mark.unit
    def test_tags_untagged_position(self):
        portfolio = {"closed_positions": [_pos(logic_epoch=None)]}
        tagged, already_tagged, unresolvable = backfill(portfolio)
        assert (tagged, already_tagged, unresolvable) == (1, 0, 0)
        pos = portfolio["closed_positions"][0]
        assert pos["logic_epoch"] == CURRENT_LOGIC_EPOCH
        assert pos["approval_commit"] == CURRENT_APPROVAL_COMMIT

    @pytest.mark.unit
    def test_idempotent_skips_already_tagged(self):
        portfolio = {"closed_positions": [_pos(logic_epoch=2, approval_commit="abc123")]}
        tagged, already_tagged, unresolvable = backfill(portfolio)
        assert (tagged, already_tagged, unresolvable) == (0, 1, 0)
        # Untouched — not overwritten to the current epoch.
        assert portfolio["closed_positions"][0]["logic_epoch"] == 2
        assert portfolio["closed_positions"][0]["approval_commit"] == "abc123"

    @pytest.mark.unit
    def test_unresolvable_when_entered_at_missing(self):
        portfolio = {"open_positions": [_pos(entered_at="", logic_epoch=None)]}
        tagged, already_tagged, unresolvable = backfill(portfolio)
        assert (tagged, already_tagged, unresolvable) == (0, 0, 1)
        assert "logic_epoch" not in portfolio["open_positions"][0] or \
            portfolio["open_positions"][0]["logic_epoch"] is None

    @pytest.mark.unit
    def test_covers_all_three_ledger_keys(self):
        portfolio = {
            "open_positions": [_pos(logic_epoch=None, entered_at=_PRE_HISTORY)],
            "closed_positions": [_pos(logic_epoch=None, entered_at=_POST_GG087_PRE_GG077)],
            "rejected_positions": [_pos(logic_epoch=None, entered_at=_POST_GG077)],
        }
        tagged, already_tagged, unresolvable = backfill(portfolio)
        assert (tagged, already_tagged, unresolvable) == (3, 0, 0)
        assert portfolio["open_positions"][0]["logic_epoch"] == 1
        assert portfolio["open_positions"][0]["approval_commit"] == approval_commit_for_epoch(1)
        assert portfolio["closed_positions"][0]["logic_epoch"] == 2
        assert portfolio["rejected_positions"][0]["logic_epoch"] == 3


class TestMainAtomicWrite:
    @pytest.mark.unit
    def test_dry_run_does_not_write(self, tmp_path, capsys, monkeypatch):
        p = tmp_path / "paper_portfolio.json"
        p.write_text(json.dumps({"closed_positions": [_pos(logic_epoch=None)]}))
        original = p.read_text()
        monkeypatch.setattr(sys, "argv", ["backfill_logic_epoch.py", str(p), "--dry-run"])
        rc = main()
        assert rc == 0
        assert p.read_text() == original  # unchanged on disk

    @pytest.mark.unit
    def test_writes_tagged_positions_to_disk(self, tmp_path, monkeypatch):
        p = tmp_path / "paper_portfolio.json"
        p.write_text(json.dumps({"closed_positions": [_pos(logic_epoch=None)]}))
        monkeypatch.setattr(sys, "argv", ["backfill_logic_epoch.py", str(p)])
        rc = main()
        assert rc == 0
        data = json.loads(p.read_text())
        assert data["closed_positions"][0]["logic_epoch"] == CURRENT_LOGIC_EPOCH
        assert data["closed_positions"][0]["approval_commit"] == CURRENT_APPROVAL_COMMIT

    @pytest.mark.unit
    def test_rerun_is_idempotent(self, tmp_path, monkeypatch):
        p = tmp_path / "paper_portfolio.json"
        p.write_text(json.dumps({"closed_positions": [_pos(logic_epoch=None)]}))
        monkeypatch.setattr(sys, "argv", ["backfill_logic_epoch.py", str(p)])
        main()
        first = json.loads(p.read_text())
        main()
        second = json.loads(p.read_text())
        assert first == second
