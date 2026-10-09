"""GG-527 (operator decision 2026-10-08, W61.1): fills-only execution evidence for T4M-PROJ.

W60.1 (#185) joined every epoch-12 T4M-PROJ row against the demo venue's own fill
history: 107 of 1,952 rows ever filled. A paper position whose order never filled is
model-calibration evidence only -- it is not execution evidence. This module is the
single place that decides which closed T4 positions count as execution evidence.

Sidecar, not a ledger edit: ``logs/t4_mlb_fill_status.jsonl``, one row per closed T4
position. No live-ledger row is ever rewritten. The sidecar itself is append-only for new
positions and never rewrites an existing row (same rule as the GG-228 guard).

Fill classes:
  CONFIRMED_FILLED      the venue's fill history carries a fill for this order (by
                        order_id, or by ticker+side within FALLBACK_WINDOW of entry)
  CONFIRMED_NOT_FILLED  no fill, and the position is inside the fill-history horizon
                        (or the order itself is canceled/expired with zero fill)
  UNVERIFIABLE          no fill found, but the position predates the retained history

Only GET calls, against the demo venue. Refuses BOT_ENV=live.

CLI (VPS): PYTHONPATH=src python3 -m prediction_market_bot.t4_fill_status \
               --portfolio logs/paper_portfolio_mlb_t4.json
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import sys
import time
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable, Iterable, Optional

logger = logging.getLogger(__name__)

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_PORTFOLIO = REPO_ROOT / "logs" / "paper_portfolio_mlb_t4.json"
DEFAULT_SIDECAR = REPO_ROOT / "logs" / "t4_mlb_fill_status.jsonl"

CONFIRMED_FILLED = "CONFIRMED_FILLED"
CONFIRMED_NOT_FILLED = "CONFIRMED_NOT_FILLED"
UNVERIFIABLE = "UNVERIFIABLE"
FILL_CLASSES = (CONFIRMED_FILLED, CONFIRMED_NOT_FILLED, UNVERIFIABLE)

FALLBACK_WINDOW = timedelta(seconds=180)
HORIZON_MARGIN = timedelta(hours=1)

# Label every all-rows figure carries wherever it is still printed (GG-527 (b)).
CALIBRATION_LABEL = "calibration only - not execution evidence"
EXECUTION_LABEL = "execution evidence: CONFIRMED_FILLED rows only"


def parse_ts(s: Any) -> Optional[datetime]:
    if not s:
        return None
    try:
        return datetime.fromisoformat(str(s).replace("Z", "+00:00")).astimezone(timezone.utc)
    except ValueError:
        return None


# ---------------------------------------------------------------------------
# Sidecar I/O
# ---------------------------------------------------------------------------

def load_fill_status(path: Path = DEFAULT_SIDECAR) -> dict[str, dict]:
    """position_id -> sidecar row. Missing file -> {} (nothing counts as filled)."""
    out: dict[str, dict] = {}
    path = Path(path)
    if not path.exists():
        return out
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            logger.warning("t4_fill_status: skipping unparseable sidecar line")
            continue
        pid = row.get("position_id")
        if pid and pid not in out:  # first row wins; sidecar rows are never rewritten
            out[pid] = row
    return out


def is_confirmed_filled(rec: dict, status: dict[str, dict]) -> bool:
    row = status.get(rec.get("position_id"))
    return bool(row) and row.get("fill_class") == CONFIRMED_FILLED


def filter_confirmed_filled(recs: Iterable[dict], status: dict[str, dict]) -> list[dict]:
    """Execution-evidence subset of ``recs`` (anything not CONFIRMED_FILLED is dropped,
    including positions with no sidecar row yet -- conservative by construction)."""
    return [r for r in recs if is_confirmed_filled(r, status)]


# ---------------------------------------------------------------------------
# Classification (pure -- venue access is injected)
# ---------------------------------------------------------------------------

def classify_position(
    pos: dict,
    fills_by_order: dict[str, list[dict]],
    fills_by_ticker: dict[str, list[dict]],
    horizon: Optional[datetime],
    order_lookup: Optional[Callable[[str], dict]] = None,
) -> tuple[str, str, list[str]]:
    """-> (fill_class, how, matched_fill_ids). Logic lifted from W60.1's
    scripts/w60_1_cohort_fill_truth.py so the audited result is reproduced exactly."""
    oid, tk = pos.get("kalshi_order_id"), pos.get("kalshi_ticker")
    et = parse_ts(pos.get("entered_at"))
    side = str(pos.get("direction") or "").lower()

    if oid and oid in fills_by_order:
        ids = [str(f.get("fill_id") or f.get("trade_id") or "") for f in fills_by_order[oid]]
        return CONFIRMED_FILLED, "order_id", [i for i in ids if i]
    if et:
        cands = []
        for f in fills_by_ticker.get(tk, []):
            t = parse_ts(f.get("created_time"))
            if (f.get("side") or "").lower() == side and t and abs(t - et) <= FALLBACK_WINDOW:
                cands.append(f)
        if cands:
            ids = [str(f.get("fill_id") or f.get("trade_id") or "") for f in cands]
            return CONFIRMED_FILLED, "fallback_ticker_side_window", [i for i in ids if i]

    if order_lookup is not None and oid:
        looked = order_lookup(oid)
        if looked.get("verdict") == "FILLED":
            return CONFIRMED_FILLED, "order_lookup_filled", []
        if looked.get("verdict") == "CANCELED":
            return CONFIRMED_NOT_FILLED, "order_lookup_canceled", []
    if horizon and et and et >= horizon + HORIZON_MARGIN:
        return CONFIRMED_NOT_FILLED, "inside_fills_horizon_no_match", []
    return UNVERIFIABLE, "outside_horizon_or_no_timestamp", []


def index_fills(fills: list[dict]) -> tuple[dict[str, list[dict]], dict[str, list[dict]]]:
    by_order: dict[str, list[dict]] = defaultdict(list)
    by_ticker: dict[str, list[dict]] = defaultdict(list)
    for f in fills:
        by_order[f.get("order_id")].append(f)
        by_ticker[f.get("ticker")].append(f)
    return by_order, by_ticker


def closed_t4_positions(portfolio_path: Path) -> list[dict]:
    with open(portfolio_path) as fh:
        data = json.load(fh)
    return [p for p in data.get("closed_positions", []) if p.get("position_id")]


def classify_new_positions(
    positions: list[dict],
    fills: list[dict],
    fills_complete: bool,
    existing: dict[str, dict],
    order_lookup: Optional[Callable[[str], dict]] = None,
    now: Optional[datetime] = None,
) -> list[dict]:
    """Rows for positions with no sidecar row yet. Never touches ``existing``.

    ``fills_complete`` False (pagination stopped early) -> the horizon is unknown, so a
    no-match position can only be UNVERIFIABLE, never CONFIRMED_NOT_FILLED."""
    now = now or datetime.now(timezone.utc)
    by_order, by_ticker = index_fills(fills)
    fts = sorted(t for t in (parse_ts(f.get("created_time")) for f in fills) if t)
    horizon = fts[0] if (fts and fills_complete) else None
    out = []
    for pos in positions:
        pid = pos.get("position_id")
        if pid in existing:
            continue
        label, how, ids = classify_position(pos, by_order, by_ticker, horizon, order_lookup)
        out.append({
            "position_id": pid,
            "kalshi_order_id": pos.get("kalshi_order_id"),
            "band": pos.get("band"),
            "kalshi_ticker": pos.get("kalshi_ticker"),
            "fill_class": label,
            "how": how,
            "matched_fill_ids": ids,
            "classified_at": now.isoformat(),
        })
    return out


def append_sidecar(rows: list[dict], path: Path = DEFAULT_SIDECAR) -> int:
    """Append-only. Re-reads the file under the write so a concurrent run cannot
    duplicate a position_id; an existing row is never replaced."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    seen = set(load_fill_status(path))
    fresh = [r for r in rows if r["position_id"] not in seen]
    if fresh:
        with open(path, "a") as fh:
            for r in fresh:
                fh.write(json.dumps(r, default=str) + "\n")
    return len(fresh)


# ---------------------------------------------------------------------------
# Venue access (demo-only, GET-only)
# ---------------------------------------------------------------------------

def _load_dotenv_if_needed(env_path: Path) -> None:
    """The weekly cron line does not export .env; load missing VENUE_* / BOT_ENV here."""
    if not env_path.exists():
        return
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        k, v = k.strip(), v.strip().strip('"').strip("'")
        if k in ("VENUE_API_KEY", "VENUE_PRIVATE_KEY_PATH") and not os.environ.get(k):
            os.environ[k] = v


def _paginate(client: Any, path: str, key: str, limit: int = 1000) -> tuple[list[dict], bool]:
    items: list[dict] = []
    cursor = None
    while True:
        params: dict[str, Any] = {"limit": limit}
        if cursor:
            params["cursor"] = cursor
        ok, data = client._get(path, params=params, authenticated=True)
        if not ok:
            logger.warning("t4_fill_status: %s pagination stopped: %s", path, str(data)[:200])
            return items, False
        batch = data.get(key, [])
        items.extend(batch)
        cursor = data.get("cursor")
        if not cursor or not batch:
            return items, True
        time.sleep(0.15)


def run_classifier(
    portfolio_path: Path = DEFAULT_PORTFOLIO,
    sidecar_path: Path = DEFAULT_SIDECAR,
    client: Any = None,
) -> dict:
    """Classify every closed T4 position that has no sidecar row yet and append the
    rows. Returns counts. Never raises on a venue/credential problem: it returns
    ``{"status": "SKIPPED", "reason": ...}`` and leaves the sidecar untouched (a position
    with no row simply does not count as execution evidence)."""
    # Demo only. BOT_ENV is blank in the VPS .env; the other crons set paper explicitly.
    if os.environ.get("BOT_ENV", "").lower() == "live":
        return {"status": "SKIPPED", "reason": "BOT_ENV=live (demo-only)"}
    os.environ["BOT_ENV"] = "paper"

    if client is None:
        _load_dotenv_if_needed(REPO_ROOT / ".env")
        try:
            from prediction_market_bot.c5_execution.kalshi_client import KalshiMarketClient
            client = KalshiMarketClient.from_env()
        except Exception as exc:  # missing creds etc.
            return {"status": "SKIPPED", "reason": f"client unavailable: {exc}"}
        if not client.has_signing_key():
            return {"status": "SKIPPED", "reason": "no signing key"}

    positions = closed_t4_positions(Path(portfolio_path))
    existing = load_fill_status(sidecar_path)
    todo = [p for p in positions if p["position_id"] not in existing]
    if not todo:
        return {"status": "OK", "closed_positions": len(positions), "already_classified": len(existing),
                "appended": 0, "counts": {}}

    fills, complete = _paginate(client, "/portfolio/fills", "fills")
    if not fills and not complete:
        return {"status": "SKIPPED", "reason": "fills history unavailable"}

    def order_lookup(order_id: str) -> dict:
        from t571_verify_t4mproj_kalshi_fills import check_order  # scripts/ on sys.path in CLI use
        time.sleep(0.15)
        return check_order(client, order_id)

    # Order lookup only matters for positions the fills history cannot settle; it is
    # 1 GET per such position, and only for the first run's outside-horizon remainder.
    try:
        import t571_verify_t4mproj_kalshi_fills  # noqa: F401
        lookup: Optional[Callable[[str], dict]] = order_lookup
    except ImportError:
        lookup = None

    rows = classify_new_positions(todo, fills, complete, existing, lookup)
    appended = append_sidecar(rows, sidecar_path)
    return {"status": "OK", "closed_positions": len(positions), "already_classified": len(existing),
            "appended": appended, "fills_complete": complete, "n_fills": len(fills),
            "counts": dict(Counter(r["fill_class"] for r in rows))}


def main(argv: Optional[list[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="GG-527: classify closed T4 positions by venue fill status")
    ap.add_argument("--portfolio", type=Path, default=DEFAULT_PORTFOLIO)
    ap.add_argument("--sidecar", type=Path, default=DEFAULT_SIDECAR)
    a = ap.parse_args(argv)
    sys.path.insert(0, str(REPO_ROOT / "scripts"))
    result = run_classifier(a.portfolio, a.sidecar)
    print(json.dumps(result, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
