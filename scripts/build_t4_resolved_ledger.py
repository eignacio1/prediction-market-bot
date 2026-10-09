#!/usr/bin/env python3
"""
T-254 — T4M-PROJ Resolved-Outcome Ledger
GG-099 | ADR-0042 D2 | Companion to run_exp017_mlb.py

CONTEXT (corrected scope — see GOVERNANCE_GAP_LOG.md GG-099 correction, 2026-07-08)
------------------------------------------------------------------------------------
GG-099 originally claimed T4M-PROJ (the ACTIVE MLB T4 band, `run_t4_mlb_live.py`)
had "no resolved-outcome join at all," citing `t4_position_trajectories.jsonl`.
Direct inspection found that file is 100% NBA data (KXNBAPTS/NBA_TEST/NBA_EXIT_TES
tickers) — it belongs to the dark/frozen NBA T4 band, not MLB. This is the GG-061
NBA/MLB-T4-conflation failure mode recurring.

The real state: `run_resolve_mlb.py` already resolves the isolated T4 MLB pool
(`paper_portfolio_mlb_t4.json`, via the shared `_resolve_pool()` helper) exactly
like it resolves the T1/T2 pool. Every closed position already carries
`outcome`/`pnl`/`model_p`/`mid_price_at_entry` (mip)/`vig_at_entry`. The resolved
join is NOT missing — it is just never extracted into a stable, analysis-ready
artifact independent of the live-mutating portfolio JSON, and the stored
`fee_net_edge` field is YES-frame-only and wrong-signed for NO bets (GG-077).

This script closes that actual gap: it reads the T4 MLB portfolio's
`closed_positions`, recomputes edge direction-aware via the audited
`run_exp017_mlb.compute_fee_net_edge` helper (GG-077 — do not reimplement),
tags every row `band=T4M-PROJ`, and writes a stable JSONL ledger that
downstream per-band monitors (T-255) can consume the same way
`run_exp017_mlb.py` already consumes the T1 book.

2026-07-08 (T-255): added `size_usd` to the ledger row. It was present in the
raw T4 portfolio source all along but not carried into the original ledger —
T-255's per-band monitor needs it for the $/staked metric, same as the T1/T2/T3
loader (`run_exp017b_decomp_mlb.load_records`) already exposes via `_size`.

2026-07-10 (T-322): added `logic_epoch`/`approval_commit` passthrough. T-320
stamps both fields on every position `paper_trader.py::open_position()` writes,
including T4 MLB, but this script builds each ledger row from a fresh dict
literal rather than `dict(p)` (unlike the T1/T2/T3 loader), so the fields were
silently dropped. Without them, `run_band_monitor.py` could not compute
clean_n for T4M-PROJ at all.

Run:
  python3 scripts/build_t4_resolved_ledger.py                    # use existing local cache
  python3 scripts/build_t4_resolved_ledger.py --pull             # ssh-refresh cache from VPS first
  python3 scripts/build_t4_resolved_ledger.py --portfolio PATH   # read an arbitrary portfolio JSON
  python3 scripts/build_t4_resolved_ledger.py --out PATH         # override ledger output path
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import run_exp017_mlb as e17  # noqa: E402  reuse compute_fee_net_edge (GG-077 direction-aware)

REPO_ROOT = Path(__file__).resolve().parents[1]
BAND = "T4M-PROJ"
VPS_ALIAS = "prediction-market-vps"
VPS_PORTFOLIO_PATH = "/opt/prediction-market-bot/logs/paper_portfolio_mlb_t4.json"
DEFAULT_CACHE = Path("logs/.vps_portfolio_cache_mlb_t4.json")
DEFAULT_OUT = Path("logs/t4_mlb_resolved_ledger.jsonl")


def pull_vps_cache(cache_path: Path) -> bool:
    """Mirrors governance_scan.sh's ssh-cache pattern (ConnectTimeout=3, BatchMode)."""
    cache_path.parent.mkdir(parents=True, exist_ok=True)  # GG-138: logs/ is gitignored, absent on a fresh worktree
    tmp = cache_path.with_suffix(cache_path.suffix + ".tmp")
    try:
        result = subprocess.run(
            ["ssh", "-o", "ConnectTimeout=3", "-o", "BatchMode=yes", VPS_ALIAS,
             f"cat {VPS_PORTFOLIO_PATH}"],
            capture_output=True, timeout=15,
        )
        if result.returncode != 0 or not result.stdout:
            print(f"pull_vps_cache: ssh/cat failed (rc={result.returncode}): "
                  f"{result.stderr.decode(errors='replace').strip()}", file=sys.stderr)
            return False
        json.loads(result.stdout)  # validate before committing
        tmp.write_bytes(result.stdout)
        tmp.replace(cache_path)
        return True
    except Exception as exc:
        print(f"pull_vps_cache: {type(exc).__name__}: {exc}", file=sys.stderr)
        tmp.unlink(missing_ok=True)
        return False


def build_ledger(portfolio_path: Path) -> tuple[list[dict], int]:
    """
    Extract every CLOSED T4 MLB position into a normalized ledger row.
    Returns (rows, n_open) — n_open is a visibility count, not part of the ledger
    (open positions have no outcome yet and are not measurable).
    """
    with open(portfolio_path) as fh:
        data = json.load(fh)

    rows: list[dict] = []
    for p in data.get("closed_positions", []):
        outcome = p.get("outcome", "")
        if outcome not in ("WIN", "LOSS"):
            continue
        raw_model_p = p.get("model_p")
        if raw_model_p is None:
            continue
        try:
            model_p = float(raw_model_p)
            mip = float(p["mid_price_at_entry"])
            vig = float(p.get("vig_at_entry", 0.0))
        except (KeyError, TypeError, ValueError):
            continue
        direction = str(p.get("direction", "YES"))
        # GG-077: never trust the stored fee_net_edge (YES-frame only, wrong-signed
        # for NO bets). Recompute via the audited, direction-aware helper.
        edge = e17.compute_fee_net_edge(direction, model_p, mip)
        try:
            threshold = int(p.get("kalshi_threshold", p.get("threshold", 0)))
        except (TypeError, ValueError):
            threshold = 0
        rows.append({
            "band": BAND,
            "position_id": p.get("position_id"),
            "forecast_id": p.get("forecast_id"),
            "kalshi_ticker": p.get("kalshi_ticker", ""),
            "player_name": p.get("player_name", ""),
            "player_id": p.get("player_id"),
            "threshold": threshold,
            "direction": direction,
            "game_date": p.get("game_date", ""),
            "entered_at": p.get("entered_at"),
            "resolved_at": p.get("resolved_at"),
            "model_p": model_p,
            "mip": mip,
            "vig": vig,
            "edge": edge,
            "outcome": outcome,
            "pnl": float(p.get("pnl", 0.0) or 0.0),
            "size_usd": float(p.get("size_usd", 0.0) or 0.0),
            "actual_hits": p.get("actual_hits"),
            # T-322: pass through T-320's write-path provenance stamp so
            # downstream clean_n filtering (run_band_monitor.py) works for
            # T4M-PROJ, not just the T1/T2/T3 loader (which copies via dict(p)).
            "logic_epoch": p.get("logic_epoch"),
            "approval_commit": p.get("approval_commit"),
            # T-595 D2: pass the pool row's model_identity through UNCHANGED — no default,
            # no relabel, no repair (GG-228). Absent stays None, "UNKNOWN" stays "UNKNOWN";
            # logic_epoch.evidence_class() classifies both UNATTRIBUTED. Closes GG-319's drop
            # for rows written from now on; the monitor itself is not changed.
            "model_identity": p.get("model_identity"),
        })

    n_open = len(data.get("open_positions", []))
    return rows, n_open


def write_jsonl(rows: list[dict], out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as fh:
        for row in sorted(rows, key=lambda r: r.get("resolved_at") or ""):
            fh.write(json.dumps(row) + "\n")


def _row_key(row: dict) -> str:
    return str(row.get("position_id") or json.dumps(row, sort_keys=True))


def _read_existing(path: Path) -> tuple[list[dict] | None, str | None]:
    """Returns (rows, None), or (None, reason) when the file cannot be read as a ledger."""
    rows: list[dict] = []
    try:
        with open(path) as fh:
            for line in fh:
                if line.strip():
                    rows.append(json.loads(line))
    except (OSError, ValueError) as exc:
        return None, f"{type(exc).__name__}: {exc}"
    return rows, None


def diff_ledgers(existing: list[dict], rebuilt: list[dict]) -> dict:
    """GG-228: classify rebuilt vs existing by position_id. Added rows are safe;
    a changed or removed existing row means the rebuild would overwrite state."""
    old = {_row_key(r): r for r in existing}
    new = {_row_key(r): json.loads(json.dumps(r)) for r in rebuilt}
    changed = sorted(k for k in old if k in new and old[k] != new[k])
    removed = sorted(k for k in old if k not in new)
    added = sorted(k for k in new if k not in old)
    return {"changed": changed, "removed": removed, "added": added}


def guarded_write(rows: list[dict], out_path: Path) -> tuple[Path, dict | None]:
    """Write the ledger without clobbering a repaired file (GG-228).

    Returns (path_written, diff). If any existing row would change or disappear the
    live file is left untouched and the rebuild lands beside it as
    <name>.rebuild_<UTC>.jsonl; the caller still exits 0."""
    tmp = out_path.with_name(out_path.name + ".tmp")
    write_jsonl(rows, tmp)
    if not out_path.exists():
        os.replace(tmp, out_path)
        return out_path, None
    existing, err = _read_existing(out_path)
    if existing is None:
        diff = {"changed": [], "removed": [], "added": [], "unreadable": err}
        differs = 1
    else:
        diff = diff_ledgers(existing, json.loads(json.dumps(rows)))
        differs = len(diff["changed"]) + len(diff["removed"])
    if differs:
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        side = out_path.with_name(f"{out_path.stem}.rebuild_{stamp}{out_path.suffix}")
        os.replace(tmp, side)
        logging.getLogger("build_t4_resolved_ledger").warning(
            "GG-228 GUARD: %d existing row(s) differ from rebuild (changed=%d removed=%d%s); "
            "NOT overwriting %s; rebuild written to %s",
            differs, len(diff["changed"]), len(diff["removed"]),
            f" unreadable={diff['unreadable']}" if "unreadable" in diff else "", out_path, side)
        return side, diff
    os.replace(tmp, out_path)
    return out_path, diff


def _print_summary(rows: list[dict], n_open: int, portfolio_path: Path, out_path: Path) -> None:
    n = len(rows)
    wins = sum(1 for r in rows if r["outcome"] == "WIN")
    total_pnl = sum(r["pnl"] for r in rows)
    tickers = {r["kalshi_ticker"] for r in rows}
    print("=" * 68)
    print(f"T4 MLB Resolved Ledger — band={BAND}")
    print("=" * 68)
    print(f"  Source:        {portfolio_path}")
    print(f"  Output:        {out_path}")
    print(f"  Resolved rows: {n}  (win={wins}, loss={n - wins}, win_rate={wins / n:.3f})" if n
          else "  Resolved rows: 0")
    print(f"  Unique tickers among resolved: {len(tickers)}  "
          f"(re-entries: {n - len(tickers)} — T4 legitimately re-evaluates the same "
          f"ticker across cycles; this is NOT the T1 duplicate_of case)")
    print(f"  Total P&L:     ${total_pnl:+.4f}")
    print(f"  Still open (not yet resolvable): {n_open}")
    print("=" * 68)


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Build the T4M-PROJ resolved-outcome ledger (T-254 / GG-099)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    p.add_argument("--portfolio", metavar="PATH", default=str(DEFAULT_CACHE),
                    help=f"T4 MLB portfolio JSON (default: {DEFAULT_CACHE})")
    p.add_argument("--pull", action="store_true",
                    help="ssh-refresh the VPS cache before building the ledger")
    p.add_argument("--out", metavar="PATH", default=str(DEFAULT_OUT),
                    help=f"Ledger output path (default: {DEFAULT_OUT})")
    return p


def main(argv=None) -> int:
    args = _build_parser().parse_args(argv)
    portfolio_path = Path(args.portfolio)

    if args.pull:
        if not pull_vps_cache(portfolio_path):
            print(f"WARNING: VPS pull failed; falling back to existing {portfolio_path}",
                  file=sys.stderr)

    if not portfolio_path.exists():
        print(f"ERROR: portfolio not found: {portfolio_path}", file=sys.stderr)
        print("  Run with --pull to fetch the live VPS T4 MLB book first.", file=sys.stderr)
        return 1

    rows, n_open = build_ledger(portfolio_path)
    out_path = Path(args.out)
    logging.basicConfig(format="%(levelname)s %(message)s")
    written, _ = guarded_write(rows, out_path)
    _print_summary(rows, n_open, portfolio_path, written)
    _classify_fills(portfolio_path)
    return 0


def _classify_fills(portfolio_path: Path) -> None:
    """GG-527: keep logs/t4_mlb_fill_status.jsonl current from the already-scheduled weekly
    ledger build (Mon 14:20 cron) -- no new cron line. Runs only against the live VPS
    book (logs/paper_portfolio_mlb_t4.json), never a local cache. Never fails the build:
    on any problem the sidecar is untouched and unclassified positions simply do not
    count as execution evidence."""
    try:
        sys.path.insert(0, str(REPO_ROOT / "src"))
        sys.path.insert(0, str(REPO_ROOT / "scripts"))
        from prediction_market_bot import t4_fill_status as tfs
        if portfolio_path.resolve() != tfs.DEFAULT_PORTFOLIO.resolve():
            return
        result = tfs.run_classifier(portfolio_path, tfs.DEFAULT_SIDECAR)
        print(f"  Fill-status sidecar (GG-527): {json.dumps(result)}")
    except Exception as exc:  # noqa: BLE001
        print(f"  Fill-status sidecar (GG-527): SKIPPED {type(exc).__name__}: {exc}", file=sys.stderr)


if __name__ == "__main__":
    raise SystemExit(main())
