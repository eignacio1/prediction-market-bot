#!/usr/bin/env python3
"""
EXP-017B MLB — Edge Decomposition of the Tier-1 T1 MLB Book
Parent: EXP-017 / GG-004 / ADR-0024  |  Companion to run_exp017_mlb.py

PURPOSE
-------
EXP-017 established a HEADLINE verdict (n=151, EV/bet=+$0.1009, WR=49.7%,
PnL=+$15.23, DIRECTIONAL_POSITIVE, ADR-0024 Tier 1 reached, 2026-07-06).
This script asks the follow-on internal-validity question BEFORE any enhancer
(PAM, psych gradients, multi-factor formulas) is built:

    Is the +$0.10/bet edge BROAD, or is it a favourable subset dragged down
    (or propped up) by a broken subset?

It does NOT re-verdict the book. It decomposes the same deduplicated position
set EXP-017 uses, along every axis the position records support, reporting for
each subgroup:
    - n
    - win rate
    - EV/bet in DOLLARS         (total_pnl / n) -- the official GG-004 metric
    - normalized pnl per $1 staked (sum(pnl)/sum(size_usd)) -- sizing-neutral
    - total_pnl
    - bootstrap 95% CI on dollar EV/bet + P(EV>0) from the bootstrap
    - Fisher exact p for win-rate contrasts where a natural 2-way split exists

METHODOLOGY DISCIPLINE (must match EXP-017 for defensibility)
-------------------------------------------------------------
  * Same loader filters: outcome in {WIN,LOSS}, model_p present, drop duplicate_of.
  * Same dedup: one position per kalshi_ticker, earliest (file-order) wins.
  * Same EV: dollar EV/bet = sum(stored pnl) / n ; WR = wins / n.
  * fee_net_edge is ALWAYS recomputed direction-aware via
    run_exp017_mlb.compute_fee_net_edge (GG-077 -- stored value is YES-frame
    only and is wrong-signed for NO bets, which are the majority here).

Run:
  python3 scripts/run_exp017b_decomp_mlb.py
  python3 scripts/run_exp017b_decomp_mlb.py --portfolio logs/.vps_portfolio_cache_mlb.json
  python3 scripts/run_exp017b_decomp_mlb.py --seed 7 --boot 20000
"""
from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path
from typing import Callable

# Reuse the parent experiment's audited fee/edge helpers -- do not reimplement.
sys.path.insert(0, str(Path(__file__).resolve().parent))
import run_exp017_mlb as e17  # noqa: E402

from math import comb

try:
    from scipy.stats import fisher_exact as _scipy_fisher
    _HAS_SCIPY = True
except ImportError:  # pragma: no cover
    _HAS_SCIPY = False


def _fisher_exact_2sided(a: int, b: int, c: int, d: int) -> float:
    """Two-sided Fisher exact p-value (pure-python hypergeometric).
    Table [[a,b],[c,d]]. Sums hypergeometric probs <= P(observed)."""
    if _HAS_SCIPY:
        _, p = _scipy_fisher([[a, b], [c, d]], alternative="two-sided")
        return float(p)
    row1, row2 = a + b, c + d
    col1, n = a + c, a + b + c + d
    if row1 == 0 or row2 == 0 or col1 == 0 or (b + d) == 0:
        return 1.0
    denom = comb(n, col1)
    def hyp(x: int) -> float:
        return comb(row1, x) * comb(row2, col1 - x) / denom
    p_obs = hyp(a)
    lo = max(0, col1 - row2)
    hi = min(col1, row1)
    return min(1.0, sum(hyp(x) for x in range(lo, hi + 1)
                        if hyp(x) <= p_obs + 1e-12))

DEFAULT_PORTFOLIO = Path("logs/.vps_portfolio_cache_mlb.json")
OUT_DIR = Path("exp_output/EXP-017B-DECOMP")


# ── Load: keep FULL records (need signal fields the NamedTuple drops) ────────────

def load_records(path: Path) -> list[dict]:
    """Filtered + deduped raw dicts, in EXP-017-identical order, with a
    recomputed direction-aware fee_net_edge attached as _fne."""
    data = json.loads(path.read_text())
    seen: set[str] = set()
    out: list[dict] = []
    for p in data.get("closed_positions", []):
        if p.get("duplicate_of"):
            continue
        if p.get("outcome") not in ("WIN", "LOSS"):
            continue
        if p.get("model_p") is None:
            continue
        try:
            model_p = float(p["model_p"])
            mip = float(p["mid_price_at_entry"])
        except (KeyError, TypeError, ValueError):
            continue
        tkr = str(p.get("kalshi_ticker", ""))
        if tkr in seen:
            continue
        seen.add(tkr)
        direction = str(p.get("direction", "YES"))
        r = dict(p)
        r["_model_p"] = model_p
        r["_mip"] = mip
        r["_dir"] = direction
        r["_win"] = 1 if p.get("outcome") == "WIN" else 0
        r["_pnl"] = float(p.get("pnl", 0.0) or 0.0)
        r["_size"] = float(p.get("size_usd", 0.0) or 0.0)
        # GG-077: recompute, never trust stored fee_net_edge
        r["_fne"] = e17.compute_fee_net_edge(direction, model_p, mip)
        try:
            r["_thr"] = int(p.get("kalshi_threshold", p.get("threshold", 0)))
        except (TypeError, ValueError):
            r["_thr"] = 0
        out.append(r)
    return out


# ── Stats ───────────────────────────────────────────────────────────────────────

def _boot_ci(pnls: list[float], boot: int, rng: random.Random) -> dict:
    """Bootstrap 95% CI on dollar EV/bet + P(EV>0)."""
    n = len(pnls)
    if n == 0:
        return {"ci_lo": 0.0, "ci_hi": 0.0, "p_ev_gt_0": 0.0}
    means = []
    for _ in range(boot):
        s = 0.0
        for _ in range(n):
            s += pnls[rng.randrange(n)]
        means.append(s / n)
    means.sort()
    lo = means[int(0.025 * boot)]
    hi = means[min(int(0.975 * boot), boot - 1)]
    p_pos = sum(1 for m in means if m > 0) / boot
    return {"ci_lo": lo, "ci_hi": hi, "p_ev_gt_0": p_pos}


def stats(recs: list[dict], boot: int, rng: random.Random) -> dict:
    n = len(recs)
    if n == 0:
        return {"n": 0}
    wins = sum(r["_win"] for r in recs)
    pnls = [r["_pnl"] for r in recs]
    tot_pnl = sum(pnls)
    tot_size = sum(r["_size"] for r in recs)
    d = {
        "n": n,
        "win_rate": wins / n,
        "ev_per_bet_usd": tot_pnl / n,
        "pnl_per_dollar": (tot_pnl / tot_size) if tot_size else 0.0,
        "total_pnl": tot_pnl,
        "total_size": tot_size,
    }
    d.update(_boot_ci(pnls, boot, rng))
    return d


def fisher(g1: list[dict], g2: list[dict]) -> float | None:
    """Two-sided Fisher exact p on win-rate contrast g1 vs g2."""
    if not g1 or not g2:
        return None
    a = sum(r["_win"] for r in g1); b = len(g1) - a
    c = sum(r["_win"] for r in g2); d = len(g2) - c
    return round(_fisher_exact_2sided(a, b, c, d), 5)


def split_by(recs: list[dict], keyfn: Callable[[dict], object],
             boot: int, rng: random.Random) -> dict:
    buckets: dict[object, list[dict]] = {}
    for r in recs:
        buckets.setdefault(keyfn(r), []).append(r)
    return {str(k): stats(buckets[k], boot, rng) for k in
            sorted(buckets, key=lambda x: (str(type(x)), x))}


# ── Bucketers ────────────────────────────────────────────────────────────────────

def edge_bucket(fne: float) -> str:
    if fne <= 0:      return "1_edge<=0"
    if fne <= 0.03:   return "2_(0,0.03]"
    if fne <= 0.06:   return "3_(0.03,0.06]"
    if fne <= 0.10:   return "4_(0.06,0.10]"
    return "5_>0.10"


def mip_bucket(mip: float) -> str:
    if mip < 0.30:    return "1_mip<0.30"
    if mip < 0.50:    return "2_[0.30,0.50)"
    if mip < 0.70:    return "3_[0.50,0.70)"
    return "4_mip>=0.70"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--portfolio", type=Path, default=DEFAULT_PORTFOLIO)
    ap.add_argument("--boot", type=int, default=10000)
    ap.add_argument("--seed", type=int, default=17)
    ap.add_argument("--out", type=Path, default=OUT_DIR)
    args = ap.parse_args()
    rng = random.Random(args.seed)

    recs = load_records(args.portfolio)
    overall = stats(recs, args.boot, rng)

    yes = [r for r in recs if r["_dir"] == "YES"]
    no = [r for r in recs if r["_dir"] == "NO"]

    # time window: split unique game_dates in half
    dates = sorted({r.get("game_date", "") for r in recs})
    half = dates[: len(dates) // 2] if len(dates) > 1 else dates
    early = [r for r in recs if r.get("game_date", "") in set(half)]
    late = [r for r in recs if r.get("game_date", "") not in set(half)]

    report = {
        "meta": {
            "portfolio": str(args.portfolio),
            "boot": args.boot,
            "seed": args.seed,
            "scipy": _HAS_SCIPY,
            "game_dates": dates,
        },
        "overall": overall,
        "by_direction": split_by(recs, lambda r: r["_dir"], args.boot, rng),
        "by_threshold": split_by(recs, lambda r: r["_thr"], args.boot, rng),
        "by_edge_bucket_all": split_by(recs, lambda r: edge_bucket(r["_fne"]), args.boot, rng),
        "by_edge_bucket_NO_only": split_by(no, lambda r: edge_bucket(r["_fne"]), args.boot, rng),
        "by_mip_bucket": split_by(recs, lambda r: mip_bucket(r["_mip"]), args.boot, rng),
        "NO_by_threshold": split_by(no, lambda r: r["_thr"], args.boot, rng),
        "by_time_window": {
            "early": stats(early, args.boot, rng),
            "late": stats(late, args.boot, rng),
        },
        "robustness": {
            "full_book": overall,
            "NO_only": stats(no, args.boot, rng),
            "NO_minus_conviction_tail(>0.10)":
                stats([r for r in no if r["_fne"] <= 0.10], args.boot, rng),
            "full_minus_conviction_tail(>0.10)":
                stats([r for r in recs if r["_fne"] <= 0.10], args.boot, rng),
            "full_minus_YES_minus_edge<=0":
                stats([r for r in recs if r["_dir"] == "NO" and r["_fne"] > 0],
                      args.boot, rng),
        },
        "contrasts": {
            "fisher_YES_vs_NO": fisher(yes, no),
            "fisher_edgeGT0_vs_LE0":
                fisher([r for r in recs if r["_fne"] > 0],
                       [r for r in recs if r["_fne"] <= 0]),
        },
        "invariants": {},
    }

    # ── Verification invariants (math must close) ──
    sub_n = report["by_direction"].get("YES", {}).get("n", 0) + \
            report["by_direction"].get("NO", {}).get("n", 0)
    sub_pnl = sum(v["total_pnl"] for v in report["by_direction"].values())
    report["invariants"] = {
        "direction_n_sums_to_total": sub_n == overall["n"],
        "direction_pnl_sums_to_total":
            abs(sub_pnl - overall["total_pnl"]) < 1e-6,
        "threshold_n_sum": sum(v["n"] for v in report["by_threshold"].values()),
        "edge_n_sum": sum(v["n"] for v in report["by_edge_bucket_all"].values()),
    }

    args.out.mkdir(parents=True, exist_ok=True)
    out_json = args.out / "exp017b_decomp_results.json"
    out_json.write_text(json.dumps(report, indent=2))

    # ── Console summary ──
    def line(label: str, s: dict) -> str:
        if not s or s.get("n", 0) == 0:
            return f"  {label:<22} n=0"
        return (f"  {label:<22} n={s['n']:<4} WR={s['win_rate']*100:5.1f}%  "
                f"EV/bet=${s['ev_per_bet_usd']:+7.3f}  "
                f"$/staked={s['pnl_per_dollar']*100:+6.2f}%  "
                f"PnL=${s['total_pnl']:+8.2f}  "
                f"CI[{s['ci_lo']:+.3f},{s['ci_hi']:+.3f}] "
                f"P(EV>0)={s['p_ev_gt_0']*100:4.1f}%")

    print("=" * 100)
    print(f"EXP-017B EDGE DECOMPOSITION  |  {args.portfolio}")
    print("=" * 100)
    print(line("OVERALL", overall))
    for section in ["robustness", "by_direction", "by_threshold",
                    "by_edge_bucket_all", "by_edge_bucket_NO_only",
                    "by_mip_bucket", "NO_by_threshold", "by_time_window"]:
        print(f"\n[{section}]")
        for k, s in report[section].items():
            line_out = line(k, s)
            print(line_out)
    print("\n[contrasts]")
    for k, v in report["contrasts"].items():
        print(f"  {k}: p={v}")
    print("\n[invariants]", report["invariants"])
    print(f"\nWrote {out_json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
