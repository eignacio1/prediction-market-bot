"""Append-only per-cell JSONL shadow ledger, idempotent per (run_id, market_ticker).

This is the ONLY place the shadow package writes. Base dir defaults to
exp_output/PREGAME_SHADOW and is injectable for tests.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

from prediction_market_bot.atomic_io import alarm

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

    def _load(self) -> set[tuple[str, str]]:
        if self._keys is None:
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
        keys = self._load()
        k = (row["run_id"], row["market_ticker"])
        if k in keys:
            return False
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a") as fh:
            if fh.tell() > 0:
                with self.path.open("rb") as rh:
                    rh.seek(-1, os.SEEK_END)
                    if rh.read(1) != b"\n":
                        fh.write("\n")  # GG-672: terminate a torn trailing line so the new row stays parseable
            fh.write(json.dumps({**{f: row[f] for f in ROW_FIELDS}, **self.extra, **(row_extra or {})}, sort_keys=False) + "\n")
            fh.flush()
            os.fsync(fh.fileno())
        keys.add(k)
        return True
