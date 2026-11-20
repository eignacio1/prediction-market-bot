"""W123.1 H1 attention test, as frozen in HYPOTHESIS.md section 3 + Addendum A1 (section 8).
usage: run_h1.py <archive_dir> <settled_dir> -> writes results.json beside this file.
Read-only on the archive and on the settled-results cache (fetch_settled.py)."""
import glob, gzip, json, math, os, re, sys
from collections import defaultdict
import numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "src"))
from _fence import safe_out  # noqa: E402
from prediction_market_bot import io_jsonl  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
MON = {m: i + 1 for i, m in enumerate("JAN FEB MAR APR MAY JUN JUL AUG SEP OCT NOV DEC".split())}
BUCKETS = [(.02, .10), (.10, .25), (.25, .50), (.50, .75), (.75, .90), (.90, .98001)]
PROPS = {"PTS", "REB", "AST", "3PT", "PRA", "STL", "2D", "3D", "PASSYDS", "PASSTDS", "PASSATT", "PASSCOMP", "RSHYDS", "RSHATT", "RECYDS",
         "REC", "RRYDS", "TD", "GOAL", "AST", "LAST", "HIT"}
PERIOD = {"F3", "F5", "F7", "F5SPREAD", "F5TOTAL"}


def split_series(s):
    for sp in ("NBA", "NFL", "NHL", "MLB"):
        if s.startswith("KX" + sp):
            return sp, s[5:]
    return None, None


def game_cut(event):
    m = re.search(r"-(\d\d)([A-Z]{3})(\d\d)", event)
    if not m or m.group(2) not in MON:
        return None, None
    d = f"20{m.group(1)}-{MON[m.group(2)]:02d}-{m.group(3)}"
    return d, d + "T15:00:00Z"


def load_archive(archive):
    """ticker -> dict(last snapshot <= cut; snapshot nearest cut-24h). Streams every price file."""
    import datetime as dt
    best, near, anyk = {}, {}, {}
    for f in io_jsonl.glob_files(f"{archive}/prices_*.jsonl"):
        for l in io_jsonl.open_jsonl(f):
            try:
                r = json.loads(l)
            except Exception:
                continue
            t = r["ticker"]
            sp, typ = split_series(r["series_ticker"])
            if sp is None:
                continue
            d, cut = game_cut(r["event_ticker"])
            if t not in anyk or r["run_ts"] < anyk[t][0]:
                anyk[t] = (r["run_ts"], r["series_ticker"], r["event_ticker"], cut)
            if cut is None or r["run_ts"] > cut:
                continue
            if t not in best or r["run_ts"] >= best[t]["run_ts"]:
                best[t] = r | {"_d": d, "_cut": cut}
            tgt = (dt.datetime.strptime(cut, "%Y-%m-%dT%H:%M:%SZ") - dt.timedelta(hours=24)).strftime("%Y-%m-%dT%H:%M:%SZ")
            gap = abs((dt.datetime.strptime(r["run_ts"], "%Y-%m-%dT%H:%M:%SZ") - dt.datetime.strptime(tgt, "%Y-%m-%dT%H:%M:%SZ")).total_seconds())
            if gap <= 3 * 3600 and (t not in near or gap < near[t][0]):
                near[t] = (gap, r | {"_d": d, "_cut": cut})
    return best, {t: v[1] for t, v in near.items()}, anyk


def usable(r):
    try:
        b, a, nb, na = float(r["yes_bid"]), float(r["yes_ask"]), float(r["no_bid"]), float(r["no_ask"])
    except Exception:
        return None
    if min(b, a, nb, na) <= 0 or a >= 1 or na >= 1:
        return None
    mid = (b + a) / 2
    if not (0.02 <= mid <= 0.98):
        return None
    return b, a, nb, na, mid


def fee(p):
    return 0.07 * p * (1 - p)


def bucket(mid):
    for i, (lo, hi) in enumerate(BUCKETS):
        if lo <= mid < hi:
            return i


def build_rows(snap, res):
    rows, drops = [], defaultdict(int)
    by_ev = defaultdict(list)
    for t, r in snap.items():
        sp, typ = split_series(r["series_ticker"])
        if res.get(t) not in ("yes", "no"):
            drops["no_settled_result"] += 1
            continue
        u = usable(r)
        if u is None:
            drops["unusable_quote"] += 1
            continue
        b, a, nb, na, mid = u
        by_ev[(r["event_ticker"], r["series_ticker"])].append((t, r, u))
    for (ev, ser), lst in by_ev.items():
        sp, typ = split_series(ser)
        main = None
        if typ in ("SPREAD", "TOTAL"):
            main = min(lst, key=lambda x: (abs(x[2][4] - 0.5), x[0]))[0]
        for t, r, (b, a, nb, na, mid) in lst:
            if typ == "GAME":
                fam, head = "moneyline", True
            elif typ in ("SPREAD", "TOTAL"):
                head = t == main
                fam = ("spread" if typ == "SPREAD" else "total") + ("_main" if head else "_alt")
            elif typ == "TEAMTOTAL":
                fam, head = "team_total", False
            elif typ in PERIOD:
                fam, head = "period_" + typ.lower(), False
            else:
                fam, head = "prop_" + typ.lower(), False
            y = 1.0 if res[t] == "yes" else 0.0
            rows.append(dict(t=t, sport=sp, fam=fam, head=head, game=ev.split("-", 1)[1][:13] if "-" in ev else ev, date=r["_d"],
                             mid=mid, bk=bucket(mid), y=y,
                             net_yes=y - a - fee(a), net_no=(1 - y) - na - fee(na), cost=(a - mid) + fee(a), raw=y - mid))
    return rows, dict(drops)


def split_dates(rows):
    cut = {}
    for sp in {r["sport"] for r in rows}:
        g = sorted({(r["date"], r["game"]) for r in rows if r["sport"] == sp})
        cut[sp] = g[int(len(g) * 2 / 3)][0] if g else None
    return cut


def boot(S, N, rng, B=2000):
    G = len(S)
    idx = rng.integers(0, G, size=(B, G))
    st = S[idx].sum(1) / N[idx].sum(1)
    return np.percentile(st, [5, 95]), st


def evaluate(rows, cuts, rng, label_key):
    """rows: list; groups by label_key(row). direction from fit window per (group, bucket)."""
    out = {}
    groups = defaultdict(list)
    for r in rows:
        groups[label_key(r)].append(r)
    for k, rs in groups.items():
        fit = [r for r in rs if r["date"] < cuts[r["sport"]]]
        jud = [r for r in rs if r["date"] >= cuts[r["sport"]]]
        dirn = {}
        for b in range(len(BUCKETS)):
            f = [r["raw"] for r in fit if r["bk"] == b]
            dirn[b] = (1 if np.mean(f) >= 0 else -1) if f else None
        # judged rows: only buckets with a fit-window direction (counted)
        use = [r for r in jud if dirn[r["bk"]] is not None]
        res = dict(n_total=len(rs), games_total=len({r['game'] for r in rs}), n_fit=len(fit), games_fit=len({r["game"] for r in fit}), n_judged_rows=len(jud), n_judged_used=len(use),
                   games_judged=len({r["game"] for r in use}))
        if use:
            nets = np.array([r["net_yes"] if dirn[r["bk"]] > 0 else r["net_no"] for r in use])
            gm = defaultdict(lambda: [0.0, 0])
            for r, n in zip(use, nets):
                gm[r["game"]][0] += n
                gm[r["game"]][1] += 1
            S = np.array([v[0] for v in gm.values()])
            N = np.array([v[1] for v in gm.values()], float)
            m = S.sum() / N.sum()
            ci, st = boot(S, N, rng)
            p = min(1.0, 2 * (min((st <= 0).sum(), (st >= 0).sum()) + 1) / (len(st) + 1))
            se = math.sqrt(((S - m * N) ** 2).sum()) / N.sum()
            cost = float(np.mean([r["cost"] for r in use]))
            gneed = len(S) * ((1.645 + 0.842) * se / cost) ** 2 if cost > 0 else None
            res |= dict(net=m, lo=float(ci[0]), hi=float(ci[1]), p=p, se=se, round_cost=cost, games_needed=gneed,
                        raw_gap_judged=float(np.mean([r["raw"] for r in use])))
            # per-bucket held-out
            bb = {}
            for b in range(len(BUCKETS)):
                u = [r for r in use if r["bk"] == b]
                if u:
                    nn = [r["net_yes"] if dirn[b] > 0 else r["net_no"] for r in u]
                    bb[b] = dict(n=len(u), games=len({r["game"] for r in u}), dir="YES" if dirn[b] > 0 else "NO", net=float(np.mean(nn)))
            res["buckets"] = bb
        out[k] = res
    return out


def bh(ps, q=0.10):
    items = sorted(ps.items(), key=lambda kv: kv[1])
    m, k_max = len(items), 0
    for i, (_, p) in enumerate(items, 1):
        if p <= q * i / m:
            k_max = i
    return {k for k, _ in items[:k_max]}


def main(archive, settled):
    res = {}
    for f in glob.glob(f"{settled}/*.json"):
        for m in json.load(open(f)):
            res[m["ticker"]] = m.get("result")
    out = {"settled_tickers": len(res)}
    for tag, loader in (("primary", 0), ("sens24h", 1)):
        pass
    best, near, anyk = load_archive(archive)
    out["archive_tickers_with_pre_start_snapshot"] = len(best)
    cov = defaultdict(lambda: dict(settled=0, any_snapshot=0, pre_start_snapshot=0, first_snapshot_after_cut=0))
    for t, (ts, ser, ev, cut) in anyk.items():
        sp, typ = split_series(ser)
        if t not in res or res[t] not in ("yes", "no"):
            continue
        k = f"{sp}|{ser[5:]}"
        cov[k]["any_snapshot"] += 1
        if t in best:
            cov[k]["pre_start_snapshot"] += 1
        else:
            cov[k]["first_snapshot_after_cut"] += 1
    for t, v in res.items():
        pass
    out["coverage_by_series"] = cov
    for tag, snap in (("primary", best), ("sens24h", near)):
        rows, drops = build_rows(snap, res)
        cuts = split_dates(rows)
        rng = np.random.default_rng(123)
        fam = evaluate(rows, cuts, rng, lambda r: f"{r['sport']}|{r['fam']}")
        fam_head = {}
        for k, v in fam.items():
            sp, f = k.split("|")
            v["head"] = any(r["head"] for r in rows if r["sport"] == sp and r["fam"] == f)
        pooled = evaluate(rows, cuts, rng, lambda r: "HEAD" if r["head"] else "NONHEAD")
        pooled_f = evaluate(rows, cuts, rng, lambda r: ("HEAD:" if r["head"] else "NONHEAD:") + r["fam"].split("_")[0] if not r["head"] else "HEAD:" + r["fam"])
        judged = {k: v for k, v in fam.items() if v.get("games_judged", 0) >= 30 and "net" in v}
        sig = bh({k: v["p"] for k, v in judged.items()})
        for k, v in fam.items():
            v["judged"] = k in judged
            v["bh_significant"] = k in sig
        out[tag] = dict(drops=drops, rows=len(rows), split_dates=cuts, sports_games={sp: len({r["game"] for r in rows if r["sport"] == sp}) for sp in cuts},
                        families=fam, pooled=pooled, pooled_by_type=pooled_f, n_family_tests=len(judged))
        # rule
        if tag == "primary":
            nh = {k: v for k, v in judged.items() if not v["head"]}
            hd = {k: v for k, v in judged.items() if v["head"]}
            c1 = [k for k, v in nh.items() if v["lo"] > 0]
            wmean = lambda d, key: (sum(v["net"] * v["n_judged_used"] for v in d.values()) / sum(v["n_judged_used"] for v in d.values())) if d else None
            amean = lambda d: (sum(abs(v["net"]) * v["n_judged_used"] for v in d.values()) / sum(v["n_judged_used"] for v in d.values())) if d else None
            out["rule"] = dict(clause1_families=c1, clause1_bh=[k for k in c1 if k in sig], nonhead_signed=wmean(nh, "net"), head_signed=wmean(hd, "net"),
                               nonhead_abs=amean(nh), head_abs=amean(hd), n_nonhead_judged=len(nh), n_head_judged=len(hd),
                               underpowered=[k for k, v in fam.items() if not v["judged"]])
    json.dump(out, open(safe_out(f"{HERE}/results.json"), "w"), indent=1, default=float)
    print(json.dumps(out["rule"], indent=1))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
