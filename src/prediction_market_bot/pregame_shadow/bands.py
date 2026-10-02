"""Pre-game band windows (EXECUTION_BANDS.md): T1 12-48h, T2 4-8h, T3 15-60 min before start."""
from __future__ import annotations

from typing import Optional

# (band_value, lo_hours, hi_hours)  -- half-open [lo, hi)
PREGAME_WINDOWS = (
    ("T1", 12.0, 48.0),
    ("T2", 4.0, 8.0),
    ("T3", 0.25, 1.0),
)


def band_for_horizon(hours_to_start: float) -> Optional[str]:
    for band, lo, hi in PREGAME_WINDOWS:
        if lo <= hours_to_start < hi:
            return band
    return None
