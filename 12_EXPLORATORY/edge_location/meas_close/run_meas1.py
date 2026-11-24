"""W124.2 H-MEAS-1, as frozen in PREREG.md (+ A1). usage: run_meas1.py <archive_dir> <cache_dir> <orders.jsonl> -> results.json, tables.md beside this file.
Read-only on the archive, the settled cache (fetch_settled.py), the milestone starts (fetch_starts.py) and the order log."""
import calendar, json, math, os, sys, time
from collections import defaultdict
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "h1_attention"))
sys.path.insert(0, os.path.join(HERE, "..", ".."))
sys.path.insert(0, os.path.join(HERE, "..", "..", "..", "src"))
import run_h1 as H1  # noqa: E402  (taxonomy, bucket edges, fee)
from _fence import safe_out  # noqa: E402
from prediction_market_bot import io_jsonl  # noqa: E402

SPLIT = {"NHL": "2026-11-12", "NBA": "2026-11-11", "MLB": "2026-09-25", "NFL": "2026-10-25"}
FWD = calendar.timegm(time.strptime("2026-11-20T20:00:00Z", "%Y-%m-%dT%H:%M:%SZ"))
B, LEVEL, SEED, MAXSP, CLOSE_H = 2000, 0.90, 20261124, 0.10, 2.0
_E = {}


def ep(s):
    if s not in _E:
        _E[s] = calendar.timegm(time.strptime(s[:19] + "Z", "%Y-%m-%dT%H:%M:%SZ"))
    return _E[s]


def qual(r):
    try:
        b, a, nb, na = float(r["yes_bid"]), float(r["yes_ask"]), float(r["no_bid"]), float(r["no_ask"])
    except Exception:
        return None
    if b <= 0 or a <= b or a - b > MAXSP + 1e-9 or a >= 1:
        return None
    m = (a + b) / 2
    return (m, a) if 0.02 <= m <= 0.98 else None


def scan(archive, starts):
    close, e6, e24 = {}, {}, {}  # ticker -> (dt_s, mid, ask, run_ts); e*: (abs distance to target, mid)
    for f in io_jsonl.glob_files(f"{archive}/prices_*.jsonl"):
        for l in io_jsonl.open_jsonl(f):
            try:
                r = json.loads(l)
            except Exception:
                continue
            st = starts.get(r.get("event_ticker"))
            if st is None:
                continue
            q = qual(r)
            if q is None:
                continue
            dt = ep(st) - ep(r["run_ts"])
            if dt < 0:
                continue
            t = r["ticker"]
            if dt <= CLOSE_H * 3600 and (t not in close or dt < close[t][0]):
                close[t] = (dt, q[0], q[1], r["event_ticker"])
            for tab, lo, hi, tgt in ((e6, 5, 7, 6), (e24, 22, 26, 24)):
                if lo * 3600 <= dt <= hi * 3600:
                    d = abs(dt - tgt * 3600)
                    if t not in tab or d < tab[t][0]:
                        tab[t] = (d, q[0])
    return close, e6, e24


def build(close, e6, e24, settled, starts, drops):
    by_ev = defaultdict(list)
    for t, (dt, mid, ask, ev) in close.items():
        if t not in settled:
            drops["no_settled_result_or_void"] += 1
            continue
        by_ev[ev].append(t)
    rows = []
    for ev, ts in by_ev.items():
        ser = ev.split("-")[0]
        sp, typ = H1.split_series(ser)
        if sp is None:
            continue
        d, _ = H1.game_cut(ev)
        if d is None:
            drops["no_ticker_date"] += len(ts)
            continue
        st = ep(starts[ev])
        main = min(ts, key=lambda t: (abs(close[t][1] - 0.5), t)) if typ in ("SPREAD", "TOTAL") else None
        for t in ts:
            dt, mid, ask, _ = close[t]
            if typ == "GAME":
                fam = "moneyline"
            elif typ in ("SPREAD", "TOTAL"):
                fam = ("spread" if typ == "SPREAD" else "total") + ("_main" if t == main else "_alt")
            elif typ == "TEAMTOTAL":
                fam = "team_total"
            elif typ in H1.PERIOD:
                fam = "period_" + typ.lower()
            else:
                fam = "prop_" + typ.lower()
            pop = "early" if d < SPLIT[sp] else ("late" if st > FWD else "w123_heldout")
            rows.append(dict(t=t, sport=sp, fam=fam, game=ev.split("-", 1)[1][:13], pop=pop, c=mid, y=settled[t],
                             cost=(ask - mid) + H1.fee(ask), e6=e6.get(t, (0, None))[1], e24=e24.get(t, (0, None))[1]))
    return rows


def game_sums(rows, fn, k):
    g = {}
    for r in rows:
        v = fn(r)
        a = g.setdefault(r["game"], np.zeros(k))
        a += v
    return np.array(list(g.values()))


def boot_idx(G, rng):
    return rng.integers(0, G, size=(B, G))


def slope_from(S):  # S columns: n, sx, sy, sxx, sxy
    n = S[..., 0]
    mx, my = S[..., 1] / n, S[..., 2] / n
    vx = S[..., 3] / n - mx ** 2
    b = (S[..., 4] / n - mx * my) / np.where(vx > 1e-12, vx, np.nan)
    return b, my - b * mx


def ci(x):
    return [float(np.nanpercentile(x, 100 * (1 - LEVEL) / 2)), float(np.nanpercentile(x, 100 * (1 + LEVEL) / 2))]


def groups_for(counts):
    """merge buckets with < 20 markets toward 0.5 (PREREG rule 2)."""
    g = list(range(6))
    cnt = list(counts)
    nb = {0: 1, 1: 2, 2: 3, 3: 2, 4: 3, 5: 4}
    for _ in range(12):
        small = [i for i in range(6) if 0 < sum(c for j, c in enumerate(cnt) if g[j] == i) < 20 and any(g[j] == i for j in range(6))]
        tot = lambda i: sum(c for j, c in enumerate(cnt) if g[j] == i)
        small = [i for i in sorted(set(g)) if tot(i) < 20]
        if not small:
            break
        i = small[0]
        tgt = g[nb[min(j for j in range(6) if g[j] == i)]]
        if tgt == i:
            tgt = next((x for x in sorted(set(g)) if x != i), i)
            if tgt == i:
                break
        g = [tgt if x == i else x for x in g]
    return g


def family_stats(rows, rng, with_extras=True):
    rows = [r for r in rows]
    G = len({r["game"] for r in rows})
    out = {"markets": len(rows), "games": G}
    if G < 2:
        return out
    cm = lambda r: np.array([1, r["c"], r["y"], r["c"] ** 2, r["c"] * r["y"]])
    S = game_sums(rows, cm, 5)
    idx = boot_idx(len(S), rng)
    b0, a0 = slope_from(S.sum(0))
    bb, aa = slope_from(S[idx].sum(1))
    out |= dict(slope=float(b0), intercept=float(a0), slope_ci=ci(bb), intercept_ci=ci(aa), slope_contains_1=bool(ci(bb)[0] <= 1 <= ci(bb)[1]))
    # buckets
    bk = lambda r: H1.bucket(r["c"])
    cnt = [sum(1 for r in rows if bk(r) == i) for i in range(6)]
    grp = groups_for(cnt)
    def bv(r):
        v = np.zeros(18)
        i = bk(r)
        if i is None:
            return v
        j = grp[i]
        v[3 * j: 3 * j + 3] = (1, r["y"], r["c"])
        return v
    BS = game_sums(rows, bv, 18).reshape(-1, 6, 3)
    tot = BS.sum(0)
    keys = [j for j in sorted(set(grp)) if tot[j, 0] > 0]
    gap = {j: tot[j, 1] / tot[j, 0] - tot[j, 2] / tot[j, 0] for j in keys}
    bsum = BS[idx].sum(1)  # (B,6,3)
    se = {j: float(np.std(bsum[:, j, 1] / np.maximum(bsum[:, j, 0], 1) - bsum[:, j, 2] / np.maximum(bsum[:, j, 0], 1))) for j in keys}
    w = {j: tot[j, 0] for j in keys}
    W = sum(w.values())
    mean_abs = sum(w[j] * abs(gap[j]) for j in keys) / W
    floor = 0.798 * sum(w[j] * se[j] for j in keys) / W
    cost = float(np.mean([r["cost"] for r in rows]))
    out |= dict(round_cost=cost, half_cost=cost / 2, mean_abs_gap=float(mean_abs), noise_floor=float(floor), debiased_gap=float(max(mean_abs - floor, 0)),
                cond_B=bool(mean_abs < cost / 2),
                buckets=[dict(bucket=H1.BUCKETS[min(j for j in range(6) if grp[j] == k)] if True else None, merged=[j for j in range(6) if grp[j] == k],
                              n=int(w[k]), settled=float(tot[k, 1] / tot[k, 0]), mean_c=float(tot[k, 2] / tot[k, 0]), gap=float(gap[k]), se=se[k]) for k in keys])
    lo = [k for k in keys if min(j for j in range(6) if grp[j] == k) <= 1]
    hi = [k for k in keys if max(j for j in range(6) if grp[j] == k) >= 4]
    if lo and hi:
        out["flb"] = float(np.mean([gap[k] for k in lo]) - np.mean([gap[k] for k in hi]))
    # variance ratio
    for name, key in (("6h", "e6"), ("24h", "e24")):
        sub = [r for r in rows if r[key] is not None]
        if len({r["game"] for r in sub}) >= 10:
            V = game_sums(sub, lambda r: np.array([1, r["y"] - r[key], (r["y"] - r[key]) ** 2, r["c"] - r[key], (r["c"] - r[key]) ** 2]), 5)
            def ratio(T):
                n = T[..., 0]
                vu = T[..., 2] / n - (T[..., 1] / n) ** 2
                vv = T[..., 4] / n - (T[..., 3] / n) ** 2
                return vu / np.where(vv > 1e-12, vv, np.nan)
            vi = boot_idx(len(V), rng)
            out["varratio_" + name] = dict(ratio=float(ratio(V.sum(0))), ci=ci(ratio(V[vi].sum(1))), n=len(sub), games=len(V),
                                           sd_settle=float(math.sqrt(max(V.sum(0)[2] / V.sum(0)[0] - (V.sum(0)[1] / V.sum(0)[0]) ** 2, 0))),
                                           sd_clv=float(math.sqrt(max(V.sum(0)[4] / V.sum(0)[0] - (V.sum(0)[3] / V.sum(0)[0]) ** 2, 0))))
    return out


def verdict(rows, rng):
    st = family_stats(rows, rng)
    mk, G = st["markets"], st["games"]
    if G < 30 or mk < 200:
        mpg = mk / max(G, 1)
        need = max(30, math.ceil(200 / max(mpg, 1e-9))) - G
        return st | dict(verdict="UNDERPOWERED", games_needed=int(need))
    # stability
    stab = None
    pe = [r for r in rows if r["pop"] == "early"]
    pl = [r for r in rows if r["pop"] == "late"]
    if len({r["game"] for r in pe}) >= 30 and len({r["game"] for r in pl}) >= 30:
        se_, sl = family_stats(pe, rng, False), family_stats(pl, rng, False)
        ex = lambda s: not s["slope_contains_1"]
        flip = ex(se_) and ex(sl) and ((se_["slope"] - 1) * (sl["slope"] - 1) < 0)
        stab = dict(early_slope=se_["slope"], early_ci=se_["slope_ci"], late_slope=sl["slope"], late_ci=sl["slope_ci"], flip=bool(flip))
    st["stability"] = stab
    ok = st["slope_contains_1"] and st["cond_B"] and not (stab and stab["flip"])
    if ok:
        return st | dict(verdict="LICENSED")
    tag = "miscalibrated"
    if st["slope_contains_1"] and not st["cond_B"] and st["debiased_gap"] < st["half_cost"]:
        tag = "noise_limited"
        st["games_needed_for_floor"] = int(math.ceil(G * (st["noise_floor"] / st["half_cost"]) ** 2)) - G if st["noise_floor"] > st["half_cost"] else 0
    return st | dict(verdict="NOT LICENSED", tag=tag)


def orders(path, close, settled, starts, rng):
    rows, pre_no = [], 0
    for l in open(path):
        if '"event": "arm_order"' not in l:
            continue
        o = json.loads(l)
        t = o["ticker"]
        if t not in close or t not in settled or o.get("side") not in ("yes", "no"):
            continue
        if o["side"] == "no" and str(o.get("ts", ""))[:19] < "2026-11-06T01:03:42":  # GG-1771/GG-1784 data epoch: pre-epoch NO-side is mirror-priced
            pre_no += 1
            continue
        mid = close[t][1]
        own = mid if o["side"] == "yes" else 1 - mid
        yside = settled[t] if o["side"] == "yes" else 1 - settled[t]
        e = float(o["entry_price"])
        rows.append(dict(game=o["event_ticker"].split("-", 1)[1][:13], clv=own - e, gross=yside - e, arm=o.get("arm")))
    if not rows:
        return dict(orders=0, verdict="UNDERPOWERED")
    S = game_sums(rows, lambda r: np.array([1, r["clv"], r["gross"], r["clv"] ** 2, r["clv"] * r["gross"]]), 5)
    idx = boot_idx(len(S), rng)
    b0, a0 = slope_from(S.sum(0))
    bb, _ = slope_from(S[idx].sum(1))
    D = game_sums(rows, lambda r: np.array([1, r["gross"] - r["clv"]]), 2)
    dm = D[idx].sum(1)
    dd = dm[:, 1] / dm[:, 0]
    o = dict(excluded_pre_epoch_no=pre_no, orders=len(rows), games=len(S), slope=float(b0), intercept=float(a0), slope_ci=ci(bb), mean_clv=float(np.mean([r["clv"] for r in rows])),
             mean_gross=float(np.mean([r["gross"] for r in rows])), gap_mean=float(D.sum(0)[1] / D.sum(0)[0]), gap_ci=ci(dd),
             sd_clv=float(np.std([r["clv"] for r in rows])), sd_gross=float(np.std([r["gross"] for r in rows])))
    o["verdict"] = "UNDERPOWERED" if len(S) < 30 else ("PASS" if o["slope_ci"][0] <= 1 <= o["slope_ci"][1] else "FAIL")
    by = {}
    for a in sorted({r["arm"] for r in rows}):
        sub = [r for r in rows if r["arm"] == a]
        by[a] = dict(n=len(sub), games=len({r["game"] for r in sub}), mean_clv=float(np.mean([r["clv"] for r in sub])), mean_gross=float(np.mean([r["gross"] for r in sub])))
    return o | dict(by_arm=by)


def main(archive, cache, orders_path):
    starts = json.load(open(f"{cache}/starts.json"))
    settled = {}
    for f in os.listdir(f"{cache}/settled"):
        for m in json.load(open(f"{cache}/settled/{f}")):
            if m["result"] in ("yes", "no"):
                settled[m["ticker"]] = 1.0 if m["result"] == "yes" else 0.0
    close, e6, e24 = scan(archive, starts)
    drops = defaultdict(int)
    rows = build(close, e6, e24, settled, starts, drops)
    res = dict(drops=dict(drops), n_starts=len(starts), n_settled=len(settled), n_close=len(close), n_rows=len(rows), families={}, descriptive_w123_heldout={})
    # coverage: markets in settled+archive with no milestone start are not observable here; reported via the archive tickers below
    rng = np.random.default_rng(SEED)
    fams = sorted({(r["sport"], r["fam"]) for r in rows})
    for sp, fam in fams:
        v = [r for r in rows if r["sport"] == sp and r["fam"] == fam and r["pop"] in ("early", "late")]
        h = [r for r in rows if r["sport"] == sp and r["fam"] == fam and r["pop"] == "w123_heldout"]
        res["families"][f"{sp}|{fam}"] = verdict(v, rng) if v else dict(markets=0, verdict="UNDERPOWERED")
        if len({r["game"] for r in h}) >= 5:
            res["descriptive_w123_heldout"][f"{sp}|{fam}"] = family_stats(h, rng, False)
    res["orders"] = orders(orders_path, close, settled, starts, rng)
    json.dump(res, open(safe_out(os.path.join(HERE, "results.json")), "w"), indent=1, default=float)
    print(json.dumps({k: v for k, v in res.items() if k not in ("families", "descriptive_w123_heldout")}, default=float)[:1500])


if __name__ == "__main__":
    main(*sys.argv[1:4])
