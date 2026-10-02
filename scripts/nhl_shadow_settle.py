#!/usr/bin/env python3
"""Settlement join for NHL shadow ledgers (T-607 / EXP-036). Read-only Kalshi reads.

For every shadow row whose market has settled, append one row to
``<root>/settled/<cell>.jsonl`` (idempotent per (run_id, market_ticker)) carrying the outcome
and the model/market squared errors. Never writes to the shadow ledgers themselves.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from prediction_market_bot.c1_signal_ingestion import nhl_ingest as ni  # noqa: E402

KALSHI = "https://api.elections.kalshi.com/trade-api/v2"
SHADOW_DIR = Path("data/shadow/nhl")


def outcome_of(market: dict):
    """1/0 when settled with a yes/no result, else None (open, voided or fair-price)."""
    if market.get("status") not in ("settled", "finalized"):
        return None
    return {"yes": 1, "no": 0}.get(market.get("result"))


def settle_rows(rows: list[dict], markets: dict[str, dict]) -> list[dict]:
    out = []
    for r in rows:
        y = outcome_of(markets.get(r["market_ticker"], {}))
        if y is None:
            continue
        out.append({"run_id": r["run_id"], "market_ticker": r["market_ticker"], "market_type": r["market_type"],
                    "band": r["band"], "outcome": y, "p_yes": r["p_yes"], "mid": r["mid"],
                    "brier_model": (r["p_yes"] - y) ** 2, "brier_market": (r["mid"] - y) ** 2,
                    "model_id": r["model_id"], "e_net_yes_k007": r["e_net_yes_k007"],
                    "e_net_no_k007": r["e_net_no_k007"], "start_time_utc": r["start_time_utc"]})
    return out


def read_cell_rows(root: Path) -> dict[Path, list[dict]]:
    return {p: [json.loads(l) for l in p.read_text().splitlines() if l.strip()]
            for p in sorted(root.glob("NHL_*.jsonl"))}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=str(SHADOW_DIR))
    a = ap.parse_args(argv)
    root = Path(a.root)
    cells = read_cell_rows(root)
    th = ni.Throttle(1.0)
    markets: dict[str, dict] = {}
    done: dict[Path, set] = {}
    for p, rows in cells.items():
        sp = root / "settled" / p.name
        done[p] = {(d["run_id"], d["market_ticker"]) for d in
                   (json.loads(l) for l in sp.read_text().splitlines() if l.strip())} if sp.exists() else set()
    todo = {r["market_ticker"] for p, rows in cells.items() for r in rows
            if (r["run_id"], r["market_ticker"]) not in done[p]}
    for t in sorted(todo):
        try:
            markets[t] = ni.http_get_json(f"{KALSHI}/markets/{t}", th).get("market", {})
        except ni.NhlHttpError:
            continue
    n = 0
    for p, rows in cells.items():
        new = [r for r in settle_rows(rows, markets) if (r["run_id"], r["market_ticker"]) not in done[p]]
        if new:
            sp = root / "settled" / p.name
            sp.parent.mkdir(parents=True, exist_ok=True)
            with sp.open("a") as f:
                for r in new:
                    f.write(json.dumps(r, sort_keys=True) + "\n")
        n += len(new)
    print(json.dumps({"tickers_checked": len(todo), "settled_rows_appended": n}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
