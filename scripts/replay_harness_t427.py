#!/usr/bin/env python3
"""T-427 / Phase 1 exit-gate harness (MARKET_EXPANSION_ACTION_PLAN.md box 1.6).

Replays every stored position in the T1/MAIN and T4M-PROJ ledgers through
open_position() on the CURRENT (unrefactored) code path and asserts the
replayed record matches the stored record field-for-field, modulo an
explicitly frozen non-determinism set. See
05_RESEARCH_EXPERIMENTS/T427_REPLAY_DETERMINISM_AUDIT.md for the audit that
derived that set and the corrected gate proposal this harness implements.

Read-only against src/. Does not mutate the pulled ledger files. Writes the
replay trader's scratch state to a tempdir that is discarded on exit.

Usage:
    python scripts/replay_harness_t427.py
    python scripts/replay_harness_t427.py --ledger logs/.vps_cache_paper_portfolio_mlb.json
"""
from __future__ import annotations

import argparse
import json
import sys
import tempfile
from collections import Counter
from pathlib import Path
from unittest import mock

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "src"))

from prediction_market_bot.c5_execution import paper_trader as pt_module  # noqa: E402
from prediction_market_bot.c6_audit_logger.audit_logger import AuditLogger  # noqa: E402

DEFAULT_LEDGERS = [
    REPO_ROOT / "logs" / ".vps_cache_paper_portfolio_mlb.json",
    REPO_ROOT / "logs" / ".vps_cache_paper_portfolio_mlb_t4.json",
]

# Fields open_position() itself writes into the position dict (its literal,
# paper_trader.py:487-530). Anything else present on a stored record (e.g.
# aged_open*, pnl/resolved_at/exit_* fields) was added by a LATER function
# (mark_aged_open, resolve_pending/exit_position) and is out of this
# function's determinism scope by construction.
OPEN_POSITION_FIELDS = [
    "position_id", "player_name", "player_id", "kalshi_ticker",
    "kalshi_threshold", "direction", "mid_price_at_entry", "vig_at_entry",
    "size_usd", "game_date", "entered_at", "risk_eval_id", "forecast_id",
    "band", "logic_epoch", "approval_commit", "status", "pool_isolated",
    "kalshi_order_id", "kalshi_order_status", "kalshi_contracts",
    "model_p", "gross_edge", "fee_per_contract", "fee_net_edge",
    "fee_contaminated", "probable_injury_signal", "t3_signal", "t1_edge",
    "h_so_far_at_entry", "ab_remaining_at_entry", "entry_price_paid",
    "price_stratum", "contracts",
]

# Genuinely irreproducible: real Kalshi demo-venue state assigned at the
# original network call. Excluded from comparison whenever the ORIGINAL
# record shows a real submission was attempted (status != "local_only") —
# a replay with kalshi_client=None can only ever produce
# ("local_only", None, None) and cannot recreate a historical order id or a
# historical HTTP failure code.
KALSHI_FIELDS = {"kalshi_order_id", "kalshi_order_status", "kalshi_contracts"}

# Mutated post-open by a different function (mark_aged_open at 48h, or
# resolve_pending/exit_position on settlement) — not evidence of
# open_position() non-determinism if it differs, so excluded whenever the
# stored record is no longer in its as-opened state.
STATUS_FIELD = "status"

# Randomness / call-time globals open_position() cannot derive from its own
# arguments. The harness PINS these via monkeypatch to the stored value
# before replaying, then verifies the pin actually reproduced the field
# (i.e. that pinning — not luck — is what makes it match).
PINNED_FIELDS = {"position_id", "entered_at", "logic_epoch", "approval_commit"}


def reconstruct_approval(pos: dict) -> dict:
    return {
        "approved_size": pos.get("size_usd", 0.0),
        "approved_direction": pos.get("direction", "PASS"),
        "risk_eval_id": pos.get("risk_eval_id", ""),
        "forecast_id": pos.get("forecast_id", ""),
        "band": pos.get("band"),
        "model_p": pos.get("model_p", 0.0),
        "gross_edge": pos.get("gross_edge", 0.0),
        "t3_signal": pos.get("t3_signal", "NEUTRAL"),
        "t1_edge": pos.get("t1_edge", pos.get("gross_edge", 0.0)),
        "entry_price_paid": pos.get("entry_price_paid"),
        "price_stratum": pos.get("price_stratum"),
        "contracts": pos.get("contracts"),
    }


def _fake_uuid4(target_hex10: str):
    padded = (target_hex10.lower() + "0" * 22)[:32]
    return mock.Mock(hex=padded)


def replay_one(trader, pos: dict) -> dict:
    approval = reconstruct_approval(pos)
    target_hex10 = pos["position_id"].removeprefix("POS-")
    with mock.patch.object(pt_module, "_utc_now", return_value=pos["entered_at"]), \
         mock.patch.object(pt_module, "CURRENT_LOGIC_EPOCH", pos.get("logic_epoch")), \
         mock.patch.object(pt_module, "CURRENT_APPROVAL_COMMIT", pos.get("approval_commit")), \
         mock.patch.object(pt_module.uuid, "uuid4", return_value=_fake_uuid4(target_hex10)):
        ok, replayed = trader.open_position(
            approval=approval,
            player_name=pos.get("player_name"),
            player_id=pos.get("player_id"),
            kalshi_ticker=pos.get("kalshi_ticker"),
            kalshi_threshold=pos.get("kalshi_threshold"),
            mid_price=pos.get("mid_price_at_entry", 0.0),
            vig=pos.get("vig_at_entry", 0.0),
            game_date=pos.get("game_date"),
            session_id="replay-t427",
            pool_isolated=pos.get("pool_isolated", False),
            h_so_far_at_entry=pos.get("h_so_far_at_entry"),
            ab_remaining_at_entry=pos.get("ab_remaining_at_entry"),
        )
    if not ok or not replayed:
        raise RuntimeError(f"replay rejected {pos.get('position_id')}: ok={ok} replayed={replayed}")
    return replayed


def compare(pos: dict, replayed: dict) -> list[str]:
    mismatches = []
    submitted_originally = pos.get("kalshi_order_status") not in (None, "local_only")
    resolved_originally = pos.get(STATUS_FIELD) not in (None, "OPEN")

    for field in OPEN_POSITION_FIELDS:
        if field in KALSHI_FIELDS and submitted_originally:
            continue  # excluded: irreproducible external venue state
        if field == STATUS_FIELD and resolved_originally:
            continue  # excluded: mutated post-open by resolve/exit, not by open_position()
        original = pos.get(field)
        got = replayed.get(field)
        if original != got:
            mismatches.append(f"{field}: stored={original!r} replayed={got!r}")
    return mismatches


def branch_for(pos: dict) -> str:
    direction = pos.get("direction")
    band = pos.get("band")
    if direction == "YES":
        return "YES"
    if band == "T4M-PROJ":
        return "T4M-PROJ-NO"
    if band == "T1":
        return "T1-NO"
    return "ELSE-fallthrough"


def run_ledger(ledger_path: Path, tmpdir: Path) -> dict:
    data = json.loads(ledger_path.read_text())
    positions = data.get("open_positions", []) + data.get("closed_positions", [])

    portfolio_path = tmpdir / f"replay_{ledger_path.stem}.json"
    portfolio_path.write_text(json.dumps({
        "bankroll_usd": 1_000_000_000.0,
        "initial_bankroll_usd": 1_000_000_000.0,
        "total_realized_pnl": 0.0,
        "current_daily_loss": 0.0,
        "daily_loss_date": "1970-01-01",
        "open_positions": [],
        "closed_positions": [],
        "rejected_positions": [],
        "created_at": "1970-01-01T00:00:00.000Z",
        "last_updated": "1970-01-01T00:00:00.000Z",
    }))
    logger = AuditLogger(log_path=tmpdir / f"audit_{ledger_path.stem}.jsonl", min_severity="ERROR")
    trader = pt_module.PaperTrader(portfolio_path=portfolio_path, logger=logger, kalshi_client=None)

    branch_counts = Counter()
    branch_pass = Counter()
    mismatch_examples: dict[str, list[str]] = {}
    n_pass = 0
    n_fail = 0
    n_error = 0
    first_errors = []

    for pos in positions:
        if pos.get("size_usd", 0.0) <= 0 or pos.get("direction") not in ("YES", "NO"):
            continue  # PASS/zero-size positions never reach the dict-literal write
        branch = branch_for(pos)
        branch_counts[branch] += 1
        try:
            replayed = replay_one(trader, pos)
        except Exception as exc:  # noqa: BLE001
            n_error += 1
            if len(first_errors) < 5:
                first_errors.append(f"{pos.get('position_id')}: {exc}")
            continue
        mismatches = compare(pos, replayed)
        if mismatches:
            n_fail += 1
            mismatch_examples.setdefault(branch, mismatches[:6])
        else:
            n_pass += 1
            branch_pass[branch] += 1

    return {
        "ledger": ledger_path.name,
        "n_total": len(positions),
        "n_evaluated": n_pass + n_fail,
        "n_pass": n_pass,
        "n_fail": n_fail,
        "n_error": n_error,
        "first_errors": first_errors,
        "branch_counts": dict(branch_counts),
        "branch_pass": dict(branch_pass),
        "mismatch_examples": mismatch_examples,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ledger", action="append", dest="ledgers", default=None)
    args = parser.parse_args()

    ledgers = [Path(p) for p in args.ledgers] if args.ledgers else DEFAULT_LEDGERS
    overall_ok = True

    with tempfile.TemporaryDirectory(prefix="t427_replay_") as tmp:
        tmpdir = Path(tmp)
        for ledger_path in ledgers:
            if not ledger_path.exists():
                print(f"SKIP {ledger_path} (not found — pull via ssh first)")
                continue
            result = run_ledger(ledger_path, tmpdir)
            print(f"\n=== {result['ledger']} ===")
            print(f"total positions in file:  {result['n_total']}")
            print(f"evaluated (size>0, YES/NO): {result['n_evaluated']}")
            print(f"PASS: {result['n_pass']}  FAIL: {result['n_fail']}  ERROR: {result['n_error']}")
            print("branch coverage (real ledger data):")
            for branch, count in sorted(result["branch_counts"].items()):
                passed = result["branch_pass"].get(branch, 0)
                print(f"  {branch:18s} n={count:5d}  pass={passed:5d}")
            if result["first_errors"]:
                print("first errors:")
                for e in result["first_errors"]:
                    print(f"  {e}")
            if result["mismatch_examples"]:
                print("mismatch examples by branch:")
                for branch, ex in result["mismatch_examples"].items():
                    print(f"  [{branch}]")
                    for m in ex:
                        print(f"    {m}")
            if result["n_fail"] or result["n_error"]:
                overall_ok = False

    print("\n" + ("ALL REPLAYS MATCHED (modulo frozen exclusion set)" if overall_ok else "MISMATCHES FOUND — see above"))
    return 0 if overall_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
