"""W117.2 Tests 1 and 2, exactly as PREREG.md (committed 2a45e52 before this ran). usage: python3 tests_momentum_kalshi.py <archive_root> <kalshi_dir>
kalshi_dir = exp_output/KALSHI_HISTORY_NHL (candles/KXNHLGAME.jsonl, markets/KXNHLGAME.jsonl). Writes momentum_kalshi_results.json beside this file."""
import collections, datetime as D, json, math, os, sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE)); sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(HERE)), "src"))
from _fence import safe_out  # noqa: E402
from prediction_market_bot.archive_intake import closing_lines as cl  # noqa: E402

SEED, B = 117, 2000
CODES = {'Anaheim Ducks':'ANA','Boston Bruins':'BOS','Buffalo Sabres':'BUF','Calgary Flames':'CGY','Carolina Hurricanes':'CAR','Chicago Blackhawks':'CHI','Colorado Avalanche':'COL','Columbus Blue Jackets':'CBJ','Dallas Stars':'DAL','Detroit Red Wings':'DET','Edmonton Oilers':'EDM','Florida Panthers':'FLA','Los Angeles Kings':'LA','Minnesota Wild':'MIN','Montreal Canadiens':'MTL','Nashville Predators':'NSH','New Jersey Devils':'NJ','New York Islanders':'NYI','New York Rangers':'NYR','Ottawa Senators':'OTT','Philadelphia Flyers':'PHI','Pittsburgh Penguins':'PIT','San Jose Sharks':'SJ','Seattle Kraken':'SEA','St. Louis Blues':'STL','Tampa Bay Lightning':'TB','Toronto Maple Leafs':'TOR','Utah Mammoth':'UTA','Vancouver Canucks':'VAN','Vegas Golden Knights':'VGK','Washington Capitals':'WSH','Winnipeg Jets':'WPG'}
logit = lambda p: np.log(p / (1 - p))


def fit_beta(y, off, x):
    b = 0.0
    for _ in range(50):
        p = 1 / (1 + np.exp(-(off + b * x)))
        g = np.sum((y - p) * x); h = np.sum(p * (1 - p) * x * x)
        if h <= 1e-12:
            return float("nan")
        nb = b + g / h
        if abs(nb - b) < 1e-10:
            return nb
        b = nb
    return b


def boot(stat, n, rng):
    return np.array([stat(rng.integers(0, n, n)) for _ in range(B)])


def ci(v):
    v = v[~np.isnan(v)]
    return [round(float(np.percentile(v, 5)), 5), round(float(np.percentile(v, 95)), 5)]


def momentum(games):
    specs = {
        "moneyline": lambda g: (None if None in (g["open_home_win_prob"], g["close_home_win_prob"]) else
                                (1.0 if g["moneyline_winner"] == "home" else 0.0, g["close_home_win_prob"], g["close_home_win_prob"] - g["open_home_win_prob"])),
        "puck_line": lambda g: (None if None in (g["open_spread_home"], g["close_spread_home"], g["close_home_cover_prob"]) or g["ats_result"] not in ("home", "away") else
                                (1.0 if g["ats_result"] == "home" else 0.0, g["close_home_cover_prob"], g["open_spread_home"] - g["close_spread_home"])),
        "total": lambda g: (None if None in (g["open_total"], g["close_total"], g["close_over_prob"]) or g["total_result"] not in ("over", "under") else
                            (1.0 if g["total_result"] == "over" else 0.0, g["close_over_prob"], g["close_total"] - g["open_total"])),
    }
    out = {}
    for name, f in specs.items():
        rs = [f(g) for g in games]; rs = [r for r in rs if r and 0 < r[1] < 1]
        a = np.array(rs); y, p, x = a[:, 0], a[:, 1], a[:, 2]; off = logit(p); n = len(y)
        stat = lambda i: fit_beta(y[i], off[i], x[i])
        b = fit_beta(y, off, x); v = boot(stat, n, np.random.default_rng(SEED)); lo, hi = ci(v)
        cut = int(round(n * 0.7)); bf = fit_beta(y[:cut], off[:cut], x[:cut])
        ll = lambda bb, yy, oo, xx: float(np.sum(yy * (oo + bb * xx) - np.log1p(np.exp(oo + bb * xx))))
        out[name] = {"n": n, "beta": round(float(b), 4), "ci90": [lo, hi], "moved_share": round(float(np.mean(x != 0)), 3), "move_sd": round(float(np.std(x)), 4),
                     "verdict": ("move carries information (prior for follow-the-move)" if lo > 0 else "close over-reacts (fade-the-move)" if hi < 0 else
                                 f"hypothesis closed (EXP-W117.2-MOM-{name}, parked for R&D)"),
                     "heldout_30pct": {"beta_fit_first70": round(float(bf), 4), "loglik_gain_vs_beta0_on_last30": round(ll(bf, y[cut:], off[cut:], x[cut:]) - ll(0.0, y[cut:], off[cut:], x[cut:]), 3), "n": n - cut}}
    return out


def kalshi(games, kdir):
    mk = [json.loads(l) for l in open(f"{kdir}/markets/KXNHLGAME.jsonl")]
    cd = {}
    for l in open(f"{kdir}/candles/KXNHLGAME.jsonl"):
        r = json.loads(l); cd[r["ticker"]] = r["candles"]
    ev = collections.defaultdict(dict)
    for m in mk:
        ev[m["event_ticker"]][m["ticker"].rsplit("-", 1)[1]] = m["ticker"]
    idx = {}
    for e, d in ev.items():
        idx[(frozenset(d), D.datetime.strptime(e.split("-")[1][:7], "%y%b%d").date())] = e
    def px(tk, cutoff):
        cs = [c for c in cd.get(tk, []) if c["t"] <= cutoff and c["bid"]["close"] is not None and c["ask"]["close"] is not None]
        if not cs:
            return None
        c = max(cs, key=lambda c: c["t"])
        return None if c["ask"]["close"] - c["bid"]["close"] > 0.10 else (c["bid"]["close"], c["ask"]["close"], cutoff - c["t"])
    matched = unmatched = no_px = 0; rows = []
    for g in games:
        h, a = CODES[g["home_team"]], CODES[g["away_team"]]
        e = idx.get((frozenset([h, a]), D.date.fromisoformat(g["date_et"])))
        if not e:
            unmatched += 1; continue
        matched += 1
        cutoff = int(D.datetime.strptime(g["start_time_utc"], "%Y-%m-%dT%H:%M:%S%z").timestamp()) - 3600
        ph, pa = px(ev[e][h], cutoff), px(ev[e][a], cutoff)
        if not ph or not pa:
            no_px += 1; continue
        mid = (ph[0] + ph[1]) / 2; pc = g["close_home_win_prob"]; hw = 1.0 if g["moneyline_winner"] == "home" else 0.0
        side_home = pc >= 0.5
        ask = ph[1] if side_home else pa[1]; won = hw if side_home else 1 - hw
        fee = 0.07 * ask * (1 - ask)
        oask = pa[1] if side_home else ph[1]; ofee = 0.07 * oask * (1 - oask)
        rows.append((mid - pc, won - ask - fee, (1 - won) - oask - ofee, ph[2]))
    a = np.array(rows) if rows else np.zeros((0, 4)); n = len(a); rng = np.random.default_rng(SEED)
    res = {"consensus_games": len(games), "matched_to_kalshi_event": matched, "unmatched": unmatched, "no_eligible_price": no_px, "n_eligible": n,
           "eligibility": "last hourly candle with t <= start-1h, bid and ask present, spread <= 0.10, both tickers", "thin_rule_n": 300}
    if n:
        for k, col in (("gap_kalshi_mid_minus_consensus_home", 0), ("ride_consensus_side_net", 1), ("mirror_other_side_net", 2)):
            v = boot(lambda i, c=col: a[i, c].mean(), n, rng)
            res[k] = {"mean": round(float(a[:, col].mean()), 5), "sd": round(float(a[:, col].std()), 4), "ci90": ci(v)}
        res["median_age_of_price_min_before_cutoff"] = int(np.median(a[:, 3]) // 60)
        res["thin"] = n < 300
    return res


if __name__ == "__main__":
    d = cl.load_nhl_closing(sys.argv[1]); reg = d["regular"]
    out = {"prereg": "12_EXPLORATORY/nhl_consensus/PREREG.md @ 2a45e52", "seed": SEED, "boot": B,
           "momentum_regular": momentum(reg), "momentum_playoffs_descriptive": momentum(d["postseason"]),
           "kalshi_vs_books_regular": kalshi(reg, sys.argv[2]), "kalshi_vs_books_playoffs_descriptive": kalshi(d["postseason"], sys.argv[2])}
    safe_out(os.path.join(HERE, "momentum_kalshi_results.json")).write_text(json.dumps(out, indent=1))
    print(json.dumps(out, indent=1))
