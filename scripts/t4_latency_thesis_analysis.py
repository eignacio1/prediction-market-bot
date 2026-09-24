#!/usr/bin/env python3
"""T-569: T4 latency thesis measurement (D2/D3/D4).

Implements the methodology pre-registered in
05_RESEARCH_EXPERIMENTS/RESULTS_SUMMARIES/T569_t4_latency_thesis_PREREGISTRATION.md.
Reads only the fresh VPS pull of t4_mlb_cycle_log.jsonl; touches no ledger,
portfolio, or outcome data. Read-only with respect to the repo except for
writing derived summary artifacts under exp_output/t4_latency_thesis/.

Performance note: cluster (ticker) block-bootstrap is done on aggregated
per-cluster sufficient statistics (n, sums of x/y/x^2/xy, ...), not on raw
row lists, so each of the 1000 bootstrap replicates is O(n_clusters) rather
than O(n_rows). This is required at this data volume (~390k rows / ~8.3k
tickers) to keep the block bootstrap tractable in pure Python.
"""
import json
import math
import random
import statistics
import sys
from collections import defaultdict
from datetime import datetime

random.seed(569)

IN_PATH = "exp_output/t4_latency_thesis/t4_mlb_cycle_log_fresh.jsonl"
OUT_DIR = "exp_output/t4_latency_thesis"
N_BOOT = 1000
MAX_K = 4
MIN_CELL_N = 30


def load_rows(path):
    rows = []
    with open(path) as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    return rows


def parse_ts(ts):
    return datetime.fromisoformat(ts).timestamp()


def build_sequences(rows):
    by_ticker = defaultdict(list)
    for r in rows:
        by_ticker[r["ticker"]].append(r)
    for t in by_ticker:
        by_ticker[t].sort(key=lambda r: r["ts"])
    return by_ticker


# ---------- sufficient-statistics accumulators ----------

def add_scalar(stats, key, v):
    n, s = stats.get(key, (0, 0.0))
    stats[key] = (n + 1, s + v)


def agg_scalar(stats, keys):
    n = 0
    s = 0.0
    for k in keys:
        t = stats.get(k)
        if t is None:
            continue
        tn, ts = t
        n += tn
        s += ts
    return n, s


def bootstrap_mean(stats, n_boot=N_BOOT):
    clusters = list(stats.keys())
    if not clusters:
        return (float("nan"), float("nan"), float("nan"), float("nan"), 0)
    n_all, s_all = agg_scalar(stats, clusters)
    if n_all == 0:
        return (float("nan"), float("nan"), float("nan"), float("nan"), 0)
    point = s_all / n_all
    if len(clusters) < 2:
        return (point, float("nan"), float("nan"), float("nan"), n_all)
    boots = []
    ncl = len(clusters)
    for _ in range(n_boot):
        sample = [clusters[random.randrange(ncl)] for _ in range(ncl)]
        n_b, s_b = agg_scalar(stats, sample)
        if n_b > 0:
            boots.append(s_b / n_b)
    if len(boots) < 10:
        return (point, float("nan"), float("nan"), float("nan"), n_all)
    boots.sort()
    se = statistics.pstdev(boots)
    lo = boots[int(0.025 * len(boots))]
    hi = boots[int(0.975 * len(boots)) - 1]
    return (point, se, lo, hi, n_all)


def add_xy(stats, key, x, y):
    n, sx, sy, sxx, sxy = stats.get(key, (0, 0.0, 0.0, 0.0, 0.0))
    stats[key] = (n + 1, sx + x, sy + y, sxx + x * x, sxy + x * y)


def agg_xy(stats, keys):
    n = sx = sy = sxx = sxy = 0.0
    for k in keys:
        t = stats.get(k)
        if t is None:
            continue
        tn, tsx, tsy, tsxx, tsxy = t
        n += tn
        sx += tsx
        sy += tsy
        sxx += tsxx
        sxy += tsxy
    return n, sx, sy, sxx, sxy


def slope_from_xy_agg(agg):
    n, sx, sy, sxx, sxy = agg
    if n < 2:
        return float("nan")
    sxx_c = sxx - (sx * sx) / n
    sxy_c = sxy - (sx * sy) / n
    if sxx_c == 0:
        return float("nan")
    return sxy_c / sxx_c


def bootstrap_slope(stats, n_boot=N_BOOT):
    clusters = list(stats.keys())
    if len(clusters) < 2:
        return (float("nan"), float("nan"), float("nan"), float("nan"), 0)
    agg_all = agg_xy(stats, clusters)
    point = slope_from_xy_agg(agg_all)
    n_all = agg_all[0]
    boots = []
    ncl = len(clusters)
    for _ in range(n_boot):
        sample = [clusters[random.randrange(ncl)] for _ in range(ncl)]
        agg = agg_xy(stats, sample)
        s = slope_from_xy_agg(agg)
        if not math.isnan(s):
            boots.append(s)
    if len(boots) < 10:
        return (point, float("nan"), float("nan"), float("nan"), n_all)
    boots.sort()
    se = statistics.pstdev(boots)
    lo = boots[int(0.025 * len(boots))]
    hi = boots[int(0.975 * len(boots)) - 1]
    return (point, se, lo, hi, n_all)


def add_multi(stats, key, x1, x2, y):
    n, sx1, sx2, sy, s11, s22, s12, s1y, s2y = stats.get(
        key, (0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    )
    stats[key] = (
        n + 1, sx1 + x1, sx2 + x2, sy + y,
        s11 + x1 * x1, s22 + x2 * x2, s12 + x1 * x2,
        s1y + x1 * y, s2y + x2 * y,
    )


def agg_multi(stats, keys):
    n = sx1 = sx2 = sy = s11 = s22 = s12 = s1y = s2y = 0.0
    for k in keys:
        t = stats.get(k)
        if t is None:
            continue
        (tn, tsx1, tsx2, tsy, ts11, ts22, ts12, ts1y, ts2y) = t
        n += tn; sx1 += tsx1; sx2 += tsx2; sy += tsy
        s11 += ts11; s22 += ts22; s12 += ts12; s1y += ts1y; s2y += ts2y
    return n, sx1, sx2, sy, s11, s22, s12, s1y, s2y


def multi_coefs_from_agg(agg):
    n, sx1, sx2, sy, s11, s22, s12, s1y, s2y = agg
    if n < 3:
        return (float("nan"), float("nan"))
    S11 = s11 - (sx1 * sx1) / n
    S22 = s22 - (sx2 * sx2) / n
    S12 = s12 - (sx1 * sx2) / n
    S1y = s1y - (sx1 * sy) / n
    S2y = s2y - (sx2 * sy) / n
    det = S11 * S22 - S12 * S12
    if det == 0:
        return (float("nan"), float("nan"))
    b1 = (S1y * S22 - S2y * S12) / det
    b2 = (S2y * S11 - S1y * S12) / det
    return (b1, b2)


def bootstrap_multi_b1(stats, n_boot=N_BOOT):
    clusters = list(stats.keys())
    if len(clusters) < 2:
        return (float("nan"), float("nan"))
    agg_all = agg_multi(stats, clusters)
    b1_point, b2_point = multi_coefs_from_agg(agg_all)
    n_all = agg_all[0]
    boots = []
    ncl = len(clusters)
    for _ in range(n_boot):
        sample = [clusters[random.randrange(ncl)] for _ in range(ncl)]
        agg = agg_multi(stats, sample)
        b1, _ = multi_coefs_from_agg(agg)
        if not math.isnan(b1):
            boots.append(b1)
    if len(boots) < 10:
        return {"point": b1_point, "boot_se": float("nan"), "ci_lo": float("nan"),
                "ci_hi": float("nan"), "n": n_all}, b2_point
    boots.sort()
    se = statistics.pstdev(boots)
    lo = boots[int(0.025 * len(boots))]
    hi = boots[int(0.975 * len(boots)) - 1]
    return {"point": b1_point, "boot_se": se, "ci_lo": lo, "ci_hi": hi, "n": n_all}, b2_point


def pct(p, sorted_arr):
    if not sorted_arr:
        return float("nan")
    idx = min(len(sorted_arr) - 1, int(p * len(sorted_arr)))
    return sorted_arr[idx]


def inning_bucket(inn):
    if inn is None:
        return None
    if inn <= 3:
        return "early_1-3"
    if inn <= 6:
        return "mid_4-6"
    return "late_7plus"


def ab_bucket(ab):
    if ab is None:
        return None
    if ab <= 0:
        return "0"
    if ab == 1:
        return "1"
    if ab == 2:
        return "2"
    return "3plus"


def price_bucket(mip):
    if mip is None:
        return None
    if mip < 0.10:
        return "<0.10"
    if mip < 0.30:
        return "0.10-0.30"
    if mip < 0.50:
        return "0.30-0.50"
    if mip < 0.70:
        return "0.50-0.70"
    if mip < 0.90:
        return "0.70-0.90"
    return ">0.90"


def main():
    print("Loading fresh cycle log...", file=sys.stderr)
    rows = load_rows(IN_PATH)
    print(f"Loaded {len(rows)} rows", file=sys.stderr)
    by_ticker = build_sequences(rows)
    print(f"{len(by_ticker)} distinct tickers", file=sys.stderr)

    results = {"meta": {"n_rows": len(rows), "n_tickers": len(by_ticker), "n_boot": N_BOOT}}

    # ================= D2 =================
    etypes = ("H_EVENT", "AB_EVENT", "INNING_EVENT")
    d2_pooled_stats = {e: {k: {} for k in range(1, MAX_K + 1)} for e in etypes}
    d2_signed_stats = {e: {k: {} for k in range(1, MAX_K + 1)} for e in etypes}
    d2_elapsed = {e: {k: [] for k in range(1, MAX_K + 1)} for e in etypes}
    d2_already_closed = {e: 0 for e in etypes}
    d2_event_total = {e: 0 for e in etypes}

    for ticker, seq in by_ticker.items():
        for i in range(1, len(seq)):
            prev, cur = seq[i - 1], seq[i]
            events = []
            if cur.get("h_so_far") is not None and prev.get("h_so_far") is not None:
                if cur["h_so_far"] > prev["h_so_far"]:
                    events.append("H_EVENT")
            if cur.get("ab_so_far") is not None and prev.get("ab_so_far") is not None:
                if cur["ab_so_far"] > prev["ab_so_far"]:
                    events.append("AB_EVENT")
            if cur.get("inning") is not None and prev.get("inning") is not None:
                if cur["inning"] != prev["inning"]:
                    events.append("INNING_EVENT")
            if not events:
                continue
            ge_t = cur.get("gross_edge")
            mip_t = cur.get("mip")
            if mip_t is None:
                continue
            sign = None
            if ge_t is not None and ge_t != 0:
                sign = 1 if ge_t > 0 else -1
            for etype in events:
                d2_event_total[etype] += 1
                if ge_t is not None and abs(ge_t) < 0.005:
                    d2_already_closed[etype] += 1
                for k in range(1, MAX_K + 1):
                    j = i + k
                    if j >= len(seq):
                        break
                    fut = seq[j]
                    mip_fut = fut.get("mip")
                    if mip_fut is None:
                        continue
                    dm = mip_fut - mip_t
                    add_scalar(d2_pooled_stats[etype][k], ticker, dm)
                    if sign is not None:
                        add_scalar(d2_signed_stats[etype][k], ticker, dm * sign)
                    try:
                        dt = parse_ts(fut["ts"]) - parse_ts(cur["ts"])
                        d2_elapsed[etype][k].append(dt)
                    except Exception:
                        pass

    d2_out = {}
    for etype in etypes:
        d2_out[etype] = {
            "n_events": d2_event_total[etype],
            "already_closed_ge_lt_0.005_frac": (
                d2_already_closed[etype] / d2_event_total[etype]
                if d2_event_total[etype] else float("nan")
            ),
            "horizons": {},
        }
        for k in range(1, MAX_K + 1):
            mean_p, se_p, lo_p, hi_p, n_p = bootstrap_mean(d2_pooled_stats[etype][k])
            mean_s, se_s, lo_s, hi_s, n_s = bootstrap_mean(d2_signed_stats[etype][k])
            elapsed_sorted = sorted(d2_elapsed[etype][k])
            d2_out[etype]["horizons"][f"k{k}"] = {
                "pooled_delta_mip": {"mean": mean_p, "boot_se": se_p, "ci_lo": lo_p, "ci_hi": hi_p, "n": n_p},
                "signed_delta_mip_x_sign_gross_edge": {"mean": mean_s, "boot_se": se_s, "ci_lo": lo_s, "ci_hi": hi_s, "n": n_s},
                "elapsed_seconds": {
                    "p10": pct(0.10, elapsed_sorted),
                    "median": pct(0.50, elapsed_sorted),
                    "p90": pct(0.90, elapsed_sorted),
                    "n": len(elapsed_sorted),
                },
            }
    results["D2"] = d2_out
    print("D2 done", file=sys.stderr)

    # ================= D3 =================
    d3_fwd_stats = {k: {} for k in range(1, MAX_K + 1)}
    d3_bwd_stats = {k: {} for k in range(1, MAX_K + 1)}
    d3_rev_uni_stats = {k: {} for k in range(1, MAX_K + 1)}   # x=own_dislocation, y=dmip_fwd
    d3_rev_multi_stats = {k: {} for k in range(1, MAX_K + 1)}  # x1=ge, x2=own_dislocation, y=dmip_fwd

    for ticker, seq in by_ticker.items():
        mip_hist = []
        for i, row in enumerate(seq):
            mip_t = row.get("mip")
            ge_t = row.get("gross_edge")
            if mip_t is not None:
                mip_hist.append(mip_t)
            if ge_t is None or mip_t is None:
                continue
            trailing_mean = None
            if len(mip_hist) >= 4:
                trailing_mean = statistics.fmean(mip_hist[:-1])
            for k in range(1, MAX_K + 1):
                j_fwd = i + k
                j_bwd = i - k
                if j_fwd < len(seq):
                    mip_fwd = seq[j_fwd].get("mip")
                    if mip_fwd is not None:
                        dmip_fwd = mip_fwd - mip_t
                        add_xy(d3_fwd_stats[k], ticker, ge_t, dmip_fwd)
                        if trailing_mean is not None:
                            own_dis = mip_t - trailing_mean
                            add_xy(d3_rev_uni_stats[k], ticker, own_dis, dmip_fwd)
                            add_multi(d3_rev_multi_stats[k], ticker, ge_t, own_dis, dmip_fwd)
                if j_bwd >= 0:
                    mip_bwd = seq[j_bwd].get("mip")
                    if mip_bwd is not None:
                        dmip_bwd = mip_t - mip_bwd
                        add_xy(d3_bwd_stats[k], ticker, ge_t, dmip_bwd)

    d3_out = {}
    for k in range(1, MAX_K + 1):
        slope_fwd, se_fwd, lo_fwd, hi_fwd, n_fwd = bootstrap_slope(d3_fwd_stats[k])
        slope_bwd, se_bwd, lo_bwd, hi_bwd, n_bwd = bootstrap_slope(d3_bwd_stats[k])
        slope_dis, se_dis, lo_dis, hi_dis, n_dis = bootstrap_slope(d3_rev_uni_stats[k])
        b_ge_result, b_dis_point = bootstrap_multi_b1(d3_rev_multi_stats[k])

        d3_out[f"k{k}"] = {
            "forward": {"slope": slope_fwd, "boot_se": se_fwd, "ci_lo": lo_fwd, "ci_hi": hi_fwd, "n": n_fwd},
            "backward_placebo": {"slope": slope_bwd, "boot_se": se_bwd, "ci_lo": lo_bwd, "ci_hi": hi_bwd, "n": n_bwd},
            "reversion_confound": {
                "own_dislocation_univariate_slope": {"slope": slope_dis, "boot_se": se_dis, "ci_lo": lo_dis, "ci_hi": hi_dis, "n": n_dis},
                "multiple_regression_gross_edge_coef": b_ge_result,
                "multiple_regression_own_dislocation_coef_point": b_dis_point,
            },
        }
        print(f"D3 k={k} done", file=sys.stderr)
    results["D3"] = d3_out

    # ================= D4 =================
    seg_fwd_stats = defaultdict(dict)   # (dim,bucket,k) -> ticker stats (x=ge,y=dmip_fwd)
    seg_bwd_stats = defaultdict(dict)   # (dim,bucket,k) -> ticker stats (x=ge,y=dmip_bwd) -- placebo per cell

    for ticker, seq in by_ticker.items():
        for i, row in enumerate(seq):
            ge_t = row.get("gross_edge")
            mip_t = row.get("mip")
            if ge_t is None or mip_t is None:
                continue
            ib = inning_bucket(row.get("inning"))
            ab = ab_bucket(row.get("ab_remaining"))
            pb = price_bucket(mip_t)
            th = row.get("threshold")
            dims = []
            if ib is not None:
                dims.append(("inning", ib))
            if ab is not None:
                dims.append(("ab_remaining", ab))
            if pb is not None:
                dims.append(("price", pb))
            if th is not None:
                dims.append(("threshold", str(th)))
            for k in range(1, MAX_K + 1):
                j_fwd = i + k
                j_bwd = i - k
                mip_fwd = seq[j_fwd].get("mip") if j_fwd < len(seq) else None
                mip_bwd = seq[j_bwd].get("mip") if j_bwd >= 0 else None
                for dim, bucket in dims:
                    key = (dim, bucket, k)
                    if mip_fwd is not None:
                        add_xy(seg_fwd_stats[key], ticker, ge_t, mip_fwd - mip_t)
                    if mip_bwd is not None:
                        add_xy(seg_bwd_stats[key], ticker, ge_t, mip_t - mip_bwd)

    d4_out = defaultdict(dict)
    all_keys = set(seg_fwd_stats.keys()) | set(seg_bwd_stats.keys())
    for (dim, bucket, k) in all_keys:
        fwd = seg_fwd_stats.get((dim, bucket, k), {})
        bwd = seg_bwd_stats.get((dim, bucket, k), {})
        n_fwd = sum(v[0] for v in fwd.values())
        cell_key = f"{bucket}__k{k}"
        if n_fwd < MIN_CELL_N:
            d4_out[dim][cell_key] = {"status": "INSUFFICIENT_N", "n": n_fwd}
            continue
        slope_f, se_f, lo_f, hi_f, n_f = bootstrap_slope(fwd)
        slope_b, se_b, lo_b, hi_b, n_b = bootstrap_slope(bwd)
        d4_out[dim][cell_key] = {
            "forward": {"slope": slope_f, "boot_se": se_f, "ci_lo": lo_f, "ci_hi": hi_f, "n": n_f},
            "backward_placebo": {"slope": slope_b, "boot_se": se_b, "ci_lo": lo_b, "ci_hi": hi_b, "n": n_b},
        }
    results["D4"] = dict(d4_out)
    print("D4 done", file=sys.stderr)

    out_path = f"{OUT_DIR}/t569_results.json"
    with open(out_path, "w") as fh:
        json.dump(results, fh, indent=2, default=str)
    print(f"Wrote {out_path}", file=sys.stderr)


if __name__ == "__main__":
    main()
