#!/usr/bin/env python3
"""EXP-035 D2 diagnosis (T-605). READ-ONLY on the store, the archive and EXP-031/032. Part 1's verdict is not
altered by anything here and no number here validates candles. Writes diag_d2.json.

  (a) classify every Part 1 G2/G3-failing snapshot (i)-(iv) [+ (v) unresolvable in-window]
  (b) per-ticker candle first-seen minus archive first-seen; B and H recomputed at the archive's first-seen (DIAGNOSTIC)
"""
from __future__ import annotations

import glob
import json
import os
import sys
from collections import Counter

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import board_survey_sports_gate as g  # noqa: E402
import board_survey_sports_store as bs  # noqa: E402
from market_efficiency_survey import calib_gap  # noqa: E402

TOL = 0.01 + 1e-9


def load(store_dir, exp031):
    stores = [bs.Store(d) for d in [store_dir] + sorted(glob.glob(os.path.join(store_dir, "shard_*")))]
    hourly, minute = {}, {}
    for s in stores:
        for r in s.rows():
            if r["kind"] != "candles":
                continue
            t, per, a, b = r["key"].split("|")
            cs = r["payload"].get("candlesticks") or []
            if per == "60":
                hourly[t] = cs
            else:
                minute.setdefault(t, {})[(int(a), int(b))] = cs
    settle = {}
    for f in glob.glob(os.path.join(exp031, "settlements", "*.json")):
        settle.update(json.load(open(f)))
    return hourly, minute, settle


def quote(c):
    return g.q(c.get("yes_bid"), "close"), g.q(c.get("yes_ask"), "close")


def placeholder(c):
    """Empty-book placeholder: a missing side printed as 0 bid or 1.00 ask (or non-positive ask)."""
    b, a = quote(c)
    return b is None or a is None or b <= 0 or a <= 0 or a >= 1.0


def resolve_i(run, hcs, tt):
    """No 1-minute candle in [t-120s, t+120s] => the quote did not change in that window. The hourly candle covering t
    brackets it: constant hour (open=high=low=close on both sides) => prevailing is exactly known; archive quote outside
    [low, high] => disagrees whatever the in-hour path was; otherwise unresolvable from stored data."""
    cov = [c for c in sorted(hcs, key=lambda c: c["end_period_ts"]) if tt < c["end_period_ts"] <= tt + 3600]
    if not cov:
        return "no_covering_hourly"
    c = cov[0]; n = g.norm_candle(c)
    bid, ask = n["yes_bid"], n["yes_ask"]
    if None in (*bid.values(), *ask.values()):
        return "hourly_has_null_fields"
    if bid["low"] - 1e-9 > run[1] or run[1] > bid["high"] + 1e-9 or ask["low"] - 1e-9 > run[2] or run[2] > ask["high"] + 1e-9:
        return "archive_quote_outside_hourly_low_high"
    if len({*bid.values()}) == 1 and len({*ask.values()}) == 1:
        return "constant_hour_prevailing_agrees" if agrees(run, c) else "constant_hour_prevailing_disagrees"
    return "unresolvable_within_hourly_range"


def agrees(run, c):
    b, a = quote(c)
    return b is not None and a is not None and abs(run[1] - b) <= TOL and abs(run[2] - a) <= TOL


def part_a(snaps, minute, hourly):
    cls, rows = Counter(), []
    for t, wins in minute.items():
        for (s0, e0), cs in wins.items():
            tt = (s0 + e0) // 2
            run = next(r for r in snaps[t] if abs(g.ts(r[0]) - tt) <= 1)
            cs = sorted(cs, key=lambda c: c["end_period_ts"])
            idx, _ = g.part1_match(cs, tt)
            prev = [c for c in cs if c["end_period_ts"] <= tt]
            prev = prev[-1] if prev else None
            matched = cs[idx] if idx is not None else None
            p1_ok = matched is not None and agrees(run, matched)
            prev_ok = prev is not None and agrees(run, prev)
            if p1_ok:
                k = "PASS_part1"
            elif not cs:
                k = "i_no_candle_in_window/" + resolve_i(run, hourly.get(t, []), tt)
            elif matched is not None and placeholder(matched):
                k = "iii_empty_book_placeholder_matched"
            elif prev is not None and placeholder(prev) and not prev_ok:
                k = "iii_empty_book_placeholder_prevailing"
            elif prev_ok:
                k = ("ii_matched_is_later_change_prevailing_agrees" if matched is not None
                     else "ii_no_candle_at_or_after_t_prevailing_agrees")
            elif prev is not None:
                k = "iv_prevailing_also_disagrees"
            else:
                k = "v_no_candle_at_or_before_t_in_window"
            cls[k] += 1
            rows.append({"t": t, "tt": tt, "class": k, "prev_agrees": prev_ok, "part1_agrees": p1_ok,
                         "matched_lag_s": (matched["end_period_ts"] - tt) if matched else None})
    return cls, rows


def part_b(snaps, hourly, settle):
    w0 = g.ts(g.WINDOW_START)
    first_arch = {t: v[0] for t, v in snaps.items()}      # (run_ts, bid, ask): first usable archive row
    lags, P = [], {"archive": ([], [], []), "archive_same_subset_as_prevailing": ([], [], []), "candle_first_usable": ([], [], []), "prevailing_hourly_at_t0": ([], [], []),
                   "next_hourly_at_t0": ([], [], [])}
    unavailable = Counter()
    for t in g.binary_settled(snaps, settle):
        y = 1.0 if settle[t]["result"] == "yes" else 0.0
        r0 = first_arch[t]; t0 = g.ts(r0[0])
        cs = sorted(hourly.get(t, []), key=lambda c: c["end_period_ts"])
        usable = [c for c in cs if c["end_period_ts"] >= w0 and (quote(c)[0] or 0) > 0 and (quote(c)[1] or 0) > 0]
        def add(name, b, a):
            P[name][0].append((a + b) / 2); P[name][1].append((a - b) / 2); P[name][2].append(y)
        add("archive", r0[1], r0[2])
        if usable:
            c = usable[0]; b, a = quote(c); add("candle_first_usable", b, a)
            lags.append(c["end_period_ts"] - t0)
        else:
            unavailable["no_usable_hourly"] += 1
        pv = [c for c in cs if c["end_period_ts"] <= t0]
        pv = pv[-1] if pv else None
        if pv is not None and (quote(pv)[0] or 0) > 0 and (quote(pv)[1] or 0) > 0:
            add("prevailing_hourly_at_t0", *quote(pv))
            add("archive_same_subset_as_prevailing", r0[1], r0[2])
        else:
            unavailable["no_usable_hourly_at_or_before_t0"] += 1
        nx = next((c for c in cs if c["end_period_ts"] >= t0 and (quote(c)[0] or 0) > 0 and (quote(c)[1] or 0) > 0), None)
        if nx is not None:
            add("next_hourly_at_t0", *quote(nx))
        else:
            unavailable["no_usable_hourly_at_or_after_t0"] += 1
    out = {}
    for k, (p, h, y) in P.items():
        p, h, y = np.array(p), np.array(h), np.array(y)
        out[k] = {"n": int(len(p)), "B": float(calib_gap(p, y)[0]), "H_median": float(np.median(h))}
    la = np.array(lags, float) / 60.0
    q = lambda x: float(np.percentile(la, x))
    dist = {"n": int(len(la)), "unit": "minutes (candle end_period_ts - archive first run_ts)", "min": float(la.min()),
            "p05": q(5), "p25": q(25), "p50": q(50), "p75": q(75), "p95": q(95), "max": float(la.max()),
            "share_within_60min": float((np.abs(la) <= 60).mean()), "share_negative": float((la < 0).mean()),
            "share_over_6h": float((la > 360).mean()), "share_over_24h": float((la > 1440).mean())}
    return {"lag_distribution": dist, "recomputed_DIAGNOSTIC": out, "unavailable": dict(unavailable)}


if __name__ == "__main__":
    archive, store, exp031, out = sys.argv[1:5]
    hourly, minute, settle = load(store, exp031)
    snaps = g.archive_snaps(archive)
    cls, rows = part_a(snaps, minute, hourly)
    n = sum(cls.values()); fails = n - cls.get("PASS_part1", 0)
    res = {"a": {"n_snapshots": n, "n_pass_part1_g2": cls.get("PASS_part1", 0), "n_fail": fails,
                 "counts": dict(cls),
                 "share_of_failures": {k: v / fails for k, v in cls.items() if k != "PASS_part1"},
                 "share_of_all": {k: v / n for k, v in cls.items()},
                 "prevailing_agrees_all": sum(r["prev_agrees"] for r in rows) / n,
                 "matched_lag_s_pctiles": [float(x) for x in np.percentile([r["matched_lag_s"] for r in rows
                                           if r["matched_lag_s"] is not None], [5, 25, 50, 75, 95])]},
           "b": part_b(snaps, hourly, settle)}
    # bounds on the EXP-034 (prevailing) rule's G2 share: agree / disagree / unresolved from stored data
    agree = dis = unres = 0
    for r in rows:
        c = r["class"]
        if r["prev_agrees"] or c.endswith("constant_hour_prevailing_agrees"):
            agree += 1
        elif c.startswith("iv_") or c.startswith("iii_") or c.endswith(("constant_hour_prevailing_disagrees", "outside_hourly_low_high")):
            dis += 1
        elif c.startswith("PASS_part1"):
            dis += 1            # part1 matched a candle that agrees, but the prevailing close (exists, in-window) does not
        else:
            unres += 1
    res["a"]["prevailing_rule_g2_bounds"] = {"agree": agree, "disagree": dis, "unresolved": unres, "n": n,
                                             "lower": agree / n, "upper": (agree + unres) / n}
    json.dump(res, open(out, "w"), indent=1)
    print(json.dumps(res, indent=1))
