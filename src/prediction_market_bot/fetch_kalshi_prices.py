"""
fetch_kalshi_prices.py — Pull pre-game forecast logs from VPS for EXP-017 data collection
==========================================================================================
Purpose:
    Sync pregame_YYYYMMDD.json files from the VPS to a local directory so that
    EXP-017 --from-pregame can accumulate data across multiple Finals games.
    Optionally also pulls the current paper portfolio for resolved outcomes.

Pipeline role:
    T-109 standing procedure (after each game day):
      1. run_resolve_local.py     — resolve positions, push updated portfolio to VPS
      2. fetch_kalshi_prices.py   — sync pregame files locally for EXP-017
      3. run_exp017.py --from-pregame exp_output/EXP-017/ --portfolio ...
         (optional re-run; only meaningful once >= 66 resolved markets accumulated)

Why pre-game logs are the right EXP-017 price source:
    - Settled Kalshi markets: last_price_dollars is contaminated by in-play trading
      (near 0 for NO outcome, near 1 for YES outcome) — unusable as a pre-game price.
    - Candlestick endpoint: returns 404 on public API — not available.
    - Pre-game logs (pregame_YYYYMMDD.json): captured at T1 cron (21:30 UTC night before)
      alongside model p_estimates and actual Kalshi mid/bid/ask prices. Clean.

Usage:
    # Pull pregame files only (default):
    PYTHONPATH=src python3 src/prediction_market_bot/fetch_kalshi_prices.py

    # Pull pregame files + paper portfolio:
    PYTHONPATH=src python3 src/prediction_market_bot/fetch_kalshi_prices.py --portfolio

    # Pull + immediately run EXP-017 (once enough data is available):
    PYTHONPATH=src python3 src/prediction_market_bot/fetch_kalshi_prices.py --portfolio --run-exp017

Security (NFR-05):
    Uses SSH key at ~/.ssh/id_ed25519_droplet (same as run_resolve_local.py).
    No API keys required. No order placement.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

# ---------------------------------------------------------------------------
# Config — must match run_resolve_local.py
# ---------------------------------------------------------------------------

VPS_HOST     = "root@157.230.91.33"
VPS_KEY      = Path.home() / ".ssh" / "id_ed25519_droplet"
VPS_LOG_DIR  = "/opt/prediction-market-bot/logs"
VPS_PORTFOLIO = f"{VPS_LOG_DIR}/paper_portfolio.json"

LOCAL_OUTPUT_DIR = Path("exp_output/EXP-017")
LOCAL_PORTFOLIO  = LOCAL_OUTPUT_DIR / "paper_portfolio.json"

_SSH_OPTS = [
    "-i", str(VPS_KEY),
    "-o", "StrictHostKeyChecking=no",
    "-o", "ConnectTimeout=15",
    "-o", "BatchMode=yes",
]


def _utc_now() -> str:
    return datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _check_key() -> None:
    if not VPS_KEY.exists():
        print(f"ERROR: SSH key not found: {VPS_KEY}", file=sys.stderr)
        print("  The key must exist at ~/.ssh/id_ed25519_droplet", file=sys.stderr)
        sys.exit(1)


def _list_remote_pregame_files() -> list[str]:
    """Return list of pregame_YYYYMMDD.json filenames on the VPS."""
    result = subprocess.run(
        ["ssh"] + _SSH_OPTS + [VPS_HOST, f"ls {VPS_LOG_DIR}/pregame_*.json 2>/dev/null"],
        capture_output=True, text=True, timeout=30,
    )
    if result.returncode != 0 and result.returncode != 1:
        print(f"ERROR: SSH failed (rc={result.returncode}): {result.stderr.strip()}", file=sys.stderr)
        sys.exit(1)
    lines = [line.strip() for line in result.stdout.splitlines() if line.strip()]
    return [Path(p).name for p in lines]


def _scp_pull(remote_path: str, local_path: Path) -> bool:
    """SCP a single file from VPS. Returns True on success."""
    result = subprocess.run(
        ["scp"] + _SSH_OPTS + [f"{VPS_HOST}:{remote_path}", str(local_path)],
        capture_output=True, text=True, timeout=30,
    )
    if result.returncode != 0:
        print(f"  ERROR pulling {remote_path}: {result.stderr.strip()}", file=sys.stderr)
        return False
    return True


def _summarise_pregame_file(local_path: Path) -> str:
    """One-line summary of a pregame file."""
    try:
        data = json.loads(local_path.read_text())
        n_actionable = data.get("actionable", "?")
        game_date    = data.get("game_date", "?")
        run_at       = data.get("run_at", "?")[:16]
        return f"game_date={game_date} | run_at={run_at} | actionable={n_actionable}"
    except Exception:
        return "(could not parse)"


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Sync pre-game forecast logs from VPS for EXP-017 data collection"
    )
    parser.add_argument(
        "--portfolio",
        action="store_true",
        default=False,
        help="Also pull the current paper_portfolio.json from VPS",
    )
    parser.add_argument(
        "--run-exp017",
        action="store_true",
        default=False,
        help="After pulling, run EXP-017 --from-pregame with the fetched data (requires --portfolio)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        default=False,
        help="Re-download files even if they already exist locally",
    )
    args = parser.parse_args()

    print(f"\n{'='*65}")
    print(f"fetch_kalshi_prices.py — VPS pre-game log sync")
    print(f"Run at: {_utc_now()}")
    print(f"Target: {LOCAL_OUTPUT_DIR.resolve()}")
    print(f"{'='*65}\n")

    _check_key()
    LOCAL_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # --- List remote pregame files ---
    print(f"[1/3] Listing remote pregame files on VPS ({VPS_HOST})...")
    remote_names = _list_remote_pregame_files()
    if not remote_names:
        print("  No pregame files found on VPS yet.")
    else:
        print(f"  Found {len(remote_names)} file(s): {', '.join(remote_names)}")

    # --- Pull missing (or all with --force) pregame files ---
    print(f"\n[2/3] Syncing pregame files to {LOCAL_OUTPUT_DIR}/...")
    n_skipped  = 0
    n_pulled   = 0
    n_failed   = 0
    for fname in remote_names:
        local_path  = LOCAL_OUTPUT_DIR / fname
        remote_path = f"{VPS_LOG_DIR}/{fname}"

        if local_path.exists() and not args.force:
            print(f"  SKIP  {fname} (already local)")
            n_skipped += 1
            continue

        print(f"  PULL  {fname}...", end=" ")
        ok = _scp_pull(remote_path, local_path)
        if ok:
            summary = _summarise_pregame_file(local_path)
            print(f"OK — {summary}")
            n_pulled += 1
        else:
            n_failed += 1

    print(f"\n  Pulled: {n_pulled}  |  Skipped (already local): {n_skipped}  |  Failed: {n_failed}")

    # --- Optionally pull portfolio ---
    if args.portfolio or args.run_exp017:
        print(f"\n[3/3] Pulling paper_portfolio.json...")
        ok = _scp_pull(VPS_PORTFOLIO, LOCAL_PORTFOLIO)
        if ok:
            try:
                data   = json.loads(LOCAL_PORTFOLIO.read_text())
                n_open = len(data.get("open_positions", []))
                n_closed = len(data.get("closed_positions", []))
                bankroll = data.get("bankroll_usd", "?")
                print(f"  OK — {n_closed} closed / {n_open} open positions | bankroll=${bankroll}")
            except Exception:
                print("  OK (could not parse summary)")
        else:
            if args.run_exp017:
                print("  ERROR: portfolio pull failed; cannot run EXP-017.", file=sys.stderr)
                sys.exit(1)
    else:
        print(f"\n[3/3] Portfolio pull skipped (use --portfolio to include)")

    # --- Optionally run EXP-017 ---
    if args.run_exp017:
        print(f"\n{'='*65}")
        print(f"Running EXP-017 --from-pregame ...")
        print(f"{'='*65}\n")
        import subprocess as _sp
        result = _sp.run(
            [
                sys.executable, "-m", "prediction_market_bot.run_exp017",
                "--from-pregame", str(LOCAL_OUTPUT_DIR),
                "--portfolio",    str(LOCAL_PORTFOLIO),
            ],
            cwd=Path.cwd(),
            env={**__import__("os").environ, "PYTHONPATH": "src"},
        )
        sys.exit(result.returncode)

    # --- Summary ---
    print(f"\n{'='*65}")
    print("DONE")
    print(f"{'='*65}")
    local_pregame = sorted(LOCAL_OUTPUT_DIR.glob("pregame_*.json"))
    print(f"  Local pregame files now available: {len(local_pregame)}")
    for f in local_pregame:
        summary = _summarise_pregame_file(f)
        print(f"    {f.name}: {summary}")
    if LOCAL_PORTFOLIO.exists():
        print(f"  Portfolio: {LOCAL_PORTFOLIO}")
    print(f"\n  To run EXP-017 Part B:")
    print(f"    PYTHONPATH=src python3 src/prediction_market_bot/run_exp017.py \\")
    print(f"        --from-pregame {LOCAL_OUTPUT_DIR} \\")
    print(f"        --portfolio {LOCAL_PORTFOLIO}")


if __name__ == "__main__":
    main()
