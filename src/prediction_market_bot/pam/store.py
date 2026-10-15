"""PAM store: versioned, append-only; one point-in-time read path (pam_as_of)."""
from __future__ import annotations

import datetime as _dt
import json
import os
from pathlib import Path
from typing import Iterable

from .schema import PamRecord, PamValidationError, to_date

DEFAULT_ROOT = Path(__file__).resolve().parents[3] / "qualitative_data" / "pam"


class PamStore:
    """One JSONL file per sport: ``<root>/<sport>/records.jsonl``. Lines are only ever appended."""

    def __init__(self, root: Path | str | None = None):
        self.root = Path(root) if root else DEFAULT_ROOT

    def path(self, sport: str) -> Path:
        return self.root / sport / "records.jsonl"

    def load(self, sport: str) -> list[PamRecord]:
        p = self.path(sport)
        if not p.exists():
            return []
        with p.open(encoding="utf-8") as fh:
            return [PamRecord.from_dict(json.loads(line)) for line in fh if line.strip()]

    def append(self, records: Iterable[PamRecord]) -> int:
        """Append validated records. Never rewrites a line. Returns count written."""
        recs = list(records)
        by_sport: dict[str, list[PamRecord]] = {}
        for r in recs:
            by_sport.setdefault(r.sport, []).append(r)
        n = 0
        for sport, batch in by_sport.items():
            known = {r.record_id: r for r in self.load(sport)}
            lines = []
            for r in batch:
                if r.record_id in known:
                    raise PamValidationError(f"record_id already in store (append-only): {r.record_id}")
                for sid in r.supersedes:
                    old = known.get(sid)
                    if old is None:
                        raise PamValidationError(f"{r.record_id} supersedes unknown record {sid}")
                    if (old.sport, old.player_id) != (r.sport, r.player_id):
                        raise PamValidationError(f"{r.record_id} supersedes another player's record {sid}")
                known[r.record_id] = r
                lines.append(json.dumps(r.to_dict(), sort_keys=True, ensure_ascii=False))
            p = self.path(sport)
            p.parent.mkdir(parents=True, exist_ok=True)
            with p.open("a", encoding="utf-8") as fh:
                fh.write("\n".join(lines) + "\n")
                fh.flush()
                os.fsync(fh.fileno())
            n += len(lines)
        return n

    def as_of(self, sport: str, player_id: str | int, as_of, *, known_at=None,
              records: list[PamRecord] | None = None) -> PamRecord | None:
        return resolve_as_of(records if records is not None else self.load(sport),
                             sport, str(player_id), as_of, known_at=known_at)


def resolve_as_of(records: list[PamRecord], sport: str, player_id: str, as_of, *, known_at=None) -> PamRecord | None:
    """Record in force for (sport, player) on date ``as_of``; None if there is none.

    A record applies iff effective_from <= as_of < effective_until (open if None). If ``known_at`` is
    given, records made after that date are invisible (what did we know then). A record named in a later
    record's ``supersedes`` is dropped only from the date the superseder takes effect, so history before
    that date still reads the old classification. Remaining ties: latest effective_from, then latest
    recorded_at, then deep over mass, then record_id (deterministic).
    """
    d = to_date(as_of)
    k = to_date(known_at) if known_at is not None else None
    mine = [r for r in records if r.sport == sport and r.player_id == str(player_id)
            and (k is None or r.recorded_at <= k)]
    live = [r for r in mine if r.effective_from <= d and (r.effective_until is None or d < r.effective_until)]
    dead = {sid for r in mine if r.effective_from <= d for sid in r.supersedes}
    live = [r for r in live if r.record_id not in dead]
    if not live:
        return None
    return max(live, key=lambda r: (r.effective_from, r.recorded_at, r.tier == "deep", r.record_id))


def pam_as_of(sport: str, player_id: str | int, as_of, *, known_at=None, root: Path | str | None = None) -> PamRecord | None:
    """The one read path every engine uses."""
    return PamStore(root).as_of(sport, player_id, as_of, known_at=known_at)
