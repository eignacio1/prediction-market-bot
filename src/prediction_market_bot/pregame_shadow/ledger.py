"""Append-only per-cell JSONL shadow ledger, idempotent per (run_id, market_ticker).

This is the ONLY place the shadow package writes. Base dir defaults to
exp_output/PREGAME_SHADOW and is injectable for tests.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

from prediction_market_bot.atomic_io import alarm, file_lock

DEFAULT_DIR = Path("exp_output") / "PREGAME_SHADOW"
ROW_FIELDS = (
    "run_id", "ts_utc", "sport", "market_type", "band", "horizon_hours_to_start", "event_ticker",
    "market_ticker", "p_yes", "yes_bid", "yes_ask", "mid", "half_spread", "fee_k007", "fee_kmult",
    "e_net_yes_k007", "e_net_no_k007", "model_id", "model_sha256", "feature_row_sha256",
    "start_time_utc", "start_time_source", "code_sha",
)


class CellLedger:
    def __init__(self, base_dir: Path, sport: str, market_type: str, band: str,
                 extra: dict | None = None) -> None:
        self.extra = dict(extra or {})      # constant labels appended to every row (e.g. season_phase)
        self.path = Path(base_dir) / f"{sport}_{market_type}_{band}.jsonl"
        self._keys: set[tuple[str, str]] | None = None
        self._size: int = -1    # file size when _keys was last loaded; a change means another process appended

    def _load(self) -> set[tuple[str, str]]:
        size = self.path.stat().st_size if self.path.exists() else 0
        if self._keys is not None and size != self._size:
            self._keys = None   # another process appended since our last load (W76.3, GG-748): re-read dedup keys
        if self._keys is None:
            self._size = size
            self._keys = set()
            if self.path.exists():
                lines = self.path.read_text().splitlines()
                for i, line in enumerate(lines):
                    if not line.strip():
                        continue
                    try:
                        r = json.loads(line)
                        self._keys.add((r["run_id"], r["market_ticker"]))
                    except (ValueError, KeyError, TypeError) as e:
                        # GG-672: one torn line (crash mid-append) must not take the whole arm down.
                        # Rows are never rewritten here; the line is skipped for dedup and alarmed.
                        alarm(f"{self.path}:{i + 1}: unparseable shadow-ledger line skipped ({e!r})")
        return self._keys

    def append(self, row: dict, row_extra: dict | None = None) -> bool:
        missing = [f for f in ROW_FIELDS if f not in row]
        if missing:
            raise ValueError(f"ledger row missing fields: {missing}")
        k = (row["run_id"], row["market_ticker"])
        line = json.dumps({**{f: row[f] for f in ROW_FIELDS}, **self.extra, **(row_extra or {})}, sort_keys=False) + "\n"
        self.path.parent.mkdir(parents=True, exist_ok=True)
        # W76.3 / GG-748: cross-process flock (<ledger>.lock) so concurrent runners appending to one arm's
        # ledger can neither lose nor interleave a row; dedup is re-checked under the lock.
        with file_lock(self.path):
            keys = self._load()
            if k in keys:
                return False
            payload = line.encode()
            if self.path.exists() and self.path.stat().st_size > 0:
                with self.path.open("rb") as rh:
                    rh.seek(-1, os.SEEK_END)
                    if rh.read(1) != b"\n":
                        payload = b"\n" + payload  # GG-672: terminate a torn trailing line so the new row stays parseable
            fd = os.open(self.path, os.O_WRONLY | os.O_APPEND | os.O_CREAT, 0o644)
            try:
                os.write(fd, payload)   # one write on an O_APPEND fd: the row is never split
                os.fsync(fd)
            finally:
                os.close(fd)
            keys.add(k)
            self._size = self.path.stat().st_size
        return True
