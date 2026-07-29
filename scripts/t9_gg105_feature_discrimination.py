#!/usr/bin/env python3
"""
T9 / A1 — Feature-level discrimination check (GG-105 rework, no live epoch bump)

WHY THIS EXISTS
----------------
GG-140 established that Platt/isotonic/temperature scaling are monotonic
transforms of the model score and structurally cannot repair an inverted
edge-tercile rank ordering. The remaining question A1 asks is one level
deeper than anything scripts/what_if_harness.py (D1) can answer: D1's own
SCOPE LIMITATION says the resolved-ledger schema persists only the final
scalar model_p, never the raw per-bet features (ba_l10, park_factor_hits,
opponent context, ...) that fed it -- so D1 cannot test whether any
INDIVIDUAL raw feature rank-orders realized outcomes, only whether a
post-hoc transform of the already-computed model_p does.

This script closes that specific gap by joining the real resolved MAIN
ledger (paper_portfolio_mlb.json closed_positions, T1/T2/T3 pooled) against
the real historical C2 feature matrix (exp_output/MLB/mlb_feature_matrix.csv,
pulled from the VPS -- confirmed to be a cumulative history back to
2026-03-26, not a same-day snapshot) on the only join key both sides
carry: (player_id, game_date). Ambiguous joins (a small number of
doubleheader-style duplicate (player_id, game_date) keys where the feature
matrix has >1 row with genuinely different values, i.e. two different
temporal_cutoff snapshots -- the ledger does not carry game_id, so which of
the two games a given bet resolved against cannot be disambiguated) are
DROPPED from both sides rather than guessed, matching the discipline
what_if_harness.py's --overrides-file join already applies to threshold
collisions.

METHODOLOGY
------------
For each candidate feature, reuses the exact tercile/Fisher-exact machinery
already audited in exp_retrospective_core.edge_monotonicity() /
_tercile_table() / _fisher_pvalue(), but keyed on the RAW FEATURE VALUE
instead of fee_net_edge, and tested against the reconstructed underlying
EVENT indicator (did the player actually clear the threshold?) instead of
the bet's WIN/LOSS outcome -- because WIN/LOSS flips sign with bet direction
(YES vs NO) while the event ("player_hits >= threshold") does not. This is
the same _event convention exp_retrospective_core._calibration_records()
already uses: event = 1 iff (direction == "YES") == (outcome == "WIN").

For binary/near-binary features (is_home_game, opp_sp_is_known, b2b_flag),
a plain 2x2 Fisher exact replaces the tercile split (a tercile split on a
0/1 column is degenerate).

NO WRITE to any live file, portfolio, or ledger, and NO epoch bump.
Read-only by construction: reads two already-pulled local files and prints
(or --out writes) a report.

Run:
  python3 scripts/t9_gg105_feature_discrimination.py
  python3 scripts/t9_gg105_feature_discrimination.py --out exp_output/T9_GG105_REWORK/a1_report.json
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from exp_retrospective_core import (  # noqa: E402
    MLBPosition,
    load_portfolio,
    deduplicate,
    MIN_N,
    _fisher_pvalue,
)

DEFAULT_PORTFOLIO = Path("logs/.vps_portfolio_cache_mlb.json")
DEFAULT_FEATURE_CSV = Path("exp_output/T9_GG105_REWORK/mlb_feature_matrix.csv")
ALPHA = 0.10  # matches edge_monotonicity's convention (T-177/GG-037)

# Candidate continuous/ordinal features to test (name -> CSV column).
CONTINUOUS_CANDIDATES = {
    "ba_l10": "ba_l10",
    "ba_l10_shrunk": "ba_l10_shrunk",
    "slg_l10": "slg_l10",
    "obp_l10": "obp_l10",
    "ops_l10": "ops_l10",
    "h_l10_mean": "h_l10_mean",
    "k_rate_l10": "k_rate_l10",
    "bb_rate_l10": "bb_rate_l10",
    "hr_rate_l10": "hr_rate_l10",
    "days_rest": "days_rest",
    "opp_runs_allowed_l10": "opp_runs_allowed_l10",
    "opp_sp_era_l5": "opp_sp_era_l5",
    "opp_sp_k9_l5": "opp_sp_k9_l5",
    "opp_sp_bb9_l5": "opp_sp_bb9_l5",
    "park_factor_hits": "park_factor_hits",
}

# Candidate binary/near-binary features (plain 2x2 Fisher, no terciles).
BINARY_CANDIDATES = {
    "is_home_game": "is_home_game",
    "b2b_flag": "b2b_flag",
    "opp_sp_is_known": "opp_sp_is_known",
}

# Not present in the current C2 feature matrix at all -- flagged as a data
# gap rather than fabricated: batting-order/lineup slot is a T4-only live
# in-game field (CLAUDE.md's "batting_slot" reference), not a pregame C2
# MAIN feature. No column exists to test it here.
MISSING_CANDIDATES_NOTE = (
    "order-slot (batting lineup position) requested by A1 has NO pregame "
    "MAIN-book column in mlb_feature_matrix.csv -- 'batting_slot' exists "
    "only as a T4 live in-game field (see CLAUDE.md T4 thesis description), "
    "not a C2 pregame feature. Cannot be tested from this data source; "
    "would require either adding it to C2's pregame feature set (if a "
    "pre-game projected batting order is obtainable from the data source) "
    "or restricting this specific candidate to a T4-ledger-based test."
)

# Confirmed by direct full-matrix inspection (not just the joined subset):
# these four opponent/matchup columns exist in the CSV schema but are DEAD
# -- never populated by C2 ingestion, across all 17,145 rows since
# 2026-03-26, not just the ~313 rows joined to MAIN's resolved ledger. This
# is a genuine C2 data-gap finding, not a join artifact: opp_sp_era_l5,
# opp_sp_k9_l5, opp_sp_bb9_l5 are 100% blank; opp_sp_is_known is a hardcoded
# constant 0.0 in every row. "matchup/opponent" -- one of A1's explicitly
# requested candidate categories -- currently has NO usable signal anywhere
# in the historical feature matrix to test, let alone deploy.
DEAD_COLUMNS_NOTE = (
    "opp_sp_era_l5, opp_sp_k9_l5, opp_sp_bb9_l5, opp_runs_allowed_l10 are "
    "100% blank across all 17,145 rows of the full historical feature "
    "matrix (not just the 313 joined to MAIN's ledger) -- these columns "
    "were scaffolded into the C2 schema but never populated by ingestion. "
    "opp_sp_is_known is present but is a hardcoded constant 0.0 in every "
    "row, i.e. it always reads 'no confirmed starter', never 1. The "
    "'matchup/opponent' candidate category A1 asked to test has NO live "
    "signal anywhere in this data source -- this is a C2 ingestion gap, "
    "not a modeling finding, and should be registered as its own "
    "governance item before any matchup-based rank-ordering candidate can "
    "be evaluated."
)


def load_feature_index(path: Path) -> tuple[dict[tuple[str, str], dict], int]:
    """Returns ({(player_id, game_date): row}, n_ambiguous_dropped)."""
    groups: dict[tuple[str, str], list[dict]] = {}
    with open(path) as fh:
        for row in csv.DictReader(fh):
            key = (row["player_id"], row["game_date"])
            groups.setdefault(key, []).append(row)
    index: dict[tuple[str, str], dict] = {}
    ambiguous = 0
    for key, rows in groups.items():
        if len(rows) == 1:
            index[key] = rows[0]
            continue
        # Multiple feature rows for this (player_id, game_date). Keep only
        # if every candidate field agrees across rows (harmless duplicate,
        # e.g. identical re-ingestion) -- otherwise this is a genuine
        # doubleheader-style ambiguity (different temporal_cutoff snapshots)
        # that cannot be resolved without game_id, which the ledger lacks.
        all_cols = set(CONTINUOUS_CANDIDATES.values()) | set(BINARY_CANDIDATES.values())
        first = rows[0]
        if all(r.get(c) == first.get(c) for r in rows[1:] for c in all_cols):
            index[key] = first
        else:
            ambiguous += 1
    return index, ambiguous


def reconstruct_event(p: MLBPosition) -> int:
    """Same convention as exp_retrospective_core._calibration_records():
    1 iff the underlying fact ('player cleared threshold') actually
    happened, regardless of which side (YES/NO) the bet took."""
    return 1 if ((p.direction == "YES") == (p.outcome == "WIN")) else 0


def _to_float(val: str | None) -> float | None:
    if val is None or val == "" or val.upper() == "NAN" if isinstance(val, str) else False:
        return None
    try:
        f = float(val)
    except (TypeError, ValueError):
        return None
    if f != f:  # NaN
        return None
    return f


def tercile_test(label: str, pairs: list[tuple[float, int]]) -> dict:
    """pairs: list of (feature_value, event). Same tercile/Fisher machinery
    as exp_retrospective_core._tercile_table()/_fisher_pvalue(), keyed on
    feature_value instead of fee_net_edge and event instead of WIN/LOSS."""
    n = len(pairs)
    if n < MIN_N:
        return {"feature": label, "n": n, "verdict": "INCONCLUSIVE",
                "reason": f"n={n} < MIN_N={MIN_N}"}
    sorted_pairs = sorted(pairs, key=lambda t: t[0])
    chunks = [sorted_pairs[i * n // 3:(i + 1) * n // 3] for i in range(3)]
    if n % 3 != 0:
        chunks[2] = sorted_pairs[2 * n // 3:]
    terciles = []
    for i, chunk in enumerate(chunks):
        if not chunk:
            continue
        terciles.append({
            "tercile": i + 1,
            "n": len(chunk),
            "feature_min": chunk[0][0],
            "feature_max": chunk[-1][0],
            "feature_mean": sum(v for v, _ in chunk) / len(chunk),
            "event_rate": sum(e for _, e in chunk) / len(chunk),
        })
    if len(terciles) < 3:
        return {"feature": label, "n": n, "verdict": "INCONCLUSIVE",
                "reason": "degenerate tercile split", "terciles": terciles}
    # Fisher: top tercile vs bottom tercile event rate (mirrors
    # edge_monotonicity's pos-edge-vs-neg-edge two-group comparison, adapted
    # to a 3-group split since there is no natural feature "zero" to split
    # on the way fee_net_edge has one).
    class _Row:
        __slots__ = ("outcome",)
        def __init__(self, outcome): self.outcome = outcome
    top = [_Row("WIN" if e else "LOSS") for _, e in chunks[2]]
    bot = [_Row("WIN" if e else "LOSS") for _, e in chunks[0]]
    or_, pval = _fisher_pvalue(top, bot)
    er_top = terciles[2]["event_rate"]
    er_bot = terciles[0]["event_rate"]
    if pval < ALPHA and er_top > er_bot:
        verdict = "MONOTONIC"
    elif pval < ALPHA and er_top < er_bot:
        verdict = "ANTI-PREDICTIVE"
    else:
        verdict = "INCONCLUSIVE"
    return {
        "feature": label, "n": n, "verdict": verdict,
        "fisher_odds_ratio": or_, "fisher_pvalue": pval,
        "event_rate_top_tercile": er_top, "event_rate_bottom_tercile": er_bot,
        "terciles": terciles,
    }


def binary_test(label: str, pairs: list[tuple[float, int]]) -> dict:
    n = len(pairs)
    if n < MIN_N:
        return {"feature": label, "n": n, "verdict": "INCONCLUSIVE",
                "reason": f"n={n} < MIN_N={MIN_N}"}
    class _Row:
        __slots__ = ("outcome",)
        def __init__(self, outcome): self.outcome = outcome
    ones = [_Row("WIN" if e else "LOSS") for v, e in pairs if v == 1]
    zeros = [_Row("WIN" if e else "LOSS") for v, e in pairs if v == 0]
    if not ones or not zeros:
        return {"feature": label, "n": n, "verdict": "INCONCLUSIVE",
                "reason": f"degenerate split (n_1={len(ones)}, n_0={len(zeros)})"}
    or_, pval = _fisher_pvalue(ones, zeros)
    er1 = sum(1 for r in ones if r.outcome == "WIN") / len(ones)
    er0 = sum(1 for r in zeros if r.outcome == "WIN") / len(zeros)
    if pval < ALPHA and er1 > er0:
        verdict = "MONOTONIC"
    elif pval < ALPHA and er1 < er0:
        verdict = "ANTI-PREDICTIVE"
    else:
        verdict = "INCONCLUSIVE"
    return {"feature": label, "n": n, "verdict": verdict,
            "fisher_odds_ratio": or_, "fisher_pvalue": pval,
            "event_rate_1": er1, "event_rate_0": er0,
            "n_1": len(ones), "n_0": len(zeros)}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                  formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--portfolio", default=str(DEFAULT_PORTFOLIO))
    ap.add_argument("--feature-csv", default=str(DEFAULT_FEATURE_CSV))
    ap.add_argument("--out", default=None)
    args = ap.parse_args(argv)

    portfolio_path = Path(args.portfolio)
    feature_path = Path(args.feature_csv)
    if not portfolio_path.exists():
        print(f"ERROR: {portfolio_path} not found.", file=sys.stderr)
        return 1
    if not feature_path.exists():
        print(f"ERROR: {feature_path} not found.", file=sys.stderr)
        return 1

    positions = deduplicate(load_portfolio(portfolio_path))
    print(f"Loaded {len(positions)} deduped resolved MAIN (T1/T2/T3) positions.")

    feature_index, n_ambiguous = load_feature_index(feature_path)
    print(f"Feature matrix: {len(feature_index)} unambiguous (player_id, game_date) keys "
          f"({n_ambiguous} ambiguous keys dropped -- doubleheader-style duplicate rows "
          f"with genuinely differing feature values and no game_id to disambiguate).")

    joined: list[tuple[MLBPosition, dict]] = []
    unmatched = 0
    for p in positions:
        key = (str(p.player_id), p.game_date)
        row = feature_index.get(key)
        if row is None:
            unmatched += 1
            continue
        joined.append((p, row))
    print(f"Joined: {len(joined)}/{len(positions)} positions matched to a feature row "
          f"({unmatched} unmatched -- no feature row for that (player_id, game_date)).")
    print()

    report: dict = {
        "n_positions": len(positions),
        "n_feature_keys": len(feature_index),
        "n_ambiguous_dropped": n_ambiguous,
        "n_joined": len(joined),
        "n_unmatched": unmatched,
        "results": [],
        "data_gap_note": MISSING_CANDIDATES_NOTE,
    }

    print("=" * 100)
    print("CONTINUOUS/ORDINAL FEATURES (tercile split, event = did player clear threshold)")
    print("=" * 100)
    for label, col in CONTINUOUS_CANDIDATES.items():
        pairs = []
        for p, row in joined:
            v = _to_float(row.get(col))
            if v is None:
                continue
            pairs.append((v, reconstruct_event(p)))
        result = tercile_test(label, pairs)
        report["results"].append(result)
        if result.get("terciles"):
            print(f"{label:24s} n={result['n']:>4}  verdict={result['verdict']:16s}"
                  f"  p={result.get('fisher_pvalue', float('nan')):.4f}"
                  f"  event_rate(top)={result.get('event_rate_top_tercile', float('nan')):.3f}"
                  f"  event_rate(bot)={result.get('event_rate_bottom_tercile', float('nan')):.3f}")
        else:
            print(f"{label:24s} n={result['n']:>4}  verdict={result['verdict']:16s}"
                  f"  ({result.get('reason', '')})")

    print()
    print("=" * 100)
    print("BINARY FEATURES (2x2 Fisher, event = did player clear threshold)")
    print("=" * 100)
    for label, col in BINARY_CANDIDATES.items():
        pairs = []
        for p, row in joined:
            v = _to_float(row.get(col))
            if v is None:
                continue
            pairs.append((round(v), reconstruct_event(p)))
        result = binary_test(label, pairs)
        report["results"].append(result)
        if "reason" in result:
            print(f"{label:24s} n={result['n']:>4}  verdict={result['verdict']:16s}  ({result['reason']})")
        else:
            print(f"{label:24s} n={result['n']:>4}  verdict={result['verdict']:16s}"
                  f"  p={result['fisher_pvalue']:.4f}"
                  f"  event_rate(1)={result['event_rate_1']:.3f} (n={result['n_1']})"
                  f"  event_rate(0)={result['event_rate_0']:.3f} (n={result['n_0']})")

    print()
    print("=" * 100)
    print("MARKET-RELATIVE CANDIDATE: (ba_l10_shrunk - mid_price_at_entry)")
    print("(does raw-feature-vs-market divergence, independent of the LR+Platt model, rank-order outcomes?)")
    print("=" * 100)
    mr_pairs = []
    for p, row in joined:
        v = _to_float(row.get("ba_l10_shrunk"))
        if v is None:
            continue
        mr_pairs.append((v - p.mip, reconstruct_event(p)))
    mr_result = tercile_test("ba_l10_shrunk_minus_mip", mr_pairs)
    report["results"].append(mr_result)
    if mr_result.get("terciles"):
        print(f"{'ba_l10_shrunk - mip':24s} n={mr_result['n']:>4}  verdict={mr_result['verdict']:16s}"
              f"  p={mr_result.get('fisher_pvalue', float('nan')):.4f}"
              f"  event_rate(top)={mr_result.get('event_rate_top_tercile', float('nan')):.3f}"
              f"  event_rate(bot)={mr_result.get('event_rate_bottom_tercile', float('nan')):.3f}")
    else:
        print(f"{'ba_l10_shrunk - mip':24s} n={mr_result['n']:>4}  verdict={mr_result['verdict']:16s}"
              f"  ({mr_result.get('reason', '')})")

    print()
    print(f"DATA GAP (order-slot): {MISSING_CANDIDATES_NOTE}")
    print()
    print(f"DATA GAP (matchup/opponent, dead columns): {DEAD_COLUMNS_NOTE}")
    report["data_gap_note_dead_columns"] = DEAD_COLUMNS_NOTE

    if args.out:
        out_path = Path(args.out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(report, indent=2, default=str))
        print(f"\nWrote report: {out_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
