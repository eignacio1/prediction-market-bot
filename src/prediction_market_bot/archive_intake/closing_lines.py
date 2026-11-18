"""Read-only loader for Muse's NHL closing-lines table (W117.2, B-099).

Folder ``L3-closing-lines/nhl/minmaxxxer-2025-26/`` at a pinned archive SHA.  The file hash is verified before a
row is returned; regular season and postseason are kept apart (never pooled).  Nothing here feeds a model.
"""
from __future__ import annotations

import csv
import hashlib
from pathlib import Path

PINNED_SHA = "018634eca5555e3ab1936862b9842bf850e63084"
FOLDER = Path("L3-closing-lines/nhl/minmaxxxer-2025-26")
CSV_NAME = "nhl_2025_26_closing_odds.csv"
CSV_SHA256 = "459588b31cf4dd543f745910b018d42aa6c7ac4cbf53c9b2068e549dcb62b345"
CSV_BYTES = 335103
TERMS = {
    "dataset": "minmaxxxer/nhl-closing-odds-2025-26 (HuggingFace)",
    "license": "CC-BY-4.0",
    "terms": ("Data compiled from publicly available game and odds information; not affiliated with the NHL, "
              "Flashscore or any bookmaker. For research and analysis."),
    "authorization": "Earl, 2026-11-17 16:13 PT: this source and table only; no paid sources, ever",
}
FLOAT_COLS = ("open_home_win_prob", "close_home_win_prob", "open_spread_home", "close_spread_home",
              "close_home_cover_prob", "open_total", "close_total", "close_over_prob", "home_score", "away_score")


class ClosingLinesError(RuntimeError):
    pass


def _num(v: str):
    return float(v) if v not in ("", None) else None


def load_nhl_closing(root: Path, sha: str = PINNED_SHA) -> dict[str, list[dict]]:
    """Return {"regular": [...], "postseason": [...]} from an archive checkout at ``root`` (already pinned to ``sha``).

    Read-only.  Raises ClosingLinesError if the file hash or size differs from the recorded one."""
    if sha != PINNED_SHA:
        raise ClosingLinesError(f"unpinned archive sha {sha}")
    p = Path(root) / FOLDER / CSV_NAME
    raw = p.read_bytes()
    if len(raw) != CSV_BYTES or hashlib.sha256(raw).hexdigest() != CSV_SHA256:
        raise ClosingLinesError("closing-lines file does not match the recorded SOURCE.md hash")
    out: dict[str, list[dict]] = {"regular": [], "postseason": []}
    for r in csv.DictReader(raw.decode().splitlines()):
        for c in FLOAT_COLS:
            r[c] = _num(r.get(c, ""))
        st = r["season_type"]
        if st not in out:
            raise ClosingLinesError(f"unknown season_type {st!r}")
        out[st].append(r)
    return out
