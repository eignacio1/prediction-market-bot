"""W103.2 (B-045) analysis runner. Reads the compact TSV (epoch, series, event, ticker, yes_mid, half_spread)
extracted read-only from exp_output/PRICE_ARCHIVE. Parameters are the frozen pre-registration in RESULT.md.
Usage: python3 analyze.py compact.tsv.gz out.json
"""
import collections
import gzip
import json
import re
import sys
from datetime import datetime, timedelta, timezone

from prediction_market_bot.quant.multiplicity import benjamini_hochberg, holm
from prediction_market_bot.quant.price_dynamics import (
    big_move_events, hourly_regimes, lagged_regime, move_sigma, moves, reversion_fraction)

K = 3.0
MAX_GAP = 1800.0
REFRACT = 3600.0
H20, H60 = 1200.0, 3600.0
TOL = {H20: 300.0, H60: 600.0}
MIN_GAMES = 15
MON = {m: i + 1 for i, m in enumerate("JAN FEB MAR APR MAY JUN JUL AUG SEP OCT NOV DEC".split())}
DATE_RE = re.compile(r"-(\d{2})([A-Z]{3})(\d{2})")


def ticker_date(event):
    m = DATE_RE.search(event)
    if not m or m.group(2) not in MON:
        return None
    return datetime(2000 + int(m.group(1)), MON[m.group(2)], int(m.group(3)), tzinfo=timezone.utc).date()


def load(path):
    op = gzip.open if path.endswith(".gz") else open
    data = collections.defaultdict(lambda: collections.defaultdict(list))  # series -> ticker -> [(t, mid, hs, event)]
    with op(path, "rt") as f:
        for line in f:
            p = line.rstrip("\n").split("\t")
            if len(p) < 6:
                continue
            try:
                t, mid, hs = float(p[0]), float(p[4]), float(p[5]) if p[5] else 0.0
            except ValueError:
                continue
            data[p[1]][p[3]].append((t, mid, hs, p[2]))
    return data


def stat(evs_by_game, h):
    r = reversion_fraction(evs_by_game, h)
    r["flag"] = "interval undercovers (<%d games)" % MIN_GAMES if 0 < r["n_games"] < MIN_GAMES else ""
    return r


def main(src, dst):
    data = load(src)
    out = {"params": {"k": K, "max_gap_s": MAX_GAP, "refractory_s": REFRACT, "h": [H20, H60]}, "series": {}}
    for fam in sorted(data):
        tick = {tk: sorted(rows) for tk, rows in data[fam].items()}
        ser = {tk: [(t, m) for t, m, _, _ in rows] for tk, rows in tick.items()}
        hs_at = {tk: {t: hs for t, _, hs, _ in rows} for tk, rows in tick.items()}
        ev_of = {tk: rows[0][3] for tk, rows in tick.items()}
        deltas = [d for s in ser.values() for _, d, _ in moves(s, MAX_GAP)]
        sigma = move_sigma(deltas)
        groups = {"all": collections.defaultdict(list), "prior": collections.defaultdict(list),
                  "gameday": collections.defaultdict(list), "tight": collections.defaultdict(list)}
        by_reg = {"calm": collections.defaultdict(list), "jumpy": collections.defaultdict(list),
                  "none": collections.defaultdict(list)}
        trans_c = collections.Counter()
        n_big = 0
        for tk, s in ser.items():
            evs = big_move_events(s, K, sigma, MAX_GAP, REFRACT, [H60], TOL[H60], settle=True)
            ev20 = big_move_events(s, K, sigma, MAX_GAP, REFRACT, [H20], TOL[H20], settle=False)  # same events, +/-5 min tolerance
            assert [e["t"] for e in evs] == [e["t"] for e in ev20]
            for e, e2 in zip(evs, ev20):
                e["rev"][H20] = e2["rev"][H20]
            ev_date = ticker_date(ev_of[tk])
            labels = hourly_regimes(s, K, sigma, MAX_GAP)
            for h, a in labels.items():
                b = labels.get(h + 1)
                if b is not None:
                    trans_c[(a, b)] += 1
            for e in evs:
                if not (0.05 <= e["price"] - e["move"] <= 0.95):
                    continue
                n_big += 1
                g = ev_of[tk]
                groups["all"][g].append(e)
                d = datetime.fromtimestamp(e["t"], timezone.utc).date()
                if ev_date is not None:
                    if d < ev_date:
                        groups["prior"][g].append(e)
                    elif d <= ev_date + timedelta(days=1):
                        groups["gameday"][g].append(e)
                if hs_at[tk].get(e["t"], 1.0) <= 0.01:
                    groups["tight"][g].append(e)
                lab = lagged_regime(labels, e["t"]) or "none"
                by_reg[lab][g].append(e)
        nj = trans_c[("jumpy", "jumpy")] + trans_c[("jumpy", "calm")]
        nc = trans_c[("calm", "jumpy")] + trans_c[("calm", "calm")]
        rec = {"sigma": sigma, "n_steps": len(deltas), "n_events": n_big,
               "n_games_with_data": len({ev_of[t] for t in ser}),
               "regime": {"p_jj": trans_c[("jumpy", "jumpy")] / nj if nj else None,
                          "p_cj": trans_c[("calm", "jumpy")] / nc if nc else None, "n_after_jumpy": nj, "n_after_calm": nc}}
        for name, g in groups.items():
            rec[name] = {"h60": stat(g, H60), "h20": stat(g, H20), "settle": stat(g, "settle")}
        rec["by_regime"] = {n: {"h60": stat(g, H60)} for n, g in by_reg.items()}
        out["series"][fam] = rec
        print(fam, n_big, rec["all"]["h60"]["R"], flush=True)
    fams = [f for f in out["series"] if out["series"][f]["all"]["h60"]["n_games"] >= MIN_GAMES]
    ps = [out["series"][f]["all"]["h60"]["p_two_sided"] for f in fams]
    if ps:
        for f, h, b in zip(fams, holm(ps, 0.05), benjamini_hochberg(ps, 0.10)):
            out["series"][f]["primary"] = {"p": h["p"], "p_holm": h["p_adj"], "holm_reject": h["reject"],
                                          "q_bh": b["q"], "bh_reject": b["reject"]}
    out["primary_families"] = fams
    json.dump(out, open(dst, "w"), indent=1, default=str)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
