"""Append-only per-cell JSONL shadow ledger, idempotent per (run_id, market_ticker).

This is the ONLY place the shadow package writes. Base dir defaults to
exp_output/PREGAME_SHADOW and is injectable for tests.
"""
from __future__ import annotations

import json
from pathlib import Path

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
                for line in self.path.read_text().splitlines():
                    if line.strip():
                        r = json.loads(line)
                        self._keys.add((r["run_id"], r["market_ticker"]))
        return self._keys

    def append(self, row: dict) -> bool:
        missing = [f for f in ROW_FIELDS if f not in row]
        if missing:
            raise ValueError(f"ledger row missing fields: {missing}")
        keys = self._load()
        k = (row["run_id"], row["market_ticker"])
        if k in keys:
            return False
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a") as fh:
            fh.write(json.dumps({**{f: row[f] for f in ROW_FIELDS}, **self.extra}, sort_keys=False) + "\n")
        keys.add(k)
        return True
