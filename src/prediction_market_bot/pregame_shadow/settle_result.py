"""GG-751 / W75.5: typed settlement result shared by every settlement module.

Before this, "no result" was one value (None / a missing dict key) that meant three different things:
the game is not over yet, the lookup broke, or the row could not be parsed. A caller that waits on None
waits forever on the second and third. A result is now exactly one of:

  FINAL          outcome is set (the joined row, or the NFLGameResult for the ESPN fetcher)
  NOT_FINAL      the game is genuinely not over yet (inside its scheduled-end window); safe to wait
  LOOKUP_FAILED  reason is set; the lookup/parse failed OR the game should be final by now but no final
                 is available. Callers treat this as an ALARM, never as a wait.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from typing import Any, Optional

FINAL = "FINAL"
NOT_FINAL = "NOT_FINAL"
LOOKUP_FAILED = "LOOKUP_FAILED"

# A game dated D (UTC midnight) is scheduled to end by D + 30h (late west-coast kickoff / tip + overtime).
# Past that plus the grace, a missing final is a failure, not "not final yet".
GAME_END_AFTER_DATE_H = 30
GRACE_H = 24


@dataclass(frozen=True)
class SettleResult:
    status: str
    outcome: Any = None
    reason: str = ""

    @property
    def is_final(self) -> bool:
        return self.status == FINAL

    @property
    def is_alarm(self) -> bool:
        return self.status == LOOKUP_FAILED


def final(outcome: Any) -> SettleResult:
    return SettleResult(FINAL, outcome)


def not_final(reason: str = "") -> SettleResult:
    return SettleResult(NOT_FINAL, None, reason)


def lookup_failed(reason: str) -> SettleResult:
    return SettleResult(LOOKUP_FAILED, None, reason)


def _as_date(game_date: "str | date | datetime") -> date:
    if isinstance(game_date, datetime):
        return game_date.date()
    if isinstance(game_date, date):
        return game_date
    return date.fromisoformat(str(game_date)[:10])


def overdue(game_date: "str | date | datetime", now: Optional[datetime] = None) -> bool:
    """True when the game's scheduled end plus the grace has passed."""
    now = now or datetime.now(timezone.utc)
    d = _as_date(game_date)
    deadline = datetime(d.year, d.month, d.day, tzinfo=timezone.utc) + timedelta(
        hours=GAME_END_AFTER_DATE_H + GRACE_H)
    return now > deadline


def missing_final(game_date: "str | date | datetime", now: Optional[datetime] = None,
                  what: str = "final") -> SettleResult:
    """A final was not found. Inside the window it is NOT_FINAL; past it, it is LOOKUP_FAILED."""
    if overdue(game_date, now):
        return lookup_failed(f"no_{what}_past_game_end+{GRACE_H}h game_date={_as_date(game_date)}")
    return not_final(f"game_date={_as_date(game_date)}")
