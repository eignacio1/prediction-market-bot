"""EXPLORATORY (W103.1, B-044): tails and kill-switch breach odds per (book, sport, side). Not evidence about any cell.

Purpose: PROOF/EXECUTION measurement quality - make ADR-0076 s4's blank limits computable. Reports tail geometry and
breach odds only; it publishes no win rate, mean P&L or verdict for any cell. Read-only on copies of the box files.

Usage: python3 run_tails_w103.py <fills_raw.csv> <t4m_proj_ledger.jsonl> <t1_mlb_paper_portfolio.json> <outdir>
  fills_raw.csv  = demo_fill_policy.jsonl events joined to the fill-status cache (cols ts,book,ticker,ident,side,price,fills,won,status)
  Money math: prediction_market_bot.quant.money.fill_pnl / fee_k007 (not re-implemented here).
"""
import csv
import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _fence import safe_out  # noqa: E402
from prediction_market_bot.quant import tails  # noqa: E402
from prediction_market_bot.quant.money import fee_k007, fill_pnl  # noqa: E402

KELLYS = (0.01, 0.025, 0.05)
MONTHS = (1, 6, 12)
MIN_DAYS = 15          # fewer active days than this: no breach estimate is made
MIN_GAMES = 60         # fewer games than this: no game-level tail fit is attempted
DEPLOY_CAP = 0.60      # ADR-0026 aggregate deployment cap, fraction of equity
EVENT_CAP_USD = 500.0  # _HARD_LIMITS max_single_event_exposure_usd
FAMILY_SPORT = {"KXNBA": "NBA", "KXNFL": "NFL", "KXNHL": "NHL", "KXMLB": "MLB"}


def sport_of(ticker):
    return FAMILY_SPORT.get(ticker[:5], "other")


def game_of(ticker):
    p = ticker.split("-")
    return p[1] if len(p) > 1 else ticker


def load_fills(path):
    """Shadow fills: YES-side only (mirror pricing is not involved). Returns {(book,sport,side): [(day, game, stake, pnl)]}."""
    out = defaultdict(list)
    skipped_unsettled = 0
    with open(path) as fh:
        for r in csv.DictReader(fh):
            fills = float(r["fills"] or 0)
            if fills <= 0:
                continue
            if r["won"] not in ("True", "False"):
                skipped_unsettled += 1
                continue
            if r["book"] != "shadow" or r["side"] != "yes":
                continue
            price = float(r["price"])
            y = 1.0 if r["won"] == "True" else 0.0
            pnl = fills * fill_pnl("yes", price, y)
            stake = fills * (price + fee_k007(price))
            out[("shadow", sport_of(r["ticker"]), "YES")].append((r["ts"][:10], game_of(r["ticker"]), stake, pnl))
    return out, skipped_unsettled


def load_ledger(rows, book, sport, kalshi_key, date_key="game_date"):
    out = defaultdict(list)
    fbar = defaultdict(list)
    for x in rows:
        if x.get("outcome") not in ("WIN", "LOSS"):
            continue
        side = x["direction"]
        stake = float(x["size_usd"])
        out[(book, sport, side)].append((x[date_key], game_of(x[kalshi_key]), stake, float(x["pnl"])))
        mp = float(x["model_p"])
        price = float(x.get("mip") or x.get("mid_price_at_entry"))
        p_side, c_side = (mp, price) if side == "YES" else (1 - mp, 1 - price)
        fbar[(book, sport, side)].append(max(0.0, (p_side - c_side) / (1 - c_side)))
    return out, {k: float(np.mean(v)) for k, v in fbar.items()}


def clusters(rows, idx):
    d = defaultdict(lambda: [0, 0.0, 0.0])
    for r in rows:
        c = d[r[idx]]
        c[0] += 1
        c[1] += r[2]
        c[2] += r[3]
    return d


def game_tail(rows, rng_seed=20261105):
    g = clusters(rows, 1)
    rho = np.array([v[2] / v[1] for v in g.values() if v[1] > 0])
    n = len(rho)
    res = {"n_games": n}
    if n < MIN_GAMES:
        res["status"] = "too few"
        return res
    loss = np.maximum(-rho, 0.0)
    ch = tails.choose_threshold(loss)
    f = ch["fit"]
    res["worst_game_loss_per_dollar"] = float(loss.max())
    if f["status"] != "OK":
        res["status"] = "too few"
        res["n_exc_at_q75"] = tails.pot_fit(loss)["n_exc"]
        return res
    res.update(status="OK", stable=ch["stable"], q=f["q"], n_exc=f["n_exc"], xi=f["xi"], sigma=f["sigma"])
    ci = tails.shape_ci(loss, q=f["q"], n_boot=300)
    res["xi_ci"] = [ci["lo"], ci["hi"]]
    res["tail_class"] = ci["class"]
    res["var99"] = tails.var(f, 0.99)
    res["es99"] = tails.expected_shortfall(f, 0.99)
    res["empirical_var99"] = float(np.quantile(loss, 0.99))
    rng = np.random.default_rng(rng_seed)
    vs = []
    for _ in range(300):
        b = pot = tails.pot_fit(rng.choice(loss, size=n, replace=True), q=f["q"])
        v = tails.var(b, 0.99) if b["status"] == "OK" else None
        if v is not None:
            vs.append(v)
    res["var99_ci"] = [float(np.percentile(vs, 2.5)), float(np.percentile(vs, 97.5))] if len(vs) > 50 else None
    res["var99_at_event_cap_usd"] = res["var99"] * EVENT_CAP_USD if res["var99"] is not None else None
    res["es99_at_event_cap_usd"] = res["es99"] * EVENT_CAP_USD if res["es99"] is not None else None
    return res


def breach_table(rows, fbar_book):
    d = clusters(rows, 0)
    days = sorted(d)
    n_days = len(days)
    span = (np.datetime64(days[-1]) - np.datetime64(days[0])).astype(int) + 1
    res = {"n_days": n_days, "calendar_span_days": int(span), "n_bets": int(sum(v[0] for v in d.values()))}
    if n_days < MIN_DAYS:
        res["status"] = "too few"
        return res
    rho = np.array([v[2] / v[1] for v in (d[k] for k in days)])
    nb = np.array([v[0] for v in (d[k] for k in days)], float)
    per_month = n_days / span * 30.4
    res.update(status="OK", active_days_per_month=float(per_month), bets_per_active_day=float(nb.mean()),
               worst_day_per_dollar=float(rho.min()), kelly_map_fbar=fbar_book)
    res["worst_day_equity_pct_at_cap"] = float(rho.min() * DEPLOY_CAP * 100)
    res["breach"] = {}
    for k in KELLYS:
        s = k * fbar_book
        ret = rho * np.minimum(nb, DEPLOY_CAP / s)  # equity change = s * ret = rho * min(s*n, cap)
        res["breach"][str(k)] = {"stake_frac": s, "cap_binds_share": float((s * nb >= DEPLOY_CAP).mean())}
        for m in MONTHS:
            h = max(1, int(round(per_month * m)))
            b = tails.breach_probability(ret, s, h, n_paths=20000, n_outer=200)
            res["breach"][str(k)][f"{m}m"] = {"horizon_days": h, "kill": b["drawdown_kill"], "breaker": b["daily_breaker"]}
    return res


def main(fills_p, ledger_p, t1_p, outdir):
    fills, unsettled = load_fills(fills_p)
    ledger = [json.loads(line) for line in open(ledger_p)]
    t1 = json.load(open(t1_p))["closed_positions"]
    books = dict(fills)
    fb = {}
    for rows, book, key in ((ledger, "T4M-PROJ", "kalshi_ticker"), (t1, "T1", "kalshi_ticker")):
        b, f = load_ledger(rows, book, "MLB", key)
        books.update(b)
        fb.update(f)
    f_proxy = fb[("T4M-PROJ", "MLB", "YES")]
    out = {"proxy_fbar_T4M_PROJ_YES": f_proxy, "skipped_unsettled_fill_rows": unsettled, "books": {}}
    series = []
    for key in sorted(books):
        rows = books[key]
        name = "|".join(key)
        fbar = fb.get(key, f_proxy)
        out["books"][name] = {"n_bets": len(rows), "kelly_map": "own ledger" if key in fb else "T4M-PROJ YES proxy",
                              "tail": game_tail(rows), "breach": breach_table(rows, fbar)}
        for day, v in sorted(clusters(rows, 0).items()):
            series.append((key[0], key[1], key[2], day, v[0], round(v[1], 4), round(v[2], 4)))
        print(name, out["books"][name]["tail"].get("status"), out["books"][name]["breach"].get("status"))
    with open(safe_out(Path(outdir) / "daily_series.csv"), "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["book", "sport", "side", "day", "n_bets", "stake_usd", "pnl_usd"])
        w.writerows(series)
    safe_out(Path(outdir) / "result.json").write_text(json.dumps(out, indent=1, default=float))


if __name__ == "__main__":
    main(*sys.argv[1:4], Path(sys.argv[4]).resolve())
