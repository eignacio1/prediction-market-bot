"""W104.1 Part B runner: why demo fills lose. READ-ONLY on every input; writes only result.json.

Usage: python3 run_w104_fills.py <FORWARD_TEST dir> <orders_ok.jsonl> <out path relative to 12_EXPLORATORY, e.g. quant_w104_fills/result.json>
  FORWARD_TEST dir holds demo_fill_forward_cache.json and markouts/markouts.jsonl (pulled read-only from the box);
  orders_ok.jsonl = policy-log shadow_order ok=true rows: [order_id, ts, row_id, price_yes, stake].

Epoch rule: NO-side fills before 2026-11-06T01:03:42Z are mirror-priced (GG-1771/GG-1784) -> excluded.
No order in the pulled data is after that epoch, so post-epoch n = 0 and everything below is YES-side.
"""
import json
import sys
from collections import Counter, defaultdict
from datetime import datetime

import numpy as np

sys.path.insert(0, "src")
sys.path.insert(0, "12_EXPLORATORY")
from _fence import safe_out  # noqa: E402
from prediction_market_bot.quant import fills  # noqa: E402

EPOCH = "2026-11-06T01:03:42"


def sport_of(ticker):
    for k, s in (("NFL", "NFL"), ("NHL", "NHL"), ("NBA", "NBA"), ("MLB", "MLB")):
        if k in ticker.split("-")[0]:
            return s
    return "OTH"


def parse_ts(s):
    return datetime.fromisoformat(s.rstrip("Z")[:26].split("+")[0])


def days_ahead(ticker, ots):
    """Coarse proxy for time-to-start: ticker game date (YYMONDD) minus order date, capped at 2."""
    try:
        seg = ticker.split("-")[1]
        d = datetime.strptime(seg[:7].title(), "%y%b%d")
        return int(min(max((d.date() - ots.date()).days, 0), 2))
    except Exception:
        return 0


def build(ft, ordf):
    cache = json.load(open(f"{ft}/demo_fill_forward_cache.json"))
    mk = {}
    for l in open(f"{ft}/markouts/markouts.jsonl"):
        r = json.loads(l)
        mk[r["order_id"]] = r
    start = json.load(open(f"{ft}/markouts/EPOCH.json"))["collection_start"][:19]
    rows = []
    for l in open(ordf):
        oid, ts, rid, p, _ = json.loads(l)
        c = cache.get(oid)
        if not c or not c.get("settled") or ts[:19] < start or ts[:19] >= EPOCH:
            continue
        ticker = rid.split("|", 1)[1]
        filled = c.get("fills", 0) > 0
        m = mk.get(oid)
        if filled and m is None:
            continue  # fill with unknown held side
        if filled and m["side"] != "YES":
            continue  # pre-epoch NO fills are mirror-priced
        win = c.get("won") if filled else c.get("nf_won")
        if win is None:
            continue
        ots = parse_ts(ts)
        rows.append(dict(oid=oid, ts=ts, day=ts[:10], game=ticker.rsplit("-", 1)[0], sport=sport_of(ticker), p=p,
                         filled=filled, win=float(win), da=days_ahead(ticker, ots), hour=ots.hour,
                         mk={h: (None if m is None or m.get(h) is None else m[h])  # already a markout (held mid - fill price)
                             for h in ("h1", "h5", "h30")} if filled else None))
    return rows


def design(rows):
    sp = ["NFL", "NHL", "NBA", "MLB"]
    X = []
    for r in rows:
        ext = abs(r["p"] - 0.5)
        X.append([ext, r["p"]] + [1.0 if r["sport"] == s else 0.0 for s in sp] +
                 [1.0 if r["da"] == 1 else 0.0, 1.0 if r["da"] >= 2 else 0.0,
                  1.0 if 0 <= r["hour"] < 12 else 0.0])
    return np.array(X)


NAMES = ["const", "|p-0.5|", "price_yes", "NFL", "NHL", "NBA", "MLB", "days_ahead=1", "days_ahead>=2", "hour_0_12UTC"]


def main(ft, ordf, out):
    rows = build(ft, ordf)
    days = sorted({r["day"] for r in rows})
    cut = days[int(len(days) * 0.7)]
    tr = [r for r in rows if r["day"] < cut]
    te = [r for r in rows if r["day"] >= cut]
    res = {"n_total": len(rows), "days": [days[0], days[-1]], "split_day": cut, "n_train": len(tr), "n_test": len(te),
           "epoch_note": "post-epoch n=0 (last pulled order precedes 2026-11-06T01:03:42Z); YES-side only",
           "sport_counts": dict(Counter(r["sport"] for r in rows))}

    Xtr, Xte = fills.add_const(design(tr)), fills.add_const(design(te))
    ytr = np.array([r["filled"] for r in tr], float)
    yte = np.array([r["filled"] for r in te], float)
    f = fills.fit_logit(Xtr, ytr)
    pte = fills.predict_logit(f, Xte)
    # game-clustered bootstrap CIs for coefficients (train)
    rng = np.random.default_rng(5)
    games = defaultdict(list)
    for i, r in enumerate(tr):
        games[r["game"]].append(i)
    gl = list(games.values())
    bs = []
    for _ in range(100):
        idx = np.concatenate([gl[k] for k in rng.integers(0, len(gl), len(gl))])
        try:
            bs.append(fills.fit_logit(Xtr[idx], ytr[idx])["beta"])
        except Exception:
            pass
    bs = np.array(bs)
    res["fill_model"] = {
        "train_fill_rate": float(ytr.mean()), "test_fill_rate": float(yte.mean()),
        "coef": [{"name": n, "beta": float(b), "ci90": [float(np.percentile(bs[:, k], 5)), float(np.percentile(bs[:, k], 95))]}
                 for k, (n, b) in enumerate(zip(NAMES, f["beta"]))],
        "test_calibration": fills.calibration(pte, yte),
        "test_auc_note": "see auc", "auc": _auc(pte, yte)}

    # markout by feature bucket + cluster OLS (YES fills only)
    fl = [r for r in rows if r["filled"]]
    res["markout"] = {}
    for h in ("h1", "h5", "h30"):
        sub = [r for r in fl if r["mk"][h] is not None]
        if len(sub) < 200:
            continue
        y = np.array([r["mk"][h] for r in sub])
        sdesign = fills.add_const(design(sub))
        o = fills.ols_cluster(sdesign, y, [r["game"] for r in sub])
        buckets = {}
        for name, fn in (("price<0.2", lambda r: r["p"] < .2), ("0.2-0.5", lambda r: .2 <= r["p"] < .5),
                         ("0.5-0.8", lambda r: .5 <= r["p"] < .8), (">=0.8", lambda r: r["p"] >= .8)):
            v = [r["mk"][h] for r in sub if fn(r)]
            if len(v) >= 30:
                buckets[name] = {"n": len(v), "mean": float(np.mean(v))}
        for s in ("NFL", "NHL", "NBA", "MLB"):
            v = [r["mk"][h] for r in sub if r["sport"] == s]
            if len(v) >= 30:
                buckets[s] = {"n": len(v), "mean": float(np.mean(v))}
        res["markout"][h] = {"n": len(sub), "mean": float(y.mean()), "clusters": o["clusters"],
                             "coef": [{"name": n, "beta": float(b), "se": float(s)} for n, b, s in zip(NAMES, o["beta"], o["se"])],
                             "buckets": buckets}

    # E3 gap explained: propensity fitted on TRAIN days, applied to TEST days
    ft_ = np.array([r["filled"] for r in te])
    wt = np.array([r["win"] for r in te])
    ptr_all = fills.predict_logit(f, Xte)
    res["e3"] = {"all_sports": fills.gap_explained(wt, ft_, ptr_all, clusters=[r["game"] for r in te], reps=500)}
    for s in ("NFL", "NHL", "NBA", "MLB"):
        ix = [i for i, r in enumerate(te) if r["sport"] == s]
        if len(ix) >= 400 and ft_[ix].sum() >= 50 and (~ft_[ix]).sum() >= 50:
            res["e3"][s] = fills.gap_explained(wt[ix], ft_[ix], ptr_all[ix], clusters=[te[i]["game"] for i in ix], reps=300)
    json.dump(res, open(safe_out(out), "w"), indent=1, default=float)
    print(json.dumps({k: res[k] for k in ("n_total", "n_train", "n_test", "split_day", "sport_counts")}))


def _auc(p, y):
    o = np.argsort(p)
    r = np.empty(len(p))
    r[o] = np.arange(1, len(p) + 1)
    n1 = y.sum()
    n0 = len(y) - n1
    return float((r[y == 1].sum() - n1 * (n1 + 1) / 2) / (n1 * n0))


if __name__ == "__main__":
    main(*sys.argv[1:4])
