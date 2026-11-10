"""W108.4 Part B analysis. Reads data/*.json (fetch_weather.py). Research only.
Per market: model p (Gaussian around forecast max, bias/sigma fit per city on earlier 70% of days) vs Kalshi last-trade price
at the 23:00Z D-1 snapshot. Scores on the later 30%. Trade-toward-model net/contract after exact fee + half-spread proxy."""
import glob, json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))
from prediction_market_bot.quant import weather_calib as W
from prediction_market_bot.quant.scoring import brier_mean, log_loss_mean
from prediction_market_bot.quant.inference import cluster_bootstrap

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_HALF = 0.02


def parse_trades(trs, snap):
    out = []
    for t, px, side, cnt in trs:
        out.append((t, float(px), side, float(cnt)))
    return out


def price_and_spread(m):
    trs = m["trades"]
    if not trs:
        return None, None
    trs = sorted(trs, key=lambda x: x[0])
    last = float(trs[-1][1])
    ys = [float(p) for _, p, s, _ in trs if s == "yes"]
    ns = [float(p) for _, p, s, _ in trs if s == "no"]
    half = (sum(ys) / len(ys) - sum(ns) / len(ns)) / 2 if ys and ns else None
    if half is not None and not (0 <= half <= 0.2):
        half = None
    return last, half


def rolling_fit(hist, date, window=30):
    """Causal bias/sd from residuals of days <= date-2 within the trailing `window` days (all known at the D-1 snapshot)."""
    import datetime as dt
    d0 = dt.datetime.strptime(date, "%Y-%m-%d")
    lo = (d0 - dt.timedelta(days=window + 2)).strftime("%Y-%m-%d")
    hi = (d0 - dt.timedelta(days=2)).strftime("%Y-%m-%d")
    pr = [(f, a) for dd, f, a in hist if lo <= dd <= hi]
    if len(pr) < 10:
        return None
    b, sd = W.fit_error([f for f, _ in pr], [a for _, a in pr])
    return b, max(sd, 1.0)


def main():
    rows = []
    for f in sorted(glob.glob(os.path.join(HERE, "data", "*.json"))):
        for r in json.load(open(f)):
            if r["fc_max"] is None or not r["markets"]:
                continue
            act = None
            for m in r["markets"]:
                if m["exp_value"] not in (None, ""):
                    act = float(m["exp_value"]); break
            if act is None:
                continue
            rows.append((r["series"], r["date"], r["fc_max"], act, r["markets"]))
    dates = sorted({d for _, d, *_ in rows})
    cut = dates[int(len(dates) * 0.7)]
    out = {"cut_date": cut, "days_total": len(rows)}
    fits = {}
    for s in {r[0] for r in rows}:
        tr = [(r[2], r[3]) for r in rows if r[0] == s and r[1] < cut]
        if len(tr) >= 20:
            fits[s] = W.fit_error([a for a, _ in tr], [b for _, b in tr])
    out["fits"] = {k: {"bias": round(v[0], 3), "sd": round(v[1], 3), "n_train_days": sum(1 for r in rows if r[0] == k and r[1] < cut)} for k, v in fits.items()}
    hist = {}
    for s_, d_, fc_, act_, _ in rows:
        hist.setdefault(s_, []).append((d_, fc_, act_))
    P, Q, Y, cl = [], [], [], []
    PR = []
    pnl = {t: {} for t in (0.0, 0.03, 0.06, 0.10)}
    spreads = []
    for s, d, fc, act, ms in rows:
        if d < cut or s not in fits:
            continue
        b, sd = fits[s]
        for m in ms:
            px, half = price_and_spread(m)
            if px is None or not (0.01 <= px <= 0.99) or m["result"] not in ("yes", "no"):
                continue
            y = 1 if m["result"] == "yes" else 0
            p = W.strike_prob(fc + b, sd, m["floor"], m["cap"])
            p = min(max(p, 0.005), 0.995)
            rf = rolling_fit(hist[s], d)
            if rf is None:
                continue
            p2 = min(max(W.strike_prob(fc + rf[0], rf[1], m["floor"], m["cap"]), 0.005), 0.995)
            PR.append(p2)
            P.append(p); Q.append(px); Y.append(y); cl.append(f"{s}|{d}")
            if half is not None:
                spreads.append(half)
            h = half if half is not None else DEFAULT_HALF
            tt = W.trade_toward(p2, px, h, s)
            for th in pnl:
                if tt["edge"] > th:
                    v = W.realised(tt["side"], tt["ask_yes"], tt["ask_no"], y, s)
                    pnl[th].setdefault(f"{s}|{d}", []).append(v)
    out["n_test_markets"] = len(P); out["n_test_cityDays"] = len(set(cl))
    if P:
        out["brier_model_global_fit"] = brier_mean(P, Y); out["logloss_model_global_fit"] = log_loss_mean(P, Y)
        out["brier_model"] = brier_mean(PR, Y); out["logloss_model"] = log_loss_mean(PR, Y)
        out["note"] = "brier_model/logloss_model and net_per_contract use the causal trailing-30d bias/sd; *_global_fit uses the 70% train-split fit"
        _unused = ( 0,)
        out["brier_market"] = brier_mean(Q, Y)
        out["logloss_market"] = log_loss_mean(Q, Y)
        byc = {}
        for p, q, y, c in zip(PR, Q, Y, cl):
            byc.setdefault(c, []).append((q - y) ** 2 - (p - y) ** 2)
        pass  # >0: model better
        out["brier_gain_market_minus_model"] = dict(zip(("mean", "lo", "hi"), cluster_bootstrap(byc)))
    out["half_spread_proxy"] = {"n_with_proxy": len(spreads), "mean": sum(spreads) / len(spreads) if spreads else None, "default_used_otherwise": DEFAULT_HALF}
    out["net_per_contract"] = {}
    for th, d in pnl.items():
        n = sum(len(v) for v in d.values())
        if n:
            mean, lo, hi = cluster_bootstrap(d)
            out["net_per_contract"][f"edge>{th}"] = {"n_trades": n, "n_cityDays": len(d), "mean": mean, "lo": lo, "hi": hi}
    json.dump(out, open(os.path.join(HERE, "results.json"), "w"), indent=1)
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
