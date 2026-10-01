#!/usr/bin/env python3
"""EXP-032 execution cost surface (T-603, GG-325). Implements the frozen pre-registration
`05_RESEARCH_EXPERIMENTS/EXP032_EXECUTION_COST_SURFACE_PREREGISTRATION_2026-10-01.md`.

Cost side only. B, the 10-bucket tables, the null bands and B's CIs are read from EXP-031's
`d3_d4_results.json` as given inputs and are never re-derived. Settlements are read from
EXP-031's cache and never re-fetched. The archive and cache are read-only. No model, no order,
no sizing.

Usage:
    python3 scripts/execution_cost_surface.py --archive <PRICE_ARCHIVE> \
        --exp031 exp_output/EXP-031-MKT-EFF-SURVEY --out exp_output/EXP-032-EXECUTION-COST-SURFACE
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import re
import sys
from datetime import datetime
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from market_efficiency_survey import (  # noqa: E402  (EXP-031, read-only reuse)
    N_BUCKETS, N_DRAWS, NULL_Q, SEED, _null_B, calib_gap,
)

# ------------------------------------------------------------------ frozen parameters (prereg §2-§7)
TAU_EDGES = [-np.inf, 0, 1, 3, 6, 12, 24, 48, np.inf]
TAU_LABELS = ["<0 (in-play)", "[0,1)", "[1,3)", "[3,6)", "[6,12)", "[12,24)", "[24,48)", ">=48"]
PHASES = {"overnight 00-06": (0, 6), "morning 06-12": (6, 12), "afternoon 12-18": (12, 18), "evening 18-24": (18, 24)}
CELL_MIN_SNAP, CELL_MIN_TICKERS, CELL_MIN_DAYS = 200, 30, 5
B_MIN_TICKERS, B_MIN_DAYS = 200, 5
FILL_RATE_MIN = 0.10
DRIFT_MIN_TICKERS, DRIFT_MIN_DAYS = 200, 5
DRIFT_MIN_FIRST_TAU_H, DRIFT_MIN_GAP_H = 6.0, 1.0
STAKES = [5, 25, 100, 500]
DEPTH_MIN_ROWS, DEPTH_MIN_TICKERS, DEPTH_COVER = 30, 10, 5.0
CLOCK_MEDIAN_RANGE, CLOCK_SHARE_MIN, CLOCK_MAX_H = (2.0, 4.5), 0.95, 8.0
ET = ZoneInfo("America/New_York")
_TICKER_RE = re.compile(r"-(\d{2})([A-Z]{3})(\d{2})(\d{4})?[A-Z]")
_MONTHS = {m: i for i, m in enumerate(["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"], 1)}


# ------------------------------------------------------------------ ticker clock
def parse_ticker_start(ticker: str):
    """(start_utc or None, game_date or None). MLB tickers embed ET start time; NFL tickers do not."""
    m = _TICKER_RE.search(ticker)
    if not m or m.group(2) not in _MONTHS:
        return None, None
    yy, mon, dd, hhmm = int(m.group(1)), _MONTHS[m.group(2)], int(m.group(3)), m.group(4)
    try:
        date = datetime(2000 + yy, mon, dd).date()
        if not hhmm:
            return None, date
        hh, mi = int(hhmm[:2]), int(hhmm[2:])
        return datetime(2000 + yy, mon, dd, hh, mi, tzinfo=ET).astimezone(ZoneInfo("UTC")), date
    except ValueError:
        return None, None


# ------------------------------------------------------------------ loading
def load_archive(archive_dir: str) -> pd.DataFrame:
    parts = []
    for path in sorted(glob.glob(os.path.join(archive_dir, "prices_*.jsonl"))):
        parts.append(pd.read_json(path, lines=True, dtype=False))
    df = pd.concat(parts, ignore_index=True)
    for c in ["yes_bid", "yes_ask", "no_bid", "no_ask", "yes_mid", "half_spread"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df["run_ts"] = df["run_ts"].astype(str)
    return df


def load_settlements(settle_dir: str) -> dict:
    st = {}
    for f in glob.glob(os.path.join(settle_dir, "*.json")):
        st.update(json.load(open(f)))
    return st


def enrich(df: pd.DataFrame, settle: dict) -> pd.DataFrame:
    """Attach clocks, buckets, side costs. Adds columns; never drops rows."""
    df = df.copy()
    df["t"] = pd.to_datetime(df["run_ts"], utc=True)
    ct = df["ticker"].map(lambda t: (settle.get(t) or {}).get("close_time"))
    df["close_t"] = pd.to_datetime(ct, utc=True)
    df["tau_close_h"] = (df["close_t"] - df["t"]).dt.total_seconds() / 3600.0
    uniq = df["ticker"].unique()
    starts = {t: parse_ticker_start(t) for t in uniq}
    df["start_t"] = pd.to_datetime(df["ticker"].map(lambda t: starts[t][0]), utc=True)
    df["game_date"] = df["ticker"].map(lambda t: starts[t][1])
    df["tau_start_h"] = (df["start_t"] - df["t"]).dt.total_seconds() / 3600.0
    df["et_hour"] = df["t"].dt.tz_convert(ET).dt.hour
    df["usable"] = (df["yes_bid"] > 0) & (df["yes_ask"] > 0) & df["yes_mid"].notna()
    df["vig"] = df["yes_ask"] + df["no_ask"] - 1.0
    df["yes_cost"] = df["yes_ask"] - df["yes_mid"]
    df["no_cost"] = df["no_ask"] - (1.0 - df["yes_mid"])
    df["price_b"] = np.minimum((df["yes_mid"] * N_BUCKETS).fillna(0).astype(int), N_BUCKETS - 1)
    df["yes_buyable"] = (df["yes_ask"] > 0) & (df["yes_ask"] < 0.99) & (df["no_bid"] > 0)
    df["no_buyable"] = (df["no_ask"] > 0) & (df["no_ask"] < 0.99) & (df["yes_bid"] > 0)
    df["day_utc"] = df["run_ts"].str[:10]
    return df


def clock_gate(df: pd.DataFrame) -> dict:
    """Prereg §2 sanity gate per MLB family: ticker start vs settlement-cache close."""
    out = {}
    for s, g in df[df["series_ticker"].str.startswith("KXMLB")].groupby("series_ticker"):
        t = g.drop_duplicates("ticker")
        d = (t["close_t"] - t["start_t"]).dt.total_seconds() / 3600.0
        d = d.dropna()
        if len(d) == 0:
            out[s] = {"passed": False, "n": 0, "reason": "no tickers with both clocks"}
            continue
        med = float(d.median()); share = float(((d > 0) & (d <= CLOCK_MAX_H)).mean())
        out[s] = {"passed": bool(CLOCK_MEDIAN_RANGE[0] <= med <= CLOCK_MEDIAN_RANGE[1] and share >= CLOCK_SHARE_MIN),
                  "n": int(len(d)), "median_close_minus_start_h": round(med, 3), "share_in_0_8h": round(share, 4)}
    return out


# ------------------------------------------------------------------ D1: the surface
def _cell_stats(g: pd.DataFrame) -> dict:
    n_snap, n_t = len(g), g["ticker"].nunique()
    n_d = g["game_date"].nunique() if g["game_date"].notna().any() else g["day_utc"].nunique()
    measured = bool(n_snap >= CELL_MIN_SNAP and n_t >= CELL_MIN_TICKERS and n_d >= CELL_MIN_DAYS)
    out = {"n_snap": int(n_snap), "n_tickers": int(n_t), "n_days": int(n_d), "measured": measured}
    if measured:
        hs = g["half_spread"]
        out.update({"hs_med": round(float(hs.median()), 5), "hs_p25": round(float(hs.quantile(.25)), 5),
                    "hs_p75": round(float(hs.quantile(.75)), 5), "vig_med": round(float(g["vig"].median()), 5)})
    return out


def tau_bucket(tau_h: pd.Series) -> pd.Series:
    return pd.cut(tau_h, bins=TAU_EDGES, labels=TAU_LABELS, right=False)


def surface_for_family(g: pd.DataFrame, use_start: bool) -> dict:
    """Marginals + 2-D tau x price and tau x phase cross-tabs for one family's usable snapshots."""
    u = g[g["usable"]].copy()
    tcol = "tau_start_h" if use_start else "tau_close_h"
    u["tb"] = tau_bucket(u[tcol])
    u["phase"] = pd.cut(u["et_hour"], bins=[-1, 5, 11, 17, 23], labels=list(PHASES))
    out = {"clock": "tau_start" if use_start else "tau_close", "usable_snapshots": int(len(u)),
           "all_rows": int(len(g)), "tau": {}, "phase": {}, "price": {}, "tau_x_price": {}, "tau_x_phase": {}}
    for k, grp in u.groupby("tb", observed=True):
        out["tau"][str(k)] = _cell_stats(grp)
    for k, grp in u.groupby("phase", observed=True):
        out["phase"][str(k)] = _cell_stats(grp)
    for k, grp in u.groupby("price_b"):
        out["price"][f"{k/N_BUCKETS:.1f}"] = _cell_stats(grp)
    for (a, b), grp in u.groupby(["tb", "price_b"], observed=True):
        out["tau_x_price"][f"{a}|{b/N_BUCKETS:.1f}"] = _cell_stats(grp)
    for (a, b), grp in u.groupby(["tb", "phase"], observed=True):
        out["tau_x_phase"][f"{a}|{b}"] = _cell_stats(grp)
    meas = sum(1 for c in out["tau_x_price"].values() if c["measured"])
    snaps_meas = sum(c["n_snap"] for c in out["tau_x_price"].values() if c["measured"])
    out["coverage"] = {"grid_cells": len(TAU_LABELS) * N_BUCKETS, "measured_cells": meas,
                       "measured_cell_share": round(meas / (len(TAU_LABELS) * N_BUCKETS), 4),
                       "snapshot_share_in_measured_cells": round(snaps_meas / max(len(u), 1), 4)}
    # side: costs reported separately; availability over ALL rows with a quote of either side
    out["side"] = {
        "yes_cost_median": round(float(u["yes_cost"].median()), 5), "no_cost_median": round(float(u["no_cost"].median()), 5),
        "max_abs_yes_minus_no_cost": round(float((u["yes_cost"] - u["no_cost"]).abs().max()), 8),
        "yes_buyable_share": round(float(g["yes_buyable"].mean()), 4), "no_buyable_share": round(float(g["no_buyable"].mean()), 4),
    }
    hs = u["half_spread"]
    out["ticks"] = {"share_whole_cent_hs": round(float(((hs * 100).round(6) % 1 == 0).mean()), 4),
                    "min_nonzero_hs": round(float(hs[hs > 0].min()), 5) if (hs > 0).any() else None}
    return out


# ------------------------------------------------------------------ shared building blocks
def first_seen(df: pd.DataFrame) -> pd.DataFrame:
    """EXP-031's decision snapshot: earliest usable snapshot per ticker."""
    u = df[df["usable"]].sort_values("run_ts", kind="stable")
    return u.drop_duplicates("ticker", keep="first")


def outcome_map(settle: dict, tickers) -> dict:
    return {t: (1.0 if settle[t]["result"] == "yes" else 0.0) for t in tickers
            if t in settle and settle[t].get("result") in ("yes", "no")}


def boot_median_ci(h: np.ndarray, labels: np.ndarray) -> list:
    """Cost-side cluster bootstrap of a median (EXP-031 machinery: N_DRAWS//4 resamples, SEED)."""
    rng = np.random.default_rng(SEED)
    uniq, inv = np.unique(labels, return_inverse=True)
    idx = [np.where(inv == k)[0] for k in range(len(uniq))]
    meds = []
    for _ in range(N_DRAWS // 4):
        pick = rng.integers(0, len(uniq), len(uniq))
        meds.append(float(np.median(h[np.concatenate([idx[k] for k in pick])])))
    return [float(np.percentile(meds, 2.5)), float(np.percentile(meds, 97.5))]


def boot_mean_ci(x: np.ndarray, labels: np.ndarray) -> list:
    rng = np.random.default_rng(SEED)
    uniq, inv = np.unique(labels, return_inverse=True)
    idx = [np.where(inv == k)[0] for k in range(len(uniq))]
    ms = []
    for _ in range(N_DRAWS // 4):
        pick = rng.integers(0, len(uniq), len(uniq))
        ms.append(float(np.mean(x[np.concatenate([idx[k] for k in pick])])))
    return [float(np.percentile(ms, 2.5)), float(np.percentile(ms, 97.5))]


def interval_sum_E(B_ci, null_med: float, H_ci) -> list:
    """Prereg §4: [B_lo - null - H_hi, B_hi - null - H_lo]."""
    return [B_ci[0] - null_med - H_ci[1], B_ci[1] - null_med - H_ci[0]]


def label_policy(clears_null: bool, E: float, lo_game: float, lo_day: float, day_fragile: bool,
                 extras_ok: bool = True, b_not_earned: bool = False) -> str:
    """Prereg §5 decision rule."""
    if not (clears_null and E > 0):
        return "NO"
    if lo_game > 0 and lo_day > 0:
        if b_not_earned:
            return "CANDIDATE-B-NOT-EARNED-AT-ENTRY"
        if not extras_ok:
            return "NEAR"
        return "CANDIDATE-FRAGILE" if day_fragile else "CANDIDATE"
    return "NEAR"


def sigma_dist(E: float, ci) -> float | None:
    hw = (ci[1] - ci[0]) / 2
    return round(E / hw, 3) if hw > 0 else None


# ------------------------------------------------------------------ policy (a)
def policy_a(fs: pd.DataFrame, settle: dict, ref: dict) -> dict:
    """Recompute EXP-031's H_a from the archive and gate it against the stored value."""
    oc = outcome_map(settle, fs["ticker"])
    keep = fs[fs["ticker"].isin(oc)]
    p = keep["yes_mid"].to_numpy(float); y = np.array([oc[t] for t in keep["ticker"]])
    h = keep["half_spread"].to_numpy(float)
    B = calib_gap(p, y)[0]; H = float(np.median(h)); nm = ref["null_B_median"]
    gate = {"B_recomputed": round(B, 5), "H_recomputed": round(H, 5), "E_recomputed": round(B - nm - H, 5),
            "B_stored": ref["B"], "H_stored": ref["H"], "E_stored": ref["E"],
            "passed": bool(abs(B - ref["B"]) <= 1e-5 and abs(H - ref["H"]) <= 1e-5 and abs(B - nm - H - ref["E"]) <= 1e-5)}
    ev = keep["event_ticker"].to_numpy(); dy = keep["day_utc"].to_numpy()
    Hg, Hd = boot_median_ci(h, ev), boot_median_ci(h, dy)
    Eg, Ed = interval_sum_E(ref["ci_game"]["B"], nm, Hg), interval_sum_E(ref["ci_day"]["B"], nm, Hd)
    E = ref["B"] - nm - H
    return {"H": H, "E": E, "E_ci_game": Eg, "E_ci_day": Ed, "H_ci_game": Hg, "H_ci_day": Hd, "gate": gate,
            "label": label_policy(ref["clears_null"], E, Eg[0], Ed[0], ref["day_fragile"]),
            "dist_game": sigma_dist(E, Eg), "dist_day": sigma_dist(E, Ed)}


# ------------------------------------------------------------------ policy (b)
def entry_snapshots(g: pd.DataFrame, tcol: str) -> pd.DataFrame:
    """Earliest usable snapshot per (ticker, tau bucket), pregame buckets only (tau >= 0)."""
    u = g[g["usable"] & (g[tcol] >= 0)].copy()
    u["tb"] = tau_bucket(u[tcol])
    u = u.sort_values("run_ts", kind="stable")
    return u.drop_duplicates(["ticker", "tb"], keep="first")


def policy_b(g: pd.DataFrame, settle: dict, ref: dict, tcol: str = "tau_start_h") -> dict:
    oc = outcome_map(settle, g["ticker"].unique())
    ent = entry_snapshots(g, tcol)
    ent = ent[ent["ticker"].isin(oc)]
    if ent.empty:
        return {"measured": False, "reason": "no pregame entry snapshots"}
    dates = sorted(ent["game_date"].dropna().unique())
    ordinal = {d: i for i, d in enumerate(dates)}
    ent = ent.assign(sel=ent["game_date"].map(lambda d: ordinal.get(d, -1) % 2 == 0))
    per_bucket = {}
    for lab in TAU_LABELS[1:]:
        e = ent[ent["tb"] == lab]
        s, v = e[e["sel"]], e[~e["sel"]]
        elig = bool(len(s) >= B_MIN_TICKERS and s["game_date"].nunique() >= B_MIN_DAYS
                    and len(v) >= B_MIN_TICKERS and v["game_date"].nunique() >= B_MIN_DAYS)
        per_bucket[lab] = {"n_sel": int(len(s)), "n_eval": int(len(v)), "days_sel": int(s["game_date"].nunique()),
                           "days_eval": int(v["game_date"].nunique()), "eligible": elig,
                           "hs_med_sel": round(float(s["half_spread"].median()), 5) if len(s) else None,
                           "hs_med_eval": round(float(v["half_spread"].median()), 5) if len(v) else None}
    elig = {k: c for k, c in per_bucket.items() if c["eligible"]}
    if not elig:
        return {"measured": False, "reason": "no pregame bucket meets coverage in both halves", "per_bucket": per_bucket}
    tau_star = min(elig, key=lambda k: elig[k]["hs_med_sel"])
    v = ent[(ent["tb"] == tau_star) & (~ent["sel"])]
    h = v["half_spread"].to_numpy(float); nm = ref["null_B_median"]
    H = float(np.median(h))
    Hg, Hd = boot_median_ci(h, v["event_ticker"].to_numpy()), boot_median_ci(h, v["game_date"].astype(str).to_numpy())
    Eg, Ed = interval_sum_E(ref["ci_game"]["B"], nm, Hg), interval_sum_E(ref["ci_day"]["B"], nm, Hd)
    E = ref["B"] - nm - H
    # B-entry diagnostic: calibration gap at the entry snapshots actually used
    p = v["yes_mid"].to_numpy(float); y = np.array([oc[t] for t in v["ticker"]])
    Be = calib_gap(p, y)[0]
    nullE = _null_B(p, np.random.default_rng(SEED))
    nmE, n995E = float(np.median(nullE)), float(np.percentile(nullE, NULL_Q))
    entry_earned = bool(Be > n995E and Be - nmE - H > 0)
    return {"measured": True, "tau_star": tau_star, "per_bucket": per_bucket, "n_eval_tickers": int(len(v)),
            "H": H, "E": E, "E_ci_game": Eg, "E_ci_day": Ed, "H_ci_game": Hg, "H_ci_day": Hd,
            "B_entry": round(Be, 5), "B_entry_null_median": round(nmE, 5), "B_entry_null_99.5": round(n995E, 5),
            "E_entry": round(Be - nmE - H, 5), "entry_earned": entry_earned,
            "label": label_policy(ref["clears_null"], E, Eg[0], Ed[0], ref["day_fragile"], b_not_earned=not entry_earned),
            "dist_game": sigma_dist(E, Eg), "dist_day": sigma_dist(E, Ed)}


# ------------------------------------------------------------------ policy (c)
def policy_c_fills(g: pd.DataFrame, fs: pd.DataFrame, side: dict, pregame_col: str, pregame_min: float) -> pd.DataFrame:
    """Per first-seen ticker: filled? A fill is evidenced ONLY by a strictly later, pregame snapshot whose
    opposite quote is strictly through the resting price (prereg §3c). Anything else is unfilled."""
    f = fs[["ticker", "run_ts", "yes_mid"]].rename(columns={"run_ts": "t0", "yes_mid": "m"})
    later = g.merge(f, on="ticker")
    later = later[(later["run_ts"] > later["t0"]) & (later[pregame_col] >= pregame_min)]
    later = later.assign(ask_ok=later["yes_ask"].where(later["yes_ask"] > 0))
    agg = later.groupby("ticker").agg(min_ask=("ask_ok", "min"), max_bid=("yes_bid", "max"))
    out = f.set_index("ticker").join(agg)
    out["bucket"] = np.minimum((out["m"] * N_BUCKETS).astype(int), N_BUCKETS - 1)
    out["s"] = out["bucket"].map(side)
    out["fill"] = np.where(out["s"] > 0, out["min_ask"] < out["m"], np.where(out["s"] < 0, out["max_bid"] > out["m"], False))
    out["fill"] = out["fill"].fillna(False).astype(bool)
    return out


def side_signs(p: np.ndarray, y: np.ndarray) -> dict:
    _, _, gap = calib_gap(p, y)
    return {b: int(np.sign(gap[b])) for b in range(N_BUCKETS)}


def policy_c(g: pd.DataFrame, fs: pd.DataFrame, settle: dict, ref: dict, pregame_col: str, pregame_min: float,
             force_fill: bool = False) -> dict:
    oc = outcome_map(settle, fs["ticker"])
    fsk = fs[fs["ticker"].isin(oc)]
    p = fsk["yes_mid"].to_numpy(float); y = np.array([oc[t] for t in fsk["ticker"]])
    side = side_signs(p, y)
    # the bucket table is a given input: signs must agree wherever the stored (rounded) gap is non-zero
    for b, r in enumerate(ref["buckets"]):
        if r["f_minus_p"] != 0 and np.sign(r["f_minus_p"]) != side[b]:
            raise AssertionError(f"side sign disagrees with EXP-031 bucket table at bucket {b}")
    gk = g[g["ticker"].isin(oc)]
    fl = policy_c_fills(gk, fsk, side, pregame_col, pregame_min)
    fl = fl.loc[fsk["ticker"]]
    if force_fill:
        fl["fill"] = True
    yv = np.array([oc[t] for t in fl.index]); sv = fl["s"].to_numpy(float)
    r_i = np.where(fl["fill"].to_numpy(), sv * (yv - fl["m"].to_numpy(float)), 0.0)
    Rc = float(r_i.mean()); nm = ref["null_B_median"]
    out = {"R_c": Rc, "fill_rate": float(fl["fill"].mean()), "n": int(len(fl))}
    if force_fill:
        return out
    ev = fsk.set_index("ticker").loc[fl.index, "event_ticker"].to_numpy()
    dy = fsk.set_index("ticker").loc[fl.index, "day_utc"].to_numpy()
    Rg, Rd = boot_mean_ci(r_i, ev), boot_mean_ci(r_i, dy)
    Eg, Ed = [Rg[0] - nm, Rg[1] - nm], [Rd[0] - nm, Rd[1] - nm]
    E = Rc - nm
    filled = fl["fill"].to_numpy()
    cf = sv * (yv - fl["m"].to_numpy(float))  # what each order would earn if it filled
    out.update({"E": E, "E_ci_game": Eg, "E_ci_day": Ed,
                "mean_edge_filled": float(cf[filled].mean()) if filled.any() else None,
                "mean_edge_unfilled_counterfactual": float(cf[~filled].mean()) if (~filled).any() else None,
                "label": label_policy(ref["clears_null"], E, Eg[0], Ed[0], ref["day_fragile"],
                                      extras_ok=bool(out["fill_rate"] >= FILL_RATE_MIN)),
                "dist_game": sigma_dist(E, Eg), "dist_day": sigma_dist(E, Ed)})
    return out


# ------------------------------------------------------------------ D5: drift + backward placebo
def _slope(x: np.ndarray, d: np.ndarray) -> float:
    xc = x - x.mean()
    den = float((xc ** 2).sum())
    return float((xc * (d - d.mean())).sum() / den) if den > 0 else float("nan")


def _boot_slope(x, d, labels):
    rng = np.random.default_rng(SEED)
    uniq, inv = np.unique(labels, return_inverse=True)
    idx = [np.where(inv == k)[0] for k in range(len(uniq))]
    ss = []
    for _ in range(N_DRAWS // 4):
        pick = rng.integers(0, len(uniq), len(uniq))
        ix = np.concatenate([idx[k] for k in pick])
        ss.append(_slope(x[ix], d[ix]))
    ss = [s for s in ss if s == s]
    return [float(np.percentile(ss, 2.5)), float(np.percentile(ss, 97.5))]


def drift_pairs(g: pd.DataFrame, settle: dict) -> pd.DataFrame:
    u = g[g["usable"]].sort_values("run_ts", kind="stable")
    first = u.drop_duplicates("ticker", keep="first")
    first = first[first["tau_start_h"] >= DRIFT_MIN_FIRST_TAU_H]
    pre = u[u["tau_start_h"] >= 0]
    last = pre.drop_duplicates("ticker", keep="last")
    m = first[["ticker", "t", "yes_mid", "game_date", "event_ticker"]].merge(
        last[["ticker", "t", "yes_mid"]], on="ticker", suffixes=("_f", "_l"))
    m = m[(m["t_l"] - m["t_f"]).dt.total_seconds() / 3600.0 >= DRIFT_MIN_GAP_H]
    return m.rename(columns={"yes_mid_f": "p_first", "yes_mid_l": "p_last"})


def drift_result(pairs: pd.DataFrame, settle: dict, ref: dict) -> dict:
    if len(pairs) < DRIFT_MIN_TICKERS or pairs["game_date"].nunique() < DRIFT_MIN_DAYS:
        return {"measured": False, "n": int(len(pairs))}
    pf, pl = pairs["p_first"].to_numpy(float), pairs["p_last"].to_numpy(float)
    dts = pairs["game_date"].astype(str).to_numpy()
    D = pl - pf
    sf = _slope(pf - 0.5, D); sci = _boot_slope(pf - 0.5, D, dts)
    sb = _slope(pl - 0.5, -D); sbci = _boot_slope(pl - 0.5, -D, dts)
    ratio = abs(sb) / abs(sf) if sf else float("inf")
    survives = bool(ratio < 0.5 or (sbci[0] <= 0 <= sbci[1]))
    sgn = {b: int(np.sign(r["f_minus_p"])) for b, r in enumerate(ref["buckets"])}
    bf = np.minimum((pf * N_BUCKETS).astype(int), N_BUCKETS - 1)
    bl = np.minimum((pl * N_BUCKETS).astype(int), N_BUCKETS - 1)
    clv = np.array([sgn[b] for b in bf]) * D
    clv_b = np.array([sgn[b] for b in bl]) * (-D)
    cells = {}
    for b in range(N_BUCKETS):
        sel = bf == b
        n, nd = int(sel.sum()), int(pd.Series(dts[sel]).nunique()) if sel.any() else 0
        c = {"n": n, "days": nd, "measured": bool(n >= DRIFT_MIN_TICKERS and nd >= DRIFT_MIN_DAYS)}
        if c["measured"]:
            c.update({"mean_drift": round(float(D[sel].mean()), 5),
                      "ci_day": [round(x, 5) for x in boot_mean_ci(D[sel], dts[sel])]})
        cells[f"{b/N_BUCKETS:.1f}"] = c
    return {"measured": True, "n": int(len(pairs)), "days": int(pairs["game_date"].nunique()),
            "forward_slope": round(sf, 5), "forward_slope_ci_day": [round(x, 5) for x in sci],
            "backward_slope": round(sb, 5), "backward_slope_ci_day": [round(x, 5) for x in sbci],
            "placebo_ratio": round(float(ratio), 3), "survives_T569_rule": survives,
            "mean_drift": round(float(D.mean()), 5),
            "clv_forward_mean": round(float(clv.mean()), 5), "clv_forward_ci_day": [round(x, 5) for x in boot_mean_ci(clv, dts)],
            "clv_backward_mean": round(float(clv_b.mean()), 5), "cells": cells}


# ------------------------------------------------------------------ D4: capacity
def capacity(depth: pd.DataFrame, family: str, window_tickers=None) -> dict:
    d = depth[depth["series_ticker"] == family]
    if window_tickers is not None:
        d = d[d["ticker"].isin(window_tickers)]
    d = d[d["usable"].astype(bool)]
    out = {"rows": int(len(d)), "tickers": int(d["ticker"].nunique()), "stakes": {}}
    enough = bool(len(d) >= DEPTH_MIN_ROWS and out["tickers"] >= DEPTH_MIN_TICKERS)
    q25 = float(d["within_5c_usd_min_side"].quantile(.25)) if len(d) else None
    out["within_5c_usd_min_side_p25"] = q25
    for s in STAKES:
        out["stakes"][str(s)] = bool(enough and q25 is not None and q25 >= DEPTH_COVER * s)
    out["sample_sufficient"] = enough
    return out


def load_depth(archive_dir: str) -> pd.DataFrame:
    parts = [pd.read_json(p, lines=True, dtype=False) for p in sorted(glob.glob(os.path.join(archive_dir, "depth_*.jsonl")))]
    d = pd.concat(parts, ignore_index=True)
    d["within_5c_usd_min_side"] = pd.to_numeric(d["within_5c_usd_min_side"], errors="coerce")
    return d


# ------------------------------------------------------------------ driver
def _jsonable(o):
    if isinstance(o, dict):
        return {str(k): _jsonable(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [_jsonable(v) for v in o]
    if isinstance(o, (np.floating,)):
        return float(o)
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.bool_,)):
        return bool(o)
    return o


def run(archive_dir: str, exp031_dir: str, out_dir: str, cache: str | None = None) -> dict:
    ref_all = json.load(open(os.path.join(exp031_dir, "d3_d4_results.json")))["families"]
    settle = load_settlements(os.path.join(exp031_dir, "settlements"))
    if cache and os.path.exists(cache):
        df = pd.read_pickle(cache)
    else:
        df = enrich(load_archive(archive_dir), settle)
        if cache:
            df.to_pickle(cache)
    gates = clock_gate(df)
    res = {"clock_gate": gates, "families": {}}
    for fam, ref in ref_all.items():
        g = df[df["series_ticker"] == fam]
        is_mlb = fam.startswith("KXMLB")
        use_start = bool(is_mlb and gates.get(fam, {}).get("passed"))
        fs = first_seen(g)
        r = {"surface": surface_for_family(g, use_start), "use_tau_start": use_start}
        r["policy_a"] = policy_a(fs, settle, ref)
        if use_start:
            r["policy_b"] = policy_b(g, settle, ref)
            r["policy_c"] = policy_c(g, fs, settle, ref, "tau_start_h", 0.0)
            r["policy_c_forcefill_gate"] = policy_c(g, fs, settle, ref, "tau_start_h", 0.0, force_fill=True)
            r["policy_c_forcefill_gate"]["B_stored"] = ref["B"]
            r["policy_c_forcefill_gate"]["passed"] = bool(abs(r["policy_c_forcefill_gate"]["R_c"] - ref["B"]) <= 1e-5)
            r["drift"] = drift_result(drift_pairs(g, settle), settle, ref)
        else:
            r["policy_b"] = {"measured": False, "reason": "no pregame clock (NFL tickers carry no start time or clock gate failed)"}
            c = policy_c(g, fs, settle, ref, "tau_close_h", 0.0)
            c["caveat"] = "no start time: 'pregame' = before market close, so fills may be in-play; not pregame-clean"
            r["policy_c"] = c
            fg = policy_c(g, fs, settle, ref, "tau_close_h", 0.0, force_fill=True)
            fg["B_stored"] = ref["B"]; fg["passed"] = bool(abs(fg["R_c"] - ref["B"]) <= 1e-5)
            r["policy_c_forcefill_gate"] = fg
            r["drift"] = {"measured": False, "reason": "no start time"}
        r["ref"] = {k: ref[k] for k in ("B", "H", "E", "null_B_median", "null_B_99.5", "clears_null", "day_fragile",
                                         "ci_game", "ci_day", "vig_median", "included_settled_tickers")}
        res["families"][fam] = r
    os.makedirs(out_dir, exist_ok=True)
    json.dump(_jsonable(res), open(os.path.join(out_dir, "results.json"), "w"), indent=1)
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--archive", default="exp_output/PRICE_ARCHIVE")
    ap.add_argument("--exp031", default="exp_output/EXP-031-MKT-EFF-SURVEY")
    ap.add_argument("--out", default="exp_output/EXP-032-EXECUTION-COST-SURFACE")
    ap.add_argument("--cache", default=None, help="optional pickle cache of the enriched archive (dev speed-up)")
    a = ap.parse_args()
    run(a.archive, a.exp031, a.out, a.cache)
    print("wrote", os.path.join(a.out, "results.json"))


if __name__ == "__main__":
    main()
