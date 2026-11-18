"""Tolerant ISO-8601 timestamp parse (GG-1934, W116.2).

Applies when: any timestamp read from Kalshi (fills `created_time`, order `last_update`, market `close_time`) or from our
own logs is parsed on the box. The box runs Python 3.9, whose `datetime.fromisoformat` rejects a trailing "Z" and any
fractional-seconds width other than 3 or 6 (Kalshi sends 5). One parser for the whole repo, so the bug is fixed once.
"""
from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any, Optional

_FRAC = re.compile(r"\.(\d+)")


def parse_ts(s: Any) -> Optional[datetime]:
    """Return an aware UTC datetime, or None when `s` is empty or unparseable.

    Handles: trailing "Z", 1-9 fractional digits (padded / truncated to 6), naive values (treated as UTC), datetime input.
    """
    if s is None or s == "":
        return None
    if isinstance(s, datetime):
        d = s
    else:
        t = str(s).strip().replace("Z", "+00:00").replace("z", "+00:00")
        t = _FRAC.sub(lambda m: "." + (m.group(1) + "000000")[:6], t, count=1)
        try:
            d = datetime.fromisoformat(t)
        except ValueError:
            return None
    return d.replace(tzinfo=timezone.utc) if d.tzinfo is None else d.astimezone(timezone.utc)
