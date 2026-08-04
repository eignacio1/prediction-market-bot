"""Tests for scripts/archive_market_prices.py's depth-capture fold-in (Phase 0-H / T-412).

Depth used to be a hand-run, three-sample point estimate (GG-155). This
verifies `_sample_depth` produces a balanced, family-tagged orderbook sample
using the same classifier/sampler as phase0_market_survey.py, so the two
never drift into inconsistent family taxonomies.
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

_SCRIPTS = Path(__file__).parent.parent / "scripts"
_SRC = Path(__file__).parent.parent / "src"
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from archive_market_prices import _sample_depth  # noqa: E402

_BOOK_FP = {
    "orderbook_fp": {
        "yes_dollars": [["0.4500", "10"]],
        "no_dollars": [["0.4500", "10"]],
    }
}


class _FakeClient:
    def __init__(self) -> None:
        self.calls: list[str] = []

    def _get(self, path: str, params: dict[str, Any] | None = None) -> tuple[bool, dict[str, Any]]:
        self.calls.append(path)
        return True, _BOOK_FP


def test_sample_depth_tags_rows_with_family_and_balances_series() -> None:
    markets_by_series = {
        "KXMLBHIT": [{"ticker": f"KXMLBHIT-{i}"} for i in range(10)],
        "KXMLBPTS": [{"ticker": f"KXMLBPTS-{i}"} for i in range(10)],
        "KXMLBGAME": [{"ticker": f"KXMLBGAME-{i}"} for i in range(10)],
    }
    client = _FakeClient()
    rows = _sample_depth(client, markets_by_series, per_family=2, pause=0.0, run_ts="2026-08-04T00:00:00Z")

    families = {r["family"] for r in rows}
    assert "PLAYER_PROP" in families        # KXMLBHIT + KXMLBPTS
    assert "GAME_WINNER" in families         # KXMLBGAME

    player_prop_series = {r["series_ticker"] for r in rows if r["family"] == "PLAYER_PROP"}
    # Both PLAYER_PROP series must appear in the sample -- a head-slice bug
    # (the GG-155 shape) would let one series eat the whole per-family budget.
    assert player_prop_series == {"KXMLBHIT", "KXMLBPTS"}

    for row in rows:
        assert row["run_ts"] == "2026-08-04T00:00:00Z"
        assert row["usable"] is True


def test_sample_depth_marks_fetch_failure_without_dropping_the_row() -> None:
    class _FailingClient:
        def _get(self, path: str, params: dict[str, Any] | None = None) -> tuple[bool, Any]:
            return False, None

    markets_by_series = {"KXMLBHIT": [{"ticker": "KXMLBHIT-0"}]}
    rows = _sample_depth(_FailingClient(), markets_by_series, per_family=1, pause=0.0, run_ts="ts")
    assert len(rows) == 1
    assert rows[0]["usable"] is False
    assert rows[0]["reason"] == "fetch_failed"
