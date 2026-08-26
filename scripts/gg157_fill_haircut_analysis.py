#!/usr/bin/env python3
"""GG-157/T-488: measure realized mid-vs-book fill haircut for T4M-PROJ epoch-12
positions (props) and synthetically for game markets. MEASUREMENT ONLY.

Haircut model (derived from scripts/phase0_market_survey.py::_book_metrics):
  - _book_metrics gives, per depth observation: mid_cents, half_spread_cents,
    top_of_book_contracts{yes,no}, within_5c_contracts{yes,no}.
  - Buying YES crosses NO-side resting liquidity (yes_ask = 100 - best_no), so
    the size available to a YES taker at touch is top_of_book_contracts["no"],
    and depth-to-5c-wall is within_5c_contracts["no"]. Symmetric for NO buyers
    using the "yes" side. (Confirmed via _book_metrics source, in-code comments.)
  - haircut(contracts) in dollars/contract, relative to recorded mid:
        contracts <= touch_size        -> half_spread_cents/100  (touch-only)
        touch_size < contracts <= wall_size -> linear interpolation between
                                                half_spread and $0.05 (the 5c
                                                measurement wall)
        contracts > wall_size          -> $0.05, flagged depth_exhausted
                                            (floor estimate, likely an
                                            UNDERESTIMATE of true cost)
  - Depth observations are per-sampled-ticker within a family (2 samples per
    family per run, GG-155 balanced), not per-exact-position-ticker (1080
    KXMLBHIT depth rows vs 6867 epoch-12 evaluations) -- so this is a nearest
    -in-time, family-level proxy for prevailing book conditions, not an
    exact-ticker join. That is what "join to nearest depth observation" means
    here given the sampling budget; stated explicitly, not hidden.
"""
import json
import glob
import math
import statistics
import sys
from pathlib import Path
from datetime import datetime, timezone

sys.path.insert(0, str(Path(__file__).resolve().parent))
from run_power_calc import z_for  # noqa: E402  (reuse project's own inverse-normal, not scipy)

DEPTH_DIR = "exp_output/PRICE_ARCHIVE"
LEDGER = "logs/.vps_portfolio_cache_mlb_t4.json"
WALL_CENTS = 5.0


def parse_ts(s):
    return datetime.strptime(s, "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=timezone.utc) \
        if "." in s else datetime.strptime(s, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)


def load_depth(family=None, series_tickers=None):
    rows = []
    for fp in sorted(glob.glob(f"{DEPTH_DIR}/depth_*.jsonl")):
        with open(fp) as f:
            for line in f:
                try:
                    d = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if not d.get("usable"):
                    continue
                if family and d.get("family") != family:
                    continue
                if series_tickers and d.get("series_ticker") not in series_tickers:
                    continue
                d["_ts"] = parse_ts(d["run_ts"])
                rows.append(d)
    rows.sort(key=lambda r: r["_ts"])
    return rows


def nearest_depth(depth_rows, ts):
    # depth_rows sorted by ts; linear-ish binary search
    import bisect
    keys = [r["_ts"] for r in depth_rows]
    i = bisect.bisect_left(keys, ts)
    candidates = []
    if i < len(depth_rows):
        candidates.append(depth_rows[i])
    if i > 0:
        candidates.append(depth_rows[i - 1])
    if not candidates:
        return None
    return min(candidates, key=lambda r: abs((r["_ts"] - ts).total_seconds()))


def haircut_for(depth_row, direction, contracts):
    half_spread = depth_row["half_spread_cents"] / 100.0
    side = "no" if direction == "YES" else "yes"
    touch = depth_row["top_of_book_contracts"][side]
    wall = depth_row["within_5c_contracts"][side]
    depth_exhausted = False
    if contracts <= touch:
        hc = half_spread
    elif wall > touch and contracts <= wall:
        frac = (contracts - touch) / (wall - touch)
        hc = half_spread + (0.05 - half_spread) * frac
    else:
        hc = 0.05
        depth_exhausted = True
    return hc, depth_exhausted


def pct(vals, p):
    if not vals:
        return None
    s = sorted(vals)
    k = (len(s) - 1) * p
    f, c = int(k), min(int(k) + 1, len(s) - 1)
    if f == c:
        return s[f]
    return s[f] + (s[c] - s[f]) * (k - f)


def summarize(label, vals):
    if not vals:
        print(f"{label}: n=0 (no data)")
        return
    print(f"{label}: n={len(vals)} mean={statistics.mean(vals):.4f} "
          f"median={statistics.median(vals):.4f} p10={pct(vals,0.10):.4f} "
          f"p90={pct(vals,0.90):.4f} min={min(vals):.4f} max={max(vals):.4f}")


# ---------------------------------------------------------------------------
# TASK 1 + 2: props (KXMLBHIT / PLAYER_PROP), epoch-12 T4M-PROJ
# ---------------------------------------------------------------------------
print("=" * 78)
print("TASK 1/2 -- T4M-PROJ epoch-12 props fill haircut")
print("=" * 78)

with open(LEDGER) as f:
    ledger = json.load(f)
all_pos = ledger["closed_positions"] + ledger["open_positions"] + ledger.get("rejected_positions", [])
e12 = [p for p in all_pos if p.get("logic_epoch") == 12 and p.get("band") == "T4M-PROJ"
       and p.get("status") in ("OPEN", "CLOSED")]

depth_covered = [p for p in e12 if p["entered_at"] >= "2026-08-04"]
depth_uncovered = [p for p in e12 if p["entered_at"] < "2026-08-04"]
print(f"traded epoch-12 T4M-PROJ positions: {len(e12)} "
      f"(depth-covered={len(depth_covered)}, pre-depth-window excluded={len(depth_uncovered)})")

prop_depth = load_depth(family="PLAYER_PROP")
print(f"PLAYER_PROP (KXMLBHIT) usable depth observations available: {len(prop_depth)}")

haircuts = []
depth_exhausted_ct = 0
adjusted_pnls = []
raw_pnls = []
per_position = []

for p in depth_covered:
    ts = parse_ts(p["entered_at"])
    d = nearest_depth(prop_depth, ts)
    if d is None:
        continue
    contracts = p.get("kalshi_contracts") or round(p["contracts"])
    hc, exhausted = haircut_for(d, p["direction"], contracts)
    if exhausted:
        depth_exhausted_ct += 1
    haircuts.append(hc)
    per_position.append((p, hc, exhausted))
    if p["status"] == "CLOSED" and p.get("outcome") in ("WIN", "LOSS"):
        raw_pnls.append(p["pnl"])
        adjusted_pnls.append(p["pnl"] - contracts * hc)

summarize("Per-contract haircut ($/contract, PLAYER_PROP)", haircuts)
print(f"depth-exhausted (floor-estimate, size > 5c-wall depth): {depth_exhausted_ct}/{len(haircuts)} "
      f"({100*depth_exhausted_ct/len(haircuts):.1f}%)" if haircuts else "n/a")

print()
print("-- resolved-only cohort (CLOSED, WIN/LOSS, depth-covered) --")
print(f"n resolved = {len(raw_pnls)}")
print("NOTE: this is 'traded, depth-covered, resolved' -- NOT necessarily identical to "
      "run_power_calc.py's official filter_clean() clean_n cohort (which applies its own "
      "epoch-floor/legitimacy filters). Same formula (n* = ((z_a+z_b)*sigma/mu)^2, sample "
      "stdev ddof=1, alpha=0.05, power=0.95) is reused via run_power_calc.z_for for an "
      "apples-to-apples before/after comparison on THIS cohort, not a substitute for the "
      "official gate figure.")
if raw_pnls:
    mu0, s0 = statistics.mean(raw_pnls), statistics.stdev(raw_pnls)
    mu1, s1 = statistics.mean(adjusted_pnls), statistics.stdev(adjusted_pnls)
    print(f"mean P&L/bet BEFORE haircut: ${mu0:.4f}")
    print(f"mean P&L/bet AFTER  haircut: ${mu1:.4f}")
    print(f"sample stdev P&L/bet BEFORE (ddof=1): ${s0:.4f}")
    print(f"sample stdev P&L/bet AFTER  (ddof=1): ${s1:.4f}")
    wins_before = sum(1 for x in raw_pnls if x > 0)
    wins_after = sum(1 for x in adjusted_pnls if x > 0)
    print(f"positions with pnl>0 BEFORE: {wins_before}/{len(raw_pnls)}  "
          f"AFTER: {wins_after}/{len(adjusted_pnls)}")

    def n_star(mu, sigma, alpha=0.05, power=0.95):
        if mu is None or sigma in (None, 0) or mu <= 0:
            return None
        z_a, z_b = z_for(alpha), z_for(1.0 - power)
        return math.ceil(((z_a + z_b) * sigma / mu) ** 2)

    ns0 = n_star(mu0, s0)
    ns1 = n_star(mu1, s1)
    print(f"n* BEFORE haircut (alpha=0.05, power=0.95): {ns0}  "
          f"(current n={len(raw_pnls)} {'MEETS' if ns0 and len(raw_pnls)>=ns0 else 'does not meet'} this)")
    print(f"n* AFTER  haircut (alpha=0.05, power=0.95): {ns1}  "
          f"(current n={len(adjusted_pnls)} {'MEETS' if ns1 and len(adjusted_pnls)>=ns1 else 'does not meet'} this)")

print()
print("=" * 78)
print("TASK 4 -- synthetic $1.00 ADR-0050 flat-stake haircut, GAME MARKETS")
print("=" * 78)

game_families = {
    "GAME_WINNER": {"KXMLBGAME"},
    "GAME_TOTAL": {"KXMLBTOTAL"},   # full-game only, exclude KXMLBF5TOTAL per task scope
    "RUN_LINE": {"KXMLBSPREAD"},    # full-game only, exclude KXMLBF5SPREAD
}

results_json = {
    "props": {
        "traded_epoch12_t4m_proj": len(e12),
        "depth_covered": len(depth_covered),
        "pre_depth_window_excluded": len(depth_uncovered),
        "haircut_per_contract_usd": {
            "n": len(haircuts), "mean": statistics.mean(haircuts) if haircuts else None,
            "median": statistics.median(haircuts) if haircuts else None,
            "p10": pct(haircuts, 0.10), "p90": pct(haircuts, 0.90),
            "min": min(haircuts) if haircuts else None, "max": max(haircuts) if haircuts else None,
            "depth_exhausted_n": depth_exhausted_ct,
        },
        "resolved_cohort": {
            "n": len(raw_pnls),
            "mean_pnl_before": statistics.mean(raw_pnls) if raw_pnls else None,
            "mean_pnl_after": statistics.mean(adjusted_pnls) if raw_pnls else None,
            "sample_stdev_before": statistics.stdev(raw_pnls) if len(raw_pnls) > 1 else None,
            "sample_stdev_after": statistics.stdev(adjusted_pnls) if len(raw_pnls) > 1 else None,
            "n_star_before": n_star(statistics.mean(raw_pnls), statistics.stdev(raw_pnls)) if len(raw_pnls) > 1 else None,
            "n_star_after": n_star(statistics.mean(adjusted_pnls), statistics.stdev(adjusted_pnls)) if len(raw_pnls) > 1 else None,
        } if raw_pnls else None,
    },
    "game_markets_synthetic": {},
    "d1_status": "NOT APPLIED -- ADR-0055 Status: PROPOSED, not accepted; figures scoped to uncorrected ledger",
}

for label, tickers in game_families.items():
    rows = load_depth(family=label, series_tickers=tickers)
    hcs_yes = []
    hcs_no = []
    for d in rows:
        # $1.00 stake -> contracts = 1 / price. Price unknown per-contract without
        # a specific market; use the depth row's own mid as the reference price
        # (self-consistent: this IS the market being priced).
        mid = d["mid_cents"] / 100.0
        if 0 < mid < 1:
            contracts_yes = round(1.0 / mid)
            contracts_no = round(1.0 / (1.0 - mid))
        else:
            continue
        hc_y, _ = haircut_for(d, "YES", max(contracts_yes, 1))
        hc_n, _ = haircut_for(d, "NO", max(contracts_no, 1))
        hcs_yes.append(hc_y)
        hcs_no.append(hc_n)
    print(f"-- {label} ({sorted(tickers)}) --")
    summarize(f"  YES-side haircut ($/contract)", hcs_yes)
    summarize(f"  NO-side haircut ($/contract)", hcs_no)
    combined = hcs_yes + hcs_no
    if combined:
        summarize(f"  combined haircut ($/contract)", combined)
    print()
    results_json["game_markets_synthetic"][label] = {
        "n": len(combined),
        "mean": statistics.mean(combined) if combined else None,
        "median": statistics.median(combined) if combined else None,
        "p10": pct(combined, 0.10), "p90": pct(combined, 0.90),
        "min": min(combined) if combined else None, "max": max(combined) if combined else None,
    }

out_path = Path("exp_output/T488_GG157_FILL_HAIRCUT/results.json")
out_path.parent.mkdir(parents=True, exist_ok=True)
out_path.write_text(json.dumps(results_json, indent=2, default=str))
print(f"\nWrote {out_path}")
