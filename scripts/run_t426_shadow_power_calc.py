#!/usr/bin/env python3
"""T-426 — shadow power-calc via the decoupled outcome-measurement store.

READ-ONLY. Does not edit run_power_calc.py, run_band_monitor.py, or
build_t4_outcome_store.py. Builds ALONGSIDE the governance path.

Three tasks, per T-426's scope:

  TASK 1 (gating) — Agreement check. Restrict the decoupled outcome store to
  the tickers underlying the T4M-PROJ epoch-12 clean ledger cohort (the same
  cohort run_power_calc.py's clean_n=157 is computed from) and check whether
  the store's independently-fetched actual_hits agrees with the ledger's own
  actual_hits field for the same ticker. This is the real test: both numbers
  are supposed to be "how many hits did this player get in this game" —
  the ledger's copy was captured by run_resolve_mlb.py at bet-resolution
  time; the store's copy was captured independently, days later, by
  build_t4_outcome_store.py's own MLB_R/MLB_P/ESPN cascade. If they don't
  match, the ledger path and the decoupled path are not measuring the same
  fact, and the disagreement is the finding.

  TASK 2 — Full-population Brier/calibration (2,021 tickers), split
  bet-fired vs declined, with reliability bins.

  TASK 3 — n-for-verdict comparison: what n would the decoupled path need,
  and how does that compare to n*=267 (ledger path, from run_power_calc.py).

Definitional reconciliation required before any numeric comparison
(per T-426's brief):
  (1) Ledger counts POSITIONS (raw_n=2193, clean_n=157); the store counts
      TICKERS (2,021 total, distinct join key). A ticker can carry >1
      position (re-entries: 958 of the ledger's 2193 resolved rows share a
      ticker with another resolved row). This script is explicit about
      which unit each reported number is in.
  (2) Clean-epoch filtering (logic_epoch >= 12 for T4M-PROJ, via
      is_clean_for_band()) is a LEDGER-side (position-level) concept. The
      store has no epoch field — a ticker's cycle-log rows may span
      multiple logic epochs. This script filters the LEDGER side by epoch
      first, then joins the resulting position set's tickers into the
      store — it never attempts to filter the store itself by epoch.
"""
from __future__ import annotations

import json
import math
import statistics
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from prediction_market_bot.logic_epoch import (  # noqa: E402
    clean_epoch_floor_for_band,
    is_clean_for_band,
)

DEFAULT_LEDGER = _REPO_ROOT / "logs" / "t4_mlb_resolved_ledger.jsonl"
DEFAULT_STORE = _REPO_ROOT / "logs" / "t4_mlb_outcome_store.jsonl"
DEFAULT_CYCLE_LOG = _REPO_ROOT / "logs" / ".vps_t4_mlb_cycle_log_cache.jsonl"
BAND = "T4M-PROJ"


def load_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    out = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line:
                out.append(json.loads(line))
    return out


def load_store_by_ticker(path: Path) -> dict[str, dict]:
    return {r["ticker"]: r for r in load_jsonl(path)}


# ── TASK 1 — agreement check ────────────────────────────────────────────────

def task1_agreement_check(ledger_path: Path, store_path: Path) -> dict:
    ledger = load_jsonl(ledger_path)
    resolved = [r for r in ledger if r.get("outcome") in ("WIN", "LOSS") and r.get("model_p") is not None]
    floor = clean_epoch_floor_for_band(BAND)
    clean = [r for r in resolved if is_clean_for_band(r.get("logic_epoch"), BAND)]

    store = load_store_by_ticker(store_path)

    matched, unmatched, unresolved_in_store = [], [], []
    hits_agree, hits_disagree = [], []
    outcome_agree, outcome_disagree = [], []

    for r in clean:
        ticker = r.get("kalshi_ticker", "")
        srec = store.get(ticker)
        if srec is None:
            unmatched.append(r)
            continue
        if not srec.get("resolved"):
            unresolved_in_store.append(r)
            continue
        matched.append(r)

        ledger_hits = r.get("actual_hits")
        store_hits = srec.get("actual_hits")
        rec = {
            "position_id": r.get("position_id"),
            "ticker": ticker,
            "player_name": r.get("player_name"),
            "ledger_actual_hits": ledger_hits,
            "store_actual_hits": store_hits,
            "ledger_outcome": r.get("outcome"),
            "ledger_direction": r.get("direction"),
            "threshold": r.get("threshold"),
            "resolution_source": srec.get("resolution_source"),
        }
        if ledger_hits is not None and store_hits is not None and float(ledger_hits) == float(store_hits):
            hits_agree.append(rec)
        else:
            hits_disagree.append(rec)

        # Independently re-derive WIN/LOSS from the store's own actual_hits +
        # the ledger's threshold/direction (both structural, not measured
        # quantities, so no cross-source risk there), then compare to the
        # ledger's recorded outcome.
        try:
            thr = int(r.get("threshold", 0) or 0)
            direction = str(r.get("direction", "YES"))
            store_meets = float(store_hits) >= thr
            derived_outcome = "WIN" if (store_meets if direction == "YES" else not store_meets) else "LOSS"
        except (TypeError, ValueError):
            derived_outcome = None
        rec2 = dict(rec)
        rec2["store_derived_outcome"] = derived_outcome
        if derived_outcome is not None and derived_outcome == r.get("outcome"):
            outcome_agree.append(rec2)
        else:
            outcome_disagree.append(rec2)

    # Shadow clean_n / mu / sigma, restricted to the matched+resolved cohort
    # (using the LEDGER's own pnl field, since the store has no price/stake
    # to independently compute pnl from — this reports whether the ledger's
    # recorded pnl is trustworthy for the subset the store can corroborate,
    # not a fully independent pnl recomputation).
    pnl = [float(r.get("pnl", 0.0) or 0.0) for r in matched]
    shadow_n = len(pnl)
    shadow_mu = statistics.mean(pnl) if pnl else None
    shadow_sigma = statistics.stdev(pnl) if len(pnl) >= 2 else None

    return {
        "band": BAND,
        "clean_epoch_floor": floor,
        "ledger_raw_n_resolved_positions": len(resolved),
        "ledger_clean_n_positions_epoch_ge_floor": len(clean),
        "unique_tickers_in_clean_cohort": len({r.get("kalshi_ticker") for r in clean}),
        "store_total_tickers": len(store),
        "clean_cohort_matched_in_store": len(matched),
        "clean_cohort_unmatched_in_store": len(unmatched),
        "clean_cohort_matched_but_unresolved_in_store": len(unresolved_in_store),
        "hits_agree": len(hits_agree),
        "hits_disagree": len(hits_disagree),
        "hits_disagree_examples": hits_disagree[:10],
        "outcome_agree": len(outcome_agree),
        "outcome_disagree": len(outcome_disagree),
        "outcome_disagree_examples": outcome_disagree[:10],
        "shadow_clean_n_positions": shadow_n,
        "shadow_mu_pnl_per_bet": shadow_mu,
        "shadow_sigma_pnl_per_bet": shadow_sigma,
        "unmatched_examples": [
            {"position_id": r.get("position_id"), "ticker": r.get("kalshi_ticker"),
             "player_name": r.get("player_name")}
            for r in unmatched[:10]
        ],
    }


def main() -> None:
    result = task1_agreement_check(DEFAULT_LEDGER, DEFAULT_STORE)
    print(json.dumps(result, indent=2, default=str))


if __name__ == "__main__":
    main()
