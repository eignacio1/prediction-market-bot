"""
Walk-Forward Backtest Runner — EXP-002, EXP-003
================================================
Experiment IDs:  EXP-002, EXP-003
Phase:           Phase 3 (Research Build)
Status:          CANONICAL RUNNER — 2026-05-27
Snapshots:       SNAP-2026-05-27-001 (reuse EXP-001 raw game logs via --raw-csv)
                 SNAP-2026-05-27-002 (fresh C1 pull — registered in DATA_SNAPSHOTS_INDEX.md)

Hypotheses tested:
  EXP-002 — HYP-001 (second independent window — 2021-22 season second half)
  EXP-003 — HYP-001 + HYP-004 (third window — 2021-22 season early-mid; signal stability)

Pipeline: C1 → C2 → C3 → C4 (C4 will REJECT at phase gate — expected)
Framework: Backtester (backtester.py)

How to run:
    From project root (with package installed: pip install -e .):

        # Reuse existing EXP-001 raw CSV (no fresh API pull — recommended):
        python -m prediction_market_bot.run_backtest \\
            --raw-csv exp_output/EXP-001/SNAP-2026-05-27-001_raw_game_logs.csv \\
            --output-dir exp_output/BACKTEST

        # Fresh C1 pull (registers SNAP-2026-05-27-002):
        python -m prediction_market_bot.run_backtest \\
            --output-dir exp_output/BACKTEST

        # Run specific windows only:
        python -m prediction_market_bot.run_backtest \\
            --raw-csv exp_output/EXP-001/SNAP-2026-05-27-001_raw_game_logs.csv \\
            --window exp002

        # Dry run (no disk writes):
        python -m prediction_market_bot.run_backtest \\
            --raw-csv exp_output/EXP-001/SNAP-2026-05-27-001_raw_game_logs.csv \\
            --dry-run

Security (NFR-05, NFR-07):
    - No API keys required. nba_api is a public endpoint scraper.
    - BOT_C4_ACTIVE must NOT be set in ENV-01 / ENV-02.
    - No live capital. No venue API calls.

Temporal integrity (TI-01–TI-04):
    - All features computed from prior games only (.shift(1) before .rolling()).
    - Each window's train/val/test labels are strictly chronological.
    - TEST rows are NEVER accessed in this runner.
    - The 2023-24 season data remains TEST for EXP-002 and EXP-003.

Window definitions (non-overlapping validation periods):
    EXP-002: Train ≤ 2022-01-31 | Val: 2022-02-01 – 2022-04-10
    EXP-003: Train ≤ 2021-12-15 | Val: 2021-12-16 – 2022-01-31

Snapshot policy:
    If --raw-csv is provided: cites SNAP-2026-05-27-001 (no new ingestion).
    If fresh pull: registers SNAP-2026-05-27-002 and saves to output_dir.
"""

from __future__ import annotations

import argparse
import sys
import uuid
from pathlib import Path

import pandas as pd

# ---------------------------------------------------------------------------
# Ensure src/ is on sys.path when run directly (not via -m)
# ---------------------------------------------------------------------------
_SRC_ROOT = Path(__file__).parent.parent.parent
if str(_SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(_SRC_ROOT))

from prediction_market_bot.backtester import Backtester, BacktestWindowDef  # noqa: E402
from prediction_market_bot.c1_signal_ingestion.ingestion import NBAIngestionClient  # noqa: E402
from prediction_market_bot.c6_audit_logger.audit_logger import AuditLogger  # noqa: E402

# ---------------------------------------------------------------------------
# Snapshot IDs
# ---------------------------------------------------------------------------

# SNAP-2026-05-27-001: EXP-001 raw game logs — reused when --raw-csv is provided
SNAPSHOT_ID_REUSE = "SNAP-2026-05-27-001"

# SNAP-2026-05-27-002: Fresh backtest ingestion — registered in DATA_SNAPSHOTS_INDEX.md
SNAPSHOT_ID_FRESH = "SNAP-2026-05-27-002"

# ---------------------------------------------------------------------------
# Players and seasons (same cohort as EXP-001 — same feature version)
# ---------------------------------------------------------------------------

TARGET_PLAYER_IDS: list[int] = [
    2544,      # LeBron James
    201142,    # Kevin Durant
    201939,    # Stephen Curry
    203507,    # Giannis Antetokounmpo
    203999,    # Nikola Jokic
    203954,    # Joel Embiid
    203081,    # Damian Lillard
    1629029,   # Luka Doncic
    1628369,   # Jayson Tatum
    202710,    # Jimmy Butler
]

TARGET_SEASONS: list[str] = ["2021-22", "2022-23", "2023-24"]
SEASON_TYPE = "Regular Season"

# ---------------------------------------------------------------------------
# Window definitions
# (ordered oldest-first for walk-forward convention)
#
# EXP-002: 2021-22 season second half
#   Train: all games through 2022-01-31 (first ~55 games of 2021-22 season per player)
#   Val  : 2022-02-01 – 2022-04-10 (final ~35 games of 2021-22 regular season)
#   Tests HYP-001 as a second independent temporal window.
#
# EXP-003: 2021-22 season early-mid
#   Train: all games through 2021-12-15 (first ~35 games of 2021-22 season per player)
#   Val  : 2021-12-16 – 2022-01-31 (games ~35–55 of 2021-22 season)
#   Tests HYP-001 (third window) and HYP-004 (signal stability — earliest window).
#   Non-overlapping with EXP-002 validation period.
# ---------------------------------------------------------------------------

BACKTEST_WINDOWS: dict[str, BacktestWindowDef] = {
    "exp002": BacktestWindowDef(
        exp_id="EXP-002",
        train_end_date="2022-01-31",
        val_end_date="2022-04-10",
        description="Window 2 — 2021-22 season second half (HYP-001 second evidence)",
        snapshot_id=SNAPSHOT_ID_REUSE,   # updated to FRESH if fresh pull
    ),
    "exp003": BacktestWindowDef(
        exp_id="EXP-003",
        train_end_date="2021-12-15",
        val_end_date="2022-01-31",
        description="Window 3 — 2021-22 season early-mid (HYP-001 + HYP-004 stability)",
        snapshot_id=SNAPSHOT_ID_REUSE,   # updated to FRESH if fresh pull
    ),
}


# ---------------------------------------------------------------------------
# Kill-switch helper (research environment)
# ---------------------------------------------------------------------------

def _kill_switch(reason: str) -> None:
    """
    Research-phase kill switch.
    In ENV-01 this halts the runner with a non-zero exit code.
    """
    print(f"\n[KILL SWITCH TRIGGERED] {reason}", file=sys.stderr)
    sys.exit(1)


# ---------------------------------------------------------------------------
# Main runner
# ---------------------------------------------------------------------------

def run_backtest(
    output_dir: Path,
    raw_csv: Path | None,
    windows_to_run: list[str],
    dry_run: bool = False,
) -> list[dict]:
    """
    Execute walk-forward backtesting across the specified windows.

    Parameters
    ----------
    output_dir : Path
        Base directory for backtest outputs. Each window writes to
        output_dir / EXP-NNN /.
    raw_csv : Path | None
        Path to a pre-ingested raw game logs CSV (SNAP-2026-05-27-001).
        If None, a fresh C1 pull is performed and SNAP-2026-05-27-002 is used.
    windows_to_run : list[str]
        Keys from BACKTEST_WINDOWS (e.g., ["exp002", "exp003"]).
        Processed oldest-first (EXP-003 before EXP-002 in chronological order,
        but both can be run in either order since they're independent).
    dry_run : bool
        If True, skip writing output CSVs. Metrics still computed and logged.

    Returns
    -------
    list[dict] — summary dicts for each completed window.
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # 1. Initialize C6 AuditLogger
    # ------------------------------------------------------------------
    session_id = f"BACKTEST-INIT-{uuid.uuid4().hex[:8].upper()}"
    log_path = output_dir / "audit_backtest_init.jsonl"
    logger = AuditLogger(log_path=log_path, min_severity="DEBUG")

    ok = logger.info(
        "BACKTEST_RUNNER",
        "backtest_run_start",
        payload={
            "session_id": session_id,
            "windows": windows_to_run,
            "raw_csv": str(raw_csv) if raw_csv else None,
            "fresh_pull": raw_csv is None,
            "dry_run": dry_run,
            "output_dir": str(output_dir),
        },
        session_id=session_id,
        snapshot_id=SNAPSHOT_ID_REUSE,
    )
    if not ok:
        _kill_switch("C6 AuditLogger write failure at backtest_run_start")

    print(f"\n{'='*60}")
    print(f"Walk-Forward Backtest Runner")
    print(f"Windows: {', '.join(w.upper() for w in windows_to_run)}")
    print(f"Session: {session_id}")
    print(f"Log: {log_path}")
    print(f"{'='*60}")

    # ------------------------------------------------------------------
    # 2. Determine snapshot ID and load/fetch raw data
    # ------------------------------------------------------------------
    if raw_csv is not None:
        # Reuse pre-ingested snapshot — no new API call
        snapshot_id = SNAPSHOT_ID_REUSE
        if not raw_csv.exists():
            _kill_switch(
                f"--raw-csv file not found: {raw_csv}\n"
                "Run EXP-001 first to generate the raw game logs, or omit --raw-csv "
                "to trigger a fresh C1 pull."
            )
        print(f"\n[C1] Loading cached game logs from {raw_csv}")
        raw_df = pd.read_csv(raw_csv)
        print(f"[C1] Loaded {len(raw_df):,} rows | "
              f"{raw_df['player_id'].nunique()} players | "
              f"{raw_df['season'].nunique()} seasons")

        ok = logger.info(
            "C1",
            "raw_data_loaded_from_cache",
            payload={
                "snapshot_id": snapshot_id,
                "raw_csv": str(raw_csv),
                "total_rows": len(raw_df),
                "player_count": int(raw_df["player_id"].nunique()),
                "season_count": int(raw_df["season"].nunique()),
            },
            session_id=session_id,
            snapshot_id=snapshot_id,
        )
        if not ok:
            _kill_switch("C6 write failure after loading cached raw data")

    else:
        # Fresh C1 pull — registers SNAP-2026-05-27-002
        snapshot_id = SNAPSHOT_ID_FRESH
        fresh_csv_path = output_dir / f"{snapshot_id}_raw_game_logs.csv"

        print(f"\n[C1] Fetching game logs for {len(TARGET_PLAYER_IDS)} players "
              f"across seasons {TARGET_SEASONS}...")
        print(f"[C1] This will register snapshot {snapshot_id}.")

        client = NBAIngestionClient(
            logger=logger,
            snapshot_id=snapshot_id,
            request_delay=0.6,
        )

        all_frames: list[pd.DataFrame] = []
        for season in TARGET_SEASONS:
            print(f"  Season {season}:")
            ok, season_df = client.fetch_player_game_logs_bulk(
                player_ids=TARGET_PLAYER_IDS,
                season=season,
                season_type=SEASON_TYPE,
                session_id=session_id,
            )
            if not ok:
                ok = logger.error(
                    "C1", "bulk_fetch_failed",
                    payload={"season": season},
                    session_id=session_id,
                    snapshot_id=snapshot_id,
                )
                if not ok:
                    _kill_switch(f"C6 write failure after C1 bulk fetch failed for season {season}")
                print(f"  WARNING: Fetch failed for season {season}. Continuing...")
            else:
                print(f"    ✓ {len(season_df):,} rows fetched.")
                all_frames.append(season_df)

        if not all_frames:
            _kill_switch("C1 produced no data — all seasons failed")

        raw_df = pd.concat(all_frames, ignore_index=True)
        print(f"\n[C1] Total: {len(raw_df):,} rows | "
              f"{raw_df['player_id'].nunique()} players | "
              f"{raw_df['season'].nunique()} seasons")

        if not dry_run:
            raw_df.to_csv(fresh_csv_path, index=False)
            print(f"[C1] Snapshot saved: {fresh_csv_path}")
            print(f"[C1] NOTE: Update DATA_SNAPSHOTS_INDEX.md row count for {snapshot_id}: "
                  f"{len(raw_df):,} rows")

        ok = logger.info(
            "C1", "raw_data_registered",
            payload={
                "snapshot_id": snapshot_id,
                "total_rows": len(raw_df),
                "player_count": int(raw_df["player_id"].nunique()),
                "season_count": int(raw_df["season"].nunique()),
                "date_range": f"{raw_df['game_date'].min()} → {raw_df['game_date'].max()}",
                "file_path": str(fresh_csv_path),
            },
            session_id=session_id,
            snapshot_id=snapshot_id,
        )
        if not ok:
            _kill_switch("C6 write failure after C1 snapshot registration")

    # ------------------------------------------------------------------
    # 3. Resolve window snapshot IDs
    # ------------------------------------------------------------------
    resolved_windows: list[BacktestWindowDef] = []
    for key in windows_to_run:
        if key not in BACKTEST_WINDOWS:
            print(f"WARNING: Unknown window key '{key}' — skipping. "
                  f"Valid: {list(BACKTEST_WINDOWS.keys())}")
            continue
        wdef = BACKTEST_WINDOWS[key]
        # Replace snapshot_id with the one determined above (reuse vs fresh)
        resolved_windows.append(
            BacktestWindowDef(
                exp_id=wdef.exp_id,
                train_end_date=wdef.train_end_date,
                val_end_date=wdef.val_end_date,
                description=wdef.description,
                snapshot_id=snapshot_id,
            )
        )

    if not resolved_windows:
        _kill_switch("No valid windows to run. Check --window argument.")

    # ------------------------------------------------------------------
    # 4. Run backtester
    # ------------------------------------------------------------------
    backtester = Backtester(
        logger=logger,
        snapshot_id=snapshot_id,
        window=10,
        market_implied_prob=0.50,
    )

    ok, results = backtester.run_windows(
        raw_df=raw_df,
        windows=resolved_windows,
        base_output_dir=output_dir,
        dry_run=dry_run,
    )
    if not ok:
        _kill_switch("Backtester.run_windows returned C6 write failure")

    # ------------------------------------------------------------------
    # 5. Print overall summary
    # ------------------------------------------------------------------
    print(f"\n{'='*60}")
    print(f"BACKTEST COMPLETE — {len(results)} window(s) run")
    print(f"{'='*60}")
    beats_null_count = 0
    for r in results:
        _bs = r.validation_brier_model
        _nbs = r.validation_brier_null
        _imp = r.brier_improvement
        beats = r.beats_null
        if beats:
            beats_null_count += 1
        print(f"\n  {r.exp_id}: {r.window_def.description}")
        print(f"    Brier (model) : {_bs:.4f}" if isinstance(_bs, float) else f"    Brier (model) : N/A")
        print(f"    Brier (null)  : {_nbs:.4f}" if isinstance(_nbs, float) else f"    Brier (null)  : N/A")
        if isinstance(_imp, float):
            print(f"    Improvement   : {_imp:+.4f} ({'✓' if beats else '✗'})")
        print(f"    ECE           : {r.validation_ece:.4f}" if isinstance(r.validation_ece, float) else f"    ECE           : N/A")
        print(f"    AUC-ROC       : {r.validation_auc_roc:.4f}" if isinstance(r.validation_auc_roc, float) else f"    AUC-ROC       : N/A")
        print(f"    C4 gate       : {r.c4_gate_result}")

    print(f"\nWindows beating null: {beats_null_count}/{len(results)}")
    print(f"G4 requirement: model beats null in ≥2/3 experiments (including EXP-001)")
    print(f"{'='*60}\n")

    # Log overall summary to C6
    summary_payload = {
        "windows_run": len(results),
        "beats_null_count": beats_null_count,
        "results": [
            {
                "exp_id": r.exp_id,
                "validation_brier_model": r.validation_brier_model,
                "validation_brier_null": r.validation_brier_null,
                "brier_improvement": r.brier_improvement,
                "beats_null": r.beats_null,
                "c4_gate_result": r.c4_gate_result,
            }
            for r in results
        ],
    }
    ok = logger.info(
        "BACKTEST_RUNNER",
        "backtest_run_complete",
        payload=summary_payload,
        session_id=session_id,
        snapshot_id=snapshot_id,
    )
    if not ok:
        _kill_switch("C6 write failure at backtest_run_complete")

    return [
        {
            "exp_id": r.exp_id,
            "session_id": r.session_id,
            "model_version": r.model_version,
            "snapshot_id": r.snapshot_id,
            "train_rows": r.train_rows,
            "val_rows": r.val_rows,
            "test_rows_held_out": r.test_rows_held_out,
            "validation_brier_model": r.validation_brier_model,
            "validation_brier_null": r.validation_brier_null,
            "brier_improvement": r.brier_improvement,
            "beats_null": r.beats_null,
            "validation_log_loss": r.validation_log_loss,
            "validation_ece": r.validation_ece,
            "validation_auc_roc": r.validation_auc_roc,
            "c4_gate_result": r.c4_gate_result,
            "output_dir": r.output_dir,
        }
        for r in results
    ]


# ---------------------------------------------------------------------------
# CLI entrypoint
# ---------------------------------------------------------------------------

def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Walk-Forward Backtest Runner — EXP-002, EXP-003"
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("exp_output/BACKTEST"),
        help="Base directory for backtest outputs (default: exp_output/BACKTEST/)",
    )
    parser.add_argument(
        "--raw-csv",
        type=Path,
        default=None,
        help=(
            "Path to a pre-ingested raw game logs CSV (SNAP-2026-05-27-001 from EXP-001). "
            "If omitted, a fresh C1 pull is performed and SNAP-2026-05-27-002 is registered."
        ),
    )
    parser.add_argument(
        "--window",
        type=str,
        default="all",
        help=(
            "Comma-separated list of window keys to run: 'exp002', 'exp003', or 'all'. "
            "Default: 'all' (runs EXP-002 and EXP-003)."
        ),
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run pipeline validation without writing CSVs to disk.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_args()

    if args.window.lower() == "all":
        windows = list(BACKTEST_WINDOWS.keys())
    else:
        windows = [w.strip().lower() for w in args.window.split(",")]

    results = run_backtest(
        output_dir=args.output_dir,
        raw_csv=args.raw_csv,
        windows_to_run=windows,
        dry_run=args.dry_run,
    )
    sys.exit(0)
